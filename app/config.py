"""Application settings, loaded from environment variables / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    env: str = "development"
    database_url: str = "sqlite:///./controle_financeiro.db"
    secret_key: str = "dev-only-secret-key-change-me-before-deploying-anywhere"
    session_max_age_days: int = 7

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
