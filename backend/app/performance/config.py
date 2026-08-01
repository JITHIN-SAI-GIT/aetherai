import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PerformanceConfig:
    """
    All performance tuning thresholds loaded from environment variables.
    Change behavior through env, never through code edits.
    """
    # Connection pool
    max_connections: int = int(os.getenv("PERF_MAX_CONNECTIONS", "100"))
    max_keepalive: int = int(os.getenv("PERF_MAX_KEEPALIVE", "20"))
    keepalive_expiry: float = float(os.getenv("PERF_KEEPALIVE_EXPIRY", "30.0"))
    http2_enabled: bool = os.getenv("PERF_HTTP2", "true").lower() == "true"

    # Request timeouts (seconds)
    connect_timeout: float = float(os.getenv("PERF_CONNECT_TIMEOUT", "5.0"))
    read_timeout: float = float(os.getenv("PERF_READ_TIMEOUT", "30.0"))
    write_timeout: float = float(os.getenv("PERF_WRITE_TIMEOUT", "10.0"))
    pool_timeout: float = float(os.getenv("PERF_POOL_TIMEOUT", "5.0"))

    # Slow request thresholds (ms)
    slow_request_ms: float = float(os.getenv("PERF_SLOW_REQUEST_MS", "2000.0"))
    slow_stage_ms: float = float(os.getenv("PERF_SLOW_STAGE_MS", "500.0"))
    ttfb_target_ms: float = float(os.getenv("PERF_TTFB_TARGET_MS", "200.0"))

    # Streaming
    stream_chunk_buffer: int = int(os.getenv("PERF_STREAM_CHUNK_BUFFER", "4"))
    stream_flush_interval_ms: float = float(os.getenv("PERF_STREAM_FLUSH_MS", "50.0"))

    # Cache
    metadata_cache_ttl_secs: int = int(os.getenv("PERF_META_CACHE_TTL", "300"))
    model_list_cache_ttl_secs: int = int(os.getenv("PERF_MODEL_CACHE_TTL", "600"))

    # Batching dedup window
    dedup_window_ms: float = float(os.getenv("PERF_DEDUP_WINDOW_MS", "50.0"))

    # Latency tracker rolling window
    latency_window_size: int = int(os.getenv("PERF_LATENCY_WINDOW", "1000"))

    # Load test
    load_test_base_url: str = os.getenv("PERF_LOAD_TEST_URL", "http://localhost:8000")
    load_test_timeout: float = float(os.getenv("PERF_LOAD_TEST_TIMEOUT", "10.0"))
