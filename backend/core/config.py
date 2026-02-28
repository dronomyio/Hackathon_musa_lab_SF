"""Configuration for the Treasury Bond Agent."""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # FRED
    fred_api_key: str = ""
    fred_base_url: str = "https://api.stlouisfed.org/fred"
    lookback_years: int = 2
    cache_ttl_seconds: int = 900  # 15 min cache
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Anthropic (optional — enables AI narrative synthesis)
    anthropic_api_key: Optional[str] = None
    claude_model: str = "claude-opus-4-6"

    # Agent config
    rolling_window: int = 30  # days for rolling calculations
    correlation_window: int = 30
    agent_loop_interval: int = 900  # seconds between agent runs (15 min)

    model_config = {
        "env_prefix": "",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
