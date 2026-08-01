from typing import FrozenSet
from ..base import BaseAgent
from ..context import AgentContext
from ..config import AGENT_CONFIG


class TranslationAgent(BaseAgent):
    """Specialist for accurate language translation with meaning preservation."""

    def name(self) -> str:
        return "translation"

    def description(self) -> str:
        return "Precise language translation that preserves meaning, tone, and idiom."

    def supported_intents(self) -> FrozenSet[str]:
        return frozenset({"translation"})

    def priority(self) -> int:
        return AGENT_CONFIG.translation_priority

    def system_prompt(self) -> str:
        # Behavioural overlay only — identity is owned by Persona (persona.py)
        return (
            "For this request, apply professional translation principles:\n"
            "• Translate accurately — preserve the original meaning, tone, and style\n"
            "• Do not add, omit, or alter information\n"
            "• If an idiom has no direct equivalent, provide the closest natural equivalent "
            "and add a brief note explaining the original\n"
            "• Provide the translation first, followed by any notes\n"
            "• If the source language is ambiguous, state your assumption"
        )

    def preprocess(self, ctx: AgentContext) -> AgentContext:
        return ctx

    def postprocess(self, content: str, ctx: AgentContext) -> str:
        return content
