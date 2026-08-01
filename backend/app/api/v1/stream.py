import json
import asyncio
import time
from typing import AsyncGenerator
from .schemas.chat_completion import ChatCompletionChunk, ChatCompletionChunkChoice, ChatCompletionChunkDelta
import uuid

# Wall-clock limit for the entire streaming response (backend pipeline timeout is 12s;
# this gives 2s grace then hard-aborts so the frontend never waits indefinitely).
STREAM_WALL_CLOCK_TIMEOUT = 14.0


async def sse_stream_generator(model: str, content_stream: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    req_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())

    def _make_chunk(content: str = "", finish_reason=None, role=None) -> str:
        delta = ChatCompletionChunkDelta(content=content or None, role=role)
        chunk = ChatCompletionChunk(
            id=req_id,
            created=created,
            model=model,
            choices=[
                ChatCompletionChunkChoice(
                    index=0,
                    delta=delta,
                    finish_reason=finish_reason,
                )
            ],
        )
        return f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"

    # Opening role chunk
    yield _make_chunk(role="assistant")

    stream_start = time.monotonic()
    received_any_content = False

    try:
        async for word in content_stream:
            # Enforce wall-clock timeout — if we've been streaming too long, abort.
            if time.monotonic() - stream_start > STREAM_WALL_CLOCK_TIMEOUT:
                yield _make_chunk(
                    content="\n\n⚠️ Response timed out — please try again.",
                    finish_reason="stop",
                )
                yield "data: [DONE]\n\n"
                return

            if word:
                received_any_content = True
                yield _make_chunk(content=word)

        # Normal completion
        if not received_any_content:
            # Stream ended cleanly but empty — surface an error chunk
            yield _make_chunk(
                content="⚠️ No response received — all providers may be rate-limited. Please try again in a moment.",
                finish_reason="stop",
            )
        else:
            yield _make_chunk(finish_reason="stop")

    except Exception as exc:
        # Provider failure (NoAvailableProviderError, etc.) — never crash the ASGI layer.
        # Always emit a graceful error chunk so the frontend knows the stream is done.
        import logging
        logging.getLogger("api.stream").error(
            "Streaming failed — sending error chunk to client",
            extra={"error": str(exc), "model": model},
        )
        yield _make_chunk(
            content="\n\n⚠️ All providers are currently unavailable — please try again in a moment.",
            finish_reason="stop",
        )

    yield "data: [DONE]\n\n"
