import pytest
import asyncio
from app.performance.load_test import LoadTester, LoadTestResult


async def fast_coroutine():
    await asyncio.sleep(0.001)


async def failing_coroutine():
    raise RuntimeError("Simulated failure")


@pytest.mark.asyncio
async def test_load_test_basic_run():
    tester = LoadTester()
    result = await tester.run(fast_coroutine, concurrency=5, total_requests=10)
    assert isinstance(result, LoadTestResult)
    assert result.total_requests == 10
    assert result.successful == 10
    assert result.failed == 0
    assert result.failure_rate == 0.0


@pytest.mark.asyncio
async def test_load_test_counts_failures():
    tester = LoadTester()
    result = await tester.run(failing_coroutine, concurrency=5, total_requests=10)
    assert result.failed == 10
    assert result.successful == 0
    assert result.failure_rate == 1.0


@pytest.mark.asyncio
async def test_load_test_throughput_positive():
    tester = LoadTester()
    result = await tester.run(fast_coroutine, concurrency=10, total_requests=20)
    assert result.throughput_rps > 0.0


@pytest.mark.asyncio
async def test_load_test_latencies_recorded():
    tester = LoadTester()
    result = await tester.run(fast_coroutine, concurrency=5, total_requests=10)
    assert len(result.latencies_ms) == 10
    pct = result.percentiles()
    assert pct["p50"] is not None


def test_load_test_result_summary_has_all_keys():
    result = LoadTestResult(
        concurrency=10,
        total_requests=20,
        successful=18,
        failed=2,
        duration_secs=1.5,
        latencies_ms=[100.0, 200.0, 300.0],
    )
    summary = result.summary()
    for key in ["concurrency", "total_requests", "successful", "failed",
                "failure_rate", "throughput_rps", "latency_ms", "duration_secs"]:
        assert key in summary
