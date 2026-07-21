import backend.app.services.hallucination_detector as detector

from backend.app.schemas.hallucination import (
    AlignmentResult,
    BackTranslationResult,
    HallucinationCheckRequest,
)
from backend.app.schemas.sql_generation import TokenUsage


CORRECT_REVENUE_SQL = """
SELECT
    p.name,
    SUM(oi.line_total) AS revenue
FROM products AS p
JOIN order_items AS oi
  ON oi.product_id = p.id
JOIN orders AS o
  ON o.id = oi.order_id
WHERE o.status IN ('completed', 'shipped')
GROUP BY p.id, p.name
ORDER BY revenue DESC
LIMIT 5
"""


def aligned_backtranslation(
    **kwargs,
):
    return (
        BackTranslationResult(
            question_answered=(
                "Which five products generated the highest "
                "revenue from completed or shipped orders?"
            ),
            operation="sum",
            metrics=["revenue"],
            dimensions=["product"],
            filters=[
                "completed or shipped orders"
            ],
            grouping=["product"],
            ordering=[
                "revenue descending"
            ],
            limit=5,
        ),
        TokenUsage(),
    )


def aligned_judge(
    **kwargs,
):
    return (
        AlignmentResult(
            score=0.95,
            verdict="aligned",
            matched_requirements=[
                "five products",
                "highest revenue",
                "valid order statuses",
            ],
            missing_requirements=[],
            extra_assumptions=[],
            explanation=(
                "The SQL answers the requested question."
            ),
        ),
        TokenUsage(),
    )


def misaligned_backtranslation(
    **kwargs,
):
    return (
        BackTranslationResult(
            question_answered=(
                "How many customers are stored?"
            ),
            operation="count",
            metrics=["customer count"],
            dimensions=[],
            filters=[],
            grouping=[],
            ordering=[],
            limit=None,
        ),
        TokenUsage(),
    )


def misaligned_judge(
    **kwargs,
):
    return (
        AlignmentResult(
            score=0.10,
            verdict="misaligned",
            matched_requirements=[],
            missing_requirements=[
                "product",
                "revenue",
                "top five",
            ],
            extra_assumptions=[
                "customer count"
            ],
            explanation=(
                "The SQL counts customers instead of "
                "calculating product revenue."
            ),
        ),
        TokenUsage(),
    )


def test_correct_revenue_query_is_not_flagged(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        detector,
        "backtranslate_sql",
        aligned_backtranslation,
    )

    monkeypatch.setattr(
        detector,
        "judge_question_alignment",
        aligned_judge,
    )

    result = detector.check_hallucination(
        HallucinationCheckRequest(
            question=(
                "Which five products generated the "
                "highest revenue?"
            ),
            sql=CORRECT_REVENUE_SQL,
        )
    )

    assert result.hallucination_detected is False
    assert result.risk_level == "low"
    assert result.alignment.score == 0.95


def test_wrong_customer_query_is_flagged(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        detector,
        "backtranslate_sql",
        misaligned_backtranslation,
    )

    monkeypatch.setattr(
        detector,
        "judge_question_alignment",
        misaligned_judge,
    )

    result = detector.check_hallucination(
        HallucinationCheckRequest(
            question=(
                "Which five products generated the "
                "highest revenue?"
            ),
            sql=(
                "SELECT COUNT(*) AS customer_count "
                "FROM customers"
            ),
        )
    )

    issue_codes = {
        issue.code
        for issue in result.issues
    }

    assert result.hallucination_detected is True
    assert result.risk_level == "high"

    assert (
        "question_sql_misalignment"
        in issue_codes
    )


def test_revenue_without_sum_is_flagged() -> None:
    execution = detector.execute_readonly_query(
        detector.QueryExecutionRequest(
            sql=(
                "SELECT id, total_amount "
                "FROM orders LIMIT 5"
            )
        )
    )

    result = detector.check_result_sanity(
        question="Show total revenue.",
        sql=execution.safe_sql,
        execution=execution,
    )

    issue_codes = {
        issue.code
        for issue in result.issues
    }

    assert result.passed is False
    assert "revenue_sum_missing" in issue_codes


def test_count_question_requires_count() -> None:
    execution = detector.execute_readonly_query(
        detector.QueryExecutionRequest(
            sql=(
                "SELECT id FROM orders LIMIT 5"
            )
        )
    )

    result = detector.check_result_sanity(
        question="How many orders are there?",
        sql=execution.safe_sql,
        execution=execution,
    )

    issue_codes = {
        issue.code
        for issue in result.issues
    }

    assert "count_operation_missing" in issue_codes

def test_revenue_status_filter_is_valid_business_rule() -> None:
    back_translation = BackTranslationResult(
        question_answered=(
            "Which five products generated the highest "
            "revenue from completed or shipped orders?"
        ),
        operation="sum",
        metrics=["revenue"],
        dimensions=["product"],
        filters=[
            "orders with completed or shipped status"
        ],
        grouping=["product"],
        ordering=["revenue descending"],
        limit=5,
    )

    alignment = AlignmentResult(
        score=0.60,
        verdict="misaligned",
        matched_requirements=[
            "top five products",
            "highest revenue",
        ],
        missing_requirements=[],
        extra_assumptions=[
            "Only completed or shipped orders are included."
        ],
        explanation=(
            "The original question did not explicitly "
            "mention order statuses."
        ),
    )

    normalized = (
        detector._normalize_business_rule_alignment(
            original_question=(
                "Which five products generated the "
                "highest revenue?"
            ),
            back_translation=back_translation,
            alignment=alignment,
        )
    )

    assert normalized.verdict == "aligned"
    assert normalized.score >= 0.90
    assert normalized.extra_assumptions == []    