import time
import logging
from typing import Optional, Dict, Any
import httpx
from .connection_pool import ConnectionPool
from .metrics import PerformanceMetrics
from .config import PerformanceConfig

logger = logging.getLogger("performance.http_client")


class PerformanceHTTPClient:
    """
    Thin wrapper around the shared ConnectionPool client.
    Adds per-request latency recording, timeout enforcement, and structured logging.
    Injected into any module that needs to make HTTP calls.
    NEVER creates its own httpx.AsyncClient.
    """

    def __init__(
        self,
        pool: ConnectionPool,
        metrics: PerformanceMetrics,
        config: Optional[PerformanceConfig] = None,
    ):
        self._pool = pool
        self._metrics = metrics
        self._config = config or PerformanceConfig()

    async def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        return await self._request("POST", url, json=json, headers=headers, **kwargs)

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        return await self._request("GET", url, headers=headers, **kwargs)

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        client = self._pool.get_client()
        start = time.perf_counter()
        try:
            response = await client.request(method, url, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._metrics.record_provider_latency(elapsed_ms)

            if elapsed_ms > self._config.slow_request_ms:
                logger.warning(
                    "Slow HTTP request",
                    extra={"method": method, "url": url, "duration_ms": elapsed_ms},
                )
            return response
        except httpx.TimeoutException as e:
            logger.error("HTTP timeout", extra={"method": method, "url": url})
            raise
        except httpx.PoolTimeout as e:
            logger.error("Connection pool exhausted", extra={"url": url})
            raise
