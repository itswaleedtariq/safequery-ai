from typing import Any, Literal
from backend.app.schemas.confidence import ConfidenceSignal
from pydantic import BaseModel, Field

from backend.app.schemas.prompt_context import (
    PromptPreviewRequest,
)


class QueryWorkflowRequest(PromptPreviewRequest):
    """Natural-language question submitted to the full pipeline."""

    run_multi_query: bool = True


class WorkflowWarning(BaseModel):
    """One warning or error produced by a pipeline stage."""

    code: str

    severity: Literal[
        "info",
        "warning",
        "error",
    ]

    message: str


class WorkflowTimings(BaseModel):
    """Wall-clock timings for major workflow stages."""

    generation_ms: float = Field(ge=0.0)

    confidence_pipeline_ms: float = Field(
        ge=0.0
    )

    total_ms: float = Field(ge=0.0)


class QueryWorkflowResponse(BaseModel):
    """Final user-facing response from the complete pipeline."""

    request_id: str

    status: Literal[
        "completed",
        "clarification_required",
        "blocked",
        "review_required",
    ]

    question: str
    summary: str

    generated_sql: str | None = None
    safe_sql: str | None = None

    explanation: str

    tables_used: list[str] = Field(
        default_factory=list
    )

    columns_used: list[str] = Field(
        default_factory=list
    )

    result_columns: list[str] = Field(
        default_factory=list
    )

    rows: list[dict[str, Any]] = Field(
        default_factory=list
    )

    row_count: int = 0
    result_hidden: bool = False

    guardrail_allowed: bool | None = None

    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    confidence_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    confidence_label: (
        Literal["high", "medium", "low"]
        | None
    ) = None

    manual_review_recommended: bool = False
    confidence_signals: list[ConfidenceSignal] = Field(
        default_factory=list
    )

    confidence_reasons: list[str] = Field(
        default_factory=list
    )
    hallucination_detected: bool | None = None

    hallucination_risk: (
        Literal["low", "medium", "high"]
        | None
    ) = None

    multi_query_status: (
        Literal[
            "matched",
            "mismatched",
            "not_required",
            "skipped",
            "failed",
        ]
        | None
    ) = None

    clarification_question: str | None = None

    warnings: list[WorkflowWarning] = Field(
        default_factory=list
    )

    provider: str | None = None
    model: str | None = None

    timings: WorkflowTimings