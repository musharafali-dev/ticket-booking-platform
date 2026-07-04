"""
Application configuration loaded from environment variables.

Design note: we fail loudly at startup (via pydantic validation) rather than
at first use, so a misconfigured deployment never serves traffic silently
in a broken state.
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # ---- Server ----
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # ---- Database ----
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "ticket_booking"
    DATABASE_ECHO: bool = False

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Used by Alembic, which does not support asyncpg directly."""
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ---- Redis ----
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---- Security ----
    SECRET_KEY: str = "dev-only-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        # Only hard-fail in production; local dev can use a weak default.
        if info.data.get("ENVIRONMENT") == "production" and (
            v == "dev-only-change-me" or len(v) < 32
        ):
            raise ValueError("SECRET_KEY must be a strong 32+ char value in production")
        return v

    # ---- CORS ----
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # ---- Email ----
    EMAIL_BACKEND: str = "console"  # console | sendgrid
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@ticketbooking.pk"

    # ---- Payments ----
    PAYMENT_PROVIDER: str = "mock"  # mock | jazzcash | easypaisa
    JAZZCASH_MERCHANT_ID: str = ""
    JAZZCASH_PASSWORD: str = ""
    JAZZCASH_INTEGRITY_SALT: str = ""
    JAZZCASH_RETURN_URL: str = ""
    EASYPAISA_STORE_ID: str = ""
    EASYPAISA_HASH_KEY: str = ""
    EASYPAISA_RETURN_URL: str = ""

    # ---- Booking rules ----
    BOOKING_EXPIRATION_MINUTES: int = 15


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — env is read once per process."""
    return Settings()


settings = get_settings()
