"""
Tavily Search Provider — real implementation using the Tavily API.
API key: TAVILY_API_KEY in .env / environment.
Falls back gracefully (raises SearchProviderError) if key is missing.
"""
import logging
from typing import List

from app.search.models import SearchResult

logger = logging.getLogger("search.providers.tavily")


class TavilySearchProvider:
    def name(self) -> str:
        return "tavily"

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        from app.config.settings import get_settings
        settings = get_settings()
        api_key = settings.tavily_api_key
        if not api_key:
            raise NotImplementedError("TAVILY_API_KEY not configured")

        try:
            import httpx
        except ImportError:
            raise NotImplementedError("httpx not installed")

        url = "https://api.tavily.com/search"
        payload = {
            "api_key":      api_key,
            "query":        query,
            "max_results":  max_results,
            "search_depth": "basic",
            "include_answer": False,
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        results: List[SearchResult] = []
        for item in data.get("results", [])[:max_results]:
            results.append(SearchResult(
                title=item.get("title", "Untitled"),
                snippet=item.get("content", ""),
                url=item.get("url", ""),
                source="Tavily",
                published=item.get("published_date"),
                summary=item.get("content", "")[:200] if item.get("content") else None,
            ))

        logger.info(
            "Tavily search complete",
            extra={"query": query[:80], "results": len(results)},
        )
        return results

    async def health_check(self) -> bool:
        try:
            results = await self.search("test", max_results=1)
            return True
        except NotImplementedError:
            return False   # No key — not healthy but not a crash
        except Exception:
            return False
