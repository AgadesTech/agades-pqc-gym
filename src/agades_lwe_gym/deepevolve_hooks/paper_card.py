from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PaperCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    authors: list[str]
    year: int = Field(gt=1900)
    url: str
    family: str
    relevance: str
    key_ideas: list[str] = Field(default_factory=list)
    operators_suggested: list[str] = Field(default_factory=list)
    implementation_status: str
    risk: str

