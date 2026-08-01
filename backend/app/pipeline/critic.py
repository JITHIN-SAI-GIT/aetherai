import logging
from typing import List
from .context import PipelineContext, CriticResult

logger = logging.getLogger("pipeline.critic")

VALID_FINISH_REASONS = {"stop", "length", "tool_calls", "content_filter"}


class Critic:
    """
    Reviews the ProviderResponse for quality and correctness.
    Substitutes a graceful degraded placeholder if the response is invalid.
    """

    def review(self, context: PipelineContext) -> PipelineContext:
        issues: List[str] = []
        resp = context.provider_response

        if resp is None:
            issues.append("ProviderResponse is None")
        else:
            if not resp.content or not resp.content.strip():
                issues.append("Response content is empty")
            if resp.finish_reason not in VALID_FINISH_REASONS:
                issues.append(f"Invalid finish_reason: {resp.finish_reason!r}")
            if resp.status >= 400:
                issues.append(f"Provider returned error status: {resp.status}")

        passed = len(issues) == 0
        degraded = not passed

        if degraded:
            # Substitute a graceful degraded response rather than crashing
            from app.providers.models import ProviderResponse
            context.provider_response = ProviderResponse(
                provider=context.selected_provider or "unknown",
                model=context.model,
                content="Hmm, something went wrong on my end — mind trying that again? 🙏",
                finish_reason="stop",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                latency_ms=0,
                status=200,
            )
            context.degraded = True

        context.critic_result = CriticResult(passed=passed, issues=issues, degraded=degraded)

        logger.info(
            "Critic review complete",
            extra={
                "request_id": context.request_id,
                "passed": passed,
                "issues": issues,
                "degraded": degraded,
            }
        )
        return context
