import pytest
from app.performance.profiler import RequestProfiler
from app.performance.metrics import PerformanceMetrics


def make_profiler() -> RequestProfiler:
    return RequestProfiler(metrics=PerformanceMetrics())


def test_profile_increments_request_count():
    m = PerformanceMetrics()
    profiler = RequestProfiler(metrics=m)
    with profiler.profile(request_id="test-1", endpoint="/v1/chat/completions"):
        pass
    snap = m.snapshot()
    assert snap["total_requests"] == 1
    assert snap["concurrent_requests"] == 0  # finished


def test_profile_concurrent_gauge_during_request():
    m = PerformanceMetrics()
    profiler = RequestProfiler(metrics=m)
    with profiler.profile():
        assert m.snapshot()["concurrent_requests"] == 1
    assert m.snapshot()["concurrent_requests"] == 0


def test_record_ttfb_callable():
    m = PerformanceMetrics()
    profiler = RequestProfiler(metrics=m)
    with profiler.profile() as record_ttfb:
        ms = record_ttfb()
    snap = m.snapshot()
    assert snap["ttfb"]["count"] == 1
    assert ms >= 0


def test_record_ttfb_idempotent():
    """Calling record_ttfb twice should only record the first measurement."""
    m = PerformanceMetrics()
    profiler = RequestProfiler(metrics=m)
    with profiler.profile() as record_ttfb:
        record_ttfb()
        record_ttfb()
    snap = m.snapshot()
    assert snap["ttfb"]["count"] == 1  # only one TTFB per request


def test_peak_concurrent_tracked():
    m = PerformanceMetrics()
    p1 = RequestProfiler(metrics=m)
    p2 = RequestProfiler(metrics=m)
    with p1.profile():
        with p2.profile():
            pass
    assert m.snapshot()["peak_concurrent"] == 2
