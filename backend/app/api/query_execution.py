from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from backend.app.core.exceptions import (
    QueryExecutionConfigurationError,
    QueryExecutionError,
    QueryPlanRejectedError,
    QueryRejectedError,
    QueryTimeoutError,
)
from backend.app.schemas.query_execution import (
    QueryExecutionRequest,
    QueryExecutionResponse,
)
from backend.app.services.query_executor import (
    execute_readonly_query,
)


router = APIRouter(tags=["Query Execution"])


@router.post(
    "/sql/execute",
    response_model=QueryExecutionResponse,
    summary="Execute approved SQL in a read-only sandbox",
)
def execute_sql(
    request: QueryExecutionRequest,
) -> QueryExecutionResponse:
    """
    Validate, inspect and execute SQL using the reader account.
    """

    try:
        return execute_readonly_query(request)

    except QueryRejectedError as error:
        guardrail = error.guardrail

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail={
                "message": str(error),
                "guardrail": guardrail.model_dump(
                    mode="json"
                ),
            },
        ) from error

    except QueryPlanRejectedError as error:
        explain = error.explain

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail={
                "message": str(error),
                "explain": explain.model_dump(
                    mode="json"
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

    except QueryExecutionConfigurationError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=str(error),
        ) from error

    except QueryExecutionError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=str(error),
        ) from error