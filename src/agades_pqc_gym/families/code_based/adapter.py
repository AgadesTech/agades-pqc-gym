from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.core.family_adapter import ReproductionResult, ValidationFinding
from agades_pqc_gym.core.operators import PLACEHOLDER_OPERATORS
from agades_pqc_gym.core.target import SupportLevel, TargetFamily, TargetSpec
from agades_pqc_gym.evaluators.base import EstimatorResult
from agades_pqc_gym.families.code_based.bit_flip_estimator import (
    MDPC_BIT_FLIP_TOY_ASSUMPTION,
    MDPC_BIT_FLIP_TOY_VARIANT,
    MDPC_BLACK_GRAY_TOY_ASSUMPTION,
    MDPC_BLACK_GRAY_TOY_VARIANT,
    MDPC_SYNDROME_WEIGHT_TOY_ASSUMPTION,
    MDPC_SYNDROME_WEIGHT_TOY_VARIANT,
    ToyCodeBasedBitFlipDecoderEstimator,
)
from agades_pqc_gym.families.code_based.bit_flip_fixture import (
    decode_toy_mdpc_bit_flip_fixture,
    decode_toy_mdpc_black_gray_fixture,
    decode_toy_mdpc_syndrome_weight_fixture,
)
from agades_pqc_gym.families.code_based.classic_mceliece_fixture_decoder import (
    decode_toy_classic_mceliece_support_syndrome_fixture,
)
from agades_pqc_gym.families.code_based.classic_mceliece_fixture_estimator import (
    CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_ASSUMPTION,
    CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_VARIANT,
    CLASSIC_MCELIECE_SYNDROME_TOY_ASSUMPTION,
    CLASSIC_MCELIECE_SYNDROME_TOY_VARIANT,
    MAX_CLASSIC_MCELIECE_SUPPORT_SIZE,
    ToyCodeBasedClassicMcElieceSupportSyndromeEstimator,
    ToyCodeBasedClassicMcElieceSyndromeEstimator,
)
from agades_pqc_gym.families.code_based.hqc_fixture_decoder import (
    decode_toy_hqc_circulant_erasure_fixture,
    decode_toy_hqc_circulant_syndrome_fixture,
    decode_toy_hqc_erasure_syndrome_fixture,
    decode_toy_hqc_parity_check_fixture,
    decode_toy_hqc_repetition_fixture,
    decode_toy_hqc_weighted_repetition_fixture,
)
from agades_pqc_gym.families.code_based.hqc_fixture_estimator import (
    HQC_CIRCULANT_ERASURE_TOY_ASSUMPTION,
    HQC_CIRCULANT_ERASURE_TOY_VARIANT,
    HQC_CIRCULANT_SYNDROME_TOY_ASSUMPTION,
    HQC_CIRCULANT_SYNDROME_TOY_VARIANT,
    HQC_ERASURE_SYNDROME_TOY_ASSUMPTION,
    HQC_ERASURE_SYNDROME_TOY_VARIANT,
    HQC_PARITY_CHECK_TOY_ASSUMPTION,
    HQC_PARITY_CHECK_TOY_VARIANT,
    HQC_REPETITION_TOY_ASSUMPTION,
    HQC_REPETITION_TOY_VARIANT,
    HQC_WEIGHTED_REPETITION_TOY_ASSUMPTION,
    HQC_WEIGHTED_REPETITION_TOY_VARIANT,
    MAX_HQC_ERASURE_COUNT,
    MAX_HQC_WEIGHTED_REPETITION_RELIABILITY,
    ToyCodeBasedCirculantErasureDecoderEstimator,
    ToyCodeBasedCirculantSyndromeDecoderEstimator,
    ToyCodeBasedErasureSyndromeDecoderEstimator,
    ToyCodeBasedParityCheckDecoderEstimator,
    ToyCodeBasedRepetitionDecoderEstimator,
    ToyCodeBasedWeightedRepetitionDecoderEstimator,
)
from agades_pqc_gym.families.code_based.isd_estimator import (
    BJMM_TOY_ASSUMPTION,
    BJMM_TOY_VARIANT,
    DUMER_TOY_ASSUMPTION,
    DUMER_TOY_VARIANT,
    LEE_BRICKELL_TOY_ASSUMPTION,
    LEE_BRICKELL_TOY_VARIANT,
    PRANGE_TOY_ASSUMPTION,
    PRANGE_TOY_VARIANT,
    QC_ROTATION_TOY_ASSUMPTION,
    QC_ROTATION_TOY_VARIANT,
    STERN_TOY_ASSUMPTION,
    STERN_TOY_VARIANT,
    ToyCodeBasedISDEstimator,
)
from agades_pqc_gym.families.code_based.syndrome_solver import (
    solve_toy_qc_rotation_fixture,
    solve_toy_syndrome_fixture,
)
from agades_pqc_gym.families.fixtures import (
    is_scoped_public_fixture_path,
    resolve_public_fixture_path,
)
from agades_pqc_gym.families.schema_only import (
    SCHEMA_ONLY_ASSUMPTION,
    SchemaOnlyFamilyAdapter,
)

_MAX_TOY_CODE_LENGTH = 256
_MAX_TOY_ERROR_WEIGHT = 32
_MAX_TOY_QC_BLOCK_SIZE = 64
_MAX_TOY_QC_BLOCK_COUNT = 16
_MAX_TOY_HQC_REPETITION_FACTOR = 16
_MAX_TOY_BJMM_REPRESENTATION_COUNT = 64
_MAX_TOY_CLASSIC_MCELIECE_SYNDROME_CANDIDATES = 100_000
CODE_BASED_INSTANCE_REPRODUCTION_SCORE = 0.4
ROOT = Path(__file__).resolve().parents[4]
PACKAGE_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_ISD_FIXTURE_ROOT_PARTS = ("benchmarks", "code_based_toy_isd", "fixtures")
_HQC_FIXTURE_ROOT_PARTS = ("benchmarks", "code_based_toy_hqc", "fixtures")
_MDPC_FIXTURE_ROOT_PARTS = ("benchmarks", "code_based_toy_mdpc", "fixtures")
_CLASSIC_MCELIECE_FIXTURE_ROOT_PARTS = (
    "benchmarks",
    "code_based_toy_classic_mceliece",
    "fixtures",
)
_SUPPORTED_TOY_ISD_VARIANTS = {
    LEE_BRICKELL_TOY_VARIANT,
    PRANGE_TOY_VARIANT,
    STERN_TOY_VARIANT,
    BJMM_TOY_VARIANT,
    DUMER_TOY_VARIANT,
    QC_ROTATION_TOY_VARIANT,
}


@dataclass(frozen=True)
class CodeBasedFamilyAdapter:
    family: TargetFamily = TargetFamily.CODE_BASED
    support_level: str = "toy_evaluator"
    estimator_name: str = ToyCodeBasedISDEstimator.estimator_name

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_schema_only",
            SchemaOnlyFamilyAdapter(
                family=TargetFamily.CODE_BASED,
                estimator_name="code-based-placeholder-estimator",
            ),
        )
        object.__setattr__(self, "_estimator", ToyCodeBasedISDEstimator())
        object.__setattr__(
            self,
            "_repetition_estimator",
            ToyCodeBasedRepetitionDecoderEstimator(),
        )
        object.__setattr__(
            self,
            "_weighted_repetition_estimator",
            ToyCodeBasedWeightedRepetitionDecoderEstimator(),
        )
        object.__setattr__(
            self,
            "_parity_check_estimator",
            ToyCodeBasedParityCheckDecoderEstimator(),
        )
        object.__setattr__(
            self,
            "_circulant_syndrome_estimator",
            ToyCodeBasedCirculantSyndromeDecoderEstimator(),
        )
        object.__setattr__(
            self,
            "_circulant_erasure_estimator",
            ToyCodeBasedCirculantErasureDecoderEstimator(),
        )
        object.__setattr__(
            self,
            "_erasure_syndrome_estimator",
            ToyCodeBasedErasureSyndromeDecoderEstimator(),
        )
        object.__setattr__(
            self,
            "_bit_flip_estimator",
            ToyCodeBasedBitFlipDecoderEstimator(),
        )
        object.__setattr__(
            self,
            "_classic_mceliece_syndrome_estimator",
            ToyCodeBasedClassicMcElieceSyndromeEstimator(),
        )
        object.__setattr__(
            self,
            "_classic_mceliece_support_syndrome_estimator",
            ToyCodeBasedClassicMcElieceSupportSyndromeEstimator(),
        )

    def validate_target(self, target: TargetSpec) -> list[ValidationFinding]:
        findings = _validate_code_based_shape(target)
        if target.family is not TargetFamily.CODE_BASED:
            return findings
        if target.support_level is SupportLevel.SCHEMA_ONLY:
            return [*findings, *self._schema_only.validate_target(target)]
        if target.support_level is not SupportLevel.IMPLEMENTED:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="code_based_support_level_unknown",
                    message=(
                        "CODE_BASED targets must be schema_only or implemented "
                        "for the reviewed toy evaluator"
                    ),
                )
            )
            return findings

        if not target.name.startswith("toy_"):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="code_based_toy_target_required",
                    message=(
                        "CODE_BASED implemented evaluator is limited to toy_ "
                        "code-based targets"
                    ),
                ),
            )
        if target.n is not None and target.n > _MAX_TOY_CODE_LENGTH:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="code_based_toy_length_limit",
                    message=(
                        "CODE_BASED implemented toy evaluator requires "
                        f"n <= {_MAX_TOY_CODE_LENGTH}"
                    ),
                )
            )
        if target.w is not None and target.w > _MAX_TOY_ERROR_WEIGHT:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="code_based_toy_weight_limit",
                    message=(
                        "CODE_BASED implemented toy evaluator requires "
                        f"w <= {_MAX_TOY_ERROR_WEIGHT}"
                    ),
                )
            )
        return findings

    def validate_plan(self, plan: AttackPlan) -> list[ValidationFinding]:
        if plan.target.support_level is SupportLevel.SCHEMA_ONLY:
            return self._schema_only.validate_plan(plan)

        findings: list[ValidationFinding] = []
        for operator in plan.operators:
            if SCHEMA_ONLY_ASSUMPTION in operator.assumptions:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="code_based_schema_only_assumption_on_implemented_plan",
                        message=(
                            "CODE_BASED implemented toy plans must not use "
                            f"{SCHEMA_ONLY_ASSUMPTION}"
                        ),
                    )
                )
            if operator.type == "information_set_decoding":
                findings.extend(_validate_isd_operator(plan, operator))
            elif operator.type == "decoding_fixture_check":
                findings.extend(_validate_decoding_fixture_operator(plan, operator))
            else:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="code_based_unreviewed_operator",
                        message=(
                            "CODE_BASED implemented evaluator supports only "
                            "information_set_decoding or decoding_fixture_check"
                        ),
                    )
                )
        if (
            plan.constraints.require_reproducibility_on_downscaled_instances
            and plan.constraints.downscaled_reproduction_fixture is None
        ):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="code_based_reproduction_fixture_required",
                    message=(
                        "CODE_BASED toy reproduction requires an explicit "
                        "public fixture"
                    ),
                )
            )
        if plan.constraints.downscaled_reproduction_fixture is not None:
            fixture_path = Path(plan.constraints.downscaled_reproduction_fixture)
            root_parts = _fixture_root_parts_for_plan(plan)
            if not is_scoped_public_fixture_path(fixture_path, root_parts):
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="code_based_reproduction_fixture_scope",
                        message=(
                            "CODE_BASED reproduction fixtures must be relative "
                            f"paths under {_fixture_scope(root_parts)}"
                        ),
                    )
                )
        if any(
            claim is not None
            for claim in (
                plan.claims.estimated_time_bits,
                plan.claims.estimated_memory_bits,
                plan.claims.success_probability,
            )
        ):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="code_based_pre_evaluation_claims_not_allowed",
                    message=(
                        "CODE_BASED toy plans must not include cryptanalytic "
                        "estimate claims"
                    ),
                )
            )
        return findings

    def supported_operators(self) -> set[str]:
        return set(PLACEHOLDER_OPERATORS[TargetFamily.CODE_BASED])

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        if plan.target.support_level is SupportLevel.SCHEMA_ONLY:
            return self._schema_only.estimate(plan)
        if _uses_hqc_weighted_repetition(plan):
            return self._weighted_repetition_estimator.estimate(plan)
        if _uses_hqc_repetition(plan):
            return self._repetition_estimator.estimate(plan)
        if _uses_hqc_parity_check(plan):
            return self._parity_check_estimator.estimate(plan)
        if _uses_hqc_circulant_syndrome(plan):
            return self._circulant_syndrome_estimator.estimate(plan)
        if _uses_hqc_circulant_erasure(plan):
            return self._circulant_erasure_estimator.estimate(plan)
        if _uses_hqc_erasure_syndrome(plan):
            return self._erasure_syndrome_estimator.estimate(plan)
        if _uses_mdpc_bit_flip(plan):
            return self._bit_flip_estimator.estimate(plan)
        if _uses_classic_mceliece_support_syndrome(plan):
            return self._classic_mceliece_support_syndrome_estimator.estimate(plan)
        if _uses_classic_mceliece_syndrome(plan):
            return self._classic_mceliece_syndrome_estimator.estimate(plan)
        return self._estimator.estimate(plan)

    def reproduce_downscaled(self, plan: AttackPlan) -> ReproductionResult | None:
        if not plan.constraints.require_reproducibility_on_downscaled_instances:
            return None

        fixture_path_value = plan.constraints.downscaled_reproduction_fixture
        if not fixture_path_value:
            return ReproductionResult(
                attempted=False,
                status="not_applicable",
                success=False,
                warnings=[
                    "CODE_BASED toy reproduction requires an explicit public "
                    "fixture."
                ],
            )

        root_parts = _fixture_root_parts_for_plan(plan)
        fixture_path, fixture_warnings = _resolve_code_based_fixture_path(
            fixture_path_value,
            root_parts=root_parts,
        )
        if fixture_path is None:
            return ReproductionResult(
                attempted=False,
                status="not_applicable",
                success=False,
                warnings=fixture_warnings,
            )
        variant = _reproduction_variant(plan)
        try:
            if variant == HQC_REPETITION_TOY_VARIANT:
                solution = decode_toy_hqc_repetition_fixture(fixture_path)
            elif variant == HQC_WEIGHTED_REPETITION_TOY_VARIANT:
                solution = decode_toy_hqc_weighted_repetition_fixture(fixture_path)
            elif variant == HQC_PARITY_CHECK_TOY_VARIANT:
                solution = decode_toy_hqc_parity_check_fixture(fixture_path)
            elif variant == HQC_CIRCULANT_SYNDROME_TOY_VARIANT:
                solution = decode_toy_hqc_circulant_syndrome_fixture(fixture_path)
            elif variant == HQC_CIRCULANT_ERASURE_TOY_VARIANT:
                solution = decode_toy_hqc_circulant_erasure_fixture(fixture_path)
            elif variant == HQC_ERASURE_SYNDROME_TOY_VARIANT:
                solution = decode_toy_hqc_erasure_syndrome_fixture(fixture_path)
            elif variant == MDPC_BIT_FLIP_TOY_VARIANT:
                solution = decode_toy_mdpc_bit_flip_fixture(fixture_path)
            elif variant == MDPC_BLACK_GRAY_TOY_VARIANT:
                solution = decode_toy_mdpc_black_gray_fixture(fixture_path)
            elif variant == MDPC_SYNDROME_WEIGHT_TOY_VARIANT:
                solution = decode_toy_mdpc_syndrome_weight_fixture(fixture_path)
            elif variant == QC_ROTATION_TOY_VARIANT:
                solution = solve_toy_qc_rotation_fixture(fixture_path)
            elif variant == CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_VARIANT:
                solution = decode_toy_classic_mceliece_support_syndrome_fixture(
                    fixture_path
                )
            else:
                solution = solve_toy_syndrome_fixture(fixture_path)
        except (OSError, ValueError) as exc:
            return ReproductionResult(
                attempted=True,
                status="failed",
                success=False,
                warnings=[
                    f"CODE_BASED toy fixture could not be solved: {exc}"
                ],
            )

        if _solution_matches_plan(solution, plan, variant):
            return ReproductionResult(
                attempted=True,
                status="instance_solved",
                success=True,
                score=CODE_BASED_INSTANCE_REPRODUCTION_SCORE,
                warnings=[_reproduction_success_warning(variant)],
            )
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "CODE_BASED toy fixture did not produce the expected "
                "public target solution."
            ],
        )


def _validate_code_based_shape(target: TargetSpec) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if target.family is not TargetFamily.CODE_BASED:
        findings.append(
            ValidationFinding(
                severity="error",
                code="family_adapter_mismatch",
                message=(
                    f"CODE_BASED adapter cannot validate {target.family.value} targets"
                ),
            )
        )
        return findings

    if target.k is not None and target.n is not None and target.k >= target.n:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_invalid_dimension",
                message="CODE_BASED target k must be smaller than n",
            )
        )
    if target.w is not None and target.n is not None and target.w >= target.n:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_invalid_weight",
                message="CODE_BASED target w must be smaller than n",
            )
        )
    return findings


def _validate_isd_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    variant = operator.params.get("variant")
    if variant not in _SUPPORTED_TOY_ISD_VARIANTS:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_unreviewed_isd_variant",
                message=(
                    "CODE_BASED implemented ISD evaluator supports only "
                    f"{PRANGE_TOY_VARIANT}, {LEE_BRICKELL_TOY_VARIANT}, "
                    f"{STERN_TOY_VARIANT}, {DUMER_TOY_VARIANT}, "
                    f"{BJMM_TOY_VARIANT}, or {QC_ROTATION_TOY_VARIANT}"
                ),
            )
        )
    if (
        variant == PRANGE_TOY_VARIANT
        and PRANGE_TOY_ASSUMPTION not in operator.assumptions
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_prange_assumption_required",
                message=(
                    "CODE_BASED prange_toy plans must include "
                    f"{PRANGE_TOY_ASSUMPTION}"
                ),
            )
        )
    if variant == STERN_TOY_VARIANT:
        findings.extend(_validate_stern_operator(plan, operator))
    if variant == DUMER_TOY_VARIANT:
        findings.extend(_validate_dumer_operator(plan, operator))
    if variant == BJMM_TOY_VARIANT:
        findings.extend(_validate_bjmm_operator(plan, operator))
    if variant == LEE_BRICKELL_TOY_VARIANT:
        findings.extend(_validate_lee_brickell_operator(plan, operator))
    if variant == QC_ROTATION_TOY_VARIANT:
        findings.extend(_validate_qc_rotation_operator(plan, operator))
    return findings


def _validate_lee_brickell_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    p = operator.params.get("p")
    if LEE_BRICKELL_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_lee_brickell_assumption_required",
                message=(
                    "CODE_BASED lee_brickell_toy plans must include "
                    f"{LEE_BRICKELL_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(p):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_lee_brickell_p_required",
                message=(
                    "CODE_BASED lee_brickell_toy requires positive integer p"
                ),
            )
        )
        return findings

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if n is None or k is None or w is None:
        return findings
    redundancy = n - k
    if p > w:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_lee_brickell_p_exceeds_weight",
                message="CODE_BASED lee_brickell_toy requires 1 <= p <= w",
            )
        )
    if p > k:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_lee_brickell_p_exceeds_dimension",
                message="CODE_BASED lee_brickell_toy requires p <= k",
            )
        )
    if w - p > redundancy:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_lee_brickell_redundancy_weight",
                message="CODE_BASED lee_brickell_toy requires w - p <= n - k",
            )
        )
    return findings


def _validate_stern_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    p = operator.params.get("p")
    if STERN_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_stern_assumption_required",
                message=(
                    "CODE_BASED stern_toy plans must include "
                    f"{STERN_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(p):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_stern_p_required",
                message="CODE_BASED stern_toy requires positive integer p",
            )
        )
        return findings

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if n is None or k is None or w is None:
        return findings
    redundancy = n - k
    if 2 * p > w:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_stern_p_exceeds_weight",
                message="CODE_BASED stern_toy requires 2p <= w",
            )
        )
    if p > k // 2:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_stern_p_exceeds_partition",
                message="CODE_BASED stern_toy requires p <= floor(k / 2)",
            )
        )
    if w - 2 * p > redundancy:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_stern_redundancy_weight",
                message="CODE_BASED stern_toy requires w - 2p <= n - k",
            )
        )
    return findings


def _validate_dumer_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    p = operator.params.get("p")
    ell = operator.params.get("ell")
    if DUMER_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_dumer_assumption_required",
                message=(
                    "CODE_BASED dumer_toy plans must include "
                    f"{DUMER_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(p):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_dumer_p_required",
                message="CODE_BASED dumer_toy requires positive integer p",
            )
        )
    if not _is_non_negative_int(ell):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_dumer_ell_required",
                message="CODE_BASED dumer_toy requires non-negative integer ell",
            )
        )
    if not (_is_positive_int(p) and _is_non_negative_int(ell)):
        return findings

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if n is None or k is None or w is None:
        return findings
    redundancy = n - k
    if 2 * p > w:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_dumer_p_exceeds_weight",
                message="CODE_BASED dumer_toy requires 2p <= w",
            )
        )
    if p > k // 2:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_dumer_p_exceeds_partition",
                message="CODE_BASED dumer_toy requires p <= floor(k / 2)",
            )
        )
    if ell > redundancy:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_dumer_ell_exceeds_redundancy",
                message="CODE_BASED dumer_toy requires ell <= n - k",
            )
        )
    if w - 2 * p > redundancy - ell:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_dumer_redundancy_weight",
                message="CODE_BASED dumer_toy requires w - 2p <= n - k - ell",
            )
        )
    return findings


def _validate_bjmm_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    p = operator.params.get("p")
    ell = operator.params.get("ell")
    representation_count = operator.params.get("representation_count")
    if BJMM_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_bjmm_assumption_required",
                message=(
                    "CODE_BASED bjmm_toy plans must include "
                    f"{BJMM_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(p):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_bjmm_p_required",
                message="CODE_BASED bjmm_toy requires positive integer p",
            )
        )
    if not _is_non_negative_int(ell):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_bjmm_ell_required",
                message="CODE_BASED bjmm_toy requires non-negative integer ell",
            )
        )
    if not _is_positive_int(representation_count):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_bjmm_representation_count_required",
                message=(
                    "CODE_BASED bjmm_toy requires positive integer "
                    "representation_count"
                ),
            )
        )
    if not (
        _is_positive_int(p)
        and _is_non_negative_int(ell)
        and _is_positive_int(representation_count)
    ):
        return findings

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if n is None or k is None or w is None:
        return findings
    redundancy = n - k
    if 2 * p > w:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_bjmm_p_exceeds_weight",
                message="CODE_BASED bjmm_toy requires 2p <= w",
            )
        )
    if p > k // 2:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_bjmm_p_exceeds_partition",
                message="CODE_BASED bjmm_toy requires p <= floor(k / 2)",
            )
        )
    if ell > redundancy:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_bjmm_ell_exceeds_redundancy",
                message="CODE_BASED bjmm_toy requires ell <= n - k",
            )
        )
    if representation_count > _MAX_TOY_BJMM_REPRESENTATION_COUNT:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_bjmm_representation_count_limit",
                message=(
                    "CODE_BASED bjmm_toy requires representation_count <= "
                    f"{_MAX_TOY_BJMM_REPRESENTATION_COUNT}"
                ),
            )
        )
    if w - 2 * p > redundancy - ell:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_bjmm_redundancy_weight",
                message="CODE_BASED bjmm_toy requires w - 2p <= n - k - ell",
            )
        )
    return findings


def _validate_qc_rotation_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    block_size = operator.params.get("block_size")
    block_count = operator.params.get("block_count")
    if QC_ROTATION_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_qc_rotation_assumption_required",
                message=(
                    "CODE_BASED qc_rotation_toy plans must include "
                    f"{QC_ROTATION_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(block_size):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_qc_rotation_block_size_required",
                message=(
                    "CODE_BASED qc_rotation_toy requires positive integer "
                    "block_size"
                ),
            )
        )
    if not _is_positive_int(block_count):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_qc_rotation_block_count_required",
                message=(
                    "CODE_BASED qc_rotation_toy requires positive integer "
                    "block_count"
                ),
            )
        )
    if not (_is_positive_int(block_size) and _is_positive_int(block_count)):
        return findings

    if block_size > _MAX_TOY_QC_BLOCK_SIZE:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_qc_rotation_block_size_limit",
                message=(
                    "CODE_BASED qc_rotation_toy requires block_size <= "
                    f"{_MAX_TOY_QC_BLOCK_SIZE}"
                ),
            )
        )
    if block_count > _MAX_TOY_QC_BLOCK_COUNT:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_qc_rotation_block_count_limit",
                message=(
                    "CODE_BASED qc_rotation_toy requires block_count <= "
                    f"{_MAX_TOY_QC_BLOCK_COUNT}"
                ),
            )
        )

    n = plan.target.n
    w = plan.target.w
    if n is not None and n != block_size * block_count:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_qc_rotation_shape_mismatch",
                message=(
                    "CODE_BASED qc_rotation_toy requires n == block_size * "
                    "block_count"
                ),
            )
        )
    if w is not None and w > block_count:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_qc_rotation_weight_limit",
                message="CODE_BASED qc_rotation_toy requires w <= block_count",
            )
        )
    if not plan.target.name.startswith("toy_qc_"):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_qc_rotation_target_name_required",
                message="CODE_BASED qc_rotation_toy targets must start with toy_qc_",
            )
        )
    return findings


def _validate_decoding_fixture_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    variant = operator.params.get("variant")
    if variant == HQC_REPETITION_TOY_VARIANT:
        return _validate_hqc_repetition_operator(plan, operator)
    if variant == HQC_WEIGHTED_REPETITION_TOY_VARIANT:
        return _validate_hqc_weighted_repetition_operator(plan, operator)
    if variant == HQC_PARITY_CHECK_TOY_VARIANT:
        return _validate_hqc_parity_check_operator(plan, operator)
    if variant == HQC_CIRCULANT_SYNDROME_TOY_VARIANT:
        return _validate_hqc_circulant_syndrome_operator(plan, operator)
    if variant == HQC_CIRCULANT_ERASURE_TOY_VARIANT:
        return _validate_hqc_circulant_erasure_operator(plan, operator)
    if variant == HQC_ERASURE_SYNDROME_TOY_VARIANT:
        return _validate_hqc_erasure_syndrome_operator(plan, operator)
    if variant == MDPC_BIT_FLIP_TOY_VARIANT:
        return _validate_mdpc_bit_flip_operator(plan, operator)
    if variant == MDPC_BLACK_GRAY_TOY_VARIANT:
        return _validate_mdpc_black_gray_operator(plan, operator)
    if variant == MDPC_SYNDROME_WEIGHT_TOY_VARIANT:
        return _validate_mdpc_syndrome_weight_operator(plan, operator)
    if variant == CLASSIC_MCELIECE_SYNDROME_TOY_VARIANT:
        return _validate_classic_mceliece_syndrome_operator(plan, operator)
    if variant == CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_VARIANT:
        return _validate_classic_mceliece_support_syndrome_operator(plan, operator)
    return [
        ValidationFinding(
            severity="error",
            code="code_based_decoding_fixture_variant_required",
            message=(
                "CODE_BASED decoding_fixture_check supports only "
                f"{HQC_REPETITION_TOY_VARIANT}, "
                f"{HQC_WEIGHTED_REPETITION_TOY_VARIANT}, "
                f"{HQC_PARITY_CHECK_TOY_VARIANT}, "
                f"{HQC_CIRCULANT_SYNDROME_TOY_VARIANT}, "
                f"{HQC_CIRCULANT_ERASURE_TOY_VARIANT}, "
                f"{HQC_ERASURE_SYNDROME_TOY_VARIANT}, "
                f"{MDPC_BIT_FLIP_TOY_VARIANT}, "
                f"{MDPC_BLACK_GRAY_TOY_VARIANT}, "
                f"{MDPC_SYNDROME_WEIGHT_TOY_VARIANT}, "
                f"{CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_VARIANT}, or "
                f"{CLASSIC_MCELIECE_SYNDROME_TOY_VARIANT}"
            ),
        )
    ]


def _validate_hqc_repetition_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    repetition_factor = operator.params.get("repetition_factor")
    if HQC_REPETITION_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_repetition_assumption_required",
                message=(
                    "CODE_BASED hqc_repetition_toy plans must include "
                    f"{HQC_REPETITION_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(repetition_factor):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_repetition_factor_required",
                message=(
                    "CODE_BASED hqc_repetition_toy requires positive integer "
                    "repetition_factor"
                ),
            )
        )
        return findings
    if repetition_factor < 3 or repetition_factor % 2 == 0:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_repetition_factor_odd",
                message=(
                    "CODE_BASED hqc_repetition_toy requires odd "
                    "repetition_factor >= 3"
                ),
            )
        )
    if repetition_factor > _MAX_TOY_HQC_REPETITION_FACTOR:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_repetition_factor_limit",
                message=(
                    "CODE_BASED hqc_repetition_toy requires "
                    "repetition_factor <= "
                    f"{_MAX_TOY_HQC_REPETITION_FACTOR}"
                ),
            )
        )

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if n is not None and k is not None and n != k * repetition_factor:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_repetition_shape_mismatch",
                message=(
                    "CODE_BASED hqc_repetition_toy requires "
                    "n == k * repetition_factor"
                ),
            )
        )
    if w is not None and k is not None and w > k:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_repetition_weight_limit",
                message="CODE_BASED hqc_repetition_toy requires w <= k",
            )
        )
    if not plan.target.name.startswith("toy_hqc_"):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_repetition_target_name_required",
                message=(
                    "CODE_BASED hqc_repetition_toy targets must start with "
                    "toy_hqc_"
                ),
            )
        )
    return findings


def _validate_hqc_weighted_repetition_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    repetition_factor = operator.params.get("repetition_factor")
    max_reliability_weight = operator.params.get("max_reliability_weight")
    if HQC_WEIGHTED_REPETITION_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_weighted_repetition_assumption_required",
                message=(
                    "CODE_BASED hqc_weighted_repetition_toy plans must include "
                    f"{HQC_WEIGHTED_REPETITION_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(repetition_factor):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_weighted_repetition_factor_required",
                message=(
                    "CODE_BASED hqc_weighted_repetition_toy requires positive "
                    "integer repetition_factor"
                ),
            )
        )
    if not _is_positive_int(max_reliability_weight):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_weighted_repetition_weight_required",
                message=(
                    "CODE_BASED hqc_weighted_repetition_toy requires positive "
                    "integer max_reliability_weight"
                ),
            )
        )
    if not (
        _is_positive_int(repetition_factor)
        and _is_positive_int(max_reliability_weight)
    ):
        return findings
    if repetition_factor < 3 or repetition_factor % 2 == 0:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_weighted_repetition_factor_odd",
                message=(
                    "CODE_BASED hqc_weighted_repetition_toy requires odd "
                    "repetition_factor >= 3"
                ),
            )
        )
    if repetition_factor > _MAX_TOY_HQC_REPETITION_FACTOR:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_weighted_repetition_factor_limit",
                message=(
                    "CODE_BASED hqc_weighted_repetition_toy requires "
                    "repetition_factor <= "
                    f"{_MAX_TOY_HQC_REPETITION_FACTOR}"
                ),
            )
        )
    if max_reliability_weight > MAX_HQC_WEIGHTED_REPETITION_RELIABILITY:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_weighted_repetition_weight_limit",
                message=(
                    "CODE_BASED hqc_weighted_repetition_toy requires "
                    "max_reliability_weight <= "
                    f"{MAX_HQC_WEIGHTED_REPETITION_RELIABILITY}"
                ),
            )
        )

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if n is not None and k is not None and n != k * repetition_factor:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_weighted_repetition_shape_mismatch",
                message=(
                    "CODE_BASED hqc_weighted_repetition_toy requires "
                    "n == k * repetition_factor"
                ),
            )
        )
    if w is not None and k is not None and w > k:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_weighted_repetition_weight_per_block_limit",
                message="CODE_BASED hqc_weighted_repetition_toy requires w <= k",
            )
        )
    if not plan.target.name.startswith("toy_hqc_"):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_weighted_repetition_target_name_required",
                message=(
                    "CODE_BASED hqc_weighted_repetition_toy targets must start "
                    "with toy_hqc_"
                ),
            )
        )
    return findings


def _validate_hqc_parity_check_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    max_error_weight = operator.params.get("max_error_weight")
    if HQC_PARITY_CHECK_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_parity_check_assumption_required",
                message=(
                    "CODE_BASED hqc_parity_check_toy plans must include "
                    f"{HQC_PARITY_CHECK_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(max_error_weight):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_parity_check_max_error_weight_required",
                message=(
                    "CODE_BASED hqc_parity_check_toy requires positive integer "
                    "max_error_weight"
                ),
            )
        )
        return findings

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if w is not None and max_error_weight != w:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_parity_check_exact_weight_required",
                message=(
                    "CODE_BASED hqc_parity_check_toy requires "
                    "max_error_weight == w"
                ),
            )
        )
    if n is not None and k is not None and k >= n:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_parity_check_invalid_dimension",
                message="CODE_BASED hqc_parity_check_toy requires k < n",
            )
        )
    if w is not None and n is not None and k is not None and w > n - k:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_parity_check_weight_limit",
                message="CODE_BASED hqc_parity_check_toy requires w <= n-k",
            )
        )
    if not plan.target.name.startswith("toy_hqc_"):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_parity_check_target_name_required",
                message=(
                    "CODE_BASED hqc_parity_check_toy targets must start with "
                    "toy_hqc_"
                ),
            )
        )
    return findings


def _validate_hqc_circulant_syndrome_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    block_size = operator.params.get("block_size")
    max_error_weight = operator.params.get("max_error_weight")
    if HQC_CIRCULANT_SYNDROME_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_syndrome_assumption_required",
                message=(
                    "CODE_BASED hqc_circulant_syndrome_toy plans must include "
                    f"{HQC_CIRCULANT_SYNDROME_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(block_size):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_syndrome_block_size_required",
                message=(
                    "CODE_BASED hqc_circulant_syndrome_toy requires positive "
                    "integer block_size"
                ),
            )
        )
    if not _is_positive_int(max_error_weight):
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_hqc_circulant_syndrome_max_error_weight_required"
                ),
                message=(
                    "CODE_BASED hqc_circulant_syndrome_toy requires positive "
                    "integer max_error_weight"
                ),
            )
        )
    if not (_is_positive_int(block_size) and _is_positive_int(max_error_weight)):
        return findings

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if block_size > _MAX_TOY_QC_BLOCK_SIZE:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_syndrome_block_size_limit",
                message=(
                    "CODE_BASED hqc_circulant_syndrome_toy requires "
                    f"block_size <= {_MAX_TOY_QC_BLOCK_SIZE}"
                ),
            )
        )
    if n is not None and n != 2 * block_size:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_syndrome_shape_mismatch",
                message=(
                    "CODE_BASED hqc_circulant_syndrome_toy requires "
                    "n == 2 * block_size"
                ),
            )
        )
    if k is not None and k != block_size:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_syndrome_dimension_mismatch",
                message=(
                    "CODE_BASED hqc_circulant_syndrome_toy requires "
                    "k == block_size"
                ),
            )
        )
    if w is not None and max_error_weight != w:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_syndrome_exact_weight_required",
                message=(
                    "CODE_BASED hqc_circulant_syndrome_toy requires "
                    "max_error_weight == w"
                ),
            )
        )
    if w is not None and w > block_size:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_syndrome_weight_limit",
                message=(
                    "CODE_BASED hqc_circulant_syndrome_toy requires "
                    "w <= block_size"
                ),
            )
        )
    if not plan.target.name.startswith("toy_hqc_"):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_syndrome_target_name_required",
                message=(
                    "CODE_BASED hqc_circulant_syndrome_toy targets must start "
                    "with toy_hqc_"
                ),
            )
        )
    return findings


def _validate_hqc_circulant_erasure_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    block_size = operator.params.get("block_size")
    max_error_weight = operator.params.get("max_error_weight")
    first_block_erasure_count = operator.params.get("first_block_erasure_count")
    second_block_erasure_count = operator.params.get("second_block_erasure_count")
    if HQC_CIRCULANT_ERASURE_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_erasure_assumption_required",
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy plans must include "
                    f"{HQC_CIRCULANT_ERASURE_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(block_size):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_erasure_block_size_required",
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy requires positive "
                    "integer block_size"
                ),
            )
        )
    if not _is_positive_int(max_error_weight):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_erasure_max_error_weight_required",
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy requires positive "
                    "integer max_error_weight"
                ),
            )
        )
    if not _is_positive_int(first_block_erasure_count):
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_hqc_circulant_erasure_first_block_"
                    "erasure_count_required"
                ),
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy requires positive "
                    "integer first_block_erasure_count"
                ),
            )
        )
    if not _is_positive_int(second_block_erasure_count):
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_hqc_circulant_erasure_second_block_"
                    "erasure_count_required"
                ),
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy requires positive "
                    "integer second_block_erasure_count"
                ),
            )
        )
    if not (
        _is_positive_int(block_size)
        and _is_positive_int(max_error_weight)
        and _is_positive_int(first_block_erasure_count)
        and _is_positive_int(second_block_erasure_count)
    ):
        return findings

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    erasure_count = first_block_erasure_count + second_block_erasure_count
    if block_size > _MAX_TOY_QC_BLOCK_SIZE:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_erasure_block_size_limit",
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy requires "
                    f"block_size <= {_MAX_TOY_QC_BLOCK_SIZE}"
                ),
            )
        )
    if first_block_erasure_count > block_size:
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_hqc_circulant_erasure_first_block_"
                    "erasure_count_shape"
                ),
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy requires "
                    "first_block_erasure_count <= block_size"
                ),
            )
        )
    if second_block_erasure_count > block_size:
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_hqc_circulant_erasure_second_block_"
                    "erasure_count_shape"
                ),
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy requires "
                    "second_block_erasure_count <= block_size"
                ),
            )
        )
    if erasure_count > MAX_HQC_ERASURE_COUNT:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_erasure_erasure_count_limit",
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy requires total "
                    f"erasure count <= {MAX_HQC_ERASURE_COUNT}"
                ),
            )
        )
    if erasure_count < max_error_weight:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_erasure_erasure_count_weight",
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy requires total "
                    "erasure count >= max_error_weight"
                ),
            )
        )
    if n is not None and n != 2 * block_size:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_erasure_shape_mismatch",
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy requires "
                    "n == 2 * block_size"
                ),
            )
        )
    if k is not None and k != block_size:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_erasure_dimension_mismatch",
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy requires "
                    "k == block_size"
                ),
            )
        )
    if w is not None and max_error_weight != w:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_erasure_exact_weight_required",
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy requires "
                    "max_error_weight == w"
                ),
            )
        )
    if not plan.target.name.startswith("toy_hqc_"):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_circulant_erasure_target_name_required",
                message=(
                    "CODE_BASED hqc_circulant_erasure_toy targets must start "
                    "with toy_hqc_"
                ),
            )
        )
    return findings


def _validate_hqc_erasure_syndrome_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    max_error_weight = operator.params.get("max_error_weight")
    erasure_count = operator.params.get("erasure_count")
    if HQC_ERASURE_SYNDROME_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_erasure_syndrome_assumption_required",
                message=(
                    "CODE_BASED hqc_erasure_syndrome_toy plans must include "
                    f"{HQC_ERASURE_SYNDROME_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(max_error_weight):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_erasure_syndrome_max_error_weight_required",
                message=(
                    "CODE_BASED hqc_erasure_syndrome_toy requires positive "
                    "integer max_error_weight"
                ),
            )
        )
    if not _is_positive_int(erasure_count):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_erasure_syndrome_erasure_count_required",
                message=(
                    "CODE_BASED hqc_erasure_syndrome_toy requires positive "
                    "integer erasure_count"
                ),
            )
        )
    if not (_is_positive_int(max_error_weight) and _is_positive_int(erasure_count)):
        return findings

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if w is not None and max_error_weight != w:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_erasure_syndrome_exact_weight_required",
                message=(
                    "CODE_BASED hqc_erasure_syndrome_toy requires "
                    "max_error_weight == w"
                ),
            )
        )
    if erasure_count < max_error_weight:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_erasure_syndrome_erasure_count_weight",
                message=(
                    "CODE_BASED hqc_erasure_syndrome_toy requires "
                    "erasure_count >= max_error_weight"
                ),
            )
        )
    if erasure_count > MAX_HQC_ERASURE_COUNT:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_erasure_syndrome_erasure_count_limit",
                message=(
                    "CODE_BASED hqc_erasure_syndrome_toy requires "
                    f"erasure_count <= {MAX_HQC_ERASURE_COUNT}"
                ),
            )
        )
    if n is not None and k is not None and k >= n:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_erasure_syndrome_invalid_dimension",
                message="CODE_BASED hqc_erasure_syndrome_toy requires k < n",
            )
        )
    if w is not None and n is not None and k is not None and w > n - k:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_erasure_syndrome_weight_limit",
                message="CODE_BASED hqc_erasure_syndrome_toy requires w <= n-k",
            )
        )
    if n is not None and erasure_count > n:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_erasure_syndrome_erasure_count_shape",
                message=(
                    "CODE_BASED hqc_erasure_syndrome_toy requires "
                    "erasure_count <= n"
                ),
            )
        )
    if not plan.target.name.startswith("toy_hqc_"):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_hqc_erasure_syndrome_target_name_required",
                message=(
                    "CODE_BASED hqc_erasure_syndrome_toy targets must start "
                    "with toy_hqc_"
                ),
            )
        )
    return findings


def _validate_mdpc_bit_flip_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    threshold = operator.params.get("threshold")
    max_iterations = operator.params.get("max_iterations")
    if MDPC_BIT_FLIP_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_bit_flip_assumption_required",
                message=(
                    "CODE_BASED mdpc_bit_flip_toy plans must include "
                    f"{MDPC_BIT_FLIP_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(threshold):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_bit_flip_threshold_required",
                message=(
                    "CODE_BASED mdpc_bit_flip_toy requires positive integer "
                    "threshold"
                ),
            )
        )
    if not _is_positive_int(max_iterations):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_bit_flip_iteration_required",
                message=(
                    "CODE_BASED mdpc_bit_flip_toy requires positive integer "
                    "max_iterations"
                ),
            )
        )
    if not (_is_positive_int(threshold) and _is_positive_int(max_iterations)):
        return findings

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if n is not None and k is not None and k >= n:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_bit_flip_invalid_dimension",
                message="CODE_BASED mdpc_bit_flip_toy requires k < n",
            )
        )
    if n is not None and k is not None and threshold > n - k:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_bit_flip_threshold_limit",
                message="CODE_BASED mdpc_bit_flip_toy requires threshold <= n-k",
            )
        )
    if max_iterations > 32:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_bit_flip_iteration_limit",
                message=(
                    "CODE_BASED mdpc_bit_flip_toy requires max_iterations <= 32"
                ),
            )
        )
    if w is not None and n is not None and k is not None and w > n - k:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_bit_flip_weight_limit",
                message="CODE_BASED mdpc_bit_flip_toy requires w <= n-k",
            )
        )
    if not plan.target.name.startswith("toy_mdpc_"):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_bit_flip_target_name_required",
                message=(
                    "CODE_BASED mdpc_bit_flip_toy targets must start with "
                    "toy_mdpc_"
                ),
            )
        )
    return findings


def _validate_mdpc_black_gray_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    black_threshold = operator.params.get("black_threshold")
    gray_threshold = operator.params.get("gray_threshold")
    max_iterations = operator.params.get("max_iterations")
    if MDPC_BLACK_GRAY_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_black_gray_assumption_required",
                message=(
                    "CODE_BASED mdpc_black_gray_bit_flip_toy plans must include "
                    f"{MDPC_BLACK_GRAY_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(black_threshold):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_black_gray_black_threshold_required",
                message=(
                    "CODE_BASED mdpc_black_gray_bit_flip_toy requires positive "
                    "integer black_threshold"
                ),
            )
        )
    if not _is_positive_int(gray_threshold):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_black_gray_gray_threshold_required",
                message=(
                    "CODE_BASED mdpc_black_gray_bit_flip_toy requires positive "
                    "integer gray_threshold"
                ),
            )
        )
    if not _is_positive_int(max_iterations):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_black_gray_iteration_required",
                message=(
                    "CODE_BASED mdpc_black_gray_bit_flip_toy requires positive "
                    "integer max_iterations"
                ),
            )
        )
    if not (
        _is_positive_int(black_threshold)
        and _is_positive_int(gray_threshold)
        and _is_positive_int(max_iterations)
    ):
        return findings

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if gray_threshold > black_threshold:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_black_gray_threshold_order",
                message=(
                    "CODE_BASED mdpc_black_gray_bit_flip_toy requires "
                    "gray_threshold <= black_threshold"
                ),
            )
        )
    if n is not None and k is not None and k >= n:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_black_gray_invalid_dimension",
                message="CODE_BASED mdpc_black_gray_bit_flip_toy requires k < n",
            )
        )
    if n is not None and k is not None and black_threshold > n - k:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_black_gray_threshold_limit",
                message=(
                    "CODE_BASED mdpc_black_gray_bit_flip_toy requires "
                    "black_threshold <= n-k"
                ),
            )
        )
    if max_iterations > 32:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_black_gray_iteration_limit",
                message=(
                    "CODE_BASED mdpc_black_gray_bit_flip_toy requires "
                    "max_iterations <= 32"
                ),
            )
        )
    if w is not None and n is not None and k is not None and w > n - k:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_black_gray_weight_limit",
                message="CODE_BASED mdpc_black_gray_bit_flip_toy requires w <= n-k",
            )
        )
    if not plan.target.name.startswith("toy_mdpc_"):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_black_gray_target_name_required",
                message=(
                    "CODE_BASED mdpc_black_gray_bit_flip_toy targets must start "
                    "with toy_mdpc_"
                ),
            )
        )
    return findings


def _validate_mdpc_syndrome_weight_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    min_syndrome_weight_drop = operator.params.get("min_syndrome_weight_drop")
    max_iterations = operator.params.get("max_iterations")
    if MDPC_SYNDROME_WEIGHT_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_syndrome_weight_assumption_required",
                message=(
                    "CODE_BASED mdpc_syndrome_weight_bit_flip_toy plans must "
                    f"include {MDPC_SYNDROME_WEIGHT_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(min_syndrome_weight_drop):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_syndrome_weight_drop_required",
                message=(
                    "CODE_BASED mdpc_syndrome_weight_bit_flip_toy requires "
                    "positive integer min_syndrome_weight_drop"
                ),
            )
        )
    if not _is_positive_int(max_iterations):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_syndrome_weight_iteration_required",
                message=(
                    "CODE_BASED mdpc_syndrome_weight_bit_flip_toy requires "
                    "positive integer max_iterations"
                ),
            )
        )
    if not (
        _is_positive_int(min_syndrome_weight_drop)
        and _is_positive_int(max_iterations)
    ):
        return findings

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if n is not None and k is not None and k >= n:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_syndrome_weight_invalid_dimension",
                message=(
                    "CODE_BASED mdpc_syndrome_weight_bit_flip_toy requires k < n"
                ),
            )
        )
    if n is not None and k is not None and min_syndrome_weight_drop > n - k:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_syndrome_weight_drop_limit",
                message=(
                    "CODE_BASED mdpc_syndrome_weight_bit_flip_toy requires "
                    "min_syndrome_weight_drop <= n-k"
                ),
            )
        )
    if max_iterations > 32:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_syndrome_weight_iteration_limit",
                message=(
                    "CODE_BASED mdpc_syndrome_weight_bit_flip_toy requires "
                    "max_iterations <= 32"
                ),
            )
        )
    if w is not None and n is not None and k is not None and w > n - k:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_syndrome_weight_weight_limit",
                message=(
                    "CODE_BASED mdpc_syndrome_weight_bit_flip_toy requires "
                    "w <= n-k"
                ),
            )
        )
    if not plan.target.name.startswith("toy_mdpc_"):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_mdpc_syndrome_weight_target_name_required",
                message=(
                    "CODE_BASED mdpc_syndrome_weight_bit_flip_toy targets "
                    "must start with toy_mdpc_"
                ),
            )
        )
    return findings


def _validate_classic_mceliece_syndrome_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    max_error_weight = operator.params.get("max_error_weight")
    if CLASSIC_MCELIECE_SYNDROME_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_classic_mceliece_syndrome_assumption_required",
                message=(
                    "CODE_BASED classic_mceliece_syndrome_toy plans must "
                    f"include {CLASSIC_MCELIECE_SYNDROME_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(max_error_weight):
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_classic_mceliece_syndrome_max_error_weight_required"
                ),
                message=(
                    "CODE_BASED classic_mceliece_syndrome_toy requires "
                    "positive integer max_error_weight"
                ),
            )
        )
        return findings

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if w is not None and max_error_weight != w:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_classic_mceliece_syndrome_exact_weight_required",
                message=(
                    "CODE_BASED classic_mceliece_syndrome_toy requires "
                    "max_error_weight == w"
                ),
            )
        )
    if n is not None and k is not None and k >= n:
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_classic_mceliece_syndrome_invalid_dimension",
                message=(
                    "CODE_BASED classic_mceliece_syndrome_toy requires k < n"
                ),
            )
        )
    if w is not None and n is not None and k is not None:
        if w > n - k:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="code_based_classic_mceliece_syndrome_weight_limit",
                    message=(
                        "CODE_BASED classic_mceliece_syndrome_toy requires "
                        "w <= n-k"
                    ),
                )
            )
        candidate_count = math.comb(n, w)
        if candidate_count > _MAX_TOY_CLASSIC_MCELIECE_SYNDROME_CANDIDATES:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="code_based_classic_mceliece_syndrome_candidate_limit",
                    message=(
                        "CODE_BASED classic_mceliece_syndrome_toy requires "
                        "comb(n, w) <= "
                        f"{_MAX_TOY_CLASSIC_MCELIECE_SYNDROME_CANDIDATES}"
                    ),
                )
            )
    if not plan.target.name.startswith("toy_classic_mceliece_"):
        findings.append(
            ValidationFinding(
                severity="error",
                code="code_based_classic_mceliece_syndrome_target_name_required",
                message=(
                    "CODE_BASED classic_mceliece_syndrome_toy targets must "
                    "start with toy_classic_mceliece_"
                ),
            )
        )
    return findings


def _validate_classic_mceliece_support_syndrome_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    max_error_weight = operator.params.get("max_error_weight")
    support_size = operator.params.get("support_size")
    if CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_classic_mceliece_support_syndrome_"
                    "assumption_required"
                ),
                message=(
                    "CODE_BASED classic_mceliece_support_syndrome_toy plans "
                    "must include "
                    f"{CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_ASSUMPTION}"
                ),
            )
        )
    if not _is_positive_int(max_error_weight):
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_classic_mceliece_support_syndrome_"
                    "max_error_weight_required"
                ),
                message=(
                    "CODE_BASED classic_mceliece_support_syndrome_toy requires "
                    "positive integer max_error_weight"
                ),
            )
        )
    if not _is_positive_int(support_size):
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_classic_mceliece_support_syndrome_"
                    "support_size_required"
                ),
                message=(
                    "CODE_BASED classic_mceliece_support_syndrome_toy requires "
                    "positive integer support_size"
                ),
            )
        )
    if not (_is_positive_int(max_error_weight) and _is_positive_int(support_size)):
        return findings

    n = plan.target.n
    k = plan.target.k
    w = plan.target.w
    if w is not None and max_error_weight != w:
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_classic_mceliece_support_syndrome_"
                    "exact_weight_required"
                ),
                message=(
                    "CODE_BASED classic_mceliece_support_syndrome_toy requires "
                    "max_error_weight == w"
                ),
            )
        )
    if support_size < max_error_weight:
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_classic_mceliece_support_syndrome_"
                    "support_size_weight"
                ),
                message=(
                    "CODE_BASED classic_mceliece_support_syndrome_toy requires "
                    "support_size >= max_error_weight"
                ),
            )
        )
    if support_size > MAX_CLASSIC_MCELIECE_SUPPORT_SIZE:
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_classic_mceliece_support_syndrome_"
                    "support_size_limit"
                ),
                message=(
                    "CODE_BASED classic_mceliece_support_syndrome_toy requires "
                    f"support_size <= {MAX_CLASSIC_MCELIECE_SUPPORT_SIZE}"
                ),
            )
        )
    if n is not None and support_size > n:
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_classic_mceliece_support_syndrome_"
                    "support_size_shape"
                ),
                message=(
                    "CODE_BASED classic_mceliece_support_syndrome_toy requires "
                    "support_size <= n"
                ),
            )
        )
    if n is not None and k is not None and k >= n:
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_classic_mceliece_support_syndrome_"
                    "invalid_dimension"
                ),
                message=(
                    "CODE_BASED classic_mceliece_support_syndrome_toy requires "
                    "k < n"
                ),
            )
        )
    if not plan.target.name.startswith("toy_classic_mceliece_"):
        findings.append(
            ValidationFinding(
                severity="error",
                code=(
                    "code_based_classic_mceliece_support_syndrome_"
                    "target_name_required"
                ),
                message=(
                    "CODE_BASED classic_mceliece_support_syndrome_toy targets "
                    "must start with toy_classic_mceliece_"
                ),
            )
        )
    return findings


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _reproduction_success_warning(variant: object) -> str:
    if variant == HQC_REPETITION_TOY_VARIANT:
        return (
            "Decoded a public toy HQC-inspired repetition-code fixture with "
            "bounded majority voting; this is reproducibility plumbing, not an "
            "HQC result and not a security claim."
        )
    if variant == HQC_WEIGHTED_REPETITION_TOY_VARIANT:
        return (
            "Decoded a public toy HQC-inspired weighted repetition-code fixture "
            "with bounded reliability-weighted voting; this is reproducibility "
            "plumbing, not an HQC result and not a security claim."
        )
    if variant == HQC_PARITY_CHECK_TOY_VARIANT:
        return (
            "Decoded a public toy HQC-inspired parity-check fixture with "
            "bounded exact-weight syndrome search; this is reproducibility "
            "plumbing, not an HQC result and not a security claim."
        )
    if variant == HQC_CIRCULANT_SYNDROME_TOY_VARIANT:
        return (
            "Decoded a public toy HQC-inspired circulant syndrome fixture with "
            "bounded double-block syndrome search; this is reproducibility "
            "plumbing, not an HQC result and not a security claim."
        )
    if variant == HQC_CIRCULANT_ERASURE_TOY_VARIANT:
        return (
            "Decoded a public toy HQC-inspired circulant-erasure fixture with "
            "bounded erasure-constrained double-block syndrome search; this is "
            "reproducibility plumbing, not an HQC result and not a security "
            "claim."
        )
    if variant == HQC_ERASURE_SYNDROME_TOY_VARIANT:
        return (
            "Decoded a public toy HQC-inspired erasure-aided syndrome fixture "
            "with bounded erasure-set search; this is reproducibility plumbing, "
            "not an HQC result and not a security claim."
        )
    if variant == MDPC_BIT_FLIP_TOY_VARIANT:
        return (
            "Decoded a public toy MDPC/BIKE-inspired bit-flip fixture with "
            "bounded JSON-only iteration; this is reproducibility plumbing, "
            "not a BIKE result and not a security claim."
        )
    if variant == MDPC_BLACK_GRAY_TOY_VARIANT:
        return (
            "Decoded a public toy MDPC/BIKE-inspired black-gray bit-flip "
            "fixture with bounded JSON-only iteration; this is reproducibility "
            "plumbing, not a BIKE result and not a security claim."
        )
    if variant == MDPC_SYNDROME_WEIGHT_TOY_VARIANT:
        return (
            "Decoded a public toy MDPC/BIKE-inspired syndrome-weight bit-flip "
            "fixture with bounded JSON-only syndrome descent; this is "
            "reproducibility plumbing, not a BIKE result and not a security "
            "claim."
        )
    if variant == QC_ROTATION_TOY_VARIANT:
        return (
            "Solved a public toy quasi-cyclic syndrome rotation fixture with "
            "bounded rotation search; this is reproducibility plumbing, not an "
            "HQC result and not a security claim."
        )
    if variant == CLASSIC_MCELIECE_SYNDROME_TOY_VARIANT:
        return (
            "Decoded a public toy Classic-McEliece-inspired binary syndrome "
            "fixture with bounded exact-weight search; this is reproducibility "
            "plumbing, not a Classic McEliece result and not a security claim."
        )
    if variant == CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_VARIANT:
        return (
            "Decoded a public toy Classic-McEliece-inspired support-set "
            "syndrome fixture with bounded support enumeration; this is "
            "reproducibility plumbing, not a Classic McEliece result and not "
            "a security claim."
        )
    return (
        "Solved a public toy binary syndrome-decoding fixture with bounded "
        "exhaustive search; this is reproducibility plumbing, not a security "
        "claim."
    )


def _resolve_code_based_fixture_path(
    value: str,
    *,
    root_parts: tuple[str, ...],
) -> tuple[Path | None, list[str]]:
    return resolve_public_fixture_path(
        value,
        repo_root=ROOT,
        package_fixture_dir=PACKAGE_FIXTURES,
        root_parts=root_parts,
        family_label="CODE_BASED",
    )


def _fixture_root_parts_for_plan(plan: AttackPlan) -> tuple[str, ...]:
    if _uses_mdpc_bit_flip(plan):
        return _MDPC_FIXTURE_ROOT_PARTS
    if (
        _uses_classic_mceliece_syndrome(plan)
        or _uses_classic_mceliece_support_syndrome(plan)
    ):
        return _CLASSIC_MCELIECE_FIXTURE_ROOT_PARTS
    if _uses_hqc_decoding_fixture(plan):
        return _HQC_FIXTURE_ROOT_PARTS
    return _ISD_FIXTURE_ROOT_PARTS


def _uses_hqc_decoding_fixture(plan: AttackPlan) -> bool:
    return (
        _uses_hqc_repetition(plan)
        or _uses_hqc_weighted_repetition(plan)
        or _uses_hqc_parity_check(plan)
        or _uses_hqc_circulant_syndrome(plan)
        or _uses_hqc_circulant_erasure(plan)
        or _uses_hqc_erasure_syndrome(plan)
    )


def _uses_hqc_repetition(plan: AttackPlan) -> bool:
    return any(
        operator.type == "decoding_fixture_check"
        and operator.params.get("variant") == HQC_REPETITION_TOY_VARIANT
        for operator in plan.operators
    )


def _uses_hqc_weighted_repetition(plan: AttackPlan) -> bool:
    return any(
        operator.type == "decoding_fixture_check"
        and operator.params.get("variant") == HQC_WEIGHTED_REPETITION_TOY_VARIANT
        for operator in plan.operators
    )


def _uses_hqc_parity_check(plan: AttackPlan) -> bool:
    return any(
        operator.type == "decoding_fixture_check"
        and operator.params.get("variant") == HQC_PARITY_CHECK_TOY_VARIANT
        for operator in plan.operators
    )


def _uses_hqc_circulant_syndrome(plan: AttackPlan) -> bool:
    return any(
        operator.type == "decoding_fixture_check"
        and operator.params.get("variant") == HQC_CIRCULANT_SYNDROME_TOY_VARIANT
        for operator in plan.operators
    )


def _uses_hqc_circulant_erasure(plan: AttackPlan) -> bool:
    return any(
        operator.type == "decoding_fixture_check"
        and operator.params.get("variant") == HQC_CIRCULANT_ERASURE_TOY_VARIANT
        for operator in plan.operators
    )


def _uses_hqc_erasure_syndrome(plan: AttackPlan) -> bool:
    return any(
        operator.type == "decoding_fixture_check"
        and operator.params.get("variant") == HQC_ERASURE_SYNDROME_TOY_VARIANT
        for operator in plan.operators
    )


def _uses_mdpc_bit_flip(plan: AttackPlan) -> bool:
    return any(
        operator.type == "decoding_fixture_check"
        and operator.params.get("variant")
        in {
            MDPC_BIT_FLIP_TOY_VARIANT,
            MDPC_BLACK_GRAY_TOY_VARIANT,
            MDPC_SYNDROME_WEIGHT_TOY_VARIANT,
        }
        for operator in plan.operators
    )


def _uses_classic_mceliece_syndrome(plan: AttackPlan) -> bool:
    return any(
        operator.type == "decoding_fixture_check"
        and operator.params.get("variant") == CLASSIC_MCELIECE_SYNDROME_TOY_VARIANT
        for operator in plan.operators
    )


def _uses_classic_mceliece_support_syndrome(plan: AttackPlan) -> bool:
    return any(
        operator.type == "decoding_fixture_check"
        and operator.params.get("variant")
        == CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_VARIANT
        for operator in plan.operators
    )


def _reproduction_variant(plan: AttackPlan) -> object:
    decoding_operator = _decoding_fixture_operator(plan)
    if decoding_operator is not None:
        return decoding_operator.params.get("variant")
    isd_operator = _information_set_decoding_operator(plan)
    if isd_operator is not None:
        return isd_operator.params.get("variant")
    return None


def _decoding_fixture_operator(plan: AttackPlan) -> AttackOperator | None:
    for operator in plan.operators:
        if operator.type == "decoding_fixture_check":
            return operator
    return None


def _information_set_decoding_operator(plan: AttackPlan) -> AttackOperator | None:
    for operator in plan.operators:
        if operator.type == "information_set_decoding":
            return operator
    return None


def _fixture_scope(root_parts: tuple[str, ...]) -> str:
    return "/".join(root_parts) + "/"


def _solution_matches_plan(
    solution: object,
    plan: AttackPlan,
    variant: object,
) -> bool:
    if variant in {
        HQC_REPETITION_TOY_VARIANT,
        HQC_WEIGHTED_REPETITION_TOY_VARIANT,
        HQC_PARITY_CHECK_TOY_VARIANT,
        HQC_CIRCULANT_SYNDROME_TOY_VARIANT,
        HQC_CIRCULANT_ERASURE_TOY_VARIANT,
        HQC_ERASURE_SYNDROME_TOY_VARIANT,
        MDPC_BIT_FLIP_TOY_VARIANT,
        MDPC_BLACK_GRAY_TOY_VARIANT,
        MDPC_SYNDROME_WEIGHT_TOY_VARIANT,
    }:
        return (
            getattr(solution, "decoded", False)
            and getattr(solution, "target_name", None) == plan.target.name
            and getattr(solution, "n", None) == plan.target.n
            and getattr(solution, "k", None) == plan.target.k
            and getattr(solution, "w", None) == plan.target.w
            and getattr(solution, "public", False)
            and not getattr(solution, "security_claim", True)
        )
    return (
        getattr(solution, "solved", False)
        and getattr(solution, "target_name", None) == plan.target.name
        and getattr(solution, "n", None) == plan.target.n
        and getattr(solution, "k", None) == plan.target.k
        and getattr(solution, "w", None) == plan.target.w
        and getattr(solution, "public", False)
        and not getattr(solution, "security_claim", True)
    )
