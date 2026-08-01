import logging
from .context import PipelineContext, UserContext

logger = logging.getLogger("pipeline.memory_loader")


class ContextLoader:
    """
    Loads memory context into the pipeline.
    Wires into MemoryManager when fully initialized; falls back to
    empty UserContext so the pipeline never blocks on missing memory.

    User ID resolution order:
        1. context.user_id  — stable ID from the frontend (preferred)
        2. context.request_id — per-request UUID (fallback, no cross-session memory)
    """

    def __init__(self, memory_manager=None):
        self._memory_manager = memory_manager

    async def load(self, context: PipelineContext) -> PipelineContext:
        # Resolve the stable user identifier
        user_id = context.user_id or context.request_id
        if not context.user_id:
            logger.warning(
                "No stable user_id on context — memory will not persist across sessions. "
                "Pass the 'user' field in ChatCompletionRequest for persistent memory.",
                extra={"request_id": context.request_id},
            )

        if self._memory_manager:
            try:
                data = await self._memory_manager.load(user_id, session_id=context.request_id)
                context.user_context = UserContext(
                    user_id=user_id,
                    preferences=data.get("preferences", {}),
                    conversation_summary=None,
                    session_metadata={"profile": data.get("profile", {})},
                )
                logger.info(
                    "Memory loaded from manager",
                    extra={"request_id": context.request_id, "user_id": user_id},
                )
                return context
            except Exception as e:
                logger.warning(
                    "Memory load failed, using empty context",
                    extra={"error": str(e)},
                )

        # Fallback: empty context
        context.user_context = UserContext(
            user_id=user_id,
            preferences={},
            conversation_summary=None,
            session_metadata={},
        )
        logger.info(
            "Context loaded (fallback)",
            extra={"request_id": context.request_id, "user_id": user_id},
        )
        return context
