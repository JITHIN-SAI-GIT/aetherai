from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from .schemas.chat_completion import ChatCompletionRequest, ChatCompletionResponse
from .validators import validate_chat_request
from .stream import sse_stream_generator
from app.core.dependencies import get_orchestrator
from app.pipeline.orchestrator import Orchestrator
from app.security.guardrails import SecurityManager

router = APIRouter(tags=["Chat Completions"])

# Module-level SecurityManager — single instance, all checks centralized here
_security = SecurityManager()


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    req: ChatCompletionRequest,
    request: Request,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    # ── Security Gate — MUST be the first call ──────────────────────────────
    ip = request.client.host if request.client else "0.0.0.0"
    auth_header = request.headers.get("Authorization")
    payload = req.model_dump()

    sec = _security.check(payload, ip=ip, authorization=auth_header)
    if not sec.allowed:
        raise HTTPException(status_code=sec.http_status, detail=sec.reason)

    # ── Existing pipeline ───────────────────────────────────────────────────
    validate_chat_request(req)

    response = await orchestrator.run(req)

    if req.stream:
        return StreamingResponse(sse_stream_generator(req.model, response), media_type="text/event-stream")

    # ── Output validation (secrets, stack traces) ───────────────────────────
    if hasattr(response, "choices") and response.choices:
        for choice in response.choices:
            if hasattr(choice, "message") and hasattr(choice.message, "content"):
                if choice.message.content:
                    choice.message.content = _security.validate_output(choice.message.content)

    return response
