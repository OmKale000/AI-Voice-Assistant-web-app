import warnings
import google.generativeai as genai
from typing import Optional, AsyncGenerator
# Suppress the deprecation warning for google-generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
from ..config import settings
from ..utils import logger
from .metrics import provider_metrics

# Lazy initialization
_model = None

def get_gemini_model():
    global _model
    if _model is None:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _model = genai.GenerativeModel(settings.FALLBACK_LLM_MODEL)
    return _model

async def gemini_generate_text_stream(messages, max_tokens, temperature, image_data: Optional[bytes] = None):
    """Gemini-specific text generation stream with multimodal support."""
    try:
        logger.info(f"Attempting Gemini multimodal: {settings.FALLBACK_LLM_MODEL}")
        model = get_gemini_model()
        
        gemini_messages = []
        for m in messages:
            role = "model" if m["role"] == "assistant" else "user"
            if m["role"] == "system":
                gemini_messages.append({"role": "user", "parts": [f"System Instruction: {m['content']}"]})
            else:
                gemini_messages.append({"role": role, "parts": [m["content"]]})

        # Add image to the last message if available
        if image_data and gemini_messages:
            gemini_messages[-1]["parts"].append({
                "mime_type": "image/jpeg",
                "data": image_data
            })

        response = await model.generate_content_async(
            gemini_messages,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
            stream=True
        )
        
        async for chunk in response:
            if chunk.text:
                yield chunk.text
        
        provider_metrics.active_provider = "gemini"
    except Exception as e:
        provider_metrics.gemini_failures += 1
        raise e


async def gemini_transcribe_audio(audio_bytes, filename):
    """Gemini-specific STT fallback."""
    try:
        logger.info("Attempting Gemini STT fallback")
        model = get_gemini_model()
        
        response = await model.generate_content_async([
            "Please transcribe this audio exactly as heard. Do not add any commentary.",
            {"mime_type": "audio/webm", "data": audio_bytes}
        ])
        provider_metrics.active_provider = "gemini"
        return response.text.strip()
    except Exception as e:
        provider_metrics.gemini_failures += 1
        raise e
