from enum import Enum
from typing import Dict, Any

class HealthState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"

class HealthTracker:
    def __init__(self):
        self.state = HealthState.HEALTHY
        self.failure_count = 0
        self.last_error = None
        self.recovery_attempts = 0

    def record_failure(self, error: str):
        self.failure_count += 1
        self.last_error = error
        if self.failure_count > 3:
            self.state = HealthState.OFFLINE
        elif self.failure_count > 0:
            self.state = HealthState.DEGRADED

    def record_success(self):
        self.failure_count = 0
        self.last_error = None
        self.state = HealthState.HEALTHY
        self.recovery_attempts = 0
        
    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_error": self.last_error,
            "recovery_attempts": self.recovery_attempts
        }
