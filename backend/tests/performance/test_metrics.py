import pytest
from app.performance.metrics import PerformanceMetrics, _percentiles


def make_metrics() -> PerformanceMetrics:
    return PerformanceMetrics(window_size=100)


def test_initial_snapshot_has_zero_requests():
    m = make_metrics()
    snap = m.snapshot()
    assert snap["total_requests"] == 0
    assert snap["concurrent_requests"] == 0


def test_request_started_increments_total():
    m = make_metrics()
    m.request_started()
    assert m.snapshot()["total_requests"] == 1
    assert m.snapshot()["concurrent_requests"] == 1


def test_request_finished_decrements_concurrent():
    m = make_metrics()
    m.request_started()
    m.request_finished(total_ms=100.0)
    assert m.snapshot()["concurrent_requests"] == 0


def test_slow_request_counted():
    m = make_metrics()
    m.request_started()
    m.request_finished(total_ms=9999.0, slow_threshold_ms=500.0)
    assert m.snapshot()["slow_requests"] == 1


def test_stage_latency_recorded():
    m = make_metrics()
    m.record_stage("intent_detection", 12.5)
    snap = m.snapshot()
    assert "intent_detection" in snap["pipeline_stages"]
    assert snap["pipeline_stages"]["intent_detection"]["count"] == 1


def test_cache_hit_rate():
    m = make_metrics()
    m.record_cache_hit()
    m.record_cache_hit()
    m.record_cache_miss()
    snap = m.snapshot()
    assert snap["cache_hit_rate"] == pytest.approx(2 / 3, rel=0.01)


def test_peak_concurrent_tracked():
    m = make_metrics()
    m.request_started()
    m.request_started()
    m.request_started()
    assert m.snapshot()["peak_concurrent"] == 3


def test_percentiles_empty():
    result = _percentiles([])
    assert result["p50"] is None
    assert result["count"] == 0


def test_percentiles_computed():
    samples = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    result = _percentiles(samples)
    assert result["p50"] is not None
    assert result["p95"] is not None
    assert result["count"] == 10
