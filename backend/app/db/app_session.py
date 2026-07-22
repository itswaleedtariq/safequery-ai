from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings


settings = get_settings()


@lru_cache(maxsize=1)
def get_app_engine() -> Engine:
    """Create the read-write engine used by application tables."""

    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=5,
        max_overflow=10,
    )


AppSessionLocal = sessionmaker(
    bind=get_app_engine(),
    autoflush=False,
    expire_on_commit=False,
)


def get_db_session() -> Generator[Session, None, None]:
    """Provide one SQLAlchemy session per request."""

    session = AppSessionLocal()

    try:
        yield session

    finally:
        session.close()