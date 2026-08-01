from typing import Dict, Any

class MetricsTracker:
    def __init__(self):
        self._metrics = {
            "requests": 0,
            "success": 0,
            "failures": 0,
            "timeouts": 0,
            "rate_limits": 0,
            "retries": 0,
            "total_latency_ms": 0
        }
    
    def record_success(self, latency_ms: int):
        self._metrics["requests"] += 1
        self._metrics["success"] += 1
        self._metrics["total_latency_ms"] += latency_ms

    def record_failure(self, error_type: str):
        self._metrics["requests"] += 1
        self._metrics["failures"] += 1
        if error_type == "timeout":
            self._metrics["timeouts"] += 1
        elif error_type == "rate_limit":
            self._metrics["rate_limits"] += 1

    def record_retry(self):
        self._metrics["retries"] += 1

    def get_snapshot(self) -> Dict[str, Any]:
        reqs = self._metrics["requests"]
        avg_lat = self._metrics["total_latency_ms"] / reqs if reqs > 0 else 0
        success_pct = (self._metrics["success"] / reqs * 100) if reqs > 0 else 100.0
        
        return {
            **self._metrics,
            "average_latency_ms": avg_lat,
            "success_percentage": success_pct
        }

global_metrics = MetricsTracker()
