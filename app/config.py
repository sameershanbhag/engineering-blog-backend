from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_JWT_DEFAULT = "dev-insecure-secret-change-me"


class Settings(BaseSettings):
    """App configuration, sourced from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "local" | "production". Production asserts a hardened config at startup.
    app_env: str = "local"

    # Local DB by default; swap to a Postgres URL to use a managed provider.
    database_url: str = "sqlite:///./blog.db"

    # Auth — MUST be overridden in production.
    jwt_secret: str = INSECURE_JWT_DEFAULT
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 30  # 30 days

    # Shared secret the trusted frontend sends to /auth/oauth so that endpoint
    # can't be called by arbitrary clients to mint tokens for any email.
    internal_api_secret: str = ""

    # Frontend origins allowed to call this API (browser-side requests).
    # Comma-separated; override via the CORS_ORIGINS env var in production.
    cors_origins: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "https://engineering-blog-lilac.vercel.app"
    )

    # Re-seed demo data on startup if the DB is empty.
    seed_on_startup: bool = True

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS resolved to an empty list")
        return origins

    @model_validator(mode="after")
    def _enforce_production_hardening(self) -> "Settings":
        if not self.is_production:
            return self
        problems: list[str] = []
        if self.jwt_secret == INSECURE_JWT_DEFAULT or len(self.jwt_secret) < 16:
            problems.append("JWT_SECRET must be set to a strong value")
        if not self.internal_api_secret:
            problems.append("INTERNAL_API_SECRET must be set")
        if self.database_url.startswith("sqlite"):
            problems.append("DATABASE_URL must point at a real database (not sqlite)")
        if problems:
            raise ValueError(
                "Insecure production config: " + "; ".join(problems)
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
