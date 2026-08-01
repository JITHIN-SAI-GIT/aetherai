# System Architecture

## Overview
The architecture is designed as a modular, scalable, and resilient enterprise-grade AI chatbot system. It separates concerns between the client UI, API gateway, routing logic, provider abstractions, memory management, and external integrations.

## System Architecture Diagram

```mermaid
graph TD
    Client[Frontend Client (React/Vite)] --> |HTTPS / WSS| Gateway[API Gateway (FastAPI)]
    
    subgraph Backend [Backend Services]
        Gateway --> Auth[Authentication & Rate Limiting]
        Auth --> Router[Core Router / Orchestrator]
        Router --> MemoryService[Memory & Context Service]
        Router --> SearchService[Web Search Service]
        Router --> ProviderManager[Provider Manager]
    end
    
    subgraph External Providers
        ProviderManager --> OpenAI[OpenAI API]
        ProviderManager --> Anthropic[Anthropic API]
        ProviderManager --> Gemini[Gemini API]
        ProviderManager --> Groq[Groq API]
        ProviderManager --> OpenRouter[OpenRouter API]
    end
    
    subgraph Data Layer
        Auth --> DB[(PostgreSQL)]
        MemoryService --> DB
        Router --> Cache[(Redis)]
        Cache --> |Rate Limits / Session Cache| Gateway
    end
    
    subgraph Observability
        Gateway --> Monitoring[Monitoring / Metrics]
        Router --> Logging[Centralized Logging]
        ProviderManager --> Metrics[Provider Metrics]
    end
```

## Provider Abstraction
To support multiple models, future integrations, and automatic failover, providers are abstracted via standard interfaces. This ensures the core system is agnostic to the specific API signatures of underlying LLM services.

### Interfaces

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any

class BaseProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique name of the provider."""
        pass

    @abstractmethod
    async def generate(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> Dict[str, Any]:
        """Generate a complete response (non-streaming)."""
        pass

    @abstractmethod
    async def generate_stream(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate a response as a stream of chunks."""
        pass

    @abstractmethod
    async def get_models(self) -> List[str]:
        """Retrieve a list of supported models by this provider."""
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """Check provider availability and latency."""
        pass
```

### Architectural Reasoning
The `BaseProvider` interface guarantees that the core orchestrator interacts with all AI APIs using a unified contract. When a provider fails or rate limits the system, the `ProviderManager` seamlessly swaps to another class implementing this exact interface, enabling robust auto-failover and zero downtime.
