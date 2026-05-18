from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.families.code_based.bit_flip_estimator import (
    MDPC_BIT_FLIP_TOY_ASSUMPTION,
    MDPC_BIT_FLIP_TOY_VARIANT,
    MDPC_BLACK_GRAY_TOY_ASSUMPTION,
    MDPC_BLACK_GRAY_TOY_VARIANT,
    MDPC_SYNDROME_WEIGHT_TOY_ASSUMPTION,
    MDPC_SYNDROME_WEIGHT_TOY_VARIANT,
    ToyCodeBasedBitFlipDecoderEstimator,
)
from agades_pqc_gym.families.code_based.classic_mceliece_fixture_estimator import (
    CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_ASSUMPTION,
    CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_VARIANT,
    CLASSIC_MCELIECE_SYNDROME_TOY_ASSUMPTION,
    CLASSIC_MCELIECE_SYNDROME_TOY_VARIANT,
    ToyCodeBasedClassicMcElieceSupportSyndromeEstimator,
    ToyCodeBasedClassicMcElieceSyndromeEstimator,
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
from agades_pqc_gym.families.hash_based.bound_estimator import (
    TOY_COLLISION_ASSUMPTION,
    TOY_COLLISION_BOUND_MODEL,
    TOY_FORS_AUTH_PATH_ASSUMPTION,
    TOY_FORS_AUTH_PATH_MODEL,
    TOY_HASH_MISUSE_ASSUMPTION,
    TOY_HASH_REUSED_SALT_MODEL,
    TOY_MERKLE_AUTH_PATH_ASSUMPTION,
    TOY_MERKLE_AUTH_PATH_MODEL,
    TOY_PREIMAGE_ASSUMPTION,
    TOY_PREIMAGE_BOUND_MODEL,
    TOY_SIGNATURE_CHAIN_ASSUMPTION,
    TOY_SIGNATURE_CHAIN_MODEL,
    TOY_SLH_DSA_HYPERTREE_ASSUMPTION,
    TOY_SLH_DSA_HYPERTREE_MODEL,
    ToyHashBoundEstimator,
)
from agades_pqc_gym.families.implementation_security.kat_estimator import (
    TOY_ACVP_ASSUMPTION,
    TOY_ACVP_MODEL,
    TOY_BENCHMARK_ASSUMPTION,
    TOY_BENCHMARK_METRIC,
    TOY_BENCHMARK_MODEL,
    TOY_BINARY_SIZE_ASSUMPTION,
    TOY_BINARY_SIZE_METRIC,
    TOY_BINARY_SIZE_MODEL,
    TOY_CTGRIND_TAINT_ASSUMPTION,
    TOY_CTGRIND_TAINT_MODEL,
    TOY_CTGRIND_TAINT_TOOL,
    TOY_DUDECT_SUMMARY_ASSUMPTION,
    TOY_DUDECT_SUMMARY_MODEL,
    TOY_DUDECT_SUMMARY_TOOL,
    TOY_KAT_ASSUMPTION,
    TOY_KAT_MODEL,
    TOY_MEMORY_ASSUMPTION,
    TOY_MEMORY_METRIC,
    TOY_MEMORY_MODEL,
    TOY_STACK_USAGE_ASSUMPTION,
    TOY_STACK_USAGE_METRIC,
    TOY_STACK_USAGE_MODEL,
    TOY_TIMING_ASSUMPTION,
    TOY_TIMING_MODEL,
    TOY_TIMING_TOOL,
    ToyImplementationSecurityEstimator,
)
from agades_pqc_gym.families.isogeny_historical.path_estimator import (
    HISTORICAL_NOT_CURRENT_ASSUMPTION,
    TOY_ISOGENY_ASSUMPTIONS_BY_CASE,
    TOY_ISOGENY_CASE,
    TOY_ISOGENY_COMMUTATIVE_WALK_CASE,
    TOY_ISOGENY_VOLCANO_WALK_CASE,
    ToyIsogenyHistoricalPathEstimator,
)
from agades_pqc_gym.families.multivariate.mq_estimator import (
    TOY_MINRANK_ASSUMPTION,
    TOY_MINRANK_MODEL,
    TOY_MQ_ASSUMPTION,
    TOY_MQ_DEGREE_BOUND_ASSUMPTION,
    TOY_MQ_DEGREE_BOUND_MODEL,
    TOY_MQ_HYBRID_ASSUMPTION,
    TOY_MQ_HYBRID_MODEL,
    TOY_MQ_MODEL,
    TOY_UOV_PUBLIC_MAP_ASSUMPTION,
    TOY_UOV_PUBLIC_MAP_MODEL,
    ToyMultivariateMQEstimator,
)
from agades_pqc_gym.families.plugins import plugin_descriptor_entries_by_family

FAMILY_OPERATOR_CATALOG_SCHEMA = "agades.pqc.family_operator_catalog.v1"
FAMILY_OPERATOR_CATALOG_VERIFICATION_SCHEMA = (
    "agades.pqc.family_operator_catalog_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
PROJECT = {
    "name": "Agades PQC Gym",
    "package": "agades_pqc_gym",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
}
LWE_REPRODUCTION_ROOT = "benchmarks/lattice_downscaled_lwe_instances"
CODE_BASED_ISD_FIXTURE_ROOT = "benchmarks/code_based_toy_isd/fixtures"
CODE_BASED_HQC_FIXTURE_ROOT = "benchmarks/code_based_toy_hqc/fixtures"
CODE_BASED_MDPC_FIXTURE_ROOT = "benchmarks/code_based_toy_mdpc/fixtures"
CODE_BASED_CLASSIC_MCELIECE_FIXTURE_ROOT = (
    "benchmarks/code_based_toy_classic_mceliece/fixtures"
)
HASH_BOUND_FIXTURE_ROOT = "benchmarks/hash_based_toy_bound/fixtures"
HASH_SIGNATURE_FIXTURE_ROOT = "benchmarks/hash_based_toy_signature/fixtures"
HASH_MISUSE_FIXTURE_ROOT = "benchmarks/hash_based_toy_misuse/fixtures"
MULTIVARIATE_MQ_FIXTURE_ROOT = "benchmarks/multivariate_toy_mq/fixtures"
MULTIVARIATE_MINRANK_FIXTURE_ROOT = "benchmarks/multivariate_toy_minrank/fixtures"
MULTIVARIATE_UOV_FIXTURE_ROOT = "benchmarks/multivariate_toy_uov/fixtures"
ISOGENY_FIXTURE_ROOT = "benchmarks/isogeny_historical_toy_path/fixtures"
IMPLEMENTATION_KAT_FIXTURE_ROOT = "benchmarks/implementation_security_toy_kat/fixtures"
IMPLEMENTATION_TIMING_FIXTURE_ROOT = (
    "benchmarks/implementation_security_toy_timing/fixtures"
)
IMPLEMENTATION_BENCHMARK_FIXTURE_ROOT = (
    "benchmarks/implementation_security_toy_benchmark/fixtures"
)
SCHEMA_ONLY_FAMILIES = ("NTRU", "SIS")
TOY_EVALUATOR_FAMILIES = (
    "CODE_BASED",
    "HASH_BASED",
    "IMPLEMENTATION_SECURITY",
    "ISOGENY_HISTORICAL",
    "MULTIVARIATE",
)
LATTICE_PLUGIN_FAMILIES = {"LWE", "MLWE", "NTRU", "SIS"}
PLUGIN_BINDINGS_BY_FAMILY = plugin_descriptor_entries_by_family()
PLUGIN_BY_FAMILY = {
    family.value: descriptor.name
    for family, descriptor, _entry in PLUGIN_BINDINGS_BY_FAMILY.values()
}
SUPPORT_LEVEL_BY_FAMILY = {
    family.value: entry.support_level
    for family, _descriptor, entry in PLUGIN_BINDINGS_BY_FAMILY.values()
}
VALIDATOR_BY_FAMILY = {
    family.value: entry.applicability_validator
    for family, _descriptor, entry in PLUGIN_BINDINGS_BY_FAMILY.values()
}


def build_family_operator_catalog(root: Path | None = None) -> dict[str, Any]:
    _ = (root or ROOT).resolve()
    families = [_family_entry(family.value) for family in TargetFamily]
    return {
        "schema_version": FAMILY_OPERATOR_CATALOG_SCHEMA,
        "project": PROJECT,
        "summary": _summary(families),
        "families": families,
        "safety": {
            "lattice_estimator_is_universal_pqc_oracle": False,
            "non_lattice_entries_use_lattice_estimator": False,
            "schema_only_families_have_runtime_estimators": False,
            "security_claim": False,
        },
        "release_gates": [
            "uv run pytest tests/test_family_operator_catalog.py -q",
            "uv run agades-pqc family-operator-catalog --out "
            "docs/family_operator_catalog.json",
            "uv run agades-pqc family-operator-catalog-verify --catalog "
            "docs/family_operator_catalog.json",
        ],
    }


def write_family_operator_catalog(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    catalog = build_family_operator_catalog(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(catalog, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return catalog


def verify_family_operator_catalog(
    path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    catalog = _read_catalog(path, failures)
    project_root = (root or ROOT).resolve()

    if catalog.get("schema_version") != FAMILY_OPERATOR_CATALOG_SCHEMA:
        failures.append(
            f"catalog: schema_version must be {FAMILY_OPERATOR_CATALOG_SCHEMA}."
        )

    _verify_safety(catalog, failures)
    families = catalog.get("families")
    if not isinstance(families, list):
        failures.append("catalog: families must be a list.")
        families = []
    summary = _verify_family_entries(families, failures)
    if not failures and catalog.get("summary") != summary:
        failures.append("catalog: summary is inconsistent with family entries.")
    if not failures and catalog != build_family_operator_catalog(root=project_root):
        failures.append(
            "catalog: contents are not synchronized with the current runtime "
            "operator catalog."
        )
    summary["failure_count"] = len(failures)

    return {
        "schema_version": FAMILY_OPERATOR_CATALOG_VERIFICATION_SCHEMA,
        "catalog_path": str(path),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _family_entry(family: str) -> dict[str, Any]:
    operators = _operator_entries_for_family(family)
    return {
        "family": family,
        "plugin": PLUGIN_BY_FAMILY[family],
        "support_level": SUPPORT_LEVEL_BY_FAMILY[family],
        "applicability_validator": VALIDATOR_BY_FAMILY[family],
        "operator_entry_count": len(operators),
        "operators": operators,
    }


def _operator_entries_for_family(family: str) -> list[dict[str, Any]]:
    if family == "LWE":
        return _lwe_entries()
    if family == "MLWE":
        return _mlwe_entries()
    if family in SCHEMA_ONLY_FAMILIES:
        return []
    if family == "CODE_BASED":
        return _code_based_entries()
    if family == "MULTIVARIATE":
        return _multivariate_entries()
    if family == "HASH_BASED":
        return _hash_based_entries()
    if family == "ISOGENY_HISTORICAL":
        return _isogeny_entries()
    if family == "IMPLEMENTATION_SECURITY":
        return _implementation_security_entries()
    raise ValueError(f"unsupported family for operator catalog: {family}")


def _lwe_entries() -> list[dict[str, Any]]:
    mappings = (
        ("bounded_distance_decoding", "bdd", ["beta"]),
        ("bkw", "bkw", ["block_size"]),
        ("dual_attack", "dual", ["beta"]),
        ("dual_hybrid", "dual_hybrid", ["beta", "zeta"]),
        ("primal_usvp", "usvp", ["beta"]),
    )
    return [
        _entry(
            operator_type=operator_type,
            default_estimator="mock-lattice-estimator",
            optional_external_estimator={
                "name": "lattice-estimator",
                "algorithm_key": algorithm_key,
                "scope": "reviewed_lwe_mapping",
            },
            required_assumptions=["lattice_estimator_default_cost_model"],
            required_parameters=required_parameters,
            reproduction_fixture_roots=[LWE_REPRODUCTION_ROOT],
            review_gate="reviewed_lwe_mapping",
            support_status="implemented_mvp",
            target_constraints=[
                "family=LWE",
                "support_level=implemented",
                "public toy/downscaled reproduction only",
            ],
        )
        for operator_type, algorithm_key, required_parameters in mappings
    ]


def _mlwe_entries() -> list[dict[str, Any]]:
    return [
        _entry(
            operator_type="bkz_parameter_sweep",
            default_estimator="mock-lattice-estimator",
            required_assumptions=["lattice_estimator_default_cost_model"],
            required_parameters=["beta_max", "beta_min"],
            reproduction_fixture_roots=[],
            review_gate="mlwe_warning_gated_flattening",
            support_status="implemented_mvp",
            target_constraints=[
                "family=MLWE",
                "support_level=implemented",
                "module rank k required",
                "optional Lattice Estimator use requires expert review",
            ],
        ),
        _entry(
            operator_type="module_lattice_reduction_hypothesis",
            default_estimator="mock-lattice-estimator",
            required_assumptions=["requires_expert_review"],
            required_parameters=["model"],
            reproduction_fixture_roots=[],
            review_gate="mlwe_warning_gated_flattening",
            support_status="implemented_mvp",
            target_constraints=[
                "family=MLWE",
                "support_level=implemented",
                "module rank k required",
                "not a direct Lattice Estimator mapping",
            ],
        ),
    ]


def _code_based_entries() -> list[dict[str, Any]]:
    estimator = ToyCodeBasedISDEstimator.estimator_name
    return [
        _entry(
            operator_type="information_set_decoding",
            variant=PRANGE_TOY_VARIANT,
            default_estimator=estimator,
            required_assumptions=[PRANGE_TOY_ASSUMPTION],
            required_parameters=["variant"],
            reproduction_fixture_roots=[CODE_BASED_ISD_FIXTURE_ROOT],
            review_gate="bounded_code_based_toy_isd_only",
            support_status="implemented_toy",
            target_constraints=["target name starts with toy_", "n <= 256", "w <= 32"],
        ),
        _entry(
            operator_type="information_set_decoding",
            variant=LEE_BRICKELL_TOY_VARIANT,
            default_estimator=estimator,
            required_assumptions=[LEE_BRICKELL_TOY_ASSUMPTION],
            required_parameters=["p", "variant"],
            reproduction_fixture_roots=[CODE_BASED_ISD_FIXTURE_ROOT],
            review_gate="bounded_code_based_toy_isd_only",
            support_status="implemented_toy",
            target_constraints=["1 <= p <= w", "p <= k", "w-p <= n-k"],
        ),
        _entry(
            operator_type="information_set_decoding",
            variant=STERN_TOY_VARIANT,
            default_estimator=estimator,
            required_assumptions=[STERN_TOY_ASSUMPTION],
            required_parameters=["p", "variant"],
            reproduction_fixture_roots=[CODE_BASED_ISD_FIXTURE_ROOT],
            review_gate="bounded_code_based_toy_isd_only",
            support_status="implemented_toy",
            target_constraints=["2p <= w", "p <= floor(k/2)", "w-2p <= n-k"],
        ),
        _entry(
            operator_type="information_set_decoding",
            variant=DUMER_TOY_VARIANT,
            default_estimator=estimator,
            required_assumptions=[DUMER_TOY_ASSUMPTION],
            required_parameters=["ell", "p", "variant"],
            reproduction_fixture_roots=[CODE_BASED_ISD_FIXTURE_ROOT],
            review_gate="bounded_code_based_toy_isd_only",
            support_status="implemented_toy",
            target_constraints=[
                "2p <= w",
                "p <= floor(k/2)",
                "ell <= n-k",
                "w-2p <= n-k-ell",
            ],
        ),
        _entry(
            operator_type="information_set_decoding",
            variant=BJMM_TOY_VARIANT,
            default_estimator=estimator,
            required_assumptions=[BJMM_TOY_ASSUMPTION],
            required_parameters=["ell", "p", "representation_count", "variant"],
            reproduction_fixture_roots=[CODE_BASED_ISD_FIXTURE_ROOT],
            review_gate="bounded_code_based_toy_isd_only",
            support_status="implemented_toy",
            target_constraints=[
                "2p <= w",
                "p <= floor(k/2)",
                "ell <= n-k",
                "representation_count <= 64",
                "w-2p <= n-k-ell",
            ],
        ),
        _entry(
            operator_type="information_set_decoding",
            variant=QC_ROTATION_TOY_VARIANT,
            default_estimator=estimator,
            required_assumptions=[QC_ROTATION_TOY_ASSUMPTION],
            required_parameters=["block_count", "block_size", "variant"],
            reproduction_fixture_roots=[CODE_BASED_ISD_FIXTURE_ROOT],
            review_gate="bounded_code_based_toy_qc_rotation_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_qc_",
                "n == block_size * block_count",
                "block_size <= 64",
                "block_count <= 16",
            ],
        ),
        _entry(
            operator_type="decoding_fixture_check",
            variant=HQC_REPETITION_TOY_VARIANT,
            default_estimator=(
                ToyCodeBasedRepetitionDecoderEstimator.estimator_name
            ),
            required_assumptions=[HQC_REPETITION_TOY_ASSUMPTION],
            required_parameters=["repetition_factor", "variant"],
            reproduction_fixture_roots=[CODE_BASED_HQC_FIXTURE_ROOT],
            review_gate="bounded_hqc_inspired_repetition_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_hqc_",
                "n == k * repetition_factor",
                "repetition_factor odd and <= 16",
            ],
        ),
        _entry(
            operator_type="decoding_fixture_check",
            variant=HQC_WEIGHTED_REPETITION_TOY_VARIANT,
            default_estimator=(
                ToyCodeBasedWeightedRepetitionDecoderEstimator.estimator_name
            ),
            required_assumptions=[HQC_WEIGHTED_REPETITION_TOY_ASSUMPTION],
            required_parameters=[
                "max_reliability_weight",
                "repetition_factor",
                "variant",
            ],
            reproduction_fixture_roots=[CODE_BASED_HQC_FIXTURE_ROOT],
            review_gate="bounded_hqc_inspired_weighted_repetition_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_hqc_",
                "n == k * repetition_factor",
                "repetition_factor odd and <= 16",
                "max_reliability_weight <= 16",
                "not an HQC result",
            ],
        ),
        _entry(
            operator_type="decoding_fixture_check",
            variant=HQC_PARITY_CHECK_TOY_VARIANT,
            default_estimator=(
                ToyCodeBasedParityCheckDecoderEstimator.estimator_name
            ),
            required_assumptions=[HQC_PARITY_CHECK_TOY_ASSUMPTION],
            required_parameters=["max_error_weight", "variant"],
            reproduction_fixture_roots=[CODE_BASED_HQC_FIXTURE_ROOT],
            review_gate="bounded_hqc_inspired_parity_check_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_hqc_",
                "k < n",
                "max_error_weight == w",
                "w <= n-k",
            ],
        ),
        _entry(
            operator_type="decoding_fixture_check",
            variant=HQC_CIRCULANT_SYNDROME_TOY_VARIANT,
            default_estimator=(
                ToyCodeBasedCirculantSyndromeDecoderEstimator.estimator_name
            ),
            required_assumptions=[HQC_CIRCULANT_SYNDROME_TOY_ASSUMPTION],
            required_parameters=["block_size", "max_error_weight", "variant"],
            reproduction_fixture_roots=[CODE_BASED_HQC_FIXTURE_ROOT],
            review_gate="bounded_hqc_inspired_circulant_syndrome_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_hqc_",
                "n == 2 * block_size",
                "k == block_size",
                "max_error_weight == w",
                "w <= block_size",
                "not an HQC result",
            ],
        ),
        _entry(
            operator_type="decoding_fixture_check",
            variant=HQC_CIRCULANT_ERASURE_TOY_VARIANT,
            default_estimator=(
                ToyCodeBasedCirculantErasureDecoderEstimator.estimator_name
            ),
            required_assumptions=[HQC_CIRCULANT_ERASURE_TOY_ASSUMPTION],
            required_parameters=[
                "block_size",
                "first_block_erasure_count",
                "max_error_weight",
                "second_block_erasure_count",
                "variant",
            ],
            reproduction_fixture_roots=[CODE_BASED_HQC_FIXTURE_ROOT],
            review_gate="bounded_hqc_inspired_circulant_erasure_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_hqc_",
                "n == 2 * block_size",
                "k == block_size",
                "max_error_weight == w",
                "total erasure count >= max_error_weight",
                "total erasure count <= 64",
                "not an HQC result",
            ],
        ),
        _entry(
            operator_type="decoding_fixture_check",
            variant=HQC_ERASURE_SYNDROME_TOY_VARIANT,
            default_estimator=(
                ToyCodeBasedErasureSyndromeDecoderEstimator.estimator_name
            ),
            required_assumptions=[HQC_ERASURE_SYNDROME_TOY_ASSUMPTION],
            required_parameters=["erasure_count", "max_error_weight", "variant"],
            reproduction_fixture_roots=[CODE_BASED_HQC_FIXTURE_ROOT],
            review_gate="bounded_hqc_inspired_erasure_syndrome_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_hqc_",
                "k < n",
                "max_error_weight == w",
                "erasure_count >= max_error_weight",
                "erasure_count <= n",
                "not an HQC result",
            ],
        ),
        _entry(
            operator_type="decoding_fixture_check",
            variant=MDPC_BIT_FLIP_TOY_VARIANT,
            default_estimator=(
                ToyCodeBasedBitFlipDecoderEstimator.estimator_name
            ),
            required_assumptions=[MDPC_BIT_FLIP_TOY_ASSUMPTION],
            required_parameters=["max_iterations", "threshold", "variant"],
            reproduction_fixture_roots=[CODE_BASED_MDPC_FIXTURE_ROOT],
            review_gate="bounded_mdpc_bit_flip_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_mdpc_",
                "k < n",
                "threshold <= n-k",
                "max_iterations <= 32",
                "not a BIKE result",
            ],
        ),
        _entry(
            operator_type="decoding_fixture_check",
            variant=MDPC_BLACK_GRAY_TOY_VARIANT,
            default_estimator=(
                ToyCodeBasedBitFlipDecoderEstimator.estimator_name
            ),
            required_assumptions=[MDPC_BLACK_GRAY_TOY_ASSUMPTION],
            required_parameters=[
                "black_threshold",
                "gray_threshold",
                "max_iterations",
                "variant",
            ],
            reproduction_fixture_roots=[CODE_BASED_MDPC_FIXTURE_ROOT],
            review_gate="bounded_mdpc_black_gray_bit_flip_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_mdpc_",
                "k < n",
                "gray_threshold <= black_threshold <= n-k",
                "max_iterations <= 32",
                "not a BIKE result",
            ],
        ),
        _entry(
            operator_type="decoding_fixture_check",
            variant=MDPC_SYNDROME_WEIGHT_TOY_VARIANT,
            default_estimator=(
                ToyCodeBasedBitFlipDecoderEstimator.estimator_name
            ),
            required_assumptions=[MDPC_SYNDROME_WEIGHT_TOY_ASSUMPTION],
            required_parameters=[
                "max_iterations",
                "min_syndrome_weight_drop",
                "variant",
            ],
            reproduction_fixture_roots=[CODE_BASED_MDPC_FIXTURE_ROOT],
            review_gate="bounded_mdpc_syndrome_weight_bit_flip_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_mdpc_",
                "k < n",
                "min_syndrome_weight_drop <= n-k",
                "max_iterations <= 32",
                "not a BIKE result",
            ],
        ),
        _entry(
            operator_type="decoding_fixture_check",
            variant=CLASSIC_MCELIECE_SYNDROME_TOY_VARIANT,
            default_estimator=(
                ToyCodeBasedClassicMcElieceSyndromeEstimator.estimator_name
            ),
            required_assumptions=[CLASSIC_MCELIECE_SYNDROME_TOY_ASSUMPTION],
            required_parameters=["max_error_weight", "variant"],
            reproduction_fixture_roots=[CODE_BASED_CLASSIC_MCELIECE_FIXTURE_ROOT],
            review_gate="bounded_classic_mceliece_inspired_syndrome_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_classic_mceliece_",
                "k < n",
                "max_error_weight == w",
                "w <= n-k",
                "comb(n, w) <= 100000",
                "not a Classic McEliece result",
            ],
        ),
        _entry(
            operator_type="decoding_fixture_check",
            variant=CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_VARIANT,
            default_estimator=(
                ToyCodeBasedClassicMcElieceSupportSyndromeEstimator.estimator_name
            ),
            required_assumptions=[
                CLASSIC_MCELIECE_SUPPORT_SYNDROME_TOY_ASSUMPTION
            ],
            required_parameters=[
                "max_error_weight",
                "support_size",
                "variant",
            ],
            reproduction_fixture_roots=[CODE_BASED_CLASSIC_MCELIECE_FIXTURE_ROOT],
            review_gate=(
                "bounded_classic_mceliece_inspired_public_support_fixture_only"
            ),
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_classic_mceliece_",
                "k < n",
                "max_error_weight == w",
                "support_size >= max_error_weight",
                "support_size <= n",
                "not a Classic McEliece result",
            ],
        ),
    ]


def _multivariate_entries() -> list[dict[str, Any]]:
    estimator = ToyMultivariateMQEstimator.estimator_name
    return [
        _entry(
            operator_type="groebner_basis",
            variant=TOY_MQ_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_MQ_ASSUMPTION],
            required_parameters=["model"],
            reproduction_fixture_roots=[MULTIVARIATE_MQ_FIXTURE_ROOT],
            review_gate="bounded_multivariate_toy_mq_only",
            support_status="implemented_toy",
            target_constraints=["variables <= 16", "equations <= 16", "GF(q) q <= 256"],
        ),
        _entry(
            operator_type="groebner_basis",
            variant=TOY_MQ_HYBRID_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_MQ_HYBRID_ASSUMPTION],
            required_parameters=["guessed_variables", "model"],
            reproduction_fixture_roots=[MULTIVARIATE_MQ_FIXTURE_ROOT],
            review_gate="bounded_multivariate_toy_mq_hybrid_only",
            support_status="implemented_toy",
            target_constraints=[
                "variables <= 16",
                "1 <= guessed_variables < variables",
                "GF(2) fixture reproduction only",
            ],
        ),
        _entry(
            operator_type="groebner_basis",
            variant=TOY_MQ_DEGREE_BOUND_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_MQ_DEGREE_BOUND_ASSUMPTION],
            required_parameters=["degree_bound", "linear_algebra_omega", "model"],
            reproduction_fixture_roots=[],
            review_gate="bounded_multivariate_toy_degree_bound_only",
            support_status="implemented_toy",
            target_constraints=[
                "variables <= 16",
                "equations <= 16",
                "GF(q) q <= 256",
                "2 <= degree_bound <= variables",
                "2.0 <= linear_algebra_omega <= 3.0",
                "degree-bound output is not a Groebner proof",
            ],
        ),
        _entry(
            operator_type="minrank_attack",
            variant=TOY_MINRANK_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_MINRANK_ASSUMPTION],
            required_parameters=["matrix_cols", "matrix_rows", "model", "target_rank"],
            reproduction_fixture_roots=[MULTIVARIATE_MINRANK_FIXTURE_ROOT],
            review_gate="bounded_multivariate_toy_minrank_only",
            support_status="implemented_toy",
            target_constraints=[
                "target_rank < min(matrix_rows, matrix_cols)",
                "GF(2) fixture reproduction only",
            ],
        ),
        _entry(
            operator_type="signature_fixture_check",
            variant=TOY_UOV_PUBLIC_MAP_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_UOV_PUBLIC_MAP_ASSUMPTION],
            required_parameters=[
                "oil_variables",
                "signature_model",
                "vinegar_variables",
            ],
            reproduction_fixture_roots=[MULTIVARIATE_UOV_FIXTURE_ROOT],
            review_gate="bounded_multivariate_toy_uov_public_map_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_uov_",
                "field == GF(2)",
                "oil_variables + vinegar_variables == variables",
                "not a UOV, MAYO, or Rainbow result",
            ],
        ),
    ]


def _hash_based_entries() -> list[dict[str, Any]]:
    estimator = ToyHashBoundEstimator.estimator_name
    return [
        _entry(
            operator_type="security_bound_check",
            variant=TOY_PREIMAGE_BOUND_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_PREIMAGE_ASSUMPTION],
            required_parameters=["bound_model"],
            reproduction_fixture_roots=[HASH_BOUND_FIXTURE_ROOT],
            review_gate="bounded_hash_preimage_bound_only",
            support_status="implemented_toy",
            target_constraints=["target name starts with toy_", "digest bits n <= 64"],
        ),
        _entry(
            operator_type="security_bound_check",
            variant=TOY_COLLISION_BOUND_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_COLLISION_ASSUMPTION],
            required_parameters=["bound_model"],
            reproduction_fixture_roots=[HASH_BOUND_FIXTURE_ROOT],
            review_gate="bounded_hash_collision_bound_only",
            support_status="implemented_toy",
            target_constraints=["target name starts with toy_", "digest bits n <= 64"],
        ),
        _entry(
            operator_type="hash_signature_verification",
            variant=TOY_SIGNATURE_CHAIN_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_SIGNATURE_CHAIN_ASSUMPTION],
            required_parameters=["chain_count", "max_chain_steps", "signature_model"],
            reproduction_fixture_roots=[HASH_SIGNATURE_FIXTURE_ROOT],
            review_gate="bounded_hash_signature_chain_fixture_only",
            support_status="implemented_toy",
            target_constraints=["chain_count > 0", "max_chain_steps > 0"],
        ),
        _entry(
            operator_type="hash_signature_verification",
            variant=TOY_MERKLE_AUTH_PATH_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_MERKLE_AUTH_PATH_ASSUMPTION],
            required_parameters=["leaf_index", "signature_model", "tree_height"],
            reproduction_fixture_roots=[HASH_SIGNATURE_FIXTURE_ROOT],
            review_gate="bounded_hash_merkle_auth_path_fixture_only",
            support_status="implemented_toy",
            target_constraints=["tree_height <= 16", "leaf_index < 2**tree_height"],
        ),
        _entry(
            operator_type="hash_signature_verification",
            variant=TOY_FORS_AUTH_PATH_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_FORS_AUTH_PATH_ASSUMPTION],
            required_parameters=[
                "selected_indices",
                "signature_model",
                "tree_count",
                "tree_height",
            ],
            reproduction_fixture_roots=[HASH_SIGNATURE_FIXTURE_ROOT],
            review_gate="bounded_hash_fors_auth_path_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "tree_count <= 16",
                "tree_height <= 16",
                "selected_indices length == tree_count",
                "not an SLH-DSA result",
            ],
        ),
        _entry(
            operator_type="hash_signature_verification",
            variant=TOY_SLH_DSA_HYPERTREE_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_SLH_DSA_HYPERTREE_ASSUMPTION],
            required_parameters=[
                "fors_selected_indices",
                "fors_tree_count",
                "fors_tree_height",
                "hypertree_height",
                "hypertree_leaf_index",
                "signature_model",
                "wots_chain_count",
                "wots_max_chain_steps",
            ],
            reproduction_fixture_roots=[HASH_SIGNATURE_FIXTURE_ROOT],
            review_gate="bounded_hash_slh_dsa_hypertree_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "fors_tree_count <= 16",
                "fors_tree_height <= 16",
                "wots_chain_count <= 16",
                "wots_max_chain_steps <= 64",
                "hypertree_height <= 16",
                "not an SLH-DSA result",
            ],
        ),
        _entry(
            operator_type="misuse_check",
            variant=TOY_HASH_REUSED_SALT_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_HASH_MISUSE_ASSUMPTION],
            required_parameters=[
                "expected_reuse_groups",
                "fixture",
                "record_count",
                "salt_bytes",
            ],
            reproduction_fixture_roots=[HASH_MISUSE_FIXTURE_ROOT],
            review_gate="json_only_hash_reused_salt_misuse_fixture_only",
            support_status="implemented_toy",
            target_constraints=[
                "fixture=toy_hash_reused_salt",
                "record_count > 0",
                "expected_reuse_groups > 0",
                "no exploit or security claim",
            ],
        ),
    ]


def _isogeny_entries() -> list[dict[str, Any]]:
    estimator = ToyIsogenyHistoricalPathEstimator.estimator_name
    return [
        _entry(
            operator_type="historical_isogeny_reconstruction",
            variant=TOY_ISOGENY_CASE,
            default_estimator=estimator,
            required_assumptions=[
                HISTORICAL_NOT_CURRENT_ASSUMPTION,
                TOY_ISOGENY_ASSUMPTIONS_BY_CASE[TOY_ISOGENY_CASE],
            ],
            required_parameters=["branching_factor", "case", "walk_length"],
            reproduction_fixture_roots=[ISOGENY_FIXTURE_ROOT],
            review_gate="historical_toy_path_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_",
                "not current-standard",
                "walk_length <= 32",
            ],
        ),
        _entry(
            operator_type="historical_isogeny_reconstruction",
            variant=TOY_ISOGENY_COMMUTATIVE_WALK_CASE,
            default_estimator=estimator,
            required_assumptions=[
                HISTORICAL_NOT_CURRENT_ASSUMPTION,
                TOY_ISOGENY_ASSUMPTIONS_BY_CASE[
                    TOY_ISOGENY_COMMUTATIVE_WALK_CASE
                ],
            ],
            required_parameters=["branching_factor", "case", "walk_length"],
            reproduction_fixture_roots=[ISOGENY_FIXTURE_ROOT],
            review_gate="historical_commutative_walk_toy_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_",
                "not current-standard",
                "branching_factor <= 8",
            ],
        ),
        _entry(
            operator_type="historical_isogeny_reconstruction",
            variant=TOY_ISOGENY_VOLCANO_WALK_CASE,
            default_estimator=estimator,
            required_assumptions=[
                HISTORICAL_NOT_CURRENT_ASSUMPTION,
                TOY_ISOGENY_ASSUMPTIONS_BY_CASE[TOY_ISOGENY_VOLCANO_WALK_CASE],
            ],
            required_parameters=[
                "branching_factor",
                "case",
                "volcano_height",
                "walk_length",
            ],
            reproduction_fixture_roots=[ISOGENY_FIXTURE_ROOT],
            review_gate="historical_volcano_walk_toy_only",
            support_status="implemented_toy",
            target_constraints=[
                "target name starts with toy_",
                "not current-standard",
                "branching_factor <= 8",
                "volcano_height <= 8",
                "fixture graph levels move by at most one",
            ],
        ),
    ]


def _implementation_security_entries() -> list[dict[str, Any]]:
    estimator = ToyImplementationSecurityEstimator.estimator_name
    return [
        _entry(
            operator_type="kat_conformance",
            variant=TOY_KAT_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_KAT_ASSUMPTION],
            required_parameters=[
                "expected_sha256",
                "model",
                "payload",
                "suite",
                "vector_count",
            ],
            reproduction_fixture_roots=[IMPLEMENTATION_KAT_FIXTURE_ROOT],
            review_gate="json_only_toy_kat_digest_only",
            support_status="implemented_toy",
            target_constraints=["payload <= 512 bytes", "vector_count <= 16"],
        ),
        _entry(
            operator_type="kat_conformance",
            variant=TOY_ACVP_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_ACVP_ASSUMPTION],
            required_parameters=[
                "expected_vector_set_sha256",
                "model",
                "suite",
                "test_count",
                "vector_set",
            ],
            reproduction_fixture_roots=[IMPLEMENTATION_KAT_FIXTURE_ROOT],
            review_gate="json_only_toy_acvp_vector_set_only",
            support_status="implemented_toy",
            target_constraints=["no ACVP certificate claim", "test_count <= 16"],
        ),
        _entry(
            operator_type="constant_time_check",
            variant=TOY_TIMING_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_TIMING_ASSUMPTION],
            required_parameters=[
                "fixed_cycles",
                "max_abs_t",
                "model",
                "random_cycles",
                "tool",
            ],
            reproduction_fixture_roots=[IMPLEMENTATION_TIMING_FIXTURE_ROOT],
            review_gate="json_only_toy_timing_summary_only",
            support_status="implemented_toy",
            target_constraints=[
                f"tool={TOY_TIMING_TOOL}",
                "no live traces or binaries",
                "no constant-time claim",
            ],
        ),
        _entry(
            operator_type="constant_time_check",
            variant=TOY_DUDECT_SUMMARY_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_DUDECT_SUMMARY_ASSUMPTION],
            required_parameters=[
                "dudect_version",
                "fixed_cycles",
                "max_abs_t",
                "model",
                "random_cycles",
                "tool",
            ],
            reproduction_fixture_roots=[IMPLEMENTATION_TIMING_FIXTURE_ROOT],
            review_gate="json_only_toy_dudect_summary_only",
            support_status="implemented_toy",
            target_constraints=[
                f"tool={TOY_DUDECT_SUMMARY_TOOL}",
                "does not execute dudect",
                "no live traces or binaries",
                "no constant-time claim",
            ],
        ),
        _entry(
            operator_type="constant_time_check",
            variant=TOY_CTGRIND_TAINT_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_CTGRIND_TAINT_ASSUMPTION],
            required_parameters=[
                "checked_blocks",
                "ctgrind_version",
                "max_secret_dependent_branch_count",
                "max_secret_dependent_memory_access_count",
                "model",
                "secret_dependent_branch_count",
                "secret_dependent_memory_access_count",
                "tool",
            ],
            reproduction_fixture_roots=[IMPLEMENTATION_TIMING_FIXTURE_ROOT],
            review_gate="json_only_toy_ctgrind_secret_taint_summary_only",
            support_status="implemented_toy",
            target_constraints=[
                f"tool={TOY_CTGRIND_TAINT_TOOL}",
                "does not execute ctgrind",
                "no live traces or binaries",
                "no constant-time claim",
            ],
        ),
        _entry(
            operator_type="benchmark_harness",
            variant=TOY_BENCHMARK_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_BENCHMARK_ASSUMPTION],
            required_parameters=[
                "max_median_cycles",
                "metric",
                "model",
                "samples",
                "suite",
            ],
            reproduction_fixture_roots=[IMPLEMENTATION_BENCHMARK_FIXTURE_ROOT],
            review_gate="json_only_toy_benchmark_summary_only",
            support_status="implemented_toy",
            target_constraints=[
                f"metric={TOY_BENCHMARK_METRIC}",
                "no live devices or binaries",
                "no performance claim",
            ],
        ),
        _entry(
            operator_type="benchmark_harness",
            variant=TOY_BINARY_SIZE_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_BINARY_SIZE_ASSUMPTION],
            required_parameters=[
                "bss_bytes",
                "data_bytes",
                "max_total_bytes",
                "metric",
                "model",
                "rodata_bytes",
                "suite",
                "text_bytes",
            ],
            reproduction_fixture_roots=[IMPLEMENTATION_BENCHMARK_FIXTURE_ROOT],
            review_gate="json_only_toy_binary_size_only",
            support_status="implemented_toy",
            target_constraints=[
                f"metric={TOY_BINARY_SIZE_METRIC}",
                "no live devices or binaries",
                "no binary-size claim",
                "no performance claim",
            ],
        ),
        _entry(
            operator_type="benchmark_harness",
            variant=TOY_MEMORY_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_MEMORY_ASSUMPTION],
            required_parameters=[
                "code_bytes",
                "heap_bytes",
                "max_code_bytes",
                "max_heap_bytes",
                "max_stack_bytes",
                "metric",
                "model",
                "stack_bytes",
                "suite",
            ],
            reproduction_fixture_roots=[IMPLEMENTATION_BENCHMARK_FIXTURE_ROOT],
            review_gate="json_only_toy_memory_footprint_only",
            support_status="implemented_toy",
            target_constraints=[
                f"metric={TOY_MEMORY_METRIC}",
                "no live devices or binaries",
                "no memory-usage claim",
                "no performance claim",
            ],
        ),
        _entry(
            operator_type="benchmark_harness",
            variant=TOY_STACK_USAGE_MODEL,
            default_estimator=estimator,
            required_assumptions=[TOY_STACK_USAGE_ASSUMPTION],
            required_parameters=[
                "max_stack_bytes",
                "metric",
                "model",
                "stack_samples",
                "suite",
            ],
            reproduction_fixture_roots=[IMPLEMENTATION_BENCHMARK_FIXTURE_ROOT],
            review_gate="json_only_toy_stack_usage_only",
            support_status="implemented_toy",
            target_constraints=[
                f"metric={TOY_STACK_USAGE_METRIC}",
                "no live devices or binaries",
                "no stack-usage claim",
                "no performance claim",
            ],
        ),
    ]


def _entry(
    *,
    operator_type: str,
    default_estimator: str,
    required_assumptions: list[str],
    required_parameters: list[str],
    reproduction_fixture_roots: list[str],
    review_gate: str,
    support_status: str,
    target_constraints: list[str],
    variant: str | None = None,
    optional_external_estimator: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "operator_type": operator_type,
        "variant": variant,
        "support_status": support_status,
        "default_estimator": default_estimator,
        "optional_external_estimator": optional_external_estimator,
        "required_assumptions": sorted(required_assumptions),
        "required_parameters": sorted(required_parameters),
        "target_constraints": target_constraints,
        "reproduction_fixture_roots": reproduction_fixture_roots,
        "review_gate": review_gate,
        "security_claim": False,
        "review_required_before_claims": True,
    }


def _summary(families: list[dict[str, Any]]) -> dict[str, Any]:
    applicability_validators: set[str] = set()
    families_with_operator_entries: list[str] = []
    lattice_estimator_operator_entries = 0
    non_lattice_lattice_estimator_operator_entries = 0
    operator_entries = 0
    schema_only_families: list[str] = []
    schema_only_operator_entries = 0
    support_level_counts: dict[str, int] = {}
    toy_evaluator_families: list[str] = []

    for family_entry in families:
        family = family_entry.get("family")
        if not isinstance(family, str) or not family:
            continue

        support_level = family_entry.get("support_level")
        if isinstance(support_level, str) and support_level:
            support_level_counts[support_level] = (
                support_level_counts.get(support_level, 0) + 1
            )
            if support_level == "schema_only":
                schema_only_families.append(family)
            if support_level == "toy_evaluator":
                toy_evaluator_families.append(family)

        validator = family_entry.get("applicability_validator")
        if isinstance(validator, str) and validator:
            applicability_validators.add(validator)

        operators = _summary_operator_entries(family_entry)
        operator_entries += len(operators)
        if operators:
            families_with_operator_entries.append(family)
        if support_level == "schema_only":
            schema_only_operator_entries += len(operators)

        for operator in operators:
            if _operator_uses_lattice_estimator(operator):
                lattice_estimator_operator_entries += 1
                if family not in LATTICE_PLUGIN_FAMILIES:
                    non_lattice_lattice_estimator_operator_entries += 1

    return {
        "applicability_validator_count": len(applicability_validators),
        "families": len(families),
        "families_with_operator_entries": sorted(families_with_operator_entries),
        "lattice_estimator_operator_entries": lattice_estimator_operator_entries,
        "non_lattice_lattice_estimator_operator_entries": (
            non_lattice_lattice_estimator_operator_entries
        ),
        "operator_entries": operator_entries,
        "schema_only_families": sorted(schema_only_families),
        "schema_only_operator_entries": schema_only_operator_entries,
        "support_level_counts": dict(sorted(support_level_counts.items())),
        "toy_evaluator_families": sorted(toy_evaluator_families),
    }


def _summary_operator_entries(family_entry: dict[str, Any]) -> list[dict[str, Any]]:
    operators = family_entry.get("operators")
    if not isinstance(operators, list):
        return []
    return [operator for operator in operators if isinstance(operator, dict)]


def _read_catalog(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"catalog: missing file {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"catalog: invalid JSON at line {exc.lineno}.")
        return {}
    if not isinstance(payload, dict):
        failures.append("catalog: top-level JSON value must be an object.")
        return {}
    return payload


def _verify_safety(catalog: dict[str, Any], failures: list[str]) -> None:
    safety = catalog.get("safety")
    if not isinstance(safety, dict):
        failures.append("catalog: safety must be an object.")
        return
    for key in (
        "lattice_estimator_is_universal_pqc_oracle",
        "non_lattice_entries_use_lattice_estimator",
        "schema_only_families_have_runtime_estimators",
        "security_claim",
    ):
        if safety.get(key) is not False:
            failures.append(f"catalog: safety.{key} must be false.")


def _verify_family_entries(
    families: list[Any],
    failures: list[str],
) -> dict[str, Any]:
    by_family: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(families):
        if not isinstance(entry, dict):
            failures.append(f"family[{index}]: family entry must be an object.")
            continue
        family = entry.get("family")
        if not isinstance(family, str) or not family:
            failures.append(f"family[{index}]: family must be a non-empty string.")
            continue
        if family in by_family:
            failures.append(f"{family}: duplicate family operator entry.")
            continue
        by_family[family] = entry

    expected_families = {family.value for family in TargetFamily}
    observed_families = set(by_family)
    for missing in sorted(expected_families - observed_families):
        failures.append(f"{missing}: missing family operator catalog entry.")
    for unexpected in sorted(observed_families - expected_families):
        failures.append(f"{unexpected}: unexpected family operator catalog entry.")

    for family, entry in by_family.items():
        operators = _operators_from_entry(family, entry, failures)
        _verify_family_entry(family, entry, operators, failures)

    return _summary(list(by_family.values()))


def _operators_from_entry(
    family: str,
    entry: dict[str, Any],
    failures: list[str],
) -> list[dict[str, Any]]:
    operators = entry.get("operators")
    if not isinstance(operators, list):
        failures.append(f"{family}: operators must be a list.")
        return []
    dict_operators = []
    for index, operator in enumerate(operators):
        if not isinstance(operator, dict):
            failures.append(f"{family}: operators[{index}] must be an object.")
            continue
        dict_operators.append(operator)
    return dict_operators


def _verify_family_entry(
    family: str,
    entry: dict[str, Any],
    operators: list[dict[str, Any]],
    failures: list[str],
) -> None:
    expected_plugin = PLUGIN_BY_FAMILY.get(family)
    if entry.get("plugin") != expected_plugin:
        failures.append(f"{family}: plugin must be {expected_plugin}.")
    expected_support_level = SUPPORT_LEVEL_BY_FAMILY.get(family)
    if entry.get("support_level") != expected_support_level:
        failures.append(f"{family}: support_level must be {expected_support_level}.")
    if entry.get("applicability_validator") != VALIDATOR_BY_FAMILY.get(family):
        failures.append(f"{family}: applicability_validator is not synchronized.")
    if family in SCHEMA_ONLY_FAMILIES and operators:
        failures.append(
            f"{family}: schema-only families must not publish runtime operator entries."
        )
    elif entry.get("operator_entry_count") != len(operators):
        failures.append(f"{family}: operator_entry_count is inconsistent.")

    seen: set[tuple[object, object]] = set()
    for operator in operators:
        key = (operator.get("operator_type"), operator.get("variant"))
        if key in seen:
            failures.append(f"{family}: duplicate operator entry {key}.")
        seen.add(key)
        _verify_operator_entry(family, operator, failures)


def _verify_operator_entry(
    family: str,
    operator: dict[str, Any],
    failures: list[str],
) -> None:
    if operator.get("security_claim") is not False:
        failures.append(f"{family}: operator entries must not make security claims.")
    if operator.get("review_required_before_claims") is not True:
        failures.append(
            f"{family}: operator entries must require review before claims."
        )
    for field in (
        "required_assumptions",
        "required_parameters",
        "target_constraints",
        "reproduction_fixture_roots",
    ):
        if not _is_text_list(operator.get(field)):
            failures.append(f"{family}: {field} must be a string list.")

    optional = operator.get("optional_external_estimator")
    if family not in LATTICE_PLUGIN_FAMILIES and _operator_uses_lattice_estimator(
        operator
    ):
        failures.append(
            f"{family}: non-lattice operator entries must not use lattice-estimator."
        )
    if family == "MLWE" and optional is not None:
        failures.append(
            "MLWE: direct external estimator entries must remain review-gated."
        )


def _is_text_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _operator_uses_lattice_estimator(operator: dict[str, Any]) -> bool:
    estimator_names = [operator.get("default_estimator")]
    optional = operator.get("optional_external_estimator")
    if isinstance(optional, dict):
        estimator_names.append(optional.get("name"))
    return "lattice-estimator" in {str(name) for name in estimator_names}
