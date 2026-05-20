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


def test_multivariate_toy_mq_estimator_scores_reviewed_target() -> None:
    plan = _toy_mq_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_assignment_bits = 8 * math.log2(16)
    expected_equation_check_bits = math.log2(6)
    expected_time_bits = expected_assignment_bits + expected_equation_check_bits
    expected_memory_bits = math.log2(8 + 6)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "MULTIVARIATE"
    assert result.metrics["feature_attack_type"] == "groebner_basis:toy_mq_search"
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-multivariate-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "assignment_space_bits": round(expected_assignment_bits, 4),
        "equation_check_bits": round(expected_equation_check_bits, 4),
        "equations": 6,
        "field_order": 16,
        "model": "toy_mq_search",
        "variables": 8,
    }
    assert any("not a security claim" in warning for warning in result.warnings)


def test_multivariate_toy_mq_hybrid_estimator_scores_reviewed_target() -> None:
    plan = _toy_mq_hybrid_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    field_order = 16
    guessed_variables = 3
    residual_variables = 5
    linearized_monomials = 1 + residual_variables + (
        residual_variables * (residual_variables + 1)
    ) // 2
    expected_guess_bits = guessed_variables * math.log2(field_order)
    expected_linear_algebra_bits = math.log2(linearized_monomials**3)
    expected_equation_check_bits = math.log2(6)
    expected_time_bits = (
        expected_guess_bits
        + expected_linear_algebra_bits
        + expected_equation_check_bits
    )
    expected_memory_bits = math.log2((linearized_monomials**2) + 6)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "MULTIVARIATE"
    assert result.metrics["feature_attack_type"] == (
        "groebner_basis:toy_mq_hybrid_search"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-multivariate-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "equation_check_bits": round(expected_equation_check_bits, 4),
        "equations": 6,
        "field_order": field_order,
        "guess_space_bits": round(expected_guess_bits, 4),
        "guessed_variables": guessed_variables,
        "linear_algebra_bits": round(expected_linear_algebra_bits, 4),
        "linearized_monomials": linearized_monomials,
        "model": "toy_mq_hybrid_search",
        "residual_variables": residual_variables,
        "variables": 8,
    }
    assert any("not a security claim" in warning for warning in result.warnings)


def test_multivariate_toy_mq_degree_bound_scores_reviewed_target() -> None:
    plan = _toy_mq_degree_bound_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    variables = 8
    equations = 6
    field_order = 16
    degree_bound = 3
    linear_algebra_omega = 2.8
    monomial_count = math.comb(variables + degree_bound, degree_bound)
    macaulay_rows = equations * math.comb(
        variables + max(degree_bound - 2, 0),
        max(degree_bound - 2, 0),
    )
    linear_algebra_bits = linear_algebra_omega * math.log2(monomial_count)
    field_operation_bits = math.log2(field_order)
    equation_check_bits = math.log2(equations)
    expected_time_bits = (
        linear_algebra_bits + field_operation_bits + equation_check_bits
    )
    expected_memory_bits = math.log2(macaulay_rows * monomial_count)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "MULTIVARIATE"
    assert result.metrics["feature_attack_type"] == (
        "groebner_basis:toy_mq_degree_bound"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-multivariate-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "degree_bound": degree_bound,
        "equation_check_bits": round(equation_check_bits, 4),
        "equations": equations,
        "field_operation_bits": round(field_operation_bits, 4),
        "field_order": field_order,
        "linear_algebra_bits": round(linear_algebra_bits, 4),
        "linear_algebra_omega": linear_algebra_omega,
        "macaulay_rows": macaulay_rows,
        "model": "toy_mq_degree_bound",
        "monomial_count": monomial_count,
        "variables": variables,
    }
    assert any("not a Groebner proof" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_multivariate_toy_minrank_estimator_scores_reviewed_target() -> None:
    plan = _toy_minrank_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_assignment_bits = 4 * math.log2(2)
    expected_rank_cost_bits = math.log2(3 * 3 * 3)
    expected_time_bits = expected_assignment_bits + expected_rank_cost_bits
    expected_memory_bits = math.log2((3 * 3) + 4)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "MULTIVARIATE"
    assert result.metrics["feature_attack_type"] == "minrank_attack:toy_minrank_search"
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-multivariate-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "assignment_space_bits": round(expected_assignment_bits, 4),
        "field_order": 2,
        "matrix_cols": 3,
        "matrix_rows": 3,
        "model": "toy_minrank_search",
        "rank_cost_bits": round(expected_rank_cost_bits, 4),
        "target_rank": 0,
        "variables": 4,
    }
    assert any("not a security claim" in warning for warning in result.warnings)


def test_multivariate_toy_uov_public_map_scores_reviewed_target() -> None:
    plan = _toy_uov_public_map_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    variables = 5
    equations = 3
    oil_variables = 2
    vinegar_variables = 3
    monomial_count = 1 + variables + (variables * (variables + 1)) // 2
    evaluation_bits = math.log2(equations * monomial_count)
    field_operation_bits = math.log2(2)
    expected_time_bits = evaluation_bits + field_operation_bits
    expected_memory_bits = math.log2(
        variables + equations + monomial_count + oil_variables + vinegar_variables
    )

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "MULTIVARIATE"
    assert result.metrics["feature_attack_type"] == (
        "signature_fixture_check:toy_uov_public_map_verify"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-multivariate-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "equations": equations,
        "evaluation_bits": round(evaluation_bits, 4),
        "field_operation_bits": round(field_operation_bits, 4),
        "field_order": 2,
        "model": "toy_uov_public_map_verify",
        "monomial_count": monomial_count,
        "oil_variables": oil_variables,
        "variables": variables,
        "vinegar_variables": vinegar_variables,
    }
    assert any("not a UOV" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_multivariate_implemented_targets_are_limited_to_reviewed_toys() -> None:
    plan = _toy_mq_plan().model_copy(
        update={
            "target": _toy_mq_plan().target.model_copy(
                update={"name": "uov_like_claimed_target", "variables": 112}
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "MULTIVARIATE implemented evaluator is limited to toy_" in error
        for error in result.errors
    )


def test_multivariate_minrank_requires_positive_matrix_dimensions() -> None:
    plan = _toy_minrank_plan().model_copy(
        update={
            "operators": [
                _toy_minrank_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "model": "toy_minrank_search",
                            "matrix_rows": 0,
                            "matrix_cols": 3,
                            "target_rank": 0,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_minrank_search requires positive integer matrix_rows" in error
        for error in result.errors
    )


def test_multivariate_minrank_requires_minrank_assumption() -> None:
    plan = _toy_minrank_plan().model_copy(
        update={
            "operators": [
                _toy_minrank_plan().operators[0].model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_minrank_exhaustive_search_model" in error for error in result.errors
    )


def test_multivariate_mq_hybrid_requires_assumption() -> None:
    plan = _toy_mq_hybrid_plan().model_copy(
        update={
            "operators": [
                _toy_mq_hybrid_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_mq_hybrid_linearization_model" in error for error in result.errors
    )


def test_multivariate_mq_hybrid_requires_partial_guess() -> None:
    plan = _toy_mq_hybrid_plan().model_copy(
        update={
            "operators": [
                _toy_mq_hybrid_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "model": "toy_mq_hybrid_search",
                            "guessed_variables": 8,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_mq_hybrid_search requires 1 <= guessed_variables < variables"
        in error
        for error in result.errors
    )


def test_multivariate_mq_degree_bound_requires_assumption() -> None:
    plan = _toy_mq_degree_bound_plan().model_copy(
        update={
            "operators": [
                _toy_mq_degree_bound_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any("toy_mq_degree_bound_model" in error for error in result.errors)


def test_multivariate_mq_degree_bound_requires_bounded_degree() -> None:
    plan = _toy_mq_degree_bound_plan().model_copy(
        update={
            "operators": [
                _toy_mq_degree_bound_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "model": "toy_mq_degree_bound",
                            "degree_bound": 1,
                            "linear_algebra_omega": 2.8,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_mq_degree_bound requires 2 <= degree_bound <= variables" in error
        for error in result.errors
    )


def test_multivariate_uov_public_map_requires_assumption() -> None:
    plan = _toy_uov_public_map_plan().model_copy(
        update={
            "operators": [
                _toy_uov_public_map_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_uov_public_map_verification_model" in error
        for error in result.errors
    )


def test_multivariate_uov_public_map_requires_oil_vinegar_partition() -> None:
    plan = _toy_uov_public_map_plan().model_copy(
        update={
            "operators": [
                _toy_uov_public_map_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "signature_model": "toy_uov_public_map_verify",
                            "oil_variables": 2,
                            "vinegar_variables": 2,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        (
            "toy_uov_public_map_verify requires "
            "oil_variables + vinegar_variables == variables"
        )
        in error
        for error in result.errors
    )


def test_multivariate_mq_hybrid_gf2_reproduction_solves_public_fixture() -> None:
    plan = _toy_mq_hybrid_gf2_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/multivariate_toy_mq/fixtures/"
                    "toy_mq_gf2_v6_e4_fixture.json"
                ),
            )
        }
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not a UOV" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_multivariate_toy_reproduction_solves_public_mq_fixture() -> None:
    plan = _toy_mq_gf2_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/multivariate_toy_mq/fixtures/"
                    "toy_mq_gf2_v6_e4_fixture.json"
                ),
            )
        }
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not a security claim" in warning for warning in result.warnings)


def test_multivariate_mq_degree_bound_gf2_reproduction_solves_public_fixture() -> None:
    plan = _toy_mq_degree_bound_gf2_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any(
        "not a Groebner proof" in warning
        for warning in result.reproduction_result.warnings
    )
    assert any("not a Groebner proof" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_multivariate_uov_public_map_reproduction_verifies_public_fixture() -> None:
    plan = _toy_uov_public_map_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not a UOV" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_multivariate_uov_public_map_fixture_must_stay_in_fixture_dir() -> None:
    plan = _toy_uov_public_map_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/multivariate_toy_mq/fixtures/"
                    "toy_uov_public_map_gf2_v5_e3_fixture.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/multivariate_toy_uov/fixtures/" in error
        for error in result.errors
    )


def test_multivariate_toy_reproduction_solves_public_minrank_fixture() -> None:
    plan = _toy_minrank_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/multivariate_toy_minrank/fixtures/"
                    "toy_minrank_gf2_m3_r0_fixture.json"
                ),
            )
        }
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not a security claim" in warning for warning in result.warnings)


def test_multivariate_toy_reproduction_solves_public_minrank_rank_one_fixture() -> None:
    plan = _toy_minrank_rank_one_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/multivariate_toy_minrank/fixtures/"
                    "toy_minrank_gf2_m3_r1_fixture.json"
                ),
            )
        }
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not a security claim" in warning for warning in result.warnings)


def test_multivariate_toy_reproduction_solves_public_minrank_rank_two_fixture() -> None:
    plan = _toy_minrank_rank_two_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/multivariate_toy_minrank/fixtures/"
                    "toy_minrank_gf2_m4_r2_fixture.json"
                ),
            )
        }
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not a security claim" in warning for warning in result.warnings)


def test_multivariate_toy_reproduction_fixture_must_stay_in_fixture_dir() -> None:
    plan = _toy_mq_gf2_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/multivariate_toy_mq/toy_mq_gf2_v6_e4.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/multivariate_toy_mq/fixtures/" in error
        for error in result.errors
    )


def test_multivariate_minrank_fixture_must_stay_in_minrank_fixture_dir() -> None:
    plan = _toy_minrank_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/multivariate_toy_mq/fixtures/"
                    "toy_mq_gf2_v6_e4_fixture.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/multivariate_toy_minrank/fixtures/" in error
        for error in result.errors
    )


def test_multivariate_toy_reproduction_fixture_rejects_path_traversal() -> None:
    plan = _toy_mq_gf2_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/multivariate_toy_mq/fixtures/"
                    "../toy_mq_gf2_v6_e4_fixture.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/multivariate_toy_mq/fixtures/" in error
        for error in result.errors
    )


def _toy_mq_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="multivariate_mq_toy_v1",
        target=TargetSpec(
            family=TargetFamily.MULTIVARIATE,
            name="toy_mq_gf16_v8_e6",
            support_level=SupportLevel.IMPLEMENTED,
            variables=8,
            equations=6,
            field="GF(16)",
            claimed_security_bits=32.0,
        ),
        operators=[
            AttackOperator(
                type="groebner_basis",
                params={"model": "toy_mq_search"},
                assumptions=["toy_mq_exhaustive_search_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy multivariate MQ baseline for public plumbing only; not a "
                "security claim."
            ),
        ),
    )


def _toy_mq_gf2_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="multivariate_mq_gf2_toy_v1",
        target=TargetSpec(
            family=TargetFamily.MULTIVARIATE,
            name="toy_mq_gf2_v6_e4",
            support_level=SupportLevel.IMPLEMENTED,
            variables=6,
            equations=4,
            field="GF(2)",
            claimed_security_bits=16.0,
        ),
        operators=[
            AttackOperator(
                type="groebner_basis",
                params={"model": "toy_mq_search"},
                assumptions=["toy_mq_exhaustive_search_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy binary multivariate MQ reproduction fixture for public "
                "plumbing only; not a security claim."
            ),
        ),
    )


def _toy_mq_hybrid_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="multivariate_mq_hybrid_toy_v1",
        target=TargetSpec(
            family=TargetFamily.MULTIVARIATE,
            name="toy_mq_hybrid_gf16_v8_e6",
            support_level=SupportLevel.IMPLEMENTED,
            variables=8,
            equations=6,
            field="GF(16)",
            claimed_security_bits=32.0,
        ),
        operators=[
            AttackOperator(
                type="groebner_basis",
                params={
                    "model": "toy_mq_hybrid_search",
                    "guessed_variables": 3,
                },
                assumptions=["toy_mq_hybrid_linearization_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy multivariate MQ hybrid-search baseline for public plumbing "
                "only; not a UOV, MAYO, Rainbow, or security claim."
            ),
        ),
    )


def _toy_mq_hybrid_gf2_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="multivariate_mq_hybrid_gf2_toy_v1",
        target=TargetSpec(
            family=TargetFamily.MULTIVARIATE,
            name="toy_mq_gf2_v6_e4",
            support_level=SupportLevel.IMPLEMENTED,
            variables=6,
            equations=4,
            field="GF(2)",
            claimed_security_bits=16.0,
        ),
        operators=[
            AttackOperator(
                type="groebner_basis",
                params={
                    "model": "toy_mq_hybrid_search",
                    "guessed_variables": 2,
                },
                assumptions=["toy_mq_hybrid_linearization_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy binary multivariate MQ hybrid-search fixture for public "
                "plumbing only; not a UOV, MAYO, Rainbow, or security claim."
            ),
        ),
    )


def _toy_mq_degree_bound_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="multivariate_mq_degree_bound_toy_v1",
        target=TargetSpec(
            family=TargetFamily.MULTIVARIATE,
            name="toy_mq_degree_bound_gf16_v8_e6",
            support_level=SupportLevel.IMPLEMENTED,
            variables=8,
            equations=6,
            field="GF(16)",
            claimed_security_bits=32.0,
        ),
        operators=[
            AttackOperator(
                type="groebner_basis",
                params={
                    "model": "toy_mq_degree_bound",
                    "degree_bound": 3,
                    "linear_algebra_omega": 2.8,
                },
                assumptions=["toy_mq_degree_bound_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy multivariate MQ degree-bound baseline for public plumbing "
                "only; not a Groebner proof, UOV/MAYO/Rainbow result, or "
                "security claim."
            ),
        ),
    )


def _toy_mq_degree_bound_gf2_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="multivariate_mq_degree_bound_gf2_toy_v1",
        target=TargetSpec(
            family=TargetFamily.MULTIVARIATE,
            name="toy_mq_gf2_v6_e4",
            support_level=SupportLevel.IMPLEMENTED,
            variables=6,
            equations=4,
            field="GF(2)",
            claimed_security_bits=16.0,
        ),
        operators=[
            AttackOperator(
                type="groebner_basis",
                params={
                    "model": "toy_mq_degree_bound",
                    "degree_bound": 3,
                    "linear_algebra_omega": 2.8,
                },
                assumptions=["toy_mq_degree_bound_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/multivariate_toy_mq/fixtures/"
                "toy_mq_gf2_v6_e4_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy binary multivariate MQ degree-bound fixture for public "
                "plumbing only; not a Groebner proof, UOV/MAYO/Rainbow "
                "result, or security claim."
            ),
        ),
    )


def _toy_minrank_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="multivariate_minrank_toy_v1",
        target=TargetSpec(
            family=TargetFamily.MULTIVARIATE,
            name="toy_minrank_gf2_m3_r0",
            support_level=SupportLevel.IMPLEMENTED,
            variables=4,
            equations=9,
            field="GF(2)",
            claimed_security_bits=12.0,
        ),
        operators=[
            AttackOperator(
                type="minrank_attack",
                params={
                    "model": "toy_minrank_search",
                    "matrix_rows": 3,
                    "matrix_cols": 3,
                    "target_rank": 0,
                },
                assumptions=["toy_minrank_exhaustive_search_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy multivariate MinRank baseline for public plumbing only; "
                "not a security claim."
            ),
        ),
    )


def _toy_uov_public_map_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="multivariate_uov_public_map_toy_v1",
        target=TargetSpec(
            family=TargetFamily.MULTIVARIATE,
            name="toy_uov_public_map_gf2_v5_e3",
            support_level=SupportLevel.IMPLEMENTED,
            variables=5,
            equations=3,
            field="GF(2)",
            claimed_security_bits=12.0,
        ),
        operators=[
            AttackOperator(
                type="signature_fixture_check",
                params={
                    "signature_model": "toy_uov_public_map_verify",
                    "oil_variables": 2,
                    "vinegar_variables": 3,
                },
                assumptions=["toy_uov_public_map_verification_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/multivariate_toy_uov/fixtures/"
                "toy_uov_public_map_gf2_v5_e3_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy UOV-inspired public-map verification fixture for public "
                "plumbing only; not a UOV, MAYO, Rainbow, or security claim."
            ),
        ),
    )


def _toy_minrank_rank_one_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="multivariate_minrank_rank_one_toy_v1",
        target=TargetSpec(
            family=TargetFamily.MULTIVARIATE,
            name="toy_minrank_gf2_m3_r1",
            support_level=SupportLevel.IMPLEMENTED,
            variables=4,
            equations=9,
            field="GF(2)",
            claimed_security_bits=12.0,
        ),
        operators=[
            AttackOperator(
                type="minrank_attack",
                params={
                    "model": "toy_minrank_search",
                    "matrix_rows": 3,
                    "matrix_cols": 3,
                    "target_rank": 1,
                },
                assumptions=["toy_minrank_exhaustive_search_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy multivariate MinRank rank-one fixture for public plumbing "
                "only; not a UOV, MAYO, Rainbow, or security claim."
            ),
        ),
    )


def _toy_minrank_rank_two_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="multivariate_minrank_rank_two_toy_v1",
        target=TargetSpec(
            family=TargetFamily.MULTIVARIATE,
            name="toy_minrank_gf2_m4_r2",
            support_level=SupportLevel.IMPLEMENTED,
            variables=4,
            equations=16,
            field="GF(2)",
            claimed_security_bits=12.0,
        ),
        operators=[
            AttackOperator(
                type="minrank_attack",
                params={
                    "model": "toy_minrank_search",
                    "matrix_rows": 4,
                    "matrix_cols": 4,
                    "target_rank": 2,
                },
                assumptions=["toy_minrank_exhaustive_search_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy multivariate MinRank rank-two fixture for public plumbing "
                "only; not a UOV, MAYO, Rainbow, or security claim."
            ),
        ),
    )
