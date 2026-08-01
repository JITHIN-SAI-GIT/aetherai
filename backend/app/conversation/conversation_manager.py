import logging
from .context_builder import ConversationContextBuilder
from .markdown_formatter import MarkdownFormatter
from .quality import QualityReviewer
from .metrics import ConversationMetrics, conversation_metrics
from .models import ConversationContext, QualityResult
from .persona import DEFAULT_PERSONA

logger = logging.getLogger("conversation.manager")


class ConversationManager:
    """
    Single entry point for the entire conversation enrichment layer.
    Called from the Phase 4 pipeline after the critic stage.
    """

    def __init__(
        self,
        context_builder: ConversationContextBuilder = None,
        markdown_formatter: MarkdownFormatter = None,
        quality_reviewer: QualityReviewer = None,
        metrics: ConversationMetrics = None,
    ):
        self._builder = context_builder or ConversationContextBuilder()
        self._md_fmt = markdown_formatter or MarkdownFormatter()
        self._quality = quality_reviewer or QualityReviewer()
        self._metrics = metrics or conversation_metrics

    def build_context(
        self,
        intent: str,
        messages: list,
        user_profile: dict = None,
        response_content: str = "",
        intent_confidence: float = 1.0,
        agent_system_prompt: str = None,
        conversation_summary: str = None,
    ) -> ConversationContext:
        """Build the conversation context — called as pipeline stage 4.5 (before provider)."""
        return self._builder.build(
            intent=intent,
            messages=messages,
            user_profile=user_profile,
            response_content=response_content,
            intent_confidence=intent_confidence,
            agent_system_prompt=agent_system_prompt,
            conversation_summary=conversation_summary,
        )

    def review_and_format(
        self, content: str, conv_ctx: ConversationContext
    ) -> tuple:
        """
        Run quality review then markdown formatting.
        Returns (final_content, quality_result).
        Called as pipeline stage 8.
        """
        # Step 1: Quality review
        quality = self._quality.review(content, conv_ctx.style)
        reviewed = quality.corrected_content if quality.corrected_content else content

        # Step 2: Markdown format
        formatted = self._md_fmt.format(reviewed, conv_ctx.style)

        # Step 3: Metrics
        self._metrics.record(
            response_length=len(formatted),
            clarification=conv_ctx.clarification.needed,
            followup=conv_ctx.follow_up.needed,
            quality_corrections=quality.corrections_applied,
        )

        return formatted, quality
