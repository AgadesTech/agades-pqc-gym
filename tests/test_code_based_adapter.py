from __future__ import annotations

import math
from pathlib import Path

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
from agades_pqc_gym.families.code_based import adapter as code_based_adapter
from agades_pqc_gym.families.code_based.classic_mceliece_fixture_decoder import (
    ToyClassicMcElieceSupportSyndromeFixture,
)
from agades_pqc_gym.validators.static import validate_attack_plan


def test_code_based_toy_prange_isd_estimator_scores_reviewed_target() -> None:
    plan = _toy_prange_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_attempts_bits = math.log2(math.comb(31, 3)) - math.log2(
        math.comb(15, 3)
    )
    expected_time_bits = expected_attempts_bits + math.log2(31) + math.log2(4)
    expected_memory_bits = math.log2(31) + math.log2(4)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "information_set_decoding:prange_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-code-based-isd-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output["attempts_bits"] == pytest.approx(
        round(expected_attempts_bits, 4)
    )
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_stern_isd_estimator_scores_reviewed_target() -> None:
    plan = _toy_stern_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_attempts_bits = (
        math.log2(math.comb(31, 3))
        - math.log2(math.comb(16, 2))
        - math.log2(math.comb(15, 1))
    )
    left_list_bits = math.log2(math.comb(8, 1))
    right_list_bits = math.log2(math.comb(8, 1))
    expected_collision_list_bits = math.log2(math.comb(8, 1) + math.comb(8, 1))
    expected_syndrome_filter_bits = math.log2(16)
    expected_time_bits = (
        expected_attempts_bits
        + max(left_list_bits, right_list_bits)
        + expected_syndrome_filter_bits
    )

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "information_set_decoding:stern_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-code-based-isd-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_collision_list_bits, 4)
    )
    assert result.estimator_result.raw_output["model"] == (
        "stern_information_set_decoding_toy"
    )
    assert result.estimator_result.raw_output["p"] == 1
    assert result.estimator_result.raw_output["information_set_errors"] == 2
    assert result.estimator_result.raw_output["redundancy_errors"] == 1
    assert result.estimator_result.raw_output["attempts_bits"] == pytest.approx(
        round(expected_attempts_bits, 4)
    )
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_dumer_isd_estimator_scores_reviewed_target() -> None:
    plan = _toy_dumer_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_attempts_bits = (
        math.log2(math.comb(31, 3))
        - math.log2(math.comb(16, 2))
        - math.log2(math.comb(15, 1))
    )
    left_list_bits = math.log2(math.comb(8, 1))
    right_list_bits = math.log2(math.comb(8, 1))
    expected_list_build_bits = math.log2(math.comb(8, 1) + math.comb(8, 1))
    expected_merge_bits = left_list_bits + right_list_bits - 2
    expected_syndrome_check_bits = math.log2(15 - 2 + 1)
    expected_time_bits = (
        expected_attempts_bits
        + expected_list_build_bits
        + expected_merge_bits
        + expected_syndrome_check_bits
    )
    expected_memory_bits = math.log2(
        math.comb(8, 1) + math.comb(8, 1) + 2**expected_merge_bits
    )

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "information_set_decoding:dumer_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-code-based-isd-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output["model"] == (
        "dumer_information_set_decoding_toy"
    )
    assert result.estimator_result.raw_output["p"] == 1
    assert result.estimator_result.raw_output["ell"] == 2
    assert result.estimator_result.raw_output["merge_filter_bits"] == 2
    assert result.estimator_result.raw_output["merge_bits"] == pytest.approx(
        round(expected_merge_bits, 4)
    )
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_bjmm_isd_estimator_scores_reviewed_target() -> None:
    plan = _toy_bjmm_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_attempts_bits = (
        math.log2(math.comb(31, 3))
        - math.log2(math.comb(16, 2))
        - math.log2(math.comb(15, 1))
    )
    left_list_bits = math.log2(math.comb(8, 1))
    right_list_bits = math.log2(math.comb(8, 1))
    expected_list_build_bits = math.log2(math.comb(8, 1) + math.comb(8, 1))
    expected_representation_gain_bits = math.log2(4)
    expected_merge_bits = (
        left_list_bits
        + right_list_bits
        - 2
        - expected_representation_gain_bits
    )
    expected_syndrome_check_bits = math.log2(15 - 2 + 1)
    expected_time_bits = (
        expected_attempts_bits
        + expected_list_build_bits
        + expected_merge_bits
        + expected_syndrome_check_bits
        + expected_representation_gain_bits
    )
    expected_memory_bits = math.log2(
        math.comb(8, 1) + math.comb(8, 1) + 2**expected_merge_bits
    )

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "information_set_decoding:bjmm_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-code-based-isd-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "attempts_bits": round(expected_attempts_bits, 4),
        "ell": 2,
        "information_set_errors": 2,
        "k": 16,
        "left_list_bits": round(left_list_bits, 4),
        "list_build_bits": round(expected_list_build_bits, 4),
        "merge_bits": round(expected_merge_bits, 4),
        "merge_filter_bits": 2,
        "model": "bjmm_information_set_decoding_toy",
        "n": 31,
        "p": 1,
        "redundancy": 15,
        "redundancy_errors": 1,
        "representation_count": 4,
        "representation_gain_bits": round(expected_representation_gain_bits, 4),
        "right_list_bits": round(right_list_bits, 4),
        "syndrome_check_bits": round(expected_syndrome_check_bits, 4),
        "w": 3,
    }
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_lee_brickell_estimator_scores_reviewed_target() -> None:
    plan = _toy_lee_brickell_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_attempts_bits = (
        math.log2(math.comb(31, 3))
        - math.log2(math.comb(16, 1))
        - math.log2(math.comb(15, 2))
    )
    expected_enumeration_bits = math.log2(math.comb(16, 1))
    expected_linear_algebra_bits = math.log2(31)
    expected_syndrome_filter_bits = math.log2(16)
    expected_time_bits = (
        expected_attempts_bits
        + expected_enumeration_bits
        + expected_linear_algebra_bits
        + expected_syndrome_filter_bits
    )
    expected_memory_bits = math.log2(math.comb(16, 1) + 31)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "information_set_decoding:lee_brickell_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-code-based-isd-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "attempts_bits": round(expected_attempts_bits, 4),
        "enumeration_bits": round(expected_enumeration_bits, 4),
        "information_set_errors": 1,
        "linear_algebra_bits": round(expected_linear_algebra_bits, 4),
        "model": "lee_brickell_information_set_decoding_toy",
        "n": 31,
        "k": 16,
        "p": 1,
        "redundancy": 15,
        "redundancy_errors": 2,
        "syndrome_filter_bits": round(expected_syndrome_filter_bits, 4),
        "w": 3,
    }
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_qc_rotation_estimator_scores_reviewed_target() -> None:
    plan = _toy_qc_rotation_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_time_bits = math.log2(7) + math.log2(21) + math.log2(3)
    expected_memory_bits = math.log2(7) + math.log2(3)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "information_set_decoding:qc_rotation_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == "toy-code-based-isd-estimator"
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output["model"] == (
        "quasi_cyclic_rotation_search_toy"
    )
    assert result.estimator_result.raw_output["rotation_count"] == 7
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_hqc_repetition_estimator_scores_reviewed_target() -> None:
    plan = _toy_hqc_repetition_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_time_bits = math.log2(21)
    expected_memory_bits = math.log2(28)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "decoding_fixture_check:hqc_repetition_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-code-based-repetition-decoder-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output["model"] == (
        "toy_hqc_repetition_majority_decode"
    )
    assert result.estimator_result.raw_output["vote_operations"] == 21
    assert any("not an HQC result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_hqc_weighted_repetition_estimator_scores() -> None:
    plan = _toy_hqc_weighted_repetition_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_weighted_vote_operations = 25
    expected_accumulator_bits = 4
    expected_time_bits = math.log2(
        expected_weighted_vote_operations * expected_accumulator_bits
    )
    expected_memory_bits = math.log2(25 + 5 + 3)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "decoding_fixture_check:hqc_weighted_repetition_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-code-based-weighted-repetition-decoder-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "accumulator_bits": expected_accumulator_bits,
        "k": 5,
        "max_reliability_weight": 3,
        "model": "toy_hqc_weighted_repetition_decode",
        "n": 25,
        "repetition_factor": 5,
        "w": 4,
        "weighted_vote_operations": expected_weighted_vote_operations,
    }
    assert any("not an HQC result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_hqc_parity_check_estimator_scores_reviewed_target() -> None:
    plan = _toy_hqc_parity_check_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_candidate_count = math.comb(15, 2)
    expected_time_bits = math.log2(expected_candidate_count) + math.log2(8 * 2)
    expected_memory_bits = math.log2(15 + 8 + 2)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "decoding_fixture_check:hqc_parity_check_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-code-based-parity-check-decoder-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output["model"] == (
        "toy_hqc_parity_check_syndrome_decode"
    )
    assert result.estimator_result.raw_output["candidate_count"] == (
        expected_candidate_count
    )
    assert result.estimator_result.raw_output["parity_check_rows"] == 8
    assert any("not an HQC result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_hqc_circulant_estimator_scores_reviewed_target() -> None:
    plan = _toy_hqc_circulant_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_candidate_count = sum(
        math.comb(8, left_weight) * math.comb(8, 2 - left_weight)
        for left_weight in range(3)
    )
    expected_syndrome_operations = expected_candidate_count * 8 * 2
    expected_time_bits = math.log2(expected_syndrome_operations)
    expected_memory_bits = math.log2(3 * 8 + 2)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "decoding_fixture_check:hqc_circulant_syndrome_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-code-based-circulant-syndrome-decoder-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "block_size": 8,
        "candidate_count": expected_candidate_count,
        "k": 8,
        "max_error_weight": 2,
        "model": "toy_hqc_circulant_syndrome_decode",
        "n": 16,
        "syndrome_operations": expected_syndrome_operations,
        "w": 2,
    }
    assert any("not an HQC result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_hqc_circulant_erasure_estimator_scores() -> None:
    plan = _toy_hqc_circulant_erasure_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_candidate_count = sum(
        math.comb(3, left_weight) * math.comb(3, 3 - left_weight)
        for left_weight in range(4)
    )
    expected_syndrome_operations = expected_candidate_count * 8 * 3
    expected_time_bits = math.log2(expected_syndrome_operations)
    expected_memory_bits = math.log2(3 * 8 + 6 + 3)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "decoding_fixture_check:hqc_circulant_erasure_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-code-based-circulant-erasure-decoder-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "block_size": 8,
        "candidate_count": expected_candidate_count,
        "erasure_count": 6,
        "first_block_erasure_count": 3,
        "k": 8,
        "max_error_weight": 3,
        "model": "toy_hqc_circulant_erasure_syndrome_decode",
        "n": 16,
        "second_block_erasure_count": 3,
        "syndrome_operations": expected_syndrome_operations,
        "w": 3,
    }
    assert any("not an HQC result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_hqc_erasure_syndrome_estimator_scores() -> None:
    plan = _toy_hqc_erasure_syndrome_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_candidate_count = math.comb(4, 2)
    expected_syndrome_operations = expected_candidate_count * 6 * 2
    expected_time_bits = math.log2(expected_syndrome_operations)
    expected_memory_bits = math.log2(12 + 4 + 2)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "decoding_fixture_check:hqc_erasure_syndrome_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-code-based-erasure-syndrome-decoder-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "candidate_count": expected_candidate_count,
        "erasure_count": 4,
        "k": 6,
        "max_error_weight": 2,
        "model": "toy_hqc_erasure_syndrome_decode",
        "n": 12,
        "syndrome_operations": expected_syndrome_operations,
        "w": 2,
    }
    assert any("not an HQC result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_mdpc_bit_flip_estimator_scores_reviewed_target() -> None:
    plan = _toy_mdpc_bit_flip_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_time_bits = math.log2(4 * (12 - 6) * 12)
    expected_memory_bits = math.log2(12 + (12 - 6) + 2)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "decoding_fixture_check:mdpc_bit_flip_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-code-based-bit-flip-decoder-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "bit_checks": 288,
        "k": 6,
        "max_iterations": 4,
        "model": "toy_mdpc_bit_flip_decode",
        "n": 12,
        "parity_check_rows": 6,
        "threshold": 2,
        "w": 2,
    }
    assert any("not a BIKE result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_mdpc_black_gray_estimator_scores_reviewed_target() -> None:
    plan = _toy_mdpc_black_gray_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_syndrome_products = 4 * (1 + 12)
    expected_bit_checks = expected_syndrome_products * (12 - 6) * 12
    expected_time_bits = math.log2(expected_bit_checks)
    expected_memory_bits = math.log2(12 + (12 - 6) + 2 + 2)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "decoding_fixture_check:mdpc_black_gray_bit_flip_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-code-based-bit-flip-decoder-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "bit_checks": expected_bit_checks,
        "black_threshold": 3,
        "gray_threshold": 2,
        "k": 6,
        "max_iterations": 4,
        "model": "toy_mdpc_black_gray_bit_flip_decode",
        "n": 12,
        "parity_check_rows": 6,
        "syndrome_products": expected_syndrome_products,
        "w": 2,
    }
    assert any("not a BIKE result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_mdpc_syndrome_weight_estimator_scores_reviewed_target() -> None:
    plan = _toy_mdpc_syndrome_weight_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_syndrome_bit_checks = 4 * 12 * (12 - 6)
    expected_time_bits = math.log2(expected_syndrome_bit_checks)
    expected_memory_bits = math.log2(12 + (12 - 6) + 2 + 1)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "decoding_fixture_check:mdpc_syndrome_weight_bit_flip_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-code-based-bit-flip-decoder-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "k": 6,
        "max_iterations": 4,
        "min_syndrome_weight_drop": 1,
        "model": "toy_mdpc_syndrome_weight_bit_flip_decode",
        "n": 12,
        "parity_check_rows": 6,
        "syndrome_bit_checks": expected_syndrome_bit_checks,
        "w": 2,
    }
    assert any("not a BIKE result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_classic_mceliece_estimator_scores_reviewed_target() -> None:
    plan = _toy_classic_mceliece_syndrome_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_candidate_count = math.comb(17, 2)
    expected_time_bits = math.log2(expected_candidate_count) + math.log2(8 * 2)
    expected_memory_bits = math.log2(17 + 8 + 2)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "decoding_fixture_check:classic_mceliece_syndrome_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-code-based-classic-mceliece-syndrome-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "candidate_count": expected_candidate_count,
        "k": 9,
        "max_error_weight": 2,
        "model": "toy_classic_mceliece_binary_syndrome_decode",
        "n": 17,
        "parity_check_rows": 8,
        "w": 2,
    }
    assert any(
        "not a Classic McEliece result" in warning for warning in result.warnings
    )
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_classic_mceliece_support_syndrome_scores() -> None:
    plan = _toy_classic_mceliece_support_syndrome_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_candidate_count = math.comb(5, 2)
    expected_time_bits = math.log2(expected_candidate_count) + math.log2(9 * 2)
    expected_memory_bits = math.log2(19 + 9 + 5 + 2)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "CODE_BASED"
    assert result.metrics["feature_attack_type"] == (
        "decoding_fixture_check:classic_mceliece_support_syndrome_toy"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.estimator_name == (
        "toy-code-based-classic-mceliece-support-syndrome-estimator"
    )
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.estimator_result.memory_bits == pytest.approx(
        round(expected_memory_bits, 4)
    )
    assert result.estimator_result.raw_output == {
        "candidate_count": expected_candidate_count,
        "k": 10,
        "max_error_weight": 2,
        "model": "toy_classic_mceliece_support_syndrome_decode",
        "n": 19,
        "parity_check_rows": 9,
        "support_size": 5,
        "w": 2,
    }
    assert any(
        "not a Classic McEliece result" in warning for warning in result.warnings
    )
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_classic_support_allows_weight_above_redundancy() -> None:
    base = _toy_classic_mceliece_support_syndrome_plan()
    plan = base.model_copy(
        update={
            "target": base.target.model_copy(
                update={
                    "name": "toy_classic_mceliece_support_syndrome_9_7_w3",
                    "n": 9,
                    "k": 7,
                    "w": 3,
                }
            ),
            "operators": [
                base.operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "classic_mceliece_support_syndrome_toy",
                            "max_error_weight": 3,
                            "support_size": 4,
                        }
                    }
                )
            ],
            "constraints": Constraints(),
        }
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.estimator_result is not None
    assert result.estimator_result.raw_output["candidate_count"] == math.comb(4, 3)
    assert result.estimator_result.raw_output["parity_check_rows"] == 2


def test_code_based_classic_support_fixture_allows_weight_above_redundancy() -> None:
    fixture = ToyClassicMcElieceSupportSyndromeFixture.model_validate(
        {
            "schema_version": (
                "agades.pqc.code_based_toy_classic_mceliece_support_syndrome.v1"
            ),
            "family": "CODE_BASED",
            "target_name": "toy_classic_mceliece_support_syndrome_6_4_w3",
            "n": 6,
            "k": 4,
            "w": 3,
            "parity_check_matrix": [
                [1, 0, 0, 0, 0, 0],
                [0, 1, 1, 0, 0, 0],
            ],
            "syndrome": [1, 0],
            "support_positions": [0, 1, 2, 3],
            "expected_error_positions": [0, 1, 2],
            "public": True,
            "security_claim": False,
        }
    )

    assert fixture.w == 3
    assert fixture.n - fixture.k == 2


def test_code_based_implemented_targets_are_limited_to_reviewed_toy_models() -> None:
    plan = _toy_prange_plan().model_copy(
        update={
            "target": _toy_prange_plan().target.model_copy(
                update={"name": "hqc_like_claimed_target", "n": 17669}
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "CODE_BASED implemented evaluator is limited to toy_" in error
        for error in result.errors
    )


def test_code_based_stern_variant_requires_positive_integer_p() -> None:
    plan = _toy_stern_plan().model_copy(
        update={
            "operators": [
                _toy_stern_plan().operators[0].model_copy(
                    update={"params": {"variant": "stern_toy"}}
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "stern_toy requires positive integer p" in error for error in result.errors
    )


def test_code_based_stern_variant_requires_stern_assumption() -> None:
    plan = _toy_stern_plan().model_copy(
        update={
            "operators": [
                _toy_stern_plan().operators[0].model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "stern_isd_partition_collision_cost_model" in error
        for error in result.errors
    )


def test_code_based_dumer_variant_requires_dumer_assumption() -> None:
    plan = _toy_dumer_plan().model_copy(
        update={
            "operators": [
                _toy_dumer_plan().operators[0].model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "dumer_isd_list_merging_cost_model" in error for error in result.errors
    )


def test_code_based_dumer_variant_requires_valid_merge_window() -> None:
    plan = _toy_dumer_plan().model_copy(
        update={
            "operators": [
                _toy_dumer_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "dumer_toy",
                            "p": 1,
                            "ell": 16,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any("dumer_toy requires ell <= n - k" in error for error in result.errors)


def test_code_based_bjmm_variant_requires_bjmm_assumption() -> None:
    plan = _toy_bjmm_plan().model_copy(
        update={
            "operators": [
                _toy_bjmm_plan().operators[0].model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "bjmm_isd_representation_merge_model" in error for error in result.errors
    )


def test_code_based_bjmm_variant_requires_bounded_representation_count() -> None:
    plan = _toy_bjmm_plan().model_copy(
        update={
            "operators": [
                _toy_bjmm_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "bjmm_toy",
                            "p": 1,
                            "ell": 2,
                            "representation_count": 65,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "bjmm_toy requires representation_count <= 64" in error
        for error in result.errors
    )


def test_code_based_lee_brickell_requires_assumption() -> None:
    plan = _toy_lee_brickell_plan().model_copy(
        update={
            "operators": [
                _toy_lee_brickell_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "lee_brickell_isd_partial_enumeration_model" in error
        for error in result.errors
    )


def test_code_based_lee_brickell_requires_valid_partial_weight() -> None:
    plan = _toy_lee_brickell_plan().model_copy(
        update={
            "operators": [
                _toy_lee_brickell_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "lee_brickell_toy",
                            "p": 4,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "lee_brickell_toy requires 1 <= p <= w" in error
        for error in result.errors
    )


def test_code_based_toy_reproduction_solves_public_syndrome_fixture() -> None:
    plan = _toy_prange_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/code_based_toy_isd/fixtures/"
                    "toy_syndrome_31_16_w3_fixture.json"
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


def test_code_based_second_toy_reproduction_solves_public_syndrome_fixture() -> None:
    plan = _toy_prange_second_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_attempts_bits = math.log2(math.comb(15, 2)) - math.log2(
        math.comb(8, 2)
    )
    expected_time_bits = expected_attempts_bits + math.log2(15) + math.log2(3)

    assert result.valid is True
    assert result.estimator_result is not None
    assert result.estimator_result.time_bits == pytest.approx(
        round(expected_time_bits, 4)
    )
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_qc_rotation_reproduction_solves_public_fixture() -> None:
    plan = _toy_qc_rotation_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_hqc_repetition_reproduction_decodes_public_fixture() -> None:
    plan = _toy_hqc_repetition_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/code_based_toy_hqc/fixtures/"
                    "toy_hqc_repetition_21_7_w3_fixture.json"
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
    assert any("not an HQC result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_hqc_weighted_repetition_reproduces_public_fixture() -> None:
    plan = _toy_hqc_weighted_repetition_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not an HQC result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_hqc_parity_check_reproduction_decodes_public_fixture() -> None:
    plan = _toy_hqc_parity_check_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not an HQC result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_hqc_circulant_reproduction_decodes_public_fixture() -> None:
    plan = _toy_hqc_circulant_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not an HQC result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_hqc_circulant_erasure_reproduction_decodes_fixture() -> None:
    plan = _toy_hqc_circulant_erasure_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not an HQC result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_hqc_erasure_syndrome_reproduction_decodes_fixture() -> None:
    plan = _toy_hqc_erasure_syndrome_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not an HQC result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_mdpc_bit_flip_reproduction_decodes_public_fixture() -> None:
    plan = _toy_mdpc_bit_flip_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not a BIKE result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_mdpc_black_gray_reproduction_decodes_public_fixture() -> None:
    plan = _toy_mdpc_black_gray_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not a BIKE result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_mdpc_syndrome_weight_decodes_public_fixture() -> None:
    plan = _toy_mdpc_syndrome_weight_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not a BIKE result" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_classic_mceliece_reproduction_decodes_public_fixture() -> None:
    plan = _toy_classic_mceliece_syndrome_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any(
        "not a Classic McEliece result" in warning for warning in result.warnings
    )
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_toy_classic_mceliece_support_syndrome_reproduction() -> None:
    plan = _toy_classic_mceliece_support_syndrome_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any(
        "not a Classic McEliece result" in warning for warning in result.warnings
    )
    assert any("not a security claim" in warning for warning in result.warnings)


def test_code_based_hqc_reproduction_uses_later_decoding_fixture_operator() -> None:
    plan = _toy_hqc_repetition_plan().model_copy(
        update={
            "operators": [
                AttackOperator(
                    type="information_set_decoding",
                    params={"variant": "prange_toy"},
                    assumptions=["prange_isd_combinatorial_cost_model"],
                ),
                _toy_hqc_repetition_plan().operators[0],
            ],
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/code_based_toy_hqc/fixtures/"
                    "toy_hqc_repetition_21_7_w3_fixture.json"
                ),
            ),
        }
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_status"] == "instance_solved"


def test_code_based_toy_reproduction_fixture_must_stay_in_fixture_dir() -> None:
    plan = _toy_prange_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/code_based_toy_isd/toy_syndrome_31_16_w3.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/code_based_toy_isd/fixtures/" in error
        for error in result.errors
    )


def test_code_based_toy_reproduction_fixture_rejects_path_traversal() -> None:
    plan = _toy_prange_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/code_based_toy_isd/fixtures/"
                    "../toy_syndrome_31_16_w3_fixture.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/code_based_toy_isd/fixtures/" in error
        for error in result.errors
    )


def test_code_based_qc_rotation_variant_requires_consistent_block_shape() -> None:
    plan = _toy_qc_rotation_plan().model_copy(
        update={
            "operators": [
                _toy_qc_rotation_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "qc_rotation_toy",
                            "block_size": 8,
                            "block_count": 3,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "qc_rotation_toy requires n == block_size * block_count" in error
        for error in result.errors
    )


def test_code_based_hqc_repetition_variant_requires_assumption() -> None:
    plan = _toy_hqc_repetition_plan().model_copy(
        update={
            "operators": [
                _toy_hqc_repetition_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_hqc_repetition_decoder_model" in error for error in result.errors
    )


def test_code_based_hqc_parity_check_variant_requires_assumption() -> None:
    plan = _toy_hqc_parity_check_plan().model_copy(
        update={
            "operators": [
                _toy_hqc_parity_check_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_hqc_parity_check_decoder_model" in error for error in result.errors
    )


def test_code_based_hqc_weighted_repetition_variant_requires_assumption() -> None:
    plan = _toy_hqc_weighted_repetition_plan().model_copy(
        update={
            "operators": [
                _toy_hqc_weighted_repetition_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_hqc_weighted_repetition_decoder_model" in error
        for error in result.errors
    )


def test_code_based_hqc_erasure_syndrome_variant_requires_assumption() -> None:
    plan = _toy_hqc_erasure_syndrome_plan().model_copy(
        update={
            "operators": [
                _toy_hqc_erasure_syndrome_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_hqc_erasure_syndrome_decoder_model" in error
        for error in result.errors
    )


def test_code_based_hqc_circulant_erasure_variant_requires_assumption() -> None:
    plan = _toy_hqc_circulant_erasure_plan().model_copy(
        update={
            "operators": [
                _toy_hqc_circulant_erasure_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_hqc_circulant_erasure_decoder_model" in error
        for error in result.errors
    )


def test_code_based_hqc_parity_check_variant_requires_exact_weight_bound() -> None:
    plan = _toy_hqc_parity_check_plan().model_copy(
        update={
            "operators": [
                _toy_hqc_parity_check_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "hqc_parity_check_toy",
                            "max_error_weight": 3,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "hqc_parity_check_toy requires max_error_weight == w"
        in error
        for error in result.errors
    )


def test_code_based_hqc_parity_check_variant_requires_hqc_toy_target_name() -> None:
    plan = _toy_hqc_parity_check_plan().model_copy(
        update={
            "target": _toy_hqc_parity_check_plan().target.model_copy(
                update={"name": "toy_syndrome_15_7_w2"}
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "hqc_parity_check_toy targets must start with toy_hqc_"
        in error
        for error in result.errors
    )


def test_code_based_hqc_weighted_repetition_requires_bounded_weight() -> None:
    plan = _toy_hqc_weighted_repetition_plan().model_copy(
        update={
            "operators": [
                _toy_hqc_weighted_repetition_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "hqc_weighted_repetition_toy",
                            "repetition_factor": 5,
                            "max_reliability_weight": 17,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "hqc_weighted_repetition_toy requires max_reliability_weight <= 16"
        in error
        for error in result.errors
    )


def test_code_based_hqc_circulant_variant_requires_double_block_shape() -> None:
    plan = _toy_hqc_circulant_plan().model_copy(
        update={
            "target": _toy_hqc_circulant_plan().target.model_copy(
                update={"n": 15}
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "hqc_circulant_syndrome_toy requires n == 2 * block_size"
        in error
        for error in result.errors
    )


def test_code_based_hqc_erasure_syndrome_requires_enough_erasures() -> None:
    plan = _toy_hqc_erasure_syndrome_plan().model_copy(
        update={
            "operators": [
                _toy_hqc_erasure_syndrome_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "hqc_erasure_syndrome_toy",
                            "max_error_weight": 2,
                            "erasure_count": 1,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "hqc_erasure_syndrome_toy requires erasure_count >= max_error_weight"
        in error
        for error in result.errors
    )


def test_code_based_hqc_circulant_erasure_requires_enough_erasures() -> None:
    plan = _toy_hqc_circulant_erasure_plan().model_copy(
        update={
            "operators": [
                _toy_hqc_circulant_erasure_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "hqc_circulant_erasure_toy",
                            "block_size": 8,
                            "max_error_weight": 3,
                            "first_block_erasure_count": 1,
                            "second_block_erasure_count": 1,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "hqc_circulant_erasure_toy requires total erasure count >= "
        "max_error_weight"
        in error
        for error in result.errors
    )


def test_code_based_mdpc_bit_flip_variant_requires_threshold() -> None:
    plan = _toy_mdpc_bit_flip_plan().model_copy(
        update={
            "operators": [
                _toy_mdpc_bit_flip_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "mdpc_bit_flip_toy",
                            "max_iterations": 4,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "mdpc_bit_flip_toy requires positive integer threshold" in error
        for error in result.errors
    )


def test_code_based_mdpc_bit_flip_variant_requires_mdpc_toy_target_name() -> None:
    plan = _toy_mdpc_bit_flip_plan().model_copy(
        update={
            "target": _toy_mdpc_bit_flip_plan().target.model_copy(
                update={"name": "toy_hqc_parity_check_12_6_w2"}
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "mdpc_bit_flip_toy targets must start with toy_mdpc_"
        in error
        for error in result.errors
    )


def test_code_based_mdpc_black_gray_variant_requires_ordered_thresholds() -> None:
    plan = _toy_mdpc_black_gray_plan().model_copy(
        update={
            "operators": [
                _toy_mdpc_black_gray_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "mdpc_black_gray_bit_flip_toy",
                            "black_threshold": 2,
                            "gray_threshold": 3,
                            "max_iterations": 4,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "mdpc_black_gray_bit_flip_toy requires gray_threshold <= black_threshold"
        in error
        for error in result.errors
    )


def test_code_based_mdpc_syndrome_weight_variant_requires_positive_drop() -> None:
    plan = _toy_mdpc_syndrome_weight_plan().model_copy(
        update={
            "operators": [
                _toy_mdpc_syndrome_weight_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "mdpc_syndrome_weight_bit_flip_toy",
                            "min_syndrome_weight_drop": 0,
                            "max_iterations": 4,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "mdpc_syndrome_weight_bit_flip_toy requires positive integer "
        "min_syndrome_weight_drop"
        in error
        for error in result.errors
    )


def test_code_based_classic_mceliece_syndrome_variant_requires_assumption() -> None:
    plan = _toy_classic_mceliece_syndrome_plan().model_copy(
        update={
            "operators": [
                _toy_classic_mceliece_syndrome_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_classic_mceliece_syndrome_decoder_model" in error
        for error in result.errors
    )


def test_code_based_classic_mceliece_syndrome_variant_requires_target_name() -> None:
    plan = _toy_classic_mceliece_syndrome_plan().model_copy(
        update={
            "target": _toy_classic_mceliece_syndrome_plan().target.model_copy(
                update={"name": "toy_hqc_parity_check_17_9_w2"}
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "classic_mceliece_syndrome_toy targets must start with toy_classic_mceliece_"
        in error
        for error in result.errors
    )


def test_code_based_classic_mceliece_support_syndrome_requires_assumption() -> None:
    plan = _toy_classic_mceliece_support_syndrome_plan().model_copy(
        update={
            "operators": [
                _toy_classic_mceliece_support_syndrome_plan()
                .operators[0]
                .model_copy(update={"assumptions": []})
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "toy_classic_mceliece_support_syndrome_decoder_model" in error
        for error in result.errors
    )


def test_code_based_classic_mceliece_support_syndrome_requires_large_support() -> None:
    plan = _toy_classic_mceliece_support_syndrome_plan().model_copy(
        update={
            "operators": [
                _toy_classic_mceliece_support_syndrome_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "classic_mceliece_support_syndrome_toy",
                            "max_error_weight": 2,
                            "support_size": 1,
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
            "classic_mceliece_support_syndrome_toy requires "
            "support_size >= max_error_weight"
        )
        in error
        for error in result.errors
    )


def test_code_based_hqc_repetition_variant_requires_consistent_shape() -> None:
    plan = _toy_hqc_repetition_plan().model_copy(
        update={
            "operators": [
                _toy_hqc_repetition_plan().operators[0].model_copy(
                    update={
                        "params": {
                            "variant": "hqc_repetition_toy",
                            "repetition_factor": 2,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "hqc_repetition_toy requires n == k * repetition_factor" in error
        for error in result.errors
    )


def test_code_based_toy_reproduction_uses_packaged_fixture_when_checkout_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(code_based_adapter, "ROOT", tmp_path)
    plan = _toy_prange_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/code_based_toy_isd/fixtures/"
                    "toy_syndrome_31_16_w3_fixture.json"
                ),
            )
        }
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_status"] == "instance_solved"


def test_code_based_hqc_erasure_syndrome_packaged_fixture_mirror() -> None:
    benchmark_fixture = Path(
        "benchmarks/code_based_toy_hqc/fixtures/"
        "toy_hqc_erasure_syndrome_12_6_w2_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/code_based/fixtures/"
        "toy_hqc_erasure_syndrome_12_6_w2_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()


def test_code_based_classic_mceliece_support_syndrome_packaged_fixture_mirror() -> None:
    benchmark_fixture = Path(
        "benchmarks/code_based_toy_classic_mceliece/fixtures/"
        "toy_classic_mceliece_support_syndrome_19_10_w2_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/code_based/fixtures/"
        "toy_classic_mceliece_support_syndrome_19_10_w2_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()


def _toy_prange_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_prange_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_syndrome_31_16_w3",
            support_level=SupportLevel.IMPLEMENTED,
            n=31,
            k=16,
            w=3,
            claimed_security_bits=32.0,
        ),
        operators=[
            AttackOperator(
                type="information_set_decoding",
                params={"variant": "prange_toy"},
                assumptions=["prange_isd_combinatorial_cost_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy Prange ISD baseline for public plumbing only; not a "
                "security claim."
            ),
        ),
    )


def _toy_stern_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_stern_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_syndrome_31_16_w3",
            support_level=SupportLevel.IMPLEMENTED,
            n=31,
            k=16,
            w=3,
            claimed_security_bits=32.0,
        ),
        operators=[
            AttackOperator(
                type="information_set_decoding",
                params={"variant": "stern_toy", "p": 1},
                assumptions=["stern_isd_partition_collision_cost_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy Stern-style ISD baseline for public plumbing only; not a "
                "security claim."
            ),
        ),
    )


def _toy_dumer_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_dumer_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_syndrome_31_16_w3",
            support_level=SupportLevel.IMPLEMENTED,
            n=31,
            k=16,
            w=3,
            claimed_security_bits=32.0,
        ),
        operators=[
            AttackOperator(
                type="information_set_decoding",
                params={"variant": "dumer_toy", "p": 1, "ell": 2},
                assumptions=["dumer_isd_list_merging_cost_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy Dumer-style ISD list-merging baseline for public plumbing "
                "only; not a security claim."
            ),
        ),
    )


def _toy_bjmm_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_bjmm_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_syndrome_31_16_w3",
            support_level=SupportLevel.IMPLEMENTED,
            n=31,
            k=16,
            w=3,
            claimed_security_bits=32.0,
        ),
        operators=[
            AttackOperator(
                type="information_set_decoding",
                params={
                    "variant": "bjmm_toy",
                    "p": 1,
                    "ell": 2,
                    "representation_count": 4,
                },
                assumptions=["bjmm_isd_representation_merge_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy BJMM-style representation merge baseline for public "
                "plumbing only; not a security claim."
            ),
        ),
    )


def _toy_lee_brickell_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_lee_brickell_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_syndrome_31_16_w3",
            support_level=SupportLevel.IMPLEMENTED,
            n=31,
            k=16,
            w=3,
            claimed_security_bits=32.0,
        ),
        operators=[
            AttackOperator(
                type="information_set_decoding",
                params={"variant": "lee_brickell_toy", "p": 1},
                assumptions=["lee_brickell_isd_partial_enumeration_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy Lee-Brickell-style ISD baseline for public plumbing only; "
                "not a security claim."
            ),
        ),
    )


def _toy_qc_rotation_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_qc_rotation_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_qc_syndrome_21_12_w2",
            support_level=SupportLevel.IMPLEMENTED,
            n=21,
            k=12,
            w=2,
            claimed_security_bits=18.0,
        ),
        operators=[
            AttackOperator(
                type="information_set_decoding",
                params={
                    "variant": "qc_rotation_toy",
                    "block_size": 7,
                    "block_count": 3,
                },
                assumptions=["toy_qc_syndrome_rotation_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/code_based_toy_isd/fixtures/"
                "toy_qc_syndrome_21_12_w2_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy quasi-cyclic syndrome rotation baseline for public "
                "plumbing only; not an HQC or security claim."
            ),
        ),
    )


def _toy_hqc_repetition_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_hqc_repetition_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_hqc_repetition_21_7_w3",
            support_level=SupportLevel.IMPLEMENTED,
            n=21,
            k=7,
            w=3,
            claimed_security_bits=12.0,
        ),
        operators=[
            AttackOperator(
                type="decoding_fixture_check",
                params={
                    "variant": "hqc_repetition_toy",
                    "repetition_factor": 3,
                },
                assumptions=["toy_hqc_repetition_decoder_model"],
            )
        ],
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy HQC-inspired repetition decoder fixture for public "
                "plumbing only; not an HQC result and not a security claim."
            ),
        ),
    )


def _toy_hqc_weighted_repetition_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_hqc_weighted_repetition_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_hqc_weighted_repetition_25_5_w4",
            support_level=SupportLevel.IMPLEMENTED,
            n=25,
            k=5,
            w=4,
            claimed_security_bits=13.0,
        ),
        operators=[
            AttackOperator(
                type="decoding_fixture_check",
                params={
                    "variant": "hqc_weighted_repetition_toy",
                    "repetition_factor": 5,
                    "max_reliability_weight": 3,
                },
                assumptions=["toy_hqc_weighted_repetition_decoder_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/code_based_toy_hqc/fixtures/"
                "toy_hqc_weighted_repetition_25_5_w4_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy HQC-inspired weighted repetition decoder fixture for "
                "public plumbing only; not an HQC result and not a security "
                "claim."
            ),
        ),
    )


def _toy_hqc_parity_check_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_hqc_parity_check_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_hqc_parity_check_15_7_w2",
            support_level=SupportLevel.IMPLEMENTED,
            n=15,
            k=7,
            w=2,
            claimed_security_bits=10.0,
        ),
        operators=[
            AttackOperator(
                type="decoding_fixture_check",
                params={
                    "variant": "hqc_parity_check_toy",
                    "max_error_weight": 2,
                },
                assumptions=["toy_hqc_parity_check_decoder_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/code_based_toy_hqc/fixtures/"
                "toy_hqc_parity_check_15_7_w2_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy HQC-inspired parity-check decoder fixture for public "
                "plumbing only; not an HQC result and not a security claim."
            ),
        ),
    )


def _toy_hqc_circulant_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_hqc_circulant_syndrome_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_hqc_circulant_syndrome_16_8_w2",
            support_level=SupportLevel.IMPLEMENTED,
            n=16,
            k=8,
            w=2,
            claimed_security_bits=11.0,
        ),
        operators=[
            AttackOperator(
                type="decoding_fixture_check",
                params={
                    "variant": "hqc_circulant_syndrome_toy",
                    "block_size": 8,
                    "max_error_weight": 2,
                },
                assumptions=["toy_hqc_circulant_syndrome_decoder_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/code_based_toy_hqc/fixtures/"
                "toy_hqc_circulant_syndrome_16_8_w2_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy HQC-inspired circulant syndrome decoder fixture for "
                "public plumbing only; not an HQC result and not a security "
                "claim."
            ),
        ),
    )


def _toy_hqc_circulant_erasure_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_hqc_circulant_erasure_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_hqc_circulant_erasure_16_8_w3",
            support_level=SupportLevel.IMPLEMENTED,
            n=16,
            k=8,
            w=3,
            claimed_security_bits=12.0,
        ),
        operators=[
            AttackOperator(
                type="decoding_fixture_check",
                params={
                    "variant": "hqc_circulant_erasure_toy",
                    "block_size": 8,
                    "max_error_weight": 3,
                    "first_block_erasure_count": 3,
                    "second_block_erasure_count": 3,
                },
                assumptions=["toy_hqc_circulant_erasure_decoder_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/code_based_toy_hqc/fixtures/"
                "toy_hqc_circulant_erasure_16_8_w3_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy HQC-inspired circulant erasure decoder fixture for public "
                "plumbing only; not an HQC result and not a security claim."
            ),
        ),
    )


def _toy_hqc_erasure_syndrome_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_hqc_erasure_syndrome_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_hqc_erasure_syndrome_12_6_w2",
            support_level=SupportLevel.IMPLEMENTED,
            n=12,
            k=6,
            w=2,
            claimed_security_bits=9.0,
        ),
        operators=[
            AttackOperator(
                type="decoding_fixture_check",
                params={
                    "variant": "hqc_erasure_syndrome_toy",
                    "max_error_weight": 2,
                    "erasure_count": 4,
                },
                assumptions=["toy_hqc_erasure_syndrome_decoder_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/code_based_toy_hqc/fixtures/"
                "toy_hqc_erasure_syndrome_12_6_w2_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy HQC-inspired erasure-aided syndrome decoder fixture for "
                "public plumbing only; not an HQC result and not a security "
                "claim."
            ),
        ),
    )


def _toy_mdpc_bit_flip_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_mdpc_bit_flip_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_mdpc_bit_flip_12_6_w2",
            support_level=SupportLevel.IMPLEMENTED,
            n=12,
            k=6,
            w=2,
            claimed_security_bits=10.0,
        ),
        operators=[
            AttackOperator(
                type="decoding_fixture_check",
                params={
                    "variant": "mdpc_bit_flip_toy",
                    "threshold": 2,
                    "max_iterations": 4,
                },
                assumptions=["toy_mdpc_bit_flip_decoder_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/code_based_toy_mdpc/fixtures/"
                "toy_mdpc_bit_flip_12_6_w2_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy MDPC/BIKE-inspired bit-flip decoder fixture for public "
                "plumbing only; not a BIKE result and not a security claim."
            ),
        ),
    )


def _toy_mdpc_black_gray_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_mdpc_black_gray_bit_flip_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_mdpc_black_gray_12_6_w2",
            support_level=SupportLevel.IMPLEMENTED,
            n=12,
            k=6,
            w=2,
            claimed_security_bits=10.0,
        ),
        operators=[
            AttackOperator(
                type="decoding_fixture_check",
                params={
                    "variant": "mdpc_black_gray_bit_flip_toy",
                    "black_threshold": 3,
                    "gray_threshold": 2,
                    "max_iterations": 4,
                },
                assumptions=["toy_mdpc_black_gray_bit_flip_decoder_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/code_based_toy_mdpc/fixtures/"
                "toy_mdpc_black_gray_12_6_w2_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy MDPC/BIKE-inspired black-gray bit-flip decoder fixture "
                "for public plumbing only; not a BIKE result and not a "
                "security claim."
            ),
        ),
    )


def _toy_mdpc_syndrome_weight_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_mdpc_syndrome_weight_bit_flip_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_mdpc_syndrome_weight_12_6_w2",
            support_level=SupportLevel.IMPLEMENTED,
            n=12,
            k=6,
            w=2,
            claimed_security_bits=10.0,
        ),
        operators=[
            AttackOperator(
                type="decoding_fixture_check",
                params={
                    "variant": "mdpc_syndrome_weight_bit_flip_toy",
                    "min_syndrome_weight_drop": 1,
                    "max_iterations": 4,
                },
                assumptions=["toy_mdpc_syndrome_weight_bit_flip_decoder_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/code_based_toy_mdpc/fixtures/"
                "toy_mdpc_syndrome_weight_12_6_w2_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy MDPC/BIKE-inspired syndrome-weight bit-flip decoder "
                "fixture for public plumbing only; not a BIKE result and not "
                "a security claim."
            ),
        ),
    )


def _toy_classic_mceliece_syndrome_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_classic_mceliece_syndrome_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_classic_mceliece_syndrome_17_9_w2",
            support_level=SupportLevel.IMPLEMENTED,
            n=17,
            k=9,
            w=2,
            claimed_security_bits=12.0,
        ),
        operators=[
            AttackOperator(
                type="decoding_fixture_check",
                params={
                    "variant": "classic_mceliece_syndrome_toy",
                    "max_error_weight": 2,
                },
                assumptions=["toy_classic_mceliece_syndrome_decoder_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/code_based_toy_classic_mceliece/fixtures/"
                "toy_classic_mceliece_syndrome_17_9_w2_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy Classic-McEliece-inspired binary syndrome fixture for "
                "public plumbing only; not a Classic McEliece result and not "
                "a security claim."
            ),
        ),
    )


def _toy_classic_mceliece_support_syndrome_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_classic_mceliece_support_syndrome_toy_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_classic_mceliece_support_syndrome_19_10_w2",
            support_level=SupportLevel.IMPLEMENTED,
            n=19,
            k=10,
            w=2,
            claimed_security_bits=10.0,
        ),
        operators=[
            AttackOperator(
                type="decoding_fixture_check",
                params={
                    "variant": "classic_mceliece_support_syndrome_toy",
                    "max_error_weight": 2,
                    "support_size": 5,
                },
                assumptions=[
                    "toy_classic_mceliece_support_syndrome_decoder_model"
                ],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/code_based_toy_classic_mceliece/fixtures/"
                "toy_classic_mceliece_support_syndrome_19_10_w2_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy Classic-McEliece-inspired public support-set syndrome "
                "fixture for plumbing only; not a Classic McEliece result and "
                "not a security claim."
            ),
        ),
    )


def _toy_prange_second_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="code_based_prange_toy_n15_v1",
        target=TargetSpec(
            family=TargetFamily.CODE_BASED,
            name="toy_syndrome_15_7_w2",
            support_level=SupportLevel.IMPLEMENTED,
            n=15,
            k=7,
            w=2,
            claimed_security_bits=16.0,
        ),
        operators=[
            AttackOperator(
                type="information_set_decoding",
                params={"variant": "prange_toy"},
                assumptions=["prange_isd_combinatorial_cost_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/code_based_toy_isd/fixtures/"
                "toy_syndrome_15_7_w2_fixture.json"
            ),
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Second toy Prange ISD reproduction fixture for public plumbing "
                "only; not a security claim."
            ),
        ),
    )
