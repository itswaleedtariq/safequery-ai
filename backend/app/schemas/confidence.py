from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.app.schemas.hallucination import (
    HallucinationCheckRequest,
    HallucinationCheckResponse,
)
from backend.app.schemas.query_execution import (
    QueryExecutionResponse,
)


class ConfidenceCheckRequest(HallucinationCheckRequest):
    """Question and SQL submitted for confidence scoring."""

    run_multi_query: bool = True


class ConfidenceSignal(BaseModel):
    """One component contributing to the final score."""

    name: str

    score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    configured_weight: float = Field(
        ge=0.0,
        le=1.0,
    )

    effective_weight: float = Field(
        ge=0.0,
        le=1.0,
    )

    weighted_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    available: bool
    explanation: str


class MultiQueryAgreement(BaseModel):
    """Comparison between primary and alternative SQL approaches."""

    required: bool
    attempted: bool

    status: Literal[
        "matched",
        "mismatched",
        "not_required",
        "skipped",
        "failed",
    ]

    score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    primary_sql: str
    alternate_sql: str | None = None

    primary_row_count: int = 0
    alternate_row_count: int | None = None

    exact_match: bool = False
    values_match: bool = False

    explanation: str

    alternate_execution: QueryExecutionResponse | None = None


class ConfidenceCheckResponse(BaseModel):
    """Complete explainable confidence report."""

    question: str
    sql: str

    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence_percent: float = Field(
        ge=0.0,
        le=100.0,
    )

    confidence_label: Literal[
        "high",
        "medium",
        "low",
    ]

    should_show_result: bool
    manual_review_recommended: bool

    signals: list[ConfidenceSignal] = Field(
        default_factory=list
    )

    reasons: list[str] = Field(
        default_factory=list
    )

    multi_query_agreement: MultiQueryAgreement

    hallucination: HallucinationCheckResponse

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )