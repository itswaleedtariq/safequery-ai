import json
import re
from collections import deque
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Any

from backend.app.schemas.database_schema import (
    DatabaseSchemaResponse,
    TableSchema,
)
from backend.app.schemas.prompt_context import (
    BusinessTermContext,
    FewShotExample,
    PromptPreviewRequest,
    PromptPreviewResponse,
    SelectedTable,
)
from backend.app.services.schema_introspection import (
    introspect_database_schema,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]

BUSINESS_GLOSSARY_PATH = (
    PROJECT_ROOT
    / "backend"
    / "app"
    / "data"
    / "business_glossary.json"
)

FEW_SHOT_EXAMPLES_PATH = (
    PROJECT_ROOT
    / "backend"
    / "app"
    / "data"
    / "few_shot_examples.json"
)

WORD_PATTERN = re.compile(r"[a-z0-9_]+")


@lru_cache(maxsize=1)
def _load_business_glossary() -> list[dict[str, Any]]:
    """Load machine-readable business definitions."""

    with BUSINESS_GLOSSARY_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


@lru_cache(maxsize=1)
def _load_few_shot_examples() -> list[dict[str, Any]]:
    """Load verified natural-language-to-SQL examples."""

    with FEW_SHOT_EXAMPLES_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def _singularize(token: str) -> str:
    """Apply simple singularization for schema matching."""

    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"

    if token.endswith("s") and not token.endswith("ss"):
        return token[:-1]

    return token


def _tokenize(text: str | None) -> set[str]:
    """Convert text into normalized matching tokens."""

    if not text:
        return set()

    raw_tokens = WORD_PATTERN.findall(text.lower())
    tokens: set[str] = set()

    for token in raw_tokens:
        tokens.add(token)
        tokens.add(_singularize(token))

        if "_" in token:
            for component in token.split("_"):
                tokens.add(component)
                tokens.add(_singularize(component))

    return tokens


def _contains_phrase(text: str, phrase: str) -> bool:
    """Check whether a complete phrase appears in text."""

    pattern = rf"\b{re.escape(phrase.lower())}\b"

    return re.search(pattern, text.lower()) is not None


def _detect_business_terms(
    question: str,
) -> list[BusinessTermContext]:
    """Find glossary terms mentioned by the user."""

    detected_terms: list[BusinessTermContext] = []

    for item in _load_business_glossary():
        phrases = [
            item["term"],
            *item.get("aliases", []),
        ]

        if any(
            _contains_phrase(question, phrase)
            for phrase in phrases
        ):
            detected_terms.append(
                BusinessTermContext(
                    term=item["term"],
                    definition=item["definition"],
                    tables=item.get("tables", []),
                    columns=item.get("columns", []),
                )
            )

    return detected_terms


def _score_table(
    table: TableSchema,
    question: str,
    question_tokens: set[str],
    business_terms: list[BusinessTermContext],
) -> tuple[float, list[str]]:
    """Calculate one table's relevance to the question."""

    score = 0.0
    reasons: list[str] = []

    table_tokens = _tokenize(table.name)
    table_overlap = question_tokens.intersection(table_tokens)

    if table_overlap:
        contribution = len(table_overlap) * 5.0
        score += contribution

        reasons.append(
            "Question matches table name: "
            + ", ".join(sorted(table_overlap))
        )

    comment_overlap = question_tokens.intersection(
        _tokenize(table.comment)
    )

    if comment_overlap:
        score += len(comment_overlap) * 0.5

        reasons.append(
            "Question matches table description."
        )

    for column in table.columns:
        column_overlap = question_tokens.intersection(
            _tokenize(column.name)
        )

        if column_overlap:
            score += len(column_overlap) * 2.0

            reasons.append(
                f"Question matches column {table.name}.{column.name}."
            )

        column_comment_overlap = question_tokens.intersection(
            _tokenize(column.comment)
        )

        if column_comment_overlap:
            score += len(column_comment_overlap) * 0.25

        for sample_value in column.sample_values:
            sample_text = str(sample_value).lower()

            if (
                sample_text
                and _contains_phrase(question, sample_text)
            ):
                score += 3.0

                reasons.append(
                    "Question matches sample value "
                    f"{table.name}.{column.name}={sample_value}."
                )

    for business_term in business_terms:
        if table.name in business_term.tables:
            score += 6.0

            reasons.append(
                f"Required by business term "
                f"'{business_term.term}'."
            )

        for qualified_column in business_term.columns:
            if qualified_column.startswith(f"{table.name}."):
                score += 1.0

    unique_reasons = list(dict.fromkeys(reasons))

    return score, unique_reasons


def _build_relationship_graph(
    schema: DatabaseSchemaResponse,
) -> dict[str, set[str]]:
    """Create an undirected graph of table relationships."""

    graph = {
        table.name: set()
        for table in schema.tables
    }

    for table in schema.tables:
        for foreign_key in table.foreign_keys:
            referred_table = foreign_key.referred_table

            if referred_table not in graph:
                continue

            graph[table.name].add(referred_table)
            graph[referred_table].add(table.name)

    return graph


def _find_shortest_path(
    graph: dict[str, set[str]],
    start: str,
    target: str,
) -> list[str]:
    """Find the shortest relationship path between two tables."""

    if start == target:
        return [start]

    queue: deque[list[str]] = deque([[start]])
    visited = {start}

    while queue:
        path = queue.popleft()
        current = path[-1]

        for neighbour in sorted(graph.get(current, set())):
            if neighbour in visited:
                continue

            next_path = [*path, neighbour]

            if neighbour == target:
                return next_path

            visited.add(neighbour)
            queue.append(next_path)

    return []


def _select_relevant_tables(
    schema: DatabaseSchemaResponse,
    question: str,
    business_terms: list[BusinessTermContext],
    max_tables: int,
) -> list[SelectedTable]:
    """Rank tables and include relationship bridge tables."""

    question_tokens = _tokenize(question)

    scored_tables: list[SelectedTable] = []

    for table in schema.tables:
        score, reasons = _score_table(
            table=table,
            question=question,
            question_tokens=question_tokens,
            business_terms=business_terms,
        )

        if score > 0:
            scored_tables.append(
                SelectedTable(
                    name=table.name,
                    score=round(score, 2),
                    reasons=reasons,
                )
            )

    scored_tables.sort(
        key=lambda item: (-item.score, item.name)
    )

    initially_selected = scored_tables[:max_tables]

    selected_names = {
        table.name
        for table in initially_selected
    }

    graph = _build_relationship_graph(schema)

    main_tables = [
        table.name
        for table in initially_selected[:3]
    ]

    bridge_tables: list[SelectedTable] = []

    for start, target in combinations(main_tables, 2):
        path = _find_shortest_path(
            graph=graph,
            start=start,
            target=target,
        )

        for table_name in path:
            if table_name in selected_names:
                continue

            selected_names.add(table_name)

            bridge_tables.append(
                SelectedTable(
                    name=table_name,
                    score=0.0,
                    reasons=[
                        "Added as a relationship bridge between "
                        "other relevant tables."
                    ],
                )
            )

    return [
        *initially_selected,
        *bridge_tables,
    ]


def _select_few_shot_examples(
    question: str,
    selected_table_names: set[str],
    max_examples: int,
) -> list[FewShotExample]:
    """Select examples similar to the current question."""

    if max_examples == 0:
        return []

    question_tokens = _tokenize(question)
    scored_examples: list[
        tuple[float, dict[str, Any]]
    ] = []

    for example in _load_few_shot_examples():
        example_tokens = _tokenize(example["question"])

        token_score = len(
            question_tokens.intersection(example_tokens)
        )

        shared_tables = selected_table_names.intersection(
            set(example.get("tables", []))
        )

        table_score = len(shared_tables) * 3

        total_score = token_score + table_score

        if total_score > 0:
            scored_examples.append(
                (
                    float(total_score),
                    example,
                )
            )

    scored_examples.sort(
        key=lambda item: (
            -item[0],
            item[1]["id"],
        )
    )

    return [
        FewShotExample(
            id=example["id"],
            question=example["question"],
            sql=example["sql"],
            tables=example.get("tables", []),
        )
        for _, example in scored_examples[:max_examples]
    ]


def _get_selected_relationships(
    schema: DatabaseSchemaResponse,
    selected_table_names: set[str],
) -> list[str]:
    """Return foreign keys connecting selected tables."""

    relationships: list[str] = []

    for table in schema.tables:
        if table.name not in selected_table_names:
            continue

        for foreign_key in table.foreign_keys:
            if (
                foreign_key.referred_table
                not in selected_table_names
            ):
                continue

            local_columns = ", ".join(
                foreign_key.constrained_columns
            )

            referred_columns = ", ".join(
                foreign_key.referred_columns
            )

            relationships.append(
                f"{table.name}.{local_columns} -> "
                f"{foreign_key.referred_table}."
                f"{referred_columns}"
            )

    return sorted(set(relationships))


def _detect_ambiguity(
    question: str,
    selected_tables: list[SelectedTable],
) -> tuple[bool, str | None, list[str]]:
    """Detect questions that require clarification."""

    lowered_question = question.lower()
    question_tokens = _tokenize(question)

    if not selected_tables:
        return (
            True,
            (
                "The question could not be mapped to the available "
                "e-commerce database."
            ),
            [
                "Ask about customers.",
                "Ask about products or categories.",
                "Ask about orders, revenue or payments.",
            ],
        )

    city_qualifiers = {
        "customer",
        "home",
        "shipping",
        "delivery",
        "destination",
    }

    if (
        "city" in question_tokens
        and not question_tokens.intersection(city_qualifiers)
    ):
        return (
            True,
            (
                "The word 'city' is ambiguous because the database "
                "contains both customer city and shipping city."
            ),
            [
                "Use customer city from customers.city.",
                "Use shipping city from orders.shipping_city.",
            ],
        )

    price_qualifiers = {
        "current",
        "catalog",
        "historical",
        "sale",
        "sold",
        "order",
    }

    if (
        "price" in question_tokens
        and not question_tokens.intersection(price_qualifiers)
        and "price at order time" not in lowered_question
    ):
        return (
            True,
            (
                "The word 'price' is ambiguous because the database "
                "contains current catalog price and historical sale "
                "price."
            ),
            [
                "Use current catalog price from products.price.",
                (
                    "Use historical sale price from "
                    "order_items.unit_price."
                ),
            ],
        )

    return False, None, []


def _build_schema_context(
    schema: DatabaseSchemaResponse,
    selected_table_names: set[str],
) -> tuple[str, dict[str, list[str]]]:
    """Format selected schema metadata for an LLM prompt."""

    context_lines: list[str] = []
    included_columns: dict[str, list[str]] = {}

    table_lookup = {
        table.name: table
        for table in schema.tables
    }

    for table_name in sorted(selected_table_names):
        table = table_lookup[table_name]

        included_columns[table.name] = [
            column.name
            for column in table.columns
        ]

        context_lines.append(
            f"TABLE {table.name}"
        )

        if table.comment:
            context_lines.append(
                f"Description: {table.comment}"
            )

        foreign_key_lookup: dict[str, str] = {}

        for foreign_key in table.foreign_keys:
            for local_column, referred_column in zip(
                foreign_key.constrained_columns,
                foreign_key.referred_columns,
                strict=False,
            ):
                foreign_key_lookup[local_column] = (
                    f"{foreign_key.referred_table}."
                    f"{referred_column}"
                )

        for column in table.columns:
            attributes: list[str] = []

            if column.primary_key:
                attributes.append("PRIMARY KEY")

            if not column.nullable:
                attributes.append("NOT NULL")

            if column.name in foreign_key_lookup:
                attributes.append(
                    "FOREIGN KEY -> "
                    + foreign_key_lookup[column.name]
                )

            if column.computed_expression:
                attributes.append(
                    "COMPUTED: "
                    + column.computed_expression
                )

            attribute_text = ""

            if attributes:
                attribute_text = " [" + "; ".join(attributes) + "]"

            context_lines.append(
                f"- {column.name}: "
                f"{column.data_type}"
                f"{attribute_text}"
            )

            if column.comment:
                context_lines.append(
                    f"  Description: {column.comment}"
                )

            if column.sample_values:
                sample_values = ", ".join(
                    str(value)
                    for value in column.sample_values
                )

                context_lines.append(
                    f"  Sample values: {sample_values}"
                )

        context_lines.append("")

    return "\n".join(context_lines).strip(), included_columns


def _build_prompt_text(
    question: str,
    schema_context: str,
    relationships: list[str],
    business_terms: list[BusinessTermContext],
    few_shot_examples: list[FewShotExample],
    requires_clarification: bool,
    clarification_message: str | None,
    clarification_options: list[str],
) -> str:
    """Construct the final prompt that Milestone 5 will send."""

    relationship_context = "\n".join(
        f"- {relationship}"
        for relationship in relationships
    )

    if not relationship_context:
        relationship_context = "- No cross-table relationship required."

    business_context = "\n".join(
        f"- {term.term}: {term.definition}"
        for term in business_terms
    )

    if not business_context:
        business_context = "- No additional business term detected."

    example_blocks: list[str] = []

    for index, example in enumerate(
        few_shot_examples,
        start=1,
    ):
        example_blocks.append(
            "\n".join(
                [
                    f"Example {index}",
                    f"Question: {example.question}",
                    f"SQL: {example.sql}",
                ]
            )
        )

    examples_context = "\n\n".join(example_blocks)

    if not examples_context:
        examples_context = "No few-shot example selected."

    clarification_context = "No clarification is currently required."

    if requires_clarification:
        option_text = "\n".join(
            f"- {option}"
            for option in clarification_options
        )

        clarification_context = (
            f"{clarification_message}\n"
            f"Possible clarifications:\n{option_text}"
        )

    output_contract = """
{
  "sql": "A single PostgreSQL SELECT query or null",
  "explanation": "Plain-English explanation",
  "tables_used": ["table_name"],
  "columns_used": ["table.column"],
  "confidence": 0.0,
  "requires_clarification": false,
  "clarification_question": null
}
""".strip()

    return f"""
You are a PostgreSQL Text-to-SQL specialist.

Your job is to translate the user's business question into one safe,
read-only PostgreSQL query.

RULES:
1. Use only the tables and columns included in the provided schema.
2. Never invent a table, column, relationship or categorical value.
3. Produce only one SELECT statement or one WITH ... SELECT statement.
4. Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE or TRUNCATE.
5. Use explicit JOIN conditions based on the provided relationships.
6. Follow the provided business definitions exactly.
7. Use historical order_items.unit_price or line_total for sales
   calculations instead of the current products.price.
8. Exclude pending and cancelled orders from revenue.
9. If the question is ambiguous, do not guess. Return a clarification
   request and set sql to null.
10. Return structured JSON matching the required output contract.

DATABASE:
{schema_context}

RELATIONSHIPS:
{relationship_context}

BUSINESS DEFINITIONS:
{business_context}

CLARIFICATION ANALYSIS:
{clarification_context}

VERIFIED EXAMPLES:
{examples_context}

REQUIRED OUTPUT CONTRACT:
{output_contract}

USER QUESTION:
{question}
""".strip()


def build_prompt_preview(
    request: PromptPreviewRequest,
) -> PromptPreviewResponse:
    """Build complete schema-aware context without calling an LLM."""

    schema = introspect_database_schema()

    business_terms = _detect_business_terms(
        request.question
    )

    selected_tables = _select_relevant_tables(
        schema=schema,
        question=request.question,
        business_terms=business_terms,
        max_tables=request.max_tables,
    )

    selected_table_names = {
        table.name
        for table in selected_tables
    }

    relationships = _get_selected_relationships(
        schema=schema,
        selected_table_names=selected_table_names,
    )

    few_shot_examples = _select_few_shot_examples(
        question=request.question,
        selected_table_names=selected_table_names,
        max_examples=request.max_examples,
    )

    (
        requires_clarification,
        clarification_message,
        clarification_options,
    ) = _detect_ambiguity(
        question=request.question,
        selected_tables=selected_tables,
    )

    schema_context, included_columns = _build_schema_context(
        schema=schema,
        selected_table_names=selected_table_names,
    )

    prompt = _build_prompt_text(
        question=request.question,
        schema_context=schema_context,
        relationships=relationships,
        business_terms=business_terms,
        few_shot_examples=few_shot_examples,
        requires_clarification=requires_clarification,
        clarification_message=clarification_message,
        clarification_options=clarification_options,
    )

    return PromptPreviewResponse(
        question=request.question,
        selected_tables=selected_tables,
        included_columns=included_columns,
        selected_relationships=relationships,
        business_terms=business_terms,
        few_shot_examples=few_shot_examples,
        requires_clarification=requires_clarification,
        clarification_message=clarification_message,
        clarification_options=clarification_options,
        prompt=prompt,
    )