from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.benchmark_source_contracts import (
    BENCHMARK_SOURCE_CONTRACTS_SCHEMA,
    BENCHMARK_SOURCE_CONTRACTS_VERIFICATION_SCHEMA,
    build_benchmark_source_contracts,
    verify_benchmark_source_contracts,
    write_benchmark_source_contracts,
)


def test_benchmark_source_contracts_keep_heavy_sources_review_gated(
    tmp_path: Path,
) -> None:
    out = tmp_path / "benchmark_source_contracts.json"

    contracts = write_benchmark_source_contracts(out)

    assert contracts == build_benchmark_source_contracts()
    assert json.loads(out.read_text()) == contracts
    assert contracts["schema_version"] == BENCHMARK_SOURCE_CONTRACTS_SCHEMA
    assert contracts["safety"] == {
        "arbitrary_code_execution": False,
        "contains_private_traces": False,
        "public_verifier_downloads_large_assets": False,
        "publishes_private_candidates": False,
        "security_claim": False,
    }
    assert contracts["summary"] == {
        "blocked_public_benchmark_claim_surface_contracts": 18,
        "blocked_public_verifier_contracts": 18,
        "blocked_prime_reward_contracts": 18,
        "contract_count": 18,
        "current_runtime_enabled_contracts": 0,
        "expert_review_gate_contracts": 18,
        "future_reviewed_adapters": 18,
        "heavy_storage_contracts": 2,
        "public_verifier_allowed_contracts": 0,
        "requires_gpu_contracts": 2,
        "source_catalog_id_count": 18,
        "target_family_counts": {
            "all": 3,
            "code_based": 3,
            "hash_based": 1,
            "implementation_security": 8,
            "lattice": 2,
            "multivariate": 1,
        },
    }

    by_id = {contract["source_id"]: contract for contract in contracts["contracts"]}
    tapas = by_id["facebook-tapas"]
    assert tapas["adapter_status"] == "future_reviewed_adapter"
    assert tapas["current_runtime_enabled"] is False
    assert tapas["public_verifier_allowed"] is False
    assert tapas["source_facts"]["license"] == "cc-by-4.0"
    assert tapas["source_facts"]["total_file_size_gb"] == 364
    assert tapas["source_facts"]["settings"][0] == {
        "n": 256,
        "log_q": 20,
        "omega": 10,
        "rho": 0.4284,
        "samples": "400M",
    }
    assert "reviewed_parameter_mapping" in tapas["required_review_gates"]

    lwe = by_id["facebook-lwe-benchmarking"]
    assert lwe["requires_gpu"] is True
    assert lwe["source_facts"]["min_python"] == "3.10.12"
    assert "flatter" in lwe["source_facts"]["external_tools"]
    assert "sage" in lwe["source_facts"]["separate_environments"]
    assert "SALSA" in lwe["source_facts"]["attacks"]
    assert "current_public_verifier" not in lwe["allowed_surfaces"]

    fr = by_id["hf-post-quantum-crypto-fr-instruction-seed"]
    assert fr["source_catalog_id"] == "hf-post-quantum-crypto-fr"
    assert fr["target_family"] == "all"
    assert fr["current_runtime_enabled"] is False
    assert fr["public_verifier_allowed"] is False
    assert "source_fact_verification" in fr["required_review_gates"]
    assert "current_public_verifier" in fr["blocked_surfaces"]
    assert fr["source_facts"]["language"] == "fr"
    assert fr["source_facts"]["row_count"] == 122

    en = by_id["hf-post-quantum-crypto-en-instruction-seed"]
    assert en["source_catalog_id"] == "hf-post-quantum-crypto-en"
    assert en["target_family"] == "all"
    assert en["source_facts"]["language"] == "en"
    assert en["source_facts"]["row_count"] == 122
    assert "answer_source_grounding_review" in en["required_review_gates"]

    ssl = by_id["hf-pqc-ssl-scans-migration-scoring"]
    assert ssl["source_catalog_id"] == "hf-pqc-ssl-scans"
    assert ssl["target_family"] == "all"
    assert ssl["source_facts"]["row_count"] == 45
    assert "migration_scoring_methodology_review" in ssl["required_review_gates"]
    assert "prime_json_only_reward_environment" in ssl["blocked_surfaces"]

    sc2026 = by_id["hf-sc2026-side-channel-research"]
    assert sc2026["source_catalog_id"] == "hf-sc2026-side-channel"
    assert sc2026["target_family"] == "implementation_security"
    assert sc2026["requires_gpu"] is True
    assert sc2026["source_facts"]["contains_kyber"] is True
    assert "trace_provenance_review" in sc2026["required_review_gates"]
    assert "public_benchmark_v0_claim_surface" in sc2026["blocked_surfaces"]

    hqc = by_id["nist-hqc-standardization-track"]
    assert hqc["target_family"] == "code_based"
    assert hqc["source_catalog_id"] == "nist-hqc-selection"
    assert hqc["adapter_status"] == "future_reviewed_adapter"
    assert hqc["current_runtime_enabled"] is False
    assert hqc["public_verifier_allowed"] is False
    assert hqc["source_facts"]["selection_date"] == "2025-03-11"
    assert hqc["source_facts"]["selected_algorithm"] == "HQC"
    assert "reviewed_hqc_parameter_mapping" in hqc["required_review_gates"]
    assert "prime_json_only_reward_environment" in hqc["blocked_surfaces"]

    bike = by_id["nist-bike-round4-status"]
    assert bike["target_family"] == "code_based"
    assert bike["source_catalog_id"] == "nist-bike-round4-status"
    assert bike["adapter_status"] == "future_reviewed_adapter"
    assert bike["current_runtime_enabled"] is False
    assert bike["public_verifier_allowed"] is False
    assert bike["source_facts"]["round4_outcome"] == "not_selected"
    assert bike["source_facts"]["selected_algorithm"] == "HQC"
    assert "reviewed_bike_parameter_mapping" in bike["required_review_gates"]
    assert "current_public_verifier" in bike["blocked_surfaces"]

    classic_mceliece = by_id["nist-classic-mceliece-round4-status"]
    assert classic_mceliece["target_family"] == "code_based"
    assert classic_mceliece["source_catalog_id"] == (
        "nist-classic-mceliece-round4-status"
    )
    assert classic_mceliece["adapter_status"] == "future_reviewed_adapter"
    assert classic_mceliece["current_runtime_enabled"] is False
    assert classic_mceliece["public_verifier_allowed"] is False
    assert classic_mceliece["source_facts"]["round4_outcome"] == "not_selected"
    assert classic_mceliece["source_facts"]["selected_algorithm"] == "HQC"
    assert (
        "reviewed_classic_mceliece_parameter_mapping"
        in classic_mceliece["required_review_gates"]
    )
    assert "current_public_verifier" in classic_mceliece["blocked_surfaces"]

    slh_dsa = by_id["nist-fips-205-slh-dsa-reference"]
    assert slh_dsa["target_family"] == "hash_based"
    assert slh_dsa["source_catalog_id"] == "nist-fips-205"
    assert slh_dsa["current_runtime_enabled"] is False
    assert slh_dsa["public_verifier_allowed"] is False
    assert slh_dsa["source_facts"]["publication_date"] == "2024-08-13"
    assert slh_dsa["source_facts"]["algorithm"] == "SLH-DSA"
    assert "SPHINCS+" in slh_dsa["source_facts"]["based_on"]
    assert "parameter_set_mapping" in slh_dsa["required_review_gates"]

    multivariate = by_id["nist-additional-signatures-round3-multivariate"]
    assert multivariate["target_family"] == "multivariate"
    assert multivariate["source_catalog_id"] == "nist-additional-signatures-round3"
    assert multivariate["adapter_status"] == "future_reviewed_adapter"
    assert multivariate["current_runtime_enabled"] is False
    assert multivariate["public_verifier_allowed"] is False
    assert multivariate["source_facts"]["announcement_date"] == "2026-05-14"
    assert multivariate["source_facts"]["multivariate_candidates"] == [
        "MAYO",
        "QR-UOV",
        "UOV",
    ]
    assert "algebraic_attack_model_review" in multivariate["required_review_gates"]

    liboqs = by_id["liboqs-implementation-harness"]
    assert liboqs["target_family"] == "implementation_security"
    assert liboqs["adapter_status"] == "future_reviewed_adapter"
    assert liboqs["current_runtime_enabled"] is False
    assert liboqs["public_verifier_allowed"] is False
    assert liboqs["requires_gpu"] is False
    assert liboqs["requires_large_storage"] is False
    assert "kat_conformance_mapping" in liboqs["required_review_gates"]
    assert "current_public_verifier" in liboqs["blocked_surfaces"]
    assert "test_kem" in liboqs["source_facts"]["test_programs"]
    assert "speed_kem" in liboqs["source_facts"]["benchmark_programs"]

    pqcp = by_id["pq-code-package-native-implementations"]
    assert pqcp["target_family"] == "implementation_security"
    assert pqcp["source_catalog_id"] == "pq-code-package"
    assert pqcp["adapter_status"] == "future_reviewed_adapter"
    assert pqcp["current_runtime_enabled"] is False
    assert pqcp["public_verifier_allowed"] is False
    assert pqcp["requires_gpu"] is False
    assert pqcp["requires_large_storage"] is False
    assert "high_assurance_source_pin" in pqcp["required_review_gates"]
    assert "current_public_verifier" in pqcp["blocked_surfaces"]
    assert "mlkem-native" in pqcp["source_facts"]["repositories"]
    assert "FIPS 203" in pqcp["source_facts"]["standards_scope"]

    pqm4 = by_id["pqm4-cortexm4-benchmarking"]
    assert pqm4["target_family"] == "implementation_security"
    assert pqm4["requires_gpu"] is False
    assert pqm4["requires_large_storage"] is False
    assert "device_or_simulator_isolation" in pqm4["required_review_gates"]
    assert "speed" in pqm4["source_facts"]["metrics"]
    assert "stack_usage" in pqm4["source_facts"]["metrics"]
    assert "code_size" in pqm4["source_facts"]["metrics"]

    acvp = by_id["nist-acvp-pqc-vectors"]
    assert acvp["target_family"] == "implementation_security"
    assert acvp["source_catalog_id"] == "nist-acvp"
    assert "ML-KEM" in acvp["source_facts"]["pqc_algorithm_groups"]
    assert "ML-DSA" in acvp["source_facts"]["pqc_algorithm_groups"]
    assert "vector_provenance_pin" in acvp["required_review_gates"]
    assert "prime_json_only_reward_environment" in acvp["blocked_surfaces"]

    dudect = by_id["dudect-statistical-timing-leakage"]
    assert dudect["target_family"] == "implementation_security"
    assert dudect["source_catalog_id"] == "dudect"
    assert dudect["adapter_status"] == "future_reviewed_adapter"
    assert dudect["current_runtime_enabled"] is False
    assert dudect["public_verifier_allowed"] is False
    assert dudect["requires_gpu"] is False
    assert "measurement_protocol_review" in dudect["required_review_gates"]
    assert "welch_t_test" in dudect["source_facts"]["statistical_method"]
    assert "public_benchmark_v0_claim_surface" in dudect["blocked_surfaces"]

    ctgrind = by_id["ctgrind-secret-taint-analysis"]
    assert ctgrind["target_family"] == "implementation_security"
    assert ctgrind["source_catalog_id"] == "ctgrind"
    assert ctgrind["current_runtime_enabled"] is False
    assert ctgrind["public_verifier_allowed"] is False
    assert "valgrind_environment_pin" in ctgrind["required_review_gates"]
    assert "secret_dependent_branch" in ctgrind["source_facts"]["checks"]
    assert "prime_json_only_reward_environment" in ctgrind["blocked_surfaces"]

    timecop = by_id["timecop-supercop-policy-checks"]
    assert timecop["target_family"] == "implementation_security"
    assert timecop["source_catalog_id"] == "timecop-supercop"
    assert timecop["current_runtime_enabled"] is False
    assert timecop["public_verifier_allowed"] is False
    assert "supercop_source_pin" in timecop["required_review_gates"]
    assert "TIMECOP 2" in timecop["source_facts"]["tool_versions"]
    assert "current_public_verifier" in timecop["blocked_surfaces"]


def test_committed_benchmark_source_contracts_are_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "benchmark_source_contracts.json"
    committed = Path("docs/benchmark_source_contracts.json")

    write_benchmark_source_contracts(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_benchmark_source_contracts_cli_writes_manifest(tmp_path: Path) -> None:
    out = tmp_path / "benchmark_source_contracts.json"

    result = CliRunner().invoke(
        app,
        ["benchmark-source-contracts", "--out", str(out)],
    )

    assert result.exit_code == 0
    assert f"benchmark_source_contracts={out}" in result.output
    assert json.loads(out.read_text())["schema_version"] == (
        "agades.pqc.benchmark_source_contracts.v1"
    )


def test_benchmark_source_contracts_verify_committed_contracts() -> None:
    result = verify_benchmark_source_contracts(
        Path("docs/benchmark_source_contracts.json")
    )

    assert result["schema_version"] == BENCHMARK_SOURCE_CONTRACTS_VERIFICATION_SCHEMA
    assert result["accepted"] is True
    assert result["summary"] == {
        "blocked_public_benchmark_claim_surface_contracts": 18,
        "blocked_public_verifier_contracts": 18,
        "blocked_prime_reward_contracts": 18,
        "contract_count": 18,
        "current_runtime_enabled_contracts": 0,
        "expert_review_gate_contracts": 18,
        "failure_count": 0,
        "future_reviewed_adapters": 18,
        "heavy_storage_contracts": 2,
        "public_verifier_allowed_contracts": 0,
        "requires_gpu_contracts": 2,
        "source_catalog_id_count": 18,
        "target_family_counts": {
            "all": 3,
            "code_based": 3,
            "hash_based": 1,
            "implementation_security": 8,
            "lattice": 2,
            "multivariate": 1,
        },
    }
    assert result["failures"] == []


def test_benchmark_source_contracts_verify_rejects_public_future_adapter(
    tmp_path: Path,
) -> None:
    contracts = build_benchmark_source_contracts()
    contracts["contracts"][0]["public_verifier_allowed"] = True
    out = tmp_path / "benchmark_source_contracts.json"
    out.write_text(json.dumps(contracts, indent=2, sort_keys=True) + "\n")

    result = verify_benchmark_source_contracts(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        (
            "facebook-tapas: future reviewed adapters must not be allowed "
            "in the public verifier."
        )
    ]


def test_benchmark_source_contracts_verify_rejects_missing_public_block(
    tmp_path: Path,
) -> None:
    contracts = build_benchmark_source_contracts()
    contracts["contracts"][0]["blocked_surfaces"].remove("current_public_verifier")
    out = tmp_path / "benchmark_source_contracts.json"
    out.write_text(json.dumps(contracts, indent=2, sort_keys=True) + "\n")

    result = verify_benchmark_source_contracts(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "facebook-tapas: missing blocked surface current_public_verifier."
    ]


def test_benchmark_source_contracts_verify_rejects_summary_drift(
    tmp_path: Path,
) -> None:
    contracts = build_benchmark_source_contracts()
    contracts["summary"] = {
        **contracts["summary"],
        "contract_count": 17,
    }
    out = tmp_path / "benchmark_source_contracts.json"
    out.write_text(json.dumps(contracts, indent=2, sort_keys=True) + "\n")

    result = verify_benchmark_source_contracts(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "manifest: summary is inconsistent with contract entries."
    ]


def test_benchmark_source_contracts_verify_rejects_runtime_contract_drift(
    tmp_path: Path,
) -> None:
    contracts = build_benchmark_source_contracts()
    by_id = {contract["source_id"]: contract for contract in contracts["contracts"]}
    by_id["nist-acvp-pqc-vectors"]["source_facts"]["vector_origin"] = (
        "stale local mirror"
    )
    out = tmp_path / "benchmark_source_contracts.json"
    out.write_text(json.dumps(contracts, indent=2, sort_keys=True) + "\n")

    result = verify_benchmark_source_contracts(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "manifest: contents are not synchronized with the current runtime "
        "benchmark source contracts."
    ]


def test_benchmark_source_contracts_verify_cli_prints_json() -> None:
    result = CliRunner().invoke(
        app,
        [
            "benchmark-source-verify",
            "--contracts",
            "docs/benchmark_source_contracts.json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == BENCHMARK_SOURCE_CONTRACTS_VERIFICATION_SCHEMA
    assert payload["accepted"] is True
    assert payload["summary"]["contract_count"] == 18


def test_benchmark_source_contracts_verify_cli_exits_nonzero_on_failure(
    tmp_path: Path,
) -> None:
    contracts = build_benchmark_source_contracts()
    contracts["contracts"][0]["current_runtime_enabled"] = True
    out = tmp_path / "benchmark_source_contracts.json"
    out.write_text(json.dumps(contracts, indent=2, sort_keys=True) + "\n")

    result = CliRunner().invoke(
        app,
        ["benchmark-source-verify", "--contracts", str(out)],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["accepted"] is False
    assert payload["failures"] == [
        "facebook-tapas: future reviewed adapters must not enable runtime."
    ]
