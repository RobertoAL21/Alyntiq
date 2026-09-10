from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Alyntiq API"
    app_env: str = "development"
    debug: bool = False
    database_url: str = "postgresql+psycopg://alyntiq:alyntiq@localhost:5432/alyntiq"
    redis_url: str = "redis://localhost:6379/0"
    trading_environment: Literal["paper", "live"] = "paper"
    alpaca_api_key: str | None = None
    alpaca_secret_key: str | None = None
    alpaca_data_url: str = "https://data.alpaca.markets/v2"
    alpaca_data_feed: Literal["iex", "sip"] = "iex"


@lru_cache
def get_settings() -> Settings:
    return Settings()
