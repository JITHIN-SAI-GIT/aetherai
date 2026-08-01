import logging
from typing import Optional, Dict, Any
from .registry import AgentRegistry
from .context import AgentContext
from .models import AgentSelection
from .base import BaseAgent

logger = logging.getLogger("agents.router")

_WILDCARD_PENALTY = 0.2   # Reduce confidence when only wildcard agent matched
_SPECIALIST_CONFIDENCE = 0.95
_FALLBACK_CONFIDENCE = 0.5


class AgentRouter:
    """
    Selects the best agent for a given request.
    Decision is purely data-driven: reads the registry, scores candidates.
    Contains ZERO hardcoded agent references.
    Adding a new agent to the registry automatically makes it eligible here.
    """

    def __init__(self, registry: AgentRegistry):
        self._registry = registry

    def route(
        self,
        intent: str,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> AgentSelection:
        """
        Select the highest-priority agent that supports this intent.
        Falls back to GeneralAgent (wildcard) if no specialist matches.
        """
        user_preferences = user_preferences or {}
        preferred_agent = user_preferences.get("preferred_agent")

        # User-specified preference takes highest priority
        if preferred_agent:
            agent = self._registry.get(preferred_agent)
            if agent and self._registry.is_enabled(preferred_agent):
                logger.info("User preference agent selected",
                            extra={"agent": preferred_agent, "intent": intent})
                return AgentSelection(
                    agent_name=preferred_agent,
                    confidence=1.0,
                    reason="user_preference",
                    is_fallback=False,
                )

        # Find all candidates that explicitly support this intent
        # (candidates_for_intent already excludes wildcards in scoring)
        candidates = self._registry.candidates_for_intent(intent)

        # Filter out pure wildcards — keep only specialists that explicitly listed this intent
        specialists = [
            a for a in candidates
            if "*" not in a.supported_intents() and intent in a.supported_intents()
        ]

        if specialists:
            winner = specialists[0]  # highest-priority specialist
            logger.info("Specialist agent selected",
                        extra={"agent": winner.name(), "intent": intent,
                               "confidence": _SPECIALIST_CONFIDENCE})
            return AgentSelection(
                agent_name=winner.name(),
                confidence=_SPECIALIST_CONFIDENCE,
                reason=f"intent_match:{intent}",
                is_fallback=False,
            )

        # Fallback: use wildcard agent (GeneralAgent)
        wildcards = [a for a in candidates if "*" in a.supported_intents()]
        if wildcards:
            fallback = wildcards[0]
            logger.info("Fallback agent selected",
                        extra={"agent": fallback.name(), "intent": intent})
            return AgentSelection(
                agent_name=fallback.name(),
                confidence=_FALLBACK_CONFIDENCE,
                reason="fallback_no_specialist",
                is_fallback=True,
            )

        # Safety net — should never reach here if GeneralAgent is registered
        logger.error("No agent found — registry may be empty", extra={"intent": intent})
        return AgentSelection(
            agent_name="general",
            confidence=0.0,
            reason="no_agent_in_registry",
            is_fallback=True,
        )
