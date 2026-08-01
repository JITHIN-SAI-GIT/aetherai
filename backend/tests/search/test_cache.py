import pytest
import asyncio
from app.search.cache import SearchCache
from app.search.models import SearchResult, SearchCategory


def make_result(title="Test") -> SearchResult:
    return SearchResult(title=title, snippet="snippet", url="https://example.com")


@pytest.fixture
def cache():
    return SearchCache(redis_url="redis://localhost:6379/99")  # won't connect in CI


@pytest.mark.asyncio
async def test_cache_miss_on_empty(cache):
    result = await cache.get("nonexistent_key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_set_and_get(cache):
    results = [make_result("Story One"), make_result("Story Two")]
    await cache.set("test_key", results, category=SearchCategory.GENERAL, ttl=3600)
    retrieved = await cache.get("test_key")
    assert retrieved is not None
    assert len(retrieved) == 2
    assert retrieved[0].title == "Story One"


@pytest.mark.asyncio
async def test_cache_tracks_hits_and_misses(cache):
    await cache.get("missing")
    await cache.set("found_key", [make_result()], ttl=3600)
    await cache.get("found_key")
    stats = cache.get_stats()
    assert stats["misses"] >= 1
    assert stats["hits"] >= 1
