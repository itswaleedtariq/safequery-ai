import json
from typing import Any

import groq
import sqlglot
from sqlglot import exp

from backend.app.core.confidence_audit_logger import (
    log_confidence_decision,
)
from backend.app.core.config import get_settings
from backend.app.schemas.confidence import (
    ConfidenceCheckRequest,
    ConfidenceCheckResponse,
    ConfidenceSignal,
    MultiQueryAgreement,
)
from backend.app.schemas.prompt_context import (
    PromptPreviewRequest,
)
from backend.app.schemas.query_execution import (
    QueryExecutionRequest,
    QueryExecutionResponse,
)
from backend.app.services.hallucination_detector import (
    check_hallucination,
)
from backend.app.services.prompt_builder import (
    build_prompt_preview,
)
from backend.app.services.query_executor import (
    execute_readonly_query,
)
from backend.app.services.sql_generator import (
    get_groq_client,
    parse_generation_content,
)
from backend.app.services.structured_output_schema import (
    SQL_GENERATION_JSON_SCHEMA,
)


settings = get_settings()


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """Keep a numeric value within a fixed range."""

    return max(
        minimum,
        min(maximum, value),
    )


def calculate_result_sanity_score(
    *,
    checks_run: int,
    issues: list[Any],
) -> float:
    """
    Convert result-sanity issues into a score.

    Errors count as one failed check, warnings as half a failed check,
    and informational issues as one tenth of a failed check.
    """

    if checks_run <= 0:
        return 1.0

    failed_equivalent = 0.0

    for issue in issues:
        if issue.severity == "error":
            failed_equivalent += 1.0

        elif issue.severity == "warning":
            failed_equivalent += 0.5

        else:
            failed_equivalent += 0.1

    return round(
        _clamp(
            1.0
            - (
                failed_equivalent
                / checks_run
            )
        ),
        4,
    )


def _is_complex_query(sql: str) -> bool:
    """Decide whether independent SQL validation is useful."""

    expression = sqlglot.parse_one(
        sql,
        read="postgres",
    )

    complex_nodes = (
        exp.Join,
        exp.Group,
        exp.Having,
        exp.Subquery,
        exp.Union,
        exp.Intersect,
        exp.Except,
    )

    return any(
        expression.find(node_type) is not None
        for node_type in complex_nodes
    )


def _create_alternate_completion(
    *,
    prompt: str,
) -> object:
    """Generate an independent SQL approach through Groq."""

    client = get_groq_client()

    arguments = {
        "model": settings.groq_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an independent PostgreSQL reviewer. "
                    "Generate a correct SQL approach without "
                    "copying a previous solution. Return every "
                    "required JSON field and no Markdown."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0,
        "max_completion_tokens": (
            settings.groq_max_completion_tokens
        ),
        "reasoning_effort": "low",
        "include_reasoning": False,
    }

    try:
        return client.chat.completions.create(
            **arguments,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": (
                        "safequery_alternate_sql"
                    ),
                    "strict": True,
                    "schema": (
                        SQL_GENERATION_JSON_SCHEMA
                    ),
                },
            },
        )

    except groq.BadRequestError as error:
        error_body = getattr(
            error,
            "body",
            {},
        ) or {}

        provider_error = error_body.get(
            "error",
            error_body,
        )

        if (
            provider_error.get("code")
            != "json_validate_failed"
        ):
            raise

        return client.chat.completions.create(
            **arguments,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": (
                        "safequery_alternate_sql"
                    ),
                    "strict": False,
                    "schema": (
                        SQL_GENERATION_JSON_SCHEMA
                    ),
                },
            },
        )


def _generate_alternate_sql(
    request: ConfidenceCheckRequest,
) -> str:
    """Generate an alternative solution without showing primary SQL."""

    preview = build_prompt_preview(
        PromptPreviewRequest(
            question=request.question,
            max_tables=request.max_tables,
            max_examples=request.max_examples,
        )
    )

    alternate_prompt = f"""
{preview.prompt}

ADDITIONAL INDEPENDENT-VALIDATION INSTRUCTIONS:

Generate an alternative correct PostgreSQL solution for the user
question.

Use a structurally different approach where reasonable. For example,
use a CTE instead of a direct aggregation, or use a different valid
join and aggregation structure.

Do not refer to or assume that another SQL solution exists.
Preserve the requested output meaning, filters, ordering and limit.
""".strip()

    completion = _create_alternate_completion(
        prompt=alternate_prompt
    )

    if not completion.choices:
        raise RuntimeError(
            "Groq returned no alternative SQL choice."
        )

    payload = parse_generation_content(
        completion.choices[0].message.content or ""
    )

    if (
        payload.requires_clarification
        or not payload.sql
    ):
        raise RuntimeError(
            "Alternative generation did not return SQL."
        )

    return payload.sql


def _canonical_rows(
    rows: list[dict[str, Any]],
) -> list[str]:
    """Create stable representations including column names."""

    return sorted(
        json.dumps(
            row,
            sort_keys=True,
            default=str,
            separators=(",", ":"),
        )
        for row in rows
    )


def _canonical_values(
    rows: list[dict[str, Any]],
) -> list[str]:
    """Create stable row representations ignoring aliases."""

    normalized_rows: list[str] = []

    for row in rows:
        values = sorted(
            json.dumps(
                value,
                sort_keys=True,
                default=str,
            )
            for value in row.values()
        )

        normalized_rows.append(
            json.dumps(values)
        )

    return sorted(normalized_rows)


def compare_result_sets(
    *,
    primary_rows: list[dict[str, Any]],
    alternate_rows: list[dict[str, Any]],
) -> tuple[
    bool,
    bool,
    float,
    str,
]:
    """Compare independent query results."""

    exact_match = (
        _canonical_rows(primary_rows)
        == _canonical_rows(alternate_rows)
    )

    if exact_match:
        return (
            True,
            True,
            1.0,
            (
                "Both SQL approaches returned exactly "
                "the same rows and columns."
            ),
        )

    values_match = (
        len(primary_rows)
        == len(alternate_rows)
        and _canonical_values(primary_rows)
        == _canonical_values(alternate_rows)
    )

    if values_match:
        return (
            False,
            True,
            0.90,
            (
                "Both approaches returned matching values, "
                "but column aliases or ordering differed."
            ),
        )

    return (
        False,
        False,
        0.0,
        (
            "The independent SQL approaches returned "
            "different results."
        ),
    )


def run_multi_query_validation(
    *,
    request: ConfidenceCheckRequest,
    primary_execution: QueryExecutionResponse,
    hallucination_detected: bool,
    hallucination_risk: str,
) -> MultiQueryAgreement:
    """Generate and compare a second SQL approach."""

    required = _is_complex_query(
        primary_execution.safe_sql
    )

    if not required:
        return MultiQueryAgreement(
            required=False,
            attempted=False,
            status="not_required",
            score=None,
            primary_sql=(
                primary_execution.safe_sql
            ),
            primary_row_count=(
                primary_execution.row_count
            ),
            explanation=(
                "The query is simple enough that a second "
                "SQL approach is not required."
            ),
        )

    if (
        not request.run_multi_query
        or not settings.multi_query_validation_enabled
    ):
        return MultiQueryAgreement(
            required=True,
            attempted=False,
            status="skipped",
            score=None,
            primary_sql=(
                primary_execution.safe_sql
            ),
            primary_row_count=(
                primary_execution.row_count
            ),
            explanation=(
                "Multi-query validation was disabled."
            ),
        )

    if (
        hallucination_detected
        and hallucination_risk == "high"
    ):
        return MultiQueryAgreement(
            required=True,
            attempted=False,
            status="skipped",
            score=None,
            primary_sql=(
                primary_execution.safe_sql
            ),
            primary_row_count=(
                primary_execution.row_count
            ),
            explanation=(
                "Independent validation was skipped because "
                "the primary SQL already has high "
                "hallucination risk."
            ),
        )

    try:
        alternate_sql = _generate_alternate_sql(
            request
        )

        alternate_execution = (
            execute_readonly_query(
                QueryExecutionRequest(
                    sql=alternate_sql
                )
            )
        )

        (
            exact_match,
            values_match,
            score,
            explanation,
        ) = compare_result_sets(
            primary_rows=(
                primary_execution.rows
            ),
            alternate_rows=(
                alternate_execution.rows
            ),
        )

        return MultiQueryAgreement(
            required=True,
            attempted=True,
            status=(
                "matched"
                if values_match
                else "mismatched"
            ),
            score=score,
            primary_sql=(
                primary_execution.safe_sql
            ),
            alternate_sql=(
                alternate_execution.safe_sql
            ),
            primary_row_count=(
                primary_execution.row_count
            ),
            alternate_row_count=(
                alternate_execution.row_count
            ),
            exact_match=exact_match,
            values_match=values_match,
            explanation=explanation,
            alternate_execution=(
                alternate_execution
            ),
        )

    except Exception as error:
        return MultiQueryAgreement(
            required=True,
            attempted=True,
            status="failed",
            score=None,
            primary_sql=(
                primary_execution.safe_sql
            ),
            primary_row_count=(
                primary_execution.row_count
            ),
            explanation=(
                "The alternative SQL approach could not "
                f"be completed: {type(error).__name__}."
            ),
        )


def calculate_weighted_confidence(
    *,
    syntax_score: float,
    alignment_score: float,
    sanity_score: float,
    schema_coverage_score: float,
    agreement_score: float | None,
    hallucination_risk: str,
    sanity_passed: bool,
    agreement_status: str,
) -> tuple[
    float,
    list[ConfidenceSignal],
    list[str],
]:
    """Calculate an explainable weighted confidence score."""

    raw_signals = [
        {
            "name": "sql_syntax_and_safety",
            "score": syntax_score,
            "weight": (
                settings.confidence_weight_syntax
            ),
            "available": True,
            "explanation": (
                "Whether the SQL passed syntax, schema "
                "and safety guardrails."
            ),
        },
        {
            "name": "question_alignment",
            "score": alignment_score,
            "weight": (
                settings
                .confidence_weight_alignment
            ),
            "available": True,
            "explanation": (
                "How closely the SQL back-translation "
                "matches the original question."
            ),
        },
        {
            "name": "result_sanity",
            "score": sanity_score,
            "weight": (
                settings
                .confidence_weight_result_sanity
            ),
            "available": True,
            "explanation": (
                "Whether deterministic result and query-shape "
                "checks passed."
            ),
        },
        {
            "name": "multi_query_agreement",
            "score": agreement_score,
            "weight": (
                settings
                .confidence_weight_multi_query
            ),
            "available": (
                agreement_score is not None
            ),
            "explanation": (
                "Whether an independent SQL approach "
                "returned equivalent results."
            ),
        },
        {
            "name": "schema_coverage",
            "score": schema_coverage_score,
            "weight": (
                settings
                .confidence_weight_schema_coverage
            ),
            "available": True,
            "explanation": (
                "Whether the SQL used the expected tables "
                "and business columns."
            ),
        },
    ]

    available_weight = sum(
        signal["weight"]
        for signal in raw_signals
        if signal["available"]
    )

    signals: list[ConfidenceSignal] = []

    for signal in raw_signals:
        effective_weight = 0.0

        if (
            signal["available"]
            and available_weight > 0
        ):
            effective_weight = (
                signal["weight"]
                / available_weight
            )

        score = signal["score"]

        weighted_score = (
            float(score) * effective_weight
            if score is not None
            else 0.0
        )

        signals.append(
            ConfidenceSignal(
                name=signal["name"],
                score=score,
                configured_weight=round(
                    signal["weight"],
                    4,
                ),
                effective_weight=round(
                    effective_weight,
                    4,
                ),
                weighted_score=round(
                    weighted_score,
                    4,
                ),
                available=signal["available"],
                explanation=(
                    signal["explanation"]
                ),
            )
        )

    final_score = sum(
        signal.weighted_score
        for signal in signals
    )

    reasons: list[str] = []

    if hallucination_risk == "high":
        final_score = min(
            final_score,
            0.49,
        )

        reasons.append(
            "Confidence was capped because hallucination "
            "risk is high."
        )

    elif hallucination_risk == "medium":
        final_score = min(
            final_score,
            0.69,
        )

        reasons.append(
            "Confidence was capped because hallucination "
            "risk is medium."
        )

    if not sanity_passed:
        final_score = min(
            final_score,
            0.59,
        )

        reasons.append(
            "Confidence was capped because result sanity "
            "checks contain an error."
        )

    if agreement_status == "mismatched":
        final_score = min(
            final_score,
            0.59,
        )

        reasons.append(
            "Confidence was capped because independent "
            "SQL approaches produced different results."
        )

    return (
        round(
            _clamp(final_score),
            4,
        ),
        signals,
        reasons,
    )


def _confidence_label(
    score: float,
) -> str:
    """Convert the numeric score into a label."""

    if (
        score
        >= settings.confidence_high_threshold
    ):
        return "high"

    if (
        score
        >= settings.confidence_medium_threshold
    ):
        return "medium"

    return "low"


def check_confidence(
    request: ConfidenceCheckRequest,
) -> ConfidenceCheckResponse:
    """Run hallucination analysis and calculate confidence."""

    hallucination = check_hallucination(
        request
    )

    execution = hallucination.execution

    agreement = run_multi_query_validation(
        request=request,
        primary_execution=execution,
        hallucination_detected=(
            hallucination.hallucination_detected
        ),
        hallucination_risk=(
            hallucination.risk_level
        ),
    )

    syntax_score = (
        1.0
        if execution.guardrail.allowed
        else 0.0
    )

    sanity_score = (
        calculate_result_sanity_score(
            checks_run=(
                hallucination
                .result_sanity
                .checks_run
            ),
            issues=(
                hallucination
                .result_sanity
                .issues
            ),
        )
    )

    (
        score,
        signals,
        reasons,
    ) = calculate_weighted_confidence(
        syntax_score=syntax_score,
        alignment_score=(
            hallucination.alignment.score
        ),
        sanity_score=sanity_score,
        schema_coverage_score=(
            hallucination
            .schema_coverage
            .overall_coverage_score
        ),
        agreement_score=agreement.score,
        hallucination_risk=(
            hallucination.risk_level
        ),
        sanity_passed=(
            hallucination
            .result_sanity
            .passed
        ),
        agreement_status=agreement.status,
    )

    label = _confidence_label(
        score
    )

    should_show_result = (
        score
        >= settings.min_confidence_score
        and hallucination.risk_level != "high"
        and agreement.status != "mismatched"
    )

    manual_review_recommended = (
        label != "high"
        or agreement.status
        in {
            "mismatched",
            "failed",
        }
    )

    if not should_show_result:
        reasons.append(
            "The result should be hidden or displayed with "
            "a strong warning because confidence is below "
            "the acceptance threshold."
        )

    signal_scores = {
        signal.name: signal.score
        for signal in signals
    }

    log_confidence_decision(
        question=request.question,
        sql=execution.safe_sql,
        score=score,
        label=label,
        signal_scores=signal_scores,
        agreement_status=agreement.status,
        metadata={
            "hallucination_risk": (
                hallucination.risk_level
            ),
            "should_show_result": (
                should_show_result
            ),
            "rows_returned": (
                execution.row_count
            ),
        },
    )

    return ConfidenceCheckResponse(
        question=request.question,
        sql=request.sql,
        confidence_score=score,
        confidence_percent=round(
            score * 100,
            2,
        ),
        confidence_label=label,
        should_show_result=(
            should_show_result
        ),
        manual_review_recommended=(
            manual_review_recommended
        ),
        signals=signals,
        reasons=reasons,
        multi_query_agreement=agreement,
        hallucination=hallucination,
        metadata={
            "minimum_accepted_score": (
                settings.min_confidence_score
            ),
            "high_threshold": (
                settings
                .confidence_high_threshold
            ),
            "medium_threshold": (
                settings
                .confidence_medium_threshold
            ),
        },
    )