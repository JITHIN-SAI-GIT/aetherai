import logging
from typing import Dict, List, Optional
from .base import BaseAgent
from .exceptions import AgentNotFoundError, AgentConfigError

logger = logging.getLogger("agents.registry")

_WILDCARD = "*"


class AgentRegistry:
    """
    Dynamic agent lookup table.
    The AgentRouter reads this registry — it never contains routing logic itself.
    Adding a new agent requires only: registry.register(MyNewAgent())
    No router, pipeline, or existing-agent changes are needed.
    """

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._enabled: Dict[str, bool] = {}

    def register(self, agent: BaseAgent, enabled: bool = True) -> None:
        """Register an agent. Overwrites silently if same name is re-registered."""
        name = agent.name()
        if not name:
            raise AgentConfigError("Agent must have a non-empty name()")
        self._agents[name] = agent
        self._enabled[name] = enabled
        logger.info("Agent registered", extra={"agent": name, "enabled": enabled})

    def enable(self, agent_name: str) -> None:
        if agent_name not in self._agents:
            raise AgentNotFoundError(agent_name)
        self._enabled[agent_name] = True

    def disable(self, agent_name: str) -> None:
        if agent_name not in self._agents:
            raise AgentNotFoundError(agent_name)
        self._enabled[agent_name] = False

    def is_enabled(self, agent_name: str) -> bool:
        return self._enabled.get(agent_name, False)

    def get(self, agent_name: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_name)

    def get_enabled(self) -> List[BaseAgent]:
        """Return all enabled agents ordered by priority descending."""
        enabled = [
            a for name, a in self._agents.items()
            if self._enabled.get(name, False)
        ]
        return sorted(enabled, key=lambda a: a.priority(), reverse=True)

    def candidates_for_intent(self, intent: str) -> List[BaseAgent]:
        """
        Return enabled agents that support this intent, priority-ordered.
        An agent with supported_intents() == {"*"} matches every intent.
        """
        matches = []
        for agent in self.get_enabled():
            intents = agent.supported_intents()
            if _WILDCARD in intents or intent in intents:
                matches.append(agent)
        return sorted(matches, key=lambda a: a.priority(), reverse=True)

    def count(self) -> int:
        return len(self._agents)

    def names(self) -> List[str]:
        return list(self._agents.keys())
