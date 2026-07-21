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
    # Query safety
    max_result_rows: int = 1000
    query_timeout_seconds: int = 10
    min_confidence_score: float = 0.65

    # Static SQL guardrails
    max_sql_length: int = 20_000
    max_subquery_depth: int = 3
    block_sql_comments: bool = True

    blocked_sql_functions: str = (
        "pg_sleep,"
        "pg_read_file,"
        "pg_read_binary_file,"
        "pg_ls_dir,"
        "lo_import,"
        "lo_export,"
        "dblink,"
        "dblink_exec"
    )

    guardrail_log_file: str = "logs/guardrails.log"
    # Read-only PostgreSQL execution
    readonly_database_url: str = ""

    max_estimated_rows_scanned: int = 100_000
    max_explain_total_cost: float = 100_000.0
    lock_timeout_seconds: int = 2

    query_audit_log_file: str = "logs/query_execution.log"
    
        # Hallucination detection
    hallucination_alignment_threshold: float = 0.70
    hallucination_schema_coverage_threshold: float = 0.60
    max_result_null_ratio: float = 0.50
    hallucination_max_completion_tokens: int = 1600
    hallucination_log_file: str = "logs/hallucination.log"
    


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""

    return Settings()