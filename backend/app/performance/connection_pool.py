import logging
import httpx
from typing import Optional
from .config import PerformanceConfig

logger = logging.getLogger("performance.connection_pool")


class ConnectionPool:
    """
    Manages the single shared httpx.AsyncClient for the entire application.
    Lifecycle is controlled by FastAPI's lifespan — startup() is called once
    at app start, shutdown() is called once at app stop.
    The same instance is distributed by the DI container.
    No module may instantiate its own httpx.AsyncClient outside this class.
    """

    def __init__(self, config: Optional[PerformanceConfig] = None):
        self._config = config or PerformanceConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self._started = False

    async def startup(self) -> None:
        """Called once during application startup. Creates the shared client."""
        if self._started:
            logger.warning("ConnectionPool.startup() called more than once — ignoring")
            return

        limits = httpx.Limits(
            max_connections=self._config.max_connections,
            max_keepalive_connections=self._config.max_keepalive,
            keepalive_expiry=self._config.keepalive_expiry,
        )
        timeout = httpx.Timeout(
            connect=self._config.connect_timeout,
            read=self._config.read_timeout,
            write=self._config.write_timeout,
            pool=self._config.pool_timeout,
        )
        self._client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            http2=self._config.http2_enabled,
            follow_redirects=True,
        )
        self._started = True
        logger.info(
            "ConnectionPool started",
            extra={
                "max_connections": self._config.max_connections,
                "max_keepalive": self._config.max_keepalive,
                "http2": self._config.http2_enabled,
            },
        )

    async def shutdown(self) -> None:
        """Called once during application shutdown. Cleanly closes all connections."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._started = False
            logger.info("ConnectionPool shut down — all connections closed")

    def get_client(self) -> httpx.AsyncClient:
        """
        Returns the shared client. Raises RuntimeError if called before startup().
        This enforces the invariant: no code may use the pool before it is ready.
        """
        if self._client is None:
            raise RuntimeError(
                "ConnectionPool.get_client() called before startup(). "
                "Ensure ConnectionPool.startup() is called in the application lifespan."
            )
        return self._client

    @property
    def is_ready(self) -> bool:
        return self._started and self._client is not None
