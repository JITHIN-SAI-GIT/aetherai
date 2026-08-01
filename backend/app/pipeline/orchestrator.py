import uuid
import logging
from app.api.v1.schemas.chat_completion import ChatCompletionRequest, ChatCompletionResponse
from app.providers.models import ProviderResponse
from .context import PipelineContext
from .pipeline import Pipeline

# Default max output tokens — enforced here so it applies even when the client
# sends no max_tokens field (Fix 4 — latency cap).
DEFAULT_MAX_TOKENS = 450

logger = logging.getLogger("pipeline.orchestrator")


class Orchestrator:
    """
    Single top-level entry point for all chat requests.
    API routes call ONLY orchestrator.run() — no business logic lives in routes.
    """

    def __init__(self, pipeline: Pipeline):
        self._pipeline = pipeline

    async def run(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        request_id = str(uuid.uuid4())

        # Apply max_tokens cap: use client value if provided and ≤ cap, else default.
        requested_max = request.max_tokens
        if not requested_max or requested_max > DEFAULT_MAX_TOKENS:
            effective_max_tokens = DEFAULT_MAX_TOKENS
        else:
            effective_max_tokens = requested_max

        logger.info(
            "Pipeline invoked",
            extra={
                "request_id": request_id,
                "model":      request.model,
                "stream":     request.stream,
                "max_tokens": effective_max_tokens,
                "msg_count":  len(request.messages),
            },
        )

        context = PipelineContext(
            request_id=request_id,
            user_id=request.user or None,
            messages=[m.model_dump(exclude_none=True) for m in request.messages],
            model=request.model,
            temperature=request.temperature or 1.0,
            max_tokens=effective_max_tokens,
            stream=request.stream or False,
            raw_request=request,
        )
        import asyncio
        from fastapi import HTTPException

        try:
            context = await asyncio.wait_for(self._pipeline.run(context), timeout=12.0)
        except asyncio.TimeoutError:
            logger.error("Pipeline execution timed out — returning graceful fallback", extra={"request_id": request_id})
            if request.stream:
                raise HTTPException(status_code=504, detail="Request timed out. Please try again.")
            
            # Non-streaming fallback
            context.provider_response = ProviderResponse(
                provider="timeout_fallback",
                model=request.model,
                content="Hmm, the request took too long to respond — mind trying that again? 🙏",
                finish_reason="stop",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                latency_ms=12000,
                status=504,
            )
            context.degraded = True
            
            from app.pipeline.formatter import Formatter
            context = Formatter().format(context)

        if request.stream:
            return context.provider_response

        return context.formatted_response
