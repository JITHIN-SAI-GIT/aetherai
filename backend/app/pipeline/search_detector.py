import logging
from .context import PipelineContext, SearchDecision, RoutingStrategy
from app.search.detector import SearchNecessityDetector

logger = logging.getLogger("pipeline.search_detector")


class SearchDetector:
    """
    Pipeline stage for detecting search necessity using the SearchNecessityDetector.
    """
    
    def __init__(self):
        self._detector = SearchNecessityDetector()

    def detect(self, context: PipelineContext) -> PipelineContext:
        # Get the latest user query, if any
        query = ""
        if context.messages and context.messages[-1].get("role") == "user":
            query = context.messages[-1].get("content", "")
            
        decision = self._detector.detect(query, intent=context.intent)
        
        context.search_decision = SearchDecision(
            required=decision.required, 
            reason=decision.reason
        )

        # ── Routing strategy decision ──────────────────────────────────────────
        has_memory = bool(context.memory_facts)
        if decision.required and has_memory:
            context.routing_strategy = RoutingStrategy.HYBRID
        elif decision.required:
            context.routing_strategy = RoutingStrategy.SEARCH
        elif has_memory:
            context.routing_strategy = RoutingStrategy.MEMORY
        else:
            context.routing_strategy = RoutingStrategy.INTERNAL

        logger.info(
            "Search decision",
            extra={
                "request_id": context.request_id,
                "search_required": context.search_decision.required,
                "reason": context.search_decision.reason,
                "routing_strategy": context.routing_strategy.value,
            }
        )
        return context
