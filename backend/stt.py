"""
stt.py — Speech-to-Text via Provider Abstraction
"""

from typing import Optional
from .provider import transcribe_audio as provider_transcribe
from .utils import logger, Timer
from .config import settings

async def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "audio.webm",
    language: Optional[str] = None,
) -> str:
    """
    Transcribe audio using the hybrid provider router.
    """
    if not audio_bytes:
        raise ValueError("Audio data is empty.")
    
    # Validation is also done in main.py but here for safety
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_AUDIO_SIZE_MB:
        raise ValueError(f"Audio file too large ({size_mb:.1f} MB). Max {settings.MAX_AUDIO_SIZE_MB} MB.")

    logger.info(f"Transcribing audio — size={len(audio_bytes)} bytes, file={filename}")

    with Timer("stt_transcription"):
        transcript = await provider_transcribe(audio_bytes, filename)
    
    result = str(transcript).strip()
    logger.info(f"Transcript ({len(result)} chars): {result[:120]}...")
    return result
