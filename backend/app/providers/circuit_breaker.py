from enum import Enum
import time
from .exceptions import CircuitBreakerOpenError

class CircuitState(Enum):
    CLOSED    = "closed"     # Healthy — provider receives traffic
    OPEN      = "open"       # DOWN — provider is skipped until cooldown expires
    HALF_OPEN = "half_open"  # Cooldown expired — one trial request allowed

class CircuitBreaker:
    """
    3-state circuit breaker per provider.

    Transitions:
        CLOSED  → OPEN      : after `failure_threshold` consecutive failures
        OPEN    → HALF_OPEN : after `cooldown_seconds` have elapsed
        HALF_OPEN → CLOSED  : on first success
        HALF_OPEN → OPEN    : on failure (reset cooldown timer)
    """

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 60):
        self.threshold          = failure_threshold
        self.cooldown           = cooldown_seconds
        self.state              = CircuitState.CLOSED
        self.failures           = 0
        self.last_failure_time  = 0.0

    def record_failure(self) -> None:
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.threshold:
            if self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN

    def record_success(self) -> None:
        self.failures = 0
        self.last_failure_time = 0.0
        self.state = CircuitState.CLOSED

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.cooldown:
                # Cooldown expired — allow a single trial request
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        # HALF_OPEN — allow one trial request; caller decides outcome
        return True

    def execute(self, func, *args, **kwargs):
        """Synchronous convenience wrapper (kept for backward compat)."""
        if not self.can_execute():
            raise CircuitBreakerOpenError("Circuit is OPEN")
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise
