from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError

from backend.app.schemas.database_schema import DatabaseSchemaResponse
from backend.app.services.schema_introspection import (
    clear_schema_cache,
    introspect_database_schema,
)


router = APIRouter(tags=["Schema"])


@router.get(
    "/schema",
    response_model=DatabaseSchemaResponse,
    summary="Inspect the connected PostgreSQL database",
)
def get_database_schema(
    refresh: bool = Query(
        default=False,
        description="Clear the cache and inspect PostgreSQL again.",
    ),
) -> DatabaseSchemaResponse:
    """Return database tables, columns, keys and relationships."""

    try:
        if refresh:
            clear_schema_cache()

        return introspect_database_schema()

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The database schema could not be inspected.",
        ) from error