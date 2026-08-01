from app.pipeline.router import ProviderRouter
from app.pipeline.context import PipelineContext
from app.providers.registry import ProviderRegistry
from app.providers.config import ProviderConfig
from app.providers.implementations.openai_provider import OpenAIProvider


def test_provider_router_selects_first_priority():
    config = ProviderConfig(provider_priority=["openai"])
    registry = ProviderRegistry(config)
    registry.register("openai", OpenAIProvider())

    ctx = PipelineContext(request_id="test", model="gpt-4")
    result = ProviderRouter(registry).route(ctx)
    assert result.selected_provider == "openai"


def test_provider_router_raises_on_empty_registry():
    import pytest
    from app.pipeline.exceptions import PipelineRoutingError
    config = ProviderConfig(provider_priority=[])
    registry = ProviderRegistry(config)

    ctx = PipelineContext(request_id="test", model="gpt-4")
    with pytest.raises(PipelineRoutingError):
        ProviderRouter(registry).route(ctx)
