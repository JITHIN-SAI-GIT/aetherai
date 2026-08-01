from app.conversation.response_style import ResponseStyleSelector


sel = ResponseStyleSelector()


def test_coding_intent_gives_coding_style():
    r = sel.select("coding")
    assert r.style == "coding"
    assert r.code_expected is True


def test_math_intent_uses_markdown():
    r = sel.select("math")
    assert r.use_markdown is True


def test_creative_intent_gives_creative_style():
    r = sel.select("creative")
    assert r.style == "creative"


def test_general_fallback():
    r = sel.select("chat")
    assert r.style == "general"
