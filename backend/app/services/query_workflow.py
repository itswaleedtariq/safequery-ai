from time import perf_counter
from uuid import uuid4

from backend.app.core.exceptions import (
    LLMResponseError,
)
from backend.app.core.workflow_audit_logger import (
    log_query_workflow,
)
from backend.app.schemas.confidence import (
    ConfidenceCheckRequest,
)
from backend.app.schemas.query_workflow import (
    QueryWorkflowRequest,
    QueryWorkflowResponse,
    WorkflowTimings,
    WorkflowWarning,
)
from backend.app.schemas.sql_generation import (
    SQLGenerationRequest,
)
from backend.app.services.confidence_scorer import (
    check_confidence,
)
from backend.app.services.sql_generator import (
    generate_sql,
)


def _add_warning(
    warnings: list[WorkflowWarning],
    *,
    code: str,
    severity: str,
    message: str,
) -> None:
    """Add one warning while avoiding duplicates."""

    duplicate_exists = any(
        warning.code == code
        and warning.message == message
        for warning in warnings
    )

    if duplicate_exists:
        return

    warnings.append(
        WorkflowWarning(
            code=code,
            severity=severity,
            message=message,
        )
    )


def _collect_guardrail_warnings(
    guardrail: object | None,
    warnings: list[WorkflowWarning],
) -> None:
    """Copy guardrail issues into the final response."""

    if guardrail is None:
        return

    for issue in getattr(
        guardrail,
        "issues",
        [],
    ):
        _add_warning(
            warnings,
            code=issue.code,
            severity=issue.severity,
            message=issue.message,
        )


def _collect_confidence_warnings(
    confidence: object,
    warnings: list[WorkflowWarning],
) -> None:
    """Copy hallucination and confidence warnings."""

    hallucination = confidence.hallucination

    for issue in hallucination.issues:
        _add_warning(
            warnings,
            code=issue.code,
            severity=issue.severity,
            message=issue.message,
        )

    for reason in confidence.reasons:
        _add_warning(
            warnings,
            code="confidence_reason",
            severity="warning",
            message=reason,
        )

    agreement = confidence.multi_query_agreement

    if agreement.status == "mismatched":
        _add_warning(
            warnings,
            code="multi_query_mismatch",
            severity="error",
            message=agreement.explanation,
        )

    elif agreement.status == "failed":
        _add_warning(
            warnings,
            code="multi_query_failed",
            severity="warning",
            message=agreement.explanation,
        )

    if confidence.manual_review_recommended:
        _add_warning(
            warnings,
            code="manual_review_recommended",
            severity="warning",
            message=(
                "The result should be reviewed before "
                "being used for an important decision."
            ),
        )


def _create_timings(
    *,
    generation_ms: float,
    confidence_pipeline_ms: float,
    total_started_at: float,
) -> WorkflowTimings:
    """Create rounded workflow timing information."""

    total_ms = round(
        (
            perf_counter()
            - total_started_at
        )
        * 1000,
        2,
    )

    return WorkflowTimings(
        generation_ms=round(
            generation_ms,
            2,
        ),
        confidence_pipeline_ms=round(
            confidence_pipeline_ms,
            2,
        ),
        total_ms=total_ms,
    )


def _write_workflow_log(
    response: QueryWorkflowResponse,
) -> None:
    """Write a final audit entry for the workflow."""

    log_query_workflow(
        request_id=response.request_id,
        question=response.question,
        status=response.status,
        confidence_score=(
            response.confidence_score
        ),
        row_count=response.row_count,
        total_latency_ms=(
            response.timings.total_ms
        ),
        warning_codes=[
            warning.code
            for warning in response.warnings
        ],
        metadata={
            "model": response.model,
            "provider": response.provider,
            "hallucination_risk": (
                response.hallucination_risk
            ),
            "multi_query_status": (
                response.multi_query_status
            ),
            "result_hidden": (
                response.result_hidden
            ),
        },
    )


def run_query_workflow(
    request: QueryWorkflowRequest,
) -> QueryWorkflowResponse:
    """
    Run the complete natural-language-to-results workflow.

    Low-confidence results are intentionally hidden from the
    user-facing rows field.
    """

    request_id = str(uuid4())
    total_started_at = perf_counter()

    generation_started_at = perf_counter()

    generation = generate_sql(
        SQLGenerationRequest(
            question=request.question,
            max_tables=request.max_tables,
            max_examples=request.max_examples,
        )
    )

    generation_ms = (
        perf_counter()
        - generation_started_at
    ) * 1000

    warnings: list[WorkflowWarning] = []

    if generation.requires_clarification:
        _add_warning(
            warnings,
            code="clarification_required",
            severity="info",
            message=(
                generation.clarification_question
                or (
                    "The question requires additional "
                    "information."
                )
            ),
        )

        timings = _create_timings(
            generation_ms=generation_ms,
            confidence_pipeline_ms=0.0,
            total_started_at=total_started_at,
        )

        response = QueryWorkflowResponse(
            request_id=request_id,
            status="clarification_required",
            question=request.question,
            summary=(
                "SafeQuery AI needs clarification before "
                "it can generate SQL safely."
            ),
            generated_sql=None,
            safe_sql=None,
            explanation=generation.explanation,
            tables_used=generation.tables_used,
            columns_used=generation.columns_used,
            result_columns=[],
            rows=[],
            row_count=0,
            result_hidden=False,
            guardrail_allowed=None,
            confidence_score=None,
            confidence_percent=None,
            confidence_label=None,
            manual_review_recommended=False,
            hallucination_detected=None,
            hallucination_risk=None,
            multi_query_status=None,
            clarification_question=(
                generation.clarification_question
            ),
            warnings=warnings,
            provider=generation.provider,
            model=generation.model,
            timings=timings,
        )

        _write_workflow_log(response)

        return response

    if not generation.sql:
        raise LLMResponseError(
            "SQL generation completed without SQL or clarification."
        )

    if generation.guardrail is None:
        raise LLMResponseError(
            "Generated SQL was not passed through guardrails."
        )

    _collect_guardrail_warnings(
        generation.guardrail,
        warnings,
    )

    if (
        not generation.guardrail.allowed
        or not generation.guardrail.safe_sql
    ):
        timings = _create_timings(
            generation_ms=generation_ms,
            confidence_pipeline_ms=0.0,
            total_started_at=total_started_at,
        )

        response = QueryWorkflowResponse(
            request_id=request_id,
            status="blocked",
            question=request.question,
            summary=(
                "The generated SQL was blocked by the "
                "safety guardrails."
            ),
            generated_sql=generation.sql,
            safe_sql=None,
            explanation=generation.explanation,
            tables_used=generation.tables_used,
            columns_used=generation.columns_used,
            result_columns=[],
            rows=[],
            row_count=0,
            result_hidden=True,
            guardrail_allowed=False,
            confidence_score=None,
            confidence_percent=None,
            confidence_label=None,
            manual_review_recommended=True,
            hallucination_detected=None,
            hallucination_risk=None,
            multi_query_status=None,
            clarification_question=None,
            warnings=warnings,
            provider=generation.provider,
            model=generation.model,
            timings=timings,
        )

        _write_workflow_log(response)

        return response

    confidence_started_at = perf_counter()

    confidence = check_confidence(
        ConfidenceCheckRequest(
            question=request.question,
            sql=generation.sql,
            max_tables=request.max_tables,
            max_examples=request.max_examples,
            run_multi_query=request.run_multi_query,
        )
    )

    confidence_pipeline_ms = (
        perf_counter()
        - confidence_started_at
    ) * 1000

    execution = (
        confidence
        .hallucination
        .execution
    )

    _collect_guardrail_warnings(
        execution.guardrail,
        warnings,
    )

    _collect_confidence_warnings(
        confidence,
        warnings,
    )

    should_show_result = (
        confidence.should_show_result
    )

    status = (
        "completed"
        if should_show_result
        else "review_required"
    )

    if should_show_result:
        summary = (
            "Query completed successfully and returned "
            f"{execution.row_count} row(s)."
        )

        visible_rows = execution.rows
        visible_columns = execution.columns

    else:
        summary = (
            "The query completed, but its results were hidden "
            "because the confidence and validation checks did "
            "not meet the acceptance requirements."
        )

        visible_rows = []
        visible_columns = []

    timings = _create_timings(
        generation_ms=generation_ms,
        confidence_pipeline_ms=(
            confidence_pipeline_ms
        ),
        total_started_at=total_started_at,
    )

    response = QueryWorkflowResponse(
        request_id=request_id,
        status=status,
        question=request.question,
        summary=summary,
        generated_sql=generation.sql,
        safe_sql=execution.safe_sql,
        explanation=generation.explanation,
        tables_used=generation.tables_used,
        columns_used=generation.columns_used,
        result_columns=visible_columns,
        rows=visible_rows,
        row_count=execution.row_count,
        result_hidden=not should_show_result,
        guardrail_allowed=(
            execution.guardrail.allowed
        ),
        confidence_score=(
            confidence.confidence_score
        ),
        confidence_percent=(
            confidence.confidence_percent
        ),
        confidence_label=(
            confidence.confidence_label
        ),
        manual_review_recommended=(
            confidence
            .manual_review_recommended
        ),
        confidence_signals=confidence.signals,
        confidence_reasons=confidence.reasons,
        hallucination_detected=(
            confidence
            .hallucination
            .hallucination_detected
        ),
        hallucination_risk=(
            confidence
            .hallucination
            .risk_level
        ),
        multi_query_status=(
            confidence
            .multi_query_agreement
            .status
        ),
        clarification_question=None,
        warnings=warnings,
        provider=generation.provider,
        model=generation.model,
        timings=timings,
    )

    _write_workflow_log(response)

    return response