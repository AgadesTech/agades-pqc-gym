from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.public_benchmark_manifest import (
    build_public_benchmark_manifest,
    verify_public_benchmark_manifest,
    write_public_benchmark_manifest,
)


def test_public_benchmark_manifest_records_public_v0_benchmark_set(
    tmp_path: Path,
) -> None:
    out = tmp_path / "public_benchmark_manifest.json"

    manifest = write_public_benchmark_manifest(out)

    assert manifest == build_public_benchmark_manifest()
    assert json.loads(out.read_text()) == manifest
    assert manifest["schema_version"] == "agades.pqc.public_benchmark_manifest.v1"
    assert manifest["benchmark"] == {
        "id": "agades-pqc-public-benchmark-v0",
        "name": "Agades PQC Gym Public Benchmark v0",
        "publication_status": "local_artifact_ready_review_required",
        "scope": "toy_and_downscaled_public_verifier_bundles",
    }
    assert manifest["project"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "cli": "agades-pqc",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert manifest["summary"] == {
        "bundle_count": 18,
        "families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
        ],
        "record_count": 59,
        "security_claim": False,
    }
    assert manifest["safety"] == {
        "contains_private_traces": False,
        "publishes_private_candidates": False,
        "arbitrary_code_execution": False,
        "live_targeting": False,
        "security_claim": False,
        "review_required_before_publish": True,
    }

    bundles = {bundle["id"]: bundle for bundle in manifest["bundles"]}
    assert set(bundles) == {
        "code_based_toy_classic_mceliece_v0",
        "code_based_toy_hqc_v0",
        "code_based_toy_isd_v0",
        "code_based_toy_mdpc_v0",
        "hash_based_toy_bound_v0",
        "hash_based_toy_misuse_v0",
        "hash_based_toy_signature_v0",
        "implementation_security_toy_benchmark_v0",
        "implementation_security_toy_kat_v0",
        "implementation_security_toy_timing_v0",
        "isogeny_historical_toy_path_v0",
        "lattice_downscaled_lwe_instance_solve_v0",
        "lattice_downscaled_mlwe_instance_solve_v0",
        "lattice_mlwe_downscaled_v0",
        "lattice_toy_lwe_v0",
        "multivariate_toy_minrank_v0",
        "multivariate_toy_mq_v0",
        "multivariate_toy_uov_v0",
    }
    assert bundles["lattice_toy_lwe_v0"] == {
        "id": "lattice_toy_lwe_v0",
        "family": "LWE",
        "run_id": "lattice_toy_lwe",
        "benchmark_path": "benchmarks/lattice_toy_lwe",
        "bundle_path": "examples/public_runs/lattice_toy_lwe_v0",
        "record_count": 2,
        "accepted_records": 2,
        "redacted_records": 0,
        "evaluation_statuses": ["ok"],
        "estimators": ["mock-lattice-estimator"],
        "trace_public_sha256": (
            "443b0f474596310f916fed2f8f958e166a52ea52f6b1ea36a0d32e7f74035d2a"
        ),
        "manifest_sha256": (
            "59a48093584b4baf2fbfbc9904ae06744ba4588a34ba27548b37348a2d82aeb0"
        ),
        "regenerate_commands": [
            (
                "uv run agades-pqc benchmark benchmarks/lattice_toy_lwe "
                "--out runs/lattice_toy_lwe.jsonl"
            ),
            (
                "uv run agades-pqc public-bundle runs/lattice_toy_lwe.jsonl "
                "--out examples/public_runs/lattice_toy_lwe_v0"
            ),
        ],
        "security_claim": False,
        "publishes_private_candidates": False,
    }
    assert bundles["code_based_toy_isd_v0"]["record_count"] == 7
    assert bundles["code_based_toy_isd_v0"]["accepted_records"] == 7
    assert bundles["code_based_toy_isd_v0"]["estimators"] == [
        "toy-code-based-isd-estimator"
    ]
    assert bundles["code_based_toy_hqc_v0"]["benchmark_path"] == (
        "benchmarks/code_based_toy_hqc"
    )
    assert bundles["code_based_toy_hqc_v0"]["record_count"] == 6
    assert bundles["code_based_toy_hqc_v0"]["accepted_records"] == 6
    assert bundles["code_based_toy_hqc_v0"]["estimators"] == [
        "toy-code-based-circulant-erasure-decoder-estimator",
        "toy-code-based-circulant-syndrome-decoder-estimator",
        "toy-code-based-erasure-syndrome-decoder-estimator",
        "toy-code-based-parity-check-decoder-estimator",
        "toy-code-based-repetition-decoder-estimator",
        "toy-code-based-weighted-repetition-decoder-estimator",
    ]
    assert bundles["code_based_toy_mdpc_v0"]["benchmark_path"] == (
        "benchmarks/code_based_toy_mdpc"
    )
    assert bundles["code_based_toy_mdpc_v0"]["record_count"] == 3
    assert bundles["code_based_toy_mdpc_v0"]["accepted_records"] == 3
    assert bundles["code_based_toy_mdpc_v0"]["estimators"] == [
        "toy-code-based-bit-flip-decoder-estimator"
    ]
    assert bundles["code_based_toy_classic_mceliece_v0"]["benchmark_path"] == (
        "benchmarks/code_based_toy_classic_mceliece"
    )
    assert bundles["code_based_toy_classic_mceliece_v0"]["record_count"] == 2
    assert (
        bundles["code_based_toy_classic_mceliece_v0"]["accepted_records"] == 2
    )
    assert bundles["code_based_toy_classic_mceliece_v0"]["estimators"] == [
        "toy-code-based-classic-mceliece-support-syndrome-estimator",
        "toy-code-based-classic-mceliece-syndrome-estimator",
    ]
    assert bundles["lattice_downscaled_lwe_instance_solve_v0"][
        "benchmark_path"
    ] == "benchmarks/lattice_downscaled_lwe_instance_solve"
    assert bundles["lattice_downscaled_lwe_instance_solve_v0"][
        "record_count"
    ] == 3
    assert bundles["lattice_downscaled_lwe_instance_solve_v0"][
        "evaluation_statuses"
    ] == ["ok"]
    assert bundles["lattice_downscaled_mlwe_instance_solve_v0"][
        "benchmark_path"
    ] == "benchmarks/lattice_downscaled_mlwe_instance_solve"
    assert bundles["lattice_downscaled_mlwe_instance_solve_v0"][
        "record_count"
    ] == 1
    assert bundles["lattice_downscaled_mlwe_instance_solve_v0"][
        "accepted_records"
    ] == 1
    assert bundles["lattice_downscaled_mlwe_instance_solve_v0"][
        "estimators"
    ] == ["mock-lattice-estimator"]
    assert bundles["hash_based_toy_signature_v0"]["benchmark_path"] == (
        "benchmarks/hash_based_toy_signature"
    )
    assert bundles["hash_based_toy_signature_v0"]["record_count"] == 4
    assert bundles["hash_based_toy_signature_v0"]["accepted_records"] == 4
    assert bundles["hash_based_toy_signature_v0"]["estimators"] == [
        "toy-hash-bound-estimator"
    ]
    assert bundles["hash_based_toy_bound_v0"]["record_count"] == 3
    assert bundles["hash_based_toy_bound_v0"]["accepted_records"] == 3
    assert bundles["hash_based_toy_bound_v0"]["estimators"] == [
        "toy-hash-bound-estimator"
    ]
    assert bundles["hash_based_toy_misuse_v0"]["benchmark_path"] == (
        "benchmarks/hash_based_toy_misuse"
    )
    assert bundles["hash_based_toy_misuse_v0"]["record_count"] == 1
    assert bundles["hash_based_toy_misuse_v0"]["accepted_records"] == 1
    assert bundles["hash_based_toy_misuse_v0"]["estimators"] == [
        "toy-hash-bound-estimator"
    ]
    assert bundles["implementation_security_toy_kat_v0"][
        "benchmark_path"
    ] == "benchmarks/implementation_security_toy_kat"
    assert bundles["implementation_security_toy_kat_v0"]["record_count"] == 5
    assert bundles["implementation_security_toy_kat_v0"]["accepted_records"] == 5
    assert bundles["implementation_security_toy_kat_v0"]["estimators"] == [
        "toy-implementation-security-estimator"
    ]
    assert bundles["implementation_security_toy_benchmark_v0"][
        "benchmark_path"
    ] == "benchmarks/implementation_security_toy_benchmark"
    assert (
        bundles["implementation_security_toy_benchmark_v0"]["record_count"]
        == 4
    )
    assert (
        bundles["implementation_security_toy_benchmark_v0"]["accepted_records"]
        == 4
    )
    assert bundles["implementation_security_toy_benchmark_v0"]["estimators"] == [
        "toy-implementation-security-estimator"
    ]
    assert bundles["isogeny_historical_toy_path_v0"]["benchmark_path"] == (
        "benchmarks/isogeny_historical_toy_path"
    )
    assert bundles["isogeny_historical_toy_path_v0"]["record_count"] == 4
    assert bundles["isogeny_historical_toy_path_v0"]["accepted_records"] == 4
    assert bundles["isogeny_historical_toy_path_v0"]["estimators"] == [
        "toy-isogeny-historical-path-estimator"
    ]
    assert bundles["implementation_security_toy_timing_v0"]["benchmark_path"] == (
        "benchmarks/implementation_security_toy_timing"
    )
    assert bundles["implementation_security_toy_timing_v0"]["record_count"] == 3
    assert bundles["implementation_security_toy_timing_v0"][
        "accepted_records"
    ] == 3
    assert bundles["implementation_security_toy_timing_v0"]["estimators"] == [
        "toy-implementation-security-estimator"
    ]
    assert bundles["multivariate_toy_minrank_v0"]["benchmark_path"] == (
        "benchmarks/multivariate_toy_minrank"
    )
    assert bundles["multivariate_toy_minrank_v0"]["record_count"] == 3
    assert bundles["multivariate_toy_minrank_v0"]["accepted_records"] == 3
    assert bundles["multivariate_toy_minrank_v0"]["estimators"] == [
        "toy-multivariate-estimator"
    ]
    assert bundles["multivariate_toy_mq_v0"]["record_count"] == 6
    assert bundles["multivariate_toy_mq_v0"]["accepted_records"] == 6
    assert bundles["multivariate_toy_mq_v0"]["estimators"] == [
        "toy-multivariate-estimator"
    ]
    assert bundles["multivariate_toy_uov_v0"]["benchmark_path"] == (
        "benchmarks/multivariate_toy_uov"
    )
    assert bundles["multivariate_toy_uov_v0"]["record_count"] == 1
    assert bundles["multivariate_toy_uov_v0"]["accepted_records"] == 1
    assert bundles["multivariate_toy_uov_v0"]["estimators"] == [
        "toy-multivariate-estimator"
    ]
    assert bundles["multivariate_toy_uov_v0"]["evaluation_statuses"] == ["ok"]

    for bundle in bundles.values():
        assert bundle["security_claim"] is False
        assert bundle["publishes_private_candidates"] is False
        assert len(bundle["manifest_sha256"]) == 64
        assert bundle["record_count"] >= 1
        assert bundle["accepted_records"] >= 1
        assert bundle["redacted_records"] == 0
        assert bundle["regenerate_commands"][0].startswith(
            "uv run agades-pqc benchmark "
        )
        assert bundle["regenerate_commands"][1].startswith(
            "uv run agades-pqc public-bundle "
        )

    assert (
        "uv run agades-pqc public-benchmark-manifest --out "
        "docs/public_benchmark_manifest.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json"
    ) in manifest["release_gates"]
    assert "public-benchmark-manifest" in manifest["release_audit_gate"]


def test_committed_public_benchmark_manifest_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "public_benchmark_manifest.json"
    committed = Path("docs/public_benchmark_manifest.json")

    write_public_benchmark_manifest(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_public_benchmark_manifest_cli_writes_manifest(tmp_path: Path) -> None:
    out = tmp_path / "public_benchmark_manifest.json"

    result = CliRunner().invoke(
        app,
        ["public-benchmark-manifest", "--out", str(out)],
    )

    assert result.exit_code == 0
    assert f"public_benchmark_manifest={out}" in result.output
    assert json.loads(out.read_text())["schema_version"] == (
        "agades.pqc.public_benchmark_manifest.v1"
    )


def test_public_benchmark_manifest_verifier_accepts_current_manifest() -> None:
    result = verify_public_benchmark_manifest(
        Path("docs/public_benchmark_manifest.json")
    )

    assert result["schema_version"] == "agades.pqc.public_benchmark_verification.v1"
    assert result["accepted"] is True
    assert result["summary"] == {
        "bundle_count": 18,
        "failure_count": 0,
        "record_count": 59,
    }
    assert result["failures"] == []


def test_public_benchmark_manifest_verifier_rejects_stale_digest(
    tmp_path: Path,
) -> None:
    manifest = build_public_benchmark_manifest()
    manifest["bundles"][0]["manifest_sha256"] = "0" * 64
    stale = tmp_path / "public_benchmark_manifest.json"
    stale.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_public_benchmark_manifest(stale)

    assert result["accepted"] is False
    assert any(
        "Public benchmark manifest is not in sync" in failure
        for failure in result["failures"]
    )
    assert any(
        "manifest_sha256 mismatch" in failure for failure in result["failures"]
    )


def test_public_benchmark_manifest_verifier_rejects_missing_manifest(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing_public_benchmark_manifest.json"

    result = verify_public_benchmark_manifest(missing)

    assert result["accepted"] is False
    assert result["summary"] == {
        "bundle_count": 0,
        "failure_count": 1,
        "record_count": 0,
    }
    assert result["failures"] == [
        f"Public benchmark manifest is missing: {missing.as_posix()}."
    ]


def test_public_benchmark_manifest_verifier_rejects_invalid_json(
    tmp_path: Path,
) -> None:
    invalid = tmp_path / "public_benchmark_manifest.json"
    invalid.write_text("{not-json", encoding="utf-8")

    result = verify_public_benchmark_manifest(invalid)

    assert result["accepted"] is False
    assert result["summary"] == {
        "bundle_count": 0,
        "failure_count": 1,
        "record_count": 0,
    }
    assert result["failures"] == [
        f"Public benchmark manifest is not valid JSON: {invalid.as_posix()}."
    ]


def test_public_benchmark_manifest_verifier_rejects_escaping_bundle_path(
    tmp_path: Path,
) -> None:
    manifest = build_public_benchmark_manifest()
    bundle_id = manifest["bundles"][0]["id"]
    manifest["bundles"][0]["bundle_path"] = "../outside"
    stale = tmp_path / "public_benchmark_manifest.json"
    stale.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_public_benchmark_manifest(stale)

    assert result["accepted"] is False
    assert any(
        f"Public benchmark bundle path escapes repository: {bundle_id}." == failure
        for failure in result["failures"]
    )


def test_public_benchmark_verify_cli_reports_json() -> None:
    result = CliRunner().invoke(
        app,
        [
            "public-benchmark-verify",
            "--manifest",
            "docs/public_benchmark_manifest.json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["accepted"] is True
    assert payload["summary"]["bundle_count"] == 18


def test_public_benchmark_verify_cli_reports_missing_manifest_json(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing_public_benchmark_manifest.json"

    result = CliRunner().invoke(
        app,
        [
            "public-benchmark-verify",
            "--manifest",
            str(missing),
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["accepted"] is False
    assert payload["failures"] == [
        f"Public benchmark manifest is missing: {missing.as_posix()}."
    ]
