import time
import logging
from collections import deque
from typing import Dict, List, Optional, Any
from .metrics import PerformanceMetrics, _percentiles
from .config import PerformanceConfig

logger = logging.getLogger("performance.latency")


class LatencyTracker:
    """
    Reads PipelineContext.timings after every request and updates PerformanceMetrics.
    Also maintains a per-stage rolling window for bottleneck detection.
    Injected into pipeline; never reaches global state.
    """

    def __init__(
        self,
        metrics: PerformanceMetrics,
        config: Optional[PerformanceConfig] = None,
    ):
        self._metrics = metrics
        self._config = config or PerformanceConfig()

    def record_pipeline_timings(self, timings: Dict[str, float]) -> None:
        """
        Called after each pipeline run with PipelineContext.timings.
        Records every stage into PerformanceMetrics and logs slow stages.
        """
        for stage, duration_ms in timings.items():
            if stage == "total_pipeline":
                continue
            self._metrics.record_stage(stage, duration_ms)
            if duration_ms > self._config.slow_stage_ms:
                logger.warning(
                    "Slow pipeline stage",
                    extra={"stage": stage, "duration_ms": duration_ms},
                )

    def bottleneck_report(self) -> Dict[str, Any]:
        """Returns a snapshot of all stage latencies from PerformanceMetrics."""
        snap = self._metrics.snapshot()
        stages = snap.get("pipeline_stages", {})

        # Identify slowest stage
        slowest = None
        slowest_p95 = 0.0
        for name, stats in stages.items():
            p95 = stats.get("p95") or 0.0
            if p95 > slowest_p95:
                slowest_p95 = p95
                slowest = name

        return {
            "stages": stages,
            "slowest_stage": slowest,
            "slowest_p95_ms": slowest_p95,
            "slow_stage_threshold_ms": self._config.slow_stage_ms,
        }
