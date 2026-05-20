from __future__ import annotations

import importlib
import json
from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.family_adapter import ValidationFinding
from agades_pqc_gym.core.registry import default_family_registry
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.integrations.family_operator_catalog import (
    FAMILY_OPERATOR_CATALOG_VERIFICATION_SCHEMA,
    build_family_operator_catalog,
    verify_family_operator_catalog,
    write_family_operator_catalog,
)

EXPECTED_VALIDATOR_BY_FAMILY = {
    "LWE": "agades_pqc_gym.families.lattice.validators.validate_lattice_plan",
    "MLWE": "agades_pqc_gym.families.lattice.validators.validate_lattice_plan",
    "NTRU": "agades_pqc_gym.families.lattice.validators.validate_lattice_plan",
    "SIS": "agades_pqc_gym.families.lattice.validators.validate_lattice_plan",
    "CODE_BASED": (
        "agades_pqc_gym.families.code_based.validators.validate_code_based_plan"
    ),
    "MULTIVARIATE": (
        "agades_pqc_gym.families.multivariate.validators."
        "validate_multivariate_plan"
    ),
    "HASH_BASED": (
        "agades_pqc_gym.families.hash_based.validators.validate_hash_based_plan"
    ),
    "ISOGENY_HISTORICAL": (
        "agades_pqc_gym.families.isogeny_historical.validators."
        "validate_isogeny_historical_plan"
    ),
    "IMPLEMENTATION_SECURITY": (
        "agades_pqc_gym.families.implementation_security.validators."
        "validate_implementation_security_plan"
    ),
}

VALIDATOR_EXAMPLE_BY_FAMILY = {
    "CODE_BASED": "examples/attack_plans/code_based_prange_toy.json",
    "MULTIVARIATE": "examples/attack_plans/multivariate_mq_toy.json",
    "HASH_BASED": "examples/attack_plans/hash_based_preimage_toy.json",
    "ISOGENY_HISTORICAL": "examples/attack_plans/isogeny_historical_toy.json",
    "IMPLEMENTATION_SECURITY": (
        "examples/attack_plans/implementation_security_kat_toy.json"
    ),
}


def test_family_operator_catalog_describes_family_specific_estimators(
    tmp_path: Path,
) -> None:
    out = tmp_path / "family_operator_catalog.json"

    catalog = write_family_operator_catalog(out)

    assert catalog == build_family_operator_catalog()
    assert json.loads(out.read_text()) == catalog
    assert catalog["schema_version"] == "agades.pqc.family_operator_catalog.v1"
    assert catalog["project"]["package"] == "agades_pqc_gym"
    assert catalog["summary"] == {
        "applicability_validator_count": 6,
        "families": 9,
        "families_with_operator_entries": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
        ],
        "lattice_estimator_operator_entries": 5,
        "non_lattice_lattice_estimator_operator_entries": 0,
        "operator_entries": 48,
        "schema_only_families": ["NTRU", "SIS"],
        "schema_only_operator_entries": 0,
        "support_level_counts": {
            "implemented": 2,
            "schema_only": 2,
            "toy_evaluator": 5,
        },
        "toy_evaluator_families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
    }
    assert catalog["safety"] == {
        "lattice_estimator_is_universal_pqc_oracle": False,
        "non_lattice_entries_use_lattice_estimator": False,
        "schema_only_families_have_runtime_estimators": False,
        "security_claim": False,
    }

    by_family = {family["family"]: family for family in catalog["families"]}
    assert list(by_family) == [
        "LWE",
        "MLWE",
        "NTRU",
        "SIS",
        "CODE_BASED",
        "MULTIVARIATE",
        "HASH_BASED",
        "ISOGENY_HISTORICAL",
        "IMPLEMENTATION_SECURITY",
    ]

    lwe_entries = _entries_by_key(by_family["LWE"])
    assert by_family["LWE"]["plugin"] == "lattice"
    assert by_family["LWE"]["applicability_validator"] == (
        "agades_pqc_gym.families.lattice.validators.validate_lattice_plan"
    )
    for family, validator_path in EXPECTED_VALIDATOR_BY_FAMILY.items():
        assert by_family[family]["applicability_validator"] == validator_path
    assert by_family["LWE"]["operator_entry_count"] == 5
    assert lwe_entries[("primal_usvp", None)]["default_estimator"] == (
        "mock-lattice-estimator"
    )
    assert lwe_entries[("primal_usvp", None)]["optional_external_estimator"] == {
        "algorithm_key": "usvp",
        "name": "lattice-estimator",
        "scope": "reviewed_lwe_mapping",
    }
    assert lwe_entries[("dual_hybrid", None)]["required_parameters"] == [
        "beta",
        "zeta",
    ]

    mlwe_entries = _entries_by_key(by_family["MLWE"])
    assert by_family["MLWE"]["operator_entry_count"] == 2
    assert mlwe_entries[("module_lattice_reduction_hypothesis", None)][
        "review_gate"
    ] == "mlwe_warning_gated_flattening"
    assert mlwe_entries[("module_lattice_reduction_hypothesis", None)][
        "optional_external_estimator"
    ] is None

    assert by_family["NTRU"]["operator_entry_count"] == 0
    assert by_family["NTRU"]["operators"] == []
    assert by_family["SIS"]["operator_entry_count"] == 0
    assert by_family["SIS"]["operators"] == []

    code_entries = _entries_by_key(by_family["CODE_BASED"])
    assert by_family["CODE_BASED"]["operator_entry_count"] == 17
    assert {
        entry["variant"]
        for entry in by_family["CODE_BASED"]["operators"]
        if entry["operator_type"] == "information_set_decoding"
    } == {
        "bjmm_toy",
        "dumer_toy",
        "lee_brickell_toy",
        "prange_toy",
        "qc_rotation_toy",
        "stern_toy",
    }
    assert code_entries[("information_set_decoding", "bjmm_toy")][
        "required_assumptions"
    ] == ["bjmm_isd_representation_merge_model"]
    assert code_entries[("information_set_decoding", "bjmm_toy")][
        "required_parameters"
    ] == ["ell", "p", "representation_count", "variant"]
    assert code_entries[("decoding_fixture_check", "hqc_repetition_toy")][
        "default_estimator"
    ] == "toy-code-based-repetition-decoder-estimator"
    assert code_entries[("decoding_fixture_check", "hqc_repetition_toy")][
        "reproduction_fixture_roots"
    ] == ["benchmarks/code_based_toy_hqc/fixtures"]
    assert code_entries[("decoding_fixture_check", "hqc_weighted_repetition_toy")][
        "default_estimator"
    ] == "toy-code-based-weighted-repetition-decoder-estimator"
    assert code_entries[("decoding_fixture_check", "hqc_weighted_repetition_toy")][
        "required_assumptions"
    ] == ["toy_hqc_weighted_repetition_decoder_model"]
    assert code_entries[("decoding_fixture_check", "hqc_weighted_repetition_toy")][
        "required_parameters"
    ] == ["max_reliability_weight", "repetition_factor", "variant"]
    assert code_entries[("decoding_fixture_check", "hqc_weighted_repetition_toy")][
        "review_gate"
    ] == "bounded_hqc_inspired_weighted_repetition_fixture_only"
    assert code_entries[("decoding_fixture_check", "hqc_weighted_repetition_toy")][
        "reproduction_fixture_roots"
    ] == ["benchmarks/code_based_toy_hqc/fixtures"]
    assert code_entries[("decoding_fixture_check", "hqc_parity_check_toy")][
        "default_estimator"
    ] == "toy-code-based-parity-check-decoder-estimator"
    assert code_entries[("decoding_fixture_check", "hqc_parity_check_toy")][
        "required_parameters"
    ] == ["max_error_weight", "variant"]
    assert code_entries[("decoding_fixture_check", "hqc_parity_check_toy")][
        "reproduction_fixture_roots"
    ] == ["benchmarks/code_based_toy_hqc/fixtures"]
    assert code_entries[("decoding_fixture_check", "hqc_circulant_syndrome_toy")][
        "default_estimator"
    ] == "toy-code-based-circulant-syndrome-decoder-estimator"
    assert code_entries[("decoding_fixture_check", "hqc_circulant_syndrome_toy")][
        "required_assumptions"
    ] == ["toy_hqc_circulant_syndrome_decoder_model"]
    assert code_entries[("decoding_fixture_check", "hqc_circulant_syndrome_toy")][
        "required_parameters"
    ] == ["block_size", "max_error_weight", "variant"]
    assert code_entries[("decoding_fixture_check", "hqc_circulant_syndrome_toy")][
        "review_gate"
    ] == "bounded_hqc_inspired_circulant_syndrome_fixture_only"
    assert code_entries[("decoding_fixture_check", "hqc_circulant_syndrome_toy")][
        "reproduction_fixture_roots"
    ] == ["benchmarks/code_based_toy_hqc/fixtures"]
    assert code_entries[("decoding_fixture_check", "hqc_circulant_erasure_toy")][
        "default_estimator"
    ] == "toy-code-based-circulant-erasure-decoder-estimator"
    assert code_entries[("decoding_fixture_check", "hqc_circulant_erasure_toy")][
        "required_assumptions"
    ] == ["toy_hqc_circulant_erasure_decoder_model"]
    assert code_entries[("decoding_fixture_check", "hqc_circulant_erasure_toy")][
        "required_parameters"
    ] == [
        "block_size",
        "first_block_erasure_count",
        "max_error_weight",
        "second_block_erasure_count",
        "variant",
    ]
    assert code_entries[("decoding_fixture_check", "hqc_circulant_erasure_toy")][
        "review_gate"
    ] == "bounded_hqc_inspired_circulant_erasure_fixture_only"
    assert code_entries[("decoding_fixture_check", "hqc_circulant_erasure_toy")][
        "reproduction_fixture_roots"
    ] == ["benchmarks/code_based_toy_hqc/fixtures"]
    assert code_entries[("decoding_fixture_check", "hqc_erasure_syndrome_toy")][
        "default_estimator"
    ] == "toy-code-based-erasure-syndrome-decoder-estimator"
    assert code_entries[("decoding_fixture_check", "hqc_erasure_syndrome_toy")][
        "required_assumptions"
    ] == ["toy_hqc_erasure_syndrome_decoder_model"]
    assert code_entries[("decoding_fixture_check", "hqc_erasure_syndrome_toy")][
        "required_parameters"
    ] == ["erasure_count", "max_error_weight", "variant"]
    assert code_entries[("decoding_fixture_check", "hqc_erasure_syndrome_toy")][
        "review_gate"
    ] == "bounded_hqc_inspired_erasure_syndrome_fixture_only"
    assert code_entries[("decoding_fixture_check", "hqc_erasure_syndrome_toy")][
        "reproduction_fixture_roots"
    ] == ["benchmarks/code_based_toy_hqc/fixtures"]
    assert code_entries[("decoding_fixture_check", "mdpc_bit_flip_toy")][
        "default_estimator"
    ] == "toy-code-based-bit-flip-decoder-estimator"
    assert code_entries[("decoding_fixture_check", "mdpc_bit_flip_toy")][
        "required_assumptions"
    ] == ["toy_mdpc_bit_flip_decoder_model"]
    assert code_entries[("decoding_fixture_check", "mdpc_bit_flip_toy")][
        "required_parameters"
    ] == ["max_iterations", "threshold", "variant"]
    assert code_entries[("decoding_fixture_check", "mdpc_bit_flip_toy")][
        "reproduction_fixture_roots"
    ] == ["benchmarks/code_based_toy_mdpc/fixtures"]
    assert code_entries[("decoding_fixture_check", "mdpc_black_gray_bit_flip_toy")][
        "default_estimator"
    ] == "toy-code-based-bit-flip-decoder-estimator"
    assert code_entries[("decoding_fixture_check", "mdpc_black_gray_bit_flip_toy")][
        "required_assumptions"
    ] == ["toy_mdpc_black_gray_bit_flip_decoder_model"]
    assert code_entries[("decoding_fixture_check", "mdpc_black_gray_bit_flip_toy")][
        "required_parameters"
    ] == ["black_threshold", "gray_threshold", "max_iterations", "variant"]
    assert code_entries[("decoding_fixture_check", "mdpc_black_gray_bit_flip_toy")][
        "review_gate"
    ] == "bounded_mdpc_black_gray_bit_flip_fixture_only"
    assert code_entries[("decoding_fixture_check", "mdpc_black_gray_bit_flip_toy")][
        "reproduction_fixture_roots"
    ] == ["benchmarks/code_based_toy_mdpc/fixtures"]
    assert code_entries[
        ("decoding_fixture_check", "mdpc_syndrome_weight_bit_flip_toy")
    ]["default_estimator"] == "toy-code-based-bit-flip-decoder-estimator"
    assert code_entries[
        ("decoding_fixture_check", "mdpc_syndrome_weight_bit_flip_toy")
    ]["required_assumptions"] == [
        "toy_mdpc_syndrome_weight_bit_flip_decoder_model"
    ]
    assert code_entries[
        ("decoding_fixture_check", "mdpc_syndrome_weight_bit_flip_toy")
    ]["required_parameters"] == [
        "max_iterations",
        "min_syndrome_weight_drop",
        "variant",
    ]
    assert code_entries[
        ("decoding_fixture_check", "mdpc_syndrome_weight_bit_flip_toy")
    ]["review_gate"] == "bounded_mdpc_syndrome_weight_bit_flip_fixture_only"
    assert code_entries[
        ("decoding_fixture_check", "mdpc_syndrome_weight_bit_flip_toy")
    ]["reproduction_fixture_roots"] == [
        "benchmarks/code_based_toy_mdpc/fixtures"
    ]
    assert code_entries[
        ("decoding_fixture_check", "classic_mceliece_syndrome_toy")
    ]["default_estimator"] == (
        "toy-code-based-classic-mceliece-syndrome-estimator"
    )
    assert code_entries[
        ("decoding_fixture_check", "classic_mceliece_syndrome_toy")
    ]["required_assumptions"] == [
        "toy_classic_mceliece_syndrome_decoder_model"
    ]
    assert code_entries[
        ("decoding_fixture_check", "classic_mceliece_syndrome_toy")
    ]["reproduction_fixture_roots"] == [
        "benchmarks/code_based_toy_classic_mceliece/fixtures"
    ]
    assert code_entries[
        ("decoding_fixture_check", "classic_mceliece_support_syndrome_toy")
    ]["default_estimator"] == (
        "toy-code-based-classic-mceliece-support-syndrome-estimator"
    )
    assert code_entries[
        ("decoding_fixture_check", "classic_mceliece_support_syndrome_toy")
    ]["required_assumptions"] == [
        "toy_classic_mceliece_support_syndrome_decoder_model"
    ]
    assert code_entries[
        ("decoding_fixture_check", "classic_mceliece_support_syndrome_toy")
    ]["required_parameters"] == [
        "max_error_weight",
        "support_size",
        "variant",
    ]
    assert code_entries[
        ("decoding_fixture_check", "classic_mceliece_support_syndrome_toy")
    ]["review_gate"] == (
        "bounded_classic_mceliece_inspired_public_support_fixture_only"
    )
    support_constraints = code_entries[
        ("decoding_fixture_check", "classic_mceliece_support_syndrome_toy")
    ]["target_constraints"]
    assert "support_size >= max_error_weight" in support_constraints
    assert "support_size <= n" in support_constraints
    assert "w <= n-k" not in support_constraints

    multivariate_entries = _entries_by_key(by_family["MULTIVARIATE"])
    assert by_family["MULTIVARIATE"]["operator_entry_count"] == 5
    assert multivariate_entries[("groebner_basis", "toy_mq_degree_bound")][
        "required_assumptions"
    ] == ["toy_mq_degree_bound_model"]
    assert multivariate_entries[("groebner_basis", "toy_mq_degree_bound")][
        "required_parameters"
    ] == ["degree_bound", "linear_algebra_omega", "model"]
    assert multivariate_entries[("groebner_basis", "toy_mq_degree_bound")][
        "review_gate"
    ] == "bounded_multivariate_toy_degree_bound_only"
    assert multivariate_entries[
        ("signature_fixture_check", "toy_uov_public_map_verify")
    ]["required_assumptions"] == ["toy_uov_public_map_verification_model"]
    assert multivariate_entries[
        ("signature_fixture_check", "toy_uov_public_map_verify")
    ]["required_parameters"] == [
        "oil_variables",
        "signature_model",
        "vinegar_variables",
    ]
    assert multivariate_entries[
        ("signature_fixture_check", "toy_uov_public_map_verify")
    ]["reproduction_fixture_roots"] == ["benchmarks/multivariate_toy_uov/fixtures"]
    assert multivariate_entries[
        ("signature_fixture_check", "toy_uov_public_map_verify")
    ]["review_gate"] == "bounded_multivariate_toy_uov_public_map_fixture_only"
    uov_constraints = multivariate_entries[
        ("signature_fixture_check", "toy_uov_public_map_verify")
    ]["target_constraints"]
    assert "field == GF(2)" in uov_constraints
    assert "oil_variables + vinegar_variables == variables" in uov_constraints
    assert "not a UOV, MAYO, or Rainbow result" in uov_constraints

    hash_entries = _entries_by_key(by_family["HASH_BASED"])
    assert by_family["HASH_BASED"]["operator_entry_count"] == 7
    assert hash_entries[("hash_signature_verification", "toy_fors_auth_path_verify")][
        "required_assumptions"
    ] == ["toy_hash_fors_auth_path_model"]
    assert hash_entries[("hash_signature_verification", "toy_fors_auth_path_verify")][
        "required_parameters"
    ] == ["selected_indices", "signature_model", "tree_count", "tree_height"]
    assert hash_entries[("hash_signature_verification", "toy_fors_auth_path_verify")][
        "review_gate"
    ] == "bounded_hash_fors_auth_path_fixture_only"
    assert hash_entries[
        ("hash_signature_verification", "toy_slh_dsa_hypertree_verify")
    ]["required_assumptions"] == ["toy_hash_slh_dsa_hypertree_model"]
    assert hash_entries[
        ("hash_signature_verification", "toy_slh_dsa_hypertree_verify")
    ]["required_parameters"] == [
        "fors_selected_indices",
        "fors_tree_count",
        "fors_tree_height",
        "hypertree_height",
        "hypertree_leaf_index",
        "signature_model",
        "wots_chain_count",
        "wots_max_chain_steps",
    ]
    assert hash_entries[
        ("hash_signature_verification", "toy_slh_dsa_hypertree_verify")
    ]["review_gate"] == "bounded_hash_slh_dsa_hypertree_fixture_only"
    assert hash_entries[("misuse_check", "toy_hash_reused_salt")][
        "required_parameters"
    ] == ["expected_reuse_groups", "fixture", "record_count", "salt_bytes"]
    assert hash_entries[("misuse_check", "toy_hash_reused_salt")][
        "reproduction_fixture_roots"
    ] == ["benchmarks/hash_based_toy_misuse/fixtures"]

    implementation_entries = _entries_by_key(by_family["IMPLEMENTATION_SECURITY"])
    assert by_family["IMPLEMENTATION_SECURITY"]["operator_entry_count"] == 9
    assert implementation_entries[
        ("constant_time_check", "toy_dudect_summary_threshold_check")
    ]["required_assumptions"] == ["toy_dudect_summary_model"]
    assert implementation_entries[
        ("constant_time_check", "toy_dudect_summary_threshold_check")
    ]["required_parameters"] == [
        "dudect_version",
        "fixed_cycles",
        "max_abs_t",
        "model",
        "random_cycles",
        "tool",
    ]
    assert implementation_entries[
        ("constant_time_check", "toy_dudect_summary_threshold_check")
    ]["review_gate"] == "json_only_toy_dudect_summary_only"
    assert implementation_entries[
        ("constant_time_check", "toy_ctgrind_secret_taint_summary_check")
    ]["required_assumptions"] == ["toy_ctgrind_secret_taint_summary_model"]
    assert implementation_entries[
        ("constant_time_check", "toy_ctgrind_secret_taint_summary_check")
    ]["required_parameters"] == [
        "checked_blocks",
        "ctgrind_version",
        "max_secret_dependent_branch_count",
        "max_secret_dependent_memory_access_count",
        "model",
        "secret_dependent_branch_count",
        "secret_dependent_memory_access_count",
        "tool",
    ]
    assert implementation_entries[
        ("constant_time_check", "toy_ctgrind_secret_taint_summary_check")
    ]["review_gate"] == "json_only_toy_ctgrind_secret_taint_summary_only"
    assert implementation_entries[
        ("benchmark_harness", "toy_binary_size_check")
    ]["required_assumptions"] == ["toy_binary_size_model"]
    assert implementation_entries[
        ("benchmark_harness", "toy_binary_size_check")
    ]["required_parameters"] == [
        "bss_bytes",
        "data_bytes",
        "max_total_bytes",
        "metric",
        "model",
        "rodata_bytes",
        "suite",
        "text_bytes",
    ]
    assert implementation_entries[
        ("benchmark_harness", "toy_binary_size_check")
    ]["review_gate"] == "json_only_toy_binary_size_only"
    assert implementation_entries[
        ("benchmark_harness", "toy_memory_footprint_check")
    ]["required_assumptions"] == ["toy_memory_footprint_model"]
    assert implementation_entries[
        ("benchmark_harness", "toy_memory_footprint_check")
    ]["required_parameters"] == [
        "code_bytes",
        "heap_bytes",
        "max_code_bytes",
        "max_heap_bytes",
        "max_stack_bytes",
        "metric",
        "model",
        "stack_bytes",
        "suite",
    ]
    assert implementation_entries[
        ("benchmark_harness", "toy_memory_footprint_check")
    ]["review_gate"] == "json_only_toy_memory_footprint_only"
    assert implementation_entries[
        ("benchmark_harness", "toy_stack_usage_check")
    ]["required_assumptions"] == ["toy_stack_usage_model"]
    assert implementation_entries[
        ("benchmark_harness", "toy_stack_usage_check")
    ]["required_parameters"] == [
        "max_stack_bytes",
        "metric",
        "model",
        "stack_samples",
        "suite",
    ]
    assert implementation_entries[
        ("benchmark_harness", "toy_stack_usage_check")
    ]["review_gate"] == "json_only_toy_stack_usage_only"

    isogeny_entries = _entries_by_key(by_family["ISOGENY_HISTORICAL"])
    assert by_family["ISOGENY_HISTORICAL"]["operator_entry_count"] == 3
    volcano_entry = isogeny_entries[
        ("historical_isogeny_reconstruction", "toy_volcano_walk_search")
    ]
    assert volcano_entry["default_estimator"] == (
        "toy-isogeny-historical-path-estimator"
    )
    assert volcano_entry["required_assumptions"] == [
        "historical_not_current_standard",
        "historical_toy_volcano_walk_model",
    ]
    assert volcano_entry["required_parameters"] == [
        "branching_factor",
        "case",
        "volcano_height",
        "walk_length",
    ]
    assert volcano_entry["review_gate"] == "historical_volcano_walk_toy_only"
    assert volcano_entry["reproduction_fixture_roots"] == [
        "benchmarks/isogeny_historical_toy_path/fixtures"
    ]
    assert "volcano_height <= 8" in volcano_entry["target_constraints"]
    assert "fixture graph levels move by at most one" in volcano_entry[
        "target_constraints"
    ]

    for family_name in (
        "CODE_BASED",
        "MULTIVARIATE",
        "HASH_BASED",
        "ISOGENY_HISTORICAL",
        "IMPLEMENTATION_SECURITY",
    ):
        for entry in by_family[family_name]["operators"]:
            assert entry["optional_external_estimator"] is None
            assert entry["default_estimator"] != "lattice-estimator"
            assert entry["security_claim"] is False
            assert entry["review_required_before_claims"] is True


def test_committed_family_operator_catalog_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "family_operator_catalog.json"
    committed = Path("docs/family_operator_catalog.json")

    write_family_operator_catalog(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_family_operator_catalog_cli_writes_catalog(tmp_path: Path) -> None:
    out = tmp_path / "family_operator_catalog.json"

    result = CliRunner().invoke(app, ["family-operator-catalog", "--out", str(out)])

    assert result.exit_code == 0
    assert f"family_operator_catalog={out}" in result.output
    assert json.loads(out.read_text())["schema_version"] == (
        "agades.pqc.family_operator_catalog.v1"
    )


def test_family_operator_catalog_verify_accepts_committed_catalog() -> None:
    result = verify_family_operator_catalog(Path("docs/family_operator_catalog.json"))

    assert result["schema_version"] == FAMILY_OPERATOR_CATALOG_VERIFICATION_SCHEMA
    assert result["accepted"] is True
    assert result["summary"] == {
        "applicability_validator_count": 6,
        "families": 9,
        "failure_count": 0,
        "families_with_operator_entries": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
        ],
        "lattice_estimator_operator_entries": 5,
        "non_lattice_lattice_estimator_operator_entries": 0,
        "operator_entries": 48,
        "schema_only_families": ["NTRU", "SIS"],
        "schema_only_operator_entries": 0,
        "support_level_counts": {
            "implemented": 2,
            "schema_only": 2,
            "toy_evaluator": 5,
        },
        "toy_evaluator_families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
    }
    assert result["failures"] == []


def test_family_operator_catalog_verify_rejects_lattice_estimator_on_non_lattice(
    tmp_path: Path,
) -> None:
    catalog = build_family_operator_catalog()
    by_family = {family["family"]: family for family in catalog["families"]}
    by_family["CODE_BASED"]["operators"][0]["default_estimator"] = "lattice-estimator"
    out = tmp_path / "family_operator_catalog.json"
    out.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")

    result = verify_family_operator_catalog(out)

    assert result["accepted"] is False
    assert result["failures"] == [
        "CODE_BASED: non-lattice operator entries must not use lattice-estimator."
    ]


def test_family_operator_catalog_imports_plugin_validators() -> None:
    catalog = build_family_operator_catalog()
    by_family = {family["family"]: family for family in catalog["families"]}
    registry = default_family_registry()

    for family, example_path in VALIDATOR_EXAMPLE_BY_FAMILY.items():
        validator_path = EXPECTED_VALIDATOR_BY_FAMILY[family]
        assert by_family[family]["applicability_validator"] == validator_path
        validator = _load_validator(validator_path)
        plan = AttackPlan.model_validate_json(Path(example_path).read_text())
        adapter = registry.get(TargetFamily(family))

        assert validator(plan) == adapter.validate_plan(plan)


def test_family_operator_catalog_verify_rejects_schema_only_runtime_entries(
    tmp_path: Path,
) -> None:
    catalog = build_family_operator_catalog()
    by_family = {family["family"]: family for family in catalog["families"]}
    by_family["NTRU"]["operators"] = [
        {
            "operator_type": "primal_usvp",
            "variant": None,
            "default_estimator": "mock-lattice-estimator",
            "optional_external_estimator": None,
            "required_assumptions": [],
            "required_parameters": ["beta"],
            "reproduction_fixture_roots": [],
            "review_gate": "unreviewed_schema_only_family",
            "security_claim": False,
            "support_status": "schema_only",
            "target_constraints": [],
            "review_required_before_claims": True,
        }
    ]
    out = tmp_path / "family_operator_catalog.json"
    out.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")

    result = verify_family_operator_catalog(out)

    assert result["accepted"] is False
    assert result["failures"] == [
        "NTRU: schema-only families must not publish runtime operator entries."
    ]


def test_family_operator_catalog_verify_rejects_summary_drift(
    tmp_path: Path,
) -> None:
    catalog = build_family_operator_catalog()
    catalog["summary"] = {
        **catalog["summary"],
        "operator_entries": 47,
    }
    out = tmp_path / "family_operator_catalog.json"
    out.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")

    result = verify_family_operator_catalog(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "catalog: summary is inconsistent with family entries."
    ]


def test_family_operator_catalog_verify_rejects_runtime_catalog_drift(
    tmp_path: Path,
) -> None:
    catalog = build_family_operator_catalog()
    by_family = {family["family"]: family for family in catalog["families"]}
    entries = _entries_by_key(by_family["CODE_BASED"])
    entries[("decoding_fixture_check", "hqc_circulant_erasure_toy")][
        "default_estimator"
    ] = "toy-code-based-erasure-syndrome-decoder-estimator"
    out = tmp_path / "family_operator_catalog.json"
    out.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")

    result = verify_family_operator_catalog(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "catalog: contents are not synchronized with the current runtime "
        "operator catalog."
    ]


def test_family_operator_catalog_verify_cli_prints_json() -> None:
    result = CliRunner().invoke(
        app,
        [
            "family-operator-catalog-verify",
            "--catalog",
            "docs/family_operator_catalog.json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == FAMILY_OPERATOR_CATALOG_VERIFICATION_SCHEMA
    assert payload["accepted"] is True
    assert payload["summary"]["operator_entries"] == 48


def _entries_by_key(family: dict[str, object]) -> dict[tuple[str, str | None], dict]:
    entries = family["operators"]
    assert isinstance(entries, list)
    return {
        (entry["operator_type"], entry["variant"]): entry
        for entry in entries
        if isinstance(entry, dict)
    }


def _load_validator(
    dotted_path: str,
) -> Callable[[AttackPlan], list[ValidationFinding]]:
    module_name, function_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    validator = getattr(module, function_name)
    assert callable(validator)
    return validator
