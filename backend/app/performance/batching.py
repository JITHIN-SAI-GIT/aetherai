import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Callable, Coroutine, Dict, Optional
from .config import PerformanceConfig

logger = logging.getLogger("performance.batching")


class RequestBatcher:
    """
    De-duplicates concurrent identical requests within a time window.
    When multiple async callers make the same request within dedup_window_ms,
    only one upstream call is made and the result is shared.
    This is most useful for search queries — prevents duplicate API calls.
    Application behavior is unchanged: all callers receive the same result.
    """

    def __init__(self, config: Optional[PerformanceConfig] = None):
        self._config = config or PerformanceConfig()
        # key -> asyncio.Future
        self._pending: Dict[str, asyncio.Future] = {}

    def _make_key(self, payload: Any) -> str:
        """Deterministic hash of the request payload."""
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    async def get_or_execute(
        self,
        payload: Any,
        factory: Callable[[], Coroutine],
    ) -> Any:
        """
        If an identical request (same payload hash) is already in-flight,
        wait for it and return its result.
        Otherwise, execute the factory coroutine and resolve all waiters.
        """
        key = self._make_key(payload)

        if key in self._pending:
            logger.debug("Request dedup hit", extra={"key": key})
            return await asyncio.shield(self._pending[key])

        loop = asyncio.get_event_loop()
        future: asyncio.Future = loop.create_future()
        self._pending[key] = future

        try:
            result = await factory()
            future.set_result(result)
            return result
        except Exception as e:
            future.set_exception(e)
            raise
        finally:
            # Hold the key briefly so late-arriving requests in the dedup window still hit
            await asyncio.sleep(self._config.dedup_window_ms / 1000.0)
            self._pending.pop(key, None)
