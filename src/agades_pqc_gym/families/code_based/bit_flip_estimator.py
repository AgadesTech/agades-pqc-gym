from __future__ import annotations

import math

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.evaluators.base import EstimatorResult

MDPC_BIT_FLIP_TOY_VARIANT = "mdpc_bit_flip_toy"
MDPC_BIT_FLIP_TOY_ASSUMPTION = "toy_mdpc_bit_flip_decoder_model"
MDPC_BLACK_GRAY_TOY_VARIANT = "mdpc_black_gray_bit_flip_toy"
MDPC_BLACK_GRAY_TOY_ASSUMPTION = "toy_mdpc_black_gray_bit_flip_decoder_model"
MDPC_SYNDROME_WEIGHT_TOY_VARIANT = "mdpc_syndrome_weight_bit_flip_toy"
MDPC_SYNDROME_WEIGHT_TOY_ASSUMPTION = (
    "toy_mdpc_syndrome_weight_bit_flip_decoder_model"
)


class ToyCodeBasedBitFlipDecoderEstimator:
    """Tiny MDPC-style bit-flip decoder cost model for public fixture plumbing."""

    estimator_name = "toy-code-based-bit-flip-decoder-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _decoding_fixture_operator(plan)
        variant = operator.params["variant"]
        if variant == MDPC_BIT_FLIP_TOY_VARIANT:
            return _estimate_threshold_bit_flip(plan, operator)
        if variant == MDPC_BLACK_GRAY_TOY_VARIANT:
            return _estimate_black_gray_bit_flip(plan, operator)
        if variant == MDPC_SYNDROME_WEIGHT_TOY_VARIANT:
            return _estimate_syndrome_weight_bit_flip(plan, operator)
        raise ValueError(
            f"unsupported CODE_BASED bit-flip fixture variant: {variant}"
        )


def _estimate_threshold_bit_flip(
    plan: AttackPlan,
    operator: AttackOperator,
) -> EstimatorResult:
    n = _required_int(plan.target.n, "n")
    k = _required_int(plan.target.k, "k")
    w = _required_int(plan.target.w, "w")
    threshold = _required_int(operator.params.get("threshold"), "threshold")
    max_iterations = _required_int(
        operator.params.get("max_iterations"),
        "max_iterations",
    )
    if k >= n:
        raise ValueError("CODE_BASED mdpc_bit_flip_toy requires k < n")

    parity_check_rows = n - k
    bit_checks = max_iterations * parity_check_rows * n
    time_bits = math.log2(bit_checks)
    memory_bits = math.log2(n + parity_check_rows + w)

    return EstimatorResult(
        estimator_name=ToyCodeBasedBitFlipDecoderEstimator.estimator_name,
        estimator_version=ToyCodeBasedBitFlipDecoderEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{operator.params['variant']}",
        time_bits=round(time_bits, 4),
        memory_bits=round(memory_bits, 4),
        success_probability=None,
        raw_output={
            "bit_checks": bit_checks,
            "k": k,
            "max_iterations": max_iterations,
            "model": "toy_mdpc_bit_flip_decode",
            "n": n,
            "parity_check_rows": parity_check_rows,
            "threshold": threshold,
            "w": w,
        },
        warnings=[
            "Toy MDPC/BIKE-inspired bit-flip decoder output is for public "
            "evaluator plumbing only; it is not a BIKE result and not a "
            "security claim."
        ],
    )


def _estimate_black_gray_bit_flip(
    plan: AttackPlan,
    operator: AttackOperator,
) -> EstimatorResult:
    n = _required_int(plan.target.n, "n")
    k = _required_int(plan.target.k, "k")
    w = _required_int(plan.target.w, "w")
    black_threshold = _required_int(
        operator.params.get("black_threshold"),
        "black_threshold",
    )
    gray_threshold = _required_int(
        operator.params.get("gray_threshold"),
        "gray_threshold",
    )
    max_iterations = _required_int(
        operator.params.get("max_iterations"),
        "max_iterations",
    )
    if k >= n:
        raise ValueError("CODE_BASED mdpc_black_gray_bit_flip_toy requires k < n")
    if gray_threshold > black_threshold:
        raise ValueError(
            "CODE_BASED mdpc_black_gray_bit_flip_toy requires "
            "gray_threshold <= black_threshold"
        )

    parity_check_rows = n - k
    syndrome_products = max_iterations * (1 + n)
    bit_checks = syndrome_products * parity_check_rows * n
    time_bits = math.log2(bit_checks)
    memory_bits = math.log2(n + parity_check_rows + w + 2)

    return EstimatorResult(
        estimator_name=ToyCodeBasedBitFlipDecoderEstimator.estimator_name,
        estimator_version=ToyCodeBasedBitFlipDecoderEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{operator.params['variant']}",
        time_bits=round(time_bits, 4),
        memory_bits=round(memory_bits, 4),
        success_probability=None,
        raw_output={
            "bit_checks": bit_checks,
            "black_threshold": black_threshold,
            "gray_threshold": gray_threshold,
            "k": k,
            "max_iterations": max_iterations,
            "model": "toy_mdpc_black_gray_bit_flip_decode",
            "n": n,
            "parity_check_rows": parity_check_rows,
            "syndrome_products": syndrome_products,
            "w": w,
        },
        warnings=[
            "Toy MDPC/BIKE-inspired black-gray bit-flip decoder output is for "
            "public evaluator plumbing only; it is not a BIKE result and not "
            "a security claim."
        ],
    )


def _estimate_syndrome_weight_bit_flip(
    plan: AttackPlan,
    operator: AttackOperator,
) -> EstimatorResult:
    n = _required_int(plan.target.n, "n")
    k = _required_int(plan.target.k, "k")
    w = _required_int(plan.target.w, "w")
    min_syndrome_weight_drop = _required_int(
        operator.params.get("min_syndrome_weight_drop"),
        "min_syndrome_weight_drop",
    )
    max_iterations = _required_int(
        operator.params.get("max_iterations"),
        "max_iterations",
    )
    if k >= n:
        raise ValueError(
            "CODE_BASED mdpc_syndrome_weight_bit_flip_toy requires k < n"
        )

    parity_check_rows = n - k
    syndrome_bit_checks = max_iterations * n * parity_check_rows
    time_bits = math.log2(syndrome_bit_checks)
    memory_bits = math.log2(n + parity_check_rows + w + min_syndrome_weight_drop)

    return EstimatorResult(
        estimator_name=ToyCodeBasedBitFlipDecoderEstimator.estimator_name,
        estimator_version=ToyCodeBasedBitFlipDecoderEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{operator.params['variant']}",
        time_bits=round(time_bits, 4),
        memory_bits=round(memory_bits, 4),
        success_probability=None,
        raw_output={
            "k": k,
            "max_iterations": max_iterations,
            "min_syndrome_weight_drop": min_syndrome_weight_drop,
            "model": "toy_mdpc_syndrome_weight_bit_flip_decode",
            "n": n,
            "parity_check_rows": parity_check_rows,
            "syndrome_bit_checks": syndrome_bit_checks,
            "w": w,
        },
        warnings=[
            "Toy MDPC/BIKE-inspired syndrome-weight bit-flip decoder output "
            "is for public evaluator plumbing only; it is not a BIKE result "
            "and not a security claim."
        ],
    )


def _decoding_fixture_operator(plan: AttackPlan) -> AttackOperator:
    for operator in plan.operators:
        if operator.type == "decoding_fixture_check":
            return operator
    raise ValueError("CODE_BASED bit-flip estimate requires decoding_fixture_check")


def _required_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"CODE_BASED bit-flip target requires {name}")
    return value
