from typing import Any

from pydantic import BaseModel, Field


class AgentAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class AgentSource(BaseModel):
    label: str
    endpoint: str


class AgentResponse(BaseModel):
    question: str
    intent: str
    answer: str
    generated_sql: str | None = Field(default=None, alias="generatedSql")
    columns: list[str] = []
    rows: list[dict[str, Any]] = []
    row_count: int = Field(default=0, alias="rowCount")
    error: str | None = None
    sources: list[AgentSource] = []
    data: list[dict[str, Any]] | dict[str, Any] | None = None
    suggestions: list[str] = []

    model_config = {"populate_by_name": True}
