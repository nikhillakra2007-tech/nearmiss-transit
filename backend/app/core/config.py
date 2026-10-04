"""Central application settings (env-driven, no secrets in code)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./nearmiss.db"
    GTFS_REALTIME_URL: str = ""
    GTFS_API_KEY: str = ""
    GTFS_STATIC_URL: str = ""
    POLL_INTERVAL_SECONDS: int = 30
    FEED_TIMEOUT_SECONDS: int = 15
    EVENT_RETENTION_DAYS: int = 14
    NEAR_MISS_RETENTION_DAYS: int = 180
    PATTERN_RETENTION_DAYS: int = 365
    NEAR_MISS_THRESHOLD: int = 600
    RECOVERY_THRESHOLD: int = 300
    PATTERN_MIN_OCCURRENCES: int = 3
    CHAIN_WINDOW_MINUTES: int = 120
    CHAIN_MAX_DEPTH: int = 3
    BASELINE_WINDOW_DAYS: int = 30
    DEVIATION_SIGMA: float = 3.0
    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "mock-investigator-1"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DEMO_MODE: bool = False


settings = Settings()
