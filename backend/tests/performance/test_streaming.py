import pytest
import asyncio
from typing import AsyncGenerator
from app.performance.streaming import StreamingOptimizer
from app.performance.metrics import PerformanceMetrics


def make_optimizer() -> StreamingOptimizer:
    return StreamingOptimizer(metrics=PerformanceMetrics())


async def simple_generator(chunks) -> AsyncGenerator[str, None]:
    for c in chunks:
        yield c


@pytest.mark.asyncio
async def test_wrapped_generator_yields_same_content():
    opt = make_optimizer()
    chunks = ["data: hello\n\n", "data: world\n\n", "data: [DONE]\n\n"]
    gen = simple_generator(chunks)
    result = []
    async for chunk in opt.wrap(gen):
        result.append(chunk)
    assert result == chunks


@pytest.mark.asyncio
async def test_ttfb_recorded_on_first_chunk():
    m = PerformanceMetrics()
    opt = StreamingOptimizer(metrics=m)
    chunks = ["data: a\n\n", "data: b\n\n"]
    gen = simple_generator(chunks)
    async for _ in opt.wrap(gen):
        pass
    snap = m.snapshot()
    assert snap["stream_ttfb"]["count"] == 1


@pytest.mark.asyncio
async def test_empty_generator_no_ttfb():
    m = PerformanceMetrics()
    opt = StreamingOptimizer(metrics=m)
    gen = simple_generator([])
    async for _ in opt.wrap(gen):
        pass
    snap = m.snapshot()
    assert snap["stream_ttfb"]["count"] == 0


@pytest.mark.asyncio
async def test_output_identical_to_input():
    opt = make_optimizer()
    expected = [f"data: chunk{i}\n\n" for i in range(20)]
    gen = simple_generator(expected)
    result = []
    async for chunk in opt.wrap(gen):
        result.append(chunk)
    assert result == expected
