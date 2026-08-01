import logging
from typing import List

from .context import PipelineContext
from app.search.models import SearchResult

logger = logging.getLogger("pipeline.citation_appender")


class CitationAppender:
    """
    Pipeline Stage 9.5 — Citation Appending.

    Runs after Format Response (Stage 9) and before Memory Update (Stage 10).
    Appends a structured **Sources** block to the LLM response content when
    context.search_citations is populated (i.e. when a live search was performed).

    Format example:
        ---
        **Sources:**
        [1] Latest React 19 features — https://react.dev/blog/...
        [2] React changelog — https://github.com/...

    No-op when:
    - context.stream is True (streaming responses are not modified post-hoc)
    - context.search_citations is empty
    - context.provider_response is None
    """

    def append(self, context: PipelineContext) -> PipelineContext:
        if context.stream:
            return context  # cannot append to a streaming response

        citations: List[dict] = context.search_citations
        if not citations:
            logger.debug(
                "No citations to append",
                extra={"request_id": context.request_id},
            )
            return context

        if not context.provider_response:
            logger.debug(
                "No provider response — skipping citation append",
                extra={"request_id": context.request_id},
            )
            return context

        # Build citation block
        lines = ["\n\n---", "**Sources:**"]
        for c in citations:
            idx   = c.get("index", "?")
            title = c.get("title", "Result")
            url   = c.get("url", "")
            lines.append(f"[{idx}] {title} — {url}")

        citation_block = "\n".join(lines)
        context.provider_response.content = (
            (context.provider_response.content or "") + citation_block
        )

        logger.info(
            "Citations appended",
            extra={
                "request_id": context.request_id,
                "citation_count": len(citations),
                "routing_strategy": context.routing_strategy.value,
            },
        )
        return context
