from types import SimpleNamespace
from uuid import UUID

import pytest

import backend.app.services.query_workflow as workflow
from backend.app.schemas.query_workflow import (
    QueryWorkflowRequest,
)


@pytest.fixture(autouse=True)
def disable_workflow_logging(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        workflow,
        "log_query_workflow",
        lambda **kwargs: None,
    )


def test_clarification_stops_pipeline(
    monkeypatch,
) -> None:
    generation = SimpleNamespace(
        requires_clarification=True,
        clarification_question=(
            "Do you mean customer city or shipping city?"
        ),
        sql=None,
        explanation=(
            "The question has two possible meanings."
        ),
        tables_used=[],
        columns_used=[],
        provider="local",
        model=None,
        guardrail=None,
    )

    monkeypatch.setattr(
        workflow,
        "generate_sql",
        lambda request: generation,
    )

    def confidence_must_not_run(
        request,
    ):
        raise AssertionError(
            "Confidence pipeline should not run."
        )

    monkeypatch.setattr(
        workflow,
        "check_confidence",
        confidence_must_not_run,
    )

    result = workflow.run_query_workflow(
        QueryWorkflowRequest(
            question="Show revenue by city"
        )
    )

    assert result.status == (
        "clarification_required"
    )

    assert result.generated_sql is None
    assert result.rows == []
    assert result.clarification_question


def test_blocked_sql_stops_pipeline(
    monkeypatch,
) -> None:
    issue = SimpleNamespace(
        code="non_read_only_statement",
        severity="error",
        message="Only SELECT queries are permitted.",
    )

    guardrail = SimpleNamespace(
        allowed=False,
        safe_sql=None,
        issues=[issue],
    )

    generation = SimpleNamespace(
        requires_clarification=False,
        clarification_question=None,
        sql="DELETE FROM customers",
        explanation="Deletes customers.",
        tables_used=["customers"],
        columns_used=[],
        provider="groq",
        model="test-model",
        guardrail=guardrail,
    )

    monkeypatch.setattr(
        workflow,
        "generate_sql",
        lambda request: generation,
    )

    result = workflow.run_query_workflow(
        QueryWorkflowRequest(
            question="Delete all customers"
        )
    )

    assert result.status == "blocked"
    assert result.guardrail_allowed is False
    assert result.result_hidden is True
    assert result.rows == []


def test_successful_workflow_returns_rows(
    monkeypatch,
) -> None:
    guardrail = SimpleNamespace(
        allowed=True,
        safe_sql=(
            "SELECT COUNT(*) AS customer_count "
            "FROM customers LIMIT 1000;"
        ),
        issues=[],
    )

    generation = SimpleNamespace(
        requires_clarification=False,
        clarification_question=None,
        sql=(
            "SELECT COUNT(*) AS customer_count "
            "FROM customers"
        ),
        explanation="Counts all customers.",
        tables_used=["customers"],
        columns_used=[],
        provider="groq",
        model="test-model",
        guardrail=guardrail,
    )

    execution = SimpleNamespace(
        safe_sql=guardrail.safe_sql,
        columns=["customer_count"],
        rows=[
            {
                "customer_count": 500,
            }
        ],
        row_count=1,
        execution_time_ms=1.5,
        guardrail=guardrail,
    )

    hallucination = SimpleNamespace(
        execution=execution,
        hallucination_detected=False,
        risk_level="low",
        issues=[],
    )

    agreement = SimpleNamespace(
        status="not_required",
        explanation=(
            "A second query was not required."
        ),
    )

    confidence = SimpleNamespace(
        confidence_score=0.96,
        confidence_percent=96.0,
        confidence_label="high",
        should_show_result=True,
        manual_review_recommended=False,
        signals=[],
        hallucination=hallucination,
        multi_query_agreement=agreement,
        reasons=[],
    )

    monkeypatch.setattr(
        workflow,
        "generate_sql",
        lambda request: generation,
    )

    monkeypatch.setattr(
        workflow,
        "check_confidence",
        lambda request: confidence,
    )

    result = workflow.run_query_workflow(
        QueryWorkflowRequest(
            question="How many customers are there?"
        )
    )

    assert result.status == "completed"
    assert result.rows == [
        {
            "customer_count": 500,
        }
    ]

    assert result.confidence_label == "high"
    assert result.result_hidden is False

    UUID(result.request_id)


def test_low_confidence_hides_rows(
    monkeypatch,
) -> None:
    guardrail = SimpleNamespace(
        allowed=True,
        safe_sql=(
            "SELECT id FROM customers LIMIT 1000;"
        ),
        issues=[],
    )

    generation = SimpleNamespace(
        requires_clarification=False,
        clarification_question=None,
        sql="SELECT id FROM customers",
        explanation="Returns customer IDs.",
        tables_used=["customers"],
        columns_used=["customers.id"],
        provider="groq",
        model="test-model",
        guardrail=guardrail,
    )

    execution = SimpleNamespace(
        safe_sql=guardrail.safe_sql,
        columns=["id"],
        rows=[
            {
                "id": 1,
            }
        ],
        row_count=1,
        execution_time_ms=1.0,
        guardrail=guardrail,
    )

    issue = SimpleNamespace(
        code="question_sql_misalignment",
        severity="error",
        message=(
            "The SQL does not answer the question."
        ),
    )

    hallucination = SimpleNamespace(
        execution=execution,
        hallucination_detected=True,
        risk_level="high",
        issues=[issue],
    )

    agreement = SimpleNamespace(
        status="skipped",
        explanation=(
            "Skipped due to high hallucination risk."
        ),
    )

    confidence = SimpleNamespace(
        confidence_score=0.40,
        confidence_percent=40.0,
        confidence_label="low",
        should_show_result=False,
        manual_review_recommended=True,
        signals=[],
        hallucination=hallucination,
        multi_query_agreement=agreement,
        reasons=[
            (
                "Confidence was capped because "
                "hallucination risk is high."
            )
        ],
    )

    monkeypatch.setattr(
        workflow,
        "generate_sql",
        lambda request: generation,
    )

    monkeypatch.setattr(
        workflow,
        "check_confidence",
        lambda request: confidence,
    )

    result = workflow.run_query_workflow(
        QueryWorkflowRequest(
            question="How many customers are there?"
        )
    )

    assert result.status == "review_required"
    assert result.rows == []
    assert result.result_columns == []
    assert result.row_count == 1
    assert result.result_hidden is True
    assert result.manual_review_recommended is True