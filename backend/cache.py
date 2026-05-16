"""
cache.py — Smart Response Cache
Implements query fingerprinting and TTL-based response caching to optimize token usage.
"""

import hashlib
import re
from typing import Optional
from cachetools import TTLCache
from .config import settings
from .utils import logger

# In-memory cache for responses
# Key: Query fingerprint, Value: Response text
_response_cache = TTLCache(maxsize=settings.MAX_CACHE_SIZE, ttl=settings.CACHE_TTL_SECONDS)

def normalize_query(query: str) -> str:
    """Normalize query for consistent fingerprinting."""
    # Lowercase, remove extra whitespace, remove non-alphanumeric at ends
    q = query.lower().strip()
    q = re.sub(r'\s+', ' ', q)
    # Remove common filler words or slight variations
    q = re.sub(r'^(please|nexus|assistant|hey|hi),?\s*', '', q)
    return q

def get_query_fingerprint(query: str) -> str:
    """Generate a stable hash for a query."""
    normalized = normalize_query(query)
    return hashlib.md5(normalized.encode()).hexdigest()

def get_cached_response(query: str) -> Optional[str]:
    """Retrieve response from cache if it exists."""
    fingerprint = get_query_fingerprint(query)
    if fingerprint in _response_cache:
        logger.info(f"Cache HIT for query fingerprint: {fingerprint}")
        return _response_cache[fingerprint]
    return None

def cache_response(query: str, response: str):
    """Store response in cache."""
    if not query or not response:
        return
    fingerprint = get_query_fingerprint(query)
    _response_cache[fingerprint] = response
    logger.info(f"Cached response for fingerprint: {fingerprint}")
