import logging
from typing import TYPE_CHECKING

from .context import PipelineContext

if TYPE_CHECKING:
    from app.search.engine import SearchEngine

logger = logging.getLogger("pipeline.search_executor")


class SearchExecutor:
    """
    Pipeline Stage 3.5 — Live Search Execution.

    Runs immediately after SearchDetector (Stage 3).
    If search_decision.required is True, calls SearchEngine.search() and
    stores the SearchResponse in context.search_response.

    Failures are non-fatal: a warning is logged and the pipeline continues
    without search results (routing_strategy falls back to INTERNAL).
    """

    def __init__(self, engine: "SearchEngine"):
        self._engine = engine

    async def execute(self, context: PipelineContext) -> PipelineContext:
        if not context.search_decision.required:
            logger.debug(
                "Search not required — skipping execution",
                extra={"request_id": context.request_id},
            )
            return context

        # Extract the raw query from the last user message
        query = ""
        for msg in reversed(context.messages):
            if msg.get("role") == "user":
                query = msg.get("content", "")
                break

        if not query:
            logger.warning(
                "Search required but no user query found in messages",
                extra={"request_id": context.request_id},
            )
            return context

        try:
            # Map the search decision category to the engine
            from app.search.models import SearchCategory
            category_map = {
                "news":    SearchCategory.NEWS,
                "weather": SearchCategory.WEATHER,
                "sports":  SearchCategory.SPORTS,
                "general": SearchCategory.GENERAL,
            }
            # Use the category from the *detector*, not the pipeline SearchDecision
            # (pipeline SearchDecision only has required + reason)
            # Re-run detect to get the full decision with category
            from app.search.detector import SearchNecessityDetector
            full_decision = SearchNecessityDetector().detect(query, intent=context.intent)
            category = category_map.get(full_decision.category.value, SearchCategory.GENERAL)

            logger.info(
                "Executing live search",
                extra={
                    "request_id": context.request_id,
                    "query": query[:100],
                    "category": category.value,
                    "routing_strategy": context.routing_strategy.value,
                },
            )

            context.search_response = await self._engine.search(query, category)

            logger.info(
                "Search execution complete",
                extra={
                    "request_id": context.request_id,
                    "results_count": len(context.search_response.results),
                    "provider": context.search_response.provider,
                    "cache_hit": context.search_response.cache_hit,
                    "latency_ms": context.search_response.latency_ms,
                },
            )

        except Exception as exc:
            logger.warning(
                "Search execution failed — continuing without search results",
                extra={"request_id": context.request_id, "error": str(exc)},
            )
            context.errors.append(f"SearchExecutor: {exc}")
            # Do NOT set degraded=True — search failure is non-fatal

        return context
