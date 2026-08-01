import asyncio
import os
import time
from dotenv import load_dotenv

# Load real environment variables before anything else
load_dotenv()

from app.config.settings import get_settings
from app.providers.factory import create_registry
from app.providers.models import ProviderResponse
from app.providers.exceptions import ProviderError
from app.db.mongo import MongoDBManager

async def test_provider(provider_name: str, registry):
    print(f"\n[{provider_name.upper()}] Starting Verification...")
    provider = registry.get_provider(provider_name)
    if not provider:
        print(f"[{provider_name.upper()}] FAILED: Not recognized by Registry")
        return False
    print(f"[{provider_name.upper()}] SUCCESS: Recognized by Registry")

    # 1 & 2. Authentication & Health Check
    try:
        is_healthy = await provider.health_check()
        if is_healthy:
            print(f"[{provider_name.upper()}] SUCCESS: Health Check / Authentication successful")
        else:
            print(f"[{provider_name.upper()}] FAILED: Health check returned False")
            return False
    except Exception as e:
        import traceback
        print(f"[{provider_name.upper()}] FAILED: Health Check error: {type(e).__name__} - {e}")
        traceback.print_exc()
        return False

    # Get a model to test
    models = provider.model_list()
    if not models:
        print(f"[{provider_name.upper()}] FAILED: No models returned")
        return False
    test_model = models[0]
    # 3. Generate (non-streaming)
    print(f"[{provider_name.upper()}] Testing generate() with {test_model}...")
    messages = [{"role": "user", "content": "Say 'hello world' and nothing else."}]
    try:
        response = await provider.generate(messages, test_model, max_tokens=10)
        
        # 5, 6, 8. Usage, Latency, Conforms to schema
        assert isinstance(response, ProviderResponse)
        assert response.content != ""
        assert response.latency_ms > 0
        assert "prompt_tokens" in response.usage
        print(f"[{provider_name.upper()}] SUCCESS: Generate successful: '{response.content}' (Latency: {response.latency_ms}ms, Usage: {response.usage})")
    except Exception as e:
        print(f"[{provider_name.upper()}] FAILED generate(): {e}")
        return False

    # 4. Stream
    print(f"[{provider_name.upper()}] Testing stream()...")
    try:
        chunks = []
        async for chunk in provider.stream(messages, test_model, max_tokens=10):
            chunks.append(chunk)
        stream_content = "".join(chunks)
        if len(chunks) > 0 and stream_content != "":
            print(f"[{provider_name.upper()}] SUCCESS: Stream successful: '{stream_content}' ({len(chunks)} chunks)")
        else:
            print(f"[{provider_name.upper()}] FAILED stream(): No chunks returned")
            return False
    except Exception as e:
        print(f"[{provider_name.upper()}] FAILED stream(): {e}")
        return False

    # 7. estimate_cost
    try:
        cost = provider.estimate_cost(100, 100, test_model)
        assert cost >= 0
        print(f"[{provider_name.upper()}] SUCCESS: Estimate Cost successful: ${cost}")
    except Exception as e:
        print(f"[{provider_name.upper()}] FAILED estimate_cost(): {e}")
        return False

    return True

async def verify_infrastructure():
    from app.providers.config import ProviderConfig
    config = ProviderConfig(providers_enabled=["openai", "anthropic", "gemini", "groq", "openrouter"])
    
    registry = create_registry(config)
    
    # Verify DB Connection for persistence
    await MongoDBManager.connect()

    providers = ["openai", "anthropic", "gemini", "groq", "openrouter"]
    results = {}
    
    for p in providers:
        success = await test_provider(p, registry)
        results[p] = success

    await MongoDBManager.disconnect()
    
    print("\n--- FINAL RESULTS ---")
    for p, s in results.items():
        print(f"{p}: {'PASS' if s else 'FAIL'}")

if __name__ == "__main__":
    asyncio.run(verify_infrastructure())
