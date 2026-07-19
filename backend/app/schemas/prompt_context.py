from pydantic import BaseModel, Field


class PromptPreviewRequest(BaseModel):
    """Input used to construct a schema-aware prompt."""

    question: str = Field(
        min_length=3,
        max_length=500,
        examples=[
            "Which five products generated the highest revenue?"
        ],
    )

    max_tables: int = Field(
        default=4,
        ge=1,
        le=8,
    )

    max_examples: int = Field(
        default=3,
        ge=0,
        le=5,
    )


class SelectedTable(BaseModel):
    """One table selected as relevant to the question."""

    name: str
    score: float
    reasons: list[str] = Field(default_factory=list)


class BusinessTermContext(BaseModel):
    """Business definition detected in a user question."""

    term: str
    definition: str
    tables: list[str] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)


class FewShotExample(BaseModel):
    """Verified question-to-SQL example."""

    id: str
    question: str
    sql: str
    tables: list[str] = Field(default_factory=list)


class PromptPreviewResponse(BaseModel):
    """Complete preview of the future LLM prompt."""

    question: str

    selected_tables: list[SelectedTable] = Field(
        default_factory=list
    )

    included_columns: dict[str, list[str]] = Field(
        default_factory=dict
    )

    selected_relationships: list[str] = Field(
        default_factory=list
    )

    business_terms: list[BusinessTermContext] = Field(
        default_factory=list
    )

    few_shot_examples: list[FewShotExample] = Field(
        default_factory=list
    )

    requires_clarification: bool = False
    clarification_message: str | None = None
    clarification_options: list[str] = Field(default_factory=list)

    prompt: str