import pytest
from app.search.engine import SearchEngine
from app.search.cache import SearchCache
from app.search.normalizer import QueryNormalizer
from app.search.summarizer import Summarizer
from app.search.metrics import SearchMetrics
from app.search.registry import SearchProviderRegistry
from app.search.models import SearchCategory


def make_engine(with_provider=False, provider_name="duckduckgo") -> SearchEngine:
    registry = SearchProviderRegistry(priority=[provider_name])
    if with_provider:
        if provider_name == "duckduckgo":
            from app.search.providers.duckduckgo import DuckDuckGoSearchProvider
            registry.register(DuckDuckGoSearchProvider())
        elif provider_name == "brave":
            from app.search.providers.brave import BraveSearchProvider
            registry.register(BraveSearchProvider())
    cache = SearchCache(redis_url="redis://localhost/99")
    return SearchEngine(
        registry=registry,
        cache=cache,
        normalizer=QueryNormalizer(),
        summarizer=Summarizer(),
        metrics=SearchMetrics(),
    )


@pytest.mark.asyncio
async def test_engine_returns_empty_on_no_provider():
    engine = make_engine(with_provider=False)
    resp = await engine.search("latest AI news", category=SearchCategory.NEWS)
    assert resp.results == []
    assert resp.provider == "none"


@pytest.mark.asyncio
async def test_engine_returns_empty_on_not_implemented_provider():
    engine = make_engine(with_provider=True, provider_name="brave")
    # Brave raises NotImplementedError — engine should degrade gracefully
    resp = await engine.search("What is the latest news?", category=SearchCategory.NEWS)
    assert resp.results == []
    assert resp.cache_hit is False


@pytest.mark.asyncio
async def test_cache_hit_on_repeated_query():
    from app.search.models import SearchResult
    engine = make_engine(with_provider=False)
    results = [SearchResult(title="Cached", snippet="s", url="https://x.com")]
    key = engine._normalizer.cache_key("latest python release")
    await engine._cache.set(key, results, ttl=3600)

    resp = await engine.search("latest python release")
    assert resp.cache_hit is True
    assert resp.results[0].title == "Cached"
