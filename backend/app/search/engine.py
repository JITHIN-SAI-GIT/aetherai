import time
import logging
from typing import Optional
from .models import SearchDecision, SearchResponse, SearchCategory
from .normalizer import QueryNormalizer
from .cache import SearchCache
from .registry import SearchProviderRegistry
from .summarizer import Summarizer
from .metrics import SearchMetrics
from .exceptions import NoSearchProviderError, SearchProviderError

logger = logging.getLogger("search.engine")


class SearchEngine:
    """
    Orchestrates the complete search flow:
    Normalize → Cache Lookup → Provider → Summarize → Cache Store → Return.
    """

    def __init__(
        self,
        registry: SearchProviderRegistry,
        cache: SearchCache,
        normalizer: QueryNormalizer,
        summarizer: Summarizer,
        metrics: SearchMetrics,
        max_results: int = 5,
    ):
        self._registry = registry
        self._cache = cache
        self._normalizer = normalizer
        self._summarizer = summarizer
        self._metrics = metrics
        self._max_results = max_results

    async def search(
        self,
        query: str,
        category: SearchCategory = SearchCategory.GENERAL,
    ) -> SearchResponse:
        start = time.perf_counter()

        # ── Step 1: Normalize ──────────────────────────────────────────────
        cache_key = self._normalizer.cache_key(query)

        # ── Step 2: Cache Lookup ───────────────────────────────────────────
        cached = await self._cache.get(cache_key)
        if cached:
            self._metrics.record_cache_hit()
            logger.info("Returning cached results", extra={"key": cache_key})
            return SearchResponse(
                query=query,
                results=cached,
                provider="cache",
                cache_hit=True,
                latency_ms=round((time.perf_counter() - start) * 1000, 2),
                category=category,
            )

        self._metrics.record_cache_miss()

        # ── Step 3: Provider Selection ────────────────────────────────────
        provider_name = "none"
        try:
            provider = self._registry.get_provider()
            provider_name = provider.name()
        except NoSearchProviderError:
            logger.warning("No search provider available — returning empty results")
            return self._empty_response(query, category, start)

        # ── Step 4: Execute Search ────────────────────────────────────────
        raw_results = []
        try:
            with self._metrics.track(provider_name):
                raw_results = await provider.search(query, self._max_results)
        except (NotImplementedError, SearchProviderError) as e:
            logger.warning(
                "Provider search failed",
                extra={"provider": provider_name, "error": str(e)},
            )
            return self._empty_response(query, category, start, provider=provider_name)

        # ── Step 5: Summarize ─────────────────────────────────────────────
        results = self._summarizer.summarize(
            [r.model_dump() for r in raw_results]
        )

        # ── Step 6: Cache Store ───────────────────────────────────────────
        await self._cache.set(cache_key, results, category=category)

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "Search complete",
            extra={
                "provider": provider_name,
                "results": len(results),
                "latency_ms": latency_ms,
                "cache_hit": False,
            },
        )
        return SearchResponse(
            query=query,
            results=results,
            provider=provider_name,
            cache_hit=False,
            latency_ms=latency_ms,
            category=category,
        )

    # ── Private helpers ─────────────────────────────────────────────────────

    def _empty_response(
        self, query: str, category: SearchCategory,
        start: float, provider: str = "none"
    ) -> SearchResponse:
        return SearchResponse(
            query=query,
            results=[],
            provider=provider,
            cache_hit=False,
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
            category=category,
        )
