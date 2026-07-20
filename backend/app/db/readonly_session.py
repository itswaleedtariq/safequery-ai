from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from backend.app.core.config import get_settings
from backend.app.core.exceptions import (
    QueryExecutionConfigurationError,
)


settings = get_settings()


@lru_cache(maxsize=1)
def get_readonly_engine() -> Engine:
    """
    Create the SQLAlchemy engine used for generated-query execution.

    This engine must use the dedicated SELECT-only PostgreSQL role.
    """

    database_url = (
        settings.readonly_database_url.strip()
    )

    if not database_url:
        raise QueryExecutionConfigurationError(
            "READONLY_DATABASE_URL is missing."
        )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=5,
        max_overflow=5,
    )