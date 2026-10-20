"""Application configuration settings using Pydantic Settings."""

from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "RouteDesk"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", alias="ENV")

    # Database
    database_url: str = Field(
        default="sqlite:///./local_db/app.db",
        description="SQLAlchemy DB URI (SQLite for local dev, PostgreSQL in prod)",
    )

    # Security
    jwt_secret: str = Field(
        default="dev-insecure-secret-key-change-in-production-min32chars",
        description="HMAC secret for JWT cookie sessions",
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 480 # 8 hours
    service_token: str = Field(
        default="dev-service-token-secret-for-github-actions",
        description="Static token for internal and CI/CD cron endpoints",
    )
    demo_mode: bool = Field(
        default=True,
        description="Enables seeded demo users and demo login endpoint",
    )

    # Model & Artifacts
    model_dir: str = Field(
        default="./artifacts/bundle",
        description="Path to active champion model bundle directory",
    )
    champion_pointer: str = Field(
        default="./models/champion.json",
        description="Path to champion metadata pointer",
    )

    # Business Calendar & Logging
    tz_business: str = "Asia/Kolkata"
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton getter for application settings."""
    return Settings()
