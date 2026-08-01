import pytest
from app.pipeline.critic import Critic
from app.pipeline.context import PipelineContext
from app.providers.models import ProviderResponse


def _response(**kwargs) -> ProviderResponse:
    defaults = dict(
        provider="openai", model="gpt-4", content="Hello!",
        finish_reason="stop", usage={}, latency_ms=10, status=200
    )
    defaults.update(kwargs)
    return ProviderResponse(**defaults)


def test_critic_passes_valid_response():
    ctx = PipelineContext(request_id="test", model="gpt-4",
                          provider_response=_response())
    result = Critic().review(ctx)
    assert result.critic_result.passed is True
    assert result.degraded is False


def test_critic_fails_empty_content():
    ctx = PipelineContext(request_id="test", model="gpt-4",
                          provider_response=_response(content=""))
    result = Critic().review(ctx)
    assert result.critic_result.passed is False
    assert result.degraded is True
    assert result.provider_response.content  # degraded placeholder injected


def test_critic_fails_none_response():
    ctx = PipelineContext(request_id="test", model="gpt-4", provider_response=None)
    result = Critic().review(ctx)
    assert result.critic_result.passed is False
    assert result.degraded is True


def test_critic_fails_invalid_finish_reason():
    ctx = PipelineContext(request_id="test", model="gpt-4",
                          provider_response=_response(finish_reason="ERROR"))
    result = Critic().review(ctx)
    assert result.critic_result.passed is False
