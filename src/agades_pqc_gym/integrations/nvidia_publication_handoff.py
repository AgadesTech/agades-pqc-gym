from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.family_support import (
    build_family_support_matrix,
    summarize_family_support_matrix,
)
from agades_pqc_gym.integrations.nvidia_accelerator import (
    verify_nvidia_accelerator_manifest,
)
from agades_pqc_gym.integrations.source_catalog import (
    build_source_catalog,
    summarize_source_catalog_scope,
)

NVIDIA_PUBLICATION_HANDOFF_SCHEMA = "agades.pqc.nvidia_publication_handoff.v1"
NVIDIA_PUBLICATION_HANDOFF_VERIFICATION_SCHEMA = (
    "agades.pqc.nvidia_publication_handoff_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
PROJECT = {
    "name": "Agades PQC Gym",
    "package": "agades_pqc_gym",
    "cli": "agades-pqc",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
}
ACCELERATOR_MANIFEST_PATH = Path("nvidia/accelerator_manifest.json")
ACCELERATOR_STRATEGY_PATH = Path("docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md")
LOCAL_ARTIFACT_PATHS = [
    ACCELERATOR_STRATEGY_PATH.as_posix(),
    "nvidia/README.md",
    ACCELERATOR_MANIFEST_PATH.as_posix(),
    "docs/source_catalog.json",
    "docs/benchmark_source_contracts.json",
    "docs/family_support_matrix.json",
    "docs/public_benchmark_manifest.json",
    "public/run_export/manifest.json",
    "docs/lattice_estimator_manifest.json",
    "docs/lattice_estimator_baseline_contracts.json",
    "hf/collection_manifest.json",
    "docs/huggingface_publication_handoff.json",
    "prime_intellect/verifiers_environment/prime_manifest.json",
    "prime_intellect/schemas/schema_manifest.json",
    "docs/prime_publication_handoff.json",
    "docs/prime_speedrun_handoff.json",
]
SOURCE_ANCHORS = [
    {
        "id": "agades-nvidia-accelerator",
        "source_catalog_required": True,
        "current_use": "current_public_accelerator_contract",
    },
    {
        "id": "nvidia-inception",
        "source_catalog_required": True,
        "current_use": "accelerator_strategy_anchor",
    },
]
SUBMISSION_PLAN = {
    "artifact_review_required": True,
    "program_application_manual_review_required": True,
    "command_templates": [],
    "contains_credentials": False,
    "external_submission_performed": False,
    "external_url_recorded": False,
    "first_publication_target": "manual_review_packet",
}
SAFETY = {
    "contains_private_traces": False,
    "publishes_private_candidates": False,
    "arbitrary_code_execution": False,
    "live_targeting": False,
    "security_claim": False,
    "claims_external_submission": False,
    "claims_gpu_results": False,
    "credentials_present_in_artifact": False,
}
REVIEW_REQUIRED_BEFORE_SUBMISSION = [
    "Confirm NVIDIA program, account, and target review channel.",
    "Run accelerator manifest, handoff, publication, and release gates.",
    "Review strategy text for CPU-only current workload boundaries.",
    "Confirm no GPU result or security claim is made before external use.",
    "Record external NVIDIA URLs only after reviewer approval.",
]
REQUIRED_RELEASE_GATES = [
    "uv run pytest tests/test_nvidia_publication_handoff.py -q",
    "uv run agades-pqc nvidia-publication-handoff --out "
    "docs/nvidia_publication_handoff.json",
    "uv run agades-pqc nvidia-publication-handoff-verify --handoff "
    "docs/nvidia_publication_handoff.json",
    "uv run agades-pqc nvidia-manifest-verify --manifest "
    "nvidia/accelerator_manifest.json",
    "uv run agades-pqc publication-manifest-verify --manifest "
    "docs/publication_manifest.json",
    "uv run agades-pqc ecosystem-smoke-verify --report "
    "reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
]


def build_nvidia_publication_handoff(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    accelerator_verification = verify_nvidia_accelerator_manifest(
        ACCELERATOR_MANIFEST_PATH,
        root=project_root,
    )
    summary = accelerator_verification["summary"]

    return {
        "schema_version": NVIDIA_PUBLICATION_HANDOFF_SCHEMA,
        "project": dict(PROJECT),
        "platform": {
            "ecosystem": "nvidia",
            "handoff_status": "strategy_ready_external_submission_blocked",
            "accelerator_manifest": ACCELERATOR_MANIFEST_PATH.as_posix(),
            "accelerator_strategy": ACCELERATOR_STRATEGY_PATH.as_posix(),
            "suggested_programs": [
                "nvidia_inception",
                "nvidia_accelerated_research_review",
            ],
            "review_channel": "manual_program_review_required",
        },
        "readiness": {
            "accelerator_manifest_accepted": accelerator_verification["accepted"],
            "all_current_workloads_cpu": summary["all_current_workloads_cpu"],
            "current_gpu_required_workload_count": summary[
                "current_gpu_required_workload_count"
            ],
            "current_workload_count": summary["current_workload_count"],
            "gpu_future_workload_count": summary[
                "reserved_future_gpu_required_workload_count"
            ],
            "public_run_bundles": summary["public_run_bundle_count"],
            "total_workload_count": summary["total_workload_count"],
            "requires_credentials": False,
            "credentials_checked_at_generation": False,
            "credentials_present_in_artifact": False,
            "external_submission_requires_review": True,
            "nvidia_submission_performed": False,
            "gpu_execution_performed": False,
        },
        "submission_plan": dict(SUBMISSION_PLAN),
        "source_anchors": list(SOURCE_ANCHORS),
        "family_support": summarize_family_support_matrix(
            build_family_support_matrix(root=project_root)
        ),
        "source_catalog_scope": summarize_source_catalog_scope(
            build_source_catalog()
        ),
        "local_artifacts": {
            "artifact_paths": list(LOCAL_ARTIFACT_PATHS),
            "artifact_sha256": _artifact_sha256(project_root, LOCAL_ARTIFACT_PATHS),
        },
        "safety": dict(SAFETY),
        "review_required_before_submission": list(REVIEW_REQUIRED_BEFORE_SUBMISSION),
        "release_gates": list(REQUIRED_RELEASE_GATES),
    }


def write_nvidia_publication_handoff(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    handoff = build_nvidia_publication_handoff(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(handoff, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return handoff


def verify_nvidia_publication_handoff(
    handoff_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    handoff = _read_handoff(handoff_path, project_root, failures)

    if handoff:
        expected = build_nvidia_publication_handoff(root=project_root)
        if handoff != expected:
            failures.append("NVIDIA publication handoff is not in sync.")

        _verify_project(handoff, failures)
        _verify_platform(handoff, failures)
        _verify_readiness(handoff, expected["readiness"], failures)
        _verify_submission_plan(handoff, failures)
        _verify_source_anchors(handoff, failures)
        _verify_family_support(handoff, expected["family_support"], failures)
        _verify_source_catalog_scope(handoff, failures)
        _verify_local_artifacts(project_root, handoff, failures)
        _verify_safety(handoff, failures)
        _verify_review_requirements(handoff, failures)
        _verify_release_gates(handoff, failures)

    return _verification_result(handoff_path, handoff, failures)


def _read_handoff(
    handoff_path: Path,
    root: Path,
    failures: list[str],
) -> dict[str, Any]:
    path = handoff_path if handoff_path.is_absolute() else root / handoff_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"NVIDIA publication handoff is missing: {handoff_path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"NVIDIA publication handoff is invalid JSON at line {exc.lineno}."
        )
        return {}

    if not isinstance(payload, dict):
        failures.append("NVIDIA publication handoff must be a JSON object.")
        return {}
    return payload


def _verify_project(handoff: dict[str, Any], failures: list[str]) -> None:
    if handoff.get("schema_version") != NVIDIA_PUBLICATION_HANDOFF_SCHEMA:
        failures.append(
            "NVIDIA publication handoff schema_version must be "
            f"{NVIDIA_PUBLICATION_HANDOFF_SCHEMA}."
        )
    if handoff.get("project") != PROJECT:
        failures.append("NVIDIA publication handoff project metadata drifted.")


def _verify_platform(handoff: dict[str, Any], failures: list[str]) -> None:
    platform = handoff.get("platform")
    if not isinstance(platform, dict):
        failures.append("NVIDIA publication handoff platform must be an object.")
        return
    expected = {
        "ecosystem": "nvidia",
        "handoff_status": "strategy_ready_external_submission_blocked",
        "accelerator_manifest": ACCELERATOR_MANIFEST_PATH.as_posix(),
        "accelerator_strategy": ACCELERATOR_STRATEGY_PATH.as_posix(),
        "suggested_programs": [
            "nvidia_inception",
            "nvidia_accelerated_research_review",
        ],
        "review_channel": "manual_program_review_required",
    }
    for key, expected_value in expected.items():
        if platform.get(key) != expected_value:
            failures.append(f"NVIDIA publication handoff platform.{key} drifted.")


def _verify_readiness(
    handoff: dict[str, Any],
    expected: dict[str, Any],
    failures: list[str],
) -> None:
    readiness = handoff.get("readiness")
    if not isinstance(readiness, dict):
        failures.append("NVIDIA publication handoff readiness must be an object.")
        return
    for key, expected_value in expected.items():
        if readiness.get(key) != expected_value:
            failures.append(f"NVIDIA handoff readiness.{key} drifted.")
    if readiness.get("accelerator_manifest_accepted") is not True:
        failures.append("NVIDIA handoff accelerator manifest is not accepted.")
    if readiness.get("all_current_workloads_cpu") is not True:
        failures.append("NVIDIA handoff must keep current workloads CPU-only.")
    if readiness.get("current_gpu_required_workload_count") != 0:
        failures.append("NVIDIA handoff current GPU-required count is nonzero.")
    if readiness.get("gpu_future_workload_count") != 1:
        failures.append("NVIDIA handoff must keep one reserved future GPU workload.")
    if readiness.get("requires_credentials") is not False:
        failures.append("NVIDIA handoff local generation must not require credentials.")
    if readiness.get("credentials_checked_at_generation") is not False:
        failures.append("NVIDIA handoff must not inspect credentials at generation.")
    if readiness.get("credentials_present_in_artifact") is not False:
        failures.append("NVIDIA handoff must not include credential evidence.")
    if readiness.get("external_submission_requires_review") is not True:
        failures.append("NVIDIA handoff lacks external submission review boundary.")
    if readiness.get("nvidia_submission_performed") is not False:
        failures.append("NVIDIA handoff must not claim external submission.")
    if readiness.get("gpu_execution_performed") is not False:
        failures.append("NVIDIA handoff must not claim GPU execution.")


def _verify_submission_plan(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    submission_plan = handoff.get("submission_plan")
    if submission_plan != SUBMISSION_PLAN:
        failures.append("NVIDIA handoff submission plan drifted.")
    if isinstance(submission_plan, dict):
        if submission_plan.get("contains_credentials") is not False:
            failures.append("NVIDIA handoff submission plan contains credentials.")
        if submission_plan.get("external_submission_performed") is not False:
            failures.append("NVIDIA handoff must not claim external submission.")


def _verify_source_anchors(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    if handoff.get("source_anchors") != SOURCE_ANCHORS:
        failures.append("NVIDIA handoff source anchors drifted.")
    source_catalog = build_source_catalog()
    source_by_id = {source["id"]: source for source in source_catalog["sources"]}
    for anchor in SOURCE_ANCHORS:
        source = source_by_id.get(anchor["id"])
        if source is None:
            failures.append(f"NVIDIA source catalog anchor is missing: {anchor['id']}.")
        elif source.get("current_use") != anchor["current_use"]:
            failures.append(
                f"NVIDIA source catalog anchor current_use drifted: {anchor['id']}."
            )


def _verify_family_support(
    handoff: dict[str, Any],
    expected: dict[str, Any],
    failures: list[str],
) -> None:
    family_support = handoff.get("family_support")
    if not isinstance(family_support, dict):
        failures.append("NVIDIA handoff family_support must be an object.")
        return
    if family_support != expected:
        failures.append("NVIDIA handoff family_support summary drifted.")
    if family_support.get("review_required_before_claims") is not True:
        failures.append(
            "NVIDIA handoff family_support.review_required_before_claims must be true."
        )


def _verify_source_catalog_scope(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    scope = handoff.get("source_catalog_scope")
    if not isinstance(scope, dict):
        failures.append("NVIDIA handoff source_catalog_scope must be an object.")
        return
    if scope.get("non_lattice_toy_operator_security_claims") != 0:
        failures.append(
            "NVIDIA handoff source catalog scope must not contain "
            "non-lattice toy security claims."
        )
    if scope.get("non_lattice_toy_evaluator_count") != scope.get("source_count"):
        failures.append("NVIDIA handoff source catalog scope must cover every source.")
    if scope.get("non_lattice_toy_operator_variant_count") != scope.get(
        "source_count"
    ):
        failures.append(
            "NVIDIA handoff source catalog operator scope must cover every source."
        )


def _verify_local_artifacts(
    root: Path,
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    local_artifacts = handoff.get("local_artifacts")
    if not isinstance(local_artifacts, dict):
        failures.append(
            "NVIDIA publication handoff local_artifacts must be an object."
        )
        return
    artifact_paths = local_artifacts.get("artifact_paths")
    if artifact_paths != LOCAL_ARTIFACT_PATHS:
        failures.append("NVIDIA handoff local artifact paths drifted.")
        artifact_paths = artifact_paths if isinstance(artifact_paths, list) else []
    artifact_sha256 = local_artifacts.get("artifact_sha256")
    if not isinstance(artifact_sha256, dict):
        failures.append("NVIDIA handoff artifact digest map must be an object.")
        artifact_sha256 = {}
    if set(artifact_sha256) != set(LOCAL_ARTIFACT_PATHS):
        failures.append("NVIDIA handoff artifact digest keys drifted.")
    for artifact_path in artifact_paths:
        if not isinstance(artifact_path, str):
            failures.append("NVIDIA handoff artifact path is invalid.")
            continue
        path = root / artifact_path
        if not path.is_file():
            failures.append(f"NVIDIA handoff artifact is missing: {artifact_path}.")
            continue
        expected_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if artifact_sha256.get(artifact_path) != expected_digest:
            failures.append(f"NVIDIA handoff artifact digest drifted: {artifact_path}.")


def _verify_safety(handoff: dict[str, Any], failures: list[str]) -> None:
    safety = handoff.get("safety")
    if not isinstance(safety, dict):
        failures.append("NVIDIA publication handoff safety must be an object.")
        return
    for key, expected_value in SAFETY.items():
        if safety.get(key) != expected_value:
            if key == "claims_external_submission":
                failures.append("NVIDIA handoff claims external submission.")
            elif key == "claims_gpu_results":
                failures.append("NVIDIA handoff claims GPU results.")
            elif key == "publishes_private_candidates":
                failures.append("NVIDIA handoff may publish private candidates.")
            elif key == "arbitrary_code_execution":
                failures.append("NVIDIA handoff advertises arbitrary execution.")
            elif key == "credentials_present_in_artifact":
                failures.append("NVIDIA handoff must not include credential evidence.")
            elif key == "security_claim":
                failures.append("NVIDIA handoff advertises a security claim.")
            else:
                failures.append(f"NVIDIA handoff safety.{key} drifted.")


def _verify_review_requirements(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    if (
        handoff.get("review_required_before_submission")
        != REVIEW_REQUIRED_BEFORE_SUBMISSION
    ):
        failures.append("NVIDIA handoff review checklist drifted.")


def _verify_release_gates(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    release_gates = handoff.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append("NVIDIA handoff release_gates must be a list.")
        return
    for required_gate in REQUIRED_RELEASE_GATES:
        if required_gate not in release_gates:
            failures.append(f"NVIDIA handoff release gate missing: {required_gate}")


def _verification_result(
    handoff_path: Path,
    handoff: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    readiness = handoff.get("readiness", {})
    if not isinstance(readiness, dict):
        readiness = {}
    local_artifacts = handoff.get("local_artifacts", {})
    if not isinstance(local_artifacts, dict):
        local_artifacts = {}
    source_catalog_scope = handoff.get("source_catalog_scope", {})
    if not isinstance(source_catalog_scope, dict):
        source_catalog_scope = {}
    family_support = handoff.get("family_support", {})
    if not isinstance(family_support, dict):
        family_support = {}
    artifact_paths = local_artifacts.get("artifact_paths", [])
    if not isinstance(artifact_paths, list):
        artifact_paths = []
    return {
        "schema_version": NVIDIA_PUBLICATION_HANDOFF_VERIFICATION_SCHEMA,
        "handoff_path": handoff_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "artifact_count": len(artifact_paths),
            "current_gpu_required_workload_count": readiness.get(
                "current_gpu_required_workload_count"
            ),
            "current_workload_count": readiness.get("current_workload_count"),
            "external_submission_requires_review": readiness.get(
                "external_submission_requires_review"
            ),
            "failure_count": len(failures),
            "gpu_execution_performed": readiness.get("gpu_execution_performed"),
            "gpu_future_workload_count": readiness.get("gpu_future_workload_count"),
            "nvidia_submission_performed": readiness.get(
                "nvidia_submission_performed"
            ),
            "family_count": family_support.get("family_count"),
            "family_support_review_required_before_claims": family_support.get(
                "review_required_before_claims"
            ),
            "implemented_families": family_support.get("implemented"),
            "non_lattice_toy_evaluator_count": source_catalog_scope.get(
                "non_lattice_toy_evaluator_count"
            ),
            "non_lattice_toy_operator_security_claims": (
                source_catalog_scope.get("non_lattice_toy_operator_security_claims")
            ),
            "non_lattice_toy_operator_variant_count": source_catalog_scope.get(
                "non_lattice_toy_operator_variant_count"
            ),
            "public_run_bundles": readiness.get("public_run_bundles"),
            "requires_credentials": readiness.get("requires_credentials"),
            "total_workload_count": readiness.get("total_workload_count"),
        },
        "failures": failures,
    }


def _artifact_sha256(root: Path, artifact_paths: list[str]) -> dict[str, str]:
    return {
        artifact_path: hashlib.sha256((root / artifact_path).read_bytes()).hexdigest()
        for artifact_path in artifact_paths
    }
