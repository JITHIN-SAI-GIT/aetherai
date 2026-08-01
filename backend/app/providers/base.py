from typing import Protocol, List, Dict, Any, AsyncGenerator
from .models import ProviderResponse

class Provider(Protocol):
    def name(self) -> str:
        ...
        
    async def generate(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> ProviderResponse:
        ...
        
    async def stream(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        ...
        
    async def health_check(self) -> bool:
        ...
        
    def supports_streaming(self) -> bool:
        ...
        
    def model_list(self) -> List[str]:
        ...
        
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        ...
