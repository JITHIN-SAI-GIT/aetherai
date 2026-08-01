from typing import Protocol, List, runtime_checkable
from .models import SearchResult


@runtime_checkable
class SearchProvider(Protocol):
    """
    Abstract contract every search provider must satisfy.
    No vendor lock-in — swap providers without changing the engine.
    """

    def name(self) -> str:
        """Return the unique identifier of this provider."""
        ...

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Execute a search and return normalized results."""
        ...

    async def health_check(self) -> bool:
        """Return True if the provider is reachable and functional."""
        ...
