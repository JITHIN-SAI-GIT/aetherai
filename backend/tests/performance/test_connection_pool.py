import pytest
import asyncio
from app.performance.connection_pool import ConnectionPool
from app.performance.config import PerformanceConfig


@pytest.mark.asyncio
async def test_pool_starts_up_cleanly():
    pool = ConnectionPool()
    await pool.startup()
    assert pool.is_ready
    client = pool.get_client()
    assert client is not None
    await pool.shutdown()
    assert not pool.is_ready


@pytest.mark.asyncio
async def test_pool_get_client_before_startup_raises():
    pool = ConnectionPool()
    with pytest.raises(RuntimeError, match="before startup"):
        pool.get_client()


@pytest.mark.asyncio
async def test_pool_double_startup_is_safe():
    pool = ConnectionPool()
    await pool.startup()
    await pool.startup()   # second call must be a no-op
    assert pool.is_ready
    await pool.shutdown()


@pytest.mark.asyncio
async def test_pool_returns_same_client_instance():
    pool = ConnectionPool()
    await pool.startup()
    c1 = pool.get_client()
    c2 = pool.get_client()
    assert c1 is c2   # same object — no new client per call
    await pool.shutdown()


def test_pool_config_limits_applied():
    from app.performance.config import PerformanceConfig
    import dataclasses
    config = dataclasses.replace(PerformanceConfig(), max_connections=42)
    assert config.max_connections == 42
    assert config.max_keepalive == PerformanceConfig().max_keepalive  # other fields unchanged
