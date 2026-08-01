from .schemas.chat_completion import ChatCompletionRequest
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
