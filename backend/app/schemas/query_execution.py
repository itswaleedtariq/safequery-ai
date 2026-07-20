from typing import Any

from pydantic import BaseModel, Field

from backend.app.schemas.sql_guardrails import (
    SQLValidationResponse,
)


class QueryExecutionRequest(BaseModel):
    """SQL submitted for guarded read-only execution."""

    sql: str = Field(
        min_length=1,
        max_length=50_000,
        examples=[
            (
                "SELECT id, full_name "
                "FROM customers LIMIT 10;"
            )
        ],
    )


class ExplainScanNode(BaseModel):
    """One scan operation found in a PostgreSQL plan."""

    node_type: str
    relation_name: str | None = None
    plan_rows: int = 0
    total_cost: float = 0.0


class ExplainPlanSummary(BaseModel):
    """Safety-relevant information extracted from EXPLAIN."""

    total_cost: float = 0.0
    root_plan_rows: int = 0
    estimated_rows_scanned: int = 0

    scan_nodes: list[ExplainScanNode] = Field(
        default_factory=list
    )

    raw_plan: dict[str, Any] = Field(
        default_factory=dict
    )


class QueryExecutionResponse(BaseModel):
    """Result of one approved read-only query."""

    original_sql: str
    safe_sql: str

    columns: list[str] = Field(
        default_factory=list
    )

    rows: list[dict[str, Any]] = Field(
        default_factory=list
    )

    row_count: int = 0
    row_limit_reached: bool = False

    execution_time_ms: float = Field(
        ge=0.0
    )

    rolled_back: bool = True

    guardrail: SQLValidationResponse
    explain: ExplainPlanSummary