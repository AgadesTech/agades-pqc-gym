from __future__ import annotations

import math

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.evaluators.base import EstimatorResult

CLASSIC_MCELIECE_SYNDROME_TOY_VARIANT = "classic_mceliece_syndrome_toy"
CLASSIC_MCELIECE_SYNDROME_TOY_ASSUMPTION = (
    "toy_classic_mceliece_syndrome_decoder_model"
)
CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_VARIANT = (
    "classic_mceliece_support_syndrome_toy"
)
CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_ASSUMPTION = (
    "toy_classic_mceliece_support_syndrome_decoder_model"
)
MAX_CLASSIC_MCELIECE_SUPPORT_SIZE = 64


class ToyCodeBasedClassicMcElieceSyndromeEstimator:
    """Bounded binary-syndrome decoder cost model for public fixture plumbing."""

    estimator_name = "toy-code-based-classic-mceliece-syndrome-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _decoding_fixture_operator(plan)
        variant = operator.params["variant"]
        if variant != CLASSIC_MCELIECE_SYNDROME_TOY_VARIANT:
            raise ValueError(
                f"unsupported CODE_BASED decoding fixture variant: {variant}"
            )

        n = _required_int(plan.target.n, "n")
        k = _required_int(plan.target.k, "k")
        w = _required_int(plan.target.w, "w")
        max_error_weight = _required_int(
            operator.params.get("max_error_weight"),
            "max_error_weight",
        )
        if max_error_weight != w:
            raise ValueError(
                "CODE_BASED classic_mceliece_syndrome_toy requires "
                "max_error_weight == w"
            )
        if k >= n:
            raise ValueError(
                "CODE_BASED classic_mceliece_syndrome_toy requires k < n"
            )

        parity_check_rows = n - k
        candidate_count = math.comb(n, w)
        time_bits = math.log2(candidate_count) + math.log2(
            max(1, parity_check_rows * w)
        )
        memory_bits = math.log2(n + parity_check_rows + w)

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
                "candidate_count": candidate_count,
                "k": k,
                "max_error_weight": max_error_weight,
                "model": "toy_classic_mceliece_binary_syndrome_decode",
                "n": n,
                "parity_check_rows": parity_check_rows,
                "w": w,
            },
            warnings=[
                "Toy Classic-McEliece-inspired binary syndrome decoder output "
                "is for public evaluator plumbing only; it is not a Classic "
                "McEliece result and not a security claim."
            ],
        )


class ToyCodeBasedClassicMcElieceSupportSyndromeEstimator:
    """Bounded public support-set syndrome decoder for toy fixtures."""

    estimator_name = "toy-code-based-classic-mceliece-support-syndrome-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _decoding_fixture_operator(plan)
        variant = operator.params["variant"]
        if variant != CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_VARIANT:
            raise ValueError(
                f"unsupported CODE_BASED decoding fixture variant: {variant}"
            )

        n = _required_int(plan.target.n, "n")
        k = _required_int(plan.target.k, "k")
        w = _required_int(plan.target.w, "w")
        max_error_weight = _required_int(
            operator.params.get("max_error_weight"),
            "max_error_weight",
        )
        support_size = _required_int(
            operator.params.get("support_size"),
            "support_size",
        )
        if max_error_weight != w:
            raise ValueError(
                "CODE_BASED classic_mceliece_support_syndrome_toy requires "
                "max_error_weight == w"
            )
        if k >= n:
            raise ValueError(
                "CODE_BASED classic_mceliece_support_syndrome_toy requires k < n"
            )
        if support_size < max_error_weight:
            raise ValueError(
                "CODE_BASED classic_mceliece_support_syndrome_toy requires "
                "support_size >= max_error_weight"
            )
        if support_size > MAX_CLASSIC_MCELIECE_SUPPORT_SIZE:
            raise ValueError(
                "CODE_BASED classic_mceliece_support_syndrome_toy requires "
                f"support_size <= {MAX_CLASSIC_MCELIECE_SUPPORT_SIZE}"
            )

        parity_check_rows = n - k
        candidate_count = math.comb(support_size, max_error_weight)
        time_bits = math.log2(candidate_count) + math.log2(
            max(1, parity_check_rows * w)
        )
        memory_bits = math.log2(n + parity_check_rows + support_size + w)

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
                "candidate_count": candidate_count,
                "k": k,
                "max_error_weight": max_error_weight,
                "model": "toy_classic_mceliece_support_syndrome_decode",
                "n": n,
                "parity_check_rows": parity_check_rows,
                "support_size": support_size,
                "w": w,
            },
            warnings=[
                "Toy Classic-McEliece-inspired public support-set syndrome "
                "decoder output is for public evaluator plumbing only; it is "
                "not a Classic McEliece result and not a security claim."
            ],
        )


def _decoding_fixture_operator(plan: AttackPlan) -> AttackOperator:
    for operator in plan.operators:
        if operator.type == "decoding_fixture_check":
            return operator
    raise ValueError("CODE_BASED estimate requires decoding_fixture_check")


def _required_int(value: int | None, name: str) -> int:
    if value is None:
        raise ValueError(f"CODE_BASED target requires {name}")
    return value
