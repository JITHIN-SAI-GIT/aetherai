import pytest
from app.performance.cache import PerformanceCache
from app.performance.metrics import PerformanceMetrics
import time


def make_cache() -> PerformanceCache:
    return PerformanceCache(metrics=PerformanceMetrics())


def test_miss_on_empty():
    c = make_cache()
    assert c.get("missing") is None


def test_set_and_get():
    c = make_cache()
    c.set("key1", "value1")
    assert c.get("key1") == "value1"


def test_ttl_expiry():
    c = make_cache()
    c.set("ttl_key", "data", ttl_secs=0)   # expires immediately
    time.sleep(0.01)
    assert c.get("ttl_key") is None


def test_no_ttl_never_expires():
    c = make_cache()
    c.set("permanent", "data", ttl_secs=None)
    assert c.get("permanent") == "data"


def test_cache_hit_increments_metric():
    m = PerformanceMetrics()
    c = PerformanceCache(metrics=m)
    c.set("k", "v")
    c.get("k")
    snap = m.snapshot()
    assert snap["cache_hits"] == 1


def test_cache_miss_increments_metric():
    m = PerformanceMetrics()
    c = PerformanceCache(metrics=m)
    c.get("nonexistent")
    snap = m.snapshot()
    assert snap["cache_misses"] == 1


def test_get_or_set_calls_factory_once():
    c = make_cache()
    calls = []
    def factory():
        calls.append(1)
        return "computed"
    val1 = c.get_or_set("k", factory)
    val2 = c.get_or_set("k", factory)
    assert val1 == val2 == "computed"
    assert len(calls) == 1  # factory called exactly once


def test_compact_removes_expired():
    c = make_cache()
    c.set("exp", "data", ttl_secs=0)
    c.set("live", "data", ttl_secs=9999)
    time.sleep(0.01)
    evicted = c.compact()
    assert evicted == 1
    assert c.size() == 1


def test_model_list_cache_helpers():
    c = make_cache()
    c.cache_model_list("openai", ["gpt-4", "gpt-3.5-turbo"])
    result = c.get_model_list("openai")
    assert result == ["gpt-4", "gpt-3.5-turbo"]
