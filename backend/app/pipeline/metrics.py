import time
import logging
from contextlib import contextmanager
from typing import Optional
from .context import PipelineContext

logger = logging.getLogger("pipeline.metrics")

# Module-level optional reference to PerformanceMetrics.
# Set by the DI container at startup via configure_metrics().
# This avoids a circular import while keeping the hook transparent.
_perf_metrics = None


def configure_metrics(metrics) -> None:
    """
    Called once by the DI container to wire PerformanceMetrics into track_stage().
    Every pipeline stage will automatically feed into performance telemetry.
    """
    global _perf_metrics
    _perf_metrics = metrics


@contextmanager
def track_stage(context: PipelineContext, stage_name: str):
    """
    Context manager that measures execution time of a named pipeline stage,
    writes the result (ms) into PipelineContext.timings, and additionally
    records into PerformanceMetrics when wired (transparent — no behavior change).
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        context.timings[stage_name] = round(elapsed_ms, 3)

        # Feed into performance telemetry (no-op if not wired)
        if _perf_metrics is not None:
            _perf_metrics.record_stage(stage_name, elapsed_ms)

        logger.info(
            "Stage complete",
            extra={
                "request_id": context.request_id,
                "stage": stage_name,
                "duration_ms": elapsed_ms,
            }
        )
