import time
import logging
from contextlib import contextmanager
from typing import Optional
from .metrics import PerformanceMetrics
from .config import PerformanceConfig

logger = logging.getLogger("performance.profiler")


class RequestProfiler:
    """
    Per-request profiling context manager.
    Records TTFB and total latency into PerformanceMetrics.
    Logs slow requests with structured output — never logs content.
    Injected; no module-level state.
    """

    def __init__(
        self,
        metrics: PerformanceMetrics,
        config: Optional[PerformanceConfig] = None,
    ):
        self._metrics = metrics
        self._config = config or PerformanceConfig()

    @contextmanager
    def profile(self, request_id: str = "", endpoint: str = ""):
        """
        Usage:
            with profiler.profile(request_id="abc", endpoint="/v1/chat/completions"):
                response = await handler()
        """
        self._metrics.request_started()
        start = time.perf_counter()
        ttfb_recorded = False

        def record_ttfb():
            nonlocal ttfb_recorded
            if not ttfb_recorded:
                ms = (time.perf_counter() - start) * 1000
                self._metrics.record_ttfb(ms)
                ttfb_recorded = True
                return ms
            return 0.0

        try:
            yield record_ttfb
        finally:
            total_ms = (time.perf_counter() - start) * 1000
            self._metrics.request_finished(total_ms, self._config.slow_request_ms)

            if total_ms > self._config.slow_request_ms:
                logger.warning(
                    "Slow request",
                    extra={
                        "request_id": request_id,
                        "endpoint": endpoint,
                        "total_ms": round(total_ms, 3),
                    },
                )
            else:
                logger.debug(
                    "Request complete",
                    extra={
                        "request_id": request_id,
                        "endpoint": endpoint,
                        "total_ms": round(total_ms, 3),
                    },
                )
