import os

base_path = r"c:\Users\jithin sai\OneDrive\Desktop\finalbot\backend"

directories = [
    "app/api/v1",
    "app/api/v1/schemas",
    "tests/api/v1",
]

files = {
    "app/api/v1/schemas/chat_message.py": """from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union

class FunctionCall(BaseModel):
    name: str
    arguments: str

class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: FunctionCall

class ChatMessage(BaseModel):
    role: str
    content: Optional[Union[str, List[Dict[str, Any]]]] = None
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
""",
    "app/api/v1/schemas/usage.py": """from pydantic import BaseModel

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
""",
    "app/api/v1/schemas/chat_completion.py": """from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from .chat_message import ChatMessage, ToolCall
from .usage import Usage

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None
    response_format: Optional[Dict[str, str]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    seed: Optional[int] = None

    model_config = ConfigDict(extra='ignore')

class ChatCompletionMessage(BaseModel):
    role: str = "assistant"
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatCompletionMessage
    finish_reason: Optional[str] = None

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[Usage] = None
    system_fingerprint: Optional[str] = None

class ChatCompletionChunkDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

class ChatCompletionChunkChoice(BaseModel):
    index: int
    delta: ChatCompletionChunkDelta
    finish_reason: Optional[str] = None

class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice]
    system_fingerprint: Optional[str] = None
""",
    "app/api/v1/schemas/error_schema.py": """from pydantic import BaseModel
from typing import Optional

class OpenAIErrorDetail(BaseModel):
    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None

class OpenAIErrorResponse(BaseModel):
    error: OpenAIErrorDetail
""",
    "app/api/v1/validators.py": """from .schemas.chat_completion import ChatCompletionRequest
from .errors import raise_invalid_request

def validate_chat_request(req: ChatCompletionRequest):
    valid_roles = {"system", "user", "assistant", "tool", "developer"}
    for idx, msg in enumerate(req.messages):
        if msg.role not in valid_roles:
            raise_invalid_request(
                message=f"Invalid role: {msg.role}. Allowed roles are: system, user, assistant, tool, developer",
                param=f"messages[{idx}].role"
            )
        if msg.role == "tool" and not msg.tool_call_id:
             raise_invalid_request(
                 message="tool_call_id is required for tool messages.",
                 param=f"messages[{idx}].tool_call_id"
             )
""",
    "app/api/v1/serializers.py": """from .schemas.chat_completion import ChatCompletionResponse, ChatCompletionChoice, ChatCompletionMessage
from .schemas.usage import Usage
from app.providers.models import ProviderResponse
import time
import uuid

def serialize_provider_response(resp: ProviderResponse) -> ChatCompletionResponse:
    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(time.time()),
        model=resp.model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content=resp.content
                ),
                finish_reason=resp.finish_reason
            )
        ],
        usage=Usage(
            prompt_tokens=resp.usage.get("prompt_tokens", 0),
            completion_tokens=resp.usage.get("completion_tokens", 0),
            total_tokens=resp.usage.get("total_tokens", 0)
        )
    )
""",
    "app/api/v1/errors.py": """from fastapi import HTTPException
from fastapi.responses import JSONResponse
from .schemas.error_schema import OpenAIErrorResponse, OpenAIErrorDetail

def raise_invalid_request(message: str, param: str = None, code: str = "invalid_request_error"):
    raise HTTPException(
        status_code=400,
        detail=OpenAIErrorResponse(
            error=OpenAIErrorDetail(
                message=message,
                type="invalid_request_error",
                param=param,
                code=code
            )
        ).model_dump()
    )
    
def raise_api_error(message: str, code: str = "api_error"):
    raise HTTPException(
        status_code=500,
        detail=OpenAIErrorResponse(
            error=OpenAIErrorDetail(
                message=message,
                type="api_error",
                code=code
            )
        ).model_dump()
    )

def open_ai_exception_handler(request, exc):
    if hasattr(exc, "detail") and isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=500,
        content=OpenAIErrorResponse(
            error=OpenAIErrorDetail(
                message=str(exc),
                type="api_error"
            )
        ).model_dump()
    )
""",
    "app/api/v1/stream.py": """import json
import asyncio
from typing import AsyncGenerator
from .schemas.chat_completion import ChatCompletionChunk, ChatCompletionChunkChoice, ChatCompletionChunkDelta
import time
import uuid

async def sse_stream_generator(model: str) -> AsyncGenerator[str, None]:
    req_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())
    
    chunks = ["Hello", " this", " is", " a", " test."]
    
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
    yield f"data: {chunk_data.model_dump_json(exclude_unset=True)}\\n\\n"
    
    for word in chunks:
        await asyncio.sleep(0.01)
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
        yield f"data: {chunk_data.model_dump_json(exclude_unset=True)}\\n\\n"
        
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
    yield f"data: {final_chunk.model_dump_json(exclude_unset=True)}\\n\\n"
    yield "data: [DONE]\\n\\n"
""",
    "app/api/v1/chat.py": """from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from .schemas.chat_completion import ChatCompletionRequest, ChatCompletionResponse
from .validators import validate_chat_request
from .serializers import serialize_provider_response
from .stream import sse_stream_generator
from app.providers.models import ProviderResponse

router = APIRouter(tags=["Chat Completions"])

@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(req: ChatCompletionRequest):
    validate_chat_request(req)
    
    if req.stream:
        return StreamingResponse(sse_stream_generator(req.model), media_type="text/event-stream")
        
    mock_resp = ProviderResponse(
        provider="placeholder",
        model=req.model,
        content="This is a mock response from Phase 3.",
        finish_reason="stop",
        usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        latency_ms=100,
        status=200
    )
    return serialize_provider_response(mock_resp)
""",
    "app/api/v1/models.py": """from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

class ModelObj(BaseModel):
    id: str
    object: str = "model"
    owned_by: str = "system"

class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelObj]

router = APIRouter(tags=["Models"])

@router.get("/v1/models", response_model=ModelList)
async def list_models():
    return ModelList(
        data=[
            ModelObj(id="gpt-4-turbo"),
            ModelObj(id="gpt-3.5-turbo"),
            ModelObj(id="claude-3-opus"),
            ModelObj(id="gemini-pro"),
        ]
    )

@router.get("/v1/models/{model}", response_model=ModelObj)
async def get_model(model: str):
    return ModelObj(id=model)
""",
    "tests/api/v1/test_chat_completions.py": """from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_chat_completions_non_stream():
    payload = {
        "model": "gpt-4-turbo",
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "chat.completion"
    assert "choices" in data
    assert data["choices"][0]["message"]["content"] == "This is a mock response from Phase 3."
    assert "usage" in data

def test_chat_completions_stream():
    payload = {
        "model": "gpt-4-turbo",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "stream": True
    }
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    text = resp.text
    assert "data: " in text
    assert "chat.completion.chunk" in text
    assert "[DONE]" in text
""",
    "tests/api/v1/test_openai_validation.py": """from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_invalid_role():
    payload = {
        "model": "gpt-4-turbo",
        "messages": [
            {"role": "invalid_role", "content": "Hello"}
        ]
    }
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data
    assert data["error"]["type"] == "invalid_request_error"
    assert "Invalid role" in data["error"]["message"]

def test_tool_missing_id():
    payload = {
        "model": "gpt-4-turbo",
        "messages": [
            {"role": "tool", "content": "Tool result"}
        ]
    }
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data
    assert data["error"]["type"] == "invalid_request_error"
    assert "tool_call_id is required" in data["error"]["message"]
""",
    "tests/api/v1/test_model_registry.py": """from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_list_models():
    resp = client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "list"
    assert len(data["data"]) > 0
    assert data["data"][0]["object"] == "model"
"""
}

# Create directories
for d in directories:
    dir_path = os.path.join(base_path, d)
    os.makedirs(dir_path, exist_ok=True)
    
# Create __init__.py files
for d in directories:
    parts = d.split('/')
    for i in range(1, len(parts) + 1):
        init_dir = os.path.join(base_path, *parts[:i])
        init_file = os.path.join(init_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, 'a').close()

# Create files
for file_path, content in files.items():
    full_path = os.path.join(base_path, file_path)
    os.makedirs(os.path.dirname(full_path) or base_path, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Phase 3 skeleton generated successfully.")
