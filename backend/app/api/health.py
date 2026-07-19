from fastapi import APIRouter, Response, status

from backend.app.core.config import get_settings
from backend.app.db.session import check_database_connection


router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health")
def application_health_check() -> dict[str, str]:
    """Confirm that the FastAPI application is running."""

    return {
        "status": "healthy",
        "project": settings.app_name,
    }


@router.get("/health/database")
def database_health_check(response: Response) -> dict[str, str]:
    """Confirm that FastAPI can connect to PostgreSQL."""

    connected = check_database_connection()

    if not connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return {
            "status": "unhealthy",
            "database": "disconnected",
        }

    return {
        "status": "healthy",
        "database": "connected",
    }