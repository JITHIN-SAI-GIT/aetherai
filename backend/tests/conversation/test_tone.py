from app.conversation.tone import ToneManager


mgr = ToneManager()


def test_coding_intent_gives_technical_tone():
    result = mgr.select(intent="coding")
    assert result.tone == "technical"
    assert result.source == "intent"


def test_creative_intent_gives_friendly_tone():
    result = mgr.select(intent="creative")
    assert result.tone == "friendly"


def test_user_preference_overrides_intent():
    result = mgr.select(intent="coding", user_tone_preference="casual")
    assert result.tone == "casual"
    assert result.source == "user_preference"


def test_default_tone_on_unknown_intent():
    """Unknown intents fall back to the default tone (now 'friendly', was 'professional')."""
    result = mgr.select(intent="unknown_intent_xyz")
    assert result.tone == "friendly"   # changed from 'professional' — see policies.py
    assert result.source == "default"
