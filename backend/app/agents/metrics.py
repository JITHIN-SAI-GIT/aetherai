import logging
from typing import Dict, Any

logger = logging.getLogger("agents.metrics")


class AgentMetrics:
    """Per-agent telemetry. Thread-safe under CPython GIL."""

    def __init__(self):
        self._selections: Dict[str, int] = {}
        self._confidence_sum: Dict[str, float] = {}
        self._fallbacks: int = 0
        self._total: int = 0
        self._latency_ms_sum: float = 0.0

    def record_selection(
        self,
        agent_name: str,
        intent: str,
        confidence: float,
        is_fallback: bool,
        latency_ms: float,
    ) -> None:
        self._total += 1
        self._latency_ms_sum += latency_ms
        self._selections[agent_name] = self._selections.get(agent_name, 0) + 1
        self._confidence_sum[agent_name] = (
            self._confidence_sum.get(agent_name, 0.0) + confidence
        )
        if is_fallback:
            self._fallbacks += 1

    def snapshot(self) -> Dict[str, Any]:
        avg_latency = round(self._latency_ms_sum / max(self._total, 1), 3)
        per_agent = {}
        for name, count in self._selections.items():
            avg_conf = round(self._confidence_sum.get(name, 0.0) / count, 4)
            per_agent[name] = {"selections": count, "avg_confidence": avg_conf}

        return {
            "total_requests": self._total,
            "fallback_rate": round(self._fallbacks / max(self._total, 1), 4),
            "average_latency_ms": avg_latency,
            "per_agent": per_agent,
        }


# Module-level singleton
agent_metrics = AgentMetrics()
