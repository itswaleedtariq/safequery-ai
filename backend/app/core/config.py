from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "SafeQuery AI"
    app_env: str = "development"
    debug: bool = True

    database_url: str
    database_schema: str = "public"

    schema_sample_limit: int = 5
    schema_categorical_max_distinct: int = 25

    max_result_rows: int = 1000
    query_timeout_seconds: int = 10
    min_confidence_score: float = 0.65

    groq_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return one cached Settings object.

    Caching prevents the application from reading the environment
    file repeatedly on every request.
    """
    return Settings()