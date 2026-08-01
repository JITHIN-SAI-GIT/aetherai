from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    env:      str = "development"
    port:     int = 8000
    log_level: str = "INFO"
    version:  str = "1.0.0"

    mongodb_uri:   str = "mongodb://localhost:27017"
    database_name: str = "aether"
    frontend_origin: str = "*"

    # Provider API Keys
    openai_api_key:     str | None = None
    anthropic_api_key:  str | None = None
    gemini_api_key:     str | None = None
    groq_api_key:       str | None = None
    groq_api_key_2:     str | None = None   # Second Groq key for Groq-2 slot
    openrouter_api_key: str | None = None

    # Search provider keys
    tavily_api_key:     str | None = None
    brave_api_key:      str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache()
def get_settings():
    return Settings()
