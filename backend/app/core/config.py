from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Application
    app_name: str = "SafeQuery AI"
    app_env: str = "development"
    debug: bool = True

    # PostgreSQL
    database_url: str
    database_schema: str = "public"

    # Schema introspection
    schema_sample_limit: int = 5
    schema_categorical_max_distinct: int = 25

    # Groq
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    groq_temperature: float = 0.0
    groq_max_completion_tokens: int = 1200
    groq_timeout_seconds: float = 30.0
    groq_max_retries: int = 2

    # Query safety
    max_result_rows: int = 1000
    query_timeout_seconds: int = 10
    min_confidence_score: float = 0.65

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""

    return Settings()