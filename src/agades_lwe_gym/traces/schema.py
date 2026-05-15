from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agades_lwe_gym.dsl.schema import AttackPlan
from agades_lwe_gym.utils.hashing import stable_sha256


class TraceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str
    run_id: str
    candidate_id: str
    parent_id: str | None
    generation: int = Field(ge=0)
    mutation_summary: str
    attack_plan: AttackPlan
    evaluation: dict[str, Any]
    accepted: bool
    public_release_ok: bool
    redaction_reason: str | None
    created_at: str

    @classmethod
    def from_evaluation(
        cls,
        *,
        run_id: str,
        candidate_id: str,
        parent_id: str | None,
        generation: int,
        mutation_summary: str,
        attack_plan: AttackPlan,
        evaluation: dict[str, Any],
        accepted: bool,
        public_release_ok: bool,
        redaction_reason: str | None,
    ) -> TraceRecord:
        created_at = datetime.now(UTC).isoformat()
        trace_material = {
            "run_id": run_id,
            "candidate_id": candidate_id,
            "parent_id": parent_id,
            "generation": generation,
            "attack_plan": attack_plan.model_dump(mode="json"),
            "evaluation": evaluation,
            "created_at": created_at,
        }
        return cls(
            trace_id=stable_sha256(trace_material),
            run_id=run_id,
            candidate_id=candidate_id,
            parent_id=parent_id,
            generation=generation,
            mutation_summary=mutation_summary,
            attack_plan=attack_plan,
            evaluation=evaluation,
            accepted=accepted,
            public_release_ok=public_release_ok,
            redaction_reason=redaction_reason,
            created_at=created_at,
        )

