import json
import httpx
from ..config import settings
from ..utils import logger
from .metrics import provider_metrics

async def groq_generate_text_stream(messages, max_tokens, temperature):
    """Groq-specific text generation stream."""
    try:
        logger.info(f"Attempting Groq generation: {settings.PRIMARY_LLM_MODEL}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                f"{settings.GROQ_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={
                    "model": settings.PRIMARY_LLM_MODEL,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,
                },
            ) as response:
                if response.status_code != 200:
                    error_detail = await response.aread()
                    raise RuntimeError(f"Groq API error {response.status_code}: {error_detail.decode()}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except json.JSONDecodeError:
                            continue
        provider_metrics.active_provider = "groq"
    except Exception as e:
        provider_metrics.groq_failures += 1
        raise e

async def groq_transcribe_audio(audio_bytes, filename):
    """Groq-specific STT."""
    try:
        logger.info(f"Attempting Groq STT: {settings.STT_MODEL}")
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": (filename, audio_bytes, "application/octet-stream")}
            data = {"model": settings.STT_MODEL}
            response = await client.post(
                f"{settings.GROQ_BASE_URL}/audio/transcriptions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json().get("text", "")
    except Exception as e:
        provider_metrics.groq_failures += 1
        raise e
