class ProviderError(Exception):
    pass

class ProviderTimeoutError(ProviderError):
    pass

class ProviderRateLimitError(ProviderError):
    pass

class ProviderAuthError(ProviderError):
    pass

class CircuitBreakerOpenError(ProviderError):
    pass

class NoAvailableProviderError(ProviderError):
    pass
