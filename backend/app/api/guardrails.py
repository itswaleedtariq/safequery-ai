from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from sqlalchemy.exc import SQLAlchemyError

from backend.app.guardrails.sql_validator import (
    validate_sql,
)
from backend.app.schemas.sql_guardrails import (
    SQLValidationRequest,
    SQLValidationResponse,
)


router = APIRouter(tags=["SQL Guardrails"])


@router.post(
    "/sql/validate",
    response_model=SQLValidationResponse,
    summary="Validate generated SQL without executing it",
)
def validate_generated_sql(
    request: SQLValidationRequest,
) -> SQLValidationResponse:
    """
    Apply static safety rules to untrusted SQL.

    This endpoint never executes the submitted query.
    """

    try:
        return validate_sql(request)

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "The database schema could not be "
                "loaded for SQL validation."
            ),
        ) from error