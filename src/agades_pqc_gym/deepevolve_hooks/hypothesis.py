from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HypothesisProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str
    source_papers: list[str]
    target_family: str
    operator: str
    claim: str
    implementation_plan: str
    review_required: bool = True

