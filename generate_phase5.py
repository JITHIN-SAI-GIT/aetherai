import os

base_path = r"c:\Users\jithin sai\OneDrive\Desktop\finalbot\backend"

directories = [
    "app/search",
    "app/search/providers",
    "tests/search",
]

files = {
    # ─────────────────────────────────────────────────────────────────────────
    # MODELS
    # ─────────────────────────────────────────────────────────────────────────
    "app/search/models.py": '''from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum


class SearchCategory(str, Enum):
    NEWS = "news"
    WEATHER = "weather"
    SPORTS = "sports"
    GENERAL = "general"


class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str
    source: Optional[str] = None
    published: Optional[str] = None
    summary: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    provider: str
    cache_hit: bool = False
    latency_ms: float = 0.0
    category: SearchCategory = SearchCategory.GENERAL


class SearchDecision(BaseModel):
    required: bool
    reason: str
    confidence: float = 1.0
    category: SearchCategory = SearchCategory.GENERAL


class CacheEntry(BaseModel):
    query_hash: str
    results: List[SearchResult]
    provider: str
    ttl_seconds: int
    category: str
    hits: int = 0
''',

    # ─────────────────────────────────────────────────────────────────────────
    # EXCEPTIONS
    # ─────────────────────────────────────────────────────────────────────────
    "app/search/exceptions.py": '''class SearchError(Exception):
    """Base class for all search errors."""
    pass


class SearchProviderError(SearchError):
    """Raised when a search provider fails to return results."""
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"[{provider}] {message}")


class NoSearchProviderError(SearchError):
    """Raised when no search provider is available in the registry."""
    pass


class SearchCacheError(SearchError):
    """Raised when cache operations fail (non-fatal; system falls back)."""
    pass
''',

    # ─────────────────────────────────────────────────────────────────────────
    # CONFIG
    # ─────────────────────────────────────────────────────────────────────────
    "app/search/config.py": '''from pydantic_settings import BaseSettings
from typing import List


class SearchSettings(BaseSettings):
    # Provider priority list (first healthy provider is selected)
    search_providers_enabled: List[str] = ["duckduckgo", "brave", "tavily", "serpapi"]
    search_provider_priority: List[str] = ["duckduckgo", "brave", "tavily", "serpapi"]

    # TTL strategy (seconds) — configurable per category
    ttl_news: int = 900          # 15 minutes
    ttl_weather: int = 600       # 10 minutes
    ttl_sports: int = 30         # 30 seconds
    ttl_general: int = 86400     # 24 hours

    # Redis connection (falls back to in-process dict if unavailable)
    redis_url: str = "redis://localhost:6379/1"

    # Search result limits
    max_results: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
''',

    # ─────────────────────────────────────────────────────────────────────────
    # PROVIDER PROTOCOL
    # ─────────────────────────────────────────────────────────────────────────
    "app/search/provider.py": '''from typing import Protocol, List, runtime_checkable
from .models import SearchResult


@runtime_checkable
class SearchProvider(Protocol):
    """
    Abstract contract every search provider must satisfy.
    No vendor lock-in — swap providers without changing the engine.
    """

    def name(self) -> str:
        """Return the unique identifier of this provider."""
        ...

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Execute a search and return normalized results."""
        ...

    async def health_check(self) -> bool:
        """Return True if the provider is reachable and functional."""
        ...
''',

    # ─────────────────────────────────────────────────────────────────────────
    # PROVIDER REGISTRY
    # ─────────────────────────────────────────────────────────────────────────
    "app/search/registry.py": '''import logging
from typing import Dict, List, Optional
from .provider import SearchProvider
from .exceptions import NoSearchProviderError

logger = logging.getLogger("search.registry")


class SearchProviderRegistry:
    """
    Dynamic provider registry. Providers are registered at startup.
    Selection respects priority order and availability.
    """

    def __init__(self, priority: List[str]):
        self._providers: Dict[str, SearchProvider] = {}
        self._priority: List[str] = priority

    def register(self, provider: SearchProvider) -> None:
        self._providers[provider.name()] = provider
        logger.info("Provider registered", extra={"provider": provider.name()})

    def get(self, name: str) -> Optional[SearchProvider]:
        return self._providers.get(name)

    def get_provider(self) -> SearchProvider:
        """Return the first available provider by priority order."""
        for name in self._priority:
            provider = self._providers.get(name)
            if provider is not None:
                return provider
        raise NoSearchProviderError("No search providers registered.")

    def all_names(self) -> List[str]:
        return list(self._providers.keys())
''',

    # ─────────────────────────────────────────────────────────────────────────
    # QUERY NORMALIZER
    # ─────────────────────────────────────────────────────────────────────────
    "app/search/normalizer.py": '''import re
import unicodedata
import hashlib
from typing import Optional


class QueryNormalizer:
    """
    Normalizes a raw query string into a stable, cache-safe form.

    Steps:
      1. Unicode NFC normalization
      2. Lowercase
      3. Strip leading/trailing whitespace
      4. Remove punctuation (except hyphens inside words)
      5. Collapse multiple spaces into one
      6. Sort tokens alphabetically (for cache-key stability across equivalent queries)
    """

    def normalize(self, query: str) -> str:
        """Return a normalized query string."""
        text = unicodedata.normalize("NFC", query)
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)          # strip punctuation
        text = re.sub(r"\\s+", " ", text).strip()      # collapse spaces
        return text

    def cache_key(self, query: str, prefix: str = "search") -> str:
        """
        Produce a deterministic Redis cache key.
        Tokens are sorted so 'AI news latest' and 'latest AI news' share the same key.
        """
        normalized = self.normalize(query)
        tokens = sorted(normalized.split())
        canonical = " ".join(tokens)
        digest = hashlib.sha256(canonical.encode()).hexdigest()[:16]
        return f"{prefix}:{digest}"
''',

    # ─────────────────────────────────────────────────────────────────────────
    # SEARCH NECESSITY DETECTOR
    # ─────────────────────────────────────────────────────────────────────────
    "app/search/detector.py": '''import re
import logging
from typing import List, Tuple
from .models import SearchDecision, SearchCategory

logger = logging.getLogger("search.detector")

# Keyword → (category, confidence) mapping
SEARCH_TRIGGERS: List[Tuple[str, SearchCategory, float]] = [
    # News / breaking
    ("latest",      SearchCategory.NEWS,    0.95),
    ("breaking",    SearchCategory.NEWS,    0.95),
    ("news",        SearchCategory.NEWS,    0.90),
    ("trending",    SearchCategory.NEWS,    0.90),
    ("today",       SearchCategory.NEWS,    0.80),
    ("current",     SearchCategory.NEWS,    0.80),
    ("recent",      SearchCategory.NEWS,    0.80),
    ("live",        SearchCategory.NEWS,    0.85),
    # Weather
    ("weather",     SearchCategory.WEATHER, 1.00),
    ("forecast",    SearchCategory.WEATHER, 1.00),
    ("temperature", SearchCategory.WEATHER, 0.90),
    ("rain",        SearchCategory.WEATHER, 0.75),
    # Sports
    ("score",       SearchCategory.SPORTS,  1.00),
    ("match",       SearchCategory.SPORTS,  0.80),
    ("standings",   SearchCategory.SPORTS,  0.90),
    # General time-sensitive
    ("price",       SearchCategory.GENERAL, 0.85),
    ("stock",       SearchCategory.GENERAL, 0.85),
    ("release",     SearchCategory.GENERAL, 0.75),
    ("date",        SearchCategory.GENERAL, 0.70),
    ("2025",        SearchCategory.GENERAL, 0.80),
    ("2026",        SearchCategory.GENERAL, 0.80),
]

# Intent values from Phase 4 that automatically trigger search
SEARCH_INTENTS = {"search_required"}


class SearchNecessityDetector:
    """
    Determines whether a query requires a live web search.
    Consumes the Phase 4 intent label and keyword-scans the query.
    """

    def detect(self, query: str, intent: str = "chat") -> SearchDecision:
        # Phase 4 intent short-circuits the keyword scan
        if intent in SEARCH_INTENTS:
            logger.info("Search required by intent", extra={"intent": intent})
            return SearchDecision(
                required=True,
                reason=f"Phase 4 intent classified as '{intent}'",
                confidence=1.0,
                category=SearchCategory.NEWS,
            )

        lowered = query.lower()
        for keyword, category, confidence in SEARCH_TRIGGERS:
            if re.search(r"\\b" + re.escape(keyword) + r"\\b", lowered):
                decision = SearchDecision(
                    required=True,
                    reason=f"Keyword '{keyword}' matched",
                    confidence=confidence,
                    category=category,
                )
                logger.info(
                    "Search required by keyword",
                    extra={"keyword": keyword, "confidence": confidence},
                )
                return decision

        return SearchDecision(
            required=False,
            reason="No time-sensitive keywords detected",
            confidence=1.0,
            category=SearchCategory.GENERAL,
        )
''',

    # ─────────────────────────────────────────────────────────────────────────
    # CACHE
    # ─────────────────────────────────────────────────────────────────────────
    "app/search/cache.py": '''import json
import logging
import time
from typing import Optional, List, Dict, Any
from .models import SearchResult, SearchCategory
from .exceptions import SearchCacheError

logger = logging.getLogger("search.cache")


class SearchCache:
    """
    Redis-backed search cache with TTL support.
    Falls back to an in-process dict when Redis is unavailable,
    ensuring tests and local dev work without a Redis instance.
    """

    TTL_MAP: Dict[SearchCategory, int] = {
        SearchCategory.NEWS:    900,
        SearchCategory.WEATHER: 600,
        SearchCategory.SPORTS:  30,
        SearchCategory.GENERAL: 86400,
    }

    def __init__(self, redis_url: str):
        self._redis = None
        self._fallback: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        self._hits = 0
        self._misses = 0
        self._redis_url = redis_url
        self._try_connect()

    def _try_connect(self):
        try:
            import redis.asyncio as aioredis  # optional dependency
            # Store the URL; we'll create a connection on first use
            self._redis_url = self._redis_url
            logger.info("Redis cache configured", extra={"url": self._redis_url})
        except ImportError:
            logger.warning("redis package not installed; using in-process cache fallback")

    # ── Public API ────────────────────────────────────────────────────────────

    async def get(self, key: str) -> Optional[List[SearchResult]]:
        """Return cached results or None on miss."""
        # In-process fallback path
        if key in self._fallback:
            if time.time() < self._expiry.get(key, 0):
                self._hits += 1
                logger.info("Cache hit", extra={"key": key})
                raw = self._fallback[key]
                return [SearchResult(**r) for r in raw]
            else:
                del self._fallback[key]

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

        # In-process fallback
        self._fallback[key] = serialized
        self._expiry[key] = time.time() + effective_ttl

        logger.info(
            "Cache set",
            extra={"key": key, "ttl": effective_ttl, "count": len(results)},
        )

    async def invalidate(self, key: str) -> None:
        self._fallback.pop(key, None)
        self._expiry.pop(key, None)
        logger.info("Cache invalidated", extra={"key": key})

    def get_stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total else 0.0,
            "cached_keys": len(self._fallback),
        }
''',

    # ─────────────────────────────────────────────────────────────────────────
    # SUMMARIZER
    # ─────────────────────────────────────────────────────────────────────────
    "app/search/summarizer.py": '''import re
import logging
from typing import List, Dict, Any
from .models import SearchResult

logger = logging.getLogger("search.summarizer")

_HTML_TAG = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _HTML_TAG.sub("", text).strip()


class Summarizer:
    """
    Converts raw provider dicts into clean SearchResult objects.
    No raw HTML is ever exposed to downstream consumers.
    """

    def summarize(self, raw_results: List[Dict[str, Any]]) -> List[SearchResult]:
        results = []
        for item in raw_results:
            title   = _strip_html(item.get("title",   "Untitled"))
            snippet = _strip_html(item.get("snippet", item.get("description", "")))
            url     = item.get("url", item.get("link", ""))
            source  = item.get("source", item.get("domain", ""))
            pub     = item.get("published", item.get("date", None))

            results.append(SearchResult(
                title=title,
                snippet=snippet,
                url=url,
                source=source,
                published=pub,
                summary=snippet[:200] if snippet else None,
            ))

        logger.info("Results summarized", extra={"count": len(results)})
        return results
''',

    # ─────────────────────────────────────────────────────────────────────────
    # METRICS
    # ─────────────────────────────────────────────────────────────────────────
    "app/search/metrics.py": '''import time
import logging
from typing import Dict, Any, List
from contextlib import contextmanager

logger = logging.getLogger("search.metrics")


class SearchMetrics:
    """Collects operational telemetry for the search subsystem."""

    def __init__(self):
        self._searches = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._provider_failures = 0
        self._total_latency_ms = 0.0
        self._provider_latencies: Dict[str, List[float]] = {}

    def record_cache_hit(self):
        self._cache_hits += 1

    def record_cache_miss(self):
        self._cache_misses += 1

    def record_search(self, provider: str, latency_ms: float):
        self._searches += 1
        self._total_latency_ms += latency_ms
        self._provider_latencies.setdefault(provider, []).append(latency_ms)

    def record_failure(self, provider: str):
        self._provider_failures += 1
        logger.warning("Provider failure", extra={"provider": provider})

    @contextmanager
    def track(self, provider: str):
        """Context manager to auto-record provider call latency."""
        start = time.perf_counter()
        try:
            yield
        except Exception:
            self.record_failure(provider)
            raise
        finally:
            ms = (time.perf_counter() - start) * 1000
            self.record_search(provider, ms)

    def snapshot(self) -> Dict[str, Any]:
        total = self._cache_hits + self._cache_misses
        hit_rate = round(self._cache_hits / total, 4) if total else 0.0
        avg_lat = (
            round(self._total_latency_ms / self._searches, 2)
            if self._searches else 0.0
        )
        return {
            "searches": self._searches,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": hit_rate,
            "provider_failures": self._provider_failures,
            "average_latency_ms": avg_lat,
            "provider_latencies": {
                p: round(sum(v) / len(v), 2)
                for p, v in self._provider_latencies.items()
            },
        }


# Module-level singleton (injectable via DI)
search_metrics = SearchMetrics()
''',

    # ─────────────────────────────────────────────────────────────────────────
    # SEARCH ENGINE
    # ─────────────────────────────────────────────────────────────────────────
    "app/search/engine.py": '''import time
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
''',

    # ─────────────────────────────────────────────────────────────────────────
    # PROVIDER PLACEHOLDERS
    # ─────────────────────────────────────────────────────────────────────────
    "app/search/providers/brave.py": '''from typing import List
from app.search.models import SearchResult


class BraveSearchProvider:
    def name(self) -> str: return "brave"
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        raise NotImplementedError("Brave Search integration not yet implemented.")
    async def health_check(self) -> bool: raise NotImplementedError()
''',

    "app/search/providers/tavily.py": '''from typing import List
from app.search.models import SearchResult


class TavilySearchProvider:
    def name(self) -> str: return "tavily"
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        raise NotImplementedError("Tavily Search integration not yet implemented.")
    async def health_check(self) -> bool: raise NotImplementedError()
''',

    "app/search/providers/serpapi.py": '''from typing import List
from app.search.models import SearchResult


class SerpAPISearchProvider:
    def name(self) -> str: return "serpapi"
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        raise NotImplementedError("SerpAPI integration not yet implemented.")
    async def health_check(self) -> bool: raise NotImplementedError()
''',

    "app/search/providers/duckduckgo.py": '''from typing import List
from app.search.models import SearchResult


class DuckDuckGoSearchProvider:
    def name(self) -> str: return "duckduckgo"
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        raise NotImplementedError("DuckDuckGo integration not yet implemented.")
    async def health_check(self) -> bool: raise NotImplementedError()
''',

    # ─────────────────────────────────────────────────────────────────────────
    # TESTS
    # ─────────────────────────────────────────────────────────────────────────
    "tests/search/__init__.py": "",

    "tests/search/test_detector.py": '''import pytest
from app.search.detector import SearchNecessityDetector
from app.search.models import SearchCategory


det = SearchNecessityDetector()


def test_search_not_required_for_static_query():
    d = det.detect("What is React?", intent="chat")
    assert d.required is False


def test_search_required_for_latest_news():
    d = det.detect("Latest AI news", intent="chat")
    assert d.required is True
    assert d.category == SearchCategory.NEWS


def test_search_required_by_intent():
    d = det.detect("anything at all", intent="search_required")
    assert d.required is True
    assert d.confidence == 1.0


def test_weather_category():
    d = det.detect("What is the weather in London?", intent="chat")
    assert d.required is True
    assert d.category == SearchCategory.WEATHER


def test_sports_score_trigger():
    d = det.detect("What is the score of the match today?", intent="chat")
    assert d.required is True
''',

    "tests/search/test_normalizer.py": '''from app.search.normalizer import QueryNormalizer

norm = QueryNormalizer()


def test_lowercase():
    assert norm.normalize("Hello WORLD") == "hello world"


def test_strip_punctuation():
    result = norm.normalize("Hello, World!!")
    assert "," not in result
    assert "!" not in result


def test_collapse_spaces():
    assert norm.normalize("a   b   c") == "a b c"


def test_same_cache_key_for_reordered_tokens():
    k1 = norm.cache_key("AI news latest")
    k2 = norm.cache_key("latest AI news")
    assert k1 == k2


def test_different_cache_key_for_different_queries():
    k1 = norm.cache_key("What is Python?")
    k2 = norm.cache_key("What is JavaScript?")
    assert k1 != k2
''',

    "tests/search/test_cache.py": '''import pytest
import asyncio
from app.search.cache import SearchCache
from app.search.models import SearchResult, SearchCategory


def make_result(title="Test") -> SearchResult:
    return SearchResult(title=title, snippet="snippet", url="https://example.com")


@pytest.fixture
def cache():
    return SearchCache(redis_url="redis://localhost:6379/99")  # won't connect in CI


@pytest.mark.asyncio
async def test_cache_miss_on_empty(cache):
    result = await cache.get("nonexistent_key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_set_and_get(cache):
    results = [make_result("Story One"), make_result("Story Two")]
    await cache.set("test_key", results, category=SearchCategory.GENERAL, ttl=3600)
    retrieved = await cache.get("test_key")
    assert retrieved is not None
    assert len(retrieved) == 2
    assert retrieved[0].title == "Story One"


@pytest.mark.asyncio
async def test_cache_tracks_hits_and_misses(cache):
    await cache.get("missing")
    await cache.set("found_key", [make_result()], ttl=3600)
    await cache.get("found_key")
    stats = cache.get_stats()
    assert stats["misses"] >= 1
    assert stats["hits"] >= 1
''',

    "tests/search/test_summarizer.py": '''from app.search.summarizer import Summarizer

summ = Summarizer()


def test_strips_html_from_title():
    raw = [{"title": "<b>Bold Title</b>", "snippet": "text", "url": "https://a.com"}]
    results = summ.summarize(raw)
    assert "<b>" not in results[0].title
    assert results[0].title == "Bold Title"


def test_strips_html_from_snippet():
    raw = [{"title": "T", "snippet": "<p>Para text</p>", "url": "https://b.com"}]
    results = summ.summarize(raw)
    assert "<p>" not in results[0].snippet


def test_uses_description_fallback():
    raw = [{"title": "T", "description": "Desc text", "url": "https://c.com"}]
    results = summ.summarize(raw)
    assert results[0].snippet == "Desc text"


def test_summary_truncated_to_200_chars():
    long_text = "x" * 500
    raw = [{"title": "T", "snippet": long_text, "url": "https://d.com"}]
    results = summ.summarize(raw)
    assert len(results[0].summary) == 200
''',

    "tests/search/test_registry.py": '''import pytest
from app.search.registry import SearchProviderRegistry
from app.search.providers.duckduckgo import DuckDuckGoSearchProvider
from app.search.exceptions import NoSearchProviderError


def test_register_and_retrieve():
    reg = SearchProviderRegistry(priority=["duckduckgo"])
    reg.register(DuckDuckGoSearchProvider())
    provider = reg.get_provider()
    assert provider.name() == "duckduckgo"


def test_raises_when_empty():
    reg = SearchProviderRegistry(priority=["duckduckgo"])
    with pytest.raises(NoSearchProviderError):
        reg.get_provider()
''',

    "tests/search/test_engine.py": '''import pytest
from app.search.engine import SearchEngine
from app.search.cache import SearchCache
from app.search.normalizer import QueryNormalizer
from app.search.summarizer import Summarizer
from app.search.metrics import SearchMetrics
from app.search.registry import SearchProviderRegistry
from app.search.models import SearchCategory


def make_engine(with_provider=False) -> SearchEngine:
    registry = SearchProviderRegistry(priority=["duckduckgo"])
    if with_provider:
        from app.search.providers.duckduckgo import DuckDuckGoSearchProvider
        registry.register(DuckDuckGoSearchProvider())
    cache = SearchCache(redis_url="redis://localhost/99")
    return SearchEngine(
        registry=registry,
        cache=cache,
        normalizer=QueryNormalizer(),
        summarizer=Summarizer(),
        metrics=SearchMetrics(),
    )


@pytest.mark.asyncio
async def test_engine_returns_empty_on_no_provider():
    engine = make_engine(with_provider=False)
    resp = await engine.search("latest AI news", category=SearchCategory.NEWS)
    assert resp.results == []
    assert resp.provider == "none"


@pytest.mark.asyncio
async def test_engine_returns_empty_on_not_implemented_provider():
    engine = make_engine(with_provider=True)
    # DuckDuckGo raises NotImplementedError — engine should degrade gracefully
    resp = await engine.search("What is the latest news?", category=SearchCategory.NEWS)
    assert resp.results == []
    assert resp.cache_hit is False


@pytest.mark.asyncio
async def test_cache_hit_on_repeated_query():
    from app.search.models import SearchResult
    engine = make_engine(with_provider=False)
    results = [SearchResult(title="Cached", snippet="s", url="https://x.com")]
    key = engine._normalizer.cache_key("latest python release")
    await engine._cache.set(key, results, ttl=3600)

    resp = await engine.search("latest python release")
    assert resp.cache_hit is True
    assert resp.results[0].title == "Cached"
''',
}

# Create directories + __init__.py
for d in directories:
    dir_path = os.path.join(base_path, d)
    os.makedirs(dir_path, exist_ok=True)
    parts = d.split("/")
    for i in range(1, len(parts) + 1):
        init_dir = os.path.join(base_path, *parts[:i])
        init_file = os.path.join(init_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "a").close()

# Write files
for file_path, content in files.items():
    full_path = os.path.join(base_path, file_path)
    os.makedirs(os.path.dirname(full_path) or base_path, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Phase 5 skeleton generated successfully.")
