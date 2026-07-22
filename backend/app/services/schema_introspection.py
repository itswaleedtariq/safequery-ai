from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from sqlalchemy import (
    Boolean,
    Enum,
    MetaData,
    String,
    Table,
    inspect,
    select,
    text,
)
from sqlalchemy.engine import Connection

from backend.app.core.config import get_settings
from backend.app.db.session import engine
from backend.app.schemas.database_schema import (
    ColumnSchema,
    DatabaseSchemaResponse,
    ForeignKeySchema,
    IndexSchema,
    TableSchema,
)


QUERYABLE_TABLE_NAMES = frozenset(
    {
        "categories",
        "customers",
        "products",
        "orders",
        "order_items",
        "payments",
    }
)

settings = get_settings()


def _get_table_comment(
    inspector: Any,
    table_name: str,
    schema_name: str,
) -> str | None:
    """Return a table comment when supported by the database."""

    try:
        comment_information = inspector.get_table_comment(
            table_name,
            schema=schema_name,
        )

        return comment_information.get("text")

    except NotImplementedError:
        return None


def _is_categorical_type(column_type: Any) -> bool:
    """Identify columns that may contain a small set of values."""

    return isinstance(
        column_type,
        (
            String,
            Boolean,
            Enum,
        ),
    )


def _get_categorical_samples(
    connection: Connection,
    reflected_table: Table,
    column_name: str,
) -> list[Any]:
    """
    Return sample values only when the column has low cardinality.

    High-cardinality columns are excluded because they would make the
    schema context unnecessarily large.
    """

    column = reflected_table.c[column_name]

    statement = (
        select(column)
        .where(column.is_not(None))
        .distinct()
        .limit(
            settings.schema_categorical_max_distinct
            + 1
        )
    )

    values = list(
        connection.execute(
            statement
        ).scalars().all()
    )

    if (
        len(values)
        > settings.schema_categorical_max_distinct
    ):
        return []

    return values[
        : settings.schema_sample_limit
    ]


def _build_column_schema(
    connection: Connection,
    reflected_table: Table,
    column_information: dict[str, Any],
    primary_key_columns: set[str],
) -> ColumnSchema:
    """Convert SQLAlchemy column metadata into a response model."""

    column_name = column_information["name"]
    column_type = column_information["type"]

    sample_values: list[Any] = []

    if _is_categorical_type(column_type):
        sample_values = _get_categorical_samples(
            connection=connection,
            reflected_table=reflected_table,
            column_name=column_name,
        )

    default_value = column_information.get(
        "default"
    )

    computed_information = (
        column_information.get("computed")
    )

    computed_expression: str | None = None

    if computed_information:
        computed_sql = (
            computed_information.get("sqltext")
        )

        if computed_sql is not None:
            computed_expression = str(
                computed_sql
            )

    return ColumnSchema(
        name=column_name,
        data_type=str(column_type),
        nullable=bool(
            column_information.get(
                "nullable",
                True,
            )
        ),
        default=(
            str(default_value)
            if default_value is not None
            else None
        ),
        primary_key=(
            column_name
            in primary_key_columns
        ),
        comment=column_information.get(
            "comment"
        ),
        computed_expression=(
            computed_expression
        ),
        sample_values=sample_values,
    )


def _build_foreign_key_schema(
    foreign_key_information: dict[str, Any],
) -> ForeignKeySchema:
    """Convert SQLAlchemy foreign-key metadata into a response model."""

    options = (
        foreign_key_information.get("options")
        or {}
    )

    return ForeignKeySchema(
        name=foreign_key_information.get(
            "name"
        ),
        constrained_columns=(
            foreign_key_information.get(
                "constrained_columns"
            )
            or []
        ),
        referred_schema=(
            foreign_key_information.get(
                "referred_schema"
            )
        ),
        referred_table=(
            foreign_key_information[
                "referred_table"
            ]
        ),
        referred_columns=(
            foreign_key_information.get(
                "referred_columns"
            )
            or []
        ),
        on_update=options.get("onupdate"),
        on_delete=options.get("ondelete"),
    )


def _build_index_schema(
    index_information: dict[str, Any],
) -> IndexSchema:
    """Convert SQLAlchemy index metadata into a response model."""

    column_names = [
        column_name
        for column_name in (
            index_information.get(
                "column_names"
            )
            or []
        )
        if column_name is not None
    ]

    return IndexSchema(
        name=index_information.get(
            "name"
        ),
        column_names=column_names,
        unique=bool(
            index_information.get(
                "unique",
                False,
            )
        ),
    )


@lru_cache(maxsize=1)
def introspect_database_schema(
) -> DatabaseSchemaResponse:
    """
    Inspect the permitted business database tables.

    Internal application tables such as users, sessions, query history,
    feedback, and authentication data are intentionally excluded from
    the schema exposed to the LLM.
    """

    inspector = inspect(engine)
    schema_name = settings.database_schema

    database_table_names = (
        inspector.get_table_names(
            schema=schema_name
        )
    )

    table_names = sorted(
        table_name
        for table_name
        in database_table_names
        if table_name
        in QUERYABLE_TABLE_NAMES
    )

    tables: list[TableSchema] = []

    with engine.connect() as connection:
        database_name = connection.execute(
            text(
                "SELECT current_database()"
            )
        ).scalar_one()

        for table_name in table_names:
            primary_key_information = (
                inspector.get_pk_constraint(
                    table_name,
                    schema=schema_name,
                )
            )

            primary_key_columns = set(
                primary_key_information.get(
                    "constrained_columns"
                )
                or []
            )

            reflected_table = Table(
                table_name,
                MetaData(),
                schema=schema_name,
                autoload_with=connection,
            )

            column_information = (
                inspector.get_columns(
                    table_name,
                    schema=schema_name,
                )
            )

            columns = [
                _build_column_schema(
                    connection=connection,
                    reflected_table=(
                        reflected_table
                    ),
                    column_information=column,
                    primary_key_columns=(
                        primary_key_columns
                    ),
                )
                for column
                in column_information
            ]

            foreign_key_information = (
                inspector.get_foreign_keys(
                    table_name,
                    schema=schema_name,
                )
            )

            foreign_keys = [
                _build_foreign_key_schema(
                    foreign_key
                )
                for foreign_key
                in foreign_key_information
            ]

            index_information = (
                inspector.get_indexes(
                    table_name,
                    schema=schema_name,
                )
            )

            indexes = [
                _build_index_schema(index)
                for index
                in index_information
            ]

            tables.append(
                TableSchema(
                    name=table_name,
                    comment=_get_table_comment(
                        inspector=inspector,
                        table_name=table_name,
                        schema_name=schema_name,
                    ),
                    primary_key_columns=sorted(
                        primary_key_columns
                    ),
                    columns=columns,
                    foreign_keys=foreign_keys,
                    indexes=indexes,
                )
            )

    return DatabaseSchemaResponse(
        database_name=database_name,
        schema_name=schema_name,
        generated_at=datetime.now(
            timezone.utc
        ),
        table_count=len(tables),
        tables=tables,
    )


def clear_schema_cache() -> None:
    """Force the next request to inspect PostgreSQL again."""

    introspect_database_schema.cache_clear()