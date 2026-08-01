# Logging & Observability Strategy

## 1. Structured JSON Logging
To ensure maximum compatibility with modern log aggregators (ELK Stack, Grafana Loki, Datadog), all backend logs are emitted strictly in JSON format. Plaintext logs are prohibited in production.

**Standard Log Payload:**
```json
{
  "timestamp": "2023-10-27T10:00:00.123Z",
  "level": "INFO",
  "correlation_id": "req-9876-uuid-1234",
  "module": "api.routes.chat",
  "message": "Chat completion successful",
  "duration_ms": 840,
  "user_id": "usr-5555"
}
```

## 2. Correlation IDs for Distributed Tracing
* **Generation**: Upon receiving an HTTP request, the API Gateway middleware checks for an `X-Correlation-ID` header. If absent, a new UUID is generated.
* **Propagation**: This ID is injected into the request context (via ContextVars in Python).
* **Usage**: Every log emitted during the lifecycle of that request—from database queries to API provider calls—includes this ID. This allows engineers to filter logs by `correlation_id` and view the exact chronological sequence of a single user's request across all microservices.

## 3. Provider Metrics & Telemetry
Because LLM API latency and stability are highly variable, strict monitoring of external providers is required.
Every invocation of an AI provider emits a specific metrics log containing:
* `provider_name` (e.g., openai, anthropic)
* `model_name` (e.g., gpt-4-turbo)
* `time_to_first_token_ms` (critical for streaming UX)
* `total_latency_ms`
* `input_tokens` / `output_tokens`
* `http_status_code`

These data points are scraped by **Prometheus** and visualized in **Grafana** to trigger automated alerts if, for example, Anthropic's latency spikes above 3 seconds, allowing engineers to manually adjust routing if the automated failover requires tuning.

## 4. Distributed Tracing (OpenTelemetry)
* The architecture utilizes **OpenTelemetry** to instrument the FastAPI application and SQLAlchemy database calls.
* Traces map the exact execution time of distinct operational spans: `Gateway Routing` -> `DB Fetch Context` -> `Provider API Call` -> `DB Save Response`.
* This ensures that if overall response latency increases, engineers can immediately identify the exact bottleneck layer.

## 5. Security & Privacy Constraints
* **No PII Logging**: User emails, raw passwords, and actual chat message contents are **strictly prohibited** from being written to system logs.
* Logs must only contain metadata (token counts, UUIDs, statuses). 
* To debug prompt-engineering issues without logging PII, isolated testing environments or opt-in telemetry channels are used.
