from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.evaluators.base import EstimatorResult

TOY_KAT_MODEL = "toy_kat_digest_match"
TOY_KAT_ASSUMPTION = "toy_kat_digest_manifest_model"
TOY_KAT_MAX_PAYLOAD_BYTES = 512
TOY_KAT_MAX_VECTOR_COUNT = 16
TOY_ACVP_MODEL = "toy_acvp_vector_set_match"
TOY_ACVP_ASSUMPTION = "toy_acvp_json_vector_set_model"
TOY_ACVP_MAX_GROUPS = 4
TOY_ACVP_MAX_TESTS = 16
TOY_ACVP_MAX_VECTOR_SET_BYTES = 2048
TOY_ACVP_MAX_FIELD_BYTES = 64
TOY_ACVP_REQUIRED_TEST_FIELDS_BY_ALGORITHM_MODE = {
    ("ML-DSA", "signature-verification"): frozenset(
        {"message", "publicKey", "seed", "signature"}
    ),
    ("ML-KEM", "encapsulation"): frozenset(
        {"ciphertext", "seed", "sharedSecret"}
    ),
}
TOY_TIMING_TOOL = "toy_welch_timing_check"
TOY_TIMING_MODEL = "toy_timing_welch_t_check"
TOY_TIMING_ASSUMPTION = "toy_timing_leakage_model"
TOY_DUDECT_SUMMARY_TOOL = "toy_dudect_summary_check"
TOY_DUDECT_SUMMARY_MODEL = "toy_dudect_summary_threshold_check"
TOY_DUDECT_SUMMARY_ASSUMPTION = "toy_dudect_summary_model"
TOY_DUDECT_SUMMARY_CLASSIFICATION = "toy_threshold_not_exceeded"
TOY_CTGRIND_TAINT_TOOL = "toy_ctgrind_secret_taint_summary_check"
TOY_CTGRIND_TAINT_MODEL = "toy_ctgrind_secret_taint_summary_check"
TOY_CTGRIND_TAINT_ASSUMPTION = "toy_ctgrind_secret_taint_summary_model"
TOY_CTGRIND_TAINT_CLASSIFICATION = "toy_no_secret_taint_observed"
TOY_CTGRIND_MAX_CHECKED_BLOCKS = 1024
TOY_CTGRIND_MAX_SECRET_DEPENDENT_COUNT = 1024
TOY_TIMING_MIN_SAMPLES = 2
TOY_TIMING_MAX_SAMPLES = 64
TOY_TIMING_MAX_CYCLE_VALUE = 1_000_000
TOY_BENCHMARK_METRIC = "toy_cycles_per_operation"
TOY_BENCHMARK_MODEL = "toy_benchmark_summary_check"
TOY_BENCHMARK_ASSUMPTION = "toy_benchmark_summary_model"
TOY_BENCHMARK_MIN_SAMPLES = 2
TOY_BENCHMARK_MAX_SAMPLES = 64
TOY_BENCHMARK_MAX_CYCLE_VALUE = 1_000_000
TOY_MEMORY_METRIC = "toy_memory_footprint_bytes"
TOY_MEMORY_MODEL = "toy_memory_footprint_check"
TOY_MEMORY_ASSUMPTION = "toy_memory_footprint_model"
TOY_MEMORY_MAX_BYTES = 1_000_000
TOY_STACK_USAGE_METRIC = "toy_stack_usage_bytes"
TOY_STACK_USAGE_MODEL = "toy_stack_usage_check"
TOY_STACK_USAGE_ASSUMPTION = "toy_stack_usage_model"
TOY_STACK_USAGE_MIN_SAMPLES = 2
TOY_STACK_USAGE_MAX_SAMPLES = 64
TOY_BINARY_SIZE_METRIC = "toy_binary_size_bytes"
TOY_BINARY_SIZE_MODEL = "toy_binary_size_check"
TOY_BINARY_SIZE_ASSUMPTION = "toy_binary_size_model"
TOY_BINARY_SIZE_MAX_BYTES = 2_000_000
TOY_KAT_SAMPLE_PAYLOAD = (
    "toy ML-KEM KAT vector\n"
    "seed=00010203\n"
    "ciphertext=abcdef\n"
    "shared_secret=012345\n"
)
TOY_KAT_SAMPLE_DIGEST = hashlib.sha256(
    TOY_KAT_SAMPLE_PAYLOAD.encode("utf-8")
).hexdigest()


class ToyImplementationSecurityEstimator:
    """Toy implementation-security checks for JSON-only public verifier plumbing."""

    estimator_name = "toy-implementation-security-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _implemented_operator(plan)
        if operator.type == "kat_conformance":
            if operator.params.get("model") == TOY_ACVP_MODEL:
                return self._estimate_acvp_toy(operator)
            return self._estimate_kat(operator)
        if operator.type == "constant_time_check":
            return self._estimate_timing_toy(operator)
        if operator.type == "benchmark_harness":
            return self._estimate_benchmark_toy(operator)
        raise ValueError(
            "IMPLEMENTATION_SECURITY estimate requires kat_conformance, "
            "constant_time_check, or benchmark_harness"
        )

    def _estimate_kat(self, operator: AttackOperator) -> EstimatorResult:
        suite = required_str(operator.params, "suite", "toy KAT")
        payload = required_str(operator.params, "payload", "toy KAT")
        expected_sha256 = required_str(operator.params, "expected_sha256", "toy KAT")
        vector_count = required_int(operator.params, "vector_count", "toy KAT")

        payload_bytes = len(payload.encode("utf-8"))
        payload_sha256 = payload_sha256_hex(payload)
        check_cost_bits = math.log2(payload_bytes + vector_count)
        memory_bits = math.log2(payload_bytes)

        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            evaluation_status="ok",
            attack_type=f"{operator.type}:{operator.params['model']}",
            time_bits=round(check_cost_bits, 4),
            memory_bits=round(memory_bits, 4),
            success_probability=None,
            raw_output={
                "digest_match": payload_sha256 == expected_sha256,
                "expected_sha256": expected_sha256,
                "model": TOY_KAT_MODEL,
                "payload_bytes": payload_bytes,
                "payload_sha256": payload_sha256,
                "suite": suite,
                "vector_count": vector_count,
            },
            warnings=[
                "Toy implementation-security KAT output is for public verifier "
                "plumbing only; it is not a security claim."
            ],
        )

    def _estimate_acvp_toy(self, operator: AttackOperator) -> EstimatorResult:
        suite = required_str(operator.params, "suite", "toy ACVP")
        algorithm = required_str(operator.params, "algorithm", "toy ACVP")
        mode = required_str(operator.params, "mode", "toy ACVP")
        expected_vector_set_sha256 = required_str(
            operator.params,
            "expected_vector_set_sha256",
            "toy ACVP",
        )
        test_count = required_int(operator.params, "test_count", "toy ACVP")
        vector_set = required_dict(operator.params, "vector_set", "toy ACVP")
        summary = analyze_toy_acvp_vector_set(vector_set, algorithm, mode)

        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            evaluation_status="ok",
            attack_type=f"{operator.type}:{operator.params['model']}",
            time_bits=round(
                math.log2(
                    summary.vector_set_bytes
                    + summary.test_group_count
                    + summary.test_count
                ),
                4,
            ),
            memory_bits=round(math.log2(summary.vector_set_bytes), 4),
            success_probability=None,
            raw_output={
                "algorithm": algorithm,
                "digest_match": (
                    summary.vector_set_sha256 == expected_vector_set_sha256
                ),
                "expected_vector_set_sha256": expected_vector_set_sha256,
                "mode": mode,
                "model": TOY_ACVP_MODEL,
                "suite": suite,
                "test_count": test_count,
                "test_group_count": summary.test_group_count,
                "vector_set_bytes": summary.vector_set_bytes,
                "vector_set_sha256": summary.vector_set_sha256,
            },
            warnings=[
                "Toy implementation-security ACVP vector-set output is for "
                "public verifier plumbing only; it is not an ACVP certificate, "
                "not a conformance result, and not a security claim."
            ],
        )

    def _estimate_timing_toy(self, operator: AttackOperator) -> EstimatorResult:
        if operator.params.get("model") == TOY_DUDECT_SUMMARY_MODEL:
            return self._estimate_dudect_summary_toy(operator)
        if operator.params.get("model") == TOY_CTGRIND_TAINT_MODEL:
            return self._estimate_ctgrind_taint_toy(operator)
        if (
            operator.params.get("tool") != TOY_TIMING_TOOL
            or operator.params.get("model") != TOY_TIMING_MODEL
        ):
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy timing requires the reviewed "
                f"{TOY_TIMING_TOOL}/{TOY_TIMING_MODEL} pair"
            )
        fixed_cycles = required_cycle_list(operator.params, "fixed_cycles")
        random_cycles = required_cycle_list(operator.params, "random_cycles")
        max_abs_t = required_positive_number(operator.params, "max_abs_t")

        fixed_mean = mean(fixed_cycles)
        random_mean = mean(random_cycles)
        observed_abs_t = welch_abs_t(fixed_cycles, random_cycles)
        threshold_passed = observed_abs_t <= max_abs_t
        if not threshold_passed:
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy timing observed abs t-statistic "
                "exceeds max_abs_t"
            )

        sample_count = len(fixed_cycles) + len(random_cycles)
        memory_samples = max(len(fixed_cycles), len(random_cycles))
        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            evaluation_status="ok",
            attack_type=f"{operator.type}:{operator.params['model']}",
            time_bits=round(math.log2(sample_count), 4),
            memory_bits=round(math.log2(memory_samples), 4),
            success_probability=None,
            raw_output={
                "fixed_mean_cycles": round(fixed_mean, 4),
                "fixed_sample_count": len(fixed_cycles),
                "max_abs_t": max_abs_t,
                "model": TOY_TIMING_MODEL,
                "observed_abs_t": round(observed_abs_t, 4),
                "random_mean_cycles": round(random_mean, 4),
                "random_sample_count": len(random_cycles),
                "threshold_passed": threshold_passed,
                "tool": TOY_TIMING_TOOL,
            },
            warnings=[
                "Toy implementation-security timing output is for public verifier "
                "plumbing only; it is not a constant-time result, not a "
                "side-channel result, and not a security claim."
            ],
        )

    def _estimate_dudect_summary_toy(
        self,
        operator: AttackOperator,
    ) -> EstimatorResult:
        if (
            operator.params.get("tool") != TOY_DUDECT_SUMMARY_TOOL
            or operator.params.get("model") != TOY_DUDECT_SUMMARY_MODEL
        ):
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy dudect summary requires the "
                f"reviewed {TOY_DUDECT_SUMMARY_TOOL}/"
                f"{TOY_DUDECT_SUMMARY_MODEL} pair"
            )
        dudect_version = required_str(
            operator.params,
            "dudect_version",
            "toy dudect summary",
        )
        if not dudect_version:
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy dudect summary requires non-empty "
                "dudect_version"
            )
        fixed_cycles = required_cycle_list(operator.params, "fixed_cycles")
        random_cycles = required_cycle_list(operator.params, "random_cycles")
        max_abs_t = required_positive_number(operator.params, "max_abs_t")

        fixed_mean = mean(fixed_cycles)
        random_mean = mean(random_cycles)
        observed_abs_t = welch_abs_t(fixed_cycles, random_cycles)
        threshold_passed = observed_abs_t <= max_abs_t
        if not threshold_passed:
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy dudect summary observed abs "
                "t-statistic exceeds max_abs_t"
            )

        sample_count = len(fixed_cycles) + len(random_cycles)
        memory_samples = max(len(fixed_cycles), len(random_cycles))
        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            evaluation_status="ok",
            attack_type=f"{operator.type}:{operator.params['model']}",
            time_bits=round(math.log2(sample_count), 4),
            memory_bits=round(math.log2(memory_samples), 4),
            success_probability=None,
            raw_output={
                "classification": TOY_DUDECT_SUMMARY_CLASSIFICATION,
                "constant_time_claim": False,
                "dudect_execution": False,
                "dudect_version": dudect_version,
                "fixed_mean_cycles": round(fixed_mean, 4),
                "fixed_sample_count": len(fixed_cycles),
                "max_abs_t": max_abs_t,
                "model": TOY_DUDECT_SUMMARY_MODEL,
                "observed_abs_t": round(observed_abs_t, 4),
                "random_mean_cycles": round(random_mean, 4),
                "random_sample_count": len(random_cycles),
                "threshold_passed": threshold_passed,
                "tool": TOY_DUDECT_SUMMARY_TOOL,
            },
            warnings=[
                "Toy implementation-security dudect summary output is for "
                "public verifier plumbing only; it did not execute dudect, "
                "is not a constant-time result, not a side-channel result, "
                "and not a security claim."
            ],
        )

    def _estimate_ctgrind_taint_toy(
        self,
        operator: AttackOperator,
    ) -> EstimatorResult:
        if (
            operator.params.get("tool") != TOY_CTGRIND_TAINT_TOOL
            or operator.params.get("model") != TOY_CTGRIND_TAINT_MODEL
        ):
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy ctgrind secret-taint summary "
                f"requires the reviewed {TOY_CTGRIND_TAINT_TOOL}/"
                f"{TOY_CTGRIND_TAINT_MODEL} pair"
            )
        ctgrind_version = required_str(
            operator.params,
            "ctgrind_version",
            "toy ctgrind secret-taint summary",
        )
        if not ctgrind_version:
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy ctgrind secret-taint summary "
                "requires non-empty ctgrind_version"
            )
        checked_blocks = required_ctgrind_checked_blocks(operator.params)
        secret_branch_count = required_ctgrind_taint_count(
            operator.params,
            "secret_dependent_branch_count",
        )
        secret_memory_count = required_ctgrind_taint_count(
            operator.params,
            "secret_dependent_memory_access_count",
        )
        max_secret_branch_count = required_ctgrind_taint_count(
            operator.params,
            "max_secret_dependent_branch_count",
        )
        max_secret_memory_count = required_ctgrind_taint_count(
            operator.params,
            "max_secret_dependent_memory_access_count",
        )

        branch_threshold_passed = secret_branch_count <= max_secret_branch_count
        memory_threshold_passed = secret_memory_count <= max_secret_memory_count
        threshold_passed = branch_threshold_passed and memory_threshold_passed
        if not branch_threshold_passed:
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy ctgrind secret-taint summary "
                "secret_dependent_branch_count exceeds "
                "max_secret_dependent_branch_count"
            )
        if not memory_threshold_passed:
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy ctgrind secret-taint summary "
                "secret_dependent_memory_access_count exceeds "
                "max_secret_dependent_memory_access_count"
            )

        memory_units = max(
            secret_branch_count,
            secret_memory_count,
            max_secret_branch_count,
            max_secret_memory_count,
        )
        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            evaluation_status="ok",
            attack_type=f"{operator.type}:{operator.params['model']}",
            time_bits=round(
                math.log2(
                    checked_blocks
                    + secret_branch_count
                    + secret_memory_count
                    + 1
                ),
                4,
            ),
            memory_bits=round(math.log2(memory_units + 1), 4),
            success_probability=None,
            raw_output={
                "artifact_execution": False,
                "checked_blocks": checked_blocks,
                "classification": TOY_CTGRIND_TAINT_CLASSIFICATION,
                "constant_time_claim": False,
                "ctgrind_execution": False,
                "ctgrind_version": ctgrind_version,
                "max_secret_dependent_branch_count": max_secret_branch_count,
                "max_secret_dependent_memory_access_count": max_secret_memory_count,
                "model": TOY_CTGRIND_TAINT_MODEL,
                "secret_dependent_branch_count": secret_branch_count,
                "secret_dependent_memory_access_count": secret_memory_count,
                "security_claim": False,
                "threshold_passed": threshold_passed,
                "tool": TOY_CTGRIND_TAINT_TOOL,
            },
            warnings=[
                "Toy implementation-security ctgrind secret-taint summary "
                "output is for public verifier plumbing only; it did not "
                "execute ctgrind, is not a constant-time result, not a "
                "side-channel result, and not a security claim."
            ],
        )

    def _estimate_benchmark_toy(self, operator: AttackOperator) -> EstimatorResult:
        if operator.params.get("model") == TOY_BINARY_SIZE_MODEL:
            return self._estimate_binary_size_toy(operator)
        if operator.params.get("model") == TOY_MEMORY_MODEL:
            return self._estimate_memory_toy(operator)
        if operator.params.get("model") == TOY_STACK_USAGE_MODEL:
            return self._estimate_stack_usage_toy(operator)

        suite = required_str(operator.params, "suite", "toy benchmark")
        metric = required_str(operator.params, "metric", "toy benchmark")
        samples = required_benchmark_samples(operator.params, "samples")
        max_median_cycles = required_benchmark_threshold(
            operator.params,
            "max_median_cycles",
        )

        sample_count = len(samples)
        total_cycles = sum(samples)
        median_value = median(samples)
        mean_value = mean(samples)
        threshold_passed = median_value <= max_median_cycles
        if not threshold_passed:
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy benchmark median cycles exceeds "
                "max_median_cycles"
            )

        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            evaluation_status="ok",
            attack_type=f"{operator.type}:{operator.params['model']}",
            time_bits=round(math.log2(total_cycles), 4),
            memory_bits=round(math.log2(sample_count), 4),
            success_probability=None,
            raw_output={
                "max_cycles": max(samples),
                "max_median_cycles": max_median_cycles,
                "mean_cycles": round(mean_value, 4),
                "median_cycles": round(median_value, 4),
                "metric": metric,
                "min_cycles": min(samples),
                "model": TOY_BENCHMARK_MODEL,
                "sample_count": sample_count,
                "suite": suite,
                "threshold_passed": threshold_passed,
                "total_cycles": total_cycles,
            },
            warnings=[
                "Toy implementation-security benchmark output is for public "
                "verifier plumbing only; it is not a performance claim, not "
                "a conformance result, and not a security claim."
            ],
        )

    def _estimate_binary_size_toy(self, operator: AttackOperator) -> EstimatorResult:
        suite = required_str(operator.params, "suite", "toy binary size")
        metric = required_str(operator.params, "metric", "toy binary size")
        text_bytes = required_binary_size_bytes(operator.params, "text_bytes")
        rodata_bytes = required_binary_size_bytes(operator.params, "rodata_bytes")
        data_bytes = required_binary_size_bytes(operator.params, "data_bytes")
        bss_bytes = required_binary_size_bytes(operator.params, "bss_bytes")
        max_total_bytes = required_binary_size_threshold(
            operator.params,
            "max_total_bytes",
        )
        total_bytes = text_bytes + rodata_bytes + data_bytes + bss_bytes
        if total_bytes <= 0:
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy binary size requires positive "
                "total bytes"
            )
        threshold_passed = total_bytes <= max_total_bytes
        if not threshold_passed:
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy binary size total binary size "
                "exceeds max_total_bytes"
            )

        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            evaluation_status="ok",
            attack_type=f"{operator.type}:{operator.params['model']}",
            time_bits=round(math.log2(total_bytes), 4),
            memory_bits=round(
                math.log2(max(text_bytes, rodata_bytes, data_bytes, bss_bytes)),
                4,
            ),
            success_probability=None,
            raw_output={
                "bss_bytes": bss_bytes,
                "data_bytes": data_bytes,
                "max_total_bytes": max_total_bytes,
                "metric": metric,
                "model": TOY_BINARY_SIZE_MODEL,
                "rodata_bytes": rodata_bytes,
                "suite": suite,
                "text_bytes": text_bytes,
                "threshold_passed": threshold_passed,
                "total_bytes": total_bytes,
            },
            warnings=[
                "Toy implementation-security binary-size output is for public "
                "verifier plumbing only; it is not a binary-size claim, not a "
                "performance claim, not a conformance result, and not a "
                "security claim."
            ],
        )

    def _estimate_stack_usage_toy(self, operator: AttackOperator) -> EstimatorResult:
        suite = required_str(operator.params, "suite", "toy stack usage")
        metric = required_str(operator.params, "metric", "toy stack usage")
        stack_samples = required_stack_samples(operator.params, "stack_samples")
        max_stack_bytes = required_memory_threshold(
            operator.params,
            "max_stack_bytes",
        )

        total_stack_bytes = sum(stack_samples)
        max_observed_stack_bytes = max(stack_samples)
        threshold_passed = max_observed_stack_bytes <= max_stack_bytes
        if not threshold_passed:
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy stack usage observed stack usage "
                "exceeds max_stack_bytes"
            )

        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            evaluation_status="ok",
            attack_type=f"{operator.type}:{operator.params['model']}",
            time_bits=round(math.log2(total_stack_bytes), 4),
            memory_bits=round(math.log2(max_observed_stack_bytes), 4),
            success_probability=None,
            raw_output={
                "max_observed_stack_bytes": max_observed_stack_bytes,
                "max_stack_bytes": max_stack_bytes,
                "mean_stack_bytes": round(mean(stack_samples), 4),
                "metric": metric,
                "model": TOY_STACK_USAGE_MODEL,
                "sample_count": len(stack_samples),
                "stack_samples": stack_samples,
                "suite": suite,
                "threshold_passed": threshold_passed,
                "total_stack_bytes": total_stack_bytes,
            },
            warnings=[
                "Toy implementation-security stack-usage output is for public "
                "verifier plumbing only; it is not a stack-usage claim, not a "
                "performance claim, not a conformance result, not a "
                "side-channel result, and not a security claim."
            ],
        )

    def _estimate_memory_toy(self, operator: AttackOperator) -> EstimatorResult:
        suite = required_str(operator.params, "suite", "toy memory")
        metric = required_str(operator.params, "metric", "toy memory")
        stack_bytes = required_memory_bytes(operator.params, "stack_bytes")
        heap_bytes = required_memory_bytes(operator.params, "heap_bytes")
        code_bytes = required_memory_bytes(operator.params, "code_bytes")
        max_stack_bytes = required_memory_threshold(
            operator.params,
            "max_stack_bytes",
        )
        max_heap_bytes = required_memory_threshold(
            operator.params,
            "max_heap_bytes",
        )
        max_code_bytes = required_memory_threshold(
            operator.params,
            "max_code_bytes",
        )
        total_bytes = stack_bytes + heap_bytes + code_bytes
        if total_bytes <= 0:
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy memory requires positive total bytes"
            )
        threshold_passed = (
            stack_bytes <= max_stack_bytes
            and heap_bytes <= max_heap_bytes
            and code_bytes <= max_code_bytes
        )
        if not threshold_passed:
            raise ValueError(
                "IMPLEMENTATION_SECURITY toy memory footprint exceeds threshold"
            )

        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            evaluation_status="ok",
            attack_type=f"{operator.type}:{operator.params['model']}",
            time_bits=round(math.log2(total_bytes), 4),
            memory_bits=round(math.log2(max(stack_bytes, heap_bytes, code_bytes)), 4),
            success_probability=None,
            raw_output={
                "code_bytes": code_bytes,
                "heap_bytes": heap_bytes,
                "max_code_bytes": max_code_bytes,
                "max_heap_bytes": max_heap_bytes,
                "max_stack_bytes": max_stack_bytes,
                "metric": metric,
                "model": TOY_MEMORY_MODEL,
                "stack_bytes": stack_bytes,
                "suite": suite,
                "threshold_passed": threshold_passed,
                "total_bytes": total_bytes,
            },
            warnings=[
                "Toy implementation-security memory-footprint output is for "
                "public verifier plumbing only; it is not a memory-usage claim, "
                "not a performance claim, not a conformance result, and not a "
                "security claim."
            ],
        )


ToyImplementationSecurityKATEstimator = ToyImplementationSecurityEstimator


@dataclass(frozen=True)
class ToyACVPVectorSetSummary:
    canonical_json: str
    vector_set_sha256: str
    vector_set_bytes: int
    test_group_count: int
    test_count: int


def _implemented_operator(plan: AttackPlan) -> AttackOperator:
    for operator in plan.operators:
        if operator.type in {
            "kat_conformance",
            "constant_time_check",
            "benchmark_harness",
        }:
            return operator
    raise ValueError(
        "IMPLEMENTATION_SECURITY estimate requires kat_conformance, "
        "constant_time_check, or benchmark_harness"
    )


def _kat_operator(plan: AttackPlan) -> AttackOperator:
    for operator in plan.operators:
        if operator.type == "kat_conformance":
            return operator
    raise ValueError("IMPLEMENTATION_SECURITY estimate requires kat_conformance")


def payload_sha256(payload: str) -> str:
    return payload_sha256_hex(payload)


def payload_sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def required_str(params: dict[str, Any], name: str, surface: str = "toy") -> str:
    value = params.get(name)
    if not isinstance(value, str):
        raise ValueError(f"IMPLEMENTATION_SECURITY {surface} requires {name}")
    return value


def required_int(params: dict[str, Any], name: str, surface: str = "toy") -> int:
    value = params.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"IMPLEMENTATION_SECURITY {surface} requires {name}")
    return value


def required_dict(params: dict[str, Any], name: str, surface: str = "toy") -> dict:
    value = params.get(name)
    if not isinstance(value, dict):
        raise ValueError(f"IMPLEMENTATION_SECURITY {surface} requires {name}")
    return value


def required_cycle_list(params: dict[str, Any], name: str) -> list[int]:
    value = params.get(name)
    if not isinstance(value, list):
        raise ValueError(f"IMPLEMENTATION_SECURITY toy timing requires {name}")
    if not TOY_TIMING_MIN_SAMPLES <= len(value) <= TOY_TIMING_MAX_SAMPLES:
        raise ValueError(
            "IMPLEMENTATION_SECURITY toy timing requires "
            f"{TOY_TIMING_MIN_SAMPLES} <= {name} samples <= "
            f"{TOY_TIMING_MAX_SAMPLES}"
        )
    if any(not isinstance(item, int) or isinstance(item, bool) for item in value):
        raise ValueError(
            f"IMPLEMENTATION_SECURITY toy timing requires integer {name} samples"
        )
    if any(item < 0 or item > TOY_TIMING_MAX_CYCLE_VALUE for item in value):
        raise ValueError(
            "IMPLEMENTATION_SECURITY toy timing cycle samples must be between "
            f"0 and {TOY_TIMING_MAX_CYCLE_VALUE}"
        )
    return value


def required_benchmark_samples(params: dict[str, Any], name: str) -> list[int]:
    value = params.get(name)
    if not isinstance(value, list):
        raise ValueError(f"IMPLEMENTATION_SECURITY toy benchmark requires {name}")
    if not TOY_BENCHMARK_MIN_SAMPLES <= len(value) <= TOY_BENCHMARK_MAX_SAMPLES:
        raise ValueError(
            "IMPLEMENTATION_SECURITY toy benchmark requires "
            f"{TOY_BENCHMARK_MIN_SAMPLES} <= {name} samples <= "
            f"{TOY_BENCHMARK_MAX_SAMPLES}"
        )
    if any(not isinstance(item, int) or isinstance(item, bool) for item in value):
        raise ValueError(
            f"IMPLEMENTATION_SECURITY toy benchmark requires integer {name} samples"
        )
    if any(item <= 0 or item > TOY_BENCHMARK_MAX_CYCLE_VALUE for item in value):
        raise ValueError(
            "IMPLEMENTATION_SECURITY toy benchmark cycle samples must be between "
            f"1 and {TOY_BENCHMARK_MAX_CYCLE_VALUE}"
        )
    return value


def required_positive_number(params: dict[str, Any], name: str) -> float:
    value = params.get(name)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"IMPLEMENTATION_SECURITY toy timing requires {name}")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(
            f"IMPLEMENTATION_SECURITY toy timing requires positive finite {name}"
        )
    return number


def required_ctgrind_checked_blocks(params: dict[str, Any]) -> int:
    return required_bounded_int(
        params,
        "checked_blocks",
        "toy ctgrind secret-taint summary",
        minimum=1,
        maximum=TOY_CTGRIND_MAX_CHECKED_BLOCKS,
    )


def required_ctgrind_taint_count(params: dict[str, Any], name: str) -> int:
    return required_bounded_int(
        params,
        name,
        "toy ctgrind secret-taint summary",
        minimum=0,
        maximum=TOY_CTGRIND_MAX_SECRET_DEPENDENT_COUNT,
    )


def required_bounded_int(
    params: dict[str, Any],
    name: str,
    surface: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    value = required_int(params, name, surface)
    if not minimum <= value <= maximum:
        raise ValueError(
            f"IMPLEMENTATION_SECURITY {surface} requires {minimum} <= "
            f"{name} <= {maximum}"
        )
    return value


def required_benchmark_threshold(params: dict[str, Any], name: str) -> float:
    value = params.get(name)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"IMPLEMENTATION_SECURITY toy benchmark requires {name}")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(
            f"IMPLEMENTATION_SECURITY toy benchmark requires positive finite {name}"
        )
    return number


def required_memory_bytes(params: dict[str, Any], name: str) -> int:
    value = params.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"IMPLEMENTATION_SECURITY toy memory requires {name}")
    if value < 0 or value > TOY_MEMORY_MAX_BYTES:
        raise ValueError(
            "IMPLEMENTATION_SECURITY toy memory byte counts must be between "
            f"0 and {TOY_MEMORY_MAX_BYTES}"
        )
    return value


def required_memory_threshold(params: dict[str, Any], name: str) -> int:
    value = params.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"IMPLEMENTATION_SECURITY toy memory requires {name}")
    if value <= 0 or value > TOY_MEMORY_MAX_BYTES:
        raise ValueError(
            "IMPLEMENTATION_SECURITY toy memory thresholds must be between "
            f"1 and {TOY_MEMORY_MAX_BYTES}"
        )
    return value


def required_stack_samples(params: dict[str, Any], name: str) -> list[int]:
    value = params.get(name)
    if not isinstance(value, list):
        raise ValueError(
            f"IMPLEMENTATION_SECURITY toy stack usage requires {name}"
        )
    if not TOY_STACK_USAGE_MIN_SAMPLES <= len(value) <= TOY_STACK_USAGE_MAX_SAMPLES:
        raise ValueError(
            "IMPLEMENTATION_SECURITY toy stack usage requires "
            f"{TOY_STACK_USAGE_MIN_SAMPLES} <= {name} samples <= "
            f"{TOY_STACK_USAGE_MAX_SAMPLES}"
        )
    if any(not isinstance(item, int) or isinstance(item, bool) for item in value):
        raise ValueError(
            f"IMPLEMENTATION_SECURITY toy stack usage requires integer {name} samples"
        )
    if any(item <= 0 or item > TOY_MEMORY_MAX_BYTES for item in value):
        raise ValueError(
            "IMPLEMENTATION_SECURITY toy stack usage samples must be between "
            f"1 and {TOY_MEMORY_MAX_BYTES}"
        )
    return value


def required_binary_size_bytes(params: dict[str, Any], name: str) -> int:
    value = params.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(
            f"IMPLEMENTATION_SECURITY toy binary size requires {name}"
        )
    if value < 0 or value > TOY_BINARY_SIZE_MAX_BYTES:
        raise ValueError(
            "IMPLEMENTATION_SECURITY toy binary size byte counts must be between "
            f"0 and {TOY_BINARY_SIZE_MAX_BYTES}"
        )
    return value


def required_binary_size_threshold(params: dict[str, Any], name: str) -> int:
    value = params.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(
            f"IMPLEMENTATION_SECURITY toy binary size requires {name}"
        )
    if value <= 0 or value > TOY_BINARY_SIZE_MAX_BYTES:
        raise ValueError(
            "IMPLEMENTATION_SECURITY toy binary size thresholds must be between "
            f"1 and {TOY_BINARY_SIZE_MAX_BYTES}"
        )
    return value


def mean(values: list[int]) -> float:
    return sum(values) / len(values)


def median(values: list[int]) -> float:
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return float(sorted_values[midpoint])
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2.0


def welch_abs_t(left: list[int], right: list[int]) -> float:
    left_mean = mean(left)
    right_mean = mean(right)
    left_variance = sample_variance(left, left_mean)
    right_variance = sample_variance(right, right_mean)
    denominator = math.sqrt(left_variance / len(left) + right_variance / len(right))
    if denominator == 0:
        return 0.0 if left_mean == right_mean else float("inf")
    return abs((left_mean - right_mean) / denominator)


def sample_variance(values: list[int], center: float) -> float:
    return sum((value - center) ** 2 for value in values) / (len(values) - 1)


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def analyze_toy_acvp_vector_set(
    vector_set: dict,
    algorithm: str,
    mode: str,
) -> ToyACVPVectorSetSummary:
    if vector_set.get("algorithm") != algorithm:
        raise ValueError("toy ACVP vector_set algorithm must match operator")
    if vector_set.get("mode") != mode:
        raise ValueError("toy ACVP vector_set mode must match operator")
    if not isinstance(vector_set.get("revision"), str) or not vector_set["revision"]:
        raise ValueError("toy ACVP vector_set requires non-empty revision")

    groups = vector_set.get("testGroups")
    if not isinstance(groups, list) or not groups:
        raise ValueError("toy ACVP vector_set requires non-empty testGroups")
    if len(groups) > TOY_ACVP_MAX_GROUPS:
        raise ValueError(
            "toy ACVP vector_set exceeds public test group limit: "
            f"{TOY_ACVP_MAX_GROUPS}"
        )

    test_count = 0
    tc_ids: set[int] = set()
    for group in groups:
        if not isinstance(group, dict):
            raise ValueError("toy ACVP testGroups entries must be objects")
        if not _positive_int(group.get("tgId")):
            raise ValueError("toy ACVP test group requires positive tgId")
        if (
            not isinstance(group.get("parameterSet"), str)
            or not group["parameterSet"]
        ):
            raise ValueError("toy ACVP test group requires parameterSet")
        tests = group.get("tests")
        if not isinstance(tests, list) or not tests:
            raise ValueError("toy ACVP test group requires non-empty tests")
        test_count += len(tests)
        if test_count > TOY_ACVP_MAX_TESTS:
            raise ValueError(
                "toy ACVP vector_set exceeds public test count limit: "
                f"{TOY_ACVP_MAX_TESTS}"
            )
        for test in tests:
            if not isinstance(test, dict):
                raise ValueError("toy ACVP tests entries must be objects")
            tc_id = test.get("tcId")
            if not _positive_int(tc_id):
                raise ValueError("toy ACVP test requires positive tcId")
            if tc_id in tc_ids:
                raise ValueError("toy ACVP tcId values must be unique")
            tc_ids.add(tc_id)
            for field in _required_toy_acvp_test_fields(algorithm, mode):
                _validate_toy_acvp_hex_field(test, field)

    encoded = canonical_json(vector_set).encode("utf-8")
    if len(encoded) > TOY_ACVP_MAX_VECTOR_SET_BYTES:
        raise ValueError(
            "toy ACVP vector_set exceeds public byte limit: "
            f"{TOY_ACVP_MAX_VECTOR_SET_BYTES}"
        )
    digest = hashlib.sha256(encoded).hexdigest()
    return ToyACVPVectorSetSummary(
        canonical_json=encoded.decode("utf-8"),
        vector_set_sha256=digest,
        vector_set_bytes=len(encoded),
        test_group_count=len(groups),
        test_count=test_count,
    )


def _validate_toy_acvp_hex_field(test: dict, field: str) -> None:
    value = test.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"toy ACVP test requires non-empty {field}")
    if value != value.lower():
        raise ValueError(f"toy ACVP {field} must be lowercase hex")
    if len(value) % 2 != 0:
        raise ValueError(f"toy ACVP {field} must contain whole bytes")
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"toy ACVP {field} must be hex") from exc
    if len(value) // 2 > TOY_ACVP_MAX_FIELD_BYTES:
        raise ValueError(
            f"toy ACVP {field} exceeds public byte limit: "
            f"{TOY_ACVP_MAX_FIELD_BYTES}"
        )


def _required_toy_acvp_test_fields(algorithm: str, mode: str) -> tuple[str, ...]:
    required_fields = TOY_ACVP_REQUIRED_TEST_FIELDS_BY_ALGORITHM_MODE.get(
        (algorithm, mode)
    )
    if required_fields is None:
        supported = ", ".join(
            f"{supported_algorithm}/{supported_mode}"
            for supported_algorithm, supported_mode in sorted(
                TOY_ACVP_REQUIRED_TEST_FIELDS_BY_ALGORITHM_MODE
            )
        )
        raise ValueError(
            "toy ACVP vector_set algorithm/mode is not reviewed; supported "
            f"toy pairs: {supported}"
        )
    return tuple(sorted(required_fields))


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
