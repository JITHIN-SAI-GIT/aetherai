from typing import FrozenSet
from ..base import BaseAgent
from ..context import AgentContext


class GeneralAgent(BaseAgent):
    """
    Catch-all fallback agent.
    Handles any intent that no specialist claims.
    Always has the lowest priority (0).
    """

    def name(self) -> str:
        return "general"

    def description(self) -> str:
        return "General-purpose assistant. Handles any topic not covered by a specialist."

    def supported_intents(self) -> FrozenSet[str]:
        return frozenset({"*"})   # Wildcard — matches every intent

    def priority(self) -> int:
        return 0

    def system_prompt(self) -> str:
        # Behavioural guidance only — identity is owned by Persona (persona.py)
        return (
            "Answer clearly, accurately, and at the right level of depth for the question. "
            "Match the user's level of expertise — don't over-explain simple things "
            "or under-explain complex ones."
        )

    def preprocess(self, ctx: AgentContext) -> AgentContext:
        return ctx

    def postprocess(self, content: str, ctx: AgentContext) -> str:
        return content
