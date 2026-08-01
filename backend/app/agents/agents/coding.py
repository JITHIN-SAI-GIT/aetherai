from typing import FrozenSet
from ..base import BaseAgent
from ..context import AgentContext
from ..config import AGENT_CONFIG


class CodingAgent(BaseAgent):
    """Specialist for code generation, review, and debugging."""

    def name(self) -> str:
        return "coding"

    def description(self) -> str:
        return "Expert software engineering reasoning for code generation, review, debugging, and architecture."

    def supported_intents(self) -> FrozenSet[str]:
        return frozenset({"coding", "tool_request"})

    def priority(self) -> int:
        return AGENT_CONFIG.coding_priority

    def system_prompt(self) -> str:
        # Behavioural overlay only — identity is owned by Persona (persona.py)
        return (
            "For this request, apply expert software engineering reasoning:\n"
            "• Write clean, idiomatic, well-structured code\n"
            "• Follow best practices for the language or framework in use\n"
            "• Prioritise readability, correctness, and performance\n"
            "• Consider security implications in every solution\n"
            "• Always include proper error handling\n"
            "• Use fenced code blocks with the correct language tag\n"
            "• Explain the key design decisions briefly after the code\n"
            "• If the language or framework is ambiguous, ask before assuming"
        )

    def preprocess(self, ctx: AgentContext) -> AgentContext:
        ctx.metadata["formatting_hint"] = "use_fenced_code_blocks"
        return ctx

    def postprocess(self, content: str, ctx: AgentContext) -> str:
        return content
