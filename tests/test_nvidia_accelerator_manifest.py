from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations import nvidia_accelerator
from agades_pqc_gym.integrations.nvidia_accelerator import (
    build_nvidia_accelerator_manifest,
    write_nvidia_accelerator_manifest,
)

EXPECTED_FAMILY_SUPPORT = {
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
    "toy_evaluators": [
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "MULTIVARIATE",
    ],
    "support_level_counts": {
        "implemented": 2,
        "schema_only": 2,
        "toy_evaluator": 5,
    },
    "unique_future_reviewed_adapter_source_count": 15,
}
EXPECTED_SOURCE_CATALOG_SCOPE = {
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
    "source_count": 41,
}
EXPECTED_PUBLIC_PRIVATE_BOUNDARY = {
    "report_generator_redaction": {
        "blocking": True,
        "check_id": "report-generator-redaction",
        "private_evaluator_output_absent": True,
        "private_mapping_evaluator_output_absent": True,
        "private_mapping_score_absent": True,
        "private_mapping_target_absent": True,
        "private_mutation_absent": True,
        "private_score_absent": True,
        "raw_mapping_redaction_covered": True,
        "redacted_records": 2,
        "sensitive_target_absent": True,
        "status": "passed",
        "typed_trace_redaction_covered": True,
    }
}


def test_nvidia_accelerator_manifest_describes_public_eval_surface(
    tmp_path: Path,
) -> None:
    out = tmp_path / "accelerator_manifest.json"

    manifest = write_nvidia_accelerator_manifest(out)

    assert manifest == build_nvidia_accelerator_manifest()
    assert out.exists()
    assert json.loads(out.read_text()) == manifest
    assert manifest["schema_version"] == "agades.pqc.nvidia_accelerator.v1"
    assert manifest["project"]["name"] == "Agades PQC Gym"
    assert manifest["project"]["package"] == "agades_pqc_gym"
    assert manifest["mvp_runtime"]["current_gpu_required"] is False
    assert manifest["mvp_runtime"]["gpu_status"] == "future_acceleration_surface"
    assert manifest["family_support"] == EXPECTED_FAMILY_SUPPORT
    assert manifest["source_catalog_scope"] == EXPECTED_SOURCE_CATALOG_SCOPE
    assert manifest["public_private_boundary"] == EXPECTED_PUBLIC_PRIVATE_BOUNDARY
    assert manifest["workload_summary"] == {
        "all_current_workloads_cpu": True,
        "cpu_workload_count": 26,
        "current_gpu_required_workload_count": 0,
        "current_workload_count": 26,
        "gpu_future_workload_count": 1,
        "no_current_workload_requires_gpu": True,
        "public_run_bundle_count": 18,
        "reserved_future_gpu_required_workload_count": 1,
        "reserved_future_workload_count": 1,
        "total_workload_count": 27,
    }
    assert manifest["safety"]["contains_private_traces"] is False
    assert manifest["safety"]["security_claim"] is False
    assert manifest["safety"]["arbitrary_code_execution"] is False
    assert manifest["public_artifacts"]["huggingface_dataset"] == "hf/dataset"
    assert manifest["public_artifacts"]["huggingface_space_manifest"] == (
        "hf/space_manifest.json"
    )
    assert manifest["public_artifacts"]["huggingface_collection_manifest"] == (
        "hf/collection_manifest.json"
    )
    assert manifest["public_artifacts"]["source_catalog"] == "docs/source_catalog.json"
    assert manifest["public_artifacts"]["publication_manifest"] == (
        "docs/publication_manifest.json"
    )
    assert manifest["public_artifacts"]["public_benchmark_manifest"] == (
        "docs/public_benchmark_manifest.json"
    )
    assert manifest["public_artifacts"]["public_run_export"] == (
        "public/run_export/manifest.json"
    )
    assert manifest["public_artifacts"]["benchmark_source_contracts"] == (
        "docs/benchmark_source_contracts.json"
    )
    assert (
        manifest["public_artifacts"]["family_support_matrix"]
        == "docs/family_support_matrix.json"
    )
    assert manifest["public_artifacts"]["lattice_estimator_manifest"] == (
        "docs/lattice_estimator_manifest.json"
    )
    assert manifest["public_artifacts"]["lattice_estimator_baseline_contracts"] == (
        "docs/lattice_estimator_baseline_contracts.json"
    )
    assert manifest["public_artifacts"]["release_audit"] == "public/release_audit.json"
    assert (
        manifest["public_artifacts"]["prime_verifiers_environment"]
        == "prime_intellect/verifiers_environment"
    )
    assert manifest["public_artifacts"]["prime_environment_manifest"] == (
        "prime_intellect/verifiers_environment/prime_manifest.json"
    )
    assert manifest["public_artifacts"]["prime_verifier_schemas"] == (
        "prime_intellect/schemas/schema_manifest.json"
    )
    assert manifest["public_artifacts"]["public_run_bundles"] == [
        "examples/public_runs/code_based_toy_classic_mceliece_v0",
        "examples/public_runs/code_based_toy_hqc_v0",
        "examples/public_runs/code_based_toy_isd_v0",
        "examples/public_runs/code_based_toy_mdpc_v0",
        "examples/public_runs/hash_based_toy_bound_v0",
        "examples/public_runs/hash_based_toy_misuse_v0",
        "examples/public_runs/hash_based_toy_signature_v0",
        "examples/public_runs/implementation_security_toy_benchmark_v0",
        "examples/public_runs/implementation_security_toy_kat_v0",
        "examples/public_runs/implementation_security_toy_timing_v0",
        "examples/public_runs/isogeny_historical_toy_path_v0",
        "examples/public_runs/lattice_downscaled_lwe_instance_solve_v0",
        "examples/public_runs/lattice_downscaled_mlwe_instance_solve_v0",
        "examples/public_runs/lattice_mlwe_downscaled_v0",
        "examples/public_runs/lattice_toy_lwe_v0",
        "examples/public_runs/multivariate_toy_minrank_v0",
        "examples/public_runs/multivariate_toy_mq_v0",
        "examples/public_runs/multivariate_toy_uov_v0",
    ]
    assert {workload["id"] for workload in manifest["workloads"]} == {
        "code-based-toy-classic-mceliece-benchmark",
        "code-based-toy-hqc-benchmark",
        "code-based-toy-isd-benchmark",
        "code-based-toy-mdpc-benchmark",
        "hash-based-toy-bound-benchmark",
        "hash-based-toy-misuse-benchmark",
        "hash-based-toy-slh-dsa-hypertree-benchmark",
        "hash-based-toy-signature-benchmark",
        "implementation-security-toy-benchmark-summary",
        "implementation-security-toy-binary-size-benchmark",
        "implementation-security-toy-kat-benchmark",
        "implementation-security-toy-memory-footprint-benchmark",
        "implementation-security-toy-stack-usage-benchmark",
        "implementation-security-toy-timing-benchmark",
        "isogeny-historical-toy-path-benchmark",
        "isogeny-historical-toy-volcano-benchmark",
        "lattice-downscaled-lwe-instance-solve-benchmark",
        "lattice-downscaled-mlwe-instance-solve-benchmark",
        "lattice-schema-only-routing",
        "multivariate-toy-mq-benchmark",
        "public-verifier-json",
        "lattice-mlwe-downscaled-benchmark",
        "lattice-toy-benchmark",
        "multivariate-toy-minrank-benchmark",
        "schema-only-family-routing",
        "multivariate-toy-uov-benchmark",
        "future-gpu-reproduction-ladder",
    }
    instance_solve_workload = next(
        workload
        for workload in manifest["workloads"]
        if workload["id"] == "lattice-downscaled-lwe-instance-solve-benchmark"
    )
    assert instance_solve_workload["status"] == "current"
    assert instance_solve_workload["entrypoint"] == (
        "agades-pqc benchmark benchmarks/lattice_downscaled_lwe_instance_solve"
    )
    assert instance_solve_workload["resource_class"] == "cpu"
    assert instance_solve_workload["gpu_required"] is False
    lattice_schema_workload = next(
        workload
        for workload in manifest["workloads"]
        if workload["id"] == "lattice-schema-only-routing"
    )
    assert lattice_schema_workload["status"] == "current"
    assert lattice_schema_workload["entrypoint"] == (
        "agades-pqc benchmark benchmarks/lattice_schema_only"
    )
    assert lattice_schema_workload["gpu_required"] is False
    memory_footprint_workload = next(
        workload
        for workload in manifest["workloads"]
        if workload["id"] == "implementation-security-toy-memory-footprint-benchmark"
    )
    assert memory_footprint_workload["status"] == "current"
    assert memory_footprint_workload["entrypoint"] == (
        "agades-pqc benchmark benchmarks/implementation_security_toy_benchmark"
    )
    assert memory_footprint_workload["resource_class"] == "cpu"
    assert memory_footprint_workload["gpu_required"] is False
    assert "JSON component byte summaries" in memory_footprint_workload["purpose"]
    assert "not a memory-usage claim" in memory_footprint_workload["purpose"]
    binary_size_workload = next(
        workload
        for workload in manifest["workloads"]
        if workload["id"] == "implementation-security-toy-binary-size-benchmark"
    )
    assert binary_size_workload["status"] == "current"
    assert binary_size_workload["entrypoint"] == (
        "agades-pqc benchmark benchmarks/implementation_security_toy_benchmark"
    )
    assert binary_size_workload["resource_class"] == "cpu"
    assert binary_size_workload["gpu_required"] is False
    assert "JSON binary-size summaries" in binary_size_workload["purpose"]
    assert "not a binary-size claim" in binary_size_workload["purpose"]
    stack_usage_workload = next(
        workload
        for workload in manifest["workloads"]
        if workload["id"] == "implementation-security-toy-stack-usage-benchmark"
    )
    assert stack_usage_workload["status"] == "current"
    assert stack_usage_workload["entrypoint"] == (
        "agades-pqc benchmark benchmarks/implementation_security_toy_benchmark"
    )
    assert stack_usage_workload["resource_class"] == "cpu"
    assert stack_usage_workload["gpu_required"] is False
    assert "JSON high-water samples" in stack_usage_workload["purpose"]
    assert "not a stack-usage claim" in stack_usage_workload["purpose"]
    slh_dsa_workload = next(
        workload
        for workload in manifest["workloads"]
        if workload["id"] == "hash-based-toy-slh-dsa-hypertree-benchmark"
    )
    assert slh_dsa_workload["status"] == "current"
    assert slh_dsa_workload["entrypoint"] == (
        "agades-pqc benchmark benchmarks/hash_based_toy_signature"
    )
    assert slh_dsa_workload["resource_class"] == "cpu"
    assert slh_dsa_workload["gpu_required"] is False
    assert "SLH-DSA-like hypertree" in slh_dsa_workload["purpose"]
    assert "not an SLH-DSA result" in slh_dsa_workload["purpose"]
    classic_workload = next(
        workload
        for workload in manifest["workloads"]
        if workload["id"] == "code-based-toy-classic-mceliece-benchmark"
    )
    assert classic_workload["status"] == "current"
    assert classic_workload["entrypoint"] == (
        "agades-pqc benchmark benchmarks/code_based_toy_classic_mceliece"
    )
    assert classic_workload["resource_class"] == "cpu"
    assert classic_workload["gpu_required"] is False
    assert "not a Classic McEliece result" in classic_workload["purpose"]
    hqc_workload = next(
        workload
        for workload in manifest["workloads"]
        if workload["id"] == "code-based-toy-hqc-benchmark"
    )
    assert hqc_workload["status"] == "current"
    assert hqc_workload["entrypoint"] == (
        "agades-pqc benchmark benchmarks/code_based_toy_hqc"
    )
    assert hqc_workload["resource_class"] == "cpu"
    assert hqc_workload["gpu_required"] is False
    assert "circulant-erasure" in hqc_workload["purpose"]
    assert "not an HQC result" in hqc_workload["purpose"]
    uov_workload = next(
        workload
        for workload in manifest["workloads"]
        if workload["id"] == "multivariate-toy-uov-benchmark"
    )
    assert uov_workload["status"] == "current"
    assert uov_workload["entrypoint"] == (
        "agades-pqc benchmark benchmarks/multivariate_toy_uov"
    )
    assert uov_workload["resource_class"] == "cpu"
    assert uov_workload["gpu_required"] is False
    assert "UOV-inspired public-map verification" in uov_workload["purpose"]
    assert "not a UOV, MAYO, Rainbow, forgery, or security claim" in uov_workload[
        "purpose"
    ]
    volcano_workload = next(
        workload
        for workload in manifest["workloads"]
        if workload["id"] == "isogeny-historical-toy-volcano-benchmark"
    )
    assert volcano_workload["status"] == "current"
    assert volcano_workload["entrypoint"] == (
        "agades-pqc benchmark benchmarks/isogeny_historical_toy_path"
    )
    assert volcano_workload["resource_class"] == "cpu"
    assert volcano_workload["gpu_required"] is False
    assert "volcano-style isogeny graph/path" in volcano_workload["purpose"]
    assert (
        "not a CSIDH, SIDH, current-standard, or security claim"
        in volcano_workload["purpose"]
    )
    future_workload = next(
        workload
        for workload in manifest["workloads"]
        if workload["id"] == "future-gpu-reproduction-ladder"
    )
    assert future_workload["status"] == "reserved_future"
    assert future_workload["entrypoint"] is None
    assert (
        "uv run agades-pqc nvidia-manifest --out nvidia/accelerator_manifest.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc nvidia-manifest-verify --manifest "
        "nvidia/accelerator_manifest.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc nvidia-manifest-safety --out "
        "reports/nvidia_manifest_safety.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc nvidia-manifest-safety-verify --report "
        "reports/nvidia_manifest_safety.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc hf-space-manifest --out hf/space_manifest.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc hf-dataset-verify --dataset hf/dataset"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc hf-collection-manifest --out hf/collection_manifest.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc lattice-estimator-manifest --out "
        "docs/lattice_estimator_manifest.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc lattice-estimator-baseline-contracts-verify "
        "--contracts docs/lattice_estimator_baseline_contracts.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc prime-manifest --out "
        "prime_intellect/verifiers_environment/prime_manifest.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc prime-schemas --out prime_intellect/schemas"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc publication-manifest --out "
        "docs/publication_manifest.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc public-benchmark-manifest --out "
        "docs/public_benchmark_manifest.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc public-benchmark-verify --manifest "
        "docs/public_benchmark_manifest.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc public-run-export --out public/run_export"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc public-run-export-verify --export public/run_export"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc benchmark-source-contracts --out "
        "docs/benchmark_source_contracts.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc benchmark-source-verify --contracts "
        "docs/benchmark_source_contracts.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc source-catalog-verify --catalog "
        "docs/source_catalog.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc family-support-verify --matrix "
        "docs/family_support_matrix.json"
        in manifest["release_gates"]
    )
    assert (
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json"
        in manifest["release_gates"]
    )


def test_committed_nvidia_accelerator_manifest_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "accelerator_manifest.json"
    committed = Path("nvidia/accelerator_manifest.json")

    write_nvidia_accelerator_manifest(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_nvidia_manifest_verify_accepts_current_manifest() -> None:
    verifier = getattr(nvidia_accelerator, "verify_nvidia_accelerator_manifest", None)
    assert verifier is not None

    result = verifier(Path("nvidia/accelerator_manifest.json"))

    assert result == {
        "schema_version": "agades.pqc.nvidia_accelerator_verification.v1",
        "manifest_path": "nvidia/accelerator_manifest.json",
        "accepted": True,
        "summary": {
            "all_current_workloads_cpu": True,
            "current_gpu_required_workload_count": 0,
            "current_workload_count": 26,
            "families_with_future_reviewed_adapters": 8,
            "family_count": 9,
            "failure_count": 0,
            "non_lattice_toy_evaluator_count": 41,
            "non_lattice_toy_operator_security_claims": 0,
            "non_lattice_toy_operator_variant_count": 41,
            "public_run_bundle_count": 18,
            "raw_mapping_redaction_covered": True,
            "report_redaction_records": 2,
            "review_required_before_claims": True,
            "reserved_future_gpu_required_workload_count": 1,
            "typed_trace_redaction_covered": True,
            "total_workload_count": 27,
        },
        "failures": [],
    }


def test_nvidia_manifest_verify_rejects_current_gpu_runtime(
    tmp_path: Path,
) -> None:
    verifier = getattr(nvidia_accelerator, "verify_nvidia_accelerator_manifest", None)
    assert verifier is not None

    out = tmp_path / "accelerator_manifest.json"
    manifest = build_nvidia_accelerator_manifest()
    manifest["mvp_runtime"]["current_gpu_required"] = True
    manifest["workload_summary"]["current_gpu_required_workload_count"] = 1
    manifest["family_support"]["review_required_before_claims"] = False
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verifier(out)

    assert result["accepted"] is False
    assert "NVIDIA manifest is not in sync." in result["failures"]
    assert "NVIDIA MVP runtime must not require GPU." in result["failures"]
    assert (
        "NVIDIA manifest current GPU-required workload count must be zero."
        in result["failures"]
    )
    assert (
        "NVIDIA manifest family support must require review before claims."
        in result["failures"]
    )


def test_nvidia_manifest_verify_rejects_source_scope_claim(
    tmp_path: Path,
) -> None:
    verifier = getattr(nvidia_accelerator, "verify_nvidia_accelerator_manifest", None)
    assert verifier is not None

    out = tmp_path / "accelerator_manifest.json"
    manifest = build_nvidia_accelerator_manifest()
    manifest["source_catalog_scope"]["non_lattice_toy_operator_security_claims"] = 1
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verifier(out)

    assert result["accepted"] is False
    assert "NVIDIA manifest is not in sync." in result["failures"]
    assert (
        "NVIDIA manifest source catalog scope must not contain "
        "non-lattice toy security claims."
    ) in result["failures"]


def test_nvidia_manifest_verify_rejects_redaction_boundary_drift(
    tmp_path: Path,
) -> None:
    verifier = getattr(nvidia_accelerator, "verify_nvidia_accelerator_manifest", None)
    assert verifier is not None

    out = tmp_path / "accelerator_manifest.json"
    manifest = build_nvidia_accelerator_manifest()
    manifest["public_private_boundary"]["report_generator_redaction"][
        "raw_mapping_redaction_covered"
    ] = False
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verifier(out)

    assert result["accepted"] is False
    assert result["summary"]["raw_mapping_redaction_covered"] is False
    assert "NVIDIA manifest is not in sync." in result["failures"]
    assert (
        "NVIDIA manifest raw trace mapping redaction gate is incomplete."
        in result["failures"]
    )


def test_nvidia_manifest_verify_rejects_empty_json_object(tmp_path: Path) -> None:
    verifier = getattr(nvidia_accelerator, "verify_nvidia_accelerator_manifest", None)
    assert verifier is not None

    out = tmp_path / "accelerator_manifest.json"
    out.write_text("{}\n", encoding="utf-8")

    result = verifier(out)

    assert result["accepted"] is False
    assert "NVIDIA manifest is not in sync." in result["failures"]
    assert "NVIDIA manifest project must be an object." in result["failures"]
    assert "NVIDIA manifest family_support must be an object." in result["failures"]


def test_nvidia_manifest_cli_writes_manifest(tmp_path: Path) -> None:
    out = tmp_path / "accelerator_manifest.json"

    result = CliRunner().invoke(app, ["nvidia-manifest", "--out", str(out)])

    assert result.exit_code == 0
    assert f"nvidia_manifest={out}" in result.output
    assert json.loads(out.read_text())["schema_version"] == (
        "agades.pqc.nvidia_accelerator.v1"
    )


def test_nvidia_manifest_verify_cli_accepts_current_manifest() -> None:
    result = CliRunner().invoke(
        app,
        [
            "nvidia-manifest-verify",
            "--manifest",
            "nvidia/accelerator_manifest.json",
        ],
    )

    assert result.exit_code == 0
    assert "agades.pqc.nvidia_accelerator_verification.v1" in result.output
    assert '"accepted": true' in result.output
