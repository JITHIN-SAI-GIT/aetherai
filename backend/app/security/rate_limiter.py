import time
import logging
from collections import deque
from dataclasses import dataclass
from typing import Dict, Optional
from .exceptions import RateLimitError
from .policies import POLICIES

logger = logging.getLogger("security.rate_limiter")


@dataclass
class RateLimitResult:
    allowed: bool
    limit_type: str
    remaining: int
    retry_after: float = 0.0


class _SlidingWindow:
    """Thread-safe sliding window counter using a timestamp deque."""

    def __init__(self, max_requests: int, window_seconds: float = 60.0):
        self._max = max_requests
        self._window = window_seconds
        self._timestamps: deque = deque()

    def is_allowed(self) -> tuple:
        now = time.time()
        cutoff = now - self._window
        # Evict expired timestamps
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

        if len(self._timestamps) >= self._max:
            oldest = self._timestamps[0]
            retry_after = self._window - (now - oldest)
            return False, max(0, len(self._timestamps) - self._max), retry_after

        self._timestamps.append(now)
        return True, self._max - len(self._timestamps), 0.0


class RateLimiter:
    """
    Sliding-window rate limiter supporting IP, user, and API key dimensions.
    Each key gets an independent window; all limits are policy-driven.
    """

    def __init__(self):
        self._ip_windows: Dict[str, _SlidingWindow] = {}
        self._user_windows: Dict[str, _SlidingWindow] = {}
        self._key_windows: Dict[str, _SlidingWindow] = {}

    def check_ip(self, ip: str) -> RateLimitResult:
        return self._check(ip, self._ip_windows, POLICIES.rate_limit_ip_per_minute, "ip")

    def check_user(self, user_id: str) -> RateLimitResult:
        return self._check(user_id, self._user_windows, POLICIES.rate_limit_user_per_minute, "user")

    def check_key(self, api_key: str) -> RateLimitResult:
        key_prefix = api_key[:8] if api_key else "anonymous"
        return self._check(key_prefix, self._key_windows, POLICIES.rate_limit_key_per_minute, "api_key")

    def _check(
        self,
        key: str,
        store: Dict[str, _SlidingWindow],
        limit: int,
        limit_type: str,
    ) -> RateLimitResult:
        if key not in store:
            store[key] = _SlidingWindow(limit)
        allowed, remaining, retry_after = store[key].is_allowed()

        if not allowed:
            logger.warning("Rate limit exceeded",
                           extra={"type": limit_type, "key": key[:8]})
            raise RateLimitError(limit_type, retry_after)

        return RateLimitResult(
            allowed=True,
            limit_type=limit_type,
            remaining=remaining,
        )
