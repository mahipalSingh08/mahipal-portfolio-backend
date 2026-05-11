import os
from functools import lru_cache
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _parse_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


class Settings:
    app_name: str = os.getenv("APP_NAME", "Portfolio Backend API")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    environment: str = os.getenv("ENVIRONMENT", "development").lower()
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    mongodb_uri: str | None = os.getenv("MONGODB_URI")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "portfolio")
    auth_user_id: str | None = os.getenv("AUTH_USER_ID")
    auth_password_hash: str | None = os.getenv("AUTH_PASSWORD_HASH")
    auth_session_duration_minutes: int = _parse_int("AUTH_SESSION_DURATION_MINUTES", 60)
    cors_origins: List[str] = _parse_csv(
        os.getenv(
            "CORS_ORIGINS",
            "http://localhost:4200,http://127.0.0.1:4200",
        )
    )
    enable_docs: bool = _parse_bool(
        os.getenv("ENABLE_DOCS", "false" if environment == "production" else "true")
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def validate(self) -> None:
        if not self.is_production:
            return

        missing = [
            name
            for name, value in {
                "MONGODB_URI": self.mongodb_uri,
                "AUTH_USER_ID": self.auth_user_id,
                "AUTH_PASSWORD_HASH": self.auth_password_hash,
                "CORS_ORIGINS": self.cors_origins,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Missing required production settings: " + ", ".join(missing)
            )

        localhost_origins = [
            origin
            for origin in self.cors_origins
            if "localhost" in origin or "127.0.0.1" in origin
        ]
        if localhost_origins:
            raise RuntimeError("Production CORS_ORIGINS must not include localhost origins.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
