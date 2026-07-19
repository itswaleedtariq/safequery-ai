from backend.app.services.schema_introspection import (
    clear_schema_cache,
    introspect_database_schema,
)


EXPECTED_TABLES = {
    "categories",
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
}


def test_schema_contains_expected_tables() -> None:
    clear_schema_cache()

    schema = introspect_database_schema()

    actual_tables = {
        table.name
        for table in schema.tables
    }

    assert schema.database_name == "safequery_db"
    assert schema.schema_name == "public"
    assert schema.table_count == 6
    assert actual_tables == EXPECTED_TABLES


def test_orders_foreign_key_points_to_customers() -> None:
    schema = introspect_database_schema()

    orders_table = next(
        table
        for table in schema.tables
        if table.name == "orders"
    )

    relationship_exists = any(
        foreign_key.constrained_columns == ["customer_id"]
        and foreign_key.referred_table == "customers"
        and foreign_key.referred_columns == ["id"]
        for foreign_key in orders_table.foreign_keys
    )

    assert relationship_exists


def test_order_items_has_computed_line_total() -> None:
    schema = introspect_database_schema()

    order_items_table = next(
        table
        for table in schema.tables
        if table.name == "order_items"
    )

    line_total_column = next(
        column
        for column in order_items_table.columns
        if column.name == "line_total"
    )

    assert line_total_column.computed_expression is not None