from app.agents.factory import AgentFactory
from app.agents.router import AgentRouter


def make_router() -> AgentRouter:
    registry = AgentFactory.build_default_registry()
    return AgentRouter(registry)


def test_coding_intent_selects_coding_agent():
    router = make_router()
    result = router.route("coding")
    assert result.agent_name == "coding"
    assert result.is_fallback is False
    assert result.confidence > 0.8


def test_math_intent_selects_math_agent():
    router = make_router()
    result = router.route("math")
    assert result.agent_name == "math"


def test_research_intent_selects_research_agent():
    router = make_router()
    result = router.route("search_required")
    assert result.agent_name == "research"


def test_creative_intent_selects_creative_agent():
    router = make_router()
    result = router.route("creative")
    assert result.agent_name == "creative"


def test_translation_intent_selects_translation_agent():
    router = make_router()
    result = router.route("translation")
    assert result.agent_name == "translation"


def test_business_intent_selects_business_agent():
    router = make_router()
    result = router.route("business")
    assert result.agent_name == "business"


def test_unknown_intent_falls_back_to_general():
    router = make_router()
    result = router.route("unknown_intent_xyz")
    assert result.agent_name == "general"
    assert result.is_fallback is True


def test_disabled_agent_triggers_fallback():
    registry = AgentFactory.build_default_registry()
    registry.disable("coding")
    router = AgentRouter(registry)
    result = router.route("coding")
    assert result.agent_name == "general"
    assert result.is_fallback is True


def test_user_preference_overrides_intent():
    registry = AgentFactory.build_default_registry()
    router = AgentRouter(registry)
    result = router.route("math", user_preferences={"preferred_agent": "general"})
    assert result.agent_name == "general"
    assert result.reason == "user_preference"
