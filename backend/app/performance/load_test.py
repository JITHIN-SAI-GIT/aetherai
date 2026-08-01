import asyncio
import time
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from .config import PerformanceConfig
from .metrics import _percentiles

logger = logging.getLogger("performance.load_test")


@dataclass
class LoadTestResult:
    """Result from a single load test run."""
    concurrency: int
    total_requests: int
    successful: int
    failed: int
    duration_secs: float
    latencies_ms: List[float] = field(default_factory=list)

    @property
    def failure_rate(self) -> float:
        return round(self.failed / max(self.total_requests, 1), 4)

    @property
    def throughput_rps(self) -> float:
        return round(self.total_requests / max(self.duration_secs, 0.001), 2)

    def percentiles(self) -> Dict[str, Any]:
        return _percentiles(sorted(self.latencies_ms))

    def summary(self) -> Dict[str, Any]:
        return {
            "concurrency": self.concurrency,
            "total_requests": self.total_requests,
            "successful": self.successful,
            "failed": self.failed,
            "failure_rate": self.failure_rate,
            "throughput_rps": self.throughput_rps,
            "latency_ms": self.percentiles(),
            "duration_secs": round(self.duration_secs, 3),
        }


class LoadTester:
    """
    Async load testing utility. Uses asyncio.gather() — no external dependencies.
    Sends concurrent HTTP requests and measures throughput + latency distribution.
    Designed for internal use; does NOT depend on the application stack.
    The caller provides a coroutine factory function.
    """

    CONCURRENCY_LEVELS = [10, 25, 50, 100]

    def __init__(self, config: Optional[PerformanceConfig] = None):
        self._config = config or PerformanceConfig()

    async def run(
        self,
        coroutine_factory,
        concurrency: int,
        total_requests: Optional[int] = None,
    ) -> LoadTestResult:
        """
        Run `total_requests` requests with `concurrency` workers.
        `coroutine_factory` is called once per request — it must return an awaitable
        that resolves to a latency_ms float, or raises on failure.
        """
        if total_requests is None:
            total_requests = concurrency * 2  # default: 2 rounds per worker

        semaphore = asyncio.Semaphore(concurrency)
        latencies: List[float] = []
        failures: int = 0

        async def _one_request():
            nonlocal failures
            async with semaphore:
                start = time.perf_counter()
                try:
                    await coroutine_factory()
                    ms = (time.perf_counter() - start) * 1000
                    latencies.append(ms)
                except Exception as e:
                    failures += 1
                    logger.debug("Load test request failed", extra={"error": str(e)})

        suite_start = time.perf_counter()
        tasks = [asyncio.create_task(_one_request()) for _ in range(total_requests)]
        await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.perf_counter() - suite_start

        result = LoadTestResult(
            concurrency=concurrency,
            total_requests=total_requests,
            successful=len(latencies),
            failed=failures,
            duration_secs=duration,
            latencies_ms=latencies,
        )
        logger.info("Load test complete", extra=result.summary())
        return result

    async def run_all_levels(self, coroutine_factory) -> Dict[int, LoadTestResult]:
        """Run at each standard concurrency level and return a mapping."""
        results = {}
        for level in self.CONCURRENCY_LEVELS:
            logger.info(f"Load test: concurrency={level}")
            results[level] = await self.run(coroutine_factory, concurrency=level)
        return results
