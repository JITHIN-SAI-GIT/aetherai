import pytest
from app.security.audit import AuditLogger


def test_records_event():
    audit = AuditLogger()
    event = audit.record("injection", "Pattern matched", ip="1.2.3.4")
    assert event.event_type == "injection"
    assert event.ip == "1.2.3.4"
    assert audit.count() == 1


def test_recent_returns_most_recent_first():
    audit = AuditLogger()
    audit.record("rate_limit", "Exceeded", ip="1.1.1.1")
    audit.record("injection", "DAN attempt", ip="2.2.2.2")
    recent = audit.recent(n=2)
    assert recent[0]["event_type"] == "injection"  # most recent first
    assert recent[1]["event_type"] == "rate_limit"


def test_circular_buffer_evicts_oldest():
    audit = AuditLogger(max_events=3)
    for i in range(4):
        audit.record("test", f"event {i}")
    assert audit.count() == 3


def test_event_never_contains_content():
    audit = AuditLogger()
    event = audit.record("injection", "blocked", ip="9.9.9.9", pattern="ignore_previous")
    # Verify the event only contains metadata, not message content
    assert "content" not in event.metadata or event.metadata.get("content") is None
    assert event.reason == "blocked"
