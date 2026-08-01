from .registry import AgentRegistry
from .config import AGENT_CONFIG
from .agents.general import GeneralAgent
from .agents.coding import CodingAgent
from .agents.research import ResearchAgent
from .agents.math import MathAgent
from .agents.creative import CreativeAgent
from .agents.translation import TranslationAgent
from .agents.business import BusinessAgent
from .agents.identity import IdentityAgent


class AgentFactory:
    """
    Constructs and registers all built-in agents.
    To add a new agent (e.g. LegalAgent), add one line here and register it.
    No other file needs to change.
    """

    @staticmethod
    def build_default_registry() -> AgentRegistry:
        registry = AgentRegistry()

        # GeneralAgent is always enabled — it is the unconditional fallback
        registry.register(GeneralAgent(), enabled=True)

        # Specialist agents — each respects its config flag
        registry.register(CodingAgent(), enabled=AGENT_CONFIG.coding_enabled)
        registry.register(ResearchAgent(), enabled=AGENT_CONFIG.research_enabled)
        registry.register(MathAgent(), enabled=AGENT_CONFIG.math_enabled)
        registry.register(CreativeAgent(), enabled=AGENT_CONFIG.creative_enabled)
        registry.register(TranslationAgent(), enabled=AGENT_CONFIG.translation_enabled)
        registry.register(BusinessAgent(), enabled=AGENT_CONFIG.business_enabled)
        registry.register(IdentityAgent(), enabled=True)   # Always enabled

        return registry
