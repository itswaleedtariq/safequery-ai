from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from backend.app.schemas.prompt_context import PromptPreviewRequest


class SQLGenerationRequest(PromptPreviewRequest):
    """Request used to generate SQL from a business question."""


class SQLGenerationPayload(BaseModel):
    """Structured content returned by the language model."""

    model_config = ConfigDict(extra="forbid")

    sql: str | None

    explanation: str = Field(
        min_length=1,
        max_length=2000,
    )

    tables_used: list[str]

    columns_used: list[str]

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    requires_clarification: bool

    clarification_question: str | None

    @model_validator(mode="after")
    def validate_sql_or_clarification(
        self,
    ) -> "SQLGenerationPayload":
        """
        Ensure clarification responses and SQL responses are consistent.
        """

        if self.requires_clarification:
            if self.sql is not None:
                raise ValueError(
                    "SQL must be null when clarification is required."
                )

            if not self.clarification_question:
                raise ValueError(
                    "A clarification question is required."
                )

            return self

        if self.sql is None or not self.sql.strip():
            raise ValueError(
                "SQL is required when clarification is not needed."
            )

        if self.clarification_question is not None:
            raise ValueError(
                "Clarification question must be null when SQL is returned."
            )

        return self


class TokenUsage(BaseModel):
    """Token counts reported by Groq."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class SQLGenerationResponse(BaseModel):
    """Complete API response for SQL generation."""

    question: str

    sql: str | None
    explanation: str

    tables_used: list[str] = Field(default_factory=list)
    columns_used: list[str] = Field(default_factory=list)

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    requires_clarification: bool
    clarification_question: str | None = None

    selected_tables: list[str] = Field(default_factory=list)

    provider: Literal["groq", "local"]
    model: str | None = None

    latency_ms: float = Field(ge=0.0)
    token_usage: TokenUsage