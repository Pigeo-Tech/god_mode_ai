"""Centralised, environment-driven configuration.

Phase 2. Uses pydantic-settings when available; falls back to a stdlib implementation so the
core framework runs with zero third-party dependencies during early development.
"""
from __future__ import annotations

import os

try:  # pragma: no cover - exercised when pydantic-settings is installed
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        app_env: str = "development"
        app_name: str = "god_mode_ai"
        log_level: str = "INFO"
        log_json: bool = True

        postgres_host: str = "localhost"
        postgres_port: int = 5432
        postgres_db: str = "god_mode_ai"
        postgres_user: str = "godmode"
        postgres_password: str = "change-me"

        redis_url: str = "redis://localhost:6379/0"
        qdrant_url: str = "http://localhost:6333"

        jwt_secret: str = "change-me"
        jwt_algorithm: str = "HS256"
        access_token_expire_minutes: int = 30

        use_in_memory_backends: bool = True

        model_config = SettingsConfigDict(env_file=".env", extra="ignore")

except ImportError:  # pragma: no cover - fallback path

    def _b(name: str, default: bool) -> bool:
        return os.getenv(name, str(default)).lower() in ("1", "true", "yes")

    class Settings:  # type: ignore[no-redef]
        def __init__(self) -> None:
            self.app_env = os.getenv("APP_ENV", "development")
            self.app_name = os.getenv("APP_NAME", "god_mode_ai")
            self.log_level = os.getenv("LOG_LEVEL", "INFO")
            self.log_json = _b("LOG_JSON", True)
            self.postgres_host = os.getenv("POSTGRES_HOST", "localhost")
            self.postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
            self.postgres_db = os.getenv("POSTGRES_DB", "god_mode_ai")
            self.postgres_user = os.getenv("POSTGRES_USER", "godmode")
            self.postgres_password = os.getenv("POSTGRES_PASSWORD", "change-me")
            self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            self.jwt_secret = os.getenv("JWT_SECRET", "change-me")
            self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
            self.access_token_expire_minutes = int(
                os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
            self.use_in_memory_backends = _b("USE_IN_MEMORY_BACKENDS", True)


settings = Settings()
