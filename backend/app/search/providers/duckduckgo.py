import logging
import json
from typing import List, Optional
from urllib.parse import urlencode

from app.search.models import SearchResult

logger = logging.getLogger("search.providers.duckduckgo")


def _parse_ddg_results(data: dict, max_results: int) -> List[SearchResult]:
    """
    Parse DuckDuckGo Instant Answer API response into SearchResult list.
    Falls back gracefully when fields are missing.
    """
    results: List[SearchResult] = []

    # RelatedTopics contains the actual web-search-style results
    for item in data.get("RelatedTopics", []):
        if len(results) >= max_results:
            break
        # Skip nested 'Topics' groupings — only grab leaf results
        if "Topics" in item:
            for sub in item.get("Topics", []):
                if len(results) >= max_results:
                    break
                text = sub.get("Text", "")
                first_url = sub.get("FirstURL", "")
                if text or first_url:
                    results.append(SearchResult(
                        title=text[:100] if text else "Result",
                        snippet=text,
                        url=first_url,
                        source="DuckDuckGo",
                        published=None,
                        summary=text[:200] if text else None,
                    ))
        else:
            text = item.get("Text", "")
            first_url = item.get("FirstURL", "")
            if text or first_url:
                results.append(SearchResult(
                    title=text[:100] if text else "Result",
                    snippet=text,
                    url=first_url,
                    source="DuckDuckGo",
                    published=None,
                    summary=text[:200] if text else None,
                ))

    # Also include Abstract if it's a knowledge-panel result
    abstract = data.get("Abstract", "")
    abstract_url = data.get("AbstractURL", "")
    if abstract and not results:
        results.insert(0, SearchResult(
            title=data.get("Heading", "Summary"),
            snippet=abstract,
            url=abstract_url,
            source=data.get("AbstractSource", "DuckDuckGo"),
            published=None,
            summary=abstract[:200],
        ))

    return results


async def _search_via_library(query: str, max_results: int) -> Optional[List[SearchResult]]:
    """
    Primary: use duckduckgo-search library for full text search results.
    Returns None if the library is not installed.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return None

    import asyncio

    def _sync_search():
        with DDGS() as ddgs:
            return ddgs.text(query, max_results=max_results)

    results: List[SearchResult] = []
    try:
        raw = await asyncio.to_thread(_sync_search)
        for item in raw or []:
            results.append(SearchResult(
                title=item.get("title", "Untitled"),
                snippet=item.get("body", ""),
                url=item.get("href", ""),
                source=item.get("source", "DuckDuckGo"),
                published=None,
                summary=item.get("body", "")[:200] if item.get("body") else None,
            ))
    except Exception as exc:
        logger.warning("duckduckgo-search library error", extra={"error": str(exc)})
        return None
    return results


async def _search_via_httpx(query: str, max_results: int) -> List[SearchResult]:
    """
    Fallback: query DuckDuckGo Instant Answer API using httpx (always available).
    Returns fewer results than the library but requires no extra dependencies.
    """
    try:
        import httpx
    except ImportError:
        logger.error("httpx not installed — cannot perform DuckDuckGo search")
        return []

    params = urlencode({
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1",
    })
    url = f"https://api.duckduckgo.com/?{params}"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, headers={"User-Agent": "AetherBot/1.0"})
            response.raise_for_status()
            data = response.json()
        return _parse_ddg_results(data, max_results)
    except Exception as exc:
        logger.warning("DuckDuckGo httpx fallback failed", extra={"error": str(exc)})
        return []


class DuckDuckGoSearchProvider:
    """
    Live search provider using DuckDuckGo.

    Strategy (in priority order):
      1. `duckduckgo-search` library — full text results (preferred)
      2. DuckDuckGo Instant Answer API via httpx — fallback (no extra deps)

    No API key required for either method.
    Degrades gracefully on any failure so the pipeline is never blocked.
    """

    def name(self) -> str:
        return "duckduckgo"

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        # Try primary: duckduckgo-search library
        results = await _search_via_library(query, max_results)
        if results is not None:
            logger.info(
                "DuckDuckGo search (library) complete",
                extra={"query": query[:80], "results": len(results)},
            )
            return results

        # Fallback: httpx Instant Answer API
        logger.info(
            "duckduckgo-search library unavailable — using httpx fallback",
            extra={"query": query[:80]},
        )
        results = await _search_via_httpx(query, max_results)
        logger.info(
            "DuckDuckGo search (httpx) complete",
            extra={"query": query[:80], "results": len(results)},
        )
        return results

    async def health_check(self) -> bool:
        try:
            results = await self.search("test", max_results=1)
            return True  # even empty is fine — no crash = healthy
        except Exception:
            return False
