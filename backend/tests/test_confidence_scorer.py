from backend.app.services.confidence_scorer import (
    calculate_result_sanity_score,
    calculate_weighted_confidence,
    compare_result_sets,
)


class FakeIssue:
    def __init__(
        self,
        severity: str,
    ) -> None:
        self.severity = severity


def test_perfect_signals_produce_high_score() -> None:
    score, signals, reasons = (
        calculate_weighted_confidence(
            syntax_score=1.0,
            alignment_score=1.0,
            sanity_score=1.0,
            schema_coverage_score=1.0,
            agreement_score=1.0,
            hallucination_risk="low",
            sanity_passed=True,
            agreement_status="matched",
        )
    )

    assert score == 1.0
    assert len(signals) == 5
    assert reasons == []


def test_missing_agreement_renormalizes_weights() -> None:
    score, signals, _ = (
        calculate_weighted_confidence(
            syntax_score=1.0,
            alignment_score=1.0,
            sanity_score=1.0,
            schema_coverage_score=1.0,
            agreement_score=None,
            hallucination_risk="low",
            sanity_passed=True,
            agreement_status="not_required",
        )
    )

    agreement = next(
        signal
        for signal in signals
        if signal.name
        == "multi_query_agreement"
    )

    assert score == 1.0
    assert agreement.available is False
    assert agreement.effective_weight == 0.0


def test_high_hallucination_risk_caps_score() -> None:
    score, _, reasons = (
        calculate_weighted_confidence(
            syntax_score=1.0,
            alignment_score=1.0,
            sanity_score=1.0,
            schema_coverage_score=1.0,
            agreement_score=1.0,
            hallucination_risk="high",
            sanity_passed=True,
            agreement_status="matched",
        )
    )

    assert score <= 0.49
    assert reasons


def test_result_mismatch_caps_score() -> None:
    score, _, reasons = (
        calculate_weighted_confidence(
            syntax_score=1.0,
            alignment_score=1.0,
            sanity_score=1.0,
            schema_coverage_score=1.0,
            agreement_score=0.0,
            hallucination_risk="low",
            sanity_passed=True,
            agreement_status="mismatched",
        )
    )

    assert score <= 0.59
    assert reasons


def test_result_sanity_score_penalizes_issues() -> None:
    score = calculate_result_sanity_score(
        checks_run=10,
        issues=[
            FakeIssue("error"),
            FakeIssue("warning"),
        ],
    )

    assert score == 0.85


def test_exact_result_sets_match() -> None:
    exact, values, score, _ = (
        compare_result_sets(
            primary_rows=[
                {
                    "name": "Product A",
                    "revenue": 100,
                }
            ],
            alternate_rows=[
                {
                    "name": "Product A",
                    "revenue": 100,
                }
            ],
        )
    )

    assert exact is True
    assert values is True
    assert score == 1.0


def test_different_result_sets_do_not_match() -> None:
    exact, values, score, _ = (
        compare_result_sets(
            primary_rows=[
                {
                    "count": 10,
                }
            ],
            alternate_rows=[
                {
                    "count": 11,
                }
            ],
        )
    )

    assert exact is False
    assert values is False
    assert score == 0.0