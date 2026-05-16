"""
search.py — Web search via Tavily (preferred) with DuckDuckGo fallback.
"""

import re
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

from .config import settings
from .utils import logger, Timer, ttl_cached, sanitize_text, truncate

# ── Tavily ───────────────────────────────────────────────────────────────────
try:
    from tavily import AsyncTavilyClient
    _TAVILY_AVAILABLE = True
except ImportError:
    _TAVILY_AVAILABLE = False

# ── DuckDuckGo ───────────────────────────────────────────────────────────────
try:
    from duckduckgo_search import DDGS
    _DDG_AVAILABLE = True
except ImportError:
    _DDG_AVAILABLE = False

def _clean_snippet(text: str) -> str:
    """Remove HTML tags, collapse whitespace, strip."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return sanitize_text(text)

def _build_context(results: List[dict], max_results: int = 4) -> str:
    """Convert raw search result list into a structured context string."""
    lines = []
    for i, r in enumerate(results[:max_results], 1):
        title = _clean_snippet(r.get("title", ""))
        snippet = _clean_snippet(r.get("content", r.get("body", "")))
        url = r.get("url", r.get("href", ""))
        if snippet:
            lines.append(f"[{i}] {title}\n{truncate(snippet, 500)}\nSource: {url}")
    return "\n\n".join(lines)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def _search_tavily(query: str, news: bool = False) -> str:
    """Search via Tavily AI Search API."""
    if not _TAVILY_AVAILABLE:
        raise ImportError("tavily-python not installed.")

    api_key = settings.TAVILY_API_KEY
    if not api_key:
        raise ValueError("TAVILY_API_KEY not configured.")

    client = AsyncTavilyClient(api_key=api_key)
    topic = "news" if news else "general"

    with Timer("tavily_search"):
        response = await client.search(
            query=query,
            search_depth="basic",
            topic=topic,
            max_results=5,
            include_answer=True,
        )

    results = response.get("results", [])
    ai_answer = response.get("answer", "")

    context_parts = []
    if ai_answer:
        context_parts.append(f"Summary: {_clean_snippet(ai_answer)}")
    if results:
        context_parts.append(_build_context(results))

    return "\n\n".join(context_parts)

async def _search_ddg(query: str, news: bool = False) -> str:
    """Synchronous DuckDuckGo search wrapped for async use."""
    if not _DDG_AVAILABLE:
        raise ImportError("duckduckgo-search not installed.")

    import asyncio

    def _sync_search() -> list:
        with DDGS() as ddgs:
            if news:
                return list(ddgs.news(query, max_results=5))
            return list(ddgs.text(query, max_results=5))

    with Timer("ddg_search"):
        results = await asyncio.get_event_loop().run_in_executor(None, _sync_search)

    normalized = []
    for r in results:
        normalized.append({
            "title": r.get("title", ""),
            "content": r.get("body", r.get("snippet", "")),
            "url": r.get("url", r.get("href", "")),
        })

    return _build_context(normalized)

@ttl_cached
async def web_search(query: str, news_mode: bool = False) -> Optional[str]:
    """Perform a web search with Tavily preferred, DDG as fallback."""
    logger.info(f"Web search — query='{query[:80]}', news={news_mode}")

    tavily_key = settings.TAVILY_API_KEY
    if _TAVILY_AVAILABLE and tavily_key:
        try:
            result = await _search_tavily(query, news=news_mode)
            if result:
                logger.info("Web search: Tavily success")
                return result
        except Exception as exc:
            logger.warning(f"Tavily failed: {exc} — falling back to DDG")

    if _DDG_AVAILABLE:
        try:
            result = await _search_ddg(query, news=news_mode)
            if result:
                logger.info("Web search: DuckDuckGo success")
                return result
        except Exception as exc:
            logger.warning(f"DuckDuckGo also failed: {exc}")

    logger.error("All search backends failed.")
    return None
