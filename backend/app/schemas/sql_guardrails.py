from typing import Literal

from pydantic import BaseModel, Field


class SQLValidationRequest(BaseModel):
    """SQL submitted to the static safety guardrail."""

    sql: str = Field(
        min_length=1,
        max_length=50_000,
        examples=[
            "SELECT id, full_name FROM customers LIMIT 10;"
        ],
    )


class GuardrailIssue(BaseModel):
    """One safety issue found during SQL validation."""

    code: str
    severity: Literal["info", "warning", "error"]
    message: str


class SQLValidationResponse(BaseModel):
    """Complete static SQL-validation result."""

    original_sql: str

    allowed: bool
    modified: bool

    statement_type: str | None = None

    normalized_sql: str | None = None
    safe_sql: str | None = None

    tables_referenced: list[str] = Field(
        default_factory=list
    )

    columns_referenced: list[str] = Field(
        default_factory=list
    )

    subquery_depth: int = 0

    limit_applied: bool = False
    effective_limit: int | None = None

    issues: list[GuardrailIssue] = Field(
        default_factory=list
    )