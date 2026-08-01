import logging
from typing import List

from .context import PipelineContext
from app.search.models import SearchResult

logger = logging.getLogger("pipeline.search_injector")

# Maximum number of search results to inject into the prompt
MAX_INJECT_RESULTS = 5

_BLOCK_HEADER = (
    "═══════════════════════════════════════════════════════════════\n"
    "  LIVE SEARCH RESULTS  (fetched just now — treat as ground truth)\n"
    "═══════════════════════════════════════════════════════════════\n"
)
_BLOCK_FOOTER = (
    "═══════════════════════════════════════════════════════════════\n"
    "Use the search results above to answer the user accurately.\n"
    "Always refer to the sources by their [N] index when citing facts.\n"
    "Never rely on your training data for facts covered by the results.\n"
    "═══════════════════════════════════════════════════════════════"
)


class SearchInjector:
    """
    Pipeline Stage 4.7 — Search Context Injection.

    Runs after system-prompt injection (Stage 4.6) and BEFORE provider routing
    (Stage 5).  Builds a structured grounding block from context.search_response
    and prepends it to the system message so the LLM treats search results as
    authoritative ground truth for this response.

    No-op when context.search_response is None or has no results.
    """

    def inject(self, context: PipelineContext) -> PipelineContext:
        if not context.search_response or not context.search_response.results:
            logger.debug(
                "No search results to inject",
                extra={"request_id": context.request_id},
            )
            return context

        results: List[SearchResult] = context.search_response.results[:MAX_INJECT_RESULTS]

        # Build numbered result entries
        entries: List[str] = []
        for i, r in enumerate(results, start=1):
            parts = [f"[{i}] {r.title}"]
            if r.snippet:
                parts.append(f"    {r.snippet[:350]}")
            if r.source:
                parts.append(f"    Source: {r.source}")
            parts.append(f"    URL: {r.url}")
            entries.append("\n".join(parts))

        grounding_block = (
            _BLOCK_HEADER
            + "\n\n".join(entries)
            + "\n\n"
            + _BLOCK_FOOTER
        )

        # Also populate context.search_citations for the CitationAppender stage
        context.search_citations = [
            {"index": str(i), "title": r.title, "url": r.url}
            for i, r in enumerate(results, start=1)
        ]

        # Inject into messages: prepend to existing system message or insert new one
        if context.messages and context.messages[0].get("role") == "system":
            existing = context.messages[0].get("content") or ""
            context.messages[0]["content"] = (
                grounding_block
                + ("\n\n" + existing if existing.strip() else "")
            )
        else:
            context.messages.insert(0, {"role": "system", "content": grounding_block})

        logger.info(
            "Search context injected",
            extra={
                "request_id": context.request_id,
                "results_injected": len(results),
                "provider": context.search_response.provider,
                "routing_strategy": context.routing_strategy.value,
            },
        )
        return context
