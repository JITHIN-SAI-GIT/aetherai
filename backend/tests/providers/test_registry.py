from app.providers.registry import ProviderRegistry
from app.providers.config import ProviderConfig
from app.providers.implementations.openai_provider import OpenAIProvider

def test_registry_registration():
    config = ProviderConfig(provider_priority=["openai"])
    registry = ProviderRegistry(config)
    
    provider = OpenAIProvider()
    registry.register("openai", provider)
    
    assert registry.get_provider("openai") == provider
    assert registry.get_priority_list() == [provider]
