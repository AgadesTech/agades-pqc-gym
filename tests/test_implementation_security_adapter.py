from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from agades_pqc_gym.core.attack_plan import (
    AttackOperator,
    AttackPlan,
    Constraints,
    Metadata,
)
from agades_pqc_gym.core.target import SupportLevel, TargetFamily, TargetSpec
from agades_pqc_gym.evaluators.cascade import CascadeEvaluator
from agades_pqc_gym.validators.static import validate_attack_plan


def test_implementation_security_toy_kat_scores_digest_manifest() -> None:
    plan = _toy_kat_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    payload_bytes = len(_TOY_KAT_PAYLOAD.encode("utf-8"))
    expected_time_bits = math.log2(payload_bytes + 2)
    expected_memory_bits = math.log2(payload_bytes)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "IMPLEMENTATION_SECURITY"
    assert result.metrics["feature_attack_type"] == (
        "kat_conformance:toy_kat_digest_match"
    )
    assert result.estimator_result is not None
    assert (
        result.estimator_result.estimator_name
        == "toy-implementation-security-estimator"
    )
    assert result.estimator_result.time_bits == round(expected_time_bits, 4)
    assert result.estimator_result.memory_bits == round(expected_memory_bits, 4)
    assert result.estimator_result.raw_output == {
        "digest_match": True,
        "expected_sha256": _TOY_KAT_DIGEST,
        "model": "toy_kat_digest_match",
        "payload_bytes": payload_bytes,
        "payload_sha256": _TOY_KAT_DIGEST,
        "suite": "toy_mlkem_kat",
        "vector_count": 2,
    }
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_timing_scores_public_trace_summary() -> None:
    plan = _toy_timing_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_abs_t = _welch_abs_t(_TOY_FIXED_CYCLES, _TOY_RANDOM_CYCLES)
    expected_time_bits = math.log2(len(_TOY_FIXED_CYCLES) + len(_TOY_RANDOM_CYCLES))
    expected_memory_bits = math.log2(
        max(len(_TOY_FIXED_CYCLES), len(_TOY_RANDOM_CYCLES))
    )

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "IMPLEMENTATION_SECURITY"
    assert result.metrics["feature_attack_type"] == (
        "constant_time_check:toy_timing_welch_t_check"
    )
    assert result.estimator_result is not None
    assert (
        result.estimator_result.estimator_name
        == "toy-implementation-security-estimator"
    )
    assert result.estimator_result.time_bits == round(expected_time_bits, 4)
    assert result.estimator_result.memory_bits == round(expected_memory_bits, 4)
    assert result.estimator_result.raw_output == {
        "fixed_mean_cycles": 100.0,
        "fixed_sample_count": 6,
        "max_abs_t": 1.0,
        "model": "toy_timing_welch_t_check",
        "observed_abs_t": round(expected_abs_t, 4),
        "random_mean_cycles": 100.5,
        "random_sample_count": 6,
        "threshold_passed": True,
        "tool": "toy_welch_timing_check",
    }
    assert any("not a constant-time" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_dudect_summary_scores_public_summary() -> None:
    plan = _toy_dudect_summary_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_abs_t = _welch_abs_t(_TOY_DUDECT_FIXED_CYCLES, _TOY_DUDECT_RANDOM_CYCLES)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "IMPLEMENTATION_SECURITY"
    assert result.metrics["feature_attack_type"] == (
        "constant_time_check:toy_dudect_summary_threshold_check"
    )
    assert result.estimator_result is not None
    assert (
        result.estimator_result.estimator_name
        == "toy-implementation-security-estimator"
    )
    assert result.estimator_result.time_bits == 4.0
    assert result.estimator_result.memory_bits == 3.0
    assert result.estimator_result.raw_output == {
        "classification": "toy_threshold_not_exceeded",
        "constant_time_claim": False,
        "dudect_execution": False,
        "dudect_version": "dudect-toy-summary-v0",
        "fixed_mean_cycles": 210.0,
        "fixed_sample_count": 8,
        "max_abs_t": 1.2,
        "model": "toy_dudect_summary_threshold_check",
        "observed_abs_t": round(expected_abs_t, 4),
        "random_mean_cycles": 210.625,
        "random_sample_count": 8,
        "threshold_passed": True,
        "tool": "toy_dudect_summary_check",
    }
    assert any("did not execute dudect" in warning for warning in result.warnings)
    assert any("not a constant-time" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_ctgrind_taint_scores_public_summary() -> None:
    plan = _toy_ctgrind_taint_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_time_bits = math.log2(
        _TOY_CTGRIND_CHECKED_BLOCKS
        + _TOY_CTGRIND_SECRET_BRANCH_COUNT
        + _TOY_CTGRIND_SECRET_MEMORY_ACCESS_COUNT
        + 1
    )

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "IMPLEMENTATION_SECURITY"
    assert result.metrics["feature_attack_type"] == (
        "constant_time_check:toy_ctgrind_secret_taint_summary_check"
    )
    assert result.estimator_result is not None
    assert (
        result.estimator_result.estimator_name
        == "toy-implementation-security-estimator"
    )
    assert result.estimator_result.time_bits == round(expected_time_bits, 4)
    assert result.estimator_result.memory_bits == 0.0
    assert result.estimator_result.raw_output == {
        "artifact_execution": False,
        "checked_blocks": _TOY_CTGRIND_CHECKED_BLOCKS,
        "classification": "toy_no_secret_taint_observed",
        "constant_time_claim": False,
        "ctgrind_execution": False,
        "ctgrind_version": "ctgrind-toy-summary-v0",
        "max_secret_dependent_branch_count": (
            _TOY_CTGRIND_MAX_SECRET_BRANCH_COUNT
        ),
        "max_secret_dependent_memory_access_count": (
            _TOY_CTGRIND_MAX_SECRET_MEMORY_ACCESS_COUNT
        ),
        "model": "toy_ctgrind_secret_taint_summary_check",
        "secret_dependent_branch_count": _TOY_CTGRIND_SECRET_BRANCH_COUNT,
        "secret_dependent_memory_access_count": (
            _TOY_CTGRIND_SECRET_MEMORY_ACCESS_COUNT
        ),
        "security_claim": False,
        "threshold_passed": True,
        "tool": "toy_ctgrind_secret_taint_summary_check",
    }
    assert any("did not execute ctgrind" in warning for warning in result.warnings)
    assert any("not a constant-time" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_acvp_scores_public_vector_set() -> None:
    plan = _toy_acvp_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    vector_set_bytes = len(_canonical_json(_TOY_ACVP_VECTOR_SET).encode("utf-8"))
    expected_time_bits = math.log2(vector_set_bytes + 1 + 2)
    expected_memory_bits = math.log2(vector_set_bytes)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "IMPLEMENTATION_SECURITY"
    assert result.metrics["feature_attack_type"] == (
        "kat_conformance:toy_acvp_vector_set_match"
    )
    assert result.estimator_result is not None
    assert (
        result.estimator_result.estimator_name
        == "toy-implementation-security-estimator"
    )
    assert result.estimator_result.time_bits == round(expected_time_bits, 4)
    assert result.estimator_result.memory_bits == round(expected_memory_bits, 4)
    assert result.estimator_result.raw_output == {
        "algorithm": "ML-KEM",
        "digest_match": True,
        "expected_vector_set_sha256": _TOY_ACVP_DIGEST,
        "mode": "encapsulation",
        "model": "toy_acvp_vector_set_match",
        "suite": "toy_acvp_mlkem_encap",
        "test_count": 2,
        "test_group_count": 1,
        "vector_set_bytes": vector_set_bytes,
        "vector_set_sha256": _TOY_ACVP_DIGEST,
    }
    assert any("not an ACVP certificate" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_acvp_scores_public_mldsa_vector_set() -> None:
    plan = _toy_acvp_mldsa_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    vector_set_bytes = len(
        _canonical_json(_TOY_ACVP_MLDSA_VECTOR_SET).encode("utf-8")
    )
    expected_time_bits = math.log2(vector_set_bytes + 1 + 2)
    expected_memory_bits = math.log2(vector_set_bytes)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "IMPLEMENTATION_SECURITY"
    assert result.metrics["feature_attack_type"] == (
        "kat_conformance:toy_acvp_vector_set_match"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.raw_output == {
        "algorithm": "ML-DSA",
        "digest_match": True,
        "expected_vector_set_sha256": _TOY_ACVP_MLDSA_DIGEST,
        "mode": "signature-verification",
        "model": "toy_acvp_vector_set_match",
        "suite": "toy_acvp_mldsa_signature",
        "test_count": 2,
        "test_group_count": 1,
        "vector_set_bytes": vector_set_bytes,
        "vector_set_sha256": _TOY_ACVP_MLDSA_DIGEST,
    }
    assert result.estimator_result.time_bits == round(expected_time_bits, 4)
    assert result.estimator_result.memory_bits == round(expected_memory_bits, 4)
    assert any("not an ACVP certificate" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_benchmark_scores_public_summary() -> None:
    plan = _toy_benchmark_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    expected_total_cycles = sum(_TOY_BENCHMARK_SAMPLES)
    expected_time_bits = math.log2(expected_total_cycles)
    expected_memory_bits = math.log2(len(_TOY_BENCHMARK_SAMPLES))

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "IMPLEMENTATION_SECURITY"
    assert result.metrics["feature_attack_type"] == (
        "benchmark_harness:toy_benchmark_summary_check"
    )
    assert result.estimator_result is not None
    assert (
        result.estimator_result.estimator_name
        == "toy-implementation-security-estimator"
    )
    assert result.estimator_result.time_bits == round(expected_time_bits, 4)
    assert result.estimator_result.memory_bits == round(expected_memory_bits, 4)
    assert result.estimator_result.raw_output == {
        "max_cycles": 1210,
        "max_median_cycles": 1250.0,
        "mean_cycles": 1200.0,
        "median_cycles": 1200.0,
        "metric": "toy_cycles_per_operation",
        "min_cycles": 1190,
        "model": "toy_benchmark_summary_check",
        "sample_count": 5,
        "suite": "toy_mlkem_benchmark",
        "threshold_passed": True,
        "total_cycles": expected_total_cycles,
    }
    assert any("not a performance claim" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_memory_scores_public_summary() -> None:
    plan = _toy_memory_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    total_bytes = _TOY_STACK_BYTES + _TOY_HEAP_BYTES + _TOY_CODE_BYTES
    expected_time_bits = math.log2(total_bytes)
    expected_memory_bits = math.log2(
        max(_TOY_STACK_BYTES, _TOY_HEAP_BYTES, _TOY_CODE_BYTES)
    )

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "IMPLEMENTATION_SECURITY"
    assert result.metrics["feature_attack_type"] == (
        "benchmark_harness:toy_memory_footprint_check"
    )
    assert result.estimator_result is not None
    assert (
        result.estimator_result.estimator_name
        == "toy-implementation-security-estimator"
    )
    assert result.estimator_result.time_bits == round(expected_time_bits, 4)
    assert result.estimator_result.memory_bits == round(expected_memory_bits, 4)
    assert result.estimator_result.raw_output == {
        "code_bytes": _TOY_CODE_BYTES,
        "heap_bytes": _TOY_HEAP_BYTES,
        "max_code_bytes": _TOY_MAX_CODE_BYTES,
        "max_heap_bytes": _TOY_MAX_HEAP_BYTES,
        "max_stack_bytes": _TOY_MAX_STACK_BYTES,
        "metric": "toy_memory_footprint_bytes",
        "model": "toy_memory_footprint_check",
        "stack_bytes": _TOY_STACK_BYTES,
        "suite": "toy_mlkem_memory",
        "threshold_passed": True,
        "total_bytes": total_bytes,
    }
    assert any("not a memory-usage claim" in warning for warning in result.warnings)
    assert any("not a performance claim" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_stack_usage_scores_public_summary() -> None:
    plan = _toy_stack_usage_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    total_stack_bytes = sum(_TOY_STACK_USAGE_SAMPLES)
    max_observed_stack_bytes = max(_TOY_STACK_USAGE_SAMPLES)
    expected_time_bits = math.log2(total_stack_bytes)
    expected_memory_bits = math.log2(max_observed_stack_bytes)

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "IMPLEMENTATION_SECURITY"
    assert result.metrics["feature_attack_type"] == (
        "benchmark_harness:toy_stack_usage_check"
    )
    assert result.estimator_result is not None
    assert (
        result.estimator_result.estimator_name
        == "toy-implementation-security-estimator"
    )
    assert result.estimator_result.time_bits == round(expected_time_bits, 4)
    assert result.estimator_result.memory_bits == round(expected_memory_bits, 4)
    assert result.estimator_result.raw_output == {
        "max_observed_stack_bytes": max_observed_stack_bytes,
        "max_stack_bytes": _TOY_MAX_STACK_USAGE_BYTES,
        "mean_stack_bytes": 1580.8,
        "metric": "toy_stack_usage_bytes",
        "model": "toy_stack_usage_check",
        "sample_count": len(_TOY_STACK_USAGE_SAMPLES),
        "stack_samples": _TOY_STACK_USAGE_SAMPLES,
        "suite": "toy_pqm4_stack_usage",
        "threshold_passed": True,
        "total_stack_bytes": total_stack_bytes,
    }
    assert any("not a stack-usage claim" in warning for warning in result.warnings)
    assert any("not a performance claim" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_binary_size_scores_public_summary() -> None:
    plan = _toy_binary_size_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    total_bytes = (
        _TOY_TEXT_BYTES
        + _TOY_RODATA_BYTES
        + _TOY_DATA_BYTES
        + _TOY_BSS_BYTES
    )
    expected_time_bits = math.log2(total_bytes)
    expected_memory_bits = math.log2(
        max(_TOY_TEXT_BYTES, _TOY_RODATA_BYTES, _TOY_DATA_BYTES, _TOY_BSS_BYTES)
    )

    assert result.valid is True
    assert result.metrics["evaluation_status"] == "ok"
    assert result.metrics["feature_family"] == "IMPLEMENTATION_SECURITY"
    assert result.metrics["feature_attack_type"] == (
        "benchmark_harness:toy_binary_size_check"
    )
    assert result.estimator_result is not None
    assert (
        result.estimator_result.estimator_name
        == "toy-implementation-security-estimator"
    )
    assert result.estimator_result.time_bits == round(expected_time_bits, 4)
    assert result.estimator_result.memory_bits == round(expected_memory_bits, 4)
    assert result.estimator_result.raw_output == {
        "bss_bytes": _TOY_BSS_BYTES,
        "data_bytes": _TOY_DATA_BYTES,
        "max_total_bytes": _TOY_MAX_BINARY_TOTAL_BYTES,
        "metric": "toy_binary_size_bytes",
        "model": "toy_binary_size_check",
        "rodata_bytes": _TOY_RODATA_BYTES,
        "suite": "toy_mlkem_binary_size",
        "text_bytes": _TOY_TEXT_BYTES,
        "threshold_passed": True,
        "total_bytes": total_bytes,
    }
    assert any("not a binary-size claim" in warning for warning in result.warnings)
    assert any("not a performance claim" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_kat_rejects_digest_mismatch() -> None:
    plan = _toy_kat_plan().model_copy(
        update={
            "operators": [
                _toy_kat_plan().operators[0].model_copy(
                    update={
                        "params": {
                            **_toy_kat_plan().operators[0].params,
                            "expected_sha256": "0" * 64,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "expected_sha256 must match SHA-256(payload)" in error
        for error in result.errors
    )


def test_implementation_security_toy_kat_rejects_live_artifact_inputs() -> None:
    plan = _toy_kat_plan().model_copy(
        update={
            "operators": [
                _toy_kat_plan().operators[0].model_copy(
                    update={
                        "params": {
                            **_toy_kat_plan().operators[0].params,
                            "binary_path": "build/mlkem_kat",
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "must not reference executable/live artifact parameter binary_path" in error
        for error in result.errors
    )


def test_implementation_security_toy_timing_rejects_live_trace_inputs() -> None:
    plan = _toy_timing_plan().model_copy(
        update={
            "operators": [
                _toy_timing_plan().operators[0].model_copy(
                    update={
                        "params": {
                            **_toy_timing_plan().operators[0].params,
                            "trace_path": "runs/private/timing.csv",
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "must not reference executable/live artifact parameter trace_path" in error
        for error in result.errors
    )


def test_implementation_security_toy_benchmark_rejects_live_device_inputs() -> None:
    plan = _toy_benchmark_plan().model_copy(
        update={
            "operators": [
                _toy_benchmark_plan().operators[0].model_copy(
                    update={
                        "params": {
                            **_toy_benchmark_plan().operators[0].params,
                            "device_id": "gpu0",
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "must not reference executable/live artifact parameter device_id" in error
        for error in result.errors
    )


def test_implementation_security_toy_kat_rejects_empty_payload() -> None:
    plan = _toy_kat_plan().model_copy(
        update={
            "operators": [
                _toy_kat_plan().operators[0].model_copy(
                    update={
                        "params": {
                            **_toy_kat_plan().operators[0].params,
                            "payload": "",
                            "expected_sha256": hashlib.sha256(b"").hexdigest(),
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any("payload must be non-empty" in error for error in result.errors)


def test_implementation_security_toy_timing_requires_threshold_pass() -> None:
    plan = _toy_timing_plan().model_copy(
        update={
            "operators": [
                _toy_timing_plan().operators[0].model_copy(
                    update={
                        "params": {
                            **_toy_timing_plan().operators[0].params,
                            "max_abs_t": 0.1,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "observed abs t-statistic exceeds max_abs_t" in error
        for error in result.errors
    )


def test_implementation_security_toy_ctgrind_taint_requires_threshold_pass() -> None:
    plan = _toy_ctgrind_taint_plan()
    params = {
        **plan.operators[0].params,
        "secret_dependent_memory_access_count": 1,
    }
    invalid = plan.model_copy(
        update={
            "operators": [
                plan.operators[0].model_copy(update={"params": params}),
            ]
        }
    )

    result = validate_attack_plan(invalid)

    assert result.valid is False
    assert any(
        "secret_dependent_memory_access_count exceeds "
        "max_secret_dependent_memory_access_count" in error
        for error in result.errors
    )


def test_implementation_security_toy_benchmark_requires_assumption() -> None:
    plan = _toy_benchmark_plan().model_copy(
        update={
            "operators": [
                _toy_benchmark_plan().operators[0].model_copy(
                    update={"assumptions": []}
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any("toy_benchmark_summary_model" in error for error in result.errors)


def test_implementation_security_toy_benchmark_requires_threshold_pass() -> None:
    plan = _toy_benchmark_plan().model_copy(
        update={
            "operators": [
                _toy_benchmark_plan().operators[0].model_copy(
                    update={
                        "params": {
                            **_toy_benchmark_plan().operators[0].params,
                            "max_median_cycles": 1000,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "median cycles exceeds max_median_cycles" in error
        for error in result.errors
    )


def test_implementation_security_toy_memory_requires_threshold_pass() -> None:
    plan = _toy_memory_plan().model_copy(
        update={
            "operators": [
                _toy_memory_plan().operators[0].model_copy(
                    update={
                        "params": {
                            **_toy_memory_plan().operators[0].params,
                            "max_stack_bytes": 1024,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "stack_bytes exceeds max_stack_bytes" in error for error in result.errors
    )


def test_implementation_security_toy_stack_usage_requires_threshold_pass() -> None:
    plan = _toy_stack_usage_plan().model_copy(
        update={
            "operators": [
                _toy_stack_usage_plan().operators[0].model_copy(
                    update={
                        "params": {
                            **_toy_stack_usage_plan().operators[0].params,
                            "max_stack_bytes": 1024,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "observed stack usage exceeds max_stack_bytes" in error
        for error in result.errors
    )


def test_implementation_security_toy_binary_size_requires_threshold_pass() -> None:
    plan = _toy_binary_size_plan().model_copy(
        update={
            "operators": [
                _toy_binary_size_plan().operators[0].model_copy(
                    update={
                        "params": {
                            **_toy_binary_size_plan().operators[0].params,
                            "max_total_bytes": 1024,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "total binary size exceeds max_total_bytes" in error
        for error in result.errors
    )


def test_implementation_security_toy_kat_reproduction_verifies_public_fixture() -> None:
    plan = _toy_kat_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/implementation_security_toy_kat/fixtures/"
                    "toy_mlkem_kat_digest_fixture.json"
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
    assert any("not a conformance" in warning for warning in result.warnings)


def test_implementation_security_toy_mldsa_kat_reproduction_verifies_fixture() -> None:
    plan = AttackPlan.model_validate_json(
        Path(
            "examples/attack_plans/implementation_security_mldsa_kat_toy.json"
        ).read_text(encoding="utf-8")
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.metrics["feature_family"] == "IMPLEMENTATION_SECURITY"
    assert result.metrics["feature_attack_type"] == (
        "kat_conformance:toy_kat_digest_match"
    )
    assert result.estimator_result is not None
    assert result.estimator_result.raw_output["suite"] == "toy_mldsa_kat"
    assert result.estimator_result.raw_output["digest_match"] is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not a conformance" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_timing_reproduction_verifies_fixture() -> None:
    plan = _toy_timing_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/implementation_security_toy_timing/fixtures/"
                    "toy_timing_welch_fixture.json"
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
    assert any("not a constant-time" in warning for warning in result.warnings)


def test_implementation_security_toy_dudect_summary_reproduction_verifies_fixture(
) -> None:
    result = CascadeEvaluator().evaluate_plan(_toy_dudect_summary_plan())

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("did not execute dudect" in warning for warning in result.warnings)
    assert any("not a constant-time" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_ctgrind_taint_reproduction_verifies_fixture(
) -> None:
    result = CascadeEvaluator().evaluate_plan(_toy_ctgrind_taint_plan())

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("did not execute ctgrind" in warning for warning in result.warnings)
    assert any("not a constant-time" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_acvp_reproduction_verifies_fixture() -> None:
    plan = _toy_acvp_plan()

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not an ACVP certificate" in warning for warning in result.warnings)


def test_implementation_security_toy_mldsa_acvp_reproduction_verifies_fixture() -> None:
    plan = AttackPlan.model_validate_json(
        Path(
            "examples/attack_plans/implementation_security_mldsa_acvp_toy.json"
        ).read_text(encoding="utf-8")
    )

    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
    assert any("not an ACVP certificate" in warning for warning in result.warnings)
    assert any("not a security claim" in warning for warning in result.warnings)


def test_implementation_security_toy_benchmark_reproduction_verifies_fixture() -> None:
    plan = _toy_benchmark_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/implementation_security_toy_benchmark/fixtures/"
                    "toy_mlkem_benchmark_summary_fixture.json"
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
    assert any("not a performance claim" in warning for warning in result.warnings)


def test_implementation_security_toy_memory_reproduction_verifies_fixture() -> None:
    plan = _toy_memory_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/implementation_security_toy_benchmark/fixtures/"
                    "toy_mlkem_memory_footprint_fixture.json"
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
    assert any("not a memory-usage claim" in warning for warning in result.warnings)
    assert any("not a performance claim" in warning for warning in result.warnings)


def test_toy_stack_usage_reproduction_verifies_fixture() -> None:
    plan = _toy_stack_usage_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/implementation_security_toy_benchmark/fixtures/"
                    "toy_pqm4_stack_usage_fixture.json"
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
    assert any("not a stack-usage claim" in warning for warning in result.warnings)
    assert any("not a performance claim" in warning for warning in result.warnings)


def test_toy_binary_size_reproduction_verifies_fixture() -> None:
    plan = _toy_binary_size_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/implementation_security_toy_benchmark/fixtures/"
                    "toy_mlkem_binary_size_fixture.json"
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
    assert any("not a binary-size claim" in warning for warning in result.warnings)
    assert any("not a performance claim" in warning for warning in result.warnings)


def test_implementation_security_toy_acvp_rejects_digest_mismatch() -> None:
    plan = _toy_acvp_plan().model_copy(
        update={
            "operators": [
                _toy_acvp_plan().operators[0].model_copy(
                    update={
                        "params": {
                            **_toy_acvp_plan().operators[0].params,
                            "expected_vector_set_sha256": "0" * 64,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "expected_vector_set_sha256 must match canonical SHA-256(vector_set)"
        in error
        for error in result.errors
    )


def test_implementation_security_toy_acvp_rejects_unreviewed_algorithm_mode() -> None:
    vector_set = {
        **_TOY_ACVP_MLDSA_VECTOR_SET,
        "mode": "signature-generation",
    }
    digest = _vector_set_digest(vector_set)
    plan = _toy_acvp_mldsa_plan().model_copy(
        update={
            "operators": [
                _toy_acvp_mldsa_plan().operators[0].model_copy(
                    update={
                        "params": {
                            **_toy_acvp_mldsa_plan().operators[0].params,
                            "mode": "signature-generation",
                            "vector_set": vector_set,
                            "expected_vector_set_sha256": digest,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any("algorithm/mode is not reviewed" in error for error in result.errors)
    assert any(
        "ML-DSA/signature-verification" in error for error in result.errors
    )


def test_implementation_security_toy_acvp_rejects_missing_mldsa_signature() -> None:
    first_test = {
        key: value
        for key, value in _TOY_ACVP_MLDSA_VECTOR_SET["testGroups"][0]["tests"][
            0
        ].items()
        if key != "signature"
    }
    vector_set = {
        **_TOY_ACVP_MLDSA_VECTOR_SET,
        "testGroups": [
            {
                **_TOY_ACVP_MLDSA_VECTOR_SET["testGroups"][0],
                "tests": [
                    first_test,
                    _TOY_ACVP_MLDSA_VECTOR_SET["testGroups"][0]["tests"][1],
                ],
            }
        ],
    }
    digest = _vector_set_digest(vector_set)
    plan = _toy_acvp_mldsa_plan().model_copy(
        update={
            "operators": [
                _toy_acvp_mldsa_plan().operators[0].model_copy(
                    update={
                        "params": {
                            **_toy_acvp_mldsa_plan().operators[0].params,
                            "vector_set": vector_set,
                            "expected_vector_set_sha256": digest,
                        }
                    }
                )
            ]
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any("requires non-empty signature" in error for error in result.errors)


def test_implementation_security_toy_kat_reproduction_requires_fixture() -> None:
    plan = _toy_kat_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "requires an explicit public fixture" in error
        for error in result.errors
    )


def test_implementation_security_toy_kat_reproduction_fixture_scope() -> None:
    plan = _toy_kat_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/implementation_security_toy_kat/"
                    "toy_mlkem_kat_digest.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/implementation_security_toy_kat/fixtures/" in error
        for error in result.errors
    )


def test_implementation_security_toy_timing_reproduction_fixture_scope() -> None:
    plan = _toy_timing_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/implementation_security_toy_kat/fixtures/"
                    "toy_mlkem_kat_digest_fixture.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/implementation_security_toy_timing/fixtures/" in error
        for error in result.errors
    )


def test_implementation_security_toy_benchmark_reproduction_fixture_scope() -> None:
    plan = _toy_benchmark_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/implementation_security_toy_timing/fixtures/"
                    "toy_timing_welch_fixture.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/implementation_security_toy_benchmark/fixtures/" in error
        for error in result.errors
    )


def test_implementation_security_toy_kat_reproduction_fixture_traversal() -> None:
    plan = _toy_kat_plan().model_copy(
        update={
            "constraints": Constraints(
                require_reproducibility_on_downscaled_instances=True,
                downscaled_reproduction_fixture=(
                    "benchmarks/implementation_security_toy_kat/fixtures/"
                    "../toy_mlkem_kat_digest_fixture.json"
                ),
            )
        }
    )

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any(
        "benchmarks/implementation_security_toy_kat/fixtures/" in error
        for error in result.errors
    )


_TOY_KAT_PAYLOAD = (
    "toy ML-KEM KAT vector\n"
    "seed=00010203\n"
    "ciphertext=abcdef\n"
    "shared_secret=012345\n"
)
_TOY_KAT_DIGEST = hashlib.sha256(_TOY_KAT_PAYLOAD.encode("utf-8")).hexdigest()
_TOY_FIXED_CYCLES = [100, 101, 99, 100, 102, 98]
_TOY_RANDOM_CYCLES = [101, 100, 100, 102, 99, 101]
_TOY_DUDECT_FIXED_CYCLES = [210, 211, 209, 210, 212, 208, 211, 209]
_TOY_DUDECT_RANDOM_CYCLES = [211, 210, 210, 212, 209, 211, 210, 212]
_TOY_CTGRIND_CHECKED_BLOCKS = 12
_TOY_CTGRIND_SECRET_BRANCH_COUNT = 0
_TOY_CTGRIND_SECRET_MEMORY_ACCESS_COUNT = 0
_TOY_CTGRIND_MAX_SECRET_BRANCH_COUNT = 0
_TOY_CTGRIND_MAX_SECRET_MEMORY_ACCESS_COUNT = 0
_TOY_BENCHMARK_SAMPLES = [1200, 1210, 1190, 1205, 1195]
_TOY_STACK_BYTES = 2048
_TOY_HEAP_BYTES = 1024
_TOY_CODE_BYTES = 8192
_TOY_MAX_STACK_BYTES = 4096
_TOY_MAX_HEAP_BYTES = 2048
_TOY_MAX_CODE_BYTES = 16384
_TOY_STACK_USAGE_SAMPLES = [1536, 1600, 1584, 1616, 1568]
_TOY_MAX_STACK_USAGE_BYTES = 2048
_TOY_TEXT_BYTES = 16384
_TOY_RODATA_BYTES = 4096
_TOY_DATA_BYTES = 1024
_TOY_BSS_BYTES = 2048
_TOY_MAX_BINARY_TOTAL_BYTES = 24576
_TOY_ACVP_VECTOR_SET = {
    "algorithm": "ML-KEM",
    "mode": "encapsulation",
    "revision": "FIPS203-toy",
    "testGroups": [
        {
            "parameterSet": "ML-KEM-512",
            "tests": [
                {
                    "ciphertext": "aabbcc",
                    "seed": "00010203",
                    "sharedSecret": "010203",
                    "tcId": 1,
                },
                {
                    "ciphertext": "ddeeff",
                    "seed": "04050607",
                    "sharedSecret": "102030",
                    "tcId": 2,
                },
            ],
            "tgId": 1,
        }
    ],
}
_TOY_ACVP_DIGEST = hashlib.sha256(
    json.dumps(
        _TOY_ACVP_VECTOR_SET,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
).hexdigest()
_TOY_ACVP_MLDSA_VECTOR_SET = {
    "algorithm": "ML-DSA",
    "mode": "signature-verification",
    "revision": "FIPS204-toy",
    "testGroups": [
        {
            "parameterSet": "ML-DSA-44",
            "tests": [
                {
                    "message": "616761646573",
                    "publicKey": "01020304",
                    "seed": "10111213",
                    "signature": "deadbeefcafebabe",
                    "tcId": 1,
                },
                {
                    "message": "706f73742d7175616e74756d",
                    "publicKey": "05060708",
                    "seed": "14151617",
                    "signature": "0011223344556677",
                    "tcId": 2,
                },
            ],
            "tgId": 1,
        }
    ],
}
_TOY_ACVP_MLDSA_DIGEST = hashlib.sha256(
    json.dumps(
        _TOY_ACVP_MLDSA_VECTOR_SET,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
).hexdigest()


def _vector_set_digest(vector_set: dict) -> str:
    return hashlib.sha256(
        json.dumps(vector_set, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _toy_kat_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="implementation_security_kat_toy_v1",
        target=TargetSpec(
            family=TargetFamily.IMPLEMENTATION_SECURITY,
            name="toy_mlkem_kat_digest",
            support_level=SupportLevel.IMPLEMENTED,
        ),
        operators=[
            AttackOperator(
                type="kat_conformance",
                params={
                    "suite": "toy_mlkem_kat",
                    "model": "toy_kat_digest_match",
                    "payload": _TOY_KAT_PAYLOAD,
                    "expected_sha256": _TOY_KAT_DIGEST,
                    "vector_count": 2,
                },
                assumptions=["toy_kat_digest_manifest_model"],
            )
        ],
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy implementation-security KAT digest check for public "
                "plumbing only; not a conformance or side-channel claim."
            ),
        ),
    )


def _toy_timing_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="implementation_security_timing_toy_v1",
        target=TargetSpec(
            family=TargetFamily.IMPLEMENTATION_SECURITY,
            name="toy_timing_welch_mlkem",
            support_level=SupportLevel.IMPLEMENTED,
        ),
        operators=[
            AttackOperator(
                type="constant_time_check",
                params={
                    "tool": "toy_welch_timing_check",
                    "model": "toy_timing_welch_t_check",
                    "fixed_cycles": _TOY_FIXED_CYCLES,
                    "random_cycles": _TOY_RANDOM_CYCLES,
                    "max_abs_t": 1.0,
                },
                assumptions=["toy_timing_leakage_model"],
            )
        ],
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy implementation-security timing summary check for public "
                "plumbing only; not a constant-time, side-channel, or security claim."
            ),
        ),
    )


def _toy_dudect_summary_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="implementation_security_dudect_summary_toy_v1",
        target=TargetSpec(
            family=TargetFamily.IMPLEMENTATION_SECURITY,
            name="toy_dudect_mlkem_summary",
            support_level=SupportLevel.IMPLEMENTED,
        ),
        operators=[
            AttackOperator(
                type="constant_time_check",
                params={
                    "tool": "toy_dudect_summary_check",
                    "model": "toy_dudect_summary_threshold_check",
                    "dudect_version": "dudect-toy-summary-v0",
                    "fixed_cycles": _TOY_DUDECT_FIXED_CYCLES,
                    "random_cycles": _TOY_DUDECT_RANDOM_CYCLES,
                    "max_abs_t": 1.2,
                },
                assumptions=["toy_dudect_summary_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/implementation_security_toy_timing/fixtures/"
                "toy_dudect_mlkem_summary_fixture.json"
            ),
        ),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy implementation-security dudect-style public summary check "
                "for verifier plumbing only. It does not execute dudect and is "
                "not a constant-time, side-channel, or security claim."
            ),
        ),
    )


def _toy_ctgrind_taint_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="implementation_security_ctgrind_taint_toy_v1",
        target=TargetSpec(
            family=TargetFamily.IMPLEMENTATION_SECURITY,
            name="toy_ctgrind_mlkem_secret_taint",
            support_level=SupportLevel.IMPLEMENTED,
        ),
        operators=[
            AttackOperator(
                type="constant_time_check",
                params={
                    "tool": "toy_ctgrind_secret_taint_summary_check",
                    "model": "toy_ctgrind_secret_taint_summary_check",
                    "ctgrind_version": "ctgrind-toy-summary-v0",
                    "checked_blocks": _TOY_CTGRIND_CHECKED_BLOCKS,
                    "secret_dependent_branch_count": (
                        _TOY_CTGRIND_SECRET_BRANCH_COUNT
                    ),
                    "secret_dependent_memory_access_count": (
                        _TOY_CTGRIND_SECRET_MEMORY_ACCESS_COUNT
                    ),
                    "max_secret_dependent_branch_count": (
                        _TOY_CTGRIND_MAX_SECRET_BRANCH_COUNT
                    ),
                    "max_secret_dependent_memory_access_count": (
                        _TOY_CTGRIND_MAX_SECRET_MEMORY_ACCESS_COUNT
                    ),
                },
                assumptions=["toy_ctgrind_secret_taint_summary_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/implementation_security_toy_timing/fixtures/"
                "toy_ctgrind_mlkem_secret_taint_fixture.json"
            ),
        ),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy implementation-security ctgrind-style public summary "
                "check for verifier plumbing only. It does not execute "
                "ctgrind and is not a constant-time, side-channel, or "
                "security claim."
            ),
        ),
    )


def _toy_acvp_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="implementation_security_acvp_toy_v1",
        target=TargetSpec(
            family=TargetFamily.IMPLEMENTATION_SECURITY,
            name="toy_acvp_mlkem_vector_set",
            support_level=SupportLevel.IMPLEMENTED,
        ),
        operators=[
            AttackOperator(
                type="kat_conformance",
                params={
                    "suite": "toy_acvp_mlkem_encap",
                    "model": "toy_acvp_vector_set_match",
                    "algorithm": "ML-KEM",
                    "mode": "encapsulation",
                    "vector_set": _TOY_ACVP_VECTOR_SET,
                    "expected_vector_set_sha256": _TOY_ACVP_DIGEST,
                    "test_count": 2,
                },
                assumptions=["toy_acvp_json_vector_set_model"],
            )
        ],
        constraints=Constraints(
            require_reproducibility_on_downscaled_instances=True,
            downscaled_reproduction_fixture=(
                "benchmarks/implementation_security_toy_kat/fixtures/"
                "toy_acvp_mlkem_vector_set_fixture.json"
            ),
        ),
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy implementation-security ACVP-like vector-set check for "
                "public plumbing only; not an ACVP certificate, conformance, "
                "side-channel, or security claim."
            ),
        ),
    )


def _toy_acvp_mldsa_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="implementation_security_mldsa_acvp_toy_v1",
        target=TargetSpec(
            family=TargetFamily.IMPLEMENTATION_SECURITY,
            name="toy_acvp_mldsa_vector_set",
            support_level=SupportLevel.IMPLEMENTED,
        ),
        operators=[
            AttackOperator(
                type="kat_conformance",
                params={
                    "suite": "toy_acvp_mldsa_signature",
                    "model": "toy_acvp_vector_set_match",
                    "algorithm": "ML-DSA",
                    "mode": "signature-verification",
                    "vector_set": _TOY_ACVP_MLDSA_VECTOR_SET,
                    "expected_vector_set_sha256": _TOY_ACVP_MLDSA_DIGEST,
                    "test_count": 2,
                },
                assumptions=["toy_acvp_json_vector_set_model"],
            )
        ],
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy implementation-security ML-DSA ACVP-like vector-set check "
                "for public plumbing only; not an ACVP certificate, conformance, "
                "side-channel, or security claim."
            ),
        ),
    )


def _toy_benchmark_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="implementation_security_benchmark_toy_v1",
        target=TargetSpec(
            family=TargetFamily.IMPLEMENTATION_SECURITY,
            name="toy_mlkem_benchmark_summary",
            support_level=SupportLevel.IMPLEMENTED,
        ),
        operators=[
            AttackOperator(
                type="benchmark_harness",
                params={
                    "suite": "toy_mlkem_benchmark",
                    "metric": "toy_cycles_per_operation",
                    "model": "toy_benchmark_summary_check",
                    "samples": _TOY_BENCHMARK_SAMPLES,
                    "max_median_cycles": 1250.0,
                },
                assumptions=["toy_benchmark_summary_model"],
            )
        ],
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy implementation-security benchmark summary check for "
                "public plumbing only; not a performance, conformance, "
                "side-channel, or security claim."
            ),
        ),
    )


def _toy_memory_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="implementation_security_memory_toy_v1",
        target=TargetSpec(
            family=TargetFamily.IMPLEMENTATION_SECURITY,
            name="toy_mlkem_memory_footprint",
            support_level=SupportLevel.IMPLEMENTED,
        ),
        operators=[
            AttackOperator(
                type="benchmark_harness",
                params={
                    "suite": "toy_mlkem_memory",
                    "metric": "toy_memory_footprint_bytes",
                    "model": "toy_memory_footprint_check",
                    "stack_bytes": _TOY_STACK_BYTES,
                    "heap_bytes": _TOY_HEAP_BYTES,
                    "code_bytes": _TOY_CODE_BYTES,
                    "max_stack_bytes": _TOY_MAX_STACK_BYTES,
                    "max_heap_bytes": _TOY_MAX_HEAP_BYTES,
                    "max_code_bytes": _TOY_MAX_CODE_BYTES,
                },
                assumptions=["toy_memory_footprint_model"],
            )
        ],
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy implementation-security memory-footprint summary check "
                "for public plumbing only; not a memory-usage, performance, "
                "conformance, side-channel, or security claim."
            ),
        ),
    )


def _toy_stack_usage_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="implementation_security_stack_usage_toy_v1",
        target=TargetSpec(
            family=TargetFamily.IMPLEMENTATION_SECURITY,
            name="toy_pqm4_stack_usage",
            support_level=SupportLevel.IMPLEMENTED,
        ),
        operators=[
            AttackOperator(
                type="benchmark_harness",
                params={
                    "suite": "toy_pqm4_stack_usage",
                    "metric": "toy_stack_usage_bytes",
                    "model": "toy_stack_usage_check",
                    "stack_samples": _TOY_STACK_USAGE_SAMPLES,
                    "max_stack_bytes": _TOY_MAX_STACK_USAGE_BYTES,
                },
                assumptions=["toy_stack_usage_model"],
            )
        ],
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy implementation-security stack-usage summary check "
                "for public plumbing only; not a stack-usage, performance, "
                "conformance, side-channel, or security claim."
            ),
        ),
    )


def _toy_binary_size_plan() -> AttackPlan:
    return AttackPlan(
        attack_plan_id="implementation_security_binary_size_toy_v1",
        target=TargetSpec(
            family=TargetFamily.IMPLEMENTATION_SECURITY,
            name="toy_mlkem_binary_size",
            support_level=SupportLevel.IMPLEMENTED,
        ),
        operators=[
            AttackOperator(
                type="benchmark_harness",
                params={
                    "suite": "toy_mlkem_binary_size",
                    "metric": "toy_binary_size_bytes",
                    "model": "toy_binary_size_check",
                    "text_bytes": _TOY_TEXT_BYTES,
                    "rodata_bytes": _TOY_RODATA_BYTES,
                    "data_bytes": _TOY_DATA_BYTES,
                    "bss_bytes": _TOY_BSS_BYTES,
                    "max_total_bytes": _TOY_MAX_BINARY_TOTAL_BYTES,
                },
                assumptions=["toy_binary_size_model"],
            )
        ],
        metadata=Metadata(
            created_by="seed",
            public=True,
            notes=(
                "Toy implementation-security binary-size summary check "
                "for public plumbing only; not a binary-size, performance, "
                "conformance, side-channel, or security claim."
            ),
        ),
    )


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _welch_abs_t(left: list[int], right: list[int]) -> float:
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    left_variance = _sample_variance(left, left_mean)
    right_variance = _sample_variance(right, right_mean)
    denominator = math.sqrt(left_variance / len(left) + right_variance / len(right))
    if denominator == 0:
        return 0.0 if left_mean == right_mean else float("inf")
    return abs((left_mean - right_mean) / denominator)


def _sample_variance(values: list[int], mean: float) -> float:
    return sum((value - mean) ** 2 for value in values) / (len(values) - 1)
