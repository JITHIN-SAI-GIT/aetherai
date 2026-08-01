from fastapi.testclient import TestClient
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
