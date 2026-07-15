import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LocalHub API"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = Field(
        default_factory=lambda: "*" if os.getenv("PORT") or os.getenv("RENDER") else "http://localhost:3000,http://127.0.0.1:3000"
    )

    database_url: str = Field(
        default_factory=lambda: "sqlite+aiosqlite:////tmp/localhub.db"
        if os.getenv("PORT") or os.getenv("RENDER")
        else "sqlite+aiosqlite:///./localhub.db"
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    openai_max_tokens: int = Field(default=500, ge=1, le=2000)
    openai_timeout_seconds: int = Field(default=15, ge=1, le=120)

    chat_max_query_length: int = Field(default=500, ge=20, le=5000)
    chat_max_references: int = Field(default=10, ge=1, le=30)

    rating_cooldown_hours: int = Field(default=24, ge=1, le=168)

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def cors_allow_credentials(self) -> bool:
        return "*" not in self.cors_origins_list


settings = Settings()
