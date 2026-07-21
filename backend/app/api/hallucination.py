import groq
from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from backend.app.core.exceptions import (
    LLMConfigurationError,
    LLMResponseError,
    QueryExecutionConfigurationError,
    QueryExecutionError,
    QueryPlanRejectedError,
    QueryRejectedError,
    QueryTimeoutError,
)
from backend.app.schemas.hallucination import (
    HallucinationCheckRequest,
    HallucinationCheckResponse,
)
from backend.app.services.hallucination_detector import (
    check_hallucination,
)


router = APIRouter(
    tags=["Hallucination Detection"]
)


@router.post(
    "/hallucination/check",
    response_model=HallucinationCheckResponse,
    summary=(
        "Check whether SQL answers the original question"
    ),
)
def detect_sql_hallucination(
    request: HallucinationCheckRequest,
) -> HallucinationCheckResponse:
    """Execute and analyze SQL for hallucination signals."""

    try:
        return check_hallucination(request)

    except QueryRejectedError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail={
                "message": str(error),
                "guardrail": (
                    error.guardrail.model_dump(
                        mode="json"
                    )
                ),
            },
        ) from error

    except QueryPlanRejectedError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail={
                "message": str(error),
                "explain": (
                    error.explain.model_dump(
                        mode="json"
                    )
                ),
            },
        ) from error

    except QueryTimeoutError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_504_GATEWAY_TIMEOUT
            ),
            detail=str(error),
        ) from error

    except (
        QueryExecutionConfigurationError,
        LLMConfigurationError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=str(error),
        ) from error

    except groq.AuthenticationError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail="Groq authentication failed.",
        ) from error

    except groq.RateLimitError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_429_TOO_MANY_REQUESTS
            ),
            detail="Groq rate limit reached.",
        ) from error

    except groq.APIConnectionError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Could not connect to Groq."
            ),
        ) from error

    except groq.APIStatusError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=(
                "Groq could not complete the "
                f"request: {error.status_code}."
            ),
        ) from error

    except (
        LLMResponseError,
        QueryExecutionError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=str(error),
        ) from error