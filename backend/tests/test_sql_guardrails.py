from backend.app.guardrails.sql_validator import (
    validate_sql,
)
from backend.app.schemas.sql_guardrails import (
    SQLValidationRequest,
)


def validate(query: str):
    return validate_sql(
        SQLValidationRequest(sql=query)
    )


def issue_codes(result) -> set[str]:
    return {
        issue.code
        for issue in result.issues
    }


def test_safe_select_gets_limit() -> None:
    result = validate(
        "SELECT id, full_name FROM customers"
    )

    assert result.allowed is True
    assert result.modified is True
    assert result.safe_sql is not None
    assert "LIMIT 1000" in result.safe_sql.upper()
    assert result.effective_limit == 1000


def test_existing_small_limit_is_preserved() -> None:
    result = validate(
        "SELECT id FROM customers LIMIT 25"
    )

    assert result.allowed is True
    assert result.modified is False
    assert result.effective_limit == 25


def test_large_limit_is_capped() -> None:
    result = validate(
        "SELECT id FROM customers LIMIT 50000"
    )

    assert result.allowed is True
    assert result.modified is True
    assert result.effective_limit == 1000
    assert "limit_capped" in issue_codes(result)


def test_delete_is_blocked() -> None:
    result = validate(
        "DELETE FROM customers"
    )

    assert result.allowed is False
    assert result.safe_sql is None
    assert "non_read_only_statement" in issue_codes(
        result
    )


def test_multiple_statements_are_blocked() -> None:
    result = validate(
        "SELECT * FROM customers; "
        "DROP TABLE customers;"
    )

    assert result.allowed is False
    assert "multiple_statements" in issue_codes(
        result
    )


def test_unknown_table_is_blocked() -> None:
    result = validate(
        "SELECT * FROM secret_users"
    )

    assert result.allowed is False
    assert "unknown_table" in issue_codes(result)


def test_unknown_qualified_column_is_blocked() -> None:
    result = validate(
        "SELECT c.nonexistent_column "
        "FROM customers AS c"
    )

    assert result.allowed is False
    assert "unknown_column" in issue_codes(result)


def test_sql_comments_are_blocked() -> None:
    result = validate(
        "SELECT * FROM customers -- hidden text"
    )

    assert result.allowed is False
    assert (
        "sql_comments_not_allowed"
        in issue_codes(result)
    )


def test_dangerous_function_is_blocked() -> None:
    result = validate(
        "SELECT pg_sleep(1)"
    )

    assert result.allowed is False
    assert (
        "blocked_function_pg_sleep"
        in issue_codes(result)
    )


def test_cte_select_is_allowed() -> None:
    result = validate(
        """
        WITH customer_orders AS (
            SELECT
                customer_id,
                COUNT(*) AS order_count
            FROM orders
            GROUP BY customer_id
        )
        SELECT
            customer_id,
            order_count
        FROM customer_orders
        """
    )

    assert result.allowed is True
    assert result.safe_sql is not None


def test_deep_subquery_is_blocked() -> None:
    result = validate(
        """
        SELECT *
        FROM (
            SELECT *
            FROM (
                SELECT *
                FROM (
                    SELECT *
                    FROM (
                        SELECT id
                        FROM customers
                    ) AS level_four
                ) AS level_three
            ) AS level_two
        ) AS level_one
        """
    )

    assert result.allowed is False
    assert (
        "subquery_depth_exceeded"
        in issue_codes(result)
    )


def test_ambiguous_unqualified_column_is_blocked() -> None:
    result = validate(
        """
        SELECT id
        FROM orders
        JOIN customers
          ON orders.customer_id = customers.id
        """
    )

    assert result.allowed is False
    assert "ambiguous_column" in issue_codes(
        result
    )