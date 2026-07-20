import pytest
from sqlalchemy import text

from backend.app.core.exceptions import (
    QueryRejectedError,
)
from backend.app.db.readonly_session import (
    get_readonly_engine,
)
from backend.app.schemas.query_execution import (
    QueryExecutionRequest,
)
from backend.app.services.query_executor import (
    execute_readonly_query,
)


def test_readonly_engine_uses_reader_role() -> None:
    engine = get_readonly_engine()

    with engine.connect() as connection:
        current_user = connection.execute(
            text("SELECT current_user")
        ).scalar_one()

    assert current_user == "safequery_reader"


def test_reader_defaults_to_read_only() -> None:
    engine = get_readonly_engine()

    with engine.connect() as connection:
        read_only = connection.execute(
            text(
                "SHOW default_transaction_read_only"
            )
        ).scalar_one()

    assert read_only == "on"


def test_execute_small_select() -> None:
    result = execute_readonly_query(
        QueryExecutionRequest(
            sql=(
                "SELECT id, full_name "
                "FROM customers LIMIT 5"
            )
        )
    )

    assert result.row_count == 5
    assert result.rolled_back is True
    assert result.guardrail.allowed is True
    assert result.safe_sql is not None
    assert len(result.columns) == 2


def test_execute_count_query() -> None:
    result = execute_readonly_query(
        QueryExecutionRequest(
            sql=(
                "SELECT COUNT(*) AS order_count "
                "FROM orders"
            )
        )
    )

    assert result.row_count == 1
    assert result.rows[0]["order_count"] == 2000
    assert result.explain.total_cost >= 0
    assert result.execution_time_ms >= 0


def test_query_without_limit_gets_capped() -> None:
    result = execute_readonly_query(
        QueryExecutionRequest(
            sql="SELECT id FROM customers"
        )
    )

    assert result.guardrail.effective_limit == 1000
    assert "LIMIT 1000" in result.safe_sql.upper()


def test_delete_is_rejected_before_execution() -> None:
    with pytest.raises(QueryRejectedError):
        execute_readonly_query(
            QueryExecutionRequest(
                sql="DELETE FROM customers"
            )
        )


def test_unknown_table_is_rejected() -> None:
    with pytest.raises(QueryRejectedError):
        execute_readonly_query(
            QueryExecutionRequest(
                sql="SELECT * FROM private_users"
            )
        )


def test_execution_response_contains_plan() -> None:
    result = execute_readonly_query(
        QueryExecutionRequest(
            sql=(
                "SELECT id, name "
                "FROM products LIMIT 3"
            )
        )
    )

    assert result.explain.raw_plan
    assert result.explain.root_plan_rows >= 0
    assert result.explain.total_cost >= 0