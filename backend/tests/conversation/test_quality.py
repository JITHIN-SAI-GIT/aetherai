from app.conversation.quality import QualityReviewer
from app.conversation.models import StyleResult


rev = QualityReviewer()
general_style = StyleResult(style="general")


def test_passes_valid_response():
    result = rev.review("This is a perfectly valid response with enough content.", general_style)
    assert result.passed is True


def test_fails_empty_response():
    result = rev.review("", general_style)
    assert result.passed is False
    assert "empty" in result.issues[0]
    assert result.corrected_content


def test_removes_banned_phrase():
    result = rev.review("As an AI language model, I can help you.", general_style)
    assert result.corrections_applied >= 1
    assert "As an AI language model" not in (result.corrected_content or "")


def test_detects_repetition():
    # Repeat a 4-gram multiple times
    text = "this is a test " * 10
    result = rev.review(text, general_style)
    assert any("repeated" in issue for issue in result.issues)
