from typing import Literal

from pydantic import BaseModel, Field

from backend.app.schemas.prompt_context import (
    PromptPreviewRequest,
)
from backend.app.schemas.query_execution import (
    QueryExecutionResponse,
)
from backend.app.schemas.sql_generation import TokenUsage


class HallucinationCheckRequest(PromptPreviewRequest):
    """Question and SQL submitted for hallucination analysis."""

    sql: str = Field(
        min_length=1,
        max_length=50_000,
        examples=[
            (
                "SELECT COUNT(*) AS order_count "
                "FROM orders;"
            )
        ],
    )


class BackTranslationResult(BaseModel):
    """Description of the question answered by the SQL."""

    question_answered: str

    operation: str

    metrics: list[str] = Field(
        default_factory=list
    )

    dimensions: list[str] = Field(
        default_factory=list
    )

    filters: list[str] = Field(
        default_factory=list
    )

    grouping: list[str] = Field(
        default_factory=list
    )

    ordering: list[str] = Field(
        default_factory=list
    )

    limit: int | None = None


class AlignmentResult(BaseModel):
    """Semantic comparison between two questions."""

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    verdict: Literal[
        "aligned",
        "partially_aligned",
        "misaligned",
    ]

    matched_requirements: list[str] = Field(
        default_factory=list
    )

    missing_requirements: list[str] = Field(
        default_factory=list
    )

    extra_assumptions: list[str] = Field(
        default_factory=list
    )

    explanation: str


class SchemaCoverageResult(BaseModel):
    """Comparison of expected and actual schema usage."""

    expected_tables: list[str] = Field(
        default_factory=list
    )

    actual_tables: list[str] = Field(
        default_factory=list
    )

    matched_tables: list[str] = Field(
        default_factory=list
    )

    missing_tables: list[str] = Field(
        default_factory=list
    )

    expected_business_columns: list[str] = Field(
        default_factory=list
    )

    actual_columns: list[str] = Field(
        default_factory=list
    )

    matched_business_columns: list[str] = Field(
        default_factory=list
    )

    missing_business_columns: list[str] = Field(
        default_factory=list
    )

    table_coverage_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    column_coverage_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    overall_coverage_score: float = Field(
        ge=0.0,
        le=1.0,
    )


class HallucinationIssue(BaseModel):
    """One suspicious signal discovered by the detector."""

    code: str

    severity: Literal[
        "info",
        "warning",
        "error",
    ]

    signal: Literal[
        "back_translation",
        "schema_coverage",
        "query_shape",
        "business_rule",
        "result_sanity",
    ]

    message: str


class ResultSanityResult(BaseModel):
    """Deterministic analysis of execution results."""

    passed: bool
    checks_run: int

    null_ratios: dict[str, float] = Field(
        default_factory=dict
    )

    issues: list[HallucinationIssue] = Field(
        default_factory=list
    )


class HallucinationCheckResponse(BaseModel):
    """Complete hallucination-detection response."""

    question: str
    sql: str

    hallucination_detected: bool

    risk_level: Literal[
        "low",
        "medium",
        "high",
    ]

    back_translation: BackTranslationResult
    alignment: AlignmentResult
    schema_coverage: SchemaCoverageResult
    result_sanity: ResultSanityResult

    issues: list[HallucinationIssue] = Field(
        default_factory=list
    )

    execution: QueryExecutionResponse

    provider: Literal["groq"]
    model: str

    latency_ms: float = Field(ge=0.0)
    token_usage: TokenUsage