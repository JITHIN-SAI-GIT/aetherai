import asyncio
from typing import Callable, Any
from .exceptions import ProviderAuthError, ProviderRateLimitError, ProviderTimeoutError

class RetryPolicy:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        attempt = 0
        while attempt <= self.max_retries:
            try:
                return await func(*args, **kwargs)
            except ProviderAuthError:
                raise
            except Exception as e:
                attempt += 1
                if attempt > self.max_retries:
                    raise
                await asyncio.sleep(self.base_delay * (2 ** (attempt - 1)))
