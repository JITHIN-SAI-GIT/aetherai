from app.pipeline.formatter import Formatter
from app.pipeline.context import PipelineContext
from app.providers.models import ProviderResponse


def test_formatter_produces_openai_schema():
    resp = ProviderResponse(
        provider="openai", model="gpt-4", content="Test content",
        finish_reason="stop", usage={"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
        latency_ms=10, status=200
    )
    ctx = PipelineContext(request_id="test", model="gpt-4", provider_response=resp)
    result = Formatter().format(ctx)

    cr = result.formatted_response
    assert cr.object == "chat.completion"
    assert cr.choices[0].message.content == "Test content"
    assert cr.usage.total_tokens == 10
    assert cr.id.startswith("chatcmpl-")
