from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/outreach"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    FRONTEND_URL: str = ""

    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    def model_post_init(self, __context):
        if self.DATABASE_URL and "+asyncpg" not in self.DATABASE_URL:
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL
        if not self.GOOGLE_REDIRECT_URI and self.FRONTEND_URL:
            self.GOOGLE_REDIRECT_URI = f"{self.FRONTEND_URL}/api/v1/gmail/callback"
        if not self.FRONTEND_URL:
            self.FRONTEND_URL = "http://localhost:3000"


settings = Settings()
