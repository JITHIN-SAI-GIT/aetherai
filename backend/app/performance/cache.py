import time
import logging
from typing import Any, Optional, Dict, Callable
from .metrics import PerformanceMetrics
from .config import PerformanceConfig

logger = logging.getLogger("performance.cache")


class PerformanceCache:
    """
    Wraps any dict-based cache with:
    - Hit/miss telemetry recorded into PerformanceMetrics
    - TTL enforcement (lazy eviction on access)
    - Metadata slot for model lists and provider info
    The underlying cache is application-owned — this class adds no storage of its own.
    """

    def __init__(
        self,
        metrics: PerformanceMetrics,
        config: Optional[PerformanceConfig] = None,
    ):
        self._metrics = metrics
        self._config = config or PerformanceConfig()
        # Internal TTL store: key -> (value, expires_at)
        self._store: Dict[str, tuple] = {}

    def get(self, key: str) -> Optional[Any]:
        """Returns cached value or None on miss/expiry."""
        entry = self._store.get(key)
        if entry is None:
            self._metrics.record_cache_miss()
            return None
        value, expires_at = entry
        if expires_at is not None and time.monotonic() > expires_at:
            del self._store[key]
            self._metrics.record_cache_miss()
            return None
        self._metrics.record_cache_hit()
        return value

    def set(self, key: str, value: Any, ttl_secs: Optional[int] = None) -> None:
        """Store value with optional TTL (seconds). None means no expiry."""
        expires_at = (time.monotonic() + ttl_secs) if ttl_secs is not None else None
        self._store[key] = (value, expires_at)

    def get_or_set(self, key: str, factory: Callable[[], Any], ttl_secs: Optional[int] = None) -> Any:
        """Return cached value or call factory(), store, and return its result."""
        val = self.get(key)
        if val is None:
            val = factory()
            self.set(key, val, ttl_secs)
        return val

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> int:
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)

    def compact(self) -> int:
        """Evict all expired entries. Returns count of evicted entries."""
        now = time.monotonic()
        expired = [
            k for k, (_, exp) in self._store.items()
            if exp is not None and now > exp
        ]
        for k in expired:
            del self._store[k]
        return len(expired)

    def size(self) -> int:
        return len(self._store)

    # ── Typed metadata helpers ────────────────────────────────────────────────

    def cache_model_list(self, provider: str, models: list) -> None:
        self.set(f"models:{provider}", models, ttl_secs=self._config.model_list_cache_ttl_secs)

    def get_model_list(self, provider: str) -> Optional[list]:
        return self.get(f"models:{provider}")

    def cache_provider_metadata(self, provider: str, meta: dict) -> None:
        self.set(f"meta:{provider}", meta, ttl_secs=self._config.metadata_cache_ttl_secs)

    def get_provider_metadata(self, provider: str) -> Optional[dict]:
        return self.get(f"meta:{provider}")
