from __future__ import annotations

import math

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.evaluators.base import EstimatorResult

HQC_REPETITION_TOY_VARIANT = "hqc_repetition_toy"
HQC_REPETITION_TOY_ASSUMPTION = "toy_hqc_repetition_decoder_model"
HQC_WEIGHTED_REPETITION_TOY_VARIANT = "hqc_weighted_repetition_toy"
HQC_WEIGHTED_REPETITION_TOY_ASSUMPTION = (
    "toy_hqc_weighted_repetition_decoder_model"
)
MAX_HQC_WEIGHTED_REPETITION_RELIABILITY = 16
HQC_PARITY_CHECK_TOY_VARIANT = "hqc_parity_check_toy"
HQC_PARITY_CHECK_TOY_ASSUMPTION = "toy_hqc_parity_check_decoder_model"
HQC_CIRCULANT_SYNDROME_TOY_VARIANT = "hqc_circulant_syndrome_toy"
HQC_CIRCULANT_SYNDROME_TOY_ASSUMPTION = (
    "toy_hqc_circulant_syndrome_decoder_model"
)
HQC_CIRCULANT_ERASURE_TOY_VARIANT = "hqc_circulant_erasure_toy"
HQC_CIRCULANT_ERASURE_TOY_ASSUMPTION = (
    "toy_hqc_circulant_erasure_decoder_model"
)
HQC_ERASURE_SYNDROME_TOY_VARIANT = "hqc_erasure_syndrome_toy"
HQC_ERASURE_SYNDROME_TOY_ASSUMPTION = (
    "toy_hqc_erasure_syndrome_decoder_model"
)
MAX_HQC_ERASURE_COUNT = 64


class ToyCodeBasedRepetitionDecoderEstimator:
    """Tiny repetition-code decoder cost model for public fixture plumbing."""

    estimator_name = "toy-code-based-repetition-decoder-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _decoding_fixture_operator(plan)
        variant = operator.params["variant"]
        if variant != HQC_REPETITION_TOY_VARIANT:
            raise ValueError(
                f"unsupported CODE_BASED decoding fixture variant: {variant}"
            )

        n = _required_int(plan.target.n, "n")
        k = _required_int(plan.target.k, "k")
        w = _required_int(plan.target.w, "w")
        repetition_factor = _required_int(
            operator.params.get("repetition_factor"),
            "repetition_factor",
        )
        if n != k * repetition_factor:
            raise ValueError(
                "CODE_BASED hqc_repetition_toy requires "
                "n == k * repetition_factor"
            )

        vote_operations = k * repetition_factor
        time_bits = math.log2(vote_operations)
        memory_bits = math.log2(n + k)

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
                "model": "toy_hqc_repetition_majority_decode",
                "n": n,
                "k": k,
                "w": w,
                "repetition_factor": repetition_factor,
                "vote_operations": vote_operations,
            },
            warnings=[
                "Toy HQC-inspired repetition-code decoder output is for "
                "public evaluator plumbing only; it is not an HQC result and "
                "not a security claim."
            ],
        )


class ToyCodeBasedWeightedRepetitionDecoderEstimator:
    """Tiny weighted repetition-code decoder model for public fixture plumbing."""

    estimator_name = "toy-code-based-weighted-repetition-decoder-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _decoding_fixture_operator(plan)
        variant = operator.params["variant"]
        if variant != HQC_WEIGHTED_REPETITION_TOY_VARIANT:
            raise ValueError(
                f"unsupported CODE_BASED decoding fixture variant: {variant}"
            )

        n = _required_int(plan.target.n, "n")
        k = _required_int(plan.target.k, "k")
        w = _required_int(plan.target.w, "w")
        repetition_factor = _required_int(
            operator.params.get("repetition_factor"),
            "repetition_factor",
        )
        max_reliability_weight = _required_int(
            operator.params.get("max_reliability_weight"),
            "max_reliability_weight",
        )
        if n != k * repetition_factor:
            raise ValueError(
                "CODE_BASED hqc_weighted_repetition_toy requires "
                "n == k * repetition_factor"
            )
        if max_reliability_weight > MAX_HQC_WEIGHTED_REPETITION_RELIABILITY:
            raise ValueError(
                "CODE_BASED hqc_weighted_repetition_toy requires "
                "max_reliability_weight <= "
                f"{MAX_HQC_WEIGHTED_REPETITION_RELIABILITY}"
            )

        accumulator_bits = math.ceil(
            math.log2(repetition_factor * max_reliability_weight + 1)
        )
        weighted_vote_operations = k * repetition_factor
        time_bits = math.log2(weighted_vote_operations * accumulator_bits)
        memory_bits = math.log2(n + k + max_reliability_weight)

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
                "accumulator_bits": accumulator_bits,
                "k": k,
                "max_reliability_weight": max_reliability_weight,
                "model": "toy_hqc_weighted_repetition_decode",
                "n": n,
                "repetition_factor": repetition_factor,
                "w": w,
                "weighted_vote_operations": weighted_vote_operations,
            },
            warnings=[
                "Toy HQC-inspired weighted repetition-code decoder output is "
                "for public evaluator plumbing only; it is not an HQC result "
                "and not a security claim."
            ],
        )


class ToyCodeBasedParityCheckDecoderEstimator:
    """Bounded toy parity-check decoder cost model for public fixture plumbing."""

    estimator_name = "toy-code-based-parity-check-decoder-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _decoding_fixture_operator(plan)
        variant = operator.params["variant"]
        if variant != HQC_PARITY_CHECK_TOY_VARIANT:
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
                "CODE_BASED hqc_parity_check_toy requires max_error_weight == w"
            )
        if k >= n:
            raise ValueError("CODE_BASED hqc_parity_check_toy requires k < n")

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
                "model": "toy_hqc_parity_check_syndrome_decode",
                "n": n,
                "k": k,
                "w": w,
                "candidate_count": candidate_count,
                "max_error_weight": max_error_weight,
                "parity_check_rows": parity_check_rows,
            },
            warnings=[
                "Toy HQC-inspired parity-check decoder output is for public "
                "evaluator plumbing only; it is not an HQC result and not a "
                "security claim."
            ],
        )


class ToyCodeBasedCirculantSyndromeDecoderEstimator:
    """Bounded toy circulant syndrome decoder cost model for public fixtures."""

    estimator_name = "toy-code-based-circulant-syndrome-decoder-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _decoding_fixture_operator(plan)
        variant = operator.params["variant"]
        if variant != HQC_CIRCULANT_SYNDROME_TOY_VARIANT:
            raise ValueError(
                f"unsupported CODE_BASED decoding fixture variant: {variant}"
            )

        n = _required_int(plan.target.n, "n")
        k = _required_int(plan.target.k, "k")
        w = _required_int(plan.target.w, "w")
        block_size = _required_int(operator.params.get("block_size"), "block_size")
        max_error_weight = _required_int(
            operator.params.get("max_error_weight"),
            "max_error_weight",
        )
        if n != 2 * block_size:
            raise ValueError(
                "CODE_BASED hqc_circulant_syndrome_toy requires "
                "n == 2 * block_size"
            )
        if k != block_size:
            raise ValueError(
                "CODE_BASED hqc_circulant_syndrome_toy requires k == block_size"
            )
        if max_error_weight != w:
            raise ValueError(
                "CODE_BASED hqc_circulant_syndrome_toy requires "
                "max_error_weight == w"
            )
        if w > block_size:
            raise ValueError(
                "CODE_BASED hqc_circulant_syndrome_toy requires w <= block_size"
            )

        candidate_count = sum(
            math.comb(block_size, left_weight)
            * math.comb(block_size, max_error_weight - left_weight)
            for left_weight in range(max_error_weight + 1)
        )
        syndrome_operations = candidate_count * block_size * max(1, max_error_weight)
        time_bits = math.log2(syndrome_operations)
        memory_bits = math.log2((3 * block_size) + max_error_weight)

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
                "block_size": block_size,
                "candidate_count": candidate_count,
                "k": k,
                "max_error_weight": max_error_weight,
                "model": "toy_hqc_circulant_syndrome_decode",
                "n": n,
                "syndrome_operations": syndrome_operations,
                "w": w,
            },
            warnings=[
                "Toy HQC-inspired circulant syndrome decoder output is for "
                "public evaluator plumbing only; it is not an HQC result and "
                "not a security claim."
            ],
        )


class ToyCodeBasedCirculantErasureDecoderEstimator:
    """Bounded toy circulant-erasure decoder cost model for HQC fixtures."""

    estimator_name = "toy-code-based-circulant-erasure-decoder-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _decoding_fixture_operator(plan)
        variant = operator.params["variant"]
        if variant != HQC_CIRCULANT_ERASURE_TOY_VARIANT:
            raise ValueError(
                f"unsupported CODE_BASED decoding fixture variant: {variant}"
            )

        n = _required_int(plan.target.n, "n")
        k = _required_int(plan.target.k, "k")
        w = _required_int(plan.target.w, "w")
        block_size = _required_int(operator.params.get("block_size"), "block_size")
        max_error_weight = _required_int(
            operator.params.get("max_error_weight"),
            "max_error_weight",
        )
        first_block_erasure_count = _required_int(
            operator.params.get("first_block_erasure_count"),
            "first_block_erasure_count",
        )
        second_block_erasure_count = _required_int(
            operator.params.get("second_block_erasure_count"),
            "second_block_erasure_count",
        )
        if n != 2 * block_size:
            raise ValueError(
                "CODE_BASED hqc_circulant_erasure_toy requires "
                "n == 2 * block_size"
            )
        if k != block_size:
            raise ValueError(
                "CODE_BASED hqc_circulant_erasure_toy requires k == block_size"
            )
        if max_error_weight != w:
            raise ValueError(
                "CODE_BASED hqc_circulant_erasure_toy requires "
                "max_error_weight == w"
            )
        erasure_count = first_block_erasure_count + second_block_erasure_count
        if erasure_count < max_error_weight:
            raise ValueError(
                "CODE_BASED hqc_circulant_erasure_toy requires total erasure "
                "count >= max_error_weight"
            )

        candidate_count = sum(
            math.comb(first_block_erasure_count, left_weight)
            * math.comb(
                second_block_erasure_count,
                max_error_weight - left_weight,
            )
            for left_weight in range(
                max(0, max_error_weight - second_block_erasure_count),
                min(max_error_weight, first_block_erasure_count) + 1,
            )
        )
        syndrome_operations = candidate_count * block_size * max(1, max_error_weight)
        time_bits = math.log2(syndrome_operations)
        memory_bits = math.log2((3 * block_size) + erasure_count + max_error_weight)

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
                "block_size": block_size,
                "candidate_count": candidate_count,
                "erasure_count": erasure_count,
                "first_block_erasure_count": first_block_erasure_count,
                "k": k,
                "max_error_weight": max_error_weight,
                "model": "toy_hqc_circulant_erasure_syndrome_decode",
                "n": n,
                "second_block_erasure_count": second_block_erasure_count,
                "syndrome_operations": syndrome_operations,
                "w": w,
            },
            warnings=[
                "Toy HQC-inspired circulant-erasure decoder output is for "
                "public evaluator plumbing only; it is not an HQC result and "
                "not a security claim."
            ],
        )


class ToyCodeBasedErasureSyndromeDecoderEstimator:
    """Bounded toy erasure-aided syndrome decoder for public HQC fixtures."""

    estimator_name = "toy-code-based-erasure-syndrome-decoder-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _decoding_fixture_operator(plan)
        variant = operator.params["variant"]
        if variant != HQC_ERASURE_SYNDROME_TOY_VARIANT:
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
        erasure_count = _required_int(
            operator.params.get("erasure_count"),
            "erasure_count",
        )
        if max_error_weight != w:
            raise ValueError(
                "CODE_BASED hqc_erasure_syndrome_toy requires "
                "max_error_weight == w"
            )
        if k >= n:
            raise ValueError(
                "CODE_BASED hqc_erasure_syndrome_toy requires k < n"
            )
        if erasure_count < max_error_weight:
            raise ValueError(
                "CODE_BASED hqc_erasure_syndrome_toy requires "
                "erasure_count >= max_error_weight"
            )
        if erasure_count > MAX_HQC_ERASURE_COUNT:
            raise ValueError(
                "CODE_BASED hqc_erasure_syndrome_toy requires "
                f"erasure_count <= {MAX_HQC_ERASURE_COUNT}"
            )

        parity_check_rows = n - k
        candidate_count = math.comb(erasure_count, max_error_weight)
        syndrome_operations = candidate_count * parity_check_rows * max(1, w)
        time_bits = math.log2(syndrome_operations)
        memory_bits = math.log2(n + erasure_count + w)

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
                "erasure_count": erasure_count,
                "k": k,
                "max_error_weight": max_error_weight,
                "model": "toy_hqc_erasure_syndrome_decode",
                "n": n,
                "syndrome_operations": syndrome_operations,
                "w": w,
            },
            warnings=[
                "Toy HQC-inspired erasure-aided syndrome decoder output is "
                "for public evaluator plumbing only; it is not an HQC result "
                "and not a security claim."
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
