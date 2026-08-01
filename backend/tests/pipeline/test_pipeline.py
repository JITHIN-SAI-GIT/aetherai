import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_pipeline_non_stream_e2e():
    """End-to-end: POST /v1/chat/completions flows through the full pipeline."""
    payload = {
        "model": "gpt-4-turbo",
        "messages": [{"role": "user", "content": "Hello pipeline!"}],
    }
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert data["choices"][0]["message"]["content"]


def test_pipeline_invalid_role_returns_400():
    payload = {
        "model": "gpt-4-turbo",
        "messages": [{"role": "bot", "content": "Hi"}],
    }
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 400
    assert resp.json()["error"]["type"] == "invalid_request_error"
