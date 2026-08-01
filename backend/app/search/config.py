from pydantic_settings import BaseSettings
from typing import List


class SearchSettings(BaseSettings):
    # Provider priority list (first healthy provider is selected)
    search_providers_enabled: List[str] = ["duckduckgo", "brave", "tavily", "serpapi"]
    search_provider_priority: List[str] = ["duckduckgo", "brave", "tavily", "serpapi"]

    # TTL strategy (seconds) — configurable per category
    ttl_news: int = 900          # 15 minutes
    ttl_weather: int = 600       # 10 minutes
    ttl_sports: int = 30         # 30 seconds
    ttl_general: int = 86400     # 24 hours

    # Redis connection (falls back to in-process dict if unavailable)
    redis_url: str = "redis://localhost:6379/1"

    # Search result limits
    max_results: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
