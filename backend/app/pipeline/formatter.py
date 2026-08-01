import logging
from .context import PipelineContext
from app.api.v1.serializers import serialize_provider_response

logger = logging.getLogger("pipeline.formatter")


class Formatter:
    """
    Converts ProviderResponse → ChatCompletionResponse.
    Builds aether_meta from conversation context so tone mirroring
    and provider information are visible in the response (Fix 11).
    """

    def format(self, context: PipelineContext) -> PipelineContext:
        # Build aether_meta from available context
        aether_meta = {
            "provider": context.selected_provider or "unknown",
            "model":    context.model or "unknown",
        }

        if context.conversation_context:
            meta = context.conversation_context.metadata or {}
            aether_meta["tone"]              = getattr(context.conversation_context.tone, "tone", None)
            aether_meta["detected_language"] = meta.get("detected_language")
            aether_meta["intent"]            = meta.get("intent")

        if context.search_response:
            aether_meta["search_used"]     = True
            aether_meta["search_provider"] = context.search_response.provider
            aether_meta["search_cache_hit"] = context.search_response.cache_hit

        context.formatted_response = serialize_provider_response(
            context.provider_response,
            aether_meta=aether_meta,
        )

        logger.info(
            "Response formatted",
            extra={
                "request_id":  context.request_id,
                "response_id": context.formatted_response.id,
                "tone":        aether_meta.get("tone"),
                "language":    aether_meta.get("detected_language"),
                "provider":    aether_meta.get("provider"),
            },
        )
        return context
