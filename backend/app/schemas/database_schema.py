from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ColumnSchema(BaseModel):
    """Metadata for one PostgreSQL column."""

    name: str
    data_type: str
    nullable: bool
    default: str | None = None
    primary_key: bool = False
    comment: str | None = None
    computed_expression: str | None = None
    sample_values: list[Any] = Field(default_factory=list)


class ForeignKeySchema(BaseModel):
    """Metadata for one foreign-key relationship."""

    name: str | None = None
    constrained_columns: list[str] = Field(default_factory=list)

    referred_schema: str | None = None
    referred_table: str
    referred_columns: list[str] = Field(default_factory=list)

    on_update: str | None = None
    on_delete: str | None = None


class IndexSchema(BaseModel):
    """Metadata for one database index."""

    name: str | None = None
    column_names: list[str] = Field(default_factory=list)
    unique: bool = False


class TableSchema(BaseModel):
    """Complete metadata for one database table."""

    name: str
    comment: str | None = None
    primary_key_columns: list[str] = Field(default_factory=list)
    columns: list[ColumnSchema] = Field(default_factory=list)
    foreign_keys: list[ForeignKeySchema] = Field(default_factory=list)
    indexes: list[IndexSchema] = Field(default_factory=list)


class DatabaseSchemaResponse(BaseModel):
    """Top-level response for GET /v1/schema."""

    database_name: str
    schema_name: str
    generated_at: datetime
    table_count: int
    tables: list[TableSchema] = Field(default_factory=list)