from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.family_support import (
    summarize_family_support_matrix,
)
from agades_pqc_gym.integrations.public_private_boundary import (
    build_public_private_boundary,
    redaction_summary_fields,
    verify_public_private_boundary,
)
from agades_pqc_gym.integrations.source_catalog import summarize_source_catalog_scope

NVIDIA_ACCELERATOR_SCHEMA = "agades.pqc.nvidia_accelerator.v1"
NVIDIA_ACCELERATOR_VERIFICATION_SCHEMA = (
    "agades.pqc.nvidia_accelerator_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
_EXPECTED_FALSE_SAFETY_FLAGS = (
    "contains_private_traces",
    "arbitrary_code_execution",
    "live_targeting",
    "security_claim",
    "publishes_private_candidates",
)
_REQUIRED_PUBLIC_ARTIFACTS = {
    "benchmark_source_contracts": "docs/benchmark_source_contracts.json",
    "family_support_matrix": "docs/family_support_matrix.json",
    "huggingface_collection_manifest": "hf/collection_manifest.json",
    "huggingface_dataset": "hf/dataset",
    "huggingface_space": "hf/app.py",
    "huggingface_space_manifest": "hf/space_manifest.json",
    "lattice_estimator_baseline_contracts": (
        "docs/lattice_estimator_baseline_contracts.json"
    ),
    "lattice_estimator_manifest": "docs/lattice_estimator_manifest.json",
    "prime_environment_manifest": (
        "prime_intellect/verifiers_environment/prime_manifest.json"
    ),
    "prime_verifier_schemas": "prime_intellect/schemas/schema_manifest.json",
    "prime_verifiers_environment": "prime_intellect/verifiers_environment",
    "public_benchmark_manifest": "docs/public_benchmark_manifest.json",
    "public_run_export": "public/run_export/manifest.json",
    "publication_manifest": "docs/publication_manifest.json",
    "release_audit": "public/release_audit.json",
    "source_catalog": "docs/source_catalog.json",
}
_REQUIRED_RELEASE_GATES = (
    "uv run agades-pqc nvidia-manifest --out nvidia/accelerator_manifest.json",
    "uv run agades-pqc nvidia-manifest-verify --manifest "
    "nvidia/accelerator_manifest.json",
    "uv run agades-pqc nvidia-manifest-safety --out "
    "reports/nvidia_manifest_safety.json",
    "uv run agades-pqc nvidia-manifest-safety-verify --report "
    "reports/nvidia_manifest_safety.json",
    "uv run agades-pqc lattice-estimator-baseline-contracts --out "
    "docs/lattice_estimator_baseline_contracts.json",
    "uv run agades-pqc lattice-estimator-baseline-contracts-verify --contracts "
    "docs/lattice_estimator_baseline_contracts.json",
    "uv run agades-pqc ecosystem-smoke-verify --report "
    "reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
)


def build_nvidia_accelerator_manifest(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    public_run_bundles = _public_run_bundles(project_root)
    family_support_matrix = json.loads(
        (project_root / "docs" / "family_support_matrix.json").read_text(
            encoding="utf-8"
        )
    )
    source_catalog = json.loads(
        (project_root / "docs" / "source_catalog.json").read_text(encoding="utf-8")
    )
    manifest = {
        "schema_version": NVIDIA_ACCELERATOR_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
            "cli": "agades-pqc",
        },
        "positioning": {
            "summary": (
                "Evaluator-driven public PQC research workbench with deterministic "
                "verifier outputs and accelerator-ready future workload boundaries."
            ),
            "current_scope": "toy-and-schema-only-public-artifacts",
            "not_a_security_claim_generator": True,
        },
        "mvp_runtime": {
            "current_gpu_required": False,
            "gpu_status": "future_acceleration_surface",
            "current_public_backend": "deterministic-python-verifier",
            "future_gpu_targets": [
                "lattice reduction reproduction ladders",
                "batch evaluation of public AttackPlan candidates",
                "side-channel trace analysis harnesses after expert review",
            ],
        },
        "public_artifacts": {
            "source_catalog": "docs/source_catalog.json",
            "benchmark_source_contracts": "docs/benchmark_source_contracts.json",
            "publication_manifest": "docs/publication_manifest.json",
            "public_benchmark_manifest": "docs/public_benchmark_manifest.json",
            "public_run_export": "public/run_export/manifest.json",
            "family_support_matrix": "docs/family_support_matrix.json",
            "lattice_estimator_manifest": "docs/lattice_estimator_manifest.json",
            "lattice_estimator_baseline_contracts": (
                "docs/lattice_estimator_baseline_contracts.json"
            ),
            "release_audit": "public/release_audit.json",
            "huggingface_dataset": "hf/dataset",
            "huggingface_space": "hf/app.py",
            "huggingface_space_manifest": "hf/space_manifest.json",
            "huggingface_collection_manifest": "hf/collection_manifest.json",
            "prime_verifiers_environment": "prime_intellect/verifiers_environment",
            "prime_environment_manifest": (
                "prime_intellect/verifiers_environment/prime_manifest.json"
            ),
            "prime_verifier_schemas": "prime_intellect/schemas/schema_manifest.json",
            "public_run_bundles": public_run_bundles,
            "accelerator_strategy": "docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md",
        },
        "family_support": summarize_family_support_matrix(family_support_matrix),
        "source_catalog_scope": summarize_source_catalog_scope(source_catalog),
        "public_private_boundary": build_public_private_boundary(project_root),
        "workloads": [
            {
                "id": "public-verifier-json",
                "status": "current",
                "entrypoint": "agades-pqc verify",
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Deterministic JSON scoring for toy/schema-only AttackPlans."
                ),
            },
            {
                "id": "lattice-toy-benchmark",
                "status": "current",
                "entrypoint": "agades-pqc benchmark benchmarks/lattice_toy_lwe",
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy LWE benchmark plumbing with mock estimator output."
                ),
            },
            {
                "id": "lattice-mlwe-downscaled-benchmark",
                "status": "current",
                "entrypoint": "agades-pqc benchmark benchmarks/lattice_mlkem_like",
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public downscaled MLWE benchmark plumbing with mock estimator "
                    "output."
                ),
            },
            {
                "id": "lattice-downscaled-lwe-instance-solve-benchmark",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark "
                    "benchmarks/lattice_downscaled_lwe_instance_solve"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public tiny LWE fixture-solving benchmark plumbing with "
                    "bounded exhaustive search; not deployed-parameter evidence."
                ),
            },
            {
                "id": "lattice-downscaled-mlwe-instance-solve-benchmark",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark "
                    "benchmarks/lattice_downscaled_mlwe_instance_solve"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public tiny linearized MLWE fixture-solving benchmark "
                    "plumbing with bounded exhaustive search; not ML-KEM "
                    "security evidence."
                ),
            },
            {
                "id": "lattice-schema-only-routing",
                "status": "current",
                "entrypoint": "agades-pqc benchmark benchmarks/lattice_schema_only",
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public schema-only NTRU/SIS routing checks that keep "
                    "unreviewed lattice families out of LWE/MLWE estimators."
                ),
            },
            {
                "id": "code-based-toy-isd-benchmark",
                "status": "current",
                "entrypoint": "agades-pqc benchmark benchmarks/code_based_toy_isd",
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy code-based ISD plumbing with bounded Prange, "
                    "Lee-Brickell, Stern, Dumer, and quasi-cyclic rotation "
                    "estimators."
                ),
            },
            {
                "id": "code-based-toy-hqc-benchmark",
                "status": "current",
                "entrypoint": "agades-pqc benchmark benchmarks/code_based_toy_hqc",
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public tiny HQC-inspired fixture plumbing with bounded "
                    "repetition, weighted repetition, parity-check, circulant, "
                    "erasure-aided syndrome, and circulant-erasure decoders; "
                    "not an HQC result or security claim."
                ),
            },
            {
                "id": "code-based-toy-mdpc-benchmark",
                "status": "current",
                "entrypoint": "agades-pqc benchmark benchmarks/code_based_toy_mdpc",
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public tiny MDPC/BIKE-inspired bit-flip fixture plumbing "
                    "with bounded JSON inputs; not a BIKE result or security "
                    "claim."
                ),
            },
            {
                "id": "code-based-toy-classic-mceliece-benchmark",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark "
                    "benchmarks/code_based_toy_classic_mceliece"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public tiny Classic-McEliece-inspired binary syndrome "
                    "and public support-set fixture plumbing with bounded "
                    "exact-weight search; not a Classic McEliece result or "
                    "security claim."
                ),
            },
            {
                "id": "hash-based-toy-bound-benchmark",
                "status": "current",
                "entrypoint": "agades-pqc benchmark benchmarks/hash_based_toy_bound",
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy hash-bound plumbing with bounded preimage "
                    "and birthday-collision cost models."
                ),
            },
            {
                "id": "hash-based-toy-signature-benchmark",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark benchmarks/hash_based_toy_signature"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy hash-signature chain and Merkle auth-path "
                    "verification plumbing with SHAKE256 fixtures; not a "
                    "signature security claim."
                ),
            },
            {
                "id": "hash-based-toy-slh-dsa-hypertree-benchmark",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark benchmarks/hash_based_toy_signature"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy hash-based SLH-DSA-like hypertree fixture "
                    "plumbing with bounded JSON-only SHAKE256 checks; not an "
                    "SLH-DSA result and not a security claim."
                ),
            },
            {
                "id": "hash-based-toy-misuse-benchmark",
                "status": "current",
                "entrypoint": "agades-pqc benchmark benchmarks/hash_based_toy_misuse",
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy hash reused-salt misuse fixture plumbing with "
                    "bounded JSON-only SHAKE256 checks; not exploit evidence "
                    "or a security claim."
                ),
            },
            {
                "id": "multivariate-toy-mq-benchmark",
                "status": "current",
                "entrypoint": "agades-pqc benchmark benchmarks/multivariate_toy_mq",
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy multivariate MQ plumbing with a bounded "
                    "exhaustive-search cost model."
                ),
            },
            {
                "id": "multivariate-toy-minrank-benchmark",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark benchmarks/multivariate_toy_minrank"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy multivariate MinRank plumbing with a bounded "
                    "exhaustive-search cost model; not a UOV/MAYO security claim."
                ),
            },
            {
                "id": "multivariate-toy-uov-benchmark",
                "status": "current",
                "entrypoint": "agades-pqc benchmark benchmarks/multivariate_toy_uov",
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy UOV-inspired public-map verification fixture "
                    "plumbing over GF(2); not a UOV, MAYO, Rainbow, forgery, "
                    "or security claim."
                ),
            },
            {
                "id": "implementation-security-toy-kat-benchmark",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark benchmarks/implementation_security_toy_kat"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy implementation-security KAT digest plumbing "
                    "without executing binaries or reading live artifacts."
                ),
            },
            {
                "id": "implementation-security-toy-benchmark-summary",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark "
                    "benchmarks/implementation_security_toy_benchmark"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy implementation-security benchmark-summary "
                    "plumbing from bounded JSON cycle arrays without executing "
                    "binaries, reading device logs, or claiming performance."
                ),
            },
            {
                "id": "implementation-security-toy-memory-footprint-benchmark",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark "
                    "benchmarks/implementation_security_toy_benchmark"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy implementation-security memory-footprint "
                    "plumbing from bounded JSON component byte summaries "
                    "without executing binaries, reading device logs, or "
                    "claiming performance; not a memory-usage claim."
                ),
            },
            {
                "id": "implementation-security-toy-binary-size-benchmark",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark "
                    "benchmarks/implementation_security_toy_benchmark"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy implementation-security binary-size plumbing "
                    "from bounded JSON binary-size summaries without executing "
                    "binaries, reading build logs, or claiming performance; "
                    "not a binary-size claim."
                ),
            },
            {
                "id": "implementation-security-toy-stack-usage-benchmark",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark "
                    "benchmarks/implementation_security_toy_benchmark"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy implementation-security stack-usage plumbing "
                    "from bounded JSON high-water samples without executing "
                    "binaries, reading device logs, or claiming performance; "
                    "not a stack-usage claim."
                ),
            },
            {
                "id": "implementation-security-toy-timing-benchmark",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark "
                    "benchmarks/implementation_security_toy_timing"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public toy implementation-security timing-summary plumbing "
                    "from bounded JSON cycle arrays without executing binaries, "
                    "reading trace files, or claiming constant-time behavior."
                ),
            },
            {
                "id": "isogeny-historical-toy-path-benchmark",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark benchmarks/isogeny_historical_toy_path"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public historical toy isogeny path plumbing without "
                    "claiming current-standard security impact."
                ),
            },
            {
                "id": "isogeny-historical-toy-volcano-benchmark",
                "status": "current",
                "entrypoint": (
                    "agades-pqc benchmark benchmarks/isogeny_historical_toy_path"
                ),
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": (
                    "Public historical toy volcano-style isogeny graph/path "
                    "verification plumbing; not a CSIDH, SIDH, "
                    "current-standard, or security claim."
                ),
            },
            {
                "id": "schema-only-family-routing",
                "status": "current",
                "entrypoint": "agades-pqc benchmark benchmarks/code_based_schema_only",
                "resource_class": "cpu",
                "gpu_required": False,
                "purpose": "Validate non-lattice routing without fake estimates.",
            },
            {
                "id": "future-gpu-reproduction-ladder",
                "status": "reserved_future",
                "entrypoint": None,
                "resource_class": "gpu-future",
                "gpu_required": True,
                "purpose": (
                    "Reserved surface for reviewed public reproduction workloads; "
                    "not part of the current MVP runtime."
                ),
            },
        ],
        "safety": {
            "contains_private_traces": False,
            "arbitrary_code_execution": False,
            "live_targeting": False,
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "release_gates": [
            "uv run pytest -q",
            "uv run ruff check .",
            "uv build",
            "uv build prime_intellect/verifiers_environment",
            "uv run agades-pqc hf-dataset --out hf/dataset",
            "uv run agades-pqc hf-dataset-verify --dataset hf/dataset",
            "uv run agades-pqc benchmark-source-contracts --out "
            "docs/benchmark_source_contracts.json",
            "uv run agades-pqc benchmark-source-verify --contracts "
            "docs/benchmark_source_contracts.json",
            "uv run agades-pqc source-catalog --out docs/source_catalog.json",
            "uv run agades-pqc source-catalog-verify --catalog "
            "docs/source_catalog.json",
            "uv run agades-pqc family-support --out docs/family_support_matrix.json",
            "uv run agades-pqc family-support-verify --matrix "
            "docs/family_support_matrix.json",
            "uv run agades-pqc lattice-estimator-manifest --out "
            "docs/lattice_estimator_manifest.json",
            "uv run agades-pqc lattice-estimator-baseline-contracts --out "
            "docs/lattice_estimator_baseline_contracts.json",
            "uv run agades-pqc lattice-estimator-baseline-contracts-verify "
            "--contracts docs/lattice_estimator_baseline_contracts.json",
            "uv run agades-pqc hf-space-manifest --out hf/space_manifest.json",
            "uv run agades-pqc hf-collection-manifest --out "
            "hf/collection_manifest.json",
            *_REQUIRED_RELEASE_GATES[:4],
            "uv run agades-pqc prime-manifest --out "
            "prime_intellect/verifiers_environment/prime_manifest.json",
            "uv run agades-pqc prime-schemas --out prime_intellect/schemas",
            "uv run agades-pqc publication-manifest --out "
            "docs/publication_manifest.json",
            "uv run agades-pqc public-benchmark-manifest --out "
            "docs/public_benchmark_manifest.json",
            "uv run agades-pqc public-benchmark-verify --manifest "
            "docs/public_benchmark_manifest.json",
            "uv run agades-pqc public-run-export --out public/run_export",
            "uv run agades-pqc public-run-export-verify --export public/run_export",
            "uv run agades-pqc ecosystem-smoke-verify --report "
            "reports/ecosystem_smoke.json",
            "uv run agades-pqc release-audit --out public/release_audit.json",
        ],
    }
    manifest["workload_summary"] = _workload_summary(
        manifest["workloads"],
        public_run_bundles,
    )
    return manifest


def verify_nvidia_accelerator_manifest(
    manifest_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    manifest = _read_nvidia_manifest(manifest_path, failures)

    if manifest or not failures:
        expected = build_nvidia_accelerator_manifest(root=project_root)
        if manifest != expected:
            failures.append("NVIDIA manifest is not in sync.")

        _verify_project_metadata(manifest, failures)
        _verify_public_artifacts(project_root, manifest, failures)
        _verify_runtime_scope(manifest, failures)
        _verify_workloads(manifest, failures)
        _verify_family_support(manifest, failures)
        _verify_source_catalog_scope(manifest, failures)
        _verify_public_private_boundary(manifest, failures)
        _verify_release_gates(manifest, failures)

    return _verification_result(manifest_path, manifest, failures)


def write_nvidia_accelerator_manifest(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    manifest = build_nvidia_accelerator_manifest(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _read_nvidia_manifest(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"NVIDIA manifest is missing: {path.as_posix()}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"NVIDIA manifest is invalid JSON at line {exc.lineno}.")
        return {}

    if not isinstance(payload, dict):
        failures.append("NVIDIA manifest must be a JSON object.")
        return {}
    return payload


def _verify_project_metadata(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    if manifest.get("schema_version") != NVIDIA_ACCELERATOR_SCHEMA:
        failures.append(
            f"NVIDIA manifest schema_version must be {NVIDIA_ACCELERATOR_SCHEMA}."
        )
    project = manifest.get("project")
    if not isinstance(project, dict):
        failures.append("NVIDIA manifest project must be an object.")
        return
    expected_project = {
        "name": "Agades PQC Gym",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
        "package": "agades_pqc_gym",
        "cli": "agades-pqc",
    }
    for key, expected in expected_project.items():
        if project.get(key) != expected:
            failures.append(f"NVIDIA manifest project.{key} is incorrect.")


def _verify_public_artifacts(
    root: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    public_artifacts = manifest.get("public_artifacts")
    if not isinstance(public_artifacts, dict):
        failures.append("NVIDIA manifest public_artifacts must be an object.")
        return

    for artifact_id, expected_path in _REQUIRED_PUBLIC_ARTIFACTS.items():
        if public_artifacts.get(artifact_id) != expected_path:
            failures.append(
                f"NVIDIA manifest public_artifacts.{artifact_id} is incorrect."
            )
            continue
        if not (root / expected_path).exists():
            failures.append(f"NVIDIA manifest artifact is missing: {expected_path}.")

    public_run_bundles = public_artifacts.get("public_run_bundles")
    if not isinstance(public_run_bundles, list) or not public_run_bundles:
        failures.append("NVIDIA manifest public_run_bundles must be a non-empty list.")
        return
    for bundle_path in public_run_bundles:
        if not isinstance(bundle_path, str):
            failures.append(
                "NVIDIA manifest public_run_bundles entries must be strings."
            )
            continue
        if not (root / bundle_path).is_dir():
            failures.append(
                f"NVIDIA manifest public run bundle is missing: {bundle_path}."
            )


def _verify_runtime_scope(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    positioning = manifest.get("positioning")
    if not isinstance(positioning, dict):
        failures.append("NVIDIA manifest positioning must be an object.")
    elif positioning.get("not_a_security_claim_generator") is not True:
        failures.append("NVIDIA manifest must not be a security-claim generator.")

    mvp_runtime = manifest.get("mvp_runtime")
    if not isinstance(mvp_runtime, dict):
        failures.append("NVIDIA manifest mvp_runtime must be an object.")
    else:
        if mvp_runtime.get("current_gpu_required") is not False:
            failures.append("NVIDIA MVP runtime must not require GPU.")
        if mvp_runtime.get("current_public_backend") != "deterministic-python-verifier":
            failures.append(
                "NVIDIA current public backend must stay deterministic Python."
            )
        if mvp_runtime.get("gpu_status") != "future_acceleration_surface":
            failures.append("NVIDIA GPU status must stay future_acceleration_surface.")

    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        failures.append("NVIDIA manifest safety must be an object.")
        return
    for flag in _EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            failures.append(f"NVIDIA manifest safety.{flag} must be false.")


def _verify_workloads(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    workloads = manifest.get("workloads")
    if not isinstance(workloads, list) or not workloads:
        failures.append("NVIDIA manifest workloads must be a non-empty list.")
        workloads = []

    workload_ids: set[str] = set()
    current_workloads = []
    reserved_future_workloads = []
    for index, workload in enumerate(workloads):
        if not isinstance(workload, dict):
            failures.append(f"NVIDIA workload[{index}] must be an object.")
            continue
        workload_id = workload.get("id")
        if not isinstance(workload_id, str) or not workload_id:
            failures.append(f"NVIDIA workload[{index}].id must be a non-empty string.")
        elif workload_id in workload_ids:
            failures.append(f"NVIDIA workload id is duplicated: {workload_id}.")
        else:
            workload_ids.add(workload_id)

        status = workload.get("status")
        resource_class = workload.get("resource_class")
        gpu_required = workload.get("gpu_required")
        if status == "current":
            current_workloads.append(workload)
            if resource_class != "cpu":
                failures.append(f"NVIDIA current workload {workload_id} must be CPU.")
            if gpu_required is not False:
                failures.append(
                    f"NVIDIA current workload {workload_id} must not require GPU."
                )
            if not isinstance(workload.get("entrypoint"), str):
                failures.append(
                    f"NVIDIA current workload {workload_id} must have an entrypoint."
                )
        elif status == "reserved_future":
            reserved_future_workloads.append(workload)
            if resource_class != "gpu-future":
                failures.append(
                    f"NVIDIA reserved future workload {workload_id} must be gpu-future."
                )
            if gpu_required is not True:
                failures.append(
                    f"NVIDIA reserved future workload {workload_id} must require GPU."
                )
            if workload.get("entrypoint") is not None:
                failures.append(
                    f"NVIDIA reserved future workload {workload_id} must have no "
                    "entrypoint."
                )
        else:
            failures.append(f"NVIDIA workload {workload_id} has unsupported status.")

    workload_summary = manifest.get("workload_summary")
    if not isinstance(workload_summary, dict):
        failures.append("NVIDIA manifest workload_summary must be an object.")
        workload_summary = {}
    expected_summary = _workload_summary(
        [workload for workload in workloads if isinstance(workload, dict)],
        _public_run_bundle_paths(manifest),
    )
    if workload_summary != expected_summary:
        failures.append("NVIDIA workload summary is inconsistent.")

    if workload_summary.get("all_current_workloads_cpu") is not True:
        failures.append("NVIDIA current workloads must all be CPU.")
    if workload_summary.get("no_current_workload_requires_gpu") is not True:
        failures.append("NVIDIA current workloads must not require GPU.")
    if workload_summary.get("current_gpu_required_workload_count") != 0:
        failures.append(
            "NVIDIA manifest current GPU-required workload count must be zero."
        )
    if workload_summary.get("reserved_future_gpu_required_workload_count") != 1:
        failures.append(
            "NVIDIA manifest must keep exactly one reserved future GPU workload."
        )
    if workload_summary.get("current_workload_count") != len(current_workloads):
        failures.append("NVIDIA current workload count is inconsistent.")
    if workload_summary.get("reserved_future_workload_count") != len(
        reserved_future_workloads
    ):
        failures.append("NVIDIA reserved future workload count is inconsistent.")
    if workload_summary.get("total_workload_count") != len(workloads):
        failures.append("NVIDIA total workload count is inconsistent.")


def _verify_family_support(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    family_support = manifest.get("family_support")
    if not isinstance(family_support, dict):
        failures.append("NVIDIA manifest family_support must be an object.")
        return
    if family_support.get("review_required_before_claims") is not True:
        failures.append(
            "NVIDIA manifest family support must require review before claims."
        )


def _verify_source_catalog_scope(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    scope = manifest.get("source_catalog_scope")
    if not isinstance(scope, dict):
        failures.append("NVIDIA manifest source_catalog_scope must be an object.")
        return
    if scope.get("non_lattice_toy_operator_security_claims") != 0:
        failures.append(
            "NVIDIA manifest source catalog scope must not contain "
            "non-lattice toy security claims."
        )
    if scope.get("non_lattice_toy_evaluator_count") != scope.get("source_count"):
        failures.append("NVIDIA manifest source catalog scope must cover every source.")
    if scope.get("non_lattice_toy_operator_variant_count") != scope.get(
        "source_count"
    ):
        failures.append(
            "NVIDIA manifest source catalog operator scope must cover every source."
        )


def _verify_public_private_boundary(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    public_private_boundary = manifest.get("public_private_boundary")
    if not isinstance(public_private_boundary, dict):
        failures.append("NVIDIA manifest public_private_boundary must be an object.")
        return
    verify_public_private_boundary(
        public_private_boundary,
        failures,
        label="NVIDIA manifest",
    )


def _verify_release_gates(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    release_gates = manifest.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append("NVIDIA manifest release_gates must be a list.")
        return
    for required_gate in _REQUIRED_RELEASE_GATES:
        if required_gate not in release_gates:
            failures.append(f"NVIDIA manifest release gate missing: {required_gate}")


def _public_run_bundle_paths(manifest: dict[str, Any]) -> list[str]:
    public_artifacts = manifest.get("public_artifacts")
    if not isinstance(public_artifacts, dict):
        return []
    public_run_bundles = public_artifacts.get("public_run_bundles")
    if not isinstance(public_run_bundles, list):
        return []
    return [path for path in public_run_bundles if isinstance(path, str)]


def _verification_result(
    manifest_path: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    workload_summary = manifest.get("workload_summary", {})
    if not isinstance(workload_summary, dict):
        workload_summary = {}
    family_support = manifest.get("family_support", {})
    if not isinstance(family_support, dict):
        family_support = {}
    source_catalog_scope = manifest.get("source_catalog_scope", {})
    if not isinstance(source_catalog_scope, dict):
        source_catalog_scope = {}
    public_private_boundary = manifest.get("public_private_boundary", {})
    if not isinstance(public_private_boundary, dict):
        public_private_boundary = {}
    redaction_summary = redaction_summary_fields(public_private_boundary)
    return {
        "schema_version": NVIDIA_ACCELERATOR_VERIFICATION_SCHEMA,
        "manifest_path": manifest_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "all_current_workloads_cpu": workload_summary.get(
                "all_current_workloads_cpu"
            ),
            "current_gpu_required_workload_count": workload_summary.get(
                "current_gpu_required_workload_count",
                0,
            ),
            "current_workload_count": workload_summary.get(
                "current_workload_count",
                0,
            ),
            "families_with_future_reviewed_adapters": _list_count(
                family_support.get("families_with_future_reviewed_adapters")
            ),
            "family_count": family_support.get("family_count"),
            "failure_count": len(failures),
            "non_lattice_toy_evaluator_count": source_catalog_scope.get(
                "non_lattice_toy_evaluator_count"
            ),
            "non_lattice_toy_operator_security_claims": (
                source_catalog_scope.get("non_lattice_toy_operator_security_claims")
            ),
            "non_lattice_toy_operator_variant_count": source_catalog_scope.get(
                "non_lattice_toy_operator_variant_count"
            ),
            "public_run_bundle_count": workload_summary.get(
                "public_run_bundle_count",
                0,
            ),
            **redaction_summary,
            "review_required_before_claims": family_support.get(
                "review_required_before_claims"
            ),
            "reserved_future_gpu_required_workload_count": workload_summary.get(
                "reserved_future_gpu_required_workload_count",
                0,
            ),
            "total_workload_count": workload_summary.get("total_workload_count", 0),
        },
        "failures": failures,
    }


def _list_count(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _public_run_bundles(root: Path) -> list[str]:
    public_runs_root = root / "examples" / "public_runs"
    if not public_runs_root.is_dir():
        return []
    return [
        path.relative_to(root).as_posix()
        for path in sorted(public_runs_root.iterdir())
        if path.is_dir()
    ]


def _workload_summary(
    workloads: list[dict[str, Any]],
    public_run_bundles: list[str],
) -> dict[str, Any]:
    current_workloads = [
        workload for workload in workloads if workload.get("status") == "current"
    ]
    reserved_future_workloads = [
        workload
        for workload in workloads
        if workload.get("status") == "reserved_future"
    ]
    cpu_workloads = [
        workload for workload in workloads if workload.get("resource_class") == "cpu"
    ]
    gpu_future_workloads = [
        workload
        for workload in workloads
        if workload.get("resource_class") == "gpu-future"
    ]
    current_gpu_required_workloads = [
        workload
        for workload in current_workloads
        if workload.get("gpu_required") is True
    ]
    reserved_future_gpu_required_workloads = [
        workload
        for workload in reserved_future_workloads
        if workload.get("gpu_required") is True
    ]
    return {
        "total_workload_count": len(workloads),
        "current_workload_count": len(current_workloads),
        "reserved_future_workload_count": len(reserved_future_workloads),
        "cpu_workload_count": len(cpu_workloads),
        "gpu_future_workload_count": len(gpu_future_workloads),
        "current_gpu_required_workload_count": len(current_gpu_required_workloads),
        "reserved_future_gpu_required_workload_count": len(
            reserved_future_gpu_required_workloads
        ),
        "public_run_bundle_count": len(public_run_bundles),
        "all_current_workloads_cpu": all(
            workload.get("resource_class") == "cpu"
            for workload in current_workloads
        ),
        "no_current_workload_requires_gpu": not current_gpu_required_workloads,
    }
