from __future__ import annotations

import math

import pytest

from agades_pqc_gym.core.attack_plan import (
    AttackOperator,
    AttackPlan,
    Claims,
    Constraints,
    Metadata,
)
from agades_pqc_gym.core.target import SupportLevel, TargetFamily, TargetSpec
from agades_pqc_gym.evaluators.cascade import CascadeEvaluator
from agades_pqc_gym.validators.static import validate_attack_plan


def test_isogeny_historical_toy_path_estimator_scores_reviewed_target() -> None:
    plan = _toy_path_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_path_count_bits = 8 * math.log2(4)
    expected_time_bits = expected_path_count_bits + math.log2(64)
    expected_memory_bits = math.log2(64 + 8 + 4)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "ISOGENY_HISTORICAL"
    assert result.metrics["feature_attack_type"] == (
        "historical_isogeny_reconstruction:toy_sidh_path_search"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-isogeny-historical-path-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "branching_factor": 4,
        "case": "toy_sidh_path_search",
        "field_overhead_bits": round(math.log2(64), 4),
        "model": "historical_toy_isogeny_path_model",
        "n": 64,
        "path_count_bits": round(expected_path_count_bits, 4),
        "walk_length": 8,
    }
    assert any("historical toy" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_isogeny_historical_toy_commutative_walk_estimator_scores() -> None:
    plan = _toy_commutative_walk_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_path_count_bits = 6 * math.log2(5)
    expected_time_bits = expected_path_count_bits + math.log2(97)
    expected_memory_bits = math.log2(97 + 6 + 5)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "ISOGENY_HISTORICAL"
    assert result.metrics["feature_attack_type"] == (
        "historical_isogeny_reconstruction:toy_commutative_walk_search"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-isogeny-historical-path-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "branching_factor": 5,
        "case": "toy_commutative_walk_search",
        "field_overhead_bits": round(math.log2(97), 4),
        "model": "historical_toy_commutative_walk_model",
        "n": 97,
        "path_count_bits": round(expected_path_count_bits, 4),
        "walk_length": 6,
    }
    assert any("historical toy" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_isogeny_historical_toy_volcano_walk_estimator_scores() -> None:
    plan = _toy_volcano_walk_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_path_count_bits = 5 * math.log2(4)
    expected_volcano_overhead_bits = math.log2(4)
    expected_time_bits = (
        expected_path_count_bits + math.log2(83) + expected_volcano_overhead_bits
    )
    expected_memory_bits = math.log2(83 + 5 + 4 + 3)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "ISOGENY_HISTORICAL"
    assert result.metrics["feature_attack_type"] == (
        "historical_isogeny_reconstruction:toy_volcano_walk_search"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-isogeny-historical-path-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "branching_factor": 4,
        "case": "toy_volcano_walk_search",
        "field_overhead_bits": round(math.log2(83), 4),
        "model": "historical_toy_volcano_walk_model",
        "n": 83,
        "path_count_bits": round(expected_path_count_bits, 4),
        "volcano_height": 3,
        "volcano_overhead_bits": round(expected_volcano_overhead_bits, 4),
        "walk_length": 5,
    }
    assert any("historical toy" in warning for warning in result.warnings)
    assert any("not a current-standard" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_isogeny_historical_toy_volcano_walk_requires_case_assumption() -> None:
    plan = _toy_volcano_walk_plan().model_copy(
        update={
            "operators": [
                _toy_volcano_walk_plan().operators[0].model_copy(
                    update={"assumptions": ["historical_not_current_standard"]}
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any("historical_toy_volcano_walk_model" in error for error in result.errors)


def test_isogeny_historical_toy_volcano_walk_requires_bounded_height() -> None:
    plan = _toy_volcano_walk_plan().model_copy(
        update={
            "operators": [
                _toy_volcano_walk_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "case": "toy_volcano_walk_search",
                            "walk_length": 5,
                            "branching_factor": 4,
                            "volcano_height": 0,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy volcano walk requires 1 <= volcano_height <= 8" in error
        for error in result.errors
    )


def test_isogeny_historical_implemented_targets_are_limited_to_reviewed_toys() -> None:
    plan = _toy_path_plan().model_copy(
        update={
            "target": _toy_path_plan().target.model_copy(
                update={"name": "sike_like_current_standard", "n": 434}
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "ISOGENY_HISTORICAL implemented evaluator is limited to toy_" in error
        for error in result.errors
    )


def test_isogeny_historical_toy_path_rejects_schema_only_assumption() -> None:
    plan = _toy_path_plan().model_copy(
        update={
            "operators": [
                _toy_path_plan().operators[0].model_copy(
                    update={
                        "assumptions": [
                            "historical_not_current_standard",
                            "historical_toy_isogeny_path_model",
                            "schema_only_no_estimator",
                        ]
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "ISOGENY_HISTORICAL implemented toy plans must not use "
        "schema_only_no_estimator"
        in error
        for error in result.errors
    )


def test_isogeny_historical_toy_path_reproduction_verifies_public_fixture() -> None:
    plan = _toy_path_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/isogeny_historical_toy_path/fixtures/"
                    "toy_sidh_path_fixture.json"
                ),
            )
        }
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.reproduction_result.score == pytest.approx(0.4)
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert any("not a current-standard" in warning for warning in result.warnings)


def test_isogeny_historical_commutative_walk_reproduces_public_fixture() -> None:
    plan = _toy_commutative_walk_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/isogeny_historical_toy_path/fixtures/"
                    "toy_commutative_walk_fixture.json"
                ),
            )
        }
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.reproduction_result.score == pytest.approx(0.4)
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert any("not a current-standard" in warning for warning in result.warnings)


def test_isogeny_historical_volcano_walk_reproduces_public_fixture() -> None:
    plan = _toy_volcano_walk_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/isogeny_historical_toy_path/fixtures/"
                    "toy_volcano_walk_fixture.json"
                ),
            )
        }
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.reproduction_result.score == pytest.approx(0.4)
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert any("not a current-standard" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_isogeny_historical_toy_path_reproduction_requires_fixture() -> None:
    plan = _toy_path_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "requires an explicit public historical path fixture" in error
        for error in result.errors
    )


def test_isogeny_historical_toy_path_reproduction_fixture_scope() -> None:
    plan = _toy_path_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/isogeny_historical_toy_path/"
                    "toy_sidh_path_fixture.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/isogeny_historical_toy_path/fixtures/" in error
        for error in result.errors
    )


def test_isogeny_historical_toy_path_reproduction_fixture_traversal() -> None:
    plan = _toy_path_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/isogeny_historical_toy_path/fixtures/"
                    "../toy_sidh_path_fixture.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/isogeny_historical_toy_path/fixtures/" in error
        for error in result.errors
    )


def _toy_path_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="isogeny_historical_toy_path_v1",
        target=TargetSpec(
            family=TargetFamily.ISOGENY_HISTORICAL,
            name="toy_sidh_path_reconstruction",
            support_level=SupportLevel.IMPLEMENTED,
            n=64,
        ),
        operators=[
            AttackOperator(
                type="historical_isogeny_reconstruction",
                params={
                    "case": "toy_sidh_path_search",
                    "walk_length": 8,
                    "branching_factor": 4,
                },
                assumptions=[
                    "historical_not_current_standard",
                    "historical_toy_isogeny_path_model",
                ],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Historical toy isogeny path baseline for public plumbing only; "
                "not a current-standard or security claim."
            ),
        ),
    )


def _toy_commutative_walk_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="isogeny_historical_commutative_walk_toy_v1",
        target=TargetSpec(
            family=TargetFamily.ISOGENY_HISTORICAL,
            name="toy_commutative_walk_reconstruction",
            support_level=SupportLevel.IMPLEMENTED,
            n=97,
        ),
        operators=[
            AttackOperator(
                type="historical_isogeny_reconstruction",
                params={
                    "case": "toy_commutative_walk_search",
                    "walk_length": 6,
                    "branching_factor": 5,
                },
                assumptions=[
                    "historical_not_current_standard",
                    "historical_toy_commutative_walk_model",
                ],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Historical toy commutative isogeny-walk baseline for public "
                "plumbing only; not a CSIDH result, current-standard result, "
                "or security claim."
            ),
        ),
    )


def _toy_volcano_walk_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="isogeny_historical_volcano_walk_toy_v1",
        target=TargetSpec(
            family=TargetFamily.ISOGENY_HISTORICAL,
            name="toy_volcano_walk_reconstruction",
            support_level=SupportLevel.IMPLEMENTED,
            n=83,
        ),
        operators=[
            AttackOperator(
                type="historical_isogeny_reconstruction",
                params={
                    "case": "toy_volcano_walk_search",
                    "walk_length": 5,
                    "branching_factor": 4,
                    "volcano_height": 3,
                },
                assumptions=[
                    "historical_not_current_standard",
                    "historical_toy_volcano_walk_model",
                ],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Historical toy volcano-style isogeny walk baseline for "
                "public plumbing only; not a CSIDH, SIDH, current-standard, "
                "or security claim."
            ),
        ),
    )
