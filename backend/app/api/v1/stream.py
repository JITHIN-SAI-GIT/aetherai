import json
import asyncio
import time
from typing import AsyncGenerator
from .schemas.chat_completion import ChatCompletionChunk, ChatCompletionChunkChoice, ChatCompletionChunkDelta
import uuid

# Wall-clock limit for the entire streaming response.
# The pipeline asyncio.wait_for (12s) handles pre-stream hangs (search, provider selection).
# This limit only kills a stream that stalls completely *after* content has started flowing.
# 30s gives enough time for a long multilingual response (Hindi/Telugu) to finish.
STREAM_WALL_CLOCK_TIMEOUT = 30.0

# SSE error event sent when streaming fails. The frontend listens for
# `event: error` lines and REPLACES the partial message (rather than appending)
# so the user never sees mid-sentence timeout text concatenated with a warning.
_SSE_ERROR_TIMEOUT  = 'event: error\ndata: {"type":"timeout","message":"The request took too long — please try again."}\n\n'
_SSE_ERROR_PROVIDER = 'event: error\ndata: {"type":"provider_unavailable","message":"All AI providers are currently busy — please try again in a moment."}\n\n'
_SSE_ERROR_EMPTY    = 'event: error\ndata: {"type":"empty_response","message":"No response received — providers may be rate-limited. Please try again."}\n\n'


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
            elapsed = time.monotonic() - stream_start

            if elapsed > STREAM_WALL_CLOCK_TIMEOUT:
                if received_any_content:
                    # Content was already streaming — end cleanly so the user keeps
                    # what they already read, rather than clearing it with an error.
                    yield _make_chunk(finish_reason="stop")
                else:
                    # Nothing shown yet — emit a proper error event so the UI can
                    # display a clear message instead of staying on "Thinking..."
                    yield _SSE_ERROR_TIMEOUT
                yield "data: [DONE]\n\n"
                return

            if word:
                received_any_content = True
                yield _make_chunk(content=word)


        # Normal completion
        if not received_any_content:
            yield _SSE_ERROR_EMPTY
        else:
            yield _make_chunk(finish_reason="stop")

    except Exception as exc:
        import logging
        logging.getLogger("api.stream").error(
            "Streaming failed — sending error event to client",
            extra={"error": str(exc), "model": model},
        )
        yield _SSE_ERROR_PROVIDER

    yield "data: [DONE]\n\n"
