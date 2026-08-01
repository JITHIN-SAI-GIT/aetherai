class SearchError(Exception):
    """Base class for all search errors."""
    pass


class SearchProviderError(SearchError):
    """Raised when a search provider fails to return results."""
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"[{provider}] {message}")


class NoSearchProviderError(SearchError):
    """Raised when no search provider is available in the registry."""
    pass


class SearchCacheError(SearchError):
    """Raised when cache operations fail (non-fatal; system falls back)."""
    pass
