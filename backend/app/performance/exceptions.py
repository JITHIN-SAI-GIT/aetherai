class PerformanceError(Exception):
    pass


class PoolExhaustedError(PerformanceError):
    def __init__(self, message: str = "HTTP connection pool exhausted"):
        super().__init__(message)


class StreamingError(PerformanceError):
    def __init__(self, message: str):
        super().__init__(f"Streaming error: {message}")


class LatencyThresholdError(PerformanceError):
    def __init__(self, stage: str, actual_ms: float, threshold_ms: float):
        self.stage = stage
        self.actual_ms = actual_ms
        self.threshold_ms = threshold_ms
        super().__init__(
            f"Stage {stage!r} exceeded latency threshold: "
            f"{actual_ms:.1f}ms > {threshold_ms:.1f}ms"
        )


class LoadTestError(PerformanceError):
    def __init__(self, message: str):
        super().__init__(f"Load test error: {message}")
