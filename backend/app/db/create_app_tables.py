from backend.app.db.app_session import (
    get_app_engine,
)
from backend.app.db.base import Base

# Import models so SQLAlchemy registers them.
from backend.app.models.user import User  # noqa: F401


def create_app_tables() -> None:
    """Create SafeQuery application tables."""

    Base.metadata.create_all(
        bind=get_app_engine()
    )


if __name__ == "__main__":
    create_app_tables()
    print(
        "SafeQuery application tables created."
    )