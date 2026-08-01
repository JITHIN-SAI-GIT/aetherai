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

        try:
            context = await asyncio.wait_for(self._pipeline.run(context), timeout=12.0)
        except asyncio.TimeoutError:
            logger.error("Pipeline execution timed out — returning graceful fallback", extra={"request_id": request_id})
            if request.stream:
                # For streaming requests: never raise HTTP 504.
                # Instead, return a one-shot async generator that yields the timeout
                # message as an SSE content chunk.  The sse_stream_generator will
                # wrap it and send [DONE] — so the client always gets a clean stream end.
                async def _timeout_stream():
                    yield "⚠️ The request took too long to respond — all AI providers may be busy. Please try again in a moment."

                return _timeout_stream()

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

