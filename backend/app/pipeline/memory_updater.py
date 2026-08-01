import logging
from .context import PipelineContext

logger = logging.getLogger("pipeline.memory_updater")


class MemoryUpdater:
    """
    Extracts facts from the completed pipeline context and persists them.
    Uses the same stable user_id resolution as ContextLoader so that saved
    facts are retrievable by the same user in future turns.

    User ID resolution order (mirrors ContextLoader):
        1. context.user_id  — stable ID from the frontend (preferred)
        2. context.request_id — per-request UUID (fallback)
    """

    def __init__(self, memory_manager=None):
        self._memory_manager = memory_manager

    async def update(self, context: PipelineContext) -> PipelineContext:
        # Mirror the same resolution used in ContextLoader
        user_id = context.user_id or context.request_id

        if self._memory_manager:
            try:
                result = await self._memory_manager.extract(
                    context.messages,
                    user_id=user_id,
                    session_turn=len(context.messages),
                )
                await self._memory_manager.save(user_id, result)
                context.memory_facts = [item.key for item in result.items]
                logger.info(
                    "Memory updated via manager",
                    extra={
                        "request_id": context.request_id,
                        "user_id": user_id,
                        "facts": len(result.items),
                    },
                )
                return context
            except Exception as e:
                logger.warning("Memory update failed", extra={"error": str(e)})

        # Fallback: produce mock facts so the pipeline remains compatible
        context.memory_facts = []
        if context.intent == "coding":
            context.memory_facts.append("preferred_language")
        logger.info(
            "Memory update triggered (fallback)",
            extra={
                "request_id": context.request_id,
                "user_id": user_id,
                "facts_extracted": len(context.memory_facts),
            },
        )
        return context
