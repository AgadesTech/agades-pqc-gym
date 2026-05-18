from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.target import TargetSpec
from agades_pqc_gym.core.trace_record import TraceRecord
from agades_pqc_gym.evolution.archive import EvolutionArchive


class HeldoutCandidatePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    parent_id: str
    generation: int = Field(ge=0)
    mutation_summary: str
    attack_plan: AttackPlan


def build_heldout_candidate_plans(
    archive: EvolutionArchive,
    source_records: Iterable[TraceRecord],
    heldout_targets: Sequence[TargetSpec],
) -> list[HeldoutCandidatePlan]:
    source_by_candidate = _source_records_by_candidate(source_records)
    candidates: list[HeldoutCandidatePlan] = []

    for elite in archive.elites:
        source_record = source_by_candidate.get(elite.candidate_id)
        if source_record is None:
            raise ValueError(
                f"Archive elite {elite.candidate_id} is missing from source trace."
            )
        for target_index, target in enumerate(heldout_targets):
            attack_plan = rebase_attack_plan_for_heldout(
                source_record.attack_plan,
                target,
            )
            candidates.append(
                HeldoutCandidatePlan(
                    candidate_id=(
                        f"{elite.candidate_id}-heldout-"
                        f"{_safe_identifier(target.name)}-{target_index}"
                    ),
                    parent_id=elite.candidate_id,
                    generation=elite.generation + 1,
                    mutation_summary=f"held-out re-evaluation on {target.name}",
                    attack_plan=attack_plan,
                )
            )

    return candidates


def rebase_attack_plan_for_heldout(
    source_plan: AttackPlan,
    heldout_target: TargetSpec,
) -> AttackPlan:
    _validate_rebase_boundary(source_plan, heldout_target)
    data = source_plan.model_dump(mode="json")
    data["attack_plan_id"] = (
        f"{source_plan.attack_plan_id}__heldout__"
        f"{_safe_identifier(heldout_target.name)}"
    )
    data["target"] = heldout_target.model_dump(mode="json")
    data["metadata"] = {
        **data["metadata"],
        "public": False,
        "notes": _heldout_notes(source_plan, heldout_target),
    }
    return AttackPlan.model_validate(data)


def _source_records_by_candidate(
    records: Iterable[TraceRecord],
) -> dict[str, TraceRecord]:
    by_candidate: dict[str, TraceRecord] = {}
    for record in records:
        if record.candidate_id in by_candidate:
            raise ValueError(
                f"Source trace contains duplicate candidate id {record.candidate_id}."
            )
        by_candidate[record.candidate_id] = record
    return by_candidate


def _validate_rebase_boundary(
    source_plan: AttackPlan,
    heldout_target: TargetSpec,
) -> None:
    if source_plan.target.family is not heldout_target.family:
        raise ValueError(
            "Held-out re-evaluation requires the same target family: "
            f"{source_plan.target.family.value} != {heldout_target.family.value}."
        )
    if _has_pre_evaluation_claim(source_plan.claims.model_dump(mode="json")):
        raise ValueError(
            "Held-out re-evaluation refuses AttackPlans with pre-evaluation claims."
        )
    if (
        source_plan.constraints.require_reproducibility_on_downscaled_instances
        or source_plan.constraints.downscaled_reproduction_fixture is not None
    ):
        raise ValueError(
            "Held-out re-evaluation refuses target-specific reproduction "
            "constraints."
        )


def _has_pre_evaluation_claim(claims: dict[str, Any]) -> bool:
    return any(
        claims.get(key) is not None
        for key in (
            "estimated_time_bits",
            "estimated_memory_bits",
            "success_probability",
            "source",
        )
    ) or claims.get("external_claim") is True


def _heldout_notes(source_plan: AttackPlan, heldout_target: TargetSpec) -> str:
    source_notes = source_plan.metadata.notes.strip()
    prefix = (
        f"Private held-out re-evaluation of {source_plan.attack_plan_id} "
        f"on {heldout_target.name}. Not a security claim."
    )
    if not source_notes:
        return prefix
    return f"{prefix} Source notes: {source_notes}"


def _safe_identifier(value: str) -> str:
    safe = "".join(
        character if character.isalnum() or character in {"_", "-"} else "_"
        for character in value
    )
    return safe.strip("_") or "target"
