import time
import logging
from typing import Optional, List, Dict, Any
from .models import SearchResult, SearchCategory
from .exceptions import SearchCacheError
from app.db.repositories.collections import SearchCacheRepository

logger = logging.getLogger("search.cache")


class SearchCache:
    """
    MongoDB-backed search cache with TTL support.
    Replaces previous Redis/in-process dictionary.
    """

    TTL_MAP: Dict[SearchCategory, int] = {
        SearchCategory.NEWS:    900,
        SearchCategory.WEATHER: 600,
        SearchCategory.SPORTS:  30,
        SearchCategory.GENERAL: 86400,
    }

    def __init__(self, redis_url: str = ""):
        self.repo = SearchCacheRepository()
        self._hits = 0
        self._misses = 0

    # ── Public API ────────────────────────────────────────────────────────────

    async def get(self, key: str) -> Optional[List[SearchResult]]:
        """Return cached results or None on miss."""
        doc = await self.repo.find_one({"key": key})
        if doc:
            expiry = doc.get("expiry", 0)
            if time.time() < expiry:
                self._hits += 1
                logger.info("Cache hit", extra={"key": key})
                raw = doc.get("results", [])
                return [SearchResult(**r) for r in raw]
            else:
                # Expired, clean it up
                await self.repo.delete_one({"key": key})

        self._misses += 1
        logger.info("Cache miss", extra={"key": key})
        return None

    async def set(
        self,
        key: str,
        results: List[SearchResult],
        category: SearchCategory = SearchCategory.GENERAL,
        ttl: Optional[int] = None,
    ) -> None:
        """Store results with a category-driven TTL."""
        effective_ttl = ttl or self.TTL_MAP.get(category, 86400)
        serialized = [r.model_dump() for r in results]
        expiry = time.time() + effective_ttl

        await self.repo.update_one(
            {"key": key},
            {"key": key, "results": serialized, "expiry": expiry, "category": category.value},
            upsert=True
        )

        logger.info(
            "Cache set",
            extra={"key": key, "ttl": effective_ttl, "count": len(results)},
        )

    async def invalidate(self, key: str) -> None:
        await self.repo.delete_one({"key": key})
        logger.info("Cache invalidated", extra={"key": key})

    def get_stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total else 0.0,
        }
