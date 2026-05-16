"""
utils.py — Shared utilities: config, logging, caching, helpers.
"""

import os
import hashlib
import functools
import time
from typing import Any, Callable, Optional

from loguru import logger
from cachetools import TTLCache
from dotenv import load_dotenv

# ── Load .env from project root ────────────────────────────────────────────
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# ── Logging Configuration ───────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger.remove()
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level=LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} — {message}",
)
logger.add(
    lambda msg: print(msg, end=""),
    level=LOG_LEVEL,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:{line} — {message}",
)

# ── In-memory TTL Cache (shared singleton) ──────────────────────────────────
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
_cache: TTLCache = TTLCache(maxsize=256, ttl=CACHE_TTL)


def cache_key(*args: Any, **kwargs: Any) -> str:
    """Generate a deterministic cache key from arguments."""
    raw = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached(key: str) -> Optional[Any]:
    """Retrieve a value from the TTL cache."""
    return _cache.get(key)


def set_cached(key: str, value: Any) -> None:
    """Store a value in the TTL cache."""
    _cache[key] = value


def ttl_cached(func: Callable) -> Callable:
    """Decorator: caches async function results by stringified args."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        key = cache_key(func.__name__, *args, **kwargs)
        hit = get_cached(key)
        if hit is not None:
            logger.debug(f"Cache HIT for {func.__name__} — key={key[:8]}")
            return hit
        result = await func(*args, **kwargs)
        set_cached(key, result)
        logger.debug(f"Cache SET for {func.__name__} — key={key[:8]}")
        return result
    return wrapper


# ── Environment Helper ──────────────────────────────────────────────────────
def require_env(var: str) -> str:
    """Return env variable or raise a clear error."""
    value = os.getenv(var)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{var}' is not set. "
            f"Please add it to your .env file."
        )
    return value


# ── Text Helpers ────────────────────────────────────────────────────────────
def truncate(text: str, max_chars: int = 4000) -> str:
    """Truncate text to avoid exceeding token limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + " [truncated]"


def sanitize_text(text: str) -> str:
    """
    Basic text sanitization:
    - Strip leading/trailing whitespace
    - Collapse multiple newlines
    - Remove null bytes
    """
    text = text.replace("\x00", "")
    text = "\n".join(line.strip() for line in text.splitlines())
    text = text.strip()
    return text


# ── Timing Helper ───────────────────────────────────────────────────────────
class Timer:
    """Context manager for timing code blocks."""
    def __init__(self, label: str = ""):
        self.label = label
        self.elapsed: float = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.elapsed = time.perf_counter() - self._start
        logger.debug(f"⏱  {self.label}: {self.elapsed:.3f}s")

    @property
    def elapsed_ms(self) -> float:
        return self.elapsed * 1000.0


# ── OS helpers ──────────────────────────────────────────────────────────────
def ensure_dir(path: str) -> None:
    """Create directory (and parents) if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


# Ensure logs dir exists at import time
ensure_dir(os.path.join(os.path.dirname(__file__), "..", "logs"))
