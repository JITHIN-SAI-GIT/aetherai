from typing import FrozenSet
from ..base import BaseAgent
from ..context import AgentContext
from ..config import AGENT_CONFIG


class MathAgent(BaseAgent):
    """Specialist for mathematical reasoning, calculation, and proofs."""

    def name(self) -> str:
        return "math"

    def description(self) -> str:
        return "Mathematical reasoning specialist with step-by-step working and validation."

    def supported_intents(self) -> FrozenSet[str]:
        return frozenset({"math"})

    def priority(self) -> int:
        return AGENT_CONFIG.math_priority

    def system_prompt(self) -> str:
        # Behavioural overlay only — identity is owned by Persona (persona.py)
        return (
            "For this request, apply rigorous mathematical reasoning:\n"
            "• Show working step-by-step, labelling each step clearly\n"
            "• State all assumptions before solving\n"
            "• Use LaTeX notation for mathematical expressions where helpful\n"
            "• State the final answer clearly on its own line, prefixed with 'Answer:'\n"
            "• Validate the answer by substituting back where applicable\n"
            "• If the problem is ambiguous, state what you assumed before solving"
        )

    def preprocess(self, ctx: AgentContext) -> AgentContext:
        ctx.metadata["formatting_hint"] = "step_by_step"
        return ctx

    def postprocess(self, content: str, ctx: AgentContext) -> str:
        # If no "Answer:" label on a substantial response, add a verification tip
        if "answer:" not in content.lower() and len(content) > 50:
            content = content + "\n\n*(Tip: verify the answer by checking against the original problem.)*"
        return content
