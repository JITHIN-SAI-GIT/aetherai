import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    """
    Per-agent configuration loaded from environment variables.
    Each flag follows the pattern AGENT_<NAME>_ENABLED / AGENT_<NAME>_PRIORITY.
    Example: AGENT_CODING_ENABLED=false disables CodingAgent at startup.
    """
    coding_enabled: bool = os.getenv("AGENT_CODING_ENABLED", "true").lower() == "true"
    coding_priority: int = int(os.getenv("AGENT_CODING_PRIORITY", "10"))

    research_enabled: bool = os.getenv("AGENT_RESEARCH_ENABLED", "true").lower() == "true"
    research_priority: int = int(os.getenv("AGENT_RESEARCH_PRIORITY", "10"))

    math_enabled: bool = os.getenv("AGENT_MATH_ENABLED", "true").lower() == "true"
    math_priority: int = int(os.getenv("AGENT_MATH_PRIORITY", "10"))

    creative_enabled: bool = os.getenv("AGENT_CREATIVE_ENABLED", "true").lower() == "true"
    creative_priority: int = int(os.getenv("AGENT_CREATIVE_PRIORITY", "10"))

    translation_enabled: bool = os.getenv("AGENT_TRANSLATION_ENABLED", "true").lower() == "true"
    translation_priority: int = int(os.getenv("AGENT_TRANSLATION_PRIORITY", "10"))

    business_enabled: bool = os.getenv("AGENT_BUSINESS_ENABLED", "true").lower() == "true"
    business_priority: int = int(os.getenv("AGENT_BUSINESS_PRIORITY", "10"))

    general_enabled: bool = True   # GeneralAgent is always enabled — it is the fallback
    general_priority: int = 0      # Lowest priority — only wins when no specialist matches


# Module-level singleton
AGENT_CONFIG = AgentConfig()
