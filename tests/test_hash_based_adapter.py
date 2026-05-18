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


def test_hash_based_toy_preimage_bound_scores_reviewed_target() -> None:
    plan = _toy_preimage_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "HASH_BASED"
    assert result.metrics["feature_attack_type"] == (
        "security_bound_check:toy_preimage_bound"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-hash-bound-estimator"
    assert result.estimator_result.time_bits == pytest.approx(32.0)
    assert result.estimator_result.memory_bits == pytest.approx(1.0)
    assert result.estimator_result.raw_output == {
        "bound_model": "toy_preimage_bound",
        "classical_preimage_bits": 32.0,
        "digest_bits": 32,
        "toy_collision_bits": 16.0,
    }
    assert any("not a security claim" in warning for warning in result.warnings)


def test_hash_based_toy_collision_bound_scores_reviewed_target() -> None:
    plan = _toy_collision_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_collision_bits = 32 / 2

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "HASH_BASED"
    assert result.metrics["feature_attack_type"] == (
        "security_bound_check:toy_collision_bound"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-hash-bound-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        expected_collision_bits
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        expected_collision_bits
    )
    assert result.estimator_result.raw_output == {
        "bound_model": "toy_collision_bound",
        "birthday_collision_bits": expected_collision_bits,
        "digest_bits": 32,
        "hash_function": "SHAKE256",
    }
    assert any("not a security claim" in warning for warning in result.warnings)


def test_hash_based_toy_signature_chain_scores_reviewed_target() -> None:
    plan = _toy_signature_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_time_bits = math.log2(4 * 8)
    expected_memory_bits = math.log2(4 * (24 // 8))

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "HASH_BASED"
    assert result.metrics["feature_attack_type"] == (
        "hash_signature_verification:toy_wots_chain_verify"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-hash-bound-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "chain_count": 4,
        "digest_bits": 24,
        "hash_function": "SHAKE256",
        "max_chain_steps": 8,
        "model": "toy_wots_chain_verify",
        "toy_chain_hashes": 32,
    }
    assert any("not a security claim" in warning for warning in result.warnings)


def test_hash_based_toy_merkle_auth_path_scores_reviewed_target() -> None:
    plan = _toy_merkle_auth_path_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_hashes = 4
    expected_memory_bytes = expected_hashes * (24 // 8)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "HASH_BASED"
    assert result.metrics["feature_attack_type"] == (
        "hash_signature_verification:toy_merkle_auth_path_verify"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-hash-bound-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(math.log2(expected_hashes), 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(math.log2(expected_memory_bytes), 4)
    )
    assert result.estimator_result.raw_output == {
        "digest_bits": 24,
        "hash_function": "SHAKE256",
        "leaf_index": 5,
        "model": "toy_merkle_auth_path_verify",
        "tree_height": 3,
        "toy_auth_path_hashes": 4,
    }
    assert any("not a security claim" in warning for warning in result.warnings)


def test_hash_based_toy_fors_auth_path_scores_reviewed_target() -> None:
    plan = _toy_fors_auth_path_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_hashes = 2 * (2 + 1)
    expected_memory_bytes = expected_hashes * (24 // 8)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "HASH_BASED"
    assert result.metrics["feature_attack_type"] == (
        "hash_signature_verification:toy_fors_auth_path_verify"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-hash-bound-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(math.log2(expected_hashes), 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(math.log2(expected_memory_bytes), 4)
    )
    assert result.estimator_result.raw_output == {
        "digest_bits": 24,
        "hash_function": "SHAKE256",
        "model": "toy_fors_auth_path_verify",
        "selected_indices": [1, 2],
        "tree_count": 2,
        "tree_height": 2,
        "toy_fors_hashes": expected_hashes,
    }
    assert any("not an SLH-DSA result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_hash_based_toy_slh_dsa_hypertree_scores_reviewed_target() -> None:
    plan = _toy_slh_dsa_hypertree_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_hashes = 2 * (2 + 1) + 4 * 8 + 3 + 2
    expected_memory_bytes = expected_hashes * (24 // 8)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "HASH_BASED"
    assert result.metrics["feature_attack_type"] == (
        "hash_signature_verification:toy_slh_dsa_hypertree_verify"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-hash-bound-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(math.log2(expected_hashes), 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(math.log2(expected_memory_bytes), 4)
    )
    assert result.estimator_result.raw_output == {
        "digest_bits": 24,
        "fors_selected_indices": [1, 2],
        "fors_tree_count": 2,
        "fors_tree_height": 2,
        "hash_function": "SHAKE256",
        "hypertree_height": 3,
        "hypertree_leaf_index": 5,
        "model": "toy_slh_dsa_hypertree_verify",
        "toy_signature_hashes": expected_hashes,
        "wots_chain_count": 4,
        "wots_max_chain_steps": 8,
    }
    assert any("not an SLH-DSA result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_hash_based_toy_misuse_check_scores_reviewed_target() -> None:
    plan = _toy_misuse_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_pair_checks = math.comb(4, 2)
    expected_time_bits = math.log2(expected_pair_checks)
    expected_memory_bits = math.log2(4 * 3)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "HASH_BASED"
    assert result.metrics["feature_attack_type"] == (
        "misuse_check:toy_hash_reused_salt"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-hash-bound-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "expected_reuse_groups": 1,
        "fixture": "toy_hash_reused_salt",
        "hash_function": "SHAKE256",
        "model": "toy_hash_reused_salt_misuse_check",
        "pair_checks": expected_pair_checks,
        "record_count": 4,
        "salt_bytes": 3,
    }
    assert any("not a security claim" in warning for warning in result.warnings)


def test_hash_based_implemented_targets_are_limited_to_reviewed_toys() -> None:
    plan = _toy_preimage_plan().model_copy(
        update={
            "target": _toy_preimage_plan().target.model_copy(
                update={"name": "slh_dsa_like_target", "n": 256}
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "HASH_BASED implemented evaluator is limited to toy_" in error
        for error in result.errors
    )


def test_hash_based_signature_chain_requires_positive_chain_parameters() -> None:
    plan = _toy_signature_plan().model_copy(
        update={
            "operators": [
                _toy_signature_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "signature_model": "toy_wots_chain_verify",
                            "chain_count": 0,
                            "max_chain_steps": 8,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_wots_chain_verify requires positive integer chain_count" in error
        for error in result.errors
    )


def test_hash_based_signature_chain_requires_chain_assumption() -> None:
    plan = _toy_signature_plan().model_copy(
        update={
            "operators": [
                _toy_signature_plan().operators[0].model_copy(
                    update={"assumptions": []}
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_hash_signature_chain_model" in error for error in result.errors
    )


def test_hash_based_merkle_auth_path_requires_merkle_assumption() -> None:
    plan = _toy_merkle_auth_path_plan().model_copy(
        update={
            "operators": [
                _toy_merkle_auth_path_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_hash_merkle_auth_path_model" in error for error in result.errors
    )


def test_hash_based_misuse_check_requires_misuse_assumption() -> None:
    plan = _toy_misuse_plan().model_copy(
        update={
            "operators": [
                _toy_misuse_plan().operators[0].model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any("toy_hash_misuse_fixture_model" in error for error in result.errors)


def test_hash_based_fors_auth_path_requires_fors_assumption() -> None:
    plan = _toy_fors_auth_path_plan().model_copy(
        update={
            "operators": [
                _toy_fors_auth_path_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any("toy_hash_fors_auth_path_model" in error for error in result.errors)


def test_hash_based_fors_auth_path_requires_matching_selected_indices() -> None:
    plan = _toy_fors_auth_path_plan().model_copy(
        update={
            "operators": [
                _toy_fors_auth_path_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "signature_model": "toy_fors_auth_path_verify",
                            "tree_count": 2,
                            "tree_height": 2,
                            "selected_indices": [1],
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_fors_auth_path_verify requires selected_indices length == tree_count"
        in error
        for error in result.errors
    )


def test_hash_based_slh_dsa_hypertree_requires_assumption() -> None:
    plan = _toy_slh_dsa_hypertree_plan().model_copy(
        update={
            "operators": [
                _toy_slh_dsa_hypertree_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_hash_slh_dsa_hypertree_model" in error for error in result.errors
    )


def test_hash_based_slh_dsa_hypertree_requires_matching_selected_indices() -> None:
    plan = _toy_slh_dsa_hypertree_plan().model_copy(
        update={
            "operators": [
                _toy_slh_dsa_hypertree_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "signature_model": "toy_slh_dsa_hypertree_verify",
                            "fors_tree_count": 2,
                            "fors_tree_height": 2,
                            "fors_selected_indices": [1],
                            "wots_chain_count": 4,
                            "wots_max_chain_steps": 8,
                            "hypertree_height": 3,
                            "hypertree_leaf_index": 5,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_slh_dsa_hypertree_verify requires "
        "fors_selected_indices length == fors_tree_count" in error
        for error in result.errors
    )


def test_hash_based_misuse_check_requires_positive_record_count() -> None:
    plan = _toy_misuse_plan().model_copy(
        update={
            "operators": [
                _toy_misuse_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "fixture": "toy_hash_reused_salt",
                            "record_count": 0,
                            "expected_reuse_groups": 1,
                            "salt_bytes": 3,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_hash_reused_salt requires positive integer record_count" in error
        for error in result.errors
    )


def test_hash_based_collision_bound_requires_collision_assumption() -> None:
    plan = _toy_collision_plan().model_copy(
        update={
            "operators": [
                _toy_collision_plan().operators[0].model_copy(
                    update={"assumptions": []}
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_hash_collision_bound_model" in error for error in result.errors
    )


def test_hash_based_toy_reproduction_verifies_public_collision_fixture() -> None:
    plan = _toy_collision_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/hash_based_toy_bound/fixtures/"
                    "toy_hash_collision_32_fixture.json"
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


def test_hash_based_toy_reproduction_solves_public_preimage_fixture() -> None:
    plan = _toy_preimage_24_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/hash_based_toy_bound/fixtures/"
                    "toy_hash_preimage_24_fixture.json"
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


def test_hash_based_toy_reproduction_verifies_public_signature_fixture() -> None:
    plan = _toy_signature_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/hash_based_toy_signature/fixtures/"
                    "toy_hash_signature_chain_24_fixture.json"
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


def test_hash_based_toy_reproduction_verifies_public_merkle_auth_path_fixture() -> None:
    plan = _toy_merkle_auth_path_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/hash_based_toy_signature/fixtures/"
                    "toy_hash_merkle_auth_path_24_fixture.json"
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


def test_hash_based_toy_reproduction_verifies_public_fors_auth_path_fixture() -> None:
    plan = _toy_fors_auth_path_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not an SLH-DSA result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_hash_based_toy_reproduction_verifies_public_slh_dsa_fixture() -> None:
    plan = _toy_slh_dsa_hypertree_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not an SLH-DSA result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_hash_based_toy_reproduction_verifies_public_misuse_fixture() -> None:
    plan = _toy_misuse_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not a security claim" in warning for warning in result.warnings)


def test_hash_based_misuse_reproduction_rejects_fixture_metadata_mismatch() -> None:
    plan = _toy_misuse_plan().model_copy(
        update={
            "operators": [
                _toy_misuse_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "fixture": "toy_hash_reused_salt",
                            "record_count": 5,
                            "expected_reuse_groups": 1,
                            "salt_bytes": 3,
                        }
                    }
                )
            ]
        }
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "failed"
    assert result.metrics["reproduction_status"] == "failed"
    assert result.metrics["reproducibility_score"] == 0.0


def test_hash_based_merkle_reproduction_uses_later_signature_operator() -> None:
    plan = _toy_merkle_auth_path_plan().model_copy(
        update={
            "operators": [
                AttackOperator(
                    type="security_bound_check",
                    params={"bound_model": "toy_preimage_bound"},
                    assumptions=["toy_hash_preimage_bound_model"],
                ),
                _toy_merkle_auth_path_plan().operators[0],
            ],
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/hash_based_toy_signature/fixtures/"
                    "toy_hash_merkle_auth_path_24_fixture.json"
                ),
            ),
        }
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_status"] == "instance_solved"


def test_hash_based_toy_reproduction_fixture_must_stay_in_fixture_dir() -> None:
    plan = _toy_preimage_24_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/hash_based_toy_bound/toy_hash_preimage_24.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/hash_based_toy_bound/fixtures/" in error
        for error in result.errors
    )


def test_hash_based_signature_fixture_must_stay_in_signature_fixture_dir() -> None:
    plan = _toy_signature_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/hash_based_toy_bound/fixtures/"
                    "toy_hash_preimage_24_fixture.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/hash_based_toy_signature/fixtures/" in error
        for error in result.errors
    )


def test_hash_based_toy_reproduction_fixture_rejects_path_traversal() -> None:
    plan = _toy_preimage_24_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/hash_based_toy_bound/fixtures/"
                    "../toy_hash_preimage_24_fixture.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/hash_based_toy_bound/fixtures/" in error
        for error in result.errors
    )


def _toy_preimage_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="hash_based_preimage_toy_v1",
        target=TargetSpec(
            family=TargetFamily.HASH_BASED,
            name="toy_hash_preimage_32",
            support_level=SupportLevel.IMPLEMENTED,
            n=32,
            hash_function="SHAKE256",
            claimed_security_bits=32.0,
        ),
        operators=[
            AttackOperator(
                type="security_bound_check",
                params={"bound_model": "toy_preimage_bound"},
                assumptions=["toy_hash_preimage_bound_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy hash preimage-bound baseline for public plumbing only; "
                "not a security claim."
            ),
        ),
    )


def _toy_preimage_24_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="hash_based_preimage_24_toy_v1",
        target=TargetSpec(
            family=TargetFamily.HASH_BASED,
            name="toy_hash_preimage_24",
            support_level=SupportLevel.IMPLEMENTED,
            n=24,
            hash_function="SHAKE256",
            claimed_security_bits=24.0,
        ),
        operators=[
            AttackOperator(
                type="security_bound_check",
                params={"bound_model": "toy_preimage_bound"},
                assumptions=["toy_hash_preimage_bound_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy SHAKE256 preimage reproduction fixture for public "
                "plumbing only; not a security claim."
            ),
        ),
    )


def _toy_collision_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="hash_based_collision_toy_v1",
        target=TargetSpec(
            family=TargetFamily.HASH_BASED,
            name="toy_hash_collision_32",
            support_level=SupportLevel.IMPLEMENTED,
            n=32,
            hash_function="SHAKE256",
            claimed_security_bits=16.0,
        ),
        operators=[
            AttackOperator(
                type="security_bound_check",
                params={"bound_model": "toy_collision_bound"},
                assumptions=["toy_hash_collision_bound_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy hash collision-bound baseline for public plumbing only; "
                "not a security claim."
            ),
        ),
    )


def _toy_signature_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="hash_based_signature_toy_v1",
        target=TargetSpec(
            family=TargetFamily.HASH_BASED,
            name="toy_hash_signature_chain_24",
            support_level=SupportLevel.IMPLEMENTED,
            n=24,
            hash_function="SHAKE256",
            claimed_security_bits=24.0,
        ),
        operators=[
            AttackOperator(
                type="hash_signature_verification",
                params={
                    "signature_model": "toy_wots_chain_verify",
                    "chain_count": 4,
                    "max_chain_steps": 8,
                },
                assumptions=["toy_hash_signature_chain_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy hash-signature chain verification baseline for public "
                "plumbing only; not a security claim."
            ),
        ),
    )


def _toy_merkle_auth_path_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="hash_based_merkle_auth_path_toy_v1",
        target=TargetSpec(
            family=TargetFamily.HASH_BASED,
            name="toy_hash_merkle_auth_path_24",
            support_level=SupportLevel.IMPLEMENTED,
            n=24,
            hash_function="SHAKE256",
            claimed_security_bits=24.0,
        ),
        operators=[
            AttackOperator(
                type="hash_signature_verification",
                params={
                    "signature_model": "toy_merkle_auth_path_verify",
                    "tree_height": 3,
                    "leaf_index": 5,
                },
                assumptions=["toy_hash_merkle_auth_path_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy Merkle auth-path verification baseline for public "
                "plumbing only; not a signature security claim."
            ),
        ),
    )


def _toy_fors_auth_path_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="hash_based_fors_auth_path_toy_v1",
        target=TargetSpec(
            family=TargetFamily.HASH_BASED,
            name="toy_hash_fors_auth_path_24",
            support_level=SupportLevel.IMPLEMENTED,
            n=24,
            hash_function="SHAKE256",
            claimed_security_bits=24.0,
        ),
        operators=[
            AttackOperator(
                type="hash_signature_verification",
                params={
                    "signature_model": "toy_fors_auth_path_verify",
                    "tree_count": 2,
                    "tree_height": 2,
                    "selected_indices": [1, 2],
                },
                assumptions=["toy_hash_fors_auth_path_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/hash_based_toy_signature/fixtures/"
                "toy_hash_fors_auth_path_24_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy FORS auth-path verification baseline for public plumbing "
                "only; not an SLH-DSA result and not a security claim."
            ),
        ),
    )


def _toy_slh_dsa_hypertree_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="hash_based_slh_dsa_hypertree_toy_v1",
        target=TargetSpec(
            family=TargetFamily.HASH_BASED,
            name="toy_hash_slh_dsa_hypertree_24",
            support_level=SupportLevel.IMPLEMENTED,
            n=24,
            hash_function="SHAKE256",
            claimed_security_bits=24.0,
        ),
        operators=[
            AttackOperator(
                type="hash_signature_verification",
                params={
                    "signature_model": "toy_slh_dsa_hypertree_verify",
                    "fors_tree_count": 2,
                    "fors_tree_height": 2,
                    "fors_selected_indices": [1, 2],
                    "wots_chain_count": 4,
                    "wots_max_chain_steps": 8,
                    "hypertree_height": 3,
                    "hypertree_leaf_index": 5,
                },
                assumptions=["toy_hash_slh_dsa_hypertree_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/hash_based_toy_signature/fixtures/"
                "toy_hash_slh_dsa_hypertree_24_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy SLH-DSA-like hypertree signature verification baseline "
                "for public plumbing only; not an SLH-DSA result and not a "
                "security claim."
            ),
        ),
    )


def _toy_misuse_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="hash_based_misuse_reused_salt_toy_v1",
        target=TargetSpec(
            family=TargetFamily.HASH_BASED,
            name="toy_hash_reused_salt_24",
            support_level=SupportLevel.IMPLEMENTED,
            n=24,
            hash_function="SHAKE256",
            claimed_security_bits=1.0,
        ),
        operators=[
            AttackOperator(
                type="misuse_check",
                params={
                    "fixture": "toy_hash_reused_salt",
                    "record_count": 4,
                    "expected_reuse_groups": 1,
                    "salt_bytes": 3,
                },
                assumptions=["toy_hash_misuse_fixture_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/hash_based_toy_misuse/fixtures/"
                "toy_hash_reused_salt_24_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy hash misuse reused-salt fixture for public plumbing only; "
                "not a security claim."
            ),
        ),
    )
