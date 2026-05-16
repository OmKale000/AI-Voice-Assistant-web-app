"""
main.py — FastAPI Application Entrypoint.
Optimized for production with robust error handling, provider health monitoring, and Firebase resilience.
"""

import json
import asyncio
import urllib.parse
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, Depends
from fastapi.responses import Response, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.utils import logger, Timer
from backend.middleware import MetricsMiddleware

# Core logic imports
from backend.stt import transcribe_audio
from backend.moderation import is_query_safe, BLOCKED_RESPONSE
from backend.weather import fetch_weather, weather_to_context
from backend.search import web_search
from backend.llm import generate_response
from backend.tts import text_to_speech
from backend.intent import detect_intent
from backend.memory import get_truncated_history
from backend.database import log_interaction, get_recent_conversations, get_session_history, firebase_status
from backend.cache import get_cached_response, cache_response

# Provider abstraction imports (new structure)
from backend.provider import provider_metrics

# --- Startup Validation ---
def validate_config():
    missing = []
    if not settings.GROQ_API_KEY: missing.append("GROQ_API_KEY")
    if not settings.GEMINI_API_KEY: missing.append("GEMINI_API_KEY")
    if not settings.WEATHER_API_KEY: missing.append("WEATHER_API_KEY")
    
    if missing:
        logger.warning(f"⚠️  Missing API keys: {', '.join(missing)}. Some features will fail.")
    else:
        logger.info("✅ All core API keys validated.")

# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    validate_config()
    logger.info("🚀 NEXUS AI API Starting Up...")
    yield
    # Shutdown
    logger.info("🛑 NEXUS AI API Shutting Down...")
    # Optional: Close database connections or streams here

# --- Rate Limiting ---
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="NEXUS AI API",
    description="Production-grade AI Voice Assistant backend.",
    version="4.1.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Global Error Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal Server Error", "detail": str(exc)}
    )

# --- Middleware ---
app.add_middleware(MetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpoints ---

@app.get("/health")
async def health_check():
    """Detailed health status for monitoring."""
    return {
        "status": "healthy",
        "version": "4.1.0",
        "providers": {
            "active": provider_metrics.active_provider,
            "groq": "online" if settings.GROQ_API_KEY else "unconfigured",
            "gemini": "online" if settings.GEMINI_API_KEY else "unconfigured"
        },
        "firebase": firebase_status
    }

@app.get("/api/history")
async def get_history():
    """Retrieve recent conversation sessions."""
    try:
        sessions = await get_recent_conversations()
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        return {"sessions": []}

@app.get("/api/history/{session_id}")
async def get_chat_history(session_id: str):
    """Retrieve messages for a specific session."""
    try:
        messages = await get_session_history(session_id)
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Session history fetch error: {e}")
        return {"messages": []}

@app.get("/api/analytics")
async def get_analytics(request: Request):
    """Aggregated usage metrics."""
    try:
        metrics_data = getattr(request.app.state, "metrics", {})
        total_reqs = metrics_data.get("total_requests", 0)
        avg_latency = 0
        if total_reqs > 0:
            avg_latency = round(metrics_data.get("total_latency_ms", 0) / total_reqs, 2)
            
        return {
            "total_requests": total_reqs,
            "failed_requests": metrics_data.get("failed_requests", 0),
            "active_provider": provider_metrics.active_provider,
            "fallbacks": provider_metrics.fallbacks,
            "groq_failures": provider_metrics.groq_failures,
            "gemini_failures": provider_metrics.gemini_failures,
            "avg_latency_ms": avg_latency
        }
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return {"error": "Failed to retrieve metrics"}

@app.post("/api/process-audio")
@limiter.limit(settings.RATE_LIMIT_VOICE)
async def process_audio(
    request: Request,
    audio: UploadFile = File(...),
    image: Optional[UploadFile] = File(None),
    chat_history: str = Form(default="[]"),
    session_id: str = Form(default="default_session"),
):
    """Main voice processing pipeline with Multimodal support."""
    with Timer("total_request_time") as t:
        try:
            # 1. Validation
            if audio.content_type not in settings.ALLOWED_AUDIO_TYPES:
                 logger.warning(f"Restricted MIME type: {audio.content_type}")

            audio_bytes = await audio.read()
            if not audio_bytes:
                raise HTTPException(status_code=400, detail="Audio stream empty.")
                
            image_bytes = None
            if image:
                image_bytes = await image.read()
                logger.info(f"Image received: {image.filename} ({len(image_bytes)} bytes)")

                
            if (len(audio_bytes) / (1024 * 1024)) > settings.MAX_AUDIO_SIZE_MB:
                raise HTTPException(status_code=413, detail="Audio file too large.")

            try:
                history: List[Dict[str, str]] = json.loads(chat_history)
            except json.JSONDecodeError:
                history = []
                
            # 2. STT
            query_text = await transcribe_audio(audio_bytes, audio.filename or "recording.webm")
            if not query_text or not query_text.strip():
                 raise HTTPException(status_code=400, detail="No speech detected.")

            # 3. Cache
            cached_answer = get_cached_response(query_text)
            if cached_answer:
                audio_response = await text_to_speech(cached_answer)
                asyncio.create_task(log_interaction(session_id, query_text, cached_answer, "cache_hit", 0, "cache"))
                return build_audio_response(query_text, cached_answer, is_safe=True, audio_bytes=audio_response)

            # 4. Moderation
            is_safe, reason = await is_query_safe(query_text)
            if not is_safe:
                response_text = BLOCKED_RESPONSE
                audio_response = await text_to_speech(response_text)
                asyncio.create_task(log_interaction(session_id, query_text, response_text, "blocked", 0, "moderation", is_safe=False))
                return build_audio_response(query_text, response_text, is_safe=False, audio_bytes=audio_response)

            # 5. Intent & Context
            intent_data = await detect_intent(query_text)
            intent = intent_data.get("intent", "general_search")
            context = None
            
            if intent == "weather":
                city = intent_data.get("city")
                if city:
                    try:
                        weather_data = await fetch_weather(city)
                        context = weather_to_context(weather_data)
                    except Exception:
                        context = f"I had trouble reaching the weather service for {city}."
                        
            elif intent in ["news", "general_search"]:
                is_news = intent == "news"
                try:
                    context = await web_search(query_text, news_mode=is_news)
                except Exception:
                    context = "I encountered an error searching the live web."
                    
            # 6. LLM
            history = get_truncated_history(history)
            response_text = await generate_response(query_text, context, history, image_data=image_bytes)
            cache_response(query_text, response_text)


            # 7. TTS
            audio_response = await text_to_speech(response_text)

            # 8. Logging
            latency = t.elapsed_ms
            asyncio.create_task(log_interaction(
                session_id, 
                query_text, 
                response_text, 
                intent, 
                latency, 
                provider_metrics.active_provider,
                image_present=(image_bytes is not None)
            ))


            return build_audio_response(query_text, response_text, is_safe=True, audio_bytes=audio_response)
        
        except HTTPException:
            raise
        except asyncio.CancelledError:
            logger.warning("Request cancelled by client.")
            raise
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stream-text")
@limiter.limit(settings.RATE_LIMIT_TEXT)
async def stream_text(
    request: Request,
    query: str = Form(...),
    chat_history: str = Form(default="[]"),
):
    """Streaming text endpoint."""
    try:
        history = json.loads(chat_history)
    except json.JSONDecodeError:
        history = []
        
    async def event_generator():
        try:
            async for chunk in await generate_response(query, None, history, stream=True):
                yield chunk
        except asyncio.CancelledError:
            logger.debug("Text stream cancelled.")

    return StreamingResponse(event_generator(), media_type="text/plain")


def build_audio_response(query: str, response: str, is_safe: bool, audio_bytes: bytes):
    """Helper to construct audio response with metadata headers."""
    # Use URL encoding for headers to safely handle non-ASCII characters
    safe_q = urllib.parse.quote(query)
    safe_r = urllib.parse.quote(response)
    
    headers = {
        "X-Query-Text": safe_q,
        "X-Response-Text": safe_r,
        "X-Is-Safe": "true" if is_safe else "false",
    }
    return Response(content=audio_bytes, media_type="audio/mpeg", headers=headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        reload_excludes=["logs/*", "__pycache__/*", "*.tmp"]
    )
