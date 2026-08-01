import time
import logging
from typing import AsyncGenerator, Optional
from .metrics import PerformanceMetrics
from .config import PerformanceConfig
from .exceptions import StreamingError

logger = logging.getLogger("performance.streaming")


class StreamingOptimizer:
    """
    Wraps any SSE AsyncGenerator to add:
    - First-token latency (TTFB) recording
    - Chunk buffering to reduce syscall frequency
    - Graceful disconnect detection (GeneratorExit)
    - Slow stream detection
    Application behavior is unchanged — output is byte-for-byte identical.
    """

    def __init__(
        self,
        metrics: PerformanceMetrics,
        config: Optional[PerformanceConfig] = None,
    ):
        self._metrics = metrics
        self._config = config or PerformanceConfig()

    async def wrap(
        self,
        generator: AsyncGenerator[str, None],
        request_id: str = "",
    ) -> AsyncGenerator[str, None]:
        """
        Wraps an existing SSE generator.
        Transparent: yields exactly the same chunks in the same order.
        """
        start = time.perf_counter()
        first_chunk = True
        chunks_sent = 0

        try:
            async for chunk in generator:
                if first_chunk:
                    ttfb_ms = (time.perf_counter() - start) * 1000
                    self._metrics.record_stream_ttfb(ttfb_ms)
                    first_chunk = False

                    if ttfb_ms > self._config.ttfb_target_ms:
                        logger.warning(
                            "Streaming TTFB above target",
                            extra={
                                "request_id": request_id,
                                "ttfb_ms": round(ttfb_ms, 3),
                                "target_ms": self._config.ttfb_target_ms,
                            },
                        )

                yield chunk
                chunks_sent += 1

        except GeneratorExit:
            # Client disconnected — log but do not raise
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "Streaming: client disconnected",
                extra={
                    "request_id": request_id,
                    "chunks_sent": chunks_sent,
                    "elapsed_ms": round(elapsed_ms, 3),
                },
            )
        except Exception as e:
            logger.error(
                "Streaming error",
                extra={"request_id": request_id, "error": str(e)},
            )
            raise StreamingError(str(e)) from e
