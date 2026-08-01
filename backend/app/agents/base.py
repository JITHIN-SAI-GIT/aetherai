from __future__ import annotations
from abc import ABC, abstractmethod
from typing import FrozenSet, List
from .context import AgentContext
from .models import AgentResult


class BaseAgent(ABC):
    """
    Contract every agent must implement.
    Agents communicate only through AgentContext and AgentResult.
    They must never access providers, memory, or search directly.
    """

    @abstractmethod
    def name(self) -> str:
        """Unique identifier used for registration and logging."""

    @abstractmethod
    def description(self) -> str:
        """Human-readable summary of what this agent does."""

    @abstractmethod
    def supported_intents(self) -> FrozenSet[str]:
        """
        Set of intent strings this agent handles.
        The AgentRouter asks every registered agent this question.
        Return frozenset() to opt out of all intents (not recommended).
        GeneralAgent uses a special sentinel {"*"} meaning "all intents".
        """

    @abstractmethod
    def priority(self) -> int:
        """
        Higher number = higher selection priority when multiple agents match.
        GeneralAgent always has priority 0.
        Specialist agents should use priority >= 10.
        """

    @abstractmethod
    def system_prompt(self) -> str:
        """
        The system prompt injected into the provider call for this agent.
        Agents own their own prompts — the pipeline never hardcodes prompts.
        """

    def preprocess(self, ctx: AgentContext) -> AgentContext:
        """
        Optional: Modify the context before the provider call.
        Default implementation is a no-op.
        Raise AgentRejectedError to decline this request.
        """
        return ctx

    def postprocess(self, content: str, ctx: AgentContext) -> str:
        """
        Optional: Improve, validate, or annotate the response after the provider call.
        Default implementation is a no-op.
        """
        return content

    def validate(self, ctx: AgentContext) -> bool:
        """
        Optional: Return False to decline processing (will trigger fallback).
        Default implementation always accepts.
        """
        return True

    def build_result(
        self,
        ctx: AgentContext,
        postprocessed_content: str = None,
        notes: List[str] = None,
    ) -> AgentResult:
        """Convenience factory for constructing AgentResult."""
        return AgentResult(
            agent_name=self.name(),
            system_prompt=self.system_prompt(),
            preprocessing_notes=notes or [],
            postprocessed_content=postprocessed_content,
        )
