import os

base_path = r"c:\Users\jithin sai\OneDrive\Desktop\finalbot\backend"

directories = [
    "app/providers",
    "app/providers/implementations",
    "tests/providers",
]

files = {
    "app/providers/models.py": """from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ProviderResponse(BaseModel):
    provider: str
    model: str
    content: str
    finish_reason: str
    usage: Dict[str, int]
    latency_ms: int
    status: int
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
""",
    "app/providers/exceptions.py": """class ProviderError(Exception):
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
""",
    "app/providers/base.py": """from typing import Protocol, List, Dict, Any
from .models import ProviderResponse

class Provider(Protocol):
    def name(self) -> str:
        ...
        
    async def generate(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> ProviderResponse:
        ...
        
    async def health_check(self) -> bool:
        ...
        
    def supports_streaming(self) -> bool:
        ...
        
    def model_list(self) -> List[str]:
        ...
        
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        ...
""",
    "app/providers/config.py": """from pydantic_settings import BaseSettings
from typing import List, Dict

class ProviderConfig(BaseSettings):
    providers_enabled: List[str] = ["openai", "anthropic", "gemini"]
    provider_priority: List[str] = ["openai", "anthropic", "gemini"]
    provider_timeouts: Dict[str, int] = {"openai": 30, "anthropic": 30, "gemini": 30}
    retry_count: int = 3
    circuit_threshold: int = 5
    circuit_cooldown: int = 60
""",
    "app/providers/metrics.py": """from typing import Dict, Any

class MetricsTracker:
    def __init__(self):
        self._metrics = {
            "requests": 0,
            "success": 0,
            "failures": 0,
            "timeouts": 0,
            "rate_limits": 0,
            "retries": 0,
            "total_latency_ms": 0
        }
    
    def record_success(self, latency_ms: int):
        self._metrics["requests"] += 1
        self._metrics["success"] += 1
        self._metrics["total_latency_ms"] += latency_ms

    def record_failure(self, error_type: str):
        self._metrics["requests"] += 1
        self._metrics["failures"] += 1
        if error_type == "timeout":
            self._metrics["timeouts"] += 1
        elif error_type == "rate_limit":
            self._metrics["rate_limits"] += 1

    def record_retry(self):
        self._metrics["retries"] += 1

    def get_snapshot(self) -> Dict[str, Any]:
        reqs = self._metrics["requests"]
        avg_lat = self._metrics["total_latency_ms"] / reqs if reqs > 0 else 0
        success_pct = (self._metrics["success"] / reqs * 100) if reqs > 0 else 100.0
        
        return {
            **self._metrics,
            "average_latency_ms": avg_lat,
            "success_percentage": success_pct
        }

global_metrics = MetricsTracker()
""",
    "app/providers/health.py": """from enum import Enum
from typing import Dict, Any

class HealthState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"

class HealthTracker:
    def __init__(self):
        self.state = HealthState.HEALTHY
        self.failure_count = 0
        self.last_error = None
        self.recovery_attempts = 0

    def record_failure(self, error: str):
        self.failure_count += 1
        self.last_error = error
        if self.failure_count > 3:
            self.state = HealthState.OFFLINE
        elif self.failure_count > 0:
            self.state = HealthState.DEGRADED

    def record_success(self):
        self.failure_count = 0
        self.last_error = None
        self.state = HealthState.HEALTHY
        self.recovery_attempts = 0
        
    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_error": self.last_error,
            "recovery_attempts": self.recovery_attempts
        }
""",
    "app/providers/circuit_breaker.py": """from enum import Enum
import time
from .exceptions import CircuitBreakerOpenError

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, cooldown_seconds: int = 60):
        self.threshold = failure_threshold
        self.cooldown = cooldown_seconds
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time = 0

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = CircuitState.OPEN
            self.last_failure_time = time.time()

    def record_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.cooldown:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        if self.state == CircuitState.HALF_OPEN:
            return True
        return False

    def execute(self, func, *args, **kwargs):
        if not self.can_execute():
            raise CircuitBreakerOpenError("Circuit is OPEN")
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise
""",
    "app/providers/retry.py": """import asyncio
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
""",
    "app/providers/key_rotation.py": """from typing import List
from .exceptions import ProviderAuthError

class KeyRotator:
    def __init__(self, keys: List[str]):
        if not keys:
            self.keys = []
        else:
            self.keys = keys
        self.current_index = 0
        self.disabled_keys = set()

    def get_key(self) -> str:
        if not self.keys:
            return ""
        
        attempts = 0
        while attempts < len(self.keys):
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
            if key not in self.disabled_keys:
                return key
            attempts += 1
        raise ProviderAuthError("No valid API keys available.")

    def disable_key(self, key: str):
        if key in self.keys:
            self.disabled_keys.add(key)
            
    def reset_key(self, key: str):
        if key in self.disabled_keys:
            self.disabled_keys.remove(key)
""",
    "app/providers/registry.py": """from typing import Dict, List
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
""",
    "app/providers/factory.py": """from .registry import ProviderRegistry
from .config import ProviderConfig
from .implementations.openai_provider import OpenAIProvider
from .implementations.anthropic_provider import AnthropicProvider

def create_registry(config: ProviderConfig) -> ProviderRegistry:
    registry = ProviderRegistry(config)
    if "openai" in config.providers_enabled:
        registry.register("openai", OpenAIProvider())
    if "anthropic" in config.providers_enabled:
        registry.register("anthropic", AnthropicProvider())
    return registry
""",
    "app/providers/manager.py": """from typing import List, Dict, Any
from .registry import ProviderRegistry
from .models import ProviderResponse
from .exceptions import NoAvailableProviderError

class ProviderManager:
    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    async def generate(self, messages: List[Dict[str, Any]], model: str = None) -> ProviderResponse:
        providers = self.registry.get_priority_list()
        if not providers:
            raise NoAvailableProviderError("No providers configured in registry.")
            
        last_error = None
        for provider in providers:
            try:
                return await provider.generate(messages, model)
            except Exception as e:
                last_error = e
                continue
                
        raise NoAvailableProviderError(f"All providers failed. Last error: {last_error}")
""",
    "app/providers/implementations/openai_provider.py": """from typing import List, Dict, Any
from ..base import ProviderResponse

class OpenAIProvider:
    def name(self) -> str: return "openai"
    async def generate(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> ProviderResponse: raise NotImplementedError()
    async def health_check(self) -> bool: raise NotImplementedError()
    def supports_streaming(self) -> bool: raise NotImplementedError()
    def model_list(self) -> List[str]: raise NotImplementedError()
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float: raise NotImplementedError()
""",
    "app/providers/implementations/anthropic_provider.py": """from typing import List, Dict, Any
from ..base import ProviderResponse

class AnthropicProvider:
    def name(self) -> str: return "anthropic"
    async def generate(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> ProviderResponse: raise NotImplementedError()
    async def health_check(self) -> bool: raise NotImplementedError()
    def supports_streaming(self) -> bool: raise NotImplementedError()
    def model_list(self) -> List[str]: raise NotImplementedError()
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float: raise NotImplementedError()
""",
    "app/providers/implementations/gemini_provider.py": """from typing import List, Dict, Any
from ..base import ProviderResponse

class GeminiProvider:
    def name(self) -> str: return "gemini"
    async def generate(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> ProviderResponse: raise NotImplementedError()
    async def health_check(self) -> bool: raise NotImplementedError()
    def supports_streaming(self) -> bool: raise NotImplementedError()
    def model_list(self) -> List[str]: raise NotImplementedError()
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float: raise NotImplementedError()
""",
    "app/providers/implementations/groq_provider.py": """from typing import List, Dict, Any
from ..base import ProviderResponse

class GroqProvider:
    def name(self) -> str: return "groq"
    async def generate(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> ProviderResponse: raise NotImplementedError()
    async def health_check(self) -> bool: raise NotImplementedError()
    def supports_streaming(self) -> bool: raise NotImplementedError()
    def model_list(self) -> List[str]: raise NotImplementedError()
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float: raise NotImplementedError()
""",
    "app/providers/implementations/openrouter_provider.py": """from typing import List, Dict, Any
from ..base import ProviderResponse

class OpenRouterProvider:
    def name(self) -> str: return "openrouter"
    async def generate(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> ProviderResponse: raise NotImplementedError()
    async def health_check(self) -> bool: raise NotImplementedError()
    def supports_streaming(self) -> bool: raise NotImplementedError()
    def model_list(self) -> List[str]: raise NotImplementedError()
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float: raise NotImplementedError()
""",
    "app/api/routes/internal.py": """from fastapi import APIRouter
from app.providers.metrics import global_metrics
from app.providers.health import HealthTracker

router = APIRouter(tags=["internal"])
global_health = HealthTracker()

@router.get("/internal/providers")
async def get_providers():
    return {"status": "ok", "providers": ["openai", "anthropic", "gemini", "groq", "openrouter"]}

@router.get("/internal/providers/health")
async def get_providers_health():
    return {"openai": global_health.get_status()}

@router.get("/internal/providers/metrics")
async def get_providers_metrics():
    return global_metrics.get_snapshot()
""",
    "tests/providers/test_circuit_breaker.py": """import pytest
from app.providers.circuit_breaker import CircuitBreaker, CircuitState
from app.providers.exceptions import CircuitBreakerOpenError
import time

def test_circuit_breaker_closes_and_opens():
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=1)
    assert cb.can_execute() is True
    
    cb.record_failure()
    assert cb.can_execute() is True
    
    cb.record_failure()
    assert cb.can_execute() is False
    assert cb.state == CircuitState.OPEN

def test_circuit_breaker_half_open(monkeypatch):
    cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=1)
    cb.record_failure()
    assert cb.can_execute() is False
    
    original_time = time.time
    monkeypatch.setattr(time, "time", lambda: original_time() + 2)
    
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN
""",
    "tests/providers/test_key_rotation.py": """import pytest
from app.providers.key_rotation import KeyRotator
from app.providers.exceptions import ProviderAuthError

def test_key_rotation():
    rotator = KeyRotator(["key1", "key2"])
    assert rotator.get_key() == "key1"
    assert rotator.get_key() == "key2"
    assert rotator.get_key() == "key1"

def test_key_disable():
    rotator = KeyRotator(["key1", "key2"])
    rotator.disable_key("key1")
    assert rotator.get_key() == "key2"
    assert rotator.get_key() == "key2"
    
    rotator.reset_key("key1")
    assert rotator.get_key() == "key2"
    assert rotator.get_key() == "key1"

def test_all_keys_disabled():
    rotator = KeyRotator(["key1"])
    rotator.disable_key("key1")
    with pytest.raises(ProviderAuthError):
        rotator.get_key()
""",
    "tests/providers/test_registry.py": """from app.providers.registry import ProviderRegistry
from app.providers.config import ProviderConfig
from app.providers.implementations.openai_provider import OpenAIProvider

def test_registry_registration():
    config = ProviderConfig(provider_priority=["openai"])
    registry = ProviderRegistry(config)
    
    provider = OpenAIProvider()
    registry.register("openai", provider)
    
    assert registry.get_provider("openai") == provider
    assert registry.get_priority_list() == [provider]
"""
}

# Create directories
for d in directories:
    dir_path = os.path.join(base_path, d)
    os.makedirs(dir_path, exist_ok=True)
    
# Create __init__.py files
for d in directories:
    parts = d.split('/')
    for i in range(1, len(parts) + 1):
        init_dir = os.path.join(base_path, *parts[:i])
        init_file = os.path.join(init_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, 'a').close()

# Create files
for file_path, content in files.items():
    full_path = os.path.join(base_path, file_path)
    os.makedirs(os.path.dirname(full_path) or base_path, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Phase 2 skeleton generated successfully.")
