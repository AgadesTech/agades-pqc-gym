from __future__ import annotations

import hashlib
import json
from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.integrations.task_metadata import (
    TASK_METADATA_SCHEMA,
    attack_plan_matches_task_metadata,
    normalize_task_metadata,
    task_metadata_for_plan,
)


def test_task_metadata_records_family_agnostic_constraints() -> None:
    source_path = Path("examples/attack_plans/lattice_primal_usvp_toy.json")
    source_text = source_path.read_text()
    plan = AttackPlan.model_validate_json(source_text)

    metadata = task_metadata_for_plan(
        plan,
        source_path=source_path.as_posix(),
        seed_attack_plan_json=source_text,
    )

    assert metadata == {
        "schema_version": "agades.pqc.task_metadata.v5",
        "source_path": "examples/attack_plans/lattice_primal_usvp_toy.json",
        "seed_attack_plan_sha256": hashlib.sha256(
            source_text.encode("utf-8")
        ).hexdigest(),
        "attack_plan_id": "lattice_primal_usvp_toy_v1",
        "target_family": "LWE",
        "target_name": "toy_lwe_n64_q257",
        "support_level": "implemented",
        "operator_types": ["primal_usvp"],
        "operator_assumptions": [["lattice_estimator_default_cost_model"]],
        "requires_reproducibility": False,
        "public": True,
        "seed_accepted": True,
        "seed_evaluation_status": "ok",
        "seed_estimator_name": "mock-lattice-estimator",
        "seed_reproduction_attempted": False,
        "seed_reproduction_status": "not_requested",
        "seed_reproduction_success": None,
        "seed_reward": 1.0,
    }
    assert metadata["schema_version"] == TASK_METADATA_SCHEMA
    assert TASK_METADATA_SCHEMA == "agades.pqc.task_metadata.v5"


def test_task_metadata_records_schema_only_seed_reward_boundary() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/code_based_bike_placeholder.json").read_text()
    )

    metadata = task_metadata_for_plan(
        plan,
        source_path="examples/attack_plans/code_based_bike_placeholder.json",
    )

    assert metadata["support_level"] == "schema_only"
    assert metadata["seed_accepted"] is False
    assert metadata["seed_evaluation_status"] == "unsupported"
    assert metadata["seed_estimator_name"] == "code-based-placeholder-estimator"
    assert metadata["seed_reproduction_attempted"] is False
    assert metadata["seed_reproduction_status"] == "not_applicable"
    assert metadata["seed_reproduction_success"] is None
    assert metadata["seed_reward"] == 0.0


def test_task_metadata_records_seed_reproduction_status_for_fixture_tasks() -> None:
    plan = AttackPlan.model_validate_json(
        Path(
            "examples/attack_plans/lattice_downscaled_lwe_instance_solve_toy.json"
        ).read_text()
    )

    metadata = task_metadata_for_plan(
        plan,
        source_path=(
            "examples/attack_plans/lattice_downscaled_lwe_instance_solve_toy.json"
        ),
    )

    assert metadata["requires_reproducibility"] is True
    assert metadata["seed_accepted"] is True
    assert metadata["seed_estimator_name"] == "mock-lattice-estimator"
    assert metadata["seed_reproduction_attempted"] is True
    assert metadata["seed_reproduction_status"] == "instance_solved"
    assert metadata["seed_reproduction_success"] is True
    assert metadata["seed_reward"] == 1.0


def test_task_metadata_match_allows_id_variant_but_rejects_wrong_task() -> None:
    lattice_data = json.loads(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    lattice_plan = AttackPlan.model_validate(lattice_data)
    metadata = task_metadata_for_plan(lattice_plan)
    lattice_data["attack_plan_id"] = "candidate_variant"
    variant_plan = AttackPlan.model_validate(lattice_data)
    missing_hypothesis_data = dict(lattice_data)
    missing_hypothesis_data["operators"] = [
        {**operator, "assumptions": []}
        for operator in missing_hypothesis_data["operators"]
    ]
    missing_hypothesis_plan = AttackPlan.model_validate(missing_hypothesis_data)
    code_based_plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/code_based_prange_toy.json").read_text()
    )

    assert attack_plan_matches_task_metadata(variant_plan, metadata)
    assert attack_plan_matches_task_metadata(
        variant_plan,
        json.dumps(metadata, sort_keys=True),
    )
    assert not attack_plan_matches_task_metadata(missing_hypothesis_plan, metadata)
    assert not attack_plan_matches_task_metadata(code_based_plan, metadata)
    assert normalize_task_metadata("{not json}") is None
    invalid_digest_metadata = dict(metadata)
    invalid_digest_metadata["seed_attack_plan_sha256"] = "not-a-sha256"
    assert normalize_task_metadata(invalid_digest_metadata) is None
