from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.family_support import (
    summarize_family_support_matrix,
    summarize_family_support_publication_gate,
)
from agades_pqc_gym.integrations.public_private_boundary import (
    public_private_boundary_from_check,
)

RELEASE_STATUS_SCHEMA = "agades.pqc.release_status.v1"
RELEASE_STATUS_VERIFICATION_SCHEMA = "agades.pqc.release_status_verification.v1"
ROOT = Path(__file__).resolve().parents[3]
PROJECT = {
    "name": "Agades PQC Gym",
    "package": "agades_pqc_gym",
    "cli": "agades-pqc",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
}
EXPECTED_FALSE_SAFETY_FLAGS = (
    "arbitrary_code_execution",
    "contains_private_traces",
    "live_targeting",
    "publishes_private_candidates",
    "security_claim",
)
PLATFORM_FAMILY_SUPPORT_KEYS = (
    "huggingface_collection",
    "prime_intellect",
    "nvidia",
)
PLATFORM_SOURCE_CATALOG_SCOPE_KEYS = PLATFORM_FAMILY_SUPPORT_KEYS
RUNBOOK_FAMILY_ARCHITECTURE_CHECK_ID = "runbook-family-agnostic-core"
RUNBOOK_ARCHITECTURE_KEYS = (
    "core_symbol_count",
    "core_symbol_import_count",
    "family_plugin_count",
    "family_plugin_manifest_digests_match",
    "family_plugin_module_count",
    "family_plugin_module_digest_count",
    "family_plugin_module_import_count",
    "family_registry_family_count_matches_plugin_manifest",
    "family_registry_plugin_count_matches_plugin_manifest",
    "family_registry_plugin_manifest_module_digest_count",
    "family_registry_plugin_manifest_synced",
    "family_registry_runtime_adapter_entries_match_plugin_manifest",
    "lattice_is_first_implemented_plugin",
    "planned_family_plugin_count",
    "public_runbook_audit_checks",
    "public_runbook_audit_synced",
)


def build_release_status(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    audit = _read_json(project_root / "public" / "release_audit.json")
    runbook_audit = _read_json(project_root / "public" / "runbook_audit.json")
    audit_checks = {check["id"]: check for check in audit["checks"]}
    dataset_info = _read_json(project_root / "hf" / "dataset" / "dataset_info.json")
    hf_space = _read_json(project_root / "hf" / "space_manifest.json")
    hf_collection = _read_json(project_root / "hf" / "collection_manifest.json")
    prime = _read_json(
        project_root
        / "prime_intellect"
        / "verifiers_environment"
        / "prime_manifest.json"
    )
    nvidia = _read_json(project_root / "nvidia" / "accelerator_manifest.json")
    family_support_matrix = _read_json(
        project_root / "docs" / "family_support_matrix.json"
    )

    public_benchmark = audit_checks["public-benchmark-manifest"]["evidence"]
    publication = audit_checks["publication-manifest-safety"]["evidence"]
    external_review = audit_checks["external-publication-review-packet"]["evidence"]
    runbook = audit_checks["runbook-deliverables"]["evidence"]
    release_plans = audit_checks["ecosystem-release-plans"]["evidence"]
    source_catalog = audit_checks["source-catalog-safety"]["evidence"]
    runbook_architecture = _runbook_architecture_from_audit(
        runbook_audit,
        release_family_plugin_manifest_evidence=audit_checks[
            "family-plugin-manifest"
        ]["evidence"],
        release_family_registry_manifest_evidence=audit_checks[
            "family-registry-manifest"
        ]["evidence"],
        release_runbook_evidence=runbook,
    )
    hf_collection_evidence = audit_checks["hf-collection-manifest"]["evidence"]
    prime_handoff = audit_checks["prime-publication-handoff"]["evidence"]
    nvidia_handoff = audit_checks["nvidia-publication-handoff"]["evidence"]
    hf_example_manifest = hf_space["example_manifest"]
    prime_task_manifest = prime["task_manifest"]
    nvidia_workload_summary = nvidia["workload_summary"]

    return {
        "schema_version": RELEASE_STATUS_SCHEMA,
        "project": PROJECT,
        "audit": {
            "accepted": audit["accepted"],
            "passed": audit["summary"]["passed"],
            "failed": audit["summary"]["failed"],
            "warning": audit["summary"]["warning"],
            "warning_check_ids": _audit_warning_ids(audit),
            "warning_records": _audit_warning_records(audit),
            "total": audit["summary"]["total"],
        },
        "runbook": {
            "artifact_count": runbook["artifact_count"],
            **runbook_architecture,
            "hf_attack_plan_rows": runbook["hf_attack_plan_rows"],
            "hf_valid_attack_plan_rows": runbook["hf_valid_attack_plan_rows"],
            "hf_invalid_attack_plan_rows": runbook["hf_invalid_attack_plan_rows"],
            "hf_task_metadata_rows": runbook["hf_task_metadata_rows"],
            "nvidia_workloads": runbook["nvidia_workloads"],
            "prime_tasks": runbook["prime_tasks"],
            "prime_tasks_match_hf_task_metadata_rows": runbook[
                "prime_tasks_match_hf_task_metadata_rows"
            ],
            "public_records": runbook["public_records"],
            "public_run_bundles": runbook["public_run_bundles"],
            "source_brief_sha256": runbook["runbook_source_brief_sha256"],
            "project_context_sha256": runbook["runbook_project_context_sha256"],
            "source_input_count": runbook["runbook_source_input_count"],
            "source_input_ids": runbook["runbook_source_input_ids"],
        },
        "public_benchmark": {
            "bundle_count": public_benchmark["bundle_count"],
            "record_count": public_benchmark["record_count"],
            "families": public_benchmark["families"],
        },
        "publication": {
            "surfaces": publication["surfaces"],
            "review_required_surfaces": publication["review_required_surfaces"],
            "credentialed_surfaces": publication["credentialed_surfaces"],
            "surface_artifact_digests": publication["surface_artifact_digests"],
            "surface_artifact_digest_exclusions": publication[
                "surface_artifact_digest_exclusions"
            ],
            "public_run_bundles": publication["public_run_bundles"],
            "public_run_bundle_artifacts": publication["public_run_bundle_artifacts"],
            "public_run_bundle_artifact_digests": publication[
                "public_run_bundle_artifact_digests"
            ],
        },
        "external_review": {
            "blockers": external_review["blockers"],
            "credential_material_included": external_review[
                "credential_material_included"
            ],
            "credential_review_queue_complete": external_review[
                "credential_review_queue_complete"
            ],
            "credential_review_queue_items": external_review[
                "credential_review_queue_items"
            ],
            "credentialed_surface_count": external_review[
                "credentialed_surface_count"
            ],
            "ready_for_external_publication": external_review[
                "ready_for_external_publication"
            ],
            "review_required_before_claims": external_review[
                "review_required_before_claims"
            ],
            "review_required_surface_count": external_review[
                "review_required_surface_count"
            ],
            "reviewer_summary_synced": external_review[
                "reviewer_summary_synced"
            ],
            "surface_count": external_review["surface_count"],
            "warning_evidence_items": external_review["warning_evidence_items"],
            "warnings": external_review["warnings"],
        },
        "family_support": summarize_family_support_matrix(family_support_matrix),
        "public_private_boundary": public_private_boundary_from_check(
            _object(audit_checks.get("report-generator-redaction"))
        ),
        "ecosystem": {
            "huggingface_dataset": {
                "attack_plan_count": dataset_info["attack_plan_count"],
                "valid_attack_plan_count": dataset_info["valid_attack_plan_count"],
                "invalid_attack_plan_count": dataset_info["invalid_attack_plan_count"],
                "task_metadata_count": dataset_info["task_metadata_count"],
                "prime_task_eligible_count": dataset_info[
                    "prime_task_eligible_count"
                ],
                "invalid_attack_plan_ids": dataset_info["invalid_attack_plan_ids"],
                "verifier_output_count": dataset_info["verifier_output_count"],
                "public_run_bundles": len(dataset_info["public_run_bundles"]),
            },
            "huggingface_space": {
                "dataset_attack_plan_count": hf_example_manifest[
                    "dataset_attack_plan_count"
                ],
                "dataset_valid_attack_plan_count": hf_example_manifest[
                    "dataset_valid_attack_plan_count"
                ],
                "dataset_invalid_attack_plan_count": hf_example_manifest[
                    "dataset_invalid_attack_plan_count"
                ],
                "example_count": hf_example_manifest["example_count"],
                "excluded_attack_plan_ids": hf_example_manifest[
                    "excluded_attack_plan_ids"
                ],
                "family_count": len(hf_example_manifest["families"]),
                "labels_match_valid_dataset_rows": hf_example_manifest[
                    "labels_match_valid_dataset_rows"
                ],
            },
            "huggingface_collection": {
                "contains_private_traces": hf_collection_evidence[
                    "contains_private_traces"
                ],
                "credentialed_entries": hf_collection_evidence[
                    "credentialed_entries"
                ],
                "entry_count": hf_collection_evidence["entry_count"],
                "external_publication_requires_review": hf_collection_evidence[
                    "external_publication_requires_review"
                ],
                "public_push_requires_review": hf_collection["collection"][
                    "public_push_requires_review"
                ],
                "review_required_entries": hf_collection_evidence[
                    "review_required_entries"
                ],
                "security_claim": hf_collection_evidence["security_claim"],
                "suggested_slug": hf_collection["collection"]["suggested_slug"],
                "suggested_title": hf_collection["collection"]["suggested_title"],
                "family_support": hf_collection["family_support"],
                "source_catalog_scope": hf_collection["source_catalog_scope"],
            },
            "prime_intellect": {
                "task_count": prime_task_manifest["task_count"],
                "family_count": len(prime_task_manifest["families"]),
                "handoff_local_package_ready": prime_handoff[
                    "local_package_ready"
                ],
                "handoff_artifact_count": prime_handoff["artifact_count"],
                "prime_hub_publication_performed": prime_handoff[
                    "prime_hub_publication_performed"
                ],
                "requires_credentials": prime["release"]["requires_credentials"],
                "review_required_before_publish": prime["release"][
                    "review_required_before_publish"
                ],
                "family_support": prime["family_support"],
                "source_catalog_scope": prime["source_catalog_scope"],
            },
            "nvidia": {
                "all_current_workloads_cpu": nvidia_workload_summary[
                    "all_current_workloads_cpu"
                ],
                "cpu_workload_count": nvidia_workload_summary["cpu_workload_count"],
                "current_gpu_required_workload_count": nvidia_workload_summary[
                    "current_gpu_required_workload_count"
                ],
                "current_workload_count": nvidia_workload_summary[
                    "current_workload_count"
                ],
                "gpu_future_workload_count": nvidia_workload_summary[
                    "gpu_future_workload_count"
                ],
                "public_run_bundle_count": len(
                    nvidia["public_artifacts"]["public_run_bundles"]
                ),
                "no_current_workload_requires_gpu": nvidia_workload_summary[
                    "no_current_workload_requires_gpu"
                ],
                "reserved_future_gpu_required_workload_count": (
                    nvidia_workload_summary[
                        "reserved_future_gpu_required_workload_count"
                    ]
                ),
                "reserved_future_workload_count": nvidia_workload_summary[
                    "reserved_future_workload_count"
                ],
                "workload_count": len(nvidia["workloads"]),
                "gpu_status": nvidia["mvp_runtime"]["gpu_status"],
                "handoff_artifact_count": nvidia_handoff["artifact_count"],
                "handoff_external_submission_requires_review": nvidia_handoff[
                    "external_submission_requires_review"
                ],
                "nvidia_submission_performed": nvidia_handoff[
                    "nvidia_submission_performed"
                ],
                "gpu_execution_performed": nvidia_handoff[
                    "gpu_execution_performed"
                ],
                "family_support": nvidia["family_support"],
                "source_catalog_scope": nvidia["source_catalog_scope"],
            },
            "source_catalog": {
                "current_public_surfaces": source_catalog[
                    "current_public_surfaces"
                ],
                "future_reviewed_adapters": source_catalog[
                    "future_reviewed_adapters"
                ],
                "non_lattice_toy_evaluator_count": source_catalog[
                    "non_lattice_toy_evaluator_count"
                ],
                "non_lattice_toy_operator_families": source_catalog[
                    "non_lattice_toy_operator_families"
                ],
                "non_lattice_toy_operator_security_claims": source_catalog[
                    "non_lattice_toy_operator_security_claims"
                ],
                "non_lattice_toy_operator_variant_count": source_catalog[
                    "non_lattice_toy_operator_variant_count"
                ],
                "platforms": source_catalog["platforms"],
                "source_count": source_catalog["source_count"],
                "source_map_only": source_catalog["source_map_only"],
            },
            "release_plans": {
                "plans": release_plans["plans"],
                "prime_ecosystem_anchors": release_plans[
                    "prime_ecosystem_anchors"
                ],
                "prime_ecosystem_anchor_plan_coverage": release_plans[
                    "prime_ecosystem_anchor_plan_coverage"
                ],
            },
        },
        "safety": {
            "arbitrary_code_execution": False,
            "contains_private_traces": False,
            "live_targeting": False,
            "publishes_private_candidates": False,
            "security_claim": False,
            "external_publication_requires_review": True,
        },
        "release_gates": [
            "uv run pytest tests/test_release_status.py -q",
            "uv run agades-pqc release-status --out docs/release_status.json",
            (
                "uv run agades-pqc release-status-verify --status "
                "docs/release_status.json"
            ),
            (
                "uv run agades-pqc ecosystem-smoke-verify --report "
                "reports/ecosystem_smoke.json"
            ),
        ],
    }


def write_release_status(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    status = build_release_status(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return status


def verify_release_status(
    path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    resolved_path = _resolve_status_path(path, root=root)
    status = _read_status(resolved_path, failures)

    if status.get("schema_version") != RELEASE_STATUS_SCHEMA:
        failures.append(
            f"release status: schema_version must be {RELEASE_STATUS_SCHEMA}."
        )

    if status.get("project") != PROJECT:
        failures.append("release status: project metadata is not Agades PQC Gym.")

    _verify_safety(status, failures)
    _verify_family_support(status, failures)
    _verify_platform_family_support(status, failures)
    _verify_platform_source_catalog_scope(status, failures)
    _verify_public_private_boundary(status, failures)
    _verify_runbook_architecture(status, failures)
    _verify_external_review(status, failures)
    _verify_audit_warnings(status, failures)

    try:
        expected = build_release_status(root=root)
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        expected = None
        failures.append(f"release status: generated status could not be built: {exc}")

    if expected is not None and status != expected:
        failures.append("release status is not synchronized with the generated status.")

    summary = _verification_summary(status)
    summary["failure_count"] = len(failures)

    return {
        "schema_version": RELEASE_STATUS_VERIFICATION_SCHEMA,
        "status_path": str(path),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def summarize_release_status_family_support(
    status: dict[str, Any],
) -> dict[str, Any]:
    family_support = _object(status.get("family_support"))
    ecosystem = _object(status.get("ecosystem"))
    platform_family_supports = _platform_family_supports(ecosystem)
    return summarize_family_support_publication_gate(
        family_support,
        platform_family_supports,
        required_platforms=PLATFORM_FAMILY_SUPPORT_KEYS,
    )


def summarize_release_status_public_private_boundary(
    status: dict[str, Any],
) -> dict[str, Any]:
    return _public_private_boundary_from_status(status)


def summarize_release_status_runbook_architecture(
    status: dict[str, Any],
) -> dict[str, Any]:
    runbook = _object(status.get("runbook"))
    return {key: runbook.get(key) for key in RUNBOOK_ARCHITECTURE_KEYS}


def summarize_release_status_source_catalog_scope(
    status: dict[str, Any],
) -> dict[str, Any]:
    ecosystem = _object(status.get("ecosystem"))
    source_catalog = _object(ecosystem.get("source_catalog"))
    platform_scopes = _platform_source_catalog_scopes(ecosystem)
    summary = _source_catalog_scope_from_source_catalog(source_catalog)
    platform_security_claims = 0
    for scope in platform_scopes.values():
        claims = scope.get("non_lattice_toy_operator_security_claims")
        if isinstance(claims, int):
            platform_security_claims += claims
    summary.update(
        {
            "platform_source_catalog_scope_counts_match": (
                _platform_source_catalog_scope_counts_match(
                    platform_scopes,
                    _source_catalog_scope_from_source_catalog(source_catalog),
                )
            ),
            "platform_source_catalog_scope_security_claims": (
                platform_security_claims
            ),
            "platform_source_catalog_scope_surfaces": len(platform_scopes),
        }
    )
    return summary


def _source_catalog_scope_from_source_catalog(
    source_catalog: dict[str, Any],
) -> dict[str, Any]:
    families = source_catalog.get("non_lattice_toy_operator_families")
    return {
        "non_lattice_toy_evaluator_count": source_catalog.get(
            "non_lattice_toy_evaluator_count"
        ),
        "non_lattice_toy_operator_families": (
            families if isinstance(families, list) else []
        ),
        "non_lattice_toy_operator_security_claims": source_catalog.get(
            "non_lattice_toy_operator_security_claims"
        ),
        "non_lattice_toy_operator_variant_count": source_catalog.get(
            "non_lattice_toy_operator_variant_count"
        ),
        "source_count": source_catalog.get("source_count"),
    }


def _public_private_boundary_from_status(
    status: dict[str, Any],
) -> dict[str, Any]:
    return _object(status.get("public_private_boundary"))


def _runbook_architecture_from_audit(
    runbook_audit: dict[str, Any],
    *,
    release_family_plugin_manifest_evidence: dict[str, Any],
    release_family_registry_manifest_evidence: dict[str, Any],
    release_runbook_evidence: dict[str, Any],
) -> dict[str, Any]:
    audit_checks = {
        check.get("id"): check
        for check in _list_or_empty(runbook_audit.get("checks"))
        if isinstance(check, dict)
    }
    architecture_check = _object(
        audit_checks.get(RUNBOOK_FAMILY_ARCHITECTURE_CHECK_ID)
    )
    evidence = _object(architecture_check.get("evidence"))
    family_plugin_modules = _object(evidence.get("family_plugin_modules"))
    return {
        "core_symbol_count": evidence.get("core_symbol_count"),
        "core_symbol_import_count": evidence.get("core_symbol_import_count"),
        "family_plugin_count": evidence.get("family_plugin_count"),
        "family_plugin_manifest_digests_match": (
            release_family_plugin_manifest_evidence.get(
                "runbook_module_digests_match"
            )
        ),
        "family_plugin_module_count": sum(
            len(_list_or_empty(paths)) for paths in family_plugin_modules.values()
        ),
        "family_plugin_module_digest_count": evidence.get(
            "family_plugin_module_digest_count"
        ),
        "family_plugin_module_import_count": evidence.get(
            "family_plugin_module_import_count"
        ),
        "family_registry_family_count_matches_plugin_manifest": (
            release_family_registry_manifest_evidence.get(
                "registry_family_count_matches_plugin_manifest"
            )
        ),
        "family_registry_plugin_count_matches_plugin_manifest": (
            release_family_registry_manifest_evidence.get(
                "registry_plugin_count_matches_plugin_manifest"
            )
        ),
        "family_registry_plugin_manifest_module_digest_count": (
            release_family_registry_manifest_evidence.get(
                "plugin_manifest_implementation_module_digest_count"
            )
        ),
        "family_registry_plugin_manifest_synced": (
            release_family_registry_manifest_evidence.get("plugin_manifest_synced")
        ),
        "family_registry_runtime_adapter_entries_match_plugin_manifest": (
            release_family_registry_manifest_evidence.get(
                "registry_runtime_adapter_entries_match_plugin_manifest"
            )
        ),
        "lattice_is_first_implemented_plugin": evidence.get(
            "lattice_is_first_implemented_plugin"
        ),
        "planned_family_plugin_count": evidence.get("planned_family_plugin_count"),
        "public_runbook_audit_checks": release_runbook_evidence.get(
            "public_runbook_audit_checks"
        ),
        "public_runbook_audit_synced": release_runbook_evidence.get(
            "public_runbook_audit_synced"
        ),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _audit_warning_ids(audit: dict[str, Any]) -> list[str]:
    return [record["id"] for record in _audit_warning_records(audit)]


def _audit_warning_records(audit: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for check in _list_or_empty(audit.get("checks")):
        if not isinstance(check, dict) or check.get("status") != "warning":
            continue
        check_id = check.get("id")
        if not isinstance(check_id, str) or not check_id:
            continue
        records.append(
            {
                "artifact": check.get("artifact"),
                "detail": check.get("detail"),
                "evidence": _object(check.get("evidence")),
                "id": check_id,
            }
        )
    return sorted(records, key=lambda record: record["id"])


def _resolve_status_path(path: Path, *, root: Path | None) -> Path:
    if path.is_absolute() or root is None:
        return path
    return root / path


def _read_status(path: Path, failures: list[str]) -> dict[str, Any]:
    if not path.is_file():
        failures.append(f"release status is missing: {path}")
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"release status is invalid JSON: {exc}")
        return {}
    if not isinstance(raw, dict):
        failures.append("release status must be a JSON object.")
        return {}
    return raw


def _verify_safety(status: dict[str, Any], failures: list[str]) -> None:
    safety = status.get("safety")
    if not isinstance(safety, dict):
        failures.append("release status: safety must be an object.")
        return
    for flag in EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            failures.append(f"release status: safety.{flag} must be false.")
    if safety.get("external_publication_requires_review") is not True:
        failures.append(
            "release status: safety.external_publication_requires_review must be true."
        )


def _verify_family_support(status: dict[str, Any], failures: list[str]) -> None:
    family_support = status.get("family_support")
    if not isinstance(family_support, dict):
        failures.append("release status: family_support must be an object.")
        return
    if family_support.get("review_required_before_claims") is not True:
        failures.append(
            "release status: family_support.review_required_before_claims must be true."
        )


def _verify_platform_family_support(
    status: dict[str, Any],
    failures: list[str],
) -> None:
    ecosystem = status.get("ecosystem")
    if not isinstance(ecosystem, dict):
        failures.append("release status: ecosystem must be an object.")
        return

    root_family_support = status.get("family_support")
    root_family_count = (
        root_family_support.get("family_count")
        if isinstance(root_family_support, dict)
        else None
    )
    for platform_key in PLATFORM_FAMILY_SUPPORT_KEYS:
        platform = ecosystem.get(platform_key)
        if not isinstance(platform, dict):
            failures.append(
                f"release status: ecosystem.{platform_key} must be an object."
            )
            continue
        family_support = platform.get("family_support")
        if not isinstance(family_support, dict):
            failures.append(
                "release status: ecosystem."
                f"{platform_key}.family_support must be an object."
            )
            continue
        if family_support.get("review_required_before_claims") is not True:
            failures.append(
                "release status: ecosystem."
                f"{platform_key}.family_support.review_required_before_claims "
                "must be true."
            )
        if family_support.get("family_count") != root_family_count:
            failures.append(
                "release status: ecosystem."
                f"{platform_key}.family_support.family_count must match "
                "family_support.family_count."
            )


def _verify_platform_source_catalog_scope(
    status: dict[str, Any],
    failures: list[str],
) -> None:
    ecosystem = status.get("ecosystem")
    if not isinstance(ecosystem, dict):
        failures.append("release status: ecosystem must be an object.")
        return

    expected_scope = _source_catalog_scope_from_source_catalog(
        _object(ecosystem.get("source_catalog"))
    )
    for platform_key in PLATFORM_SOURCE_CATALOG_SCOPE_KEYS:
        platform = ecosystem.get(platform_key)
        if not isinstance(platform, dict):
            failures.append(
                f"release status: ecosystem.{platform_key} must be an object."
            )
            continue
        scope = platform.get("source_catalog_scope")
        if not isinstance(scope, dict):
            failures.append(
                "release status: ecosystem."
                f"{platform_key}.source_catalog_scope must be an object."
            )
            continue
        if scope.get("non_lattice_toy_operator_security_claims") != 0:
            failures.append(
                "release status: ecosystem."
                f"{platform_key}.source_catalog_scope."
                "non_lattice_toy_operator_security_claims must be zero."
            )
        for field in (
            "non_lattice_toy_evaluator_count",
            "non_lattice_toy_operator_families",
            "non_lattice_toy_operator_variant_count",
            "source_count",
        ):
            if scope.get(field) != expected_scope.get(field):
                failures.append(
                    "release status: ecosystem."
                    f"{platform_key}.source_catalog_scope.{field} must match "
                    f"ecosystem.source_catalog.{field}."
                )


def _verify_public_private_boundary(
    status: dict[str, Any],
    failures: list[str],
) -> None:
    boundary = _public_private_boundary_from_status(status)
    if not boundary:
        failures.append("release status: public_private_boundary must be an object.")
        return
    redaction = _object(boundary.get("report_generator_redaction"))
    if redaction.get("status") != "passed" or redaction.get("blocking") is not True:
        failures.append(
            "release status: report-generator redaction gate must be blocking "
            "and passed."
        )
    if redaction.get("typed_trace_redaction_covered") is not True:
        failures.append(
            "release status: typed TraceRecord redaction boundary must be covered."
        )
    if redaction.get("raw_mapping_redaction_covered") is not True:
        failures.append(
            "release status: raw trace mapping redaction boundary must be covered."
        )
    if redaction.get("redacted_records") != 2:
        failures.append(
            "release status: report-generator redaction gate must cover two "
            "private input shapes."
        )


def _verify_runbook_architecture(
    status: dict[str, Any],
    failures: list[str],
) -> None:
    architecture = summarize_release_status_runbook_architecture(status)
    failures.extend(
        runbook_architecture_evidence_failures(
            architecture,
            subject="release status:",
        )
    )


def runbook_architecture_evidence_failures(
    architecture: dict[str, Any],
    *,
    subject: str,
) -> list[str]:
    failures: list[str] = []
    prefix = subject.strip()
    if not architecture:
        return [f"{prefix} runbook architecture evidence is missing."]
    if architecture.get("public_runbook_audit_synced") is not True:
        failures.append(f"{prefix} public runbook audit must be synchronized.")
    if not _positive_int(architecture.get("public_runbook_audit_checks")):
        failures.append(f"{prefix} public runbook audit must include checks.")
    if architecture.get("lattice_is_first_implemented_plugin") is not True:
        failures.append(
            f"{prefix} lattice must remain marked as the first implemented plugin."
        )
    if not _positive_counts_match(
        architecture,
        imported_key="core_symbol_import_count",
        declared_key="core_symbol_count",
    ):
        failures.append(
            f"{prefix} runbook core import evidence is incomplete."
        )
    if architecture.get("family_plugin_manifest_digests_match") is not True:
        failures.append(
            f"{prefix} runbook and family plugin manifest digests must match."
        )
    if not _positive_counts_match(
        architecture,
        imported_key="family_plugin_module_digest_count",
        declared_key="family_plugin_module_count",
    ):
        failures.append(
            f"{prefix} runbook family plugin digest evidence is incomplete."
        )
    if not _positive_counts_match(
        architecture,
        imported_key="family_plugin_module_import_count",
        declared_key="family_plugin_module_count",
    ):
        failures.append(
            f"{prefix} runbook family plugin import evidence is incomplete."
        )
    if architecture.get("family_registry_plugin_manifest_synced") is not True:
        failures.append(
            f"{prefix} family registry and plugin manifest must be synchronized."
        )
    if (
        architecture.get("family_registry_family_count_matches_plugin_manifest")
        is not True
    ):
        failures.append(
            f"{prefix} family registry families must match plugin manifest."
        )
    if (
        architecture.get("family_registry_plugin_count_matches_plugin_manifest")
        is not True
    ):
        failures.append(
            f"{prefix} family registry plugin count must match plugin manifest."
        )
    if not _positive_counts_match(
        architecture,
        imported_key="family_registry_plugin_manifest_module_digest_count",
        declared_key="family_plugin_module_count",
    ):
        failures.append(
            f"{prefix} family registry plugin manifest digest evidence is incomplete."
        )
    if (
        architecture.get(
            "family_registry_runtime_adapter_entries_match_plugin_manifest"
        )
        is not True
    ):
        failures.append(
            f"{prefix} family registry runtime adapters must match plugin manifest."
        )
    return failures


def _positive_counts_match(
    architecture: dict[str, Any],
    *,
    imported_key: str,
    declared_key: str,
) -> bool:
    imported = architecture.get(imported_key)
    declared = architecture.get(declared_key)
    return _positive_int(imported) and _positive_int(declared) and imported == declared


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _verify_audit_warnings(status: dict[str, Any], failures: list[str]) -> None:
    audit = _object(status.get("audit"))
    records = _list_or_empty(audit.get("warning_records"))
    ids = _list_or_empty(audit.get("warning_check_ids"))
    record_ids = [
        record.get("id") for record in records if isinstance(record, dict)
    ]
    if len(records) != audit.get("warning"):
        failures.append(
            "release status: audit warning records must match audit.warning."
        )
    if ids != record_ids:
        failures.append(
            "release status: audit warning ids must match audit warning records."
        )
    if any(
        not _object(record.get("evidence"))
        for record in records
        if isinstance(record, dict)
    ):
        failures.append(
            "release status: audit warning records must include evidence."
        )


def _verify_external_review(status: dict[str, Any], failures: list[str]) -> None:
    external_review = status.get("external_review")
    if not isinstance(external_review, dict):
        failures.append("release status: external_review must be an object.")
        return
    if external_review.get("reviewer_summary_synced") is not True:
        failures.append(
            "release status: external review reviewer summary must be synchronized."
        )


def _verification_summary(status: dict[str, Any]) -> dict[str, Any]:
    audit = _object(status.get("audit"))
    ecosystem = _object(status.get("ecosystem"))
    external_review = _object(status.get("external_review"))
    source_catalog = _object(ecosystem.get("source_catalog"))
    runbook = _object(status.get("runbook"))
    family_support = _object(status.get("family_support"))
    future_source_counts = _object(
        family_support.get("per_family_future_reviewed_adapter_source_counts")
    )
    public_private_boundary = _public_private_boundary_from_status(status)
    report_redaction = _object(
        public_private_boundary.get("report_generator_redaction")
    )
    platform_family_supports = _platform_family_supports(ecosystem)
    source_catalog_summary = summarize_release_status_source_catalog_scope(status)

    return {
        "audit_accepted": audit.get("accepted"),
        "audit_failed": audit.get("failed"),
        "audit_passed": audit.get("passed"),
        "audit_total": audit.get("total"),
        "audit_warning": audit.get("warning"),
        "audit_warning_evidence_items": sum(
            1
            for record in _list_or_empty(audit.get("warning_records"))
            if isinstance(record, dict) and _object(record.get("evidence"))
        ),
        "audit_warning_records": _list_count(audit.get("warning_records")),
        "current_public_surfaces": _list_count(
            source_catalog.get("current_public_surfaces")
        ),
        "family_count": family_support.get("family_count"),
        "families_with_future_reviewed_adapters": _list_count(
            family_support.get("families_with_future_reviewed_adapters")
        ),
        "future_reviewed_adapters": _list_count(
            source_catalog.get("future_reviewed_adapters")
        ),
        "future_reviewed_adapter_sources_by_family": _int_value_sum(
            future_source_counts
        ),
        "reviewer_summary_synced": external_review.get("reviewer_summary_synced"),
        "runbook_core_symbol_import_count": runbook.get(
            "core_symbol_import_count"
        ),
        "runbook_family_plugin_manifest_digests_match": runbook.get(
            "family_plugin_manifest_digests_match"
        ),
        "runbook_family_plugin_module_count": runbook.get(
            "family_plugin_module_count"
        ),
        "runbook_family_plugin_module_digest_count": runbook.get(
            "family_plugin_module_digest_count"
        ),
        "runbook_family_plugin_module_import_count": runbook.get(
            "family_plugin_module_import_count"
        ),
        "runbook_family_registry_family_count_matches_plugin_manifest": runbook.get(
            "family_registry_family_count_matches_plugin_manifest"
        ),
        "runbook_family_registry_plugin_count_matches_plugin_manifest": runbook.get(
            "family_registry_plugin_count_matches_plugin_manifest"
        ),
        "runbook_family_registry_plugin_manifest_module_digest_count": runbook.get(
            "family_registry_plugin_manifest_module_digest_count"
        ),
        "runbook_family_registry_plugin_manifest_synced": runbook.get(
            "family_registry_plugin_manifest_synced"
        ),
        "runbook_family_registry_runtime_adapter_entries_match_plugin_manifest": (
            runbook.get(
                "family_registry_runtime_adapter_entries_match_plugin_manifest"
            )
        ),
        "hf_valid_attack_plan_rows": runbook.get("hf_valid_attack_plan_rows"),
        "platform_family_support_family_counts_match": (
            _platform_family_support_family_counts_match(
                platform_family_supports,
                family_support.get("family_count"),
            )
        ),
        "platform_family_support_surfaces": len(platform_family_supports),
        "platform_source_catalog_scope_counts_match": source_catalog_summary[
            "platform_source_catalog_scope_counts_match"
        ],
        "platform_source_catalog_scope_security_claims": source_catalog_summary[
            "platform_source_catalog_scope_security_claims"
        ],
        "platform_source_catalog_scope_surfaces": source_catalog_summary[
            "platform_source_catalog_scope_surfaces"
        ],
        "platforms_with_family_claim_review_gate": sum(
            1
            for support in platform_family_supports.values()
            if support.get("review_required_before_claims") is True
        ),
        "prime_tasks": runbook.get("prime_tasks"),
        "public_run_bundles": runbook.get("public_run_bundles"),
        "raw_mapping_redaction_covered": report_redaction.get(
            "raw_mapping_redaction_covered"
        ),
        "report_redaction_records": report_redaction.get("redacted_records"),
        "non_lattice_toy_evaluator_count": source_catalog.get(
            "non_lattice_toy_evaluator_count"
        ),
        "non_lattice_toy_operator_security_claims": source_catalog.get(
            "non_lattice_toy_operator_security_claims"
        ),
        "non_lattice_toy_operator_variant_count": source_catalog.get(
            "non_lattice_toy_operator_variant_count"
        ),
        "source_count": source_catalog.get("source_count"),
        "source_map_only": _list_count(source_catalog.get("source_map_only")),
        "typed_trace_redaction_covered": report_redaction.get(
            "typed_trace_redaction_covered"
        ),
    }


def _platform_family_supports(
    ecosystem: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    supports: dict[str, dict[str, Any]] = {}
    for platform_key in PLATFORM_FAMILY_SUPPORT_KEYS:
        platform = _object(ecosystem.get(platform_key))
        family_support = platform.get("family_support")
        if isinstance(family_support, dict):
            supports[platform_key] = family_support
    return supports


def _platform_family_support_family_counts_match(
    platform_family_supports: dict[str, dict[str, Any]],
    root_family_count: Any,
) -> bool:
    if len(platform_family_supports) != len(PLATFORM_FAMILY_SUPPORT_KEYS):
        return False
    return all(
        support.get("family_count") == root_family_count
        for support in platform_family_supports.values()
    )


def _platform_source_catalog_scopes(
    ecosystem: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    scopes: dict[str, dict[str, Any]] = {}
    for platform_key in PLATFORM_SOURCE_CATALOG_SCOPE_KEYS:
        platform = _object(ecosystem.get(platform_key))
        scope = platform.get("source_catalog_scope")
        if isinstance(scope, dict):
            scopes[platform_key] = scope
    return scopes


def _platform_source_catalog_scope_counts_match(
    platform_scopes: dict[str, dict[str, Any]],
    source_catalog_scope: dict[str, Any],
) -> bool:
    if len(platform_scopes) != len(PLATFORM_SOURCE_CATALOG_SCOPE_KEYS):
        return False
    return all(scope == source_catalog_scope for scope in platform_scopes.values())


def _object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _list_count(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _int_value_sum(value: dict[str, Any]) -> int:
    total = 0
    for item in value.values():
        if isinstance(item, int):
            total += item
    return total
