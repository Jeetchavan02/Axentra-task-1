from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class CommonSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")


class AppSettings(CommonSettings):
    project_name: str = "Subscription Tracker"
    api_version: str = "0.1.0"


class CORSSettings(CommonSettings):
    # Explicit origins, because a wildcard cannot be combined with credentials.
    allowed_origins: list[str] = ["http://localhost:5173"]


class DatabaseSettings(CommonSettings):
    # No defaults: the app should refuse to start without an explicit database config.
    db_user: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str

    @property
    def url(self) -> URL:
        # URL.create escapes special characters in the password.
        return URL.create(
            "postgresql+asyncpg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


class SecuritySettings(CommonSettings):
    # No default: a known secret would let anyone forge login tokens.
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60


class Settings(CommonSettings):
    app: AppSettings = Field(default_factory=AppSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()
