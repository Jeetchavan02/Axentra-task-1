from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class CommonSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")


class AppSettings(CommonSettings):
    project_name: str = "Subscription Tracker"
    api_version: str = "0.1.0"


class CORSSettings(CommonSettings):
    # Explicit origins, because a wildcard cannot be combined with credentials.
    allowed_origins: list[str] = ["http://localhost:5173"]


class Settings(CommonSettings):
    app: AppSettings = Field(default_factory=AppSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()
