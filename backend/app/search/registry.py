import logging
from typing import Dict, List, Optional
from .provider import SearchProvider
from .exceptions import NoSearchProviderError

logger = logging.getLogger("search.registry")


class SearchProviderRegistry:
    """
    Dynamic provider registry. Providers are registered at startup.
    Selection respects priority order and availability.
    """

    def __init__(self, priority: List[str]):
        self._providers: Dict[str, SearchProvider] = {}
        self._priority: List[str] = priority

    def register(self, provider: SearchProvider) -> None:
        self._providers[provider.name()] = provider
        logger.info("Provider registered", extra={"provider": provider.name()})

    def get(self, name: str) -> Optional[SearchProvider]:
        return self._providers.get(name)

    def get_provider(self) -> SearchProvider:
        """Return the first available provider by priority order."""
        for name in self._priority:
            provider = self._providers.get(name)
            if provider is not None:
                return provider
        raise NoSearchProviderError("No search providers registered.")

    def all_names(self) -> List[str]:
        return list(self._providers.keys())
