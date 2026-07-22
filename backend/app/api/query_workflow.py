import groq
from fastapi import APIRouter, HTTPException, status

from backend.app.api.dependencies import CurrentUser
from backend.app.core.exceptions import (
    LLMConfigurationError,
    LLMResponseError,
    QueryExecutionConfigurationError,
    QueryExecutionError,
    QueryPlanRejectedError,
    QueryRejectedError,
    QueryTimeoutError,
)
from backend.app.schemas.query_workflow import (
    QueryWorkflowRequest,
    QueryWorkflowResponse,
)
from backend.app.services.query_workflow import (
    run_query_workflow,
)


router = APIRouter(
    tags=["Complete Query Workflow"],
)


@router.post(
    "/query",
    response_model=QueryWorkflowResponse,
    summary="Run the complete natural-language-to-SQL workflow",
)
def process_natural_language_query(
    request: QueryWorkflowRequest,
    _current_user: CurrentUser,
) -> QueryWorkflowResponse:
    """
    Generate SQL, validate it, execute it, detect hallucinations,
    calculate confidence, and return the final result.

    A valid bearer token is required before the workflow executes.
    """

    try:
        return run_query_workflow(request)

    except QueryRejectedError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": str(error),
                "guardrail": error.guardrail.model_dump(
                    mode="json",
                ),
            },
        ) from error

    except QueryPlanRejectedError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": str(error),
                "explain": error.explain.model_dump(
                    mode="json",
                ),
            },
        ) from error

    except QueryTimeoutError as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(error),
        ) from error

    except (
        QueryExecutionConfigurationError,
        LLMConfigurationError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    except groq.AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq authentication failed.",
        ) from error

    except groq.RateLimitError as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Groq rate limit reached.",
        ) from error

    except groq.APIConnectionError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to Groq.",
        ) from error

    except groq.APIStatusError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Groq could not complete the request. "
                f"Status code: {error.status_code}."
            ),
        ) from error

    except (
        LLMResponseError,
        QueryExecutionError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error