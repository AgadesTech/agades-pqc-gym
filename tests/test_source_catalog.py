from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.family_operator_catalog import (
    build_family_operator_catalog,
)
from agades_pqc_gym.integrations.source_catalog import (
    SOURCE_CATALOG_VERIFICATION_SCHEMA,
    build_source_catalog,
    verify_source_catalog,
    write_source_catalog,
)


def test_source_catalog_describes_public_oss_anchors(tmp_path: Path) -> None:
    out = tmp_path / "source_catalog.json"

    catalog = write_source_catalog(out)

    assert catalog == build_source_catalog()
    assert json.loads(out.read_text()) == catalog
    assert catalog["schema_version"] == "agades.pqc.source_catalog.v1"
    assert catalog["project"]["package"] == "agades_pqc_gym"
    assert catalog["safety"]["contains_private_traces"] is False
    assert catalog["safety"]["security_claim"] is False
    assert catalog["safety"]["arbitrary_code_execution"] is False
    assert catalog["summary"] == {
        "current_public_surface_count": 15,
        "current_public_surfaces": [
            "agades-benchmark-source-contracts",
            "agades-family-plugin-manifest",
            "agades-family-registry-manifest",
            "agades-family-support-matrix",
            "agades-hf-collection",
            "agades-hf-dataset",
            "agades-hf-space",
            "agades-lattice-estimator-baseline-contracts",
            "agades-nvidia-accelerator",
            "agades-nvidia-publication-handoff",
            "agades-prime-environment",
            "agades-prime-publication-handoff",
            "agades-public-run-export",
            "agades-publication-manifest",
            "prime-verifiers",
        ],
        "future_reviewed_adapter_count": 19,
        "future_reviewed_adapters": [
            "ctgrind",
            "dudect",
            "facebook-lwe-benchmarking",
            "facebook-tapas",
            "hf-post-quantum-crypto-en",
            "hf-post-quantum-crypto-fr",
            "hf-pqc-ssl-scans",
            "hf-sc2026-side-channel",
            "liboqs",
            "nist-acvp",
            "nist-additional-signatures-round3",
            "nist-bike-round4-status",
            "nist-classic-mceliece-round4-status",
            "nist-hqc-selection",
            "pq-code-package",
            "pqclean",
            "pqm4",
            "prime-rl",
            "timecop-supercop",
        ],
        "local_artifact_source_count": 14,
        "non_lattice_toy_evaluator_count": 41,
        "non_lattice_toy_operator_families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
        "non_lattice_toy_operator_security_claims": 0,
        "non_lattice_toy_operator_variant_count": 41,
        "platform_counts": {
            "ebacs": 1,
            "github": 14,
            "hugging_face": 8,
            "nist": 7,
            "nvidia": 3,
            "prime_intellect": 8,
        },
        "platforms": [
            "ebacs",
            "github",
            "hugging_face",
            "nist",
            "nvidia",
            "prime_intellect",
        ],
        "requires_gpu_source_count": 3,
        "source_count": 41,
        "source_map_only": [
            "nvidia-inception",
            "prime-autonanogpt-speedrun",
            "prime-autonomous-speedrunning-experiments",
            "prime-quickstart",
        ],
        "source_map_only_count": 4,
    }
    assert catalog["scope"]["non_lattice_toy_evaluators"] == [
        "code_based_bjmm_isd",
        "code_based_classic_mceliece_support_syndrome",
        "code_based_classic_mceliece_syndrome",
        "code_based_dumer_isd",
        "code_based_hqc_circulant_erasure",
        "code_based_hqc_circulant_syndrome",
        "code_based_hqc_erasure_syndrome",
        "code_based_hqc_parity_check",
        "code_based_hqc_repetition",
        "code_based_hqc_weighted_repetition",
        "code_based_lee_brickell_isd",
        "code_based_mdpc_bit_flip",
        "code_based_mdpc_black_gray_bit_flip",
        "code_based_mdpc_syndrome_weight_bit_flip",
        "code_based_prange_isd",
        "code_based_qc_rotation",
        "code_based_stern_isd",
        "hash_based_collision_bound",
        "hash_based_fors_auth_path_verify",
        "hash_based_merkle_auth_path_verify",
        "hash_based_misuse_reused_salt",
        "hash_based_preimage_bound",
        "hash_based_slh_dsa_hypertree_verify",
        "hash_based_wots_chain_verify",
        "implementation_security_acvp_vector_set",
        "implementation_security_benchmark_summary",
        "implementation_security_binary_size",
        "implementation_security_ctgrind_secret_taint",
        "implementation_security_dudect_summary",
        "implementation_security_kat_digest",
        "implementation_security_memory_footprint",
        "implementation_security_stack_usage",
        "implementation_security_timing_check",
        "isogeny_historical_commutative_walk",
        "isogeny_historical_sidh_path",
        "isogeny_historical_volcano_walk",
        "multivariate_minrank_search",
        "multivariate_mq_degree_bound",
        "multivariate_mq_hybrid_search",
        "multivariate_mq_search",
        "multivariate_uov_public_map_verify",
    ]

    by_id = {source["id"]: source for source in catalog["sources"]}
    assert by_id["facebook-tapas"]["family"] == "lattice"
    assert by_id["facebook-tapas"]["integration_status"] == "future_reviewed_adapter"
    assert by_id["facebook-lwe-benchmarking"]["requires_gpu"] is True
    assert by_id["hf-post-quantum-crypto-fr"]["kind"] == "instruction_seed_dataset"
    assert by_id["hf-post-quantum-crypto-fr"]["current_use"] == (
        "future_pqc_instruction_eval_seed"
    )
    assert by_id["hf-post-quantum-crypto-fr"]["integration_status"] == (
        "future_reviewed_adapter"
    )
    assert by_id["hf-post-quantum-crypto-en"]["kind"] == "instruction_seed_dataset"
    assert by_id["hf-post-quantum-crypto-en"]["current_use"] == (
        "future_pqc_instruction_eval_seed"
    )
    assert by_id["hf-pqc-ssl-scans"]["kind"] == "migration_scoring_dataset"
    assert by_id["hf-pqc-ssl-scans"]["current_use"] == (
        "future_pqc_migration_scoring_anchor"
    )
    assert by_id["hf-sc2026-side-channel"]["kind"] == "side_channel_dataset"
    assert by_id["hf-sc2026-side-channel"]["family"] == "implementation_security"
    assert by_id["hf-sc2026-side-channel"]["requires_gpu"] is True
    assert by_id["hf-sc2026-side-channel"]["current_use"] == (
        "future_side_channel_research_anchor"
    )
    assert by_id["lattice-estimator"]["current_use"] == "optional_lattice_estimator"
    assert by_id["nist-hqc-selection"]["family"] == "code_based"
    assert by_id["nist-hqc-selection"]["integration_status"] == (
        "future_reviewed_adapter"
    )
    assert by_id["nist-bike-round4-status"]["family"] == "code_based"
    assert by_id["nist-bike-round4-status"]["current_use"] == (
        "future_code_based_nonselected_candidate_anchor"
    )
    assert by_id["nist-classic-mceliece-round4-status"]["family"] == "code_based"
    assert by_id["nist-classic-mceliece-round4-status"]["current_use"] == (
        "future_code_based_nonselected_candidate_anchor"
    )
    assert by_id["nist-fips-205"]["family"] == "hash_based"
    assert by_id["nist-fips-205"]["kind"] == "standard"
    assert by_id["nist-additional-signatures-round3"]["family"] == "multivariate"
    assert by_id["nist-additional-signatures-round3"]["current_use"] == (
        "future_multivariate_signature_anchor"
    )
    assert by_id["liboqs"]["family"] == "implementation_security"
    assert by_id["pq-code-package"]["family"] == "implementation_security"
    assert by_id["pq-code-package"]["kind"] == "high_assurance_implementation_corpus"
    assert by_id["pq-code-package"]["integration_status"] == (
        "future_reviewed_adapter"
    )
    assert "mlkem-native" in " ".join(by_id["pq-code-package"]["safety_notes"])
    assert by_id["pqm4"]["kind"] == "embedded_benchmark_harness"
    assert by_id["pqm4"]["integration_status"] == "future_reviewed_adapter"
    assert by_id["nist-acvp"]["platform"] == "nist"
    assert by_id["nist-acvp"]["kind"] == "validation_protocol"
    assert by_id["dudect"]["family"] == "implementation_security"
    assert by_id["dudect"]["kind"] == "statistical_timing_leakage_tool"
    assert by_id["dudect"]["integration_status"] == "future_reviewed_adapter"
    assert "not a constant-time proof" in " ".join(by_id["dudect"]["safety_notes"])
    assert by_id["ctgrind"]["family"] == "implementation_security"
    assert by_id["ctgrind"]["kind"] == "dynamic_secret_taint_tool"
    assert by_id["ctgrind"]["integration_status"] == "future_reviewed_adapter"
    assert "not executed by the current public verifier" in " ".join(
        by_id["ctgrind"]["safety_notes"]
    ).lower()
    assert by_id["timecop-supercop"]["platform"] == "ebacs"
    assert by_id["timecop-supercop"]["family"] == "implementation_security"
    assert by_id["timecop-supercop"]["kind"] == "supercop_constant_time_tool"
    assert by_id["timecop-supercop"]["integration_status"] == (
        "future_reviewed_adapter"
    )
    assert by_id["prime-verifiers"]["platform"] == "prime_intellect"
    assert by_id["prime-quickstart"]["kind"] == "developer_onboarding"
    assert by_id["prime-quickstart"]["integration_status"] == "source_map_only"
    assert by_id["prime-rl"]["kind"] == "agentic_rl_framework"
    assert by_id["prime-rl"]["integration_status"] == "future_reviewed_adapter"
    assert by_id["prime-rl"]["current_use"] == "future_agentic_rl_training_anchor"
    assert by_id["prime-autonomous-speedrunning-experiments"]["url"] == (
        "https://github.com/PrimeIntellect-ai/experiments-autonomous-speedrunning"
    )
    assert by_id["prime-autonomous-speedrunning-experiments"]["current_use"] == (
        "public_evaluator_observability_pattern"
    )
    assert by_id["agades-family-support-matrix"]["url"] == (
        "docs/family_support_matrix.json"
    )
    assert by_id["agades-family-support-matrix"]["integration_status"] == (
        "current_public_surface"
    )
    assert by_id["agades-family-registry-manifest"]["url"] == (
        "docs/family_registry_manifest.json"
    )
    assert by_id["agades-family-registry-manifest"]["integration_status"] == (
        "current_public_surface"
    )
    assert by_id["agades-family-registry-manifest"]["current_use"] == (
        "current_runtime_family_registry_contract"
    )
    assert by_id["agades-family-plugin-manifest"]["url"] == (
        "docs/family_plugin_manifest.json"
    )
    assert by_id["agades-family-plugin-manifest"]["integration_status"] == (
        "current_public_surface"
    )
    assert by_id["agades-family-plugin-manifest"]["current_use"] == (
        "current_family_plugin_descriptor_contract"
    )
    assert by_id["agades-publication-manifest"]["platform"] == "github"
    assert by_id["agades-publication-manifest"]["url"] == (
        "docs/publication_manifest.json"
    )
    assert by_id["agades-publication-manifest"]["current_use"] == (
        "current_release_readiness_contract"
    )
    assert by_id["agades-benchmark-source-contracts"]["url"] == (
        "docs/benchmark_source_contracts.json"
    )
    assert by_id["agades-benchmark-source-contracts"]["current_use"] == (
        "current_future_adapter_contract"
    )
    assert by_id["agades-lattice-estimator-baseline-contracts"]["url"] == (
        "docs/lattice_estimator_baseline_contracts.json"
    )
    assert by_id["agades-lattice-estimator-baseline-contracts"][
        "integration_status"
    ] == "current_public_surface"
    assert by_id["agades-lattice-estimator-baseline-contracts"]["current_use"] == (
        "current_lattice_estimator_baseline_reproduction_contract"
    )
    assert by_id["agades-lattice-estimator-baseline-contracts"]["family"] == "lattice"
    assert "not a numeric baseline" in " ".join(
        by_id["agades-lattice-estimator-baseline-contracts"]["safety_notes"]
    )
    assert by_id["agades-hf-space"]["url"] == "hf/space_manifest.json"
    assert by_id["agades-hf-space"]["integration_status"] == (
        "current_public_surface"
    )
    assert by_id["agades-hf-space"]["current_use"] == (
        "current_public_gradio_space_contract"
    )
    assert by_id["agades-hf-collection"]["url"] == "hf/collection_manifest.json"
    assert by_id["agades-hf-collection"]["integration_status"] == (
        "current_public_surface"
    )
    assert by_id["agades-hf-collection"]["current_use"] == (
        "current_public_collection_contract"
    )
    assert by_id["agades-prime-environment"]["url"] == (
        "prime_intellect/verifiers_environment/prime_manifest.json"
    )
    assert by_id["agades-prime-environment"]["platform"] == "prime_intellect"
    assert by_id["agades-prime-environment"]["integration_status"] == (
        "current_public_surface"
    )
    assert by_id["agades-prime-environment"]["current_use"] == (
        "current_public_verifier_environment_contract"
    )
    assert by_id["agades-prime-publication-handoff"]["url"] == (
        "docs/prime_publication_handoff.json"
    )
    assert by_id["agades-prime-publication-handoff"]["platform"] == (
        "prime_intellect"
    )
    assert by_id["agades-prime-publication-handoff"]["integration_status"] == (
        "current_public_surface"
    )
    assert by_id["agades-prime-publication-handoff"]["current_use"] == (
        "current_prime_publication_review_handoff"
    )
    assert by_id["agades-public-run-export"]["url"] == (
        "public/run_export/manifest.json"
    )
    assert by_id["agades-public-run-export"]["platform"] == "prime_intellect"
    assert by_id["agades-public-run-export"]["integration_status"] == (
        "current_public_surface"
    )
    assert by_id["agades-public-run-export"]["current_use"] == (
        "current_flat_public_run_review_surface"
    )
    assert by_id["agades-nvidia-accelerator"]["url"] == (
        "nvidia/accelerator_manifest.json"
    )
    assert by_id["agades-nvidia-accelerator"]["platform"] == "nvidia"
    assert by_id["agades-nvidia-accelerator"]["integration_status"] == (
        "current_public_surface"
    )
    assert by_id["agades-nvidia-accelerator"]["current_use"] == (
        "current_public_accelerator_contract"
    )
    assert by_id["agades-nvidia-publication-handoff"]["url"] == (
        "docs/nvidia_publication_handoff.json"
    )
    assert by_id["agades-nvidia-publication-handoff"]["platform"] == "nvidia"
    assert by_id["agades-nvidia-publication-handoff"]["integration_status"] == (
        "current_public_surface"
    )
    assert by_id["agades-nvidia-publication-handoff"]["current_use"] == (
        "current_nvidia_publication_review_handoff"
    )
    assert (
        "uv run agades-pqc family-registry-manifest --out "
        "docs/family_registry_manifest.json"
    ) in catalog["release_gates"]
    assert (
        "uv run agades-pqc family-registry-manifest-verify --manifest "
        "docs/family_registry_manifest.json"
    ) in catalog["release_gates"]
    assert (
        "uv run agades-pqc family-plugin-manifest --out "
        "docs/family_plugin_manifest.json"
    ) in catalog["release_gates"]
    assert (
        "uv run agades-pqc family-plugin-manifest-verify --manifest "
        "docs/family_plugin_manifest.json"
    ) in catalog["release_gates"]
    assert (
        "uv run agades-pqc prime-publication-handoff --out "
        "docs/prime_publication_handoff.json"
    ) in catalog["release_gates"]
    assert (
        "uv run agades-pqc prime-publication-handoff-verify --handoff "
        "docs/prime_publication_handoff.json"
    ) in catalog["release_gates"]
    assert (
        "uv run agades-pqc public-run-export --out public/run_export"
    ) in catalog["release_gates"]
    assert (
        "uv run agades-pqc public-run-export-verify --export public/run_export"
    ) in catalog["release_gates"]

    for source in catalog["sources"]:
        assert source["public"] is True
        assert source["publishes_private_candidates"] is False
        assert source["review_required_before_claims"] is True


def test_source_catalog_scope_tracks_family_operator_catalog() -> None:
    catalog = build_source_catalog()
    operator_catalog = build_family_operator_catalog()

    expected_operator_scope = [
        {
            "default_estimator": operator["default_estimator"],
            "family": family["family"],
            "operator_type": operator["operator_type"],
            "plugin": family["plugin"],
            "review_gate": operator["review_gate"],
            "security_claim": operator["security_claim"],
            "variant": operator["variant"],
        }
        for family in operator_catalog["families"]
        if family["support_level"] == "toy_evaluator"
        for operator in family["operators"]
        if operator["support_status"] == "implemented_toy"
    ]

    assert catalog["scope"]["non_lattice_toy_operator_variants"] == (
        expected_operator_scope
    )
    assert len(catalog["scope"]["non_lattice_toy_operator_variants"]) == 41
    assert {
        "default_estimator": "toy-implementation-security-estimator",
        "family": "IMPLEMENTATION_SECURITY",
        "operator_type": "constant_time_check",
        "plugin": "implementation_security",
        "review_gate": "json_only_toy_dudect_summary_only",
        "security_claim": False,
        "variant": "toy_dudect_summary_threshold_check",
    } in catalog["scope"]["non_lattice_toy_operator_variants"]
    assert {
        "default_estimator": "toy-implementation-security-estimator",
        "family": "IMPLEMENTATION_SECURITY",
        "operator_type": "constant_time_check",
        "plugin": "implementation_security",
        "review_gate": "json_only_toy_ctgrind_secret_taint_summary_only",
        "security_claim": False,
        "variant": "toy_ctgrind_secret_taint_summary_check",
    } in catalog["scope"]["non_lattice_toy_operator_variants"]


def test_committed_source_catalog_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "source_catalog.json"
    committed = Path("docs/source_catalog.json")

    write_source_catalog(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_source_catalog_cli_writes_catalog(tmp_path: Path) -> None:
    out = tmp_path / "source_catalog.json"

    result = CliRunner().invoke(app, ["source-catalog", "--out", str(out)])

    assert result.exit_code == 0
    assert f"source_catalog={out}" in result.output
    assert json.loads(out.read_text())["schema_version"] == (
        "agades.pqc.source_catalog.v1"
    )


def test_source_catalog_verify_accepts_committed_catalog() -> None:
    result = verify_source_catalog(Path("docs/source_catalog.json"))

    assert result["schema_version"] == SOURCE_CATALOG_VERIFICATION_SCHEMA
    assert result["accepted"] is True
    assert result["summary"] == {
        "current_public_surface_count": 15,
        "current_public_surfaces": [
            "agades-benchmark-source-contracts",
            "agades-family-plugin-manifest",
            "agades-family-registry-manifest",
            "agades-family-support-matrix",
            "agades-hf-collection",
            "agades-hf-dataset",
            "agades-hf-space",
            "agades-lattice-estimator-baseline-contracts",
            "agades-nvidia-accelerator",
            "agades-nvidia-publication-handoff",
            "agades-prime-environment",
            "agades-prime-publication-handoff",
            "agades-public-run-export",
            "agades-publication-manifest",
            "prime-verifiers",
        ],
        "failure_count": 0,
        "future_reviewed_adapter_count": 19,
        "future_reviewed_adapters": [
            "ctgrind",
            "dudect",
            "facebook-lwe-benchmarking",
            "facebook-tapas",
            "hf-post-quantum-crypto-en",
            "hf-post-quantum-crypto-fr",
            "hf-pqc-ssl-scans",
            "hf-sc2026-side-channel",
            "liboqs",
            "nist-acvp",
            "nist-additional-signatures-round3",
            "nist-bike-round4-status",
            "nist-classic-mceliece-round4-status",
            "nist-hqc-selection",
            "pq-code-package",
            "pqclean",
            "pqm4",
            "prime-rl",
            "timecop-supercop",
        ],
        "local_artifact_source_count": 14,
        "non_lattice_toy_evaluator_count": 41,
        "non_lattice_toy_operator_families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
        "non_lattice_toy_operator_security_claims": 0,
        "non_lattice_toy_operator_variant_count": 41,
        "platforms": [
            "ebacs",
            "github",
            "hugging_face",
            "nist",
            "nvidia",
            "prime_intellect",
        ],
        "platform_counts": {
            "ebacs": 1,
            "github": 14,
            "hugging_face": 8,
            "nist": 7,
            "nvidia": 3,
            "prime_intellect": 8,
        },
        "requires_gpu_source_count": 3,
        "source_count": 41,
        "source_map_only": [
            "nvidia-inception",
            "prime-autonanogpt-speedrun",
            "prime-autonomous-speedrunning-experiments",
            "prime-quickstart",
        ],
        "source_map_only_count": 4,
    }
    assert result["failures"] == []


def test_source_catalog_verify_rejects_private_candidate_publication(
    tmp_path: Path,
) -> None:
    catalog = build_source_catalog()
    by_id = {source["id"]: source for source in catalog["sources"]}
    by_id["prime-rl"]["publishes_private_candidates"] = True
    out = tmp_path / "source_catalog.json"
    out.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")

    result = verify_source_catalog(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "prime-rl: sources must not publish private candidates."
    ]


def test_source_catalog_verify_rejects_security_claim(tmp_path: Path) -> None:
    catalog = build_source_catalog()
    catalog["safety"]["security_claim"] = True
    out = tmp_path / "source_catalog.json"
    out.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")

    result = verify_source_catalog(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "manifest: safety.security_claim must be false."
    ]


def test_source_catalog_verify_rejects_operator_scope_drift(tmp_path: Path) -> None:
    catalog = build_source_catalog()
    catalog["scope"]["non_lattice_toy_operator_variants"] = []
    out = tmp_path / "source_catalog.json"
    out.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")

    result = verify_source_catalog(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "manifest: non_lattice_toy_operator_variants drifted."
    ]


def test_source_catalog_verify_rejects_summary_drift(tmp_path: Path) -> None:
    catalog = build_source_catalog()
    catalog["summary"] = {
        "source_count": 40,
    }
    out = tmp_path / "source_catalog.json"
    out.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")

    result = verify_source_catalog(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "manifest: summary is inconsistent with source entries and scope."
    ]


def test_source_catalog_verify_rejects_runtime_catalog_drift(
    tmp_path: Path,
) -> None:
    catalog = build_source_catalog()
    by_id = {source["id"]: source for source in catalog["sources"]}
    by_id["agades-hf-space"]["title"] = "Stale Hugging Face Space manifest title"
    out = tmp_path / "source_catalog.json"
    out.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")

    result = verify_source_catalog(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "manifest: contents are not synchronized with the current runtime source "
        "catalog."
    ]


def test_source_catalog_verify_cli_prints_json() -> None:
    result = CliRunner().invoke(
        app,
        [
            "source-catalog-verify",
            "--catalog",
            "docs/source_catalog.json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == SOURCE_CATALOG_VERIFICATION_SCHEMA
    assert payload["accepted"] is True
    assert payload["summary"]["source_count"] == 41


def test_source_catalog_verify_cli_exits_nonzero_on_failure(
    tmp_path: Path,
) -> None:
    catalog = build_source_catalog()
    by_id = {source["id"]: source for source in catalog["sources"]}
    by_id["agades-family-support-matrix"]["url"] = "docs/missing_matrix.json"
    out = tmp_path / "source_catalog.json"
    out.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")

    result = CliRunner().invoke(
        app,
        ["source-catalog-verify", "--catalog", str(out)],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["accepted"] is False
    assert payload["failures"] == [
        (
            "agades-family-support-matrix: local artifact URL does not exist: "
            "docs/missing_matrix.json."
        )
    ]
