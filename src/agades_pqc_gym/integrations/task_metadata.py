from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agades_pqc_gym.core.attack_plan import AttackPlan

TASK_METADATA_SCHEMA = "agades.pqc.task_metadata.v6"


class TaskMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    source_path: str | None
    seed_attack_plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    attack_plan_id: str
    target_family: str
    target_name: str
    support_level: str
    operator_types: list[str]
    operator_params: list[dict[str, Any]]
    operator_assumptions: list[list[str]]
    requires_reproducibility: bool
    public: bool
    seed_accepted: bool
    seed_evaluation_status: str
    seed_estimator_name: str | None
    seed_reproduction_attempted: bool
    seed_reproduction_status: str
    seed_reproduction_success: bool | None
    seed_reward: float


def task_metadata_for_plan(
    plan: AttackPlan,
    *,
    source_path: str | None = None,
    seed_attack_plan_json: str | None = None,
) -> dict[str, Any]:
    seed_result = _verify_seed_plan(plan)
    seed_accepted = seed_result["accepted"] is True
    seed_reproduction = seed_result["reproduction"]
    seed_estimator = seed_result["estimator"]
    return TaskMetadata(
        schema_version=TASK_METADATA_SCHEMA,
        source_path=source_path,
        seed_attack_plan_sha256=_seed_attack_plan_sha256(
            plan,
            seed_attack_plan_json=seed_attack_plan_json,
        ),
        attack_plan_id=plan.attack_plan_id,
        target_family=plan.target.family.value,
        target_name=plan.target.name,
        support_level=plan.target.support_level.value,
        operator_types=[operator.type for operator in plan.operators],
        operator_params=[dict(operator.params) for operator in plan.operators],
        operator_assumptions=[
            list(operator.assumptions) for operator in plan.operators
        ],
        requires_reproducibility=(
            plan.constraints.require_reproducibility_on_downscaled_instances
        ),
        public=plan.metadata.public,
        seed_accepted=seed_accepted,
        seed_evaluation_status=seed_result["evaluation_status"],
        seed_estimator_name=seed_estimator["name"],
        seed_reproduction_attempted=seed_reproduction["attempted"],
        seed_reproduction_status=seed_reproduction["status"],
        seed_reproduction_success=seed_reproduction["success"],
        seed_reward=1.0 if seed_accepted else 0.0,
    ).model_dump(mode="json")


def _seed_attack_plan_sha256(
    plan: AttackPlan,
    *,
    seed_attack_plan_json: str | None,
) -> str:
    source = (
        seed_attack_plan_json
        if seed_attack_plan_json is not None
        else plan.model_dump_json()
    )
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def normalize_task_metadata(
    value: Mapping[str, Any] | str | None,
) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return None
        if not isinstance(decoded, dict):
            return None
        return _validate_task_metadata(decoded)
    if isinstance(value, Mapping):
        return _validate_task_metadata(dict(value))
    return None


def summarize_task_metadata_rows(
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    metadata_rows = [_validate_task_metadata_for_summary(row) for row in rows]
    return {
        "row_count": len(metadata_rows),
        "family_counts": _sorted_counts(
            metadata.target_family for metadata in metadata_rows
        ),
        "support_level_counts": _sorted_counts(
            metadata.support_level for metadata in metadata_rows
        ),
        "seed_evaluation_status_counts": _sorted_counts(
            metadata.seed_evaluation_status for metadata in metadata_rows
        ),
        "seed_reward_counts": _sorted_counts(
            f"{metadata.seed_reward:.1f}" for metadata in metadata_rows
        ),
        "seed_reproduction": {
            "attempted": sum(
                metadata.seed_reproduction_attempted for metadata in metadata_rows
            ),
            "not_attempted": sum(
                not metadata.seed_reproduction_attempted
                for metadata in metadata_rows
            ),
            "status_counts": _sorted_counts(
                metadata.seed_reproduction_status for metadata in metadata_rows
            ),
            "succeeded": sum(
                metadata.seed_reproduction_success is True
                for metadata in metadata_rows
            ),
        },
        "seed_estimator_counts": _sorted_counts(
            metadata.seed_estimator_name or "none" for metadata in metadata_rows
        ),
    }


def attack_plan_matches_task_metadata(
    plan: AttackPlan,
    metadata: Mapping[str, Any] | str | None,
    *,
    allow_operator_param_variants: bool = False,
) -> bool:
    normalized = normalize_task_metadata(metadata)
    if normalized is None:
        return False

    expected_operator_types = normalized.get("operator_types")
    expected_operator_params = normalized.get("operator_params")
    expected_operator_assumptions = normalized.get("operator_assumptions")
    candidate_operator_types = [operator.type for operator in plan.operators]
    candidate_operator_params = [dict(operator.params) for operator in plan.operators]
    candidate_operator_assumptions = [
        list(operator.assumptions) for operator in plan.operators
    ]

    return (
        normalized.get("target_family") == plan.target.family.value
        and normalized.get("target_name") == plan.target.name
        and normalized.get("support_level") == plan.target.support_level.value
        and isinstance(expected_operator_types, list)
        and expected_operator_types == candidate_operator_types
        and isinstance(expected_operator_params, list)
        and (
            allow_operator_param_variants
            or expected_operator_params == candidate_operator_params
        )
        and isinstance(expected_operator_assumptions, list)
        and expected_operator_assumptions == candidate_operator_assumptions
    )


def _validate_task_metadata(value: dict[str, Any]) -> dict[str, Any] | None:
    try:
        metadata = TaskMetadata.model_validate(value)
    except ValueError:
        return None
    if metadata.schema_version != TASK_METADATA_SCHEMA:
        return None
    return metadata.model_dump(mode="json")


def _validate_task_metadata_for_summary(row: Mapping[str, Any]) -> TaskMetadata:
    metadata = TaskMetadata.model_validate(row)
    if metadata.schema_version != TASK_METADATA_SCHEMA:
        raise ValueError(
            "Task metadata summary requires schema_version "
            f"{TASK_METADATA_SCHEMA}."
        )
    return metadata


def _sorted_counts(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _verify_seed_plan(plan: AttackPlan) -> dict[str, Any]:
    from agades_pqc_gym.verifier import verify_attack_plan_json

    return verify_attack_plan_json(plan.model_dump_json())
