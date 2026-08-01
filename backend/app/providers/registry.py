from typing import Dict, List
from .base import Provider
from .config import ProviderConfig

class ProviderRegistry:
    def __init__(self, config: ProviderConfig):
        self._providers: Dict[str, Provider] = {}
        self._priority: List[str] = config.provider_priority

    def register(self, name: str, provider: Provider):
        self._providers[name] = provider

    def get_provider(self, name: str) -> Provider:
        return self._providers.get(name)

    def get_priority_list(self) -> List[Provider]:
        providers = []
        for p_name in self._priority:
            if p_name in self._providers:
                providers.append(self._providers[p_name])
        return providers
