from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.family_support import (
    build_family_readiness_matrix,
    summarize_family_readiness_matrix,
)
from agades_pqc_gym.integrations.publication_manifest import (
    verify_publication_manifest,
)
from agades_pqc_gym.integrations.release_status import (
    runbook_architecture_evidence_failures,
    summarize_release_status_family_support,
    summarize_release_status_public_private_boundary,
    summarize_release_status_runbook_architecture,
    summarize_release_status_source_catalog_scope,
)

PUBLICATION_PREFLIGHT_SCHEMA = "agades.pqc.publication_preflight.v1"
PUBLICATION_PREFLIGHT_VERIFICATION_SCHEMA = (
    "agades.pqc.publication_preflight_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FAMILY_SUPPORT_MATRIX = Path("docs/family_support_matrix.json")
DEFAULT_PUBLICATION_MANIFEST = Path("docs/publication_manifest.json")
DEFAULT_RELEASE_AUDIT = Path("public/release_audit.json")
DEFAULT_RELEASE_STATUS = Path("docs/release_status.json")
PROJECT = {
    "name": "Agades PQC Gym",
    "package": "agades_pqc_gym",
    "cli": "agades-pqc",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
}
SAFETY = {
    "arbitrary_code_execution": False,
    "contains_private_traces": False,
    "live_targeting": False,
    "publishes_private_candidates": False,
    "security_claim": False,
    "external_publication_requires_review": True,
}
REQUIRED_PUBLICATION_PLATFORMS = {
    "github",
    "hugging_face",
    "nvidia",
    "prime_intellect",
}


def build_publication_preflight(
    *,
    family_support_matrix_path: Path = DEFAULT_FAMILY_SUPPORT_MATRIX,
    publication_manifest_path: Path = DEFAULT_PUBLICATION_MANIFEST,
    release_audit_path: Path = DEFAULT_RELEASE_AUDIT,
    release_status_path: Path = DEFAULT_RELEASE_STATUS,
    external_release_review_approved: bool = False,
    credentials_reviewed: bool = False,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    family_support_matrix = _read_json(
        _resolve(project_root, family_support_matrix_path)
    )
    publication_manifest = _read_json(_resolve(project_root, publication_manifest_path))
    release_audit = _read_json(_resolve(project_root, release_audit_path))
    release_status = _read_json(_resolve(project_root, release_status_path))
    publication_verification = verify_publication_manifest(
        publication_manifest_path,
        root=project_root,
    )

    audit_summary = _audit_summary(release_audit)
    publication_summary = _publication_summary(publication_verification)
    credentialed_surfaces = publication_summary["credentialed_surfaces"]
    credential_review_queue = build_credential_review_queue(
        publication_manifest,
        credentialed_surface_ids=credentialed_surfaces,
    )
    surface_notes = _surface_notes(publication_manifest)
    local_artifacts_ready = (
        publication_verification["accepted"] is True
        and release_audit.get("accepted") is True
        and audit_summary["failed"] == 0
        and release_status.get("audit", {}).get("accepted") is True
    )

    blockers: list[dict[str, str]] = []
    if not local_artifacts_ready:
        blockers.append(
            {
                "id": "local_artifacts_not_ready",
                "detail": (
                    "Local publication artifacts must pass publication manifest, "
                    "release audit, and release status verification before any "
                    "external publication."
                ),
            }
        )
    if not external_release_review_approved:
        blockers.append(
            {
                "id": "external_release_review_not_approved",
                "detail": (
                    "External publication to Hugging Face, Prime Intellect, or "
                    "public NVIDIA-facing channels requires explicit release review."
                ),
            }
        )
    if credentialed_surfaces and not credentials_reviewed:
        blockers.append(
            {
                "id": "credential_review_not_approved",
                "detail": (
                    "Credentialed surfaces require token/account review before "
                    f"publication: {', '.join(credentialed_surfaces)}."
                ),
            }
        )

    warnings = _release_warning_records(release_audit)

    return {
        "schema_version": PUBLICATION_PREFLIGHT_SCHEMA,
        "project": PROJECT,
        "inputs": {
            "family_support_matrix": family_support_matrix_path.as_posix(),
            "publication_manifest": publication_manifest_path.as_posix(),
            "release_audit": release_audit_path.as_posix(),
            "release_status": release_status_path.as_posix(),
        },
        "local_artifacts_ready": local_artifacts_ready,
        "ready_for_external_publication": local_artifacts_ready and not blockers,
        "review_state": {
            "credentials_reviewed": credentials_reviewed,
            "external_release_review_approved": external_release_review_approved,
        },
        "publication": {
            "surfaces": publication_summary["surfaces"],
            "review_required_surfaces": publication_summary[
                "review_required_surfaces"
            ],
            "credentialed_surfaces": credentialed_surfaces,
            "public_run_bundles": publication_summary["public_run_bundles"],
        },
        "credential_review_queue": credential_review_queue,
        "family_readiness_matrix": build_family_readiness_matrix(
            family_support_matrix
        ),
        "platform_review_matrix": build_platform_review_matrix_from_surface_records(
            surface_notes
        ),
        "family_support": summarize_release_status_family_support(release_status),
        "source_catalog_scope": summarize_release_status_source_catalog_scope(
            release_status
        ),
        "public_private_boundary": (
            summarize_release_status_public_private_boundary(release_status)
        ),
        "runbook_architecture": summarize_release_status_runbook_architecture(
            release_status
        ),
        "external_review": _external_review_from_release_status(release_status),
        "audit": audit_summary,
        "blockers": blockers,
        "warnings": warnings,
        "safety": SAFETY,
        "next_steps": _next_steps(blockers),
        "release_gates": [
            "uv run agades-pqc publication-preflight --out "
            "public/publication_preflight.json",
            "uv run agades-pqc publication-preflight-verify --preflight "
            "public/publication_preflight.json",
            "uv run agades-pqc ecosystem-smoke-verify --report "
            "reports/ecosystem_smoke.json",
        ],
        "surface_notes": surface_notes,
    }


def write_publication_preflight(
    out: Path,
    *,
    family_support_matrix_path: Path = DEFAULT_FAMILY_SUPPORT_MATRIX,
    publication_manifest_path: Path = DEFAULT_PUBLICATION_MANIFEST,
    release_audit_path: Path = DEFAULT_RELEASE_AUDIT,
    release_status_path: Path = DEFAULT_RELEASE_STATUS,
    external_release_review_approved: bool = False,
    credentials_reviewed: bool = False,
    root: Path | None = None,
) -> dict[str, Any]:
    preflight = build_publication_preflight(
        family_support_matrix_path=family_support_matrix_path,
        publication_manifest_path=publication_manifest_path,
        release_audit_path=release_audit_path,
        release_status_path=release_status_path,
        external_release_review_approved=external_release_review_approved,
        credentials_reviewed=credentials_reviewed,
        root=root,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(preflight, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return preflight


def verify_publication_preflight(
    preflight_path: Path,
    *,
    family_support_matrix_path: Path = DEFAULT_FAMILY_SUPPORT_MATRIX,
    publication_manifest_path: Path = DEFAULT_PUBLICATION_MANIFEST,
    release_audit_path: Path = DEFAULT_RELEASE_AUDIT,
    release_status_path: Path = DEFAULT_RELEASE_STATUS,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    resolved_path = _resolve(project_root, preflight_path)
    preflight = _read_preflight(resolved_path, failures)
    family_support_matrix = _read_json(
        _resolve(project_root, family_support_matrix_path)
    )

    if preflight:
        release_audit = _read_json(_resolve(project_root, release_audit_path))
        expected = build_publication_preflight(
            family_support_matrix_path=family_support_matrix_path,
            publication_manifest_path=publication_manifest_path,
            release_audit_path=release_audit_path,
            release_status_path=release_status_path,
            root=project_root,
        )
        if preflight != expected:
            failures.append("Publication preflight is not in sync.")
        _verify_conservative_default(
            preflight,
            family_support_matrix,
            _release_warning_records(release_audit),
            failures,
        )

    family_support = _dict_or_empty(preflight.get("family_support"))
    platform_support = _dict_or_empty(family_support.get("platform_support"))
    public_private_boundary = _dict_or_empty(
        preflight.get("public_private_boundary")
    )
    runbook_architecture = _dict_or_empty(preflight.get("runbook_architecture"))
    source_catalog_scope = _dict_or_empty(preflight.get("source_catalog_scope"))
    external_review = _dict_or_empty(preflight.get("external_review"))
    redaction = _dict_or_empty(
        public_private_boundary.get("report_generator_redaction")
    )
    credential_review_queue = _list_or_empty(
        preflight.get("credential_review_queue")
    )
    credentialed_surfaces = _list_or_empty(
        _dict_or_empty(preflight.get("publication")).get("credentialed_surfaces")
    )
    family_readiness_summary = summarize_family_readiness_matrix(
        _dict_or_empty(preflight.get("family_readiness_matrix"))
    )
    platform_review_summary = summarize_platform_review_matrix(
        _dict_or_empty(preflight.get("platform_review_matrix"))
    )
    warnings = _list_or_empty(preflight.get("warnings"))
    summary = {
        "blockers": len(preflight.get("blockers", [])),
        "credential_material_included": _credential_material_included(
            credential_review_queue
        ),
        "credential_review_queue_complete": _credential_review_queue_complete(
            credential_review_queue,
            credentialed_surfaces,
        ),
        "credential_review_queue_items": len(credential_review_queue),
        "failure_count": len(failures),
        "family_count": family_support.get("family_count"),
        "family_readiness_family_count": family_readiness_summary["family_count"],
        "family_readiness_lattice_estimator_families": len(
            family_readiness_summary["lattice_estimator_families"]
        ),
        "family_readiness_non_lattice_lattice_estimator_families": len(
            family_readiness_summary["non_lattice_lattice_estimator_families"]
        ),
        "family_readiness_review_required_families": family_readiness_summary[
            "review_required_families"
        ],
        "family_readiness_schema_only_default_estimators": len(
            family_readiness_summary["schema_only_default_estimator_families"]
        ),
        "local_artifacts_ready": preflight.get("local_artifacts_ready"),
        "runbook_core_symbol_import_count": runbook_architecture.get(
            "core_symbol_import_count"
        ),
        "runbook_family_plugin_manifest_digests_match": (
            runbook_architecture.get("family_plugin_manifest_digests_match")
        ),
        "runbook_family_plugin_module_count": runbook_architecture.get(
            "family_plugin_module_count"
        ),
        "runbook_family_plugin_module_digest_count": runbook_architecture.get(
            "family_plugin_module_digest_count"
        ),
        "runbook_family_plugin_module_import_count": runbook_architecture.get(
            "family_plugin_module_import_count"
        ),
        "runbook_family_registry_family_count_matches_plugin_manifest": (
            runbook_architecture.get(
                "family_registry_family_count_matches_plugin_manifest"
            )
        ),
        "runbook_family_registry_plugin_count_matches_plugin_manifest": (
            runbook_architecture.get(
                "family_registry_plugin_count_matches_plugin_manifest"
            )
        ),
        "runbook_family_registry_plugin_manifest_module_digest_count": (
            runbook_architecture.get(
                "family_registry_plugin_manifest_module_digest_count"
            )
        ),
        "runbook_family_registry_plugin_manifest_synced": (
            runbook_architecture.get("family_registry_plugin_manifest_synced")
        ),
        "runbook_family_registry_runtime_adapter_entries_match_plugin_manifest": (
            runbook_architecture.get(
                "family_registry_runtime_adapter_entries_match_plugin_manifest"
            )
        ),
        "platform_review_matrix_credentialed_surfaces": (
            platform_review_summary["credentialed_surfaces"]
        ),
        "platform_review_matrix_review_required_surfaces": (
            platform_review_summary["review_required_surfaces"]
        ),
        "platform_review_matrix_surfaces": platform_review_summary["surfaces"],
        "platform_family_support_family_counts_match": platform_support.get(
            "family_counts_match"
        ),
        "platform_family_support_surfaces": platform_support.get("surface_count"),
        "platform_source_catalog_scope_counts_match": source_catalog_scope.get(
            "platform_source_catalog_scope_counts_match"
        ),
        "platform_source_catalog_scope_security_claims": source_catalog_scope.get(
            "platform_source_catalog_scope_security_claims"
        ),
        "platform_source_catalog_scope_surfaces": source_catalog_scope.get(
            "platform_source_catalog_scope_surfaces"
        ),
        "platforms_with_family_claim_review_gate": len(
            _list_or_empty(platform_support.get("platforms_with_claim_review_gate"))
        ),
        "non_lattice_toy_evaluator_count": source_catalog_scope.get(
            "non_lattice_toy_evaluator_count"
        ),
        "non_lattice_toy_operator_security_claims": (
            source_catalog_scope.get("non_lattice_toy_operator_security_claims")
        ),
        "non_lattice_toy_operator_variant_count": source_catalog_scope.get(
            "non_lattice_toy_operator_variant_count"
        ),
        "raw_mapping_redaction_covered": redaction.get(
            "raw_mapping_redaction_covered"
        ),
        "ready_for_external_publication": preflight.get(
            "ready_for_external_publication"
        ),
        "report_redaction_records": redaction.get("redacted_records"),
        "reviewer_summary_synced": external_review.get("reviewer_summary_synced"),
        "review_required_before_claims": family_support.get(
            "review_required_before_claims"
        ),
        "typed_trace_redaction_covered": redaction.get(
            "typed_trace_redaction_covered"
        ),
        "warnings": len(warnings),
        "warning_evidence_items": _warning_evidence_items(warnings),
    }
    return {
        "schema_version": PUBLICATION_PREFLIGHT_VERIFICATION_SCHEMA,
        "preflight_path": preflight_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _publication_summary(verification: dict[str, Any]) -> dict[str, Any]:
    summary = verification["summary"]
    credentialed_surfaces = sorted(summary.get("credentialed_surfaces", []))
    return {
        "credentialed_surfaces": credentialed_surfaces,
        "public_run_bundles": summary.get("public_run_bundles", 0),
        "review_required_surfaces": summary.get("review_required_surfaces", 0),
        "surfaces": summary.get("surfaces", 0),
    }


def _external_review_from_release_status(
    release_status: dict[str, Any],
) -> dict[str, Any]:
    external_review = _dict_or_empty(release_status.get("external_review"))
    return {
        "blockers": external_review.get("blockers"),
        "credential_material_included": external_review.get(
            "credential_material_included"
        ),
        "credential_review_queue_complete": external_review.get(
            "credential_review_queue_complete"
        ),
        "credential_review_queue_items": external_review.get(
            "credential_review_queue_items"
        ),
        "credentialed_surface_count": external_review.get(
            "credentialed_surface_count"
        ),
        "ready_for_external_publication": external_review.get(
            "ready_for_external_publication"
        ),
        "review_required_before_claims": external_review.get(
            "review_required_before_claims"
        ),
        "review_required_surface_count": external_review.get(
            "review_required_surface_count"
        ),
        "reviewer_summary_synced": external_review.get("reviewer_summary_synced"),
        "surface_count": external_review.get("surface_count"),
        "warning_evidence_items": external_review.get("warning_evidence_items"),
        "warnings": external_review.get("warnings"),
    }


def _audit_summary(release_audit: dict[str, Any]) -> dict[str, Any]:
    warning_check_ids = [
        record["id"] for record in _release_warning_records(release_audit)
    ]
    summary = release_audit.get("summary", {})
    return {
        "accepted": release_audit.get("accepted") is True,
        "failed": int(summary.get("failed", 0)),
        "passed": int(summary.get("passed", 0)),
        "warning": int(summary.get("warning", 0)),
        "warning_check_ids": warning_check_ids,
        "total": int(summary.get("total", 0)),
    }


def _release_warning_records(release_audit: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for check in _list_or_empty(release_audit.get("checks")):
        if not isinstance(check, dict) or check.get("status") != "warning":
            continue
        check_id = check.get("id")
        if not isinstance(check_id, str) or not check_id:
            continue
        records.append(
            {
                "artifact": check.get("artifact"),
                "id": check_id,
                "detail": check.get("detail"),
                "evidence": _dict_or_empty(check.get("evidence")),
            }
        )
    return sorted(records, key=lambda record: record["id"])


def _surface_notes(publication_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for surface in publication_manifest.get("surfaces", []):
        if not isinstance(surface, dict):
            continue
        notes.append(
            {
                "artifact_count": len(_list_or_empty(surface.get("artifact_paths"))),
                "id": surface.get("id"),
                "platform": surface.get("platform"),
                "publication_status": surface.get("publication_status"),
                "requires_credentials": surface.get("requires_credentials"),
                "review_required_before_publish": surface.get(
                    "review_required_before_publish"
                ),
                "smoke_gate": surface.get("smoke_gate"),
            }
        )
    return sorted(notes, key=lambda entry: str(entry["id"]))


def build_platform_review_matrix(
    publication_manifest: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return build_platform_review_matrix_from_surface_records(
        _surface_notes(publication_manifest)
    )


def build_platform_review_matrix_from_surface_records(
    surface_records: list[Any],
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for surface in surface_records:
        if not isinstance(surface, dict):
            continue
        platform = surface.get("platform")
        if not isinstance(platform, str) or not platform:
            continue
        entry = grouped.setdefault(
            platform,
            {
                "artifact_count": 0,
                "credentialed_surface_count": 0,
                "publication_statuses": [],
                "review_required_surface_count": 0,
                "smoke_gates": [],
                "surface_count": 0,
                "surface_ids": [],
            },
        )
        entry["artifact_count"] += _int_or_zero(surface.get("artifact_count"))
        entry["surface_count"] += 1
        if surface.get("requires_credentials") is True:
            entry["credentialed_surface_count"] += 1
        if surface.get("review_required_before_publish") is True:
            entry["review_required_surface_count"] += 1
        _append_unique_text(entry["surface_ids"], surface.get("id"))
        _append_unique_text(
            entry["publication_statuses"],
            surface.get("publication_status"),
        )
        _append_unique_text(entry["smoke_gates"], surface.get("smoke_gate"))

    return {
        platform: {
            "artifact_count": entry["artifact_count"],
            "credentialed_surface_count": entry["credentialed_surface_count"],
            "publication_statuses": sorted(entry["publication_statuses"]),
            "review_required_surface_count": entry[
                "review_required_surface_count"
            ],
            "smoke_gates": sorted(entry["smoke_gates"]),
            "surface_count": entry["surface_count"],
            "surface_ids": sorted(entry["surface_ids"]),
        }
        for platform, entry in sorted(grouped.items())
    }


def summarize_platform_review_matrix(matrix: dict[str, Any]) -> dict[str, int]:
    entries = [entry for entry in matrix.values() if isinstance(entry, dict)]
    return {
        "credentialed_surfaces": sum(
            _int_or_zero(entry.get("credentialed_surface_count"))
            for entry in entries
        ),
        "review_required_surfaces": sum(
            _int_or_zero(entry.get("review_required_surface_count"))
            for entry in entries
        ),
        "surfaces": sum(_int_or_zero(entry.get("surface_count")) for entry in entries),
    }


def build_credential_review_queue(
    publication_manifest: dict[str, Any],
    *,
    credentialed_surface_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    expected_ids = set(credentialed_surface_ids or [])
    queue: list[dict[str, Any]] = []
    for surface in publication_manifest.get("surfaces", []):
        if not isinstance(surface, dict):
            continue
        surface_id = surface.get("id")
        if expected_ids:
            include = surface_id in expected_ids
        else:
            include = surface.get("requires_credentials") is True
        if not include:
            continue
        queue.append(
            {
                "artifact_count": len(_list_or_empty(surface.get("artifact_paths"))),
                "credential_material_included": False,
                "first_publication_target": "private_or_draft_review_surface",
                "id": surface_id,
                "platform": surface.get("platform"),
                "publication_status": surface.get("publication_status"),
                "review_required_before_publish": surface.get(
                    "review_required_before_publish"
                ),
                "smoke_gate": surface.get("smoke_gate"),
            }
        )
    return sorted(queue, key=lambda entry: str(entry["id"]))


def _next_steps(blockers: list[dict[str, str]]) -> list[str]:
    if not blockers:
        return [
            "Run the platform-specific publish command from the reviewed release plan.",
            "Record the external URL and commit only reviewed public metadata.",
        ]
    return [
        "Resolve or explicitly approve every blocker before external publication.",
        "Use private/draft publication targets first for credentialed platforms.",
        "Regenerate this preflight after release review and credential review.",
    ]


def _verify_conservative_default(
    preflight: dict[str, Any],
    family_support_matrix: dict[str, Any],
    expected_warning_records: list[dict[str, Any]],
    failures: list[str],
) -> None:
    if preflight.get("schema_version") != PUBLICATION_PREFLIGHT_SCHEMA:
        failures.append(
            "Publication preflight schema_version must be "
            f"{PUBLICATION_PREFLIGHT_SCHEMA}."
        )
    if preflight.get("project") != PROJECT:
        failures.append("Publication preflight project metadata is incorrect.")
    review_state = preflight.get("review_state", {})
    if review_state.get("external_release_review_approved") is not False:
        failures.append(
            "Committed publication preflight must not mark release review approved."
        )
    if review_state.get("credentials_reviewed") is not False:
        failures.append(
            "Committed publication preflight must not mark credentials reviewed."
        )
    blocker_ids = {
        blocker.get("id")
        for blocker in preflight.get("blockers", [])
        if isinstance(blocker, dict)
    }
    required_blockers = {
        "external_release_review_not_approved",
        "credential_review_not_approved",
    }
    if not required_blockers <= blocker_ids:
        failures.append("Publication preflight lacks conservative review blockers.")
    if preflight.get("ready_for_external_publication") is not False:
        failures.append(
            "Committed publication preflight must block external publication."
        )
    if preflight.get("safety") != SAFETY:
        failures.append("Publication preflight safety boundaries are incorrect.")
    _verify_warning_records(preflight, expected_warning_records, failures)
    _verify_credential_review_queue(preflight, failures)
    _verify_family_readiness_matrix(preflight, family_support_matrix, failures)
    _verify_platform_review_matrix(preflight, failures)
    family_support = _dict_or_empty(preflight.get("family_support"))
    platform_support = _dict_or_empty(family_support.get("platform_support"))
    if family_support.get("review_required_before_claims") is not True:
        failures.append(
            "Publication preflight must keep family-support review gate."
        )
    if (
        platform_support.get("family_counts_match") is not True
        or platform_support.get("missing_claim_review_gate") != []
    ):
        failures.append(
            "Publication preflight platform family-support gates are incomplete."
        )
    _verify_source_catalog_scope(
        _dict_or_empty(preflight.get("source_catalog_scope")),
        failures,
    )
    failures.extend(
        runbook_architecture_evidence_failures(
            _dict_or_empty(preflight.get("runbook_architecture")),
            subject="Publication preflight",
        )
    )
    _verify_external_review(
        _dict_or_empty(preflight.get("external_review")),
        failures,
    )
    public_private_boundary = _dict_or_empty(
        preflight.get("public_private_boundary")
    )
    redaction = _dict_or_empty(
        public_private_boundary.get("report_generator_redaction")
    )
    _verify_public_private_boundary(redaction, failures)


def _verify_source_catalog_scope(
    source_catalog_scope: dict[str, Any],
    failures: list[str],
) -> None:
    if source_catalog_scope.get("non_lattice_toy_operator_security_claims") != 0:
        failures.append(
            "Publication preflight source catalog scope must not contain "
            "non-lattice toy security claims."
        )
    if source_catalog_scope.get("non_lattice_toy_evaluator_count") != (
        source_catalog_scope.get("source_count")
    ):
        failures.append(
            "Publication preflight source catalog scope must cover every source."
        )
    if source_catalog_scope.get("non_lattice_toy_operator_variant_count") != (
        source_catalog_scope.get("source_count")
    ):
        failures.append(
            "Publication preflight source catalog operator scope must cover "
            "every source."
        )
    platform_counts_match = source_catalog_scope.get(
        "platform_source_catalog_scope_counts_match"
    )
    if platform_counts_match is not True:
        failures.append(
            "Publication preflight platform source catalog scope must match "
            "source catalog scope."
        )
    if source_catalog_scope.get("platform_source_catalog_scope_security_claims") != 0:
        failures.append(
            "Publication preflight platform source catalog scope must not contain "
            "non-lattice toy security claims."
        )
    if source_catalog_scope.get("platform_source_catalog_scope_surfaces") != 3:
        failures.append(
            "Publication preflight platform source catalog scope must cover "
            "Prime, Hugging Face, and NVIDIA surfaces."
        )


def _verify_public_private_boundary(
    redaction: dict[str, Any],
    failures: list[str],
) -> None:
    if redaction.get("typed_trace_redaction_covered") is not True:
        failures.append(
            "Publication preflight typed TraceRecord redaction gate is incomplete."
        )
    if redaction.get("raw_mapping_redaction_covered") is not True:
        failures.append(
            "Publication preflight raw trace mapping redaction gate is incomplete."
        )
    if redaction.get("redacted_records") != 2:
        failures.append(
            "Publication preflight report redaction gate must cover two private "
            "input shapes."
        )


def _verify_external_review(
    external_review: dict[str, Any],
    failures: list[str],
) -> None:
    if external_review.get("reviewer_summary_synced") is not True:
        failures.append(
            "Publication preflight external review reviewer summary must be "
            "synchronized."
        )


def _verify_warning_records(
    preflight: dict[str, Any],
    expected_records: list[dict[str, Any]],
    failures: list[str],
) -> None:
    records = _list_or_empty(preflight.get("warnings"))
    audit = _dict_or_empty(preflight.get("audit"))
    warning_ids = [
        record.get("id") for record in records if isinstance(record, dict)
    ]
    expected_ids = [record["id"] for record in expected_records]
    if len(records) != audit.get("warning"):
        failures.append(
            "Publication preflight warning records must match audit warning count."
        )
    if warning_ids != _list_or_empty(audit.get("warning_check_ids")):
        failures.append(
            "Publication preflight warning ids must match audit warning ids."
        )
    if any(
        not _dict_or_empty(record.get("evidence"))
        for record in records
        if isinstance(record, dict)
    ):
        failures.append(
            "Publication preflight warning records must include evidence."
        )
    if (
        len(records) == len(expected_records)
        and warning_ids == expected_ids
        and _warning_evidence_items(records) == len(expected_records)
        and records != expected_records
    ):
        failures.append(
            "Publication preflight warning records are inconsistent with release "
            "audit."
        )


def _warning_evidence_items(records: list[Any]) -> int:
    return sum(
        1
        for record in records
        if isinstance(record, dict) and _dict_or_empty(record.get("evidence"))
    )


def _verify_family_readiness_matrix(
    preflight: dict[str, Any],
    family_support_matrix: dict[str, Any],
    failures: list[str],
) -> None:
    matrix = _dict_or_empty(preflight.get("family_readiness_matrix"))
    expected = build_family_readiness_matrix(family_support_matrix)
    if matrix != expected:
        failures.append(
            "Publication preflight family readiness matrix is inconsistent with "
            "family support matrix."
        )
        return

    summary = summarize_family_readiness_matrix(matrix)
    if summary["non_lattice_lattice_estimator_families"]:
        failures.append(
            "Publication preflight family readiness matrix must not enable "
            "Lattice Estimator for non-LWE/MLWE families."
        )
    if summary["schema_only_default_estimator_families"]:
        failures.append(
            "Publication preflight family readiness matrix must not assign "
            "default estimators to schema-only families."
        )
    if summary["review_required_families"] != summary["family_count"]:
        failures.append(
            "Publication preflight family readiness matrix must keep review "
            "gates for every family."
        )


def _verify_platform_review_matrix(
    preflight: dict[str, Any],
    failures: list[str],
) -> None:
    matrix = _dict_or_empty(preflight.get("platform_review_matrix"))
    expected = build_platform_review_matrix_from_surface_records(
        _list_or_empty(preflight.get("surface_notes"))
    )
    if matrix != expected:
        failures.append(
            "Publication preflight platform review matrix is inconsistent with "
            "surface notes."
        )
        return

    missing_platforms = sorted(REQUIRED_PUBLICATION_PLATFORMS - set(matrix))
    if missing_platforms:
        failures.append(
            "Publication preflight platform review matrix is missing platforms: "
            f"{missing_platforms}."
        )
    if any(
        entry.get("review_required_surface_count") != entry.get("surface_count")
        for entry in matrix.values()
        if isinstance(entry, dict)
    ):
        failures.append(
            "Publication preflight platform review matrix must keep review gates "
            "for every surface."
        )


def _verify_credential_review_queue(
    preflight: dict[str, Any],
    failures: list[str],
) -> None:
    queue = _list_or_empty(preflight.get("credential_review_queue"))
    credentialed_surface_ids = _list_or_empty(
        _dict_or_empty(preflight.get("publication")).get("credentialed_surfaces")
    )
    if not _credential_review_queue_complete(queue, credentialed_surface_ids):
        failures.append(
            "Publication preflight credential review queue must cover every "
            "credentialed surface."
        )
    if _credential_material_included(queue):
        failures.append(
            "Publication preflight credential review queue must not include "
            "credential material."
        )
    if any(
        isinstance(entry, dict)
        and entry.get("first_publication_target")
        != "private_or_draft_review_surface"
        for entry in queue
    ):
        failures.append(
            "Publication preflight credential review queue must target private "
            "or draft review surfaces first."
        )
    if any(
        isinstance(entry, dict)
        and entry.get("review_required_before_publish") is not True
        for entry in queue
    ):
        failures.append(
            "Publication preflight credential review queue must keep review gates."
        )


def _credential_review_queue_complete(
    queue: list[Any],
    credentialed_surface_ids: list[Any],
) -> bool:
    expected_ids = sorted(str(surface_id) for surface_id in credentialed_surface_ids)
    queue_ids = sorted(
        str(entry["id"])
        for entry in queue
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    )
    if queue_ids != expected_ids:
        return False
    return all(
        isinstance(entry, dict)
        and entry.get("first_publication_target")
        == "private_or_draft_review_surface"
        and entry.get("review_required_before_publish") is True
        for entry in queue
    )


def _credential_material_included(queue: list[Any]) -> bool:
    return any(
        isinstance(entry, dict)
        and entry.get("credential_material_included") is not False
        for entry in queue
    )


def _append_unique_text(values: list[Any], value: Any) -> None:
    if isinstance(value, str) and value and value not in values:
        values.append(value)


def _int_or_zero(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _read_preflight(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Publication preflight is missing: {path.as_posix()}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"Publication preflight is invalid JSON at line {exc.lineno}.")
        return {}
    if not isinstance(payload, dict):
        failures.append("Publication preflight must be a JSON object.")
        return {}
    return payload


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return payload


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path
