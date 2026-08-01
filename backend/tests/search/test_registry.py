import pytest
from app.search.registry import SearchProviderRegistry
from app.search.providers.duckduckgo import DuckDuckGoSearchProvider
from app.search.exceptions import NoSearchProviderError


def test_register_and_retrieve():
    reg = SearchProviderRegistry(priority=["duckduckgo"])
    reg.register(DuckDuckGoSearchProvider())
    provider = reg.get_provider()
    assert provider.name() == "duckduckgo"


def test_raises_when_empty():
    reg = SearchProviderRegistry(priority=["duckduckgo"])
    with pytest.raises(NoSearchProviderError):
        reg.get_provider()
