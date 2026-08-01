import time
import threading
from collections import deque
from typing import Dict, Any, Deque, Optional


class PerformanceMetrics:
    """
    Injectable performance telemetry collector.
    Thread-safe under CPython GIL. All methods are safe to call from async context.
    Never instantiated as a module-level global — always injected by the DI container.
    """

    def __init__(self, window_size: int = 1000):
        self._window = window_size
        self._lock = threading.Lock()

        # Rolling windows per stage (stage_name -> deque of ms values)
        self._stage_latencies: Dict[str, Deque[float]] = {}

        # Request counters
        self._total_requests: int = 0
        self._slow_requests: int = 0
        self._concurrent: int = 0
        self._peak_concurrent: int = 0

        # TTFB samples
        self._ttfb_samples: Deque[float] = deque(maxlen=window_size)

        # Provider latency
        self._provider_latencies: Deque[float] = deque(maxlen=window_size)

        # Streaming latency (first token)
        self._stream_ttfb: Deque[float] = deque(maxlen=window_size)

        # Cache stats
        self._cache_hits: int = 0
        self._cache_misses: int = 0

    # ── Stage timing ─────────────────────────────────────────────────────────

    def record_stage(self, stage: str, duration_ms: float) -> None:
        with self._lock:
            if stage not in self._stage_latencies:
                self._stage_latencies[stage] = deque(maxlen=self._window)
            self._stage_latencies[stage].append(duration_ms)

    # ── Request lifecycle ────────────────────────────────────────────────────

    def request_started(self) -> None:
        with self._lock:
            self._total_requests += 1
            self._concurrent += 1
            if self._concurrent > self._peak_concurrent:
                self._peak_concurrent = self._concurrent

    def request_finished(self, total_ms: float, slow_threshold_ms: float = 2000.0) -> None:
        with self._lock:
            self._concurrent = max(0, self._concurrent - 1)
            if total_ms > slow_threshold_ms:
                self._slow_requests += 1

    # ── TTFB ─────────────────────────────────────────────────────────────────

    def record_ttfb(self, ms: float) -> None:
        with self._lock:
            self._ttfb_samples.append(ms)

    def record_stream_ttfb(self, ms: float) -> None:
        with self._lock:
            self._stream_ttfb.append(ms)

    # ── Provider ─────────────────────────────────────────────────────────────

    def record_provider_latency(self, ms: float) -> None:
        with self._lock:
            self._provider_latencies.append(ms)

    # ── Cache ─────────────────────────────────────────────────────────────────

    def record_cache_hit(self) -> None:
        with self._lock:
            self._cache_hits += 1

    def record_cache_miss(self) -> None:
        with self._lock:
            self._cache_misses += 1

    # ── Snapshot ──────────────────────────────────────────────────────────────

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            stage_stats = {}
            for name, samples in self._stage_latencies.items():
                stage_stats[name] = _percentiles(list(samples))

            total_cache = self._cache_hits + self._cache_misses
            cache_hit_rate = round(self._cache_hits / max(total_cache, 1), 4)

            return {
                "total_requests": self._total_requests,
                "slow_requests": self._slow_requests,
                "concurrent_requests": self._concurrent,
                "peak_concurrent": self._peak_concurrent,
                "ttfb": _percentiles(list(self._ttfb_samples)),
                "stream_ttfb": _percentiles(list(self._stream_ttfb)),
                "provider_latency": _percentiles(list(self._provider_latencies)),
                "cache_hit_rate": cache_hit_rate,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "pipeline_stages": stage_stats,
            }


def _percentiles(samples: list) -> Dict[str, Optional[float]]:
    """Compute P50, P95, P99 from a list of float samples."""
    if not samples:
        return {"p50": None, "p95": None, "p99": None, "avg": None, "count": 0}
    s = sorted(samples)
    n = len(s)
    return {
        "p50": round(s[int(n * 0.50)], 3),
        "p95": round(s[min(int(n * 0.95), n - 1)], 3),
        "p99": round(s[min(int(n * 0.99), n - 1)], 3),
        "avg": round(sum(s) / n, 3),
        "count": n,
    }
