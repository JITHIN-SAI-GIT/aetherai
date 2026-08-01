import time
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
