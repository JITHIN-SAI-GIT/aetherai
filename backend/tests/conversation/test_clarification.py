from app.conversation.clarification import ClarificationEngine


eng = ClarificationEngine()


def test_no_clarification_for_high_confidence_intent():
    result = eng.evaluate("chat", confidence=1.0)
    assert result.needed is False


def test_clarification_for_low_confidence():
    result = eng.evaluate("general", confidence=0.3)
    assert result.needed is True
    assert result.question


def test_clarification_for_explicit_intent():
    result = eng.evaluate("clarification_required", confidence=1.0)
    assert result.needed is True
    assert "clarify" in result.question.lower()
