import json
import asyncio
from typing import AsyncGenerator
from .schemas.chat_completion import ChatCompletionChunk, ChatCompletionChunkChoice, ChatCompletionChunkDelta
import time
import uuid

async def sse_stream_generator(model: str, content_stream: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    req_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())
    
    chunk_data = ChatCompletionChunk(
        id=req_id,
        created=created,
        model=model,
        choices=[
            ChatCompletionChunkChoice(
                index=0,
                delta=ChatCompletionChunkDelta(role="assistant", content=""),
                finish_reason=None
            )
        ]
    )
    yield f"data: {chunk_data.model_dump_json(exclude_none=True)}\n\n"
    
    async for word in content_stream:
        chunk_data = ChatCompletionChunk(
            id=req_id,
            created=created,
            model=model,
            choices=[
                ChatCompletionChunkChoice(
                    index=0,
                    delta=ChatCompletionChunkDelta(content=word),
                    finish_reason=None
                )
            ]
        )
        yield f"data: {chunk_data.model_dump_json(exclude_none=True)}\n\n"
        
    final_chunk = ChatCompletionChunk(
        id=req_id,
        created=created,
        model=model,
        choices=[
            ChatCompletionChunkChoice(
                index=0,
                delta=ChatCompletionChunkDelta(),
                finish_reason="stop"
            )
        ]
    )
    yield f"data: {final_chunk.model_dump_json(exclude_none=True)}\n\n"
    yield "data: [DONE]\n\n"
