# API Specification

## 1. POST `/v1/chat/completions` (OpenAI Compatible)
**Description**: Core endpoint to generate an AI response to a conversation. Supports streaming and tool usage.

### Request Payload
```json
{
  "model": "gpt-4-turbo",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "stream": true,
  "temperature": 0.7,
  "tools": [{"type": "web_search"}],
  "enable_memory": true
}
```

### Response (Non-streaming)
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4-turbo",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 9,
    "total_tokens": 24
  }
}
```
*Status Code*: `200 OK`

## 2. GET `/v1/models`
**Description**: Retrieve a list of available AI models and their configured routing rules.

### Response
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4-turbo",
      "object": "model",
      "owned_by": "openai",
      "routing": ["openai", "openrouter"]
    }
  ]
}
```
*Status Code*: `200 OK`

## 3. GET `/v1/memory`
**Description**: Retrieve stored long-term semantic memory for the authenticated user.

### Response
```json
{
  "memories": [
    {"id": "550e8400", "entity": "Preference", "content": "User prefers concise Python code.", "created_at": "2024-01-01T10:00:00Z"}
  ]
}
```
*Status Code*: `200 OK`

## 4. POST `/v1/search`
**Description**: Manual trigger for the web search subsystem to populate cache or verify results.

### Request
```json
{"query": "latest AI industry news 2024"}
```

### Response
```json
{
  "results": [
    {"title": "OpenAI releases new model", "url": "https://example.com/news", "snippet": "Today..."}
  ]
}
```
*Status Code*: `200 OK`

## Internal Endpoints (Protected)

### 5. GET `/internal/providers`
**Description**: Real-time health check and status of all configured AI providers. Used by Load Balancers.
*Status Code*: `200 OK` (if all primary are up) / `207 Multi-Status` (if degraded).

### 6. GET `/internal/metrics`
**Description**: Prometheus-compatible metrics endpoint for scraping telemetry and provider latencies.
*Status Code*: `200 OK`

## Global Error Schema
Standardized error responses across all endpoints.
```json
{
  "error": {
    "message": "Rate limit exceeded. Try again in 30 seconds.",
    "type": "rate_limit_error",
    "code": 429
  }
}
```

## Authentication & Security
* **Protocol**: JWT (JSON Web Tokens).
* **Header**: Requires `Authorization: Bearer <token>` on all `/v1/*` endpoints.
* **RBAC**: Internal endpoints require admin-scoped JWTs.
