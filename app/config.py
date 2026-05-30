from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, sourced from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Local DB by default; swap to a Postgres URL to use a managed provider.
    database_url: str = "sqlite:///./blog.db"

    # Auth — change JWT_SECRET in production.
    jwt_secret: str = "dev-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 30  # 30 days

    # Frontend origins allowed to call this API (browser-side requests).
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Re-seed demo data on startup if the DB is empty.
    seed_on_startup: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
