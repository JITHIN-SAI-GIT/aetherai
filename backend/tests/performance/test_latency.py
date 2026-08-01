import pytest
from app.performance.latency import LatencyTracker
from app.performance.metrics import PerformanceMetrics


def make_tracker() -> LatencyTracker:
    return LatencyTracker(metrics=PerformanceMetrics())


def test_records_stage_timings():
    m = PerformanceMetrics()
    tracker = LatencyTracker(metrics=m)
    timings = {
        "intent_detection": 5.2,
        "agent_routing": 8.1,
        "provider_call": 350.0,
        "total_pipeline": 400.0,
    }
    tracker.record_pipeline_timings(timings)
    snap = m.snapshot()
    assert "intent_detection" in snap["pipeline_stages"]
    assert "provider_call" in snap["pipeline_stages"]
    # total_pipeline should be excluded from per-stage recording
    assert "total_pipeline" not in snap["pipeline_stages"]


def test_bottleneck_report_identifies_slowest():
    m = PerformanceMetrics()
    # Inject multiple samples for two stages
    for _ in range(5):
        m.record_stage("fast_stage", 10.0)
    for _ in range(5):
        m.record_stage("slow_stage", 900.0)

    tracker = LatencyTracker(metrics=m)
    report = tracker.bottleneck_report()
    assert report["slowest_stage"] == "slow_stage"
    assert report["slowest_p95_ms"] > 500.0


def test_bottleneck_report_empty_no_crash():
    tracker = make_tracker()
    report = tracker.bottleneck_report()
    assert report["slowest_stage"] is None
    assert "stages" in report
