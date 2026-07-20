import json
from functools import lru_cache
from time import perf_counter
from groq import Groq
from pydantic import ValidationError

from backend.app.core.config import get_settings
from backend.app.core.exceptions import (
    LLMConfigurationError,
    LLMResponseError,
)
from backend.app.schemas.prompt_context import PromptPreviewRequest
from backend.app.schemas.sql_generation import (
    SQLGenerationPayload,
    SQLGenerationRequest,
    SQLGenerationResponse,
    TokenUsage,
)
from backend.app.services.prompt_builder import build_prompt_preview
from backend.app.services.structured_output_schema import (
    SQL_GENERATION_JSON_SCHEMA,
)


settings = get_settings()


@lru_cache(maxsize=1)
def get_groq_client() -> Groq:
    """
    Create and cache the Groq client.

    The client is created only after confirming that an API key exists.
    """

    if not settings.groq_api_key.strip():
        raise LLMConfigurationError(
            "GROQ_API_KEY is missing from the environment."
        )

    return Groq(
        api_key=settings.groq_api_key,
        timeout=settings.groq_timeout_seconds,
        max_retries=settings.groq_max_retries,
    )


def parse_generation_content(
    content: str,
) -> SQLGenerationPayload:
    """
    Parse and validate the JSON content returned by Groq.
    """

    if not content or not content.strip():
        raise LLMResponseError(
            "Groq returned an empty response."
        )

    try:
        raw_payload = json.loads(content)

    except json.JSONDecodeError as error:
        raise LLMResponseError(
            "Groq returned invalid JSON."
        ) from error

    try:
        return SQLGenerationPayload.model_validate(raw_payload)

    except ValidationError as error:
        raise LLMResponseError(
            "Groq returned JSON that failed application validation."
        ) from error


def _get_usage(
    completion: object,
) -> TokenUsage:
    """
    Extract token counts without failing when usage is unavailable.
    """

    usage = getattr(completion, "usage", None)

    if usage is None:
        return TokenUsage()

    return TokenUsage(
        prompt_tokens=getattr(
            usage,
            "prompt_tokens",
            0,
        )
        or 0,
        completion_tokens=getattr(
            usage,
            "completion_tokens",
            0,
        )
        or 0,
        total_tokens=getattr(
            usage,
            "total_tokens",
            0,
        )
        or 0,
    )


def _build_local_clarification_response(
    request: SQLGenerationRequest,
    selected_tables: list[str],
    clarification_message: str | None,
    clarification_options: list[str],
) -> SQLGenerationResponse:
    """
    Return clarification without calling Groq.

    This reduces cost and prevents the model from guessing when the
    local ambiguity detector already identified the problem.
    """

    options_text = " ".join(
        clarification_options
    ).strip()

    clarification_question = (
        clarification_message
        or "Please clarify the intended interpretation."
    )

    if options_text:
        clarification_question = (
            f"{clarification_question} {options_text}"
        )

    return SQLGenerationResponse(
        question=request.question,
        sql=None,
        explanation=(
            "The question requires clarification before SQL can "
            "be generated safely."
        ),
        tables_used=[],
        columns_used=[],
        confidence=0.0,
        requires_clarification=True,
        clarification_question=clarification_question,
        selected_tables=selected_tables,
        provider="local",
        model=None,
        latency_ms=0.0,
        token_usage=TokenUsage(),
    )


def generate_sql(
    request: SQLGenerationRequest,
) -> SQLGenerationResponse:
    """
    Generate structured PostgreSQL through Groq.

    This function does not execute the generated SQL.
    """

    prompt_preview = build_prompt_preview(
        PromptPreviewRequest(
            question=request.question,
            max_tables=request.max_tables,
            max_examples=request.max_examples,
        )
    )

    selected_tables = [
        table.name
        for table in prompt_preview.selected_tables
    ]

    if prompt_preview.requires_clarification:
        return _build_local_clarification_response(
            request=request,
            selected_tables=selected_tables,
            clarification_message=(
                prompt_preview.clarification_message
            ),
            clarification_options=(
                prompt_preview.clarification_options
            ),
        )

    client = get_groq_client()

    started_at = perf_counter()

    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise PostgreSQL Text-to-SQL "
                    "engine. Follow the supplied schema and business "
                    "definitions. Never invent schema objects."
                ),
            },
            {
                "role": "user",
                "content": prompt_preview.prompt,
            },
        ],
        temperature=settings.groq_temperature,
        max_completion_tokens=(
            settings.groq_max_completion_tokens
        ),
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "safequery_sql_generation",
                "strict": True,
                "schema": SQL_GENERATION_JSON_SCHEMA,
            },
        },
    )

    latency_ms = round(
        (perf_counter() - started_at) * 1000,
        2,
    )

    if not completion.choices:
        raise LLMResponseError(
            "Groq returned no completion choices."
        )

    message_content = completion.choices[0].message.content

    payload = parse_generation_content(
        message_content or ""
    )

    return SQLGenerationResponse(
        question=request.question,
        sql=payload.sql,
        explanation=payload.explanation,
        tables_used=payload.tables_used,
        columns_used=payload.columns_used,
        confidence=payload.confidence,
        requires_clarification=(
            payload.requires_clarification
        ),
        clarification_question=(
            payload.clarification_question
        ),
        selected_tables=selected_tables,
        provider="groq",
        model=getattr(
            completion,
            "model",
            settings.groq_model,
        ),
        latency_ms=latency_ms,
        token_usage=_get_usage(completion),
    )