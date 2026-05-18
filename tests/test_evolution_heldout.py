from pathlib import Path

import pytest
from pydantic import ValidationError

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.target import TargetSpec
from agades_pqc_gym.evolution.archive import build_evolution_archive
from agades_pqc_gym.evolution.heldout import build_heldout_candidate_plans
from agades_pqc_gym.traces.schema import TraceRecord


def test_build_heldout_candidate_plans_rebases_elites_to_private_targets() -> None:
    source_plan = _plan("examples/attack_plans/lattice_primal_usvp_toy.json")
    heldout_target = _target("benchmarks/lattice_toy_lwe/lwe_n96_q769.json")
    source_record = _record(
        plan=source_plan,
        candidate_id="candidate",
        score=-90.0,
        accepted=True,
    )
    archive = build_evolution_archive([source_record], run_id="training")

    candidates = build_heldout_candidate_plans(
        archive,
        [source_record],
        [heldout_target],
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.candidate_id == "candidate-heldout-toy_lwe_n96_q769-0"
    assert candidate.parent_id == "candidate"
    assert candidate.generation == 1
    assert candidate.mutation_summary == "held-out re-evaluation on toy_lwe_n96_q769"
    assert candidate.attack_plan.attack_plan_id == (
        "lattice_primal_usvp_toy_v1__heldout__toy_lwe_n96_q769"
    )
    assert candidate.attack_plan.target == heldout_target
    assert candidate.attack_plan.metadata.public is False
    assert "private held-out" in candidate.attack_plan.metadata.notes.lower()


def test_build_heldout_candidate_plans_rejects_cross_family_retargeting() -> None:
    source_plan = _plan("examples/attack_plans/lattice_primal_usvp_toy.json")
    code_based_target = _target(
        "benchmarks/code_based_toy_isd/toy_syndrome_31_16_w3.json"
    )
    source_record = _record(
        plan=source_plan,
        candidate_id="candidate",
        score=-90.0,
        accepted=True,
    )
    archive = build_evolution_archive([source_record], run_id="training")

    with pytest.raises(ValueError, match="same target family"):
        build_heldout_candidate_plans(
            archive,
            [source_record],
            [code_based_target],
        )


def test_build_heldout_candidate_plans_rejects_target_specific_reproduction() -> None:
    source_plan = _plan(
        "examples/attack_plans/lattice_primal_usvp_toy_reproducible.json"
    )
    heldout_target = _target("benchmarks/lattice_toy_lwe/lwe_n96_q769.json")
    source_record = _record(
        plan=source_plan,
        candidate_id="candidate",
        score=-90.0,
        accepted=True,
    )
    archive = build_evolution_archive([source_record], run_id="training")

    with pytest.raises(ValueError, match="target-specific reproduction"):
        build_heldout_candidate_plans(
            archive,
            [source_record],
            [heldout_target],
        )


def _plan(path: str) -> AttackPlan:
    return AttackPlan.model_validate_json(Path(path).read_text())


def _target(path: str) -> TargetSpec:
    raw = Path(path).read_text()
    try:
        return AttackPlan.model_validate_json(raw).target
    except ValidationError:
        return TargetSpec.model_validate_json(raw)


def _record(
    *,
    plan: AttackPlan,
    candidate_id: str,
    score: float,
    accepted: bool,
) -> TraceRecord:
    return TraceRecord.from_evaluation(
        run_id="training",
        candidate_id=candidate_id,
        parent_id=None,
        generation=0,
        mutation_summary="unit test",
        attack_plan=plan,
        evaluation={
            "combined_score": score,
            "evaluation_status": "ok" if accepted else "invalid",
            "feature_family": plan.target.family.value,
            "feature_attack_type": "primal_usvp",
            "feature_memory_bucket": "low",
            "feature_assumption_bucket": "some",
            "feature_estimator_model": "mock-lattice-estimator",
            "valid": accepted,
        },
        accepted=accepted,
        public_release_ok=accepted,
        redaction_reason=None if accepted else "invalid",
    )
