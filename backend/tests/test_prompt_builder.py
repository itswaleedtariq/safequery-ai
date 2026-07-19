from backend.app.schemas.prompt_context import (
    PromptPreviewRequest,
)
from backend.app.services.prompt_builder import (
    build_prompt_preview,
)


def test_revenue_question_selects_required_tables() -> None:
    result = build_prompt_preview(
        PromptPreviewRequest(
            question=(
                "Which five products generated the "
                "highest revenue?"
            )
        )
    )

    selected_table_names = {
        table.name
        for table in result.selected_tables
    }

    assert "products" in selected_table_names
    assert "order_items" in selected_table_names
    assert "orders" in selected_table_names

    assert result.requires_clarification is False

    assert any(
        term.term == "revenue"
        for term in result.business_terms
    )


def test_ambiguous_city_requires_clarification() -> None:
    result = build_prompt_preview(
        PromptPreviewRequest(
            question="Show revenue by city"
        )
    )

    assert result.requires_clarification is True
    assert result.clarification_message is not None
    assert len(result.clarification_options) == 2


def test_shipping_city_question_is_not_ambiguous() -> None:
    result = build_prompt_preview(
        PromptPreviewRequest(
            question="Show revenue by shipping city"
        )
    )

    selected_table_names = {
        table.name
        for table in result.selected_tables
    }

    assert "orders" in selected_table_names
    assert "order_items" in selected_table_names
    assert result.requires_clarification is False


def test_prompt_contains_schema_and_safety_rules() -> None:
    result = build_prompt_preview(
        PromptPreviewRequest(
            question=(
                "Which five products generated the "
                "highest revenue?"
            )
        )
    )

    assert "TABLE products" in result.prompt
    assert "TABLE order_items" in result.prompt
    assert "TABLE orders" in result.prompt

    assert "Never invent a table" in result.prompt
    assert "Never use INSERT" in result.prompt
    assert "order_items.line_total" in result.prompt


def test_customer_payment_question_includes_bridge_table() -> None:
    result = build_prompt_preview(
        PromptPreviewRequest(
            question=(
                "Show completed payments by customer city"
            )
        )
    )

    selected_table_names = {
        table.name
        for table in result.selected_tables
    }

    assert "payments" in selected_table_names
    assert "customers" in selected_table_names
    assert "orders" in selected_table_names