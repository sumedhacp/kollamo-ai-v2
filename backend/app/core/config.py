"""Configuration and Settings Module for Kollamo.ai Backend."""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Project metadata
    PROJECT_NAME: str = "Kollamo.ai"
    VERSION: str = "0.4.0"
    API_V1_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_SECRET_KEY: str = "change-this-in-production-to-a-secure-random-key"

    # Server binding
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # CORS configuration
    ALLOWED_CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kollamo_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis and Celery message broker
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # YouTube Data API v3
    YOUTUBE_API_KEY: str = ""

    # Translation service
    TRANSLATION_SERVICE: str = "marianmt"
    TRANSLATION_API_KEY: str = ""

    # Machine Learning & Device
    ML_DEVICE: str = "cpu"
    MURIL_MODEL_PATH: str = "google/muril-base-cased"
    FINETUNED_WEIGHTS_PATH: str = "ml/models/saved_weights/baseline_tfidf.joblib"
    MODEL_NAME: str = "kollamo-muril-5class"
    MODEL_VERSION: str = "v1"
    BATCH_SIZE: int = 32
    MAX_COMMENT_LENGTH: int = 5000

    # Logging
    LOG_LEVEL: str = "INFO"

    @field_validator("ALLOWED_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(origin).strip() for origin in v]
        return ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
