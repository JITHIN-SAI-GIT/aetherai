import pytest
from app.providers.circuit_breaker import CircuitBreaker, CircuitState
from app.providers.exceptions import CircuitBreakerOpenError
import time

def test_circuit_breaker_closes_and_opens():
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=1)
    assert cb.can_execute() is True
    
    cb.record_failure()
    assert cb.can_execute() is True
    
    cb.record_failure()
    assert cb.can_execute() is False
    assert cb.state == CircuitState.OPEN

def test_circuit_breaker_half_open(monkeypatch):
    cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=1)
    cb.record_failure()
    assert cb.can_execute() is False
    
    original_time = time.time
    monkeypatch.setattr(time, "time", lambda: original_time() + 2)
    
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN
