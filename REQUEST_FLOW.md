# Request Flows

## 1. Normal Conversation
Standard flow for stateless chat generation with context loading.

```mermaid
sequenceDiagram
    participant Client
    participant APIGateway as API Gateway
    participant Router
    participant Memory
    participant Provider
    participant DB
    
    Client->>APIGateway: POST /v1/chat/completions (messages)
    APIGateway->>APIGateway: Validate JWT Auth & Redis Rate Limit
    APIGateway->>Router: Forward Validated Request
    Router->>Memory: Fetch Conversation History (Session ID)
    Memory-->>Router: Context (Past Messages + System Prompt)
    Router->>Provider: generate(messages + context)
    Provider-->>Router: Response Content & Token Usage
    Router->>DB: Save User Message & AI Response
    Router-->>APIGateway: Format Response Payload
    APIGateway-->>Client: 200 OK (Response JSON)
```

## 2. Search Conversation
Flow illustrating Agentic tool usage where the LLM decides to browse the web.

```mermaid
sequenceDiagram
    participant Client
    participant Router
    participant Provider
    participant SearchEngine as Web Search Service
    
    Client->>Router: POST /v1/chat/completions (query, enable_search=True)
    Router->>Provider: generate() with Search Tool Definition
    Provider-->>Router: ToolCall: search_web(query)
    Router->>SearchEngine: Execute query against Bing/DDG
    SearchEngine-->>Router: Search Results (Snippets, URLs)
    Router->>Provider: generate(messages + tool_results)
    Provider-->>Router: Final Synthesis with Citations
    Router-->>Client: 200 OK (Response with Citations)
```

## 3. Streaming Conversation
Flow detailing low-latency token-by-token transmission to the client.

```mermaid
sequenceDiagram
    participant Client
    participant Router
    participant Provider
    participant DB
    
    Client->>Router: POST /v1/chat/completions (stream=true)
    Router->>Provider: generate_stream()
    loop Chunk by Chunk (Generator)
        Provider-->>Router: yield token chunk
        Router-->>Client: SSE Event data: {chunk}
    end
    Router->>DB: Async Background Save of Complete Assembled Message
    Provider-->>Router: Stream End signal
    Router-->>Client: SSE Event data: [DONE]
```

## 4. Provider Failover
Flow demonstrating system resilience when a primary AI API goes down.

```mermaid
sequenceDiagram
    participant Router
    participant PrimaryProvider as OpenAI (Primary)
    participant FallbackProvider as Anthropic (Fallback)
    
    Router->>PrimaryProvider: generate()
    PrimaryProvider--xRouter: HTTP 503 / Timeout Exception
    Router->>Router: Log failure & Increment Error Metrics
    Router->>FallbackProvider: generate() (Seamless swap)
    FallbackProvider-->>Router: Response Content
    Router-->>Client: 200 OK (Response from Fallback)
```

## 5. Memory Update
Background process for updating long-term semantic memory and context summarization.

```mermaid
sequenceDiagram
    participant Router
    participant BackgroundWorker as Celery/Background Task
    participant DB
    participant Provider
    
    Router->>BackgroundWorker: Trigger memory extraction (session_id)
    BackgroundWorker->>DB: Fetch recent unsummarized messages
    BackgroundWorker->>Provider: Prompt: "Extract facts and preferences"
    Provider-->>BackgroundWorker: Structured JSON (Entities)
    BackgroundWorker->>DB: Upsert Vectors to pgvector Memory table
    BackgroundWorker->>DB: Update conversation_summary and pointer
```
