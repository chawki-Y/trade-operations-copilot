from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class QueryResponse(BaseModel):
    question: str
    answer: str
    intent: str
    generated_sql: str | None = Field(default=None, alias="generatedSql")
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int = Field(alias="rowCount")
    error: str | None = None

    model_config = {"populate_by_name": True}


class HistoryItem(BaseModel):
    id: int
    question: str
    intent: str
    generated_sql: str | None
    answer: str
    row_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TableInfo(BaseModel):
    name: str
    columns: list[str]
    description: str


class SchemaResponse(BaseModel):
    tables: list[TableInfo]
    schema_context: str
