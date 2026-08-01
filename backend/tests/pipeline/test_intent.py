from app.pipeline.intent import IntentDetector
from app.pipeline.context import PipelineContext


def _make_context(content: str) -> PipelineContext:
    return PipelineContext(
        request_id="test",
        messages=[{"role": "user", "content": content}],
        model="gpt-4-turbo",
    )


def test_coding_intent():
    ctx = _make_context("Can you write a Python function to reverse a string?")
    result = IntentDetector().detect(ctx)
    assert result.intent == "coding"


def test_math_intent():
    ctx = _make_context("Can you solve this equation for me?")
    result = IntentDetector().detect(ctx)
    assert result.intent == "math"


def test_search_intent():
    ctx = _make_context("What is the latest news today?")
    result = IntentDetector().detect(ctx)
    assert result.intent == "search_required"


def test_translation_intent():
    ctx = _make_context("Translate this sentence in French please.")
    result = IntentDetector().detect(ctx)
    assert result.intent == "translation"


def test_default_chat_intent():
    ctx = _make_context("Hey, how are you doing?")
    result = IntentDetector().detect(ctx)
    assert result.intent == "chat"
