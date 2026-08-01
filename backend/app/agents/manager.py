import logging
import time
from typing import Optional, Dict, Any, List, Tuple
from .registry import AgentRegistry
from .router import AgentRouter
from .context import AgentContext
from .models import AgentSelection, AgentResult
from .metrics import AgentMetrics, agent_metrics
from .exceptions import AgentRejectedError

logger = logging.getLogger("agents.manager")


class AgentManager:
    """
    Single public interface for the agent layer.
    Called from the pipeline at Stage 4.5 (after search, before provider routing).
    No pipeline stage, security module, or route handler may call agents directly.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        metrics: Optional[AgentMetrics] = None,
    ):
        self._registry = registry
        self._router = AgentRouter(registry)
        self._metrics = metrics or agent_metrics

    def select(
        self,
        intent: str,
        messages: List[Dict[str, Any]],
        user_profile: Dict[str, Any] = None,
        search_required: bool = False,
        search_results: List[str] = None,
        conversation_summary: Optional[str] = None,
        user_preferences: Dict[str, Any] = None,
    ) -> Tuple[AgentSelection, AgentResult]:
        """
        Route to the best agent and run preprocess.
        Returns (AgentSelection, AgentResult) — the pipeline stores these on context.
        """
        start = time.perf_counter()
        user_preferences = user_preferences or {}

        # Build the agent context DTO
        ctx = AgentContext(
            intent=intent,
            messages=messages or [],
            user_profile=user_profile or {},
            search_required=search_required,
            search_results=search_results or [],
            conversation_summary=conversation_summary,
            user_preferences=user_preferences,
        )

        # Route
        selection = self._router.route(intent, user_preferences)

        # Resolve agent from registry
        agent = self._registry.get(selection.agent_name)
        if agent is None:
            # Safety net: fall back to general
            agent = self._registry.get("general")
            if agent is None:
                raise RuntimeError("GeneralAgent not found in registry — factory not called")

        # Validate & preprocess
        try:
            if not agent.validate(ctx):
                raise AgentRejectedError(agent.name(), "validate() returned False")
            ctx = agent.preprocess(ctx)
        except AgentRejectedError as e:
            logger.warning("Agent rejected request, falling back",
                           extra={"agent": agent.name(), "reason": e.reason})
            agent = self._registry.get("general")
            ctx = agent.preprocess(ctx)

        result = agent.build_result(ctx)

        # Metrics
        elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
        self._metrics.record_selection(
            agent_name=agent.name(),
            intent=intent,
            confidence=selection.confidence,
            is_fallback=selection.is_fallback,
            latency_ms=elapsed_ms,
        )

        logger.info(
            "Agent selected",
            extra={
                "agent": agent.name(),
                "intent": intent,
                "confidence": selection.confidence,
                "fallback": selection.is_fallback,
                "latency_ms": elapsed_ms,
            },
        )
        return selection, result

    def postprocess(
        self,
        agent_name: str,
        content: str,
        ctx: AgentContext,
    ) -> str:
        """Run the selected agent's postprocess step on the provider response."""
        agent = self._registry.get(agent_name)
        if agent is None:
            return content
        try:
            return agent.postprocess(content, ctx)
        except Exception as e:
            logger.warning("Agent postprocess failed",
                           extra={"agent": agent_name, "error": str(e)})
            return content
