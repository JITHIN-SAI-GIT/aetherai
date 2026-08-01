"""Per-agent contract tests — verifies that every agent satisfies the BaseAgent contract."""
import pytest
from app.agents.agents.general import GeneralAgent
from app.agents.agents.coding import CodingAgent
from app.agents.agents.research import ResearchAgent
from app.agents.agents.math import MathAgent
from app.agents.agents.creative import CreativeAgent
from app.agents.agents.translation import TranslationAgent
from app.agents.agents.business import BusinessAgent
from app.agents.context import AgentContext
from app.agents.base import BaseAgent

ALL_AGENTS = [
    GeneralAgent(),
    CodingAgent(),
    ResearchAgent(),
    MathAgent(),
    CreativeAgent(),
    TranslationAgent(),
    BusinessAgent(),
]


@pytest.mark.parametrize("agent", ALL_AGENTS, ids=lambda a: a.name())
def test_agent_has_name(agent: BaseAgent):
    assert agent.name() and isinstance(agent.name(), str)


@pytest.mark.parametrize("agent", ALL_AGENTS, ids=lambda a: a.name())
def test_agent_has_description(agent: BaseAgent):
    assert agent.description() and isinstance(agent.description(), str)


@pytest.mark.parametrize("agent", ALL_AGENTS, ids=lambda a: a.name())
def test_agent_has_system_prompt(agent: BaseAgent):
    prompt = agent.system_prompt()
    assert prompt and len(prompt) > 20


@pytest.mark.parametrize("agent", ALL_AGENTS, ids=lambda a: a.name())
def test_agent_validate_returns_bool(agent: BaseAgent):
    ctx = AgentContext(intent="general", messages=[])
    result = agent.validate(ctx)
    assert isinstance(result, bool)


@pytest.mark.parametrize("agent", ALL_AGENTS, ids=lambda a: a.name())
def test_agent_preprocess_returns_context(agent: BaseAgent):
    ctx = AgentContext(intent="general", messages=[])
    result = agent.preprocess(ctx)
    assert isinstance(result, AgentContext)


@pytest.mark.parametrize("agent", ALL_AGENTS, ids=lambda a: a.name())
def test_agent_postprocess_returns_str(agent: BaseAgent):
    ctx = AgentContext(intent="general", messages=[])
    result = agent.postprocess("Hello world", ctx)
    assert isinstance(result, str)


def test_general_agent_is_wildcard():
    assert "*" in GeneralAgent().supported_intents()


def test_coding_agent_supports_coding_intent():
    assert "coding" in CodingAgent().supported_intents()


def test_math_agent_supports_math_intent():
    assert "math" in MathAgent().supported_intents()


def test_research_postprocess_adds_sources_placeholder():
    agent = ResearchAgent()
    ctx = AgentContext(intent="search_required", messages=[], search_required=True)
    result = agent.postprocess("Here is my research summary.", ctx)
    assert "[Sources" in result


def test_math_postprocess_adds_tip_when_no_answer_label():
    agent = MathAgent()
    ctx = AgentContext(intent="math", messages=[])
    long_content = "The calculation proceeds as follows: first we add two and two together, yielding a result of four."
    result = agent.postprocess(long_content, ctx)
    assert "Tip" in result or "verify" in result
