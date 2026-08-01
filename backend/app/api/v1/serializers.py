"""
Response serializer — converts ProviderResponse → ChatCompletionResponse.
Includes aether_meta for tone mirroring visibility (Fix 11).
"""
from .schemas.chat_completion import ChatCompletionResponse, ChatCompletionChoice, ChatCompletionMessage
from .schemas.usage import Usage
from app.providers.models import ProviderResponse
import time
import uuid
from typing import Optional, Dict, Any


def serialize_provider_response(
    resp: ProviderResponse,
    aether_meta: Optional[Dict[str, Any]] = None,
) -> ChatCompletionResponse:
    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(time.time()),
        model=resp.model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content=resp.content,
                ),
                finish_reason=resp.finish_reason,
            )
        ],
        usage=Usage(
            prompt_tokens=resp.usage.get("prompt_tokens", 0),
            completion_tokens=resp.usage.get("completion_tokens", 0),
            total_tokens=resp.usage.get("total_tokens", 0),
        ),
        aether_meta=aether_meta or resp.metadata or {},
    )
