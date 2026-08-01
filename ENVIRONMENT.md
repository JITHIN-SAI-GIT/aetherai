# Environment Variables

Environment variables follow a strict grouping based on domain responsibility. 

## Application Core
* `ENV`: Deployment environment (`development`, `staging`, `production`). Controls debug modes, CORS policies, and logging verbosity.
* `SECRET_KEY`: High-entropy cryptographic string used for signing JWT tokens and encrypting sensitive user data.
* `PORT`: The internal port the FastAPI server binds to (Default: `8000`).

## Database & Caching Layer
* `DATABASE_URL`: Connection string for PostgreSQL containing credentials and db name (e.g., `postgresql://user:pass@db:5432/chatbot`).
* `REDIS_URL`: Connection string for Redis instance used for rate limits and caching (e.g., `redis://redis:6379/0`).

## AI Provider API Keys
* `OPENAI_API_KEY`: Authentication key for OpenAI model access.
* `ANTHROPIC_API_KEY`: Authentication key for Anthropic Claude models.
* `GEMINI_API_KEY`: Authentication key for Google Gemini.
* `GROQ_API_KEY`: Authentication key for Groq's low-latency inference endpoints.
* `OPENROUTER_API_KEY`: Authentication key for OpenRouter, utilized primarily as a fallback aggregator.

## Search Engine Integrations
* `SEARCH_API_KEY`: API key for external search providers (e.g., Bing Web Search, Google Custom Search).
* `SEARCH_PROVIDER`: Designates which search engine abstraction class to instantiate (e.g., `duckduckgo`, `bing`).

## Rate Limiting & Protections
* `RATE_LIMIT_FREE`: Configures requests-per-minute threshold for free tier users (e.g., `10/minute`).
* `RATE_LIMIT_PRO`: Configures requests-per-minute threshold for pro/premium tier users (e.g., `100/minute`).
* `MAX_TOKENS_PER_REQUEST`: Hard ceiling on generation tokens requested from providers to prevent malicious budget exhaustion.

## Observability & Telemetry
* `LOG_LEVEL`: Configures standard logging output (`INFO`, `DEBUG`, `WARNING`, `ERROR`).
* `ENABLE_TRACING`: Boolean (`true`/`false`) to toggle OpenTelemetry distributed request tracing.
