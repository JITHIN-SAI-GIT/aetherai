import pytest
from app.agents.registry import AgentRegistry
from app.agents.agents.general import GeneralAgent
from app.agents.agents.coding import CodingAgent
from app.agents.exceptions import AgentNotFoundError


def make_registry() -> AgentRegistry:
    r = AgentRegistry()
    r.register(GeneralAgent(), enabled=True)
    r.register(CodingAgent(), enabled=True)
    return r


def test_register_and_count():
    r = make_registry()
    assert r.count() == 2


def test_get_by_name():
    r = make_registry()
    assert r.get("coding") is not None
    assert r.get("nonexistent") is None


def test_candidates_for_coding_intent():
    r = make_registry()
    candidates = r.candidates_for_intent("coding")
    names = [a.name() for a in candidates]
    assert "coding" in names


def test_wildcard_matches_any_intent():
    r = make_registry()
    candidates = r.candidates_for_intent("unknown_intent_xyz")
    names = [a.name() for a in candidates]
    assert "general" in names


def test_disable_removes_from_candidates():
    r = make_registry()
    r.disable("coding")
    candidates = r.candidates_for_intent("coding")
    names = [a.name() for a in candidates]
    assert "coding" not in names


def test_enable_restores_agent():
    r = make_registry()
    r.disable("coding")
    r.enable("coding")
    assert r.is_enabled("coding") is True


def test_disable_unknown_raises():
    r = make_registry()
    with pytest.raises(AgentNotFoundError):
        r.disable("nonexistent")


def test_priority_ordering():
    r = make_registry()
    enabled = r.get_enabled()
    priorities = [a.priority() for a in enabled]
    assert priorities == sorted(priorities, reverse=True)
