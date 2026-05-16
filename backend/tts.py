"""
tts.py — Text-to-Speech via Provider Abstraction
"""

from .provider import synthesize_speech
from .utils import logger, Timer, truncate

async def text_to_speech(
    text: str,
    voice: str = None, # uses default from settings if None
    speed: float = 1.0, # edge-tts handles speed differently, skipping for simplicity
) -> bytes:
    """
    Convert text to speech using the hybrid provider router (Edge-TTS).
    """
    if not text or not text.strip():
        raise ValueError("Cannot synthesize empty text.")

    logger.info(f"Synthesizing TTS — chars={len(text)}")

    with Timer("tts_synthesis"):
        audio_bytes = await synthesize_speech(text)

    logger.info(f"TTS complete — {len(audio_bytes)} bytes")
    return audio_bytes
