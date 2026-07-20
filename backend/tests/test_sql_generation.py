import json

import pytest
from pydantic import ValidationError

from backend.app.schemas.sql_generation import (
    SQLGenerationPayload,
    SQLGenerationRequest,
)
from backend.app.services.sql_generator import (
    generate_sql,
    parse_generation_content,
)


def test_valid_generation_payload() -> None:
    payload = SQLGenerationPayload(
        sql="SELECT COUNT(*) FROM orders;",
        explanation="Counts all orders.",
        tables_used=["orders"],
        columns_used=[],
        confidence=0.95,
        requires_clarification=False,
        clarification_question=None,
    )

    assert payload.sql == "SELECT COUNT(*) FROM orders;"
    assert payload.confidence == 0.95


def test_confidence_must_be_between_zero_and_one() -> None:
    with pytest.raises(ValidationError):
        SQLGenerationPayload(
            sql="SELECT COUNT(*) FROM orders;",
            explanation="Counts all orders.",
            tables_used=["orders"],
            columns_used=[],
            confidence=1.5,
            requires_clarification=False,
            clarification_question=None,
        )


def test_clarification_response_cannot_contain_sql() -> None:
    with pytest.raises(ValidationError):
        SQLGenerationPayload(
            sql="SELECT * FROM orders;",
            explanation="Needs clarification.",
            tables_used=["orders"],
            columns_used=[],
            confidence=0.2,
            requires_clarification=True,
            clarification_question=(
                "Do you mean completed or all orders?"
            ),
        )


def test_parse_generation_content() -> None:
    content = json.dumps(
        {
            "sql": "SELECT COUNT(*) FROM orders;",
            "explanation": "Counts all orders.",
            "tables_used": ["orders"],
            "columns_used": [],
            "confidence": 0.9,
            "requires_clarification": False,
            "clarification_question": None,
        }
    )

    result = parse_generation_content(content)

    assert result.tables_used == ["orders"]
    assert result.requires_clarification is False


def test_ambiguous_question_bypasses_groq() -> None:
    result = generate_sql(
        SQLGenerationRequest(
            question="Show revenue by city"
        )
    )

    assert result.sql is None
    assert result.requires_clarification is True
    assert result.provider == "local"
    assert result.model is None
    assert result.token_usage.total_tokens == 0