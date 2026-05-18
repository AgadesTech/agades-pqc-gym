from __future__ import annotations

import math

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.evaluators.base import EstimatorResult

PRANGE_TOY_VARIANT = "prange_toy"
PRANGE_TOY_ASSUMPTION = "prange_isd_combinatorial_cost_model"
LEE_BRICKELL_TOY_VARIANT = "lee_brickell_toy"
LEE_BRICKELL_TOY_ASSUMPTION = "lee_brickell_isd_partial_enumeration_model"
STERN_TOY_VARIANT = "stern_toy"
STERN_TOY_ASSUMPTION = "stern_isd_partition_collision_cost_model"
DUMER_TOY_VARIANT = "dumer_toy"
DUMER_TOY_ASSUMPTION = "dumer_isd_list_merging_cost_model"
BJMM_TOY_VARIANT = "bjmm_toy"
BJMM_TOY_ASSUMPTION = "bjmm_isd_representation_merge_model"
QC_ROTATION_TOY_VARIANT = "qc_rotation_toy"
QC_ROTATION_TOY_ASSUMPTION = "toy_qc_syndrome_rotation_model"


class ToyCodeBasedISDEstimator:
    """Conservative toy ISD-style work-factor models for public plumbing."""

    estimator_name = "toy-code-based-isd-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _isd_operator(plan)
        variant = operator.params["variant"]
        if variant == LEE_BRICKELL_TOY_VARIANT:
            return _estimate_lee_brickell_toy(plan, operator)
        if variant == STERN_TOY_VARIANT:
            return _estimate_stern_toy(plan, operator)
        if variant == DUMER_TOY_VARIANT:
            return _estimate_dumer_toy(plan, operator)
        if variant == BJMM_TOY_VARIANT:
            return _estimate_bjmm_toy(plan, operator)
        if variant == QC_ROTATION_TOY_VARIANT:
            return _estimate_qc_rotation_toy(plan, operator)
        if variant != PRANGE_TOY_VARIANT:
            raise ValueError(f"unsupported CODE_BASED toy ISD variant: {variant}")

        n = _required_int(plan.target.n, "n")
        k = _required_int(plan.target.k, "k")
        w = _required_int(plan.target.w, "w")
        redundancy = n - k

        attempts_bits = _log2_binomial(n, w) - _log2_binomial(redundancy, w)
        linear_algebra_overhead_bits = math.log2(n)
        weight_overhead_bits = math.log2(w + 1)
        time_bits = attempts_bits + linear_algebra_overhead_bits + weight_overhead_bits
        memory_bits = linear_algebra_overhead_bits + weight_overhead_bits

        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            evaluation_status="ok",
            attack_type=f"{operator.type}:{variant}",
            time_bits=round(time_bits, 4),
            memory_bits=round(memory_bits, 4),
            success_probability=None,
            raw_output={
                "model": "prange_information_set_decoding_toy",
                "n": n,
                "k": k,
                "w": w,
                "redundancy": redundancy,
                "attempts_bits": round(attempts_bits, 4),
                "linear_algebra_overhead_bits": round(
                    linear_algebra_overhead_bits, 4
                ),
                "weight_overhead_bits": round(weight_overhead_bits, 4),
            },
            warnings=[
                "Toy Prange ISD output is for public evaluator plumbing only; "
                "it is not a security claim."
            ],
        )


def _estimate_lee_brickell_toy(
    plan: AttackPlan,
    operator: AttackOperator,
) -> EstimatorResult:
    n = _required_int(plan.target.n, "n")
    k = _required_int(plan.target.k, "k")
    w = _required_int(plan.target.w, "w")
    p = _required_int(operator.params.get("p"), "p")
    redundancy = n - k
    redundancy_errors = w - p

    attempts_bits = (
        _log2_binomial(n, w)
        - _log2_binomial(k, p)
        - _log2_binomial(redundancy, redundancy_errors)
    )
    enumeration_bits = _log2_binomial(k, p)
    linear_algebra_bits = math.log2(n)
    syndrome_filter_bits = math.log2(redundancy + 1)
    time_bits = (
        attempts_bits
        + enumeration_bits
        + linear_algebra_bits
        + syndrome_filter_bits
    )
    memory_bits = math.log2(math.comb(k, p) + n)

    return EstimatorResult(
        estimator_name=ToyCodeBasedISDEstimator.estimator_name,
        estimator_version=ToyCodeBasedISDEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{LEE_BRICKELL_TOY_VARIANT}",
        time_bits=round(time_bits, 4),
        memory_bits=round(memory_bits, 4),
        success_probability=None,
        raw_output={
            "attempts_bits": round(attempts_bits, 4),
            "enumeration_bits": round(enumeration_bits, 4),
            "information_set_errors": p,
            "linear_algebra_bits": round(linear_algebra_bits, 4),
            "model": "lee_brickell_information_set_decoding_toy",
            "n": n,
            "k": k,
            "p": p,
            "redundancy": redundancy,
            "redundancy_errors": redundancy_errors,
            "syndrome_filter_bits": round(syndrome_filter_bits, 4),
            "w": w,
        },
        warnings=[
            "Toy Lee-Brickell-style ISD output is for public evaluator "
            "plumbing only; it is not a security claim."
        ],
    )


def _estimate_stern_toy(plan: AttackPlan, operator: AttackOperator) -> EstimatorResult:
    n = _required_int(plan.target.n, "n")
    k = _required_int(plan.target.k, "k")
    w = _required_int(plan.target.w, "w")
    p = _required_int(operator.params.get("p"), "p")
    redundancy = n - k
    information_set_errors = 2 * p
    redundancy_errors = w - information_set_errors
    left_dimension = k // 2
    right_dimension = k - left_dimension

    attempts_bits = (
        _log2_binomial(n, w)
        - _log2_binomial(k, information_set_errors)
        - _log2_binomial(redundancy, redundancy_errors)
    )
    left_list_bits = _log2_binomial(left_dimension, p)
    right_list_bits = _log2_binomial(right_dimension, p)
    collision_list_bits = math.log2(
        math.comb(left_dimension, p) + math.comb(right_dimension, p)
    )
    syndrome_filter_bits = math.log2(redundancy + 1)
    time_bits = attempts_bits + max(left_list_bits, right_list_bits)
    time_bits += syndrome_filter_bits

    return EstimatorResult(
        estimator_name=ToyCodeBasedISDEstimator.estimator_name,
        estimator_version=ToyCodeBasedISDEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{STERN_TOY_VARIANT}",
        time_bits=round(time_bits, 4),
        memory_bits=round(collision_list_bits, 4),
        success_probability=None,
        raw_output={
            "model": "stern_information_set_decoding_toy",
            "n": n,
            "k": k,
            "w": w,
            "p": p,
            "redundancy": redundancy,
            "information_set_errors": information_set_errors,
            "redundancy_errors": redundancy_errors,
            "left_list_bits": round(left_list_bits, 4),
            "right_list_bits": round(right_list_bits, 4),
            "collision_list_bits": round(collision_list_bits, 4),
            "attempts_bits": round(attempts_bits, 4),
            "syndrome_filter_bits": round(syndrome_filter_bits, 4),
        },
        warnings=[
            "Toy Stern-style ISD output is for public evaluator plumbing only; "
            "it is not a security claim."
        ],
    )


def _estimate_dumer_toy(plan: AttackPlan, operator: AttackOperator) -> EstimatorResult:
    n = _required_int(plan.target.n, "n")
    k = _required_int(plan.target.k, "k")
    w = _required_int(plan.target.w, "w")
    p = _required_int(operator.params.get("p"), "p")
    ell = _required_int(operator.params.get("ell"), "ell")
    redundancy = n - k
    information_set_errors = 2 * p
    redundancy_errors = w - information_set_errors
    left_dimension = k // 2
    right_dimension = k - left_dimension

    attempts_bits = (
        _log2_binomial(n, w)
        - _log2_binomial(k, information_set_errors)
        - _log2_binomial(redundancy, redundancy_errors)
    )
    left_list_bits = _log2_binomial(left_dimension, p)
    right_list_bits = _log2_binomial(right_dimension, p)
    list_build_bits = _logsumexp2([left_list_bits, right_list_bits])
    merge_bits = max(0.0, left_list_bits + right_list_bits - ell)
    syndrome_check_bits = math.log2(redundancy - ell + 1)
    memory_bits = _logsumexp2([left_list_bits, right_list_bits, merge_bits])
    time_bits = attempts_bits + list_build_bits + merge_bits + syndrome_check_bits

    return EstimatorResult(
        estimator_name=ToyCodeBasedISDEstimator.estimator_name,
        estimator_version=ToyCodeBasedISDEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{DUMER_TOY_VARIANT}",
        time_bits=round(time_bits, 4),
        memory_bits=round(memory_bits, 4),
        success_probability=None,
        raw_output={
            "model": "dumer_information_set_decoding_toy",
            "n": n,
            "k": k,
            "w": w,
            "p": p,
            "ell": ell,
            "redundancy": redundancy,
            "information_set_errors": information_set_errors,
            "redundancy_errors": redundancy_errors,
            "left_list_bits": round(left_list_bits, 4),
            "right_list_bits": round(right_list_bits, 4),
            "list_build_bits": round(list_build_bits, 4),
            "merge_filter_bits": ell,
            "merge_bits": round(merge_bits, 4),
            "attempts_bits": round(attempts_bits, 4),
            "syndrome_check_bits": round(syndrome_check_bits, 4),
        },
        warnings=[
            "Toy Dumer-style ISD list-merging output is for public evaluator "
            "plumbing only; it is not a security claim."
        ],
    )


def _estimate_bjmm_toy(plan: AttackPlan, operator: AttackOperator) -> EstimatorResult:
    n = _required_int(plan.target.n, "n")
    k = _required_int(plan.target.k, "k")
    w = _required_int(plan.target.w, "w")
    p = _required_int(operator.params.get("p"), "p")
    ell = _required_int(operator.params.get("ell"), "ell")
    representation_count = _required_int(
        operator.params.get("representation_count"),
        "representation_count",
    )
    redundancy = n - k
    information_set_errors = 2 * p
    redundancy_errors = w - information_set_errors
    left_dimension = k // 2
    right_dimension = k - left_dimension

    attempts_bits = (
        _log2_binomial(n, w)
        - _log2_binomial(k, information_set_errors)
        - _log2_binomial(redundancy, redundancy_errors)
    )
    left_list_bits = _log2_binomial(left_dimension, p)
    right_list_bits = _log2_binomial(right_dimension, p)
    list_build_bits = _logsumexp2([left_list_bits, right_list_bits])
    representation_gain_bits = math.log2(representation_count)
    merge_bits = max(
        0.0,
        left_list_bits + right_list_bits - ell - representation_gain_bits,
    )
    syndrome_check_bits = math.log2(redundancy - ell + 1)
    memory_bits = _logsumexp2([left_list_bits, right_list_bits, merge_bits])
    time_bits = (
        attempts_bits
        + list_build_bits
        + merge_bits
        + syndrome_check_bits
        + representation_gain_bits
    )

    return EstimatorResult(
        estimator_name=ToyCodeBasedISDEstimator.estimator_name,
        estimator_version=ToyCodeBasedISDEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{BJMM_TOY_VARIANT}",
        time_bits=round(time_bits, 4),
        memory_bits=round(memory_bits, 4),
        success_probability=None,
        raw_output={
            "attempts_bits": round(attempts_bits, 4),
            "ell": ell,
            "information_set_errors": information_set_errors,
            "k": k,
            "left_list_bits": round(left_list_bits, 4),
            "list_build_bits": round(list_build_bits, 4),
            "merge_bits": round(merge_bits, 4),
            "merge_filter_bits": ell,
            "model": "bjmm_information_set_decoding_toy",
            "n": n,
            "p": p,
            "redundancy": redundancy,
            "redundancy_errors": redundancy_errors,
            "representation_count": representation_count,
            "representation_gain_bits": round(representation_gain_bits, 4),
            "right_list_bits": round(right_list_bits, 4),
            "syndrome_check_bits": round(syndrome_check_bits, 4),
            "w": w,
        },
        warnings=[
            "Toy BJMM-style ISD representation-merge output is for public "
            "evaluator plumbing only; it is not a security claim."
        ],
    )


def _estimate_qc_rotation_toy(
    plan: AttackPlan,
    operator: AttackOperator,
) -> EstimatorResult:
    n = _required_int(plan.target.n, "n")
    k = _required_int(plan.target.k, "k")
    w = _required_int(plan.target.w, "w")
    block_size = _required_int(operator.params.get("block_size"), "block_size")
    block_count = _required_int(operator.params.get("block_count"), "block_count")
    if n != block_size * block_count:
        raise ValueError(
            "CODE_BASED qc_rotation_toy requires n == block_size * block_count"
        )

    rotation_count = block_size
    rotation_search_bits = math.log2(rotation_count)
    syndrome_update_bits = math.log2(n)
    weight_overhead_bits = math.log2(w + 1)
    time_bits = rotation_search_bits + syndrome_update_bits + weight_overhead_bits
    memory_bits = math.log2(block_size) + weight_overhead_bits

    return EstimatorResult(
        estimator_name=ToyCodeBasedISDEstimator.estimator_name,
        estimator_version=ToyCodeBasedISDEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{QC_ROTATION_TOY_VARIANT}",
        time_bits=round(time_bits, 4),
        memory_bits=round(memory_bits, 4),
        success_probability=None,
        raw_output={
            "model": "quasi_cyclic_rotation_search_toy",
            "n": n,
            "k": k,
            "w": w,
            "block_size": block_size,
            "block_count": block_count,
            "rotation_count": rotation_count,
            "rotation_search_bits": round(rotation_search_bits, 4),
            "syndrome_update_bits": round(syndrome_update_bits, 4),
            "weight_overhead_bits": round(weight_overhead_bits, 4),
        },
        warnings=[
            "Toy quasi-cyclic rotation output is for public evaluator plumbing "
            "only; it is not an HQC result and not a security claim."
        ],
    )


def _isd_operator(plan: AttackPlan) -> AttackOperator:
    for operator in plan.operators:
        if operator.type == "information_set_decoding":
            return operator
    raise ValueError("CODE_BASED estimate requires information_set_decoding")


def _required_int(value: int | None, name: str) -> int:
    if value is None:
        raise ValueError(f"CODE_BASED target requires {name}")
    return value


def _log2_binomial(n: int, k: int) -> float:
    if k < 0 or k > n:
        raise ValueError(f"invalid binomial parameters: n={n}, k={k}")
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
    ) / math.log(2)


def _logsumexp2(values: list[float]) -> float:
    if not values:
        raise ValueError("logsumexp requires at least one value")
    max_value = max(values)
    return max_value + math.log2(sum(2 ** (value - max_value) for value in values))
