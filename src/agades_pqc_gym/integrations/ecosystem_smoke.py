from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.external_publication_review_packet import (
    verify_external_publication_review_packet,
)
from agades_pqc_gym.integrations.huggingface_collection_manifest import (
    verify_huggingface_collection_manifest,
)
from agades_pqc_gym.integrations.huggingface_dataset import (
    verify_huggingface_dataset_bundle,
)
from agades_pqc_gym.integrations.huggingface_space_manifest import (
    verify_huggingface_space_manifest,
)
from agades_pqc_gym.integrations.nvidia_accelerator import (
    verify_nvidia_accelerator_manifest,
)
from agades_pqc_gym.integrations.prime_environment_manifest import (
    verify_prime_environment_manifest,
)
from agades_pqc_gym.integrations.prime_verifier_schemas import (
    verify_prime_verifier_schemas,
)
from agades_pqc_gym.integrations.publication_manifest import (
    verify_publication_manifest,
)
from agades_pqc_gym.integrations.publication_preflight import (
    verify_publication_preflight,
)

ECOSYSTEM_SMOKE_SCHEMA = "agades.pqc.ecosystem_smoke.v1"
ECOSYSTEM_SMOKE_VERIFICATION_SCHEMA = (
    "agades.pqc.ecosystem_smoke_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
PROJECT = {
    "name": "Agades PQC Gym",
    "package": "agades_pqc_gym",
    "cli": "agades-pqc",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
}
SAFETY = {
    "arbitrary_code_execution": False,
    "external_publication_performed": False,
    "external_publication_requires_review": True,
    "live_targeting": False,
    "publishes_private_candidates": False,
    "security_claim": False,
}
ADVISORY_VERIFICATIONS = {"publication_preflight"}
RUNBOOK_ARCHITECTURE_SUMMARY_KEYS = (
    "runbook_core_symbol_import_count",
    "runbook_family_plugin_manifest_digests_match",
    "runbook_family_plugin_module_count",
    "runbook_family_plugin_module_digest_count",
    "runbook_family_plugin_module_import_count",
    "runbook_family_registry_family_count_matches_plugin_manifest",
    "runbook_family_registry_plugin_count_matches_plugin_manifest",
    "runbook_family_registry_plugin_manifest_module_digest_count",
    "runbook_family_registry_plugin_manifest_synced",
    "runbook_family_registry_runtime_adapter_entries_match_plugin_manifest",
)


def build_ecosystem_smoke_report(*, root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    verifications = _build_verifications(project_root)
    surfaces = {
        "hugging_face": _hugging_face_surface(verifications),
        "prime_intellect": _prime_surface(verifications),
        "nvidia": _nvidia_surface(verifications),
        "publication": _publication_surface(verifications),
    }
    failures = _failures(verifications, surfaces)

    return {
        "schema_version": ECOSYSTEM_SMOKE_SCHEMA,
        "project": dict(PROJECT),
        "accepted": not failures,
        "summary": _summary(surfaces, failures),
        "surfaces": surfaces,
        "safety": dict(SAFETY),
        "failures": failures,
    }


def write_ecosystem_smoke_report(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    report = build_ecosystem_smoke_report(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_ecosystem_smoke_report(
    report: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    expected = build_ecosystem_smoke_report(root=project_root)
    report_path = _resolve_path(report, root=project_root)
    failures: list[str] = []
    checked_in: dict[str, Any] = {}
    checked_in_synced = False

    if not report_path.is_file():
        failures.append("Ecosystem smoke report is not checked in.")
    else:
        try:
            loaded = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"Ecosystem smoke report is invalid JSON: {exc}")
        else:
            if isinstance(loaded, dict):
                checked_in = loaded
                checked_in_synced = checked_in == expected
            else:
                failures.append("Ecosystem smoke report must be a JSON object.")

    if checked_in and checked_in.get("accepted") is not True:
        failures.append("Ecosystem smoke report is not accepted.")
    if checked_in and not checked_in_synced:
        failures.append("Ecosystem smoke report is not in sync.")
    if expected.get("accepted") is not True:
        failures.append("Generated ecosystem smoke report is not accepted.")
        failures.extend(str(failure) for failure in expected.get("failures", []))

    checked_in_summary = _summary_dict(checked_in)
    verification_summary = {
        "checked_in_report_accepted": checked_in.get("accepted") is True,
        "checked_in_report_synced": checked_in_synced,
        "expected_report_accepted": expected.get("accepted") is True,
        "reviewer_summary_synced": checked_in_summary.get(
            "reviewer_summary_synced"
        ),
        **_runbook_architecture_summary(checked_in_summary),
    }
    verification_summary["failure_count"] = len(failures)
    return {
        "schema_version": ECOSYSTEM_SMOKE_VERIFICATION_SCHEMA,
        "report_path": _display_path(report_path, root=project_root),
        "accepted": not failures,
        "summary": verification_summary,
        "failures": failures,
    }


def _build_verifications(root: Path) -> dict[str, dict[str, Any]]:
    return {
        "hf_dataset": verify_huggingface_dataset_bundle(
            Path("hf/dataset"),
            root=root,
        ),
        "hf_space": verify_huggingface_space_manifest(
            Path("hf/space_manifest.json"),
            root=root,
        ),
        "hf_collection": verify_huggingface_collection_manifest(
            Path("hf/collection_manifest.json"),
            root=root,
        ),
        "prime_environment": verify_prime_environment_manifest(
            Path("prime_intellect/verifiers_environment/prime_manifest.json"),
            root=root,
        ),
        "prime_schemas": verify_prime_verifier_schemas(
            Path("prime_intellect/schemas"),
            root=root,
        ),
        "nvidia": verify_nvidia_accelerator_manifest(
            Path("nvidia/accelerator_manifest.json"),
            root=root,
        ),
        "publication_manifest": verify_publication_manifest(
            Path("docs/publication_manifest.json"),
            root=root,
        ),
        "publication_preflight": verify_publication_preflight(
            Path("public/publication_preflight.json"),
            root=root,
        ),
        "external_publication_review_packet": (
            verify_external_publication_review_packet(
                Path("docs/external_publication_review_packet.json"),
                root=root,
            )
        ),
    }


def _hugging_face_surface(
    verifications: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    dataset = _summary_dict(verifications["hf_dataset"])
    space = _summary_dict(verifications["hf_space"])
    collection = _summary_dict(verifications["hf_collection"])
    return {
        "accepted": all(
            _is_accepted(verifications[key])
            for key in ("hf_dataset", "hf_space", "hf_collection")
        ),
        "dataset": {
            "accepted": _is_accepted(verifications["hf_dataset"]),
            "attack_plan_count": dataset.get("attack_plan_count"),
            "public_run_bundle_count": dataset.get("public_run_bundle_count"),
            "task_metadata_rows": dataset.get("task_metadata_rows"),
            "valid_attack_plan_count": dataset.get("valid_attack_plan_count"),
        },
        "space": {
            "accepted": _is_accepted(verifications["hf_space"]),
            "example_count": space.get("example_count"),
            "public_push_requires_review": space.get(
                "public_push_requires_review"
            ),
            "uses_shared_verifier": space.get("uses_shared_verifier"),
        },
        "collection": {
            "accepted": _is_accepted(verifications["hf_collection"]),
            "entry_count": collection.get("entry_count"),
            "external_publication_requires_review": collection.get(
                "external_publication_requires_review"
            ),
            "family_support": _platform_family_support(collection),
            "public_private_boundary": _platform_public_private_boundary(
                collection
            ),
            "public_push_requires_review": collection.get(
                "public_push_requires_review"
            ),
        },
    }


def _prime_surface(verifications: dict[str, dict[str, Any]]) -> dict[str, Any]:
    environment = _summary_dict(verifications["prime_environment"])
    schemas = _summary_dict(verifications["prime_schemas"])
    families = environment.get("families")
    family_count = len(families) if isinstance(families, list) else None
    return {
        "accepted": all(
            _is_accepted(verifications[key])
            for key in ("prime_environment", "prime_schemas")
        ),
        "environment": {
            "accepted": _is_accepted(verifications["prime_environment"]),
            "family_support": _platform_family_support(environment),
            "family_count": family_count,
            "mirrors_public_examples": environment.get("mirrors_public_examples"),
            "public_private_boundary": _platform_public_private_boundary(
                environment
            ),
            "public_push_requires_review": environment.get(
                "public_push_requires_review"
            ),
            "task_count": environment.get("task_count"),
        },
        "schemas": {
            "accepted": _is_accepted(verifications["prime_schemas"]),
            "release_gate_count": schemas.get("release_gate_count"),
            "schema_files": schemas.get("schema_files"),
            "task_metadata_schema_version": schemas.get(
                "task_metadata_schema_version"
            ),
        },
    }


def _nvidia_surface(verifications: dict[str, dict[str, Any]]) -> dict[str, Any]:
    summary = _summary_dict(verifications["nvidia"])
    return {
        "accepted": _is_accepted(verifications["nvidia"]),
        "all_current_workloads_cpu": summary.get("all_current_workloads_cpu"),
        "current_gpu_required_workload_count": summary.get(
            "current_gpu_required_workload_count"
        ),
        "current_workload_count": summary.get("current_workload_count"),
        "family_support": _platform_family_support(summary),
        "public_private_boundary": _platform_public_private_boundary(summary),
        "public_run_bundle_count": summary.get("public_run_bundle_count"),
        "reserved_future_gpu_required_workload_count": summary.get(
            "reserved_future_gpu_required_workload_count"
        ),
        "total_workload_count": summary.get("total_workload_count"),
    }


def _publication_surface(
    verifications: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    manifest = _summary_dict(verifications["publication_manifest"])
    preflight = _summary_dict(verifications["publication_preflight"])
    packet = _summary_dict(verifications["external_publication_review_packet"])
    return {
        "accepted": all(
            _is_accepted(verifications[key])
            for key in (
                "publication_manifest",
                "external_publication_review_packet",
            )
        ),
        "manifest": {
            "accepted": _is_accepted(verifications["publication_manifest"]),
            "credentialed_surfaces": manifest.get("credentialed_surfaces"),
            "public_run_bundles": manifest.get("public_run_bundles"),
            "review_required_surfaces": manifest.get("review_required_surfaces"),
            "surfaces": manifest.get("surfaces"),
        },
        "preflight": {
            "accepted": _is_accepted(verifications["publication_preflight"]),
            "blockers": preflight.get("blockers"),
            "local_artifacts_ready": preflight.get("local_artifacts_ready"),
            "ready_for_external_publication": preflight.get(
                "ready_for_external_publication"
            ),
            "warnings": preflight.get("warnings"),
        },
        "external_review_packet": {
            "accepted": _is_accepted(
                verifications["external_publication_review_packet"]
            ),
            "blockers": packet.get("blockers"),
            "credentialed_surface_count": packet.get("credentialed_surface_count"),
            "families_with_future_reviewed_adapters": packet.get(
                "families_with_future_reviewed_adapters"
            ),
            "family_count": packet.get("family_count"),
            "future_reviewed_adapter_sources_by_family": packet.get(
                "future_reviewed_adapter_sources_by_family"
            ),
            "ready_for_external_publication": packet.get(
                "ready_for_external_publication"
            ),
            "review_required_before_claims": packet.get(
                "review_required_before_claims"
            ),
            "review_required_surface_count": packet.get(
                "review_required_surface_count"
            ),
            "reviewer_summary_synced": packet.get("reviewer_summary_synced"),
            "surface_count": packet.get("surface_count"),
            "warnings": packet.get("warnings"),
            **_runbook_architecture_summary(packet),
        },
    }


def _summary(
    surfaces: dict[str, dict[str, Any]],
    failures: list[str],
) -> dict[str, Any]:
    hugging_face = surfaces["hugging_face"]
    prime = surfaces["prime_intellect"]
    nvidia = surfaces["nvidia"]
    publication = surfaces["publication"]
    external_packet = publication["external_review_packet"]
    preflight = publication["preflight"]
    platform_family_supports = _platform_family_supports(surfaces)
    platform_public_private_boundaries = _platform_public_private_boundaries(
        surfaces
    )
    return {
        "credentialed_surface_count": external_packet[
            "credentialed_surface_count"
        ],
        "external_publication_ready": preflight[
            "ready_for_external_publication"
        ],
        "families_with_future_reviewed_adapters": external_packet[
            "families_with_future_reviewed_adapters"
        ],
        "failure_count": len(failures),
        "family_count": external_packet["family_count"],
        "future_reviewed_adapter_sources_by_family": external_packet[
            "future_reviewed_adapter_sources_by_family"
        ],
        "hf_space_examples": hugging_face["space"]["example_count"],
        "hf_valid_attack_plan_rows": hugging_face["dataset"][
            "valid_attack_plan_count"
        ],
        "local_artifacts_ready": preflight["local_artifacts_ready"],
        "nvidia_current_gpu_required_workloads": nvidia[
            "current_gpu_required_workload_count"
        ],
        "nvidia_current_workloads": nvidia["current_workload_count"],
        "platform_family_support_family_counts_match": (
            _platform_family_support_family_counts_match(
                platform_family_supports,
                external_packet["family_count"],
            )
        ),
        "platform_family_support_surfaces": len(platform_family_supports),
        "platform_public_private_boundary_surfaces": len(
            platform_public_private_boundaries
        ),
        "platform_report_redaction_records_match": (
            _platform_report_redaction_records_match(
                platform_public_private_boundaries
            )
        ),
        "platforms_with_family_claim_review_gate": sum(
            1
            for support in platform_family_supports
            if support.get("review_required_before_claims") is True
        ),
        "platforms_with_raw_mapping_redaction_gate": sum(
            1
            for boundary in platform_public_private_boundaries
            if boundary.get("raw_mapping_redaction_covered") is True
        ),
        "platforms_with_typed_trace_redaction_gate": sum(
            1
            for boundary in platform_public_private_boundaries
            if boundary.get("typed_trace_redaction_covered") is True
        ),
        "prime_tasks": prime["environment"]["task_count"],
        "public_run_bundles": publication["manifest"]["public_run_bundles"],
        "review_required_surface_count": external_packet[
            "review_required_surface_count"
        ],
        "reviewer_summary_synced": external_packet["reviewer_summary_synced"],
        **_runbook_architecture_summary(external_packet),
    }


def _failures(
    verifications: dict[str, dict[str, Any]],
    surfaces: dict[str, dict[str, Any]],
) -> list[str]:
    failures: list[str] = []
    for name, verification in sorted(verifications.items()):
        if name in ADVISORY_VERIFICATIONS:
            continue
        if not _is_accepted(verification):
            detail = "; ".join(str(item) for item in verification.get("failures", []))
            failures.append(f"{name} verification failed: {detail}")

    publication = surfaces["publication"]
    nvidia = surfaces["nvidia"]
    if publication["preflight"]["ready_for_external_publication"] is not False:
        failures.append(
            "Ecosystem smoke must remain blocked from external publication."
        )
    if nvidia["current_gpu_required_workload_count"] != 0:
        failures.append("NVIDIA smoke must not require current GPU workloads.")
    platform_family_supports = _platform_family_supports(surfaces)
    if len(platform_family_supports) != 3:
        failures.append("Ecosystem smoke must expose three platform family supports.")
    if any(
        support.get("review_required_before_claims") is not True
        for support in platform_family_supports
    ):
        failures.append(
            "Ecosystem smoke platform family-support gates must require review "
            "before claims."
        )
    if not _platform_family_support_family_counts_match(
        platform_family_supports,
        surfaces["publication"]["external_review_packet"]["family_count"],
    ):
        failures.append(
            "Ecosystem smoke platform family counts must match the review packet."
        )
    platform_public_private_boundaries = _platform_public_private_boundaries(
        surfaces
    )
    if len(platform_public_private_boundaries) != 3:
        failures.append(
            "Ecosystem smoke must expose three platform public/private boundaries."
        )
    if any(
        boundary.get("typed_trace_redaction_covered") is not True
        for boundary in platform_public_private_boundaries
    ):
        failures.append(
            "Ecosystem smoke platform typed TraceRecord redaction gates must be "
            "covered."
        )
    if any(
        boundary.get("raw_mapping_redaction_covered") is not True
        for boundary in platform_public_private_boundaries
    ):
        failures.append(
            "Ecosystem smoke platform raw trace mapping redaction gates must be "
            "covered."
        )
    if not _platform_report_redaction_records_match(
        platform_public_private_boundaries
    ):
        failures.append(
            "Ecosystem smoke platform report redaction record counts must match."
        )
    external_packet = publication["external_review_packet"]
    if external_packet.get("reviewer_summary_synced") is not True:
        failures.append(
            "Ecosystem smoke external review packet summary must remain "
            "synchronized."
        )
    if external_packet.get("runbook_family_plugin_manifest_digests_match") is not True:
        failures.append(
            "Ecosystem smoke runbook architecture evidence must keep plugin "
            "digests synchronized."
        )
    if (
        external_packet.get("runbook_family_registry_plugin_manifest_synced")
        is not True
    ):
        failures.append(
            "Ecosystem smoke runbook architecture evidence must keep the family "
            "registry synchronized with the plugin manifest."
        )
    if (
        external_packet.get(
            "runbook_family_registry_runtime_adapter_entries_match_plugin_manifest"
        )
        is not True
    ):
        failures.append(
            "Ecosystem smoke runbook architecture evidence must keep registry "
            "runtime adapters synchronized."
        )
    return failures


def _runbook_architecture_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        key: summary.get(key)
        for key in RUNBOOK_ARCHITECTURE_SUMMARY_KEYS
    }


def _platform_family_support(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "families_with_future_reviewed_adapters": summary.get(
            "families_with_future_reviewed_adapters"
        ),
        "family_count": summary.get("family_count"),
        "review_required_before_claims": summary.get(
            "review_required_before_claims"
        ),
    }


def _platform_public_private_boundary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "raw_mapping_redaction_covered": summary.get(
            "raw_mapping_redaction_covered"
        ),
        "report_redaction_records": summary.get("report_redaction_records"),
        "typed_trace_redaction_covered": summary.get(
            "typed_trace_redaction_covered"
        ),
    }


def _platform_family_supports(
    surfaces: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    supports = [
        surfaces["hugging_face"]["collection"].get("family_support"),
        surfaces["prime_intellect"]["environment"].get("family_support"),
        surfaces["nvidia"].get("family_support"),
    ]
    return [support for support in supports if isinstance(support, dict)]


def _platform_public_private_boundaries(
    surfaces: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    boundaries = [
        surfaces["hugging_face"]["collection"].get("public_private_boundary"),
        surfaces["prime_intellect"]["environment"].get(
            "public_private_boundary"
        ),
        surfaces["nvidia"].get("public_private_boundary"),
    ]
    return [boundary for boundary in boundaries if isinstance(boundary, dict)]


def _platform_family_support_family_counts_match(
    platform_family_supports: list[dict[str, Any]],
    expected_family_count: Any,
) -> bool:
    if len(platform_family_supports) != 3:
        return False
    return all(
        support.get("family_count") == expected_family_count
        for support in platform_family_supports
    )


def _platform_report_redaction_records_match(
    platform_public_private_boundaries: list[dict[str, Any]],
) -> bool:
    if len(platform_public_private_boundaries) != 3:
        return False
    return all(
        boundary.get("report_redaction_records") == 2
        for boundary in platform_public_private_boundaries
    )


def _summary_dict(verification: dict[str, Any]) -> dict[str, Any]:
    summary = verification.get("summary", {})
    return summary if isinstance(summary, dict) else {}


def _is_accepted(verification: dict[str, Any]) -> bool:
    return verification.get("accepted") is True


def _resolve_path(path: Path, *, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _display_path(path: Path, *, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
