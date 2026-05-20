from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.public_private_boundary import (
    redaction_summary_fields,
)

from .nvidia_accelerator import (
    NVIDIA_ACCELERATOR_SCHEMA,
    verify_nvidia_accelerator_manifest,
)

NVIDIA_MANIFEST_SAFETY_SCHEMA = "agades.pqc.nvidia_manifest_safety.v1"
NVIDIA_MANIFEST_SAFETY_VERIFICATION_SCHEMA = (
    "agades.pqc.nvidia_manifest_safety_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT = Path("reports/nvidia_manifest_safety.json")
DEFAULT_MANIFEST = Path("nvidia/accelerator_manifest.json")

_RELEASE_GATES = (
    "uv run pytest tests/test_nvidia_manifest_safety.py -q",
    "uv run agades-pqc nvidia-manifest --out nvidia/accelerator_manifest.json",
    "uv run agades-pqc nvidia-manifest-verify --manifest "
    "nvidia/accelerator_manifest.json",
    "uv run agades-pqc nvidia-manifest-safety --out "
    "reports/nvidia_manifest_safety.json",
    "uv run agades-pqc nvidia-manifest-safety-verify --report "
    "reports/nvidia_manifest_safety.json",
    "uv run agades-pqc ecosystem-smoke-verify --report reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
)
_FALSE_SAFETY_FLAGS = (
    "arbitrary_code_execution",
    "contains_private_traces",
    "live_targeting",
    "publishes_private_candidates",
    "security_claim",
)


def build_nvidia_manifest_safety_report(
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    manifest_path = project_root / DEFAULT_MANIFEST
    failures: list[str] = []
    manifest = _read_manifest(manifest_path, failures)
    verification = verify_nvidia_accelerator_manifest(
        manifest_path,
        root=project_root,
    )
    failures.extend(str(failure) for failure in verification["failures"])

    workload_summary = _dict_or_empty(manifest.get("workload_summary"))
    mvp_runtime = _dict_or_empty(manifest.get("mvp_runtime"))
    public_artifacts = _dict_or_empty(manifest.get("public_artifacts"))
    public_private_boundary = _dict_or_empty(manifest.get("public_private_boundary"))
    family_support = _dict_or_empty(manifest.get("family_support"))
    source_catalog_scope = _dict_or_empty(manifest.get("source_catalog_scope"))

    report = {
        "schema_version": NVIDIA_MANIFEST_SAFETY_SCHEMA,
        "accepted": False,
        "manifest": {
            "in_sync": verification["accepted"] is True,
            "manifest_path": DEFAULT_MANIFEST.as_posix(),
            "manifest_schema_version": manifest.get("schema_version"),
            "project_name": _dict_or_empty(manifest.get("project")).get("name"),
        },
        "runtime": {
            "current_gpu_required": mvp_runtime.get("current_gpu_required"),
            "current_public_backend": mvp_runtime.get("current_public_backend"),
            "gpu_status": mvp_runtime.get("gpu_status"),
        },
        "workloads": {
            **workload_summary,
            "workload_count": _list_count(manifest.get("workloads")),
        },
        "artifacts": {
            "artifact_count": len(public_artifacts),
            "publication_manifest": public_artifacts.get("publication_manifest"),
            "public_run_bundle_count": _list_count(
                public_artifacts.get("public_run_bundles")
            ),
            "release_audit": public_artifacts.get("release_audit"),
        },
        "family_scope": {
            "family_count": family_support.get("family_count"),
            "non_lattice_toy_operator_security_claims": (
                source_catalog_scope.get("non_lattice_toy_operator_security_claims")
            ),
            **redaction_summary_fields(public_private_boundary),
            "review_required_before_claims": family_support.get(
                "review_required_before_claims"
            ),
        },
        "safety": {
            flag: _dict_or_empty(manifest.get("safety")).get(flag)
            for flag in _FALSE_SAFETY_FLAGS
        },
        "release_gates": list(_RELEASE_GATES),
        "failures": failures,
    }
    _validate_report_contract(report, failures)
    report["accepted"] = not failures
    report["failures"] = failures
    return report


def write_nvidia_manifest_safety_report(
    out: Path = DEFAULT_REPORT,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    report = build_nvidia_manifest_safety_report(root=root)
    resolved_out = _resolve_path(out, root=root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_nvidia_manifest_safety_report(
    report_path: Path = DEFAULT_REPORT,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    expected = build_nvidia_manifest_safety_report(root=project_root)
    failures: list[str] = []
    report = _read_report(_resolve_path(report_path, root=project_root), failures)

    if report != expected:
        failures.append("NVIDIA manifest safety report is not in sync.")
    _verify_schema(report, failures)
    _verify_manifest(report, failures)
    _verify_runtime(report, failures)
    _verify_workloads(report, failures)
    _verify_artifacts(report, failures)
    _verify_family_scope(report, failures)
    _verify_safety(report, failures)
    _verify_release_gates(report, failures)

    return {
        "schema_version": NVIDIA_MANIFEST_SAFETY_VERIFICATION_SCHEMA,
        "report_path": _display_path(report_path, root=project_root),
        "accepted": not failures,
        "summary": _verification_summary(report, failures),
        "failures": failures,
    }


def _validate_report_contract(
    report: dict[str, Any],
    failures: list[str],
) -> None:
    if report["manifest"]["in_sync"] is not True:
        failures.append("NVIDIA manifest safety report source manifest is not synced.")
    if report["runtime"]["current_gpu_required"] is not False:
        failures.append("NVIDIA manifest safety report requires current GPU.")
    if report["runtime"]["gpu_status"] != "future_acceleration_surface":
        failures.append("NVIDIA manifest safety report GPU status drifted.")
    if report["workloads"].get("all_current_workloads_cpu") is not True:
        failures.append("NVIDIA manifest safety report has non-CPU current workloads.")
    if report["workloads"].get("no_current_workload_requires_gpu") is not True:
        failures.append("NVIDIA manifest safety report has GPU-required current jobs.")
    if report["workloads"].get("current_gpu_required_workload_count") != 0:
        failures.append("NVIDIA manifest safety report current GPU count is nonzero.")
    if report["workloads"].get("reserved_future_gpu_required_workload_count") != 1:
        failures.append(
            "NVIDIA manifest safety report reserved GPU future count drifted."
        )
    if report["artifacts"]["release_audit"] != "public/release_audit.json":
        failures.append("NVIDIA manifest safety report lacks release audit artifact.")
    if report["family_scope"]["review_required_before_claims"] is not True:
        failures.append("NVIDIA manifest safety report lacks family review gate.")
    if report["family_scope"]["non_lattice_toy_operator_security_claims"] != 0:
        failures.append("NVIDIA manifest safety report advertises family claims.")
    for flag in _FALSE_SAFETY_FLAGS:
        if report["safety"].get(flag) is not False:
            failures.append(f"NVIDIA manifest safety report {flag} must be false.")


def _read_manifest(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"NVIDIA manifest is missing: {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"NVIDIA manifest is invalid JSON at line {exc.lineno}.")
        return {}
    if not isinstance(payload, dict):
        failures.append("NVIDIA manifest must be a JSON object.")
        return {}
    return payload


def _read_report(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"NVIDIA manifest safety report is missing: {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"NVIDIA manifest safety report is invalid JSON at line {exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("NVIDIA manifest safety report must be a JSON object.")
        return {}
    return payload


def _verify_schema(report: dict[str, Any], failures: list[str]) -> None:
    if report.get("schema_version") != NVIDIA_MANIFEST_SAFETY_SCHEMA:
        failures.append(
            "NVIDIA manifest safety report schema_version must be "
            f"{NVIDIA_MANIFEST_SAFETY_SCHEMA}."
        )
    if report.get("accepted") is not True:
        failures.append("NVIDIA manifest safety report is not accepted.")


def _verify_manifest(report: dict[str, Any], failures: list[str]) -> None:
    manifest = report.get("manifest")
    if not isinstance(manifest, dict):
        failures.append("NVIDIA manifest safety report manifest must be an object.")
        return
    if manifest.get("in_sync") is not True:
        failures.append("NVIDIA manifest safety report source manifest is not synced.")
    if manifest.get("manifest_path") != DEFAULT_MANIFEST.as_posix():
        failures.append("NVIDIA manifest safety report path is incorrect.")
    if manifest.get("manifest_schema_version") != NVIDIA_ACCELERATOR_SCHEMA:
        failures.append("NVIDIA manifest safety report schema reference is wrong.")
    if manifest.get("project_name") != "Agades PQC Gym":
        failures.append("NVIDIA manifest safety report project name is wrong.")


def _verify_runtime(report: dict[str, Any], failures: list[str]) -> None:
    runtime = report.get("runtime")
    if not isinstance(runtime, dict):
        failures.append("NVIDIA manifest safety report runtime must be an object.")
        return
    if runtime.get("current_gpu_required") is not False:
        failures.append("NVIDIA manifest safety report requires current GPU.")
    if runtime.get("current_public_backend") != "deterministic-python-verifier":
        failures.append("NVIDIA manifest safety report backend is wrong.")
    if runtime.get("gpu_status") != "future_acceleration_surface":
        failures.append("NVIDIA manifest safety report GPU status drifted.")


def _verify_workloads(report: dict[str, Any], failures: list[str]) -> None:
    workloads = report.get("workloads")
    if not isinstance(workloads, dict):
        failures.append("NVIDIA manifest safety report workloads must be an object.")
        return
    required_values = {
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
        "workload_count": 27,
    }
    for key, expected in required_values.items():
        if workloads.get(key) != expected:
            failures.append(f"NVIDIA manifest safety report {key} is wrong.")


def _verify_artifacts(report: dict[str, Any], failures: list[str]) -> None:
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, dict):
        failures.append("NVIDIA manifest safety report artifacts must be an object.")
        return
    if artifacts.get("artifact_count") != 18:
        failures.append("NVIDIA manifest safety report artifact count is wrong.")
    if artifacts.get("publication_manifest") != "docs/publication_manifest.json":
        failures.append("NVIDIA manifest safety report publication manifest is wrong.")
    if artifacts.get("public_run_bundle_count") != 18:
        failures.append("NVIDIA manifest safety report bundle count is wrong.")
    if artifacts.get("release_audit") != "public/release_audit.json":
        failures.append("NVIDIA manifest safety report release audit is wrong.")


def _verify_family_scope(report: dict[str, Any], failures: list[str]) -> None:
    family_scope = report.get("family_scope")
    if not isinstance(family_scope, dict):
        failures.append("NVIDIA manifest safety report family_scope must be an object.")
        return
    if family_scope.get("family_count") != 9:
        failures.append("NVIDIA manifest safety report family count is wrong.")
    if family_scope.get("non_lattice_toy_operator_security_claims") != 0:
        failures.append("NVIDIA manifest safety report advertises family claims.")
    if family_scope.get("raw_mapping_redaction_covered") is not True:
        failures.append("NVIDIA manifest safety report raw redaction is incomplete.")
    if family_scope.get("report_redaction_records") != 2:
        failures.append("NVIDIA manifest safety report redaction count is wrong.")
    if family_scope.get("review_required_before_claims") is not True:
        failures.append("NVIDIA manifest safety report lacks family review gate.")
    if family_scope.get("typed_trace_redaction_covered") is not True:
        failures.append("NVIDIA manifest safety report trace redaction is incomplete.")


def _verify_safety(report: dict[str, Any], failures: list[str]) -> None:
    safety = report.get("safety")
    if not isinstance(safety, dict):
        failures.append("NVIDIA manifest safety report safety must be an object.")
        return
    for flag in _FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            failures.append(f"NVIDIA manifest safety report {flag} must be false.")


def _verify_release_gates(report: dict[str, Any], failures: list[str]) -> None:
    release_gates = report.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append(
            "NVIDIA manifest safety report release_gates must be a list."
        )
        return
    for gate in _RELEASE_GATES:
        if gate not in release_gates:
            failures.append(
                f"NVIDIA manifest safety report release gate missing: {gate}"
            )


def _verification_summary(
    report: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    runtime = report.get("runtime") if isinstance(report.get("runtime"), dict) else {}
    workloads = (
        report.get("workloads") if isinstance(report.get("workloads"), dict) else {}
    )
    artifacts = (
        report.get("artifacts") if isinstance(report.get("artifacts"), dict) else {}
    )
    safety = report.get("safety") if isinstance(report.get("safety"), dict) else {}
    return {
        "all_current_workloads_cpu": workloads.get("all_current_workloads_cpu"),
        "artifact_count": artifacts.get("artifact_count"),
        "cpu_workload_count": workloads.get("cpu_workload_count"),
        "current_gpu_required": runtime.get("current_gpu_required"),
        "current_gpu_required_workload_count": workloads.get(
            "current_gpu_required_workload_count"
        ),
        "current_workload_count": workloads.get("current_workload_count"),
        "failure_count": len(failures),
        "gpu_future_workload_count": workloads.get("gpu_future_workload_count"),
        "gpu_status": runtime.get("gpu_status"),
        "no_current_workload_requires_gpu": workloads.get(
            "no_current_workload_requires_gpu"
        ),
        "public_run_bundle_count": artifacts.get("public_run_bundle_count"),
        "reserved_future_gpu_required_workload_count": workloads.get(
            "reserved_future_gpu_required_workload_count"
        ),
        "reserved_future_workload_count": workloads.get(
            "reserved_future_workload_count"
        ),
        "security_claim": safety.get("security_claim"),
        "workload_count": workloads.get("workload_count"),
    }


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_count(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _resolve_path(path: Path, *, root: Path | None) -> Path:
    if path.is_absolute() or root is None:
        return path
    return root / path


def _display_path(path: Path, *, root: Path) -> str:
    resolved = _resolve_path(path, root=root)
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return resolved.as_posix()
