"""
moderation.py — Two-layer content safety check with Provider Fallback.

Layer 1: Fast Regex keyword check.
Layer 2: AI-based moderation (OpenAI Moderation API or Gemini/Groq safety check).
"""

import re
from typing import Tuple, Optional
from openai import AsyncOpenAI
from .provider import generate_text
from .config import settings
from .utils import logger, truncate

# ── Keyword-based blocklist ─────────────────────────────────────────────────
_BLOCK_PATTERNS = [
    r"\b(how\s+to\s+make|how\s+do\s+i\s+make|make\s+a)\s+(bomb|explosive|poison|meth|weapon)\b",
    r"\b(synthesize|manufacture|produce)\s+(drug|meth|cocaine|heroin|fentanyl)\b",
    r"\b(hack|crack|bypass)\s+(password|account|system|database)\b",
    r"\b(child\s+porn|cp|loli)\b",
    r"\b(kill\s+yourself|kys|go\s+die)\b",
    r"\b(n[i1]gg[ae]r|f[a@]gg[o0]t|c[u*]nt)\b",
    r"\b(how\s+to\s+commit\s+suicide|suicide\s+method)\b",
    r"\b(rape|sexual\s+assault)\s+(instructions|how\s+to)\b",
    r"\b(pirate|torrent|crack)\s+(software|game|movie|show)\b",
    r"\bdox\s+(someone|me|them|him|her)\b",
]
_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _BLOCK_PATTERNS]

def _keyword_check(text: str) -> Tuple[bool, str]:
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(text):
            logger.warning(f"Moderation keyword block — pattern={pattern.pattern[:40]}")
            return False, "blocked_keyword"
    return True, ""

# ── AI Moderation Check ─────────────────────────────────────────────────────
async def _ai_moderation_check(text: str) -> Tuple[bool, str]:
    """
    Check safety using OpenAI Moderation API (if key exists) 
    or fallback to a prompt-based check on the hybrid providers.
    """
    # 1. Try OpenAI Moderation if key is present
    if settings.OPENAI_API_KEY:
        try:
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.moderations.create(
                input=truncate(text, 2000),
                model="omni-moderation-latest",
            )
            if response.results[0].flagged:
                cats = [c for c, f in response.results[0].categories.__dict__.items() if f]
                logger.warning(f"OpenAI Moderation flagged: {cats}")
                return False, ", ".join(cats)
            return True, ""
        except Exception as e:
            logger.warning(f"OpenAI Moderation failed: {e}. Falling back to LLM check.")

    # 2. Fallback: LLM-based Safety Check
    logger.info("Performing LLM-based safety check...")
    safety_prompt = (
        "Analyze the following user query for safety. "
        "Is it harmful, hateful, sexually explicit, illegal, or dangerous? "
        "Return ONLY the word 'SAFE' or 'UNSAFE' followed by a short reason."
        f"\n\nQuery: {truncate(text, 500)}"
    )
    
    try:
        response = await generate_text([{"role": "user", "content": safety_prompt}])
        if "UNSAFE" in response.upper():
            logger.warning(f"LLM Moderation flagged: {response}")
            return False, "llm_flagged"
        return True, ""
    except Exception as e:
        logger.error(f"Safety check error: {e}. Blocking for safety.")
        return False, "safety_error"

async def is_query_safe(text: str) -> Tuple[bool, str]:
    if not text or not text.strip():
        return False, "empty_query"

    # Layer 1: Regex
    safe, reason = _keyword_check(text)
    if not safe:
        return False, reason

    # Layer 2: AI Check
    return await _ai_moderation_check(text)

BLOCKED_RESPONSE = (
    "I'm sorry, I'm not able to help with that request. "
    "Please ask me something appropriate and I'll be happy to assist!"
)
