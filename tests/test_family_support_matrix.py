from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.family_support import (
    FAMILY_SUPPORT_VERIFICATION_SCHEMA,
    build_family_support_matrix,
    summarize_family_support_matrix,
    summarize_family_support_publication_gate,
    verify_family_support_matrix,
    write_family_support_matrix,
)


def test_family_support_matrix_describes_current_support_boundaries(
    tmp_path: Path,
) -> None:
    out = tmp_path / "family_support_matrix.json"

    matrix = write_family_support_matrix(out)

    assert matrix == build_family_support_matrix()
    assert json.loads(out.read_text()) == matrix
    assert matrix["schema_version"] == "agades.pqc.family_support.v1"
    assert matrix["project"]["package"] == "agades_pqc_gym"
    assert matrix["safety"]["lattice_estimator_is_universal_pqc_oracle"] is False
    assert matrix["safety"]["unsupported_families_return_fake_estimates"] is False
    assert matrix["summary"] == summarize_family_support_matrix(matrix)
    assert matrix["summary"] == {
        "benchmark_count": 78,
        "cross_family_review_source_count": 3,
        "families_with_future_reviewed_adapters": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
            "NTRU",
            "SIS",
        ],
        "family_count": 9,
        "implemented": ["LWE", "MLWE"],
        "per_family_future_reviewed_adapter_source_counts": {
            "CODE_BASED": 3,
            "HASH_BASED": 1,
            "IMPLEMENTATION_SECURITY": 8,
            "ISOGENY_HISTORICAL": 0,
            "LWE": 2,
            "MLWE": 2,
            "MULTIVARIATE": 1,
            "NTRU": 2,
            "SIS": 2,
        },
        "plugin_count": 6,
        "plugins": [
            "code_based",
            "hash_based",
            "implementation_security",
            "isogeny_historical",
            "lattice",
            "multivariate",
        ],
        "public_example_count": 79,
        "review_required_before_claims": True,
        "schema_only": ["NTRU", "SIS"],
        "support_level_counts": {
            "implemented": 2,
            "schema_only": 2,
            "toy_evaluator": 5,
        },
        "toy_evaluators": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
        "unique_future_reviewed_adapter_source_count": 15,
    }

    by_family = {family["family"]: family for family in matrix["families"]}
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

    assert by_family["LWE"]["plugin"] == "lattice"
    assert by_family["LWE"]["support_level"] == "implemented"
    assert by_family["LWE"]["evaluator_status"] == "implemented"
    assert by_family["LWE"]["optional_estimators"] == ["lattice-estimator"]
    assert by_family["LWE"]["future_reviewed_adapter_source_ids"] == [
        "facebook-lwe-benchmarking",
        "facebook-tapas",
    ]
    assert by_family["LWE"]["cross_family_review_source_ids"] == [
        "hf-post-quantum-crypto-en-instruction-seed",
        "hf-post-quantum-crypto-fr-instruction-seed",
        "hf-pqc-ssl-scans-migration-scoring",
    ]
    assert "primal_usvp" in by_family["LWE"]["operators"]
    assert by_family["LWE"]["public_example_count"] >= 3
    assert by_family["LWE"]["reproduction_status"] == (
        "downscaled_lwe_mlwe_fixture_solvers_and_estimator_replay_available_for_public_toy_targets"
    )

    assert by_family["MLWE"]["support_level"] == "implemented"
    assert by_family["MLWE"]["public_example_count"] == 2
    assert by_family["MLWE"]["benchmark_count"] == 2
    assert by_family["MLWE"]["reproduction_status"] == (
        "downscaled_lwe_mlwe_fixture_solvers_and_estimator_replay_available_for_public_toy_targets"
    )

    assert by_family["NTRU"]["plugin"] == "lattice"
    assert by_family["NTRU"]["support_level"] == "schema_only"
    assert by_family["NTRU"]["evaluator_status"] == "unsupported_until_review"
    assert by_family["NTRU"]["operators"] == []
    assert by_family["NTRU"]["public_example_count"] == 1
    assert by_family["NTRU"]["benchmark_count"] == 1
    assert by_family["SIS"]["support_level"] == "schema_only"
    assert by_family["SIS"]["evaluator_status"] == "unsupported_until_review"
    assert by_family["SIS"]["operators"] == []
    assert by_family["SIS"]["public_example_count"] == 1
    assert by_family["SIS"]["benchmark_count"] == 1
    assert by_family["NTRU"]["future_reviewed_adapter_source_ids"] == [
        "facebook-lwe-benchmarking",
        "facebook-tapas",
    ]

    assert by_family["CODE_BASED"]["plugin"] == "code_based"
    assert by_family["CODE_BASED"]["support_level"] == "toy_evaluator"
    assert by_family["CODE_BASED"]["evaluator_status"] == "implemented_toy"
    assert by_family["CODE_BASED"]["default_estimator"] == (
        "toy-code-based-isd-estimator"
    )
    assert by_family["CODE_BASED"]["optional_estimators"] == [
        "toy-code-based-bit-flip-decoder-estimator",
            "toy-code-based-classic-mceliece-support-syndrome-estimator",
            "toy-code-based-classic-mceliece-syndrome-estimator",
            "toy-code-based-circulant-erasure-decoder-estimator",
            "toy-code-based-circulant-syndrome-decoder-estimator",
        "toy-code-based-erasure-syndrome-decoder-estimator",
        "toy-code-based-parity-check-decoder-estimator",
        "toy-code-based-repetition-decoder-estimator",
        "toy-code-based-weighted-repetition-decoder-estimator",
    ]
    assert "decoding_fixture_check" in by_family["CODE_BASED"]["operators"]
    assert by_family["CODE_BASED"]["reproduction_status"] == (
        "toy_syndrome_hqc_mdpc_and_classic_mceliece_fixture_solvers_available_"
        "for_public_fixtures"
    )
    assert by_family["CODE_BASED"]["future_reviewed_adapter_source_ids"] == [
        "nist-bike-round4-status",
        "nist-classic-mceliece-round4-status",
        "nist-hqc-standardization-track",
    ]
    assert by_family["CODE_BASED"]["public_example_count"] == 21
    assert by_family["CODE_BASED"]["benchmark_count"] == 21

    assert by_family["MULTIVARIATE"]["plugin"] == "multivariate"
    assert by_family["MULTIVARIATE"]["support_level"] == "toy_evaluator"
    assert by_family["MULTIVARIATE"]["evaluator_status"] == "implemented_toy"
    assert by_family["MULTIVARIATE"]["default_estimator"] == (
        "toy-multivariate-estimator"
    )
    assert "minrank_attack" in by_family["MULTIVARIATE"]["operators"]
    assert "signature_fixture_check" in by_family["MULTIVARIATE"]["operators"]
    assert by_family["MULTIVARIATE"]["reproduction_status"] == (
        "toy_mq_and_minrank_solvers_available_for_public_gf2_fixtures"
    )
    assert by_family["MULTIVARIATE"]["future_reviewed_adapter_source_ids"] == [
        "nist-additional-signatures-round3-multivariate"
    ]
    assert by_family["MULTIVARIATE"]["public_example_count"] == 12
    assert by_family["MULTIVARIATE"]["benchmark_count"] == 13
    assert (
        "examples/attack_plans/multivariate_mayo_schema_placeholder.json"
        in by_family["MULTIVARIATE"]["public_examples"]
    )
    assert (
        "examples/attack_plans/multivariate_rainbow_historical_schema_placeholder.json"
        in by_family["MULTIVARIATE"]["public_examples"]
    )
    assert (
        "benchmarks/multivariate_schema_only/mayo_like_toy_schema.json"
        in by_family["MULTIVARIATE"]["benchmarks"]
    )
    assert (
        "benchmarks/multivariate_schema_only/rainbow_historical_toy_schema.json"
        in by_family["MULTIVARIATE"]["benchmarks"]
    )
    assert (
        "examples/attack_plans/multivariate_uov_public_map_toy.json"
        in by_family["MULTIVARIATE"]["public_examples"]
    )
    assert (
        "benchmarks/multivariate_toy_uov/toy_uov_public_map_gf2_v5_e3.json"
        in by_family["MULTIVARIATE"]["benchmarks"]
    )

    assert by_family["HASH_BASED"]["plugin"] == "hash_based"
    assert by_family["HASH_BASED"]["support_level"] == "toy_evaluator"
    assert by_family["HASH_BASED"]["evaluator_status"] == "implemented_toy"
    assert by_family["HASH_BASED"]["default_estimator"] == "toy-hash-bound-estimator"
    assert "hash_signature_verification" in by_family["HASH_BASED"]["operators"]
    assert by_family["HASH_BASED"]["reproduction_status"] == (
        "toy_preimage_collision_signature_merkle_fors_slh_dsa_and_misuse_verifiers_"
        "available_for_public_fixtures"
    )
    assert by_family["HASH_BASED"]["future_reviewed_adapter_source_ids"] == [
        "nist-fips-205-slh-dsa-reference"
    ]
    assert by_family["HASH_BASED"]["public_example_count"] == 8
    assert by_family["HASH_BASED"]["benchmark_count"] == 9

    assert by_family["ISOGENY_HISTORICAL"]["plugin"] == "isogeny_historical"
    assert by_family["ISOGENY_HISTORICAL"]["support_level"] == "toy_evaluator"
    assert by_family["ISOGENY_HISTORICAL"]["evaluator_status"] == "implemented_toy"
    assert by_family["ISOGENY_HISTORICAL"]["default_estimator"] == (
        "toy-isogeny-historical-path-estimator"
    )
    assert by_family["ISOGENY_HISTORICAL"]["reproduction_status"] == (
        "historical_toy_path_verifier_available_for_public_fixtures"
    )
    assert by_family["ISOGENY_HISTORICAL"]["future_reviewed_adapter_source_ids"] == []
    assert by_family["ISOGENY_HISTORICAL"]["public_example_count"] == 4
    assert by_family["ISOGENY_HISTORICAL"]["benchmark_count"] == 5
    assert (
        "examples/attack_plans/isogeny_historical_volcano_walk_toy.json"
        in by_family["ISOGENY_HISTORICAL"]["public_examples"]
    )
    assert (
        "benchmarks/isogeny_historical_toy_path/"
        "toy_volcano_walk_fixture_verify.json"
        in by_family["ISOGENY_HISTORICAL"]["benchmarks"]
    )

    assert by_family["IMPLEMENTATION_SECURITY"]["plugin"] == (
        "implementation_security"
    )
    assert by_family["IMPLEMENTATION_SECURITY"]["support_level"] == "toy_evaluator"
    assert by_family["IMPLEMENTATION_SECURITY"]["evaluator_status"] == (
        "implemented_toy"
    )
    assert by_family["IMPLEMENTATION_SECURITY"]["default_estimator"] == (
        "toy-implementation-security-estimator"
    )
    assert by_family["IMPLEMENTATION_SECURITY"]["reproduction_status"] == (
        "toy_kat_acvp_timing_and_benchmark_verifiers_available_for_public_"
        "json_only_fixtures"
    )
    implementation_security_sources = by_family["IMPLEMENTATION_SECURITY"][
        "future_reviewed_adapter_source_ids"
    ]
    assert implementation_security_sources == [
        "ctgrind-secret-taint-analysis",
        "dudect-statistical-timing-leakage",
        "hf-sc2026-side-channel-research",
        "liboqs-implementation-harness",
        "nist-acvp-pqc-vectors",
        "pq-code-package-native-implementations",
        "pqm4-cortexm4-benchmarking",
        "timecop-supercop-policy-checks",
    ]
    assert by_family["IMPLEMENTATION_SECURITY"]["public_example_count"] == 20
    assert by_family["IMPLEMENTATION_SECURITY"]["benchmark_count"] == 21
    assert (
        "examples/attack_plans/implementation_security_dudect_summary_toy.json"
        in by_family["IMPLEMENTATION_SECURITY"]["public_examples"]
    )
    assert (
        "examples/attack_plans/implementation_security_dudect_schema.json"
        in by_family["IMPLEMENTATION_SECURITY"]["public_examples"]
    )
    assert (
        "examples/attack_plans/implementation_security_ctgrind_schema.json"
        in by_family["IMPLEMENTATION_SECURITY"]["public_examples"]
    )
    assert (
        "examples/attack_plans/implementation_security_ctgrind_taint_toy.json"
        in by_family["IMPLEMENTATION_SECURITY"]["public_examples"]
    )
    assert (
        "examples/attack_plans/implementation_security_nist_acvp_schema.json"
        in by_family["IMPLEMENTATION_SECURITY"]["public_examples"]
    )
    assert (
        "examples/attack_plans/implementation_security_timecop_schema.json"
        in by_family["IMPLEMENTATION_SECURITY"]["public_examples"]
    )
    assert (
        "benchmarks/implementation_security_schema_only/"
        "dudect_timing_leakage_schema.json"
        in by_family["IMPLEMENTATION_SECURITY"]["benchmarks"]
    )
    assert (
        "benchmarks/implementation_security_toy_timing/"
        "toy_dudect_summary_verify.json"
        in by_family["IMPLEMENTATION_SECURITY"]["benchmarks"]
    )
    assert (
        "benchmarks/implementation_security_schema_only/"
        "ctgrind_secret_taint_schema.json"
        in by_family["IMPLEMENTATION_SECURITY"]["benchmarks"]
    )
    assert (
        "benchmarks/implementation_security_toy_timing/"
        "toy_ctgrind_taint_verify.json"
        in by_family["IMPLEMENTATION_SECURITY"]["benchmarks"]
    )
    assert (
        "benchmarks/implementation_security_schema_only/"
        "nist_acvp_pqc_vectors_schema.json"
        in by_family["IMPLEMENTATION_SECURITY"]["benchmarks"]
    )
    assert (
        "benchmarks/implementation_security_schema_only/"
        "timecop_supercop_policy_schema.json"
        in by_family["IMPLEMENTATION_SECURITY"]["benchmarks"]
    )


def test_committed_family_support_matrix_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "family_support_matrix.json"
    committed = Path("docs/family_support_matrix.json")

    write_family_support_matrix(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_family_support_cli_writes_matrix(tmp_path: Path) -> None:
    out = tmp_path / "family_support_matrix.json"

    result = CliRunner().invoke(app, ["family-support", "--out", str(out)])

    assert result.exit_code == 0
    assert f"family_support={out}" in result.output
    assert json.loads(out.read_text())["schema_version"] == (
        "agades.pqc.family_support.v1"
    )


def test_family_support_verify_accepts_committed_matrix() -> None:
    result = verify_family_support_matrix(Path("docs/family_support_matrix.json"))

    assert result["schema_version"] == FAMILY_SUPPORT_VERIFICATION_SCHEMA
    assert result["accepted"] is True
    assert result["summary"] == {
        "benchmark_count": 78,
        "cross_family_review_source_count": 3,
        "family_count": 9,
        "failure_count": 0,
        "families_with_future_reviewed_adapters": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
            "NTRU",
            "SIS",
        ],
        "implemented": ["LWE", "MLWE"],
        "per_family_future_reviewed_adapter_source_counts": {
            "CODE_BASED": 3,
            "HASH_BASED": 1,
            "IMPLEMENTATION_SECURITY": 8,
            "ISOGENY_HISTORICAL": 0,
            "LWE": 2,
            "MLWE": 2,
            "MULTIVARIATE": 1,
            "NTRU": 2,
            "SIS": 2,
        },
        "plugin_count": 6,
        "plugins": [
            "code_based",
            "hash_based",
            "implementation_security",
            "isogeny_historical",
            "lattice",
            "multivariate",
        ],
        "public_example_count": 79,
        "review_required_before_claims": True,
        "schema_only": ["NTRU", "SIS"],
        "support_level_counts": {
            "implemented": 2,
            "schema_only": 2,
            "toy_evaluator": 5,
        },
        "toy_evaluators": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
        "unique_future_reviewed_adapter_source_count": 15,
    }
    assert result["failures"] == []


def test_family_support_publication_gate_summary_tracks_platforms() -> None:
    family_support = summarize_family_support_matrix(build_family_support_matrix())
    platform_family_supports = {
        "huggingface_collection": dict(family_support),
        "nvidia": dict(family_support),
        "prime_intellect": dict(family_support),
    }

    assert summarize_family_support_publication_gate(
        family_support,
        platform_family_supports,
        required_platforms=(
            "huggingface_collection",
            "nvidia",
            "prime_intellect",
        ),
    ) == {
        "family_count": 9,
        "implemented": ["LWE", "MLWE"],
        "schema_only": ["NTRU", "SIS"],
        "toy_evaluators": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
        "families_with_future_reviewed_adapters": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
            "NTRU",
            "SIS",
        ],
        "future_reviewed_adapter_sources_by_family": 21,
        "unique_future_reviewed_adapter_source_count": 15,
        "review_required_before_claims": True,
        "platform_support": {
            "family_counts_match": True,
            "missing_claim_review_gate": [],
            "platforms": [
                "huggingface_collection",
                "nvidia",
                "prime_intellect",
            ],
            "platforms_with_claim_review_gate": [
                "huggingface_collection",
                "nvidia",
                "prime_intellect",
            ],
            "surface_count": 3,
        },
    }


def test_family_support_publication_gate_summary_is_detached() -> None:
    family_support = summarize_family_support_matrix(build_family_support_matrix())
    platform_family_supports = {
        "huggingface_collection": dict(family_support),
        "nvidia": dict(family_support),
        "prime_intellect": dict(family_support),
    }

    summary = summarize_family_support_publication_gate(
        family_support,
        platform_family_supports,
        required_platforms=(
            "huggingface_collection",
            "nvidia",
            "prime_intellect",
        ),
    )
    summary["implemented"].append("BOGUS")
    summary["platform_support"]["platforms"].append("bogus")

    assert family_support["implemented"] == ["LWE", "MLWE"]
    assert "bogus" not in platform_family_supports


def test_family_support_verify_rejects_future_source_contract_drift(
    tmp_path: Path,
) -> None:
    matrix = build_family_support_matrix()
    by_family = {family["family"]: family for family in matrix["families"]}
    by_family["CODE_BASED"]["future_reviewed_adapter_source_ids"] = [
        "unreviewed-code-based-source"
    ]
    out = tmp_path / "family_support_matrix.json"
    out.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")

    result = verify_family_support_matrix(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "CODE_BASED: future_reviewed_adapter_source_ids drifted."
    ]


def test_family_support_verify_rejects_summary_drift(
    tmp_path: Path,
) -> None:
    matrix = build_family_support_matrix()
    matrix["summary"]["family_count"] = 8
    out = tmp_path / "family_support_matrix.json"
    out.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")

    result = verify_family_support_matrix(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "manifest: summary is inconsistent with family entries."
    ]


def test_family_support_verify_rejects_runtime_matrix_drift(
    tmp_path: Path,
) -> None:
    matrix = build_family_support_matrix()
    by_family = {family["family"]: family for family in matrix["families"]}
    by_family["CODE_BASED"]["default_estimator"] = "stale-code-based-estimator"
    out = tmp_path / "family_support_matrix.json"
    out.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")

    result = verify_family_support_matrix(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "manifest: contents are not synchronized with the current runtime "
        "family support matrix."
    ]


def test_family_support_verify_rejects_non_lattice_implemented_family(
    tmp_path: Path,
) -> None:
    matrix = build_family_support_matrix()
    by_family = {family["family"]: family for family in matrix["families"]}
    by_family["CODE_BASED"]["support_level"] = "implemented"
    out = tmp_path / "family_support_matrix.json"
    out.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")

    result = verify_family_support_matrix(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "CODE_BASED: non-lattice families must not be marked implemented."
    ]


def test_family_support_verify_rejects_lattice_oracle_claim(
    tmp_path: Path,
) -> None:
    matrix = build_family_support_matrix()
    matrix["safety"]["lattice_estimator_is_universal_pqc_oracle"] = True
    out = tmp_path / "family_support_matrix.json"
    out.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")

    result = verify_family_support_matrix(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "manifest: safety.lattice_estimator_is_universal_pqc_oracle must be false."
    ]


def test_family_support_verify_cli_prints_json() -> None:
    result = CliRunner().invoke(
        app,
        [
            "family-support-verify",
            "--matrix",
            "docs/family_support_matrix.json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == FAMILY_SUPPORT_VERIFICATION_SCHEMA
    assert payload["accepted"] is True
    assert payload["summary"]["family_count"] == 9


def test_family_support_verify_cli_exits_nonzero_on_failure(
    tmp_path: Path,
) -> None:
    matrix = build_family_support_matrix()
    by_family = {family["family"]: family for family in matrix["families"]}
    by_family["NTRU"]["support_level"] = "implemented"
    out = tmp_path / "family_support_matrix.json"
    out.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")

    result = CliRunner().invoke(
        app,
        ["family-support-verify", "--matrix", str(out)],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["accepted"] is False
    assert payload["failures"] == [
        "NTRU: NTRU and SIS must remain schema_only until reviewed."
    ]
