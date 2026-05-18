from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
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


def load_paper_card(path: Path) -> PaperCard:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"paper card must be a mapping: {path}")
    return PaperCard.model_validate(_string_keyed_mapping(raw))


def load_paper_cards(directory: Path) -> list[PaperCard]:
    return [load_paper_card(path) for path in sorted(directory.glob("*.yaml"))]


def _string_keyed_mapping(raw: dict[Any, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in raw.items()}
