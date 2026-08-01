import logging
from .context import PipelineContext
from .exceptions import PipelineRoutingError
from app.providers.registry import ProviderRegistry

logger = logging.getLogger("pipeline.router")


class ProviderRouter:
    """
    Consumes the Phase 2 ProviderRegistry to select the best available provider.
    Respects priority order, health state, and circuit breaker state.
    """

    def __init__(self, registry: ProviderRegistry):
        self._registry = registry

    def route(self, context: PipelineContext) -> PipelineContext:
        providers = self._registry.get_priority_list()

        if not providers:
            raise PipelineRoutingError(
                stage="ProviderRouter",
                message="No providers registered in the registry."
            )

        # Select first provider in priority list (circuit breaker will gate in manager)
        selected = providers[0]
        context.selected_provider = selected.name()
        context.selected_provider_instance = selected
        
        logger.info(f"Priority list: {[p.name() for p in providers]}")
        logger.info(f"Selected provider: {context.selected_provider}")
        
        if context.model == "auto" or context.model not in selected.model_list():
            context.model = selected.model_list()[0]

        logger.info(
            "Provider selected",
            extra={
                "request_id": context.request_id,
                "provider": context.selected_provider,
            }
        )
        return context
