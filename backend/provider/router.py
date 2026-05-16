import edge_tts
from typing import List, Dict, AsyncGenerator, Optional
from ..config import settings
from ..utils import logger, truncate
from .metrics import provider_metrics
from .groq import groq_generate_text_stream, groq_transcribe_audio
from .gemini import gemini_generate_text_stream, gemini_transcribe_audio

async def generate_text_stream(
    messages: List[Dict[str, str]],
    image_data: Optional[bytes] = None
) -> AsyncGenerator[str, None]:
    """
    Generate text with streaming support and automatic fallback.
    """
    # If image is present, go straight to Gemini (Groq/Llama3 doesn't support multimodal here yet)
    if image_data:
        try:
            async for chunk in gemini_generate_text_stream(messages, settings.MAX_TOKENS, settings.TEMPERATURE, image_data):
                yield chunk
            return
        except Exception as e:
            logger.error(f"Gemini multimodal failed: {e}")
            yield "I'm sorry, I couldn't process that image."
            return

    # 1. Try Groq (Primary)
    try:
        async for chunk in groq_generate_text_stream(messages, settings.MAX_TOKENS, settings.TEMPERATURE):
            yield chunk
        return # Success

    except Exception as e:
        logger.warning(f"Groq primary failed: {e}. Switching to Gemini fallback...")
        provider_metrics.fallbacks += 1

    # 2. Fallback to Gemini
    try:
        async for chunk in gemini_generate_text_stream(messages, settings.MAX_TOKENS, settings.TEMPERATURE):
            yield chunk
    except Exception as e:
        logger.error(f"Gemini fallback also failed: {e}")
        yield "I'm sorry, I'm having trouble connecting to my brain right now. Please try again later."

async def generate_text(messages: List[Dict[str, str]], image_data: Optional[bytes] = None) -> str:
    """Non-streaming version of generate_text."""
    full_text = ""
    async for chunk in generate_text_stream(messages, image_data=image_data):
        full_text += chunk
    return full_text


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Transcribe audio with Groq primary and Gemini fallback.
    """
    # 1. Try Groq Whisper
    try:
        return await groq_transcribe_audio(audio_bytes, filename)
    except Exception as e:
        logger.warning(f"Groq STT failed: {e}. Falling back to Gemini STT...")
        provider_metrics.fallbacks += 1
        
    # 2. Fallback to Gemini STT
    try:
        return await gemini_transcribe_audio(audio_bytes, filename)
    except Exception as e:
        logger.error(f"Gemini STT fallback failed: {e}")
        return ""

async def synthesize_speech(text: str) -> bytes:
    """
    Convert text to speech using Edge-TTS.
    """
    if not text.strip():
        return b""
        
    logger.info(f"Synthesizing speech with Edge-TTS: {settings.TTS_VOICE}")
    safe_text = truncate(text, 1000)
    
    try:
        communicate = edge_tts.Communicate(safe_text, settings.TTS_VOICE)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except Exception as e:
        logger.error(f"Edge-TTS synthesis failed: {e}")
        return b""
