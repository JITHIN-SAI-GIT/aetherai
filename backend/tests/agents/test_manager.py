from app.agents.factory import AgentFactory
from app.agents.manager import AgentManager
from app.agents.metrics import AgentMetrics


def make_manager() -> AgentManager:
    registry = AgentFactory.build_default_registry()
    return AgentManager(registry)


def test_coding_request_returns_coding_agent():
    mgr = make_manager()
    msgs = [{"role": "user", "content": "Write a Python sort function"}]
    selection, result = mgr.select(intent="coding", messages=msgs)
    assert selection.agent_name == "coding"
    assert "software engineer" in result.system_prompt.lower() or "code" in result.system_prompt.lower()


def test_math_request_returns_math_agent():
    mgr = make_manager()
    selection, result = mgr.select(intent="math", messages=[])
    assert selection.agent_name == "math"
    assert "step" in result.system_prompt.lower()


def test_unknown_intent_returns_general():
    mgr = make_manager()
    selection, result = mgr.select(intent="totally_unknown", messages=[])
    assert selection.agent_name == "general"
    assert selection.is_fallback is True


def test_postprocess_runs_without_error():
    mgr = make_manager()
    selection, result = mgr.select(intent="coding", messages=[])
    from app.agents.context import AgentContext
    ctx = AgentContext(intent="coding")
    processed = mgr.postprocess(selection.agent_name, "Here is the code.", ctx)
    assert isinstance(processed, str)


def test_metrics_updated_after_select():
    metrics = AgentMetrics()
    registry = AgentFactory.build_default_registry()
    mgr = AgentManager(registry, metrics=metrics)
    mgr.select(intent="coding", messages=[])
    snap = metrics.snapshot()
    assert snap["total_requests"] == 1
    assert "coding" in snap["per_agent"]
