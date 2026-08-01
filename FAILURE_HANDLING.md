# Failure Handling Strategy

A robust architecture must expect and elegantly mitigate failures. Below is the exact protocol for handling various sub-system failures.

## 1. External AI Provider Timeout or 5xx Error
* **Condition**: The underlying HTTP client (e.g., HTTPX) raises a timeout, or the provider API returns a 500, 502, 503, or 504 status code.
* **Action**: The exception is caught at the `ProviderManager` abstraction layer.
* **Resolution**: The system automatically initiates a **Provider Failover**. It consults the routing configuration, shifts to the next provider in the priority chain (e.g., `OpenAI -> Anthropic -> OpenRouter`), and re-attempts the generation. The user experiences slightly higher latency but receives a response. If all fallbacks are exhausted, a 503 JSON error is returned to the client explaining upstream unavailability.

## 2. Rate Limit Exceeded (User-Level)
* **Condition**: The API Gateway Redis middleware detects that the user's request count has surpassed their tier's threshold.
* **Action**: The request is intercepted immediately.
* **Resolution**: Returns a HTTP `429 Too Many Requests` status code. The response includes a `Retry-After` header indicating exactly when the client can make their next request.

## 3. Web Search Engine Failure
* **Condition**: The external search API (Bing/DuckDuckGo) times out or returns an error during an agentic search execution.
* **Action**: The `SearchService` catches the error.
* **Resolution**: Instead of aborting the request, the system injects a system-level observation into the LLM context stating: *"Web search is currently unavailable. Proceed by answering based on your internal knowledge base."* The LLM synthesizes an answer without web data, and the conversation continues smoothly.

## 4. Redis Cluster Down
* **Condition**: The backend cannot establish a connection to Redis to check rate limits or fetch session caches.
* **Action**: Redis clients are configured with very aggressive (short) timeouts to prevent hanging the main thread.
* **Resolution**: 
  - **Rate Limiting**: Fails open (bypasses rate limits entirely). It is better to temporarily allow excessive traffic than to bring down the entire service.
  - **Caching**: Falls back to querying the PostgreSQL database directly for session verification.
  - **Monitoring**: High-priority alerts are immediately dispatched to DevOps via Prometheus/Grafana.

## 5. PostgreSQL Database Unavailable
* **Condition**: The application connection pool fails to acquire a connection to PostgreSQL.
* **Action**: This is an unrecoverable error as data persistence and verification are compromised.
* **Resolution**: The API Gateway intercepts the database connection exception and immediately returns a `503 Service Unavailable` response to the client. Background queues pause processing until DB health checks pass.

## 6. Client Streaming Interruption
* **Condition**: The user closes their browser tab or loses network connectivity mid-stream, or the provider stream abruptly closes.
* **Action**: FastAPI detects an `asyncio.CancelledError` or a broken pipe.
* **Resolution**: The backend halts generation, truncates the message payload to exactly what was successfully received by the router, commits the partial message to the database to ensure UI sync upon reconnect, and cleanly terminates the socket.

## 7. Memory / Vector DB Write Failure
* **Condition**: Background tasks fail to write new extracted vectors into the pgvector tables.
* **Action**: Caught by the background worker in `MemoryService`.
* **Resolution**: The immediate chat response is unaffected (as this runs asynchronously). The system queues the failed memory update payload in a dead-letter queue (Redis/RabbitMQ) with exponential backoff for later retry.
