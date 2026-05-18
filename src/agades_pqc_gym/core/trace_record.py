from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.utils.hashing import stable_sha256

TraceRecordSchema = Literal["agades.pqc.trace_record.v1"]
TRACE_RECORD_SCHEMA: TraceRecordSchema = "agades.pqc.trace_record.v1"


class TraceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: TraceRecordSchema = TRACE_RECORD_SCHEMA
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
            "schema_version": TRACE_RECORD_SCHEMA,
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
