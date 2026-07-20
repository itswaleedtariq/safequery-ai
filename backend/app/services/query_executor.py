import json
from time import perf_counter
from typing import Any, Iterator

from fastapi.encoders import jsonable_encoder
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.engine import Connection

from backend.app.core.config import get_settings
from backend.app.core.exceptions import (
    QueryExecutionError,
    QueryPlanRejectedError,
    QueryRejectedError,
    QueryTimeoutError,
)
from backend.app.core.query_audit_logger import (
    log_query_execution,
)
from backend.app.db.readonly_session import (
    get_readonly_engine,
)
from backend.app.guardrails.sql_validator import (
    validate_sql,
)
from backend.app.schemas.query_execution import (
    ExplainPlanSummary,
    ExplainScanNode,
    QueryExecutionRequest,
    QueryExecutionResponse,
)
from backend.app.schemas.sql_guardrails import (
    SQLValidationRequest,
)


settings = get_settings()


def _set_transaction_safety(
    connection: Connection,
) -> None:
    """Apply PostgreSQL transaction-level safety settings."""

    connection.exec_driver_sql(
        "SET TRANSACTION READ ONLY"
    )

    connection.execute(
        text(
            """
            SELECT set_config(
                'statement_timeout',
                :timeout_value,
                true
            )
            """
        ),
        {
            "timeout_value": (
                f"{settings.query_timeout_seconds}s"
            )
        },
    )

    connection.execute(
        text(
            """
            SELECT set_config(
                'lock_timeout',
                :timeout_value,
                true
            )
            """
        ),
        {
            "timeout_value": (
                f"{settings.lock_timeout_seconds}s"
            )
        },
    )


def _normalize_explain_payload(
    raw_payload: Any,
) -> dict[str, Any]:
    """Normalize PostgreSQL JSON EXPLAIN output."""

    payload = raw_payload

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)

        except json.JSONDecodeError as error:
            raise QueryExecutionError(
                "PostgreSQL returned invalid EXPLAIN JSON."
            ) from error

    if isinstance(payload, list):
        if not payload:
            raise QueryExecutionError(
                "PostgreSQL returned an empty EXPLAIN plan."
            )

        payload = payload[0]

    if not isinstance(payload, dict):
        raise QueryExecutionError(
            "PostgreSQL returned an unexpected EXPLAIN format."
        )

    if "Plan" not in payload:
        raise QueryExecutionError(
            "The EXPLAIN result does not contain a plan."
        )

    return payload


def _walk_plan_nodes(
    plan: dict[str, Any],
) -> Iterator[dict[str, Any]]:
    """Yield every node in a PostgreSQL plan tree."""

    yield plan

    for child in plan.get("Plans", []):
        if isinstance(child, dict):
            yield from _walk_plan_nodes(child)


def _summarize_explain_plan(
    raw_payload: Any,
) -> ExplainPlanSummary:
    """Extract cost and scan estimates from EXPLAIN JSON."""

    explain_document = (
        _normalize_explain_payload(
            raw_payload
        )
    )

    root_plan = explain_document["Plan"]

    scan_nodes: list[ExplainScanNode] = []
    estimated_rows_scanned = 0

    for node in _walk_plan_nodes(root_plan):
        node_type = str(
            node.get("Node Type", "")
        )

        if "Scan" not in node_type:
            continue

        plan_rows = int(
            node.get("Plan Rows", 0)
            or 0
        )

        estimated_rows_scanned += plan_rows

        scan_nodes.append(
            ExplainScanNode(
                node_type=node_type,
                relation_name=node.get(
                    "Relation Name"
                ),
                plan_rows=plan_rows,
                total_cost=float(
                    node.get("Total Cost", 0.0)
                    or 0.0
                ),
            )
        )

    return ExplainPlanSummary(
        total_cost=float(
            root_plan.get("Total Cost", 0.0)
            or 0.0
        ),
        root_plan_rows=int(
            root_plan.get("Plan Rows", 0)
            or 0
        ),
        estimated_rows_scanned=(
            estimated_rows_scanned
        ),
        scan_nodes=scan_nodes,
        raw_plan=explain_document,
    )


def _get_explain_plan(
    connection: Connection,
    safe_sql: str,
) -> ExplainPlanSummary:
    """Ask PostgreSQL to plan the query without executing it."""

    query_without_semicolon = (
        safe_sql.strip().rstrip(";")
    )

    explain_sql = (
        "EXPLAIN (FORMAT JSON) "
        + query_without_semicolon
    )

    raw_payload = connection.exec_driver_sql(
        explain_sql
    ).scalar_one()

    return _summarize_explain_plan(
        raw_payload
    )


def _validate_explain_limits(
    explain: ExplainPlanSummary,
) -> None:
    """Reject plans exceeding configured safety limits."""

    rejection_reasons: list[str] = []

    if (
        explain.estimated_rows_scanned
        > settings.max_estimated_rows_scanned
    ):
        rejection_reasons.append(
            (
                "Estimated scanned rows "
                f"{explain.estimated_rows_scanned} "
                "exceed the configured maximum of "
                f"{settings.max_estimated_rows_scanned}."
            )
        )

    if (
        explain.total_cost
        > settings.max_explain_total_cost
    ):
        rejection_reasons.append(
            (
                f"Estimated total cost "
                f"{explain.total_cost} exceeds the "
                "configured maximum of "
                f"{settings.max_explain_total_cost}."
            )
        )

    if rejection_reasons:
        raise QueryPlanRejectedError(
            " ".join(rejection_reasons),
            explain=explain,
        )


def _is_query_cancelled(
    error: DBAPIError,
) -> bool:
    """Detect PostgreSQL query-cancellation SQLSTATE."""

    original_error = getattr(
        error,
        "orig",
        None,
    )

    sqlstate = getattr(
        original_error,
        "sqlstate",
        None,
    )

    return sqlstate == "57014"


def execute_readonly_query(
    request: QueryExecutionRequest,
) -> QueryExecutionResponse:
    """
    Validate, plan and execute SQL in a read-only transaction.

    The transaction is rolled back after every execution.
    """

    guardrail = validate_sql(
        SQLValidationRequest(
            sql=request.sql
        )
    )

    if not guardrail.allowed or not guardrail.safe_sql:
        log_query_execution(
            sql=request.sql,
            status="rejected_by_guardrail",
            metadata={
                "issue_codes": [
                    issue.code
                    for issue in guardrail.issues
                ]
            },
        )

        raise QueryRejectedError(
            "The submitted SQL was rejected by guardrails.",
            guardrail=guardrail,
        )

    safe_sql = guardrail.safe_sql

    engine = get_readonly_engine()

    try:
        with engine.connect() as connection:
            transaction = connection.begin()

            try:
                _set_transaction_safety(
                    connection
                )

                explain = _get_explain_plan(
                    connection=connection,
                    safe_sql=safe_sql,
                )

                try:
                    _validate_explain_limits(
                        explain
                    )

                except QueryPlanRejectedError:
                    log_query_execution(
                        sql=safe_sql,
                        status="rejected_by_explain",
                        estimated_rows_scanned=(
                            explain.estimated_rows_scanned
                        ),
                        total_cost=explain.total_cost,
                    )

                    raise

                execution_started = perf_counter()

                result = connection.exec_driver_sql(
                    safe_sql.strip().rstrip(";")
                )

                columns = list(
                    result.keys()
                )

                raw_rows = [
                    dict(row)
                    for row in result.mappings().all()
                ]

                execution_time_ms = round(
                    (
                        perf_counter()
                        - execution_started
                    )
                    * 1000,
                    2,
                )

                rows = jsonable_encoder(
                    raw_rows
                )

                effective_limit = (
                    guardrail.effective_limit
                    or settings.max_result_rows
                )

                row_limit_reached = (
                    len(rows) >= effective_limit
                )

                response = QueryExecutionResponse(
                    original_sql=request.sql,
                    safe_sql=safe_sql,
                    columns=columns,
                    rows=rows,
                    row_count=len(rows),
                    row_limit_reached=(
                        row_limit_reached
                    ),
                    execution_time_ms=(
                        execution_time_ms
                    ),
                    rolled_back=True,
                    guardrail=guardrail,
                    explain=explain,
                )

                log_query_execution(
                    sql=safe_sql,
                    status="executed",
                    rows_returned=response.row_count,
                    execution_time_ms=(
                        response.execution_time_ms
                    ),
                    estimated_rows_scanned=(
                        explain.estimated_rows_scanned
                    ),
                    total_cost=explain.total_cost,
                    metadata={
                        "columns": columns,
                        "row_limit_reached": (
                            row_limit_reached
                        ),
                    },
                )

            finally:
                if transaction.is_active:
                    transaction.rollback()

        return response

    except (
        QueryRejectedError,
        QueryPlanRejectedError,
    ):
        raise

    except DBAPIError as error:
        if _is_query_cancelled(error):
            log_query_execution(
                sql=safe_sql,
                status="timed_out",
            )

            raise QueryTimeoutError(
                (
                    "PostgreSQL cancelled the query because "
                    "it exceeded the configured timeout."
                )
            ) from error

        log_query_execution(
            sql=safe_sql,
            status="database_error",
            metadata={
                "error_type": (
                    type(error).__name__
                )
            },
        )

        raise QueryExecutionError(
            "PostgreSQL could not execute the approved query."
        ) from error

    except SQLAlchemyError as error:
        log_query_execution(
            sql=safe_sql,
            status="connection_error",
            metadata={
                "error_type": (
                    type(error).__name__
                )
            },
        )

        raise QueryExecutionError(
            "The read-only database connection failed."
        ) from error