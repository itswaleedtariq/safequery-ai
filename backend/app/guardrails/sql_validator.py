from __future__ import annotations

from typing import Any

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from backend.app.core.audit_logger import (
    log_guardrail_decision,
)
from backend.app.core.config import get_settings
from backend.app.schemas.database_schema import (
    DatabaseSchemaResponse,
)
from backend.app.schemas.sql_guardrails import (
    GuardrailIssue,
    SQLValidationRequest,
    SQLValidationResponse,
)
from backend.app.services.schema_introspection import (
    introspect_database_schema,
)


settings = get_settings()


BLOCKED_EXPRESSION_NAMES = {
    "insert",
    "update",
    "delete",
    "create",
    "drop",
    "alter",
    "merge",
    "truncatetable",
    "command",
    "grant",
    "revoke",
    "transaction",
    "commit",
    "rollback",
    "copy",
    "into",
    "lock",
    "set",
    "use",
    "execute",
    "prepare",
    "load",
    "cache",
    "uncache",
}


def _add_issue(
    issues: list[GuardrailIssue],
    *,
    code: str,
    severity: str,
    message: str,
) -> None:
    """Append an issue unless the same issue already exists."""

    duplicate_exists = any(
        issue.code == code
        and issue.message == message
        for issue in issues
    )

    if duplicate_exists:
        return

    issues.append(
        GuardrailIssue(
            code=code,
            severity=severity,
            message=message,
        )
    )


def _has_error(
    issues: list[GuardrailIssue],
) -> bool:
    """Return True when at least one blocking issue exists."""

    return any(
        issue.severity == "error"
        for issue in issues
    )


def _contains_sql_comment(sql: str) -> bool:
    """
    Detect comments outside ordinary quoted strings.

    Both single-line and block comments are rejected because comments
    can be used to hide or alter the visible meaning of generated SQL.
    """

    inside_single_quote = False
    inside_double_quote = False

    index = 0

    while index < len(sql):
        character = sql[index]
        next_character = (
            sql[index + 1]
            if index + 1 < len(sql)
            else ""
        )

        if inside_single_quote:
            if (
                character == "'"
                and next_character == "'"
            ):
                index += 2
                continue

            if character == "'":
                inside_single_quote = False

            index += 1
            continue

        if inside_double_quote:
            if (
                character == '"'
                and next_character == '"'
            ):
                index += 2
                continue

            if character == '"':
                inside_double_quote = False

            index += 1
            continue

        if character == "'":
            inside_single_quote = True
            index += 1
            continue

        if character == '"':
            inside_double_quote = True
            index += 1
            continue

        if (
            character == "-"
            and next_character == "-"
        ):
            return True

        if (
            character == "/"
            and next_character == "*"
        ):
            return True

        index += 1

    return False


def _render_sql(
    expression: exp.Expression,
) -> str:
    """Render normalized PostgreSQL ending with one semicolon."""

    rendered = expression.sql(
        dialect="postgres",
        pretty=False,
        comments=False,
    ).strip()

    return rendered.rstrip(";") + ";"


def _get_function_name(
    function: exp.Func,
) -> str:
    """Extract a normalized SQL function name."""

    name = getattr(function, "name", "")

    if name:
        return str(name).lower()

    sql_name = getattr(
        function,
        "sql_name",
        None,
    )

    if callable(sql_name):
        return str(sql_name()).lower()

    return type(function).__name__.lower()


def _validate_statement_type(
    expression: exp.Expression,
    issues: list[GuardrailIssue],
) -> None:
    """Allow only query expressions containing SELECT."""

    if not isinstance(expression, exp.Query):
        _add_issue(
            issues,
            code="non_read_only_statement",
            severity="error",
            message=(
                "Only SELECT and WITH ... SELECT queries "
                "are permitted."
            ),
        )

        return

    if expression.find(exp.Select) is None:
        _add_issue(
            issues,
            code="select_required",
            severity="error",
            message=(
                "The query must contain a SELECT statement."
            ),
        )


def _validate_blocked_operations(
    expression: exp.Expression,
    issues: list[GuardrailIssue],
) -> None:
    """Reject write operations, DDL and administrative commands."""

    blocked_nodes = {
        type(node).__name__.lower()
        for node in expression.walk()
        if (
            type(node).__name__.lower()
            in BLOCKED_EXPRESSION_NAMES
        )
    }

    for blocked_node in sorted(blocked_nodes):
        _add_issue(
            issues,
            code=f"blocked_operation_{blocked_node}",
            severity="error",
            message=(
                f"Blocked SQL operation detected: "
                f"{blocked_node}."
            ),
        )


def _validate_functions(
    expression: exp.Expression,
    issues: list[GuardrailIssue],
) -> None:
    """Reject configured PostgreSQL functions with side effects."""

    blocked_functions = {
        name.strip().lower()
        for name in (
            settings.blocked_sql_functions.split(",")
        )
        if name.strip()
    }

    for function in expression.find_all(exp.Func):
        function_name = _get_function_name(
            function
        )

        if function_name not in blocked_functions:
            continue

        _add_issue(
            issues,
            code=f"blocked_function_{function_name}",
            severity="error",
            message=(
                f"Function '{function_name}' is not "
                "allowed in generated SQL."
            ),
        )


def _calculate_subquery_depth(
    expression: exp.Expression,
) -> int:
    """Calculate maximum nested Subquery-node depth."""

    maximum_depth = 0

    def visit(
        node: exp.Expression,
        current_depth: int,
    ) -> None:
        nonlocal maximum_depth

        next_depth = current_depth

        if isinstance(node, exp.Subquery):
            next_depth += 1
            maximum_depth = max(
                maximum_depth,
                next_depth,
            )

        for child in node.iter_expressions():
            visit(child, next_depth)

    visit(expression, 0)

    return maximum_depth


def _get_cte_outputs(
    expression: exp.Expression,
) -> dict[str, set[str]]:
    """Return known output-column names for every CTE."""

    outputs: dict[str, set[str]] = {}

    for cte in expression.find_all(exp.CTE):
        cte_name = str(
            cte.alias_or_name
        ).lower()

        output_columns: set[str] = set()

        for projection in getattr(
            cte.this,
            "selects",
            [],
        ):
            projection_name = str(
                projection.alias_or_name or ""
            ).lower()

            if (
                projection_name
                and projection_name != "*"
            ):
                output_columns.add(
                    projection_name
                )

        outputs[cte_name] = output_columns

    return outputs


def _get_schema_columns(
    schema: DatabaseSchemaResponse,
) -> dict[str, set[str]]:
    """Map every real table to its real column names."""

    return {
        table.name.lower(): {
            column.name.lower()
            for column in table.columns
        }
        for table in schema.tables
    }


def _validate_schema_references(
    expression: exp.Expression,
    schema: DatabaseSchemaResponse,
    issues: list[GuardrailIssue],
) -> tuple[list[str], list[str]]:
    """
    Validate referenced tables and columns against PostgreSQL metadata.

    CTE names and projected aliases are handled separately because they
    are generated by the query rather than stored in PostgreSQL.
    """

    schema_columns = _get_schema_columns(
        schema
    )

    cte_outputs = _get_cte_outputs(
        expression
    )

    physical_aliases: dict[str, str] = {}
    cte_aliases: dict[str, set[str]] = {}

    referenced_tables: set[str] = set()
    referenced_columns: set[str] = set()

    for table in expression.find_all(exp.Table):
        table_name = str(
            table.name
        ).lower()

        table_alias = str(
            table.alias_or_name or table_name
        ).lower()

        if table_name in cte_outputs:
            output_columns = cte_outputs[
                table_name
            ]

            cte_aliases[table_alias] = (
                output_columns
            )

            cte_aliases[table_name] = (
                output_columns
            )

            continue

        catalog_name = str(
            table.catalog or ""
        ).lower()

        schema_name = str(
            table.db or ""
        ).lower()

        if catalog_name:
            _add_issue(
                issues,
                code="cross_database_access",
                severity="error",
                message=(
                    "Cross-database table references "
                    "are not allowed."
                ),
            )

        if (
            schema_name
            and schema_name
            != settings.database_schema.lower()
        ):
            _add_issue(
                issues,
                code="schema_not_allowed",
                severity="error",
                message=(
                    f"Schema '{schema_name}' is not allowed."
                ),
            )

        if table_name not in schema_columns:
            _add_issue(
                issues,
                code="unknown_table",
                severity="error",
                message=(
                    f"Table '{table_name}' does not exist "
                    "in the approved database schema."
                ),
            )

            continue

        referenced_tables.add(table_name)

        physical_aliases[table_alias] = (
            table_name
        )

        physical_aliases[table_name] = (
            table_name
        )

    select_aliases = {
        str(alias.alias).lower()
        for alias in expression.find_all(exp.Alias)
        if alias.alias
    }

    all_cte_output_columns: set[str] = set()

    for output_columns in cte_outputs.values():
        all_cte_output_columns.update(
            output_columns
        )

    for column in expression.find_all(exp.Column):
        if isinstance(column.this, exp.Star):
            continue

        column_name = str(
            column.name
        ).lower()

        qualifier = str(
            column.table or ""
        ).lower()

        referenced_columns.add(
            column.sql(
                dialect="postgres",
                comments=False,
            )
        )

        if qualifier:
            if qualifier in physical_aliases:
                physical_table = physical_aliases[
                    qualifier
                ]

                if (
                    column_name
                    not in schema_columns[
                        physical_table
                    ]
                ):
                    _add_issue(
                        issues,
                        code="unknown_column",
                        severity="error",
                        message=(
                            f"Column '{qualifier}."
                            f"{column_name}' does not "
                            "exist."
                        ),
                    )

                continue

            if qualifier in cte_aliases:
                known_outputs = cte_aliases[
                    qualifier
                ]

                if (
                    known_outputs
                    and column_name
                    not in known_outputs
                ):
                    _add_issue(
                        issues,
                        code="unknown_cte_column",
                        severity="error",
                        message=(
                            f"CTE column '{qualifier}."
                            f"{column_name}' was not "
                            "projected by the CTE."
                        ),
                    )

                continue

            _add_issue(
                issues,
                code="unknown_table_alias",
                severity="error",
                message=(
                    f"Unknown table or CTE qualifier "
                    f"'{qualifier}'."
                ),
            )

            continue

        if column_name in select_aliases:
            continue

        physical_matches = [
            table_name
            for table_name in referenced_tables
            if (
                column_name
                in schema_columns[table_name]
            )
        ]

        cte_match = (
            column_name
            in all_cte_output_columns
        )

        if not physical_matches and not cte_match:
            _add_issue(
                issues,
                code="unknown_column",
                severity="error",
                message=(
                    f"Column '{column_name}' does not "
                    "exist in any referenced table."
                ),
            )

            continue

        if (
            len(physical_matches) > 1
            and not cte_match
        ):
            _add_issue(
                issues,
                code="ambiguous_column",
                severity="error",
                message=(
                    f"Unqualified column '{column_name}' "
                    "exists in multiple referenced tables."
                ),
            )

    return (
        sorted(referenced_tables),
        sorted(referenced_columns),
    )


def _read_outer_limit(
    expression: exp.Expression,
) -> tuple[int | None, bool]:
    """Read a literal outer LIMIT value."""

    limit_node = expression.args.get(
        "limit"
    )

    if limit_node is None:
        return None, False

    limit_expression = getattr(
        limit_node,
        "expression",
        None,
    )

    if not isinstance(
        limit_expression,
        exp.Literal,
    ):
        return None, True

    try:
        return int(
            str(limit_expression.this)
        ), True

    except ValueError:
        return None, True


def _enforce_row_limit(
    expression: exp.Expression,
    issues: list[GuardrailIssue],
) -> tuple[
    exp.Expression | None,
    bool,
    int | None,
]:
    """Add or cap the outer query LIMIT."""

    current_limit, limit_exists = (
        _read_outer_limit(expression)
    )

    if limit_exists and current_limit is None:
        _add_issue(
            issues,
            code="dynamic_limit_not_allowed",
            severity="error",
            message=(
                "LIMIT must be a fixed non-negative "
                "integer."
            ),
        )

        return None, False, None

    if current_limit is not None and current_limit < 0:
        _add_issue(
            issues,
            code="negative_limit",
            severity="error",
            message=(
                "LIMIT cannot be negative."
            ),
        )

        return None, False, None

    if not limit_exists:
        _add_issue(
            issues,
            code="limit_added",
            severity="info",
            message=(
                f"LIMIT {settings.max_result_rows} "
                "was added automatically."
            ),
        )

        return (
            expression.limit(
                settings.max_result_rows,
                copy=True,
            ),
            True,
            settings.max_result_rows,
        )

    if (
        current_limit is not None
        and current_limit
        > settings.max_result_rows
    ):
        _add_issue(
            issues,
            code="limit_capped",
            severity="warning",
            message=(
                f"LIMIT {current_limit} exceeded the "
                f"maximum and was capped at "
                f"{settings.max_result_rows}."
            ),
        )

        return (
            expression.limit(
                settings.max_result_rows,
                copy=True,
            ),
            True,
            settings.max_result_rows,
        )

    return (
        expression.copy(),
        False,
        current_limit,
    )


def _create_response(
    *,
    original_sql: str,
    issues: list[GuardrailIssue],
    statement_type: str | None = None,
    normalized_sql: str | None = None,
    safe_sql: str | None = None,
    modified: bool = False,
    tables_referenced: list[str] | None = None,
    columns_referenced: list[str] | None = None,
    subquery_depth: int = 0,
    limit_applied: bool = False,
    effective_limit: int | None = None,
) -> SQLValidationResponse:
    """Construct and audit one validation result."""

    allowed = not _has_error(issues)

    response = SQLValidationResponse(
        original_sql=original_sql,
        allowed=allowed,
        modified=modified,
        statement_type=statement_type,
        normalized_sql=normalized_sql,
        safe_sql=safe_sql if allowed else None,
        tables_referenced=(
            tables_referenced or []
        ),
        columns_referenced=(
            columns_referenced or []
        ),
        subquery_depth=subquery_depth,
        limit_applied=limit_applied,
        effective_limit=effective_limit,
        issues=issues,
    )

    log_guardrail_decision(
        sql=original_sql,
        allowed=response.allowed,
        issue_codes=[
            issue.code
            for issue in issues
        ],
        metadata={
            "statement_type": statement_type,
            "tables": response.tables_referenced,
            "subquery_depth": subquery_depth,
            "effective_limit": effective_limit,
        },
    )

    return response


def validate_sql(
    request: SQLValidationRequest,
) -> SQLValidationResponse:
    """
    Parse and statically validate untrusted generated SQL.

    No SQL is executed by this function.
    """

    original_sql = request.sql.strip()
    issues: list[GuardrailIssue] = []

    if len(original_sql) > settings.max_sql_length:
        _add_issue(
            issues,
            code="sql_too_long",
            severity="error",
            message=(
                f"SQL exceeds the maximum length of "
                f"{settings.max_sql_length} characters."
            ),
        )

        return _create_response(
            original_sql=original_sql,
            issues=issues,
        )

    if (
        settings.block_sql_comments
        and _contains_sql_comment(original_sql)
    ):
        _add_issue(
            issues,
            code="sql_comments_not_allowed",
            severity="error",
            message=(
                "SQL comments are not allowed in "
                "generated queries."
            ),
        )

    try:
        parsed_statements = [
            statement
            for statement in sqlglot.parse(
                original_sql,
                read="postgres",
            )
            if statement is not None
        ]

    except ParseError as error:
        _add_issue(
            issues,
            code="sql_parse_error",
            severity="error",
            message=(
                f"SQL could not be parsed: {error}."
            ),
        )

        return _create_response(
            original_sql=original_sql,
            issues=issues,
        )

    if len(parsed_statements) != 1:
        _add_issue(
            issues,
            code="multiple_statements",
            severity="error",
            message=(
                "Exactly one SQL statement is allowed."
            ),
        )

        return _create_response(
            original_sql=original_sql,
            issues=issues,
        )

    expression = parsed_statements[0]

    statement_type = (
        type(expression).__name__.upper()
    )

    _validate_statement_type(
        expression,
        issues,
    )

    _validate_blocked_operations(
        expression,
        issues,
    )

    _validate_functions(
        expression,
        issues,
    )

    subquery_depth = (
        _calculate_subquery_depth(
            expression
        )
    )

    if (
        subquery_depth
        > settings.max_subquery_depth
    ):
        _add_issue(
            issues,
            code="subquery_depth_exceeded",
            severity="error",
            message=(
                f"Subquery depth {subquery_depth} "
                f"exceeds the maximum of "
                f"{settings.max_subquery_depth}."
            ),
        )

    schema = introspect_database_schema()

    (
        tables_referenced,
        columns_referenced,
    ) = _validate_schema_references(
        expression=expression,
        schema=schema,
        issues=issues,
    )

    normalized_sql = _render_sql(
        expression
    )

    if _has_error(issues):
        return _create_response(
            original_sql=original_sql,
            issues=issues,
            statement_type=statement_type,
            normalized_sql=normalized_sql,
            tables_referenced=tables_referenced,
            columns_referenced=columns_referenced,
            subquery_depth=subquery_depth,
        )

    (
        safe_expression,
        modified,
        effective_limit,
    ) = _enforce_row_limit(
        expression,
        issues,
    )

    if safe_expression is None or _has_error(issues):
        return _create_response(
            original_sql=original_sql,
            issues=issues,
            statement_type=statement_type,
            normalized_sql=normalized_sql,
            tables_referenced=tables_referenced,
            columns_referenced=columns_referenced,
            subquery_depth=subquery_depth,
        )

    safe_sql = _render_sql(
        safe_expression
    )

    return _create_response(
        original_sql=original_sql,
        issues=issues,
        statement_type=statement_type,
        normalized_sql=normalized_sql,
        safe_sql=safe_sql,
        modified=modified,
        tables_referenced=tables_referenced,
        columns_referenced=columns_referenced,
        subquery_depth=subquery_depth,
        limit_applied=modified,
        effective_limit=effective_limit,
    )