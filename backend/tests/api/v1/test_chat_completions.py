from fastapi.testclient import TestClient
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
    assert data["choices"][0]["message"]["content"]  # non-empty response from pipeline
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
