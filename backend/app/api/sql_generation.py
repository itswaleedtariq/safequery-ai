import groq
from fastapi import APIRouter, HTTPException, status

from backend.app.core.exceptions import (
    LLMConfigurationError,
    LLMResponseError,
)
from backend.app.schemas.sql_generation import (
    SQLGenerationRequest,
    SQLGenerationResponse,
)
from backend.app.services.sql_generator import generate_sql


router = APIRouter(tags=["SQL Generation"])


@router.post(
    "/sql/generate",
    response_model=SQLGenerationResponse,
    summary="Generate structured PostgreSQL from a question",
)
def generate_structured_sql(
    request: SQLGenerationRequest,
) -> SQLGenerationResponse:
    """
    Generate SQL through Groq without executing it.
    """

    try:
        return generate_sql(request)

    except LLMConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    except groq.AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Groq authentication failed. Check GROQ_API_KEY."
            ),
        ) from error

    except groq.RateLimitError as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Groq rate limit reached. Try again shortly."
            ),
        ) from error

    except groq.APIConnectionError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "SafeQuery AI could not connect to Groq."
            ),
        ) from error

    except groq.APIStatusError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Groq rejected or could not complete the request. "
                f"Provider status: {error.status_code}."
            ),
        ) from error

    except LLMResponseError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error