from __future__ import annotations

import json
import shlex
from hashlib import sha256
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.family_support import (
    summarize_family_readiness_matrix,
)
from agades_pqc_gym.integrations.publication_preflight import (
    build_credential_review_queue,
    build_platform_review_matrix,
    build_platform_review_matrix_from_surface_records,
    summarize_platform_review_matrix,
)
from agades_pqc_gym.integrations.release_status import (
    runbook_architecture_evidence_failures,
    summarize_release_status_family_support,
    summarize_release_status_public_private_boundary,
    summarize_release_status_runbook_architecture,
    summarize_release_status_source_catalog_scope,
)

EXTERNAL_PUBLICATION_REVIEW_PACKET_SCHEMA = (
    "agades.pqc.external_publication_review_packet.v1"
)
EXTERNAL_PUBLICATION_REVIEW_PACKET_VERIFICATION_SCHEMA = (
    "agades.pqc.external_publication_review_packet_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PACKET_PATH = Path("docs/external_publication_review_packet.json")
INPUT_PATHS = {
    "huggingface_collection_manifest": Path("hf/collection_manifest.json"),
    "huggingface_publication_handoff": Path(
        "docs/huggingface_publication_handoff.json"
    ),
    "huggingface_space_manifest": Path("hf/space_manifest.json"),
    "nvidia_accelerator_manifest": Path("nvidia/accelerator_manifest.json"),
    "nvidia_publication_handoff": Path("docs/nvidia_publication_handoff.json"),
    "prime_environment_manifest": Path(
        "prime_intellect/verifiers_environment/prime_manifest.json"
    ),
    "prime_publication_handoff": Path("docs/prime_publication_handoff.json"),
    "publication_manifest": Path("docs/publication_manifest.json"),
    "publication_preflight": Path("public/publication_preflight.json"),
    "release_status": Path("docs/release_status.json"),
}
PROJECT = {
    "name": "Agades PQC Gym",
    "package": "agades_pqc_gym",
    "cli": "agades-pqc",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
}
SAFETY = {
    "arbitrary_code_execution": False,
    "claims_external_publication": False,
    "contains_credentials": False,
    "contains_private_traces": False,
    "live_targeting": False,
    "publishes_private_candidates": False,
    "security_claim": False,
}
REQUIRED_BLOCKERS = {
    "credential_review_not_approved",
    "external_release_review_not_approved",
}
REQUIRED_ECOSYSTEM_PLATFORMS = {"hugging_face", "prime_intellect", "nvidia"}


def build_external_publication_review_packet(
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    inputs = {
        key: path.as_posix()
        for key, path in sorted(INPUT_PATHS.items(), key=lambda item: item[0])
    }
    artifacts = {
        key: _read_json(_resolve(project_root, path))
        for key, path in INPUT_PATHS.items()
    }
    publication_manifest = artifacts["publication_manifest"]
    publication_preflight = artifacts["publication_preflight"]
    release_status = artifacts["release_status"]
    ecosystem = _dict_or_empty(release_status.get("ecosystem"))

    packet = {
        "schema_version": EXTERNAL_PUBLICATION_REVIEW_PACKET_SCHEMA,
        "project": PROJECT,
        "inputs": inputs,
        "input_sha256": {
            path.as_posix(): _sha256_file(_resolve(project_root, path))
            for path in sorted(INPUT_PATHS.values(), key=lambda value: value.as_posix())
        },
        "readiness": _readiness(publication_preflight),
        "surface_review_queue": _surface_review_queue(publication_manifest),
        "credential_review_queue": build_credential_review_queue(
            publication_manifest
        ),
        "family_readiness_matrix": _dict_or_empty(
            publication_preflight.get("family_readiness_matrix")
        ),
        "platform_review_matrix": build_platform_review_matrix(
            publication_manifest
        ),
        "publication_dry_run_plan": _publication_dry_run_plan(
            publication_manifest=publication_manifest,
            huggingface_collection=artifacts["huggingface_collection_manifest"],
            huggingface_space=artifacts["huggingface_space_manifest"],
            prime_environment=artifacts["prime_environment_manifest"],
        ),
        "ecosystem_focus": _ecosystem_focus(ecosystem, release_status),
        "review_questions": _review_questions(),
        "safety": dict(SAFETY),
        "release_gates": _release_gates(),
    }
    packet["reviewer_summary"] = _reviewer_summary(packet)
    return packet


def write_external_publication_review_packet(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    packet = build_external_publication_review_packet(root=root)
    resolved_out = _resolve(root or ROOT, out)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return packet


def verify_external_publication_review_packet(
    packet_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    packet = _read_packet(_resolve(project_root, packet_path), failures)

    if packet:
        expected = build_external_publication_review_packet(root=project_root)
        if packet != expected:
            failures.append("External publication review packet is not in sync.")
        _verify_schema(packet, failures)
        _verify_project(packet, failures)
        _verify_inputs(packet, project_root, failures)
        _verify_readiness(packet, project_root, failures)
        _verify_surface_queue(packet, failures)
        _verify_credential_review_queue(packet, failures)
        _verify_family_readiness_matrix(packet, project_root, failures)
        _verify_platform_review_matrix(packet, failures)
        _verify_reviewer_summary(packet, failures)
        _verify_publication_dry_run_plan(packet, project_root, failures)
        _verify_ecosystem_focus(packet, failures)
        _verify_safety(packet, failures)
        _verify_release_gates(packet, failures)

    summary = _summary(packet, failures)
    return {
        "schema_version": EXTERNAL_PUBLICATION_REVIEW_PACKET_VERIFICATION_SCHEMA,
        "packet_path": packet_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _readiness(publication_preflight: dict[str, Any]) -> dict[str, Any]:
    publication = _dict_or_empty(publication_preflight.get("publication"))
    review_state = _dict_or_empty(publication_preflight.get("review_state"))
    blockers = _id_list(publication_preflight.get("blockers"))
    warning_records = _list_or_empty(publication_preflight.get("warnings"))
    warnings = _id_list(warning_records)
    return {
        "local_artifacts_ready": publication_preflight.get("local_artifacts_ready"),
        "ready_for_external_publication": publication_preflight.get(
            "ready_for_external_publication"
        ),
        "external_release_review_approved": review_state.get(
            "external_release_review_approved"
        ),
        "credentials_reviewed": review_state.get("credentials_reviewed"),
        "blocker_ids": blockers,
        "warning_ids": warnings,
        "warning_evidence": _warning_evidence_by_id(warning_records),
        "credentialed_surface_count": len(
            _list_or_empty(publication.get("credentialed_surfaces"))
        ),
        "review_required_surface_count": publication.get(
            "review_required_surfaces"
        ),
    }


def _warning_evidence_by_id(warning_records: list[Any]) -> dict[str, dict[str, Any]]:
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for record in warning_records:
        if not isinstance(record, dict):
            continue
        warning_id = record.get("id")
        if not isinstance(warning_id, str) or not warning_id:
            continue
        evidence_by_id[warning_id] = _dict_or_empty(record.get("evidence"))
    return dict(sorted(evidence_by_id.items()))


def _surface_review_queue(
    publication_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for surface in publication_manifest.get("surfaces", []):
        if not isinstance(surface, dict):
            continue
        entries.append(
            {
                "id": surface.get("id"),
                "platform": surface.get("platform"),
                "publication_status": surface.get("publication_status"),
                "requires_credentials": surface.get("requires_credentials"),
                "review_required_before_publish": surface.get(
                    "review_required_before_publish"
                ),
                "artifact_count": len(_list_or_empty(surface.get("artifact_paths"))),
                "smoke_gate": surface.get("smoke_gate"),
            }
        )
    return sorted(entries, key=lambda entry: str(entry["id"]))


def _publication_dry_run_plan(
    *,
    publication_manifest: dict[str, Any],
    huggingface_collection: dict[str, Any],
    huggingface_space: dict[str, Any],
    prime_environment: dict[str, Any],
) -> list[dict[str, Any]]:
    surfaces = {
        surface["id"]: surface
        for surface in publication_manifest.get("surfaces", [])
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }
    hf_entries = {
        entry["id"]: entry
        for entry in huggingface_collection.get("entries", [])
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    dataset = _dict_or_empty(hf_entries.get("huggingface-dataset"))
    space = _dict_or_empty(huggingface_space.get("space"))
    prime = _dict_or_empty(prime_environment.get("prime"))

    dataset_repo_id = _owner_template_repo_id(
        str(dataset.get("suggested_repo_id", "agades/pqc-gym-toy"))
    )
    dataset_repo_type = str(dataset.get("repo_type", "dataset"))
    dataset_local_path = str(dataset.get("local_path", "hf/dataset"))

    entries = [
        {
            "artifact_count": _surface_artifact_count(
                surfaces,
                "huggingface-collection",
            ),
            "command_templates": [],
            "contains_credentials": False,
            "external_publication_performed": False,
            "external_url_recorded": False,
            "first_publication_target": "private_or_draft_review_surface",
            "id": "huggingface-collection",
            "manual_review_action": (
                "Create or update the Hugging Face Collection from "
                "hf/collection_manifest.json only after dataset and Space "
                "private review pass."
            ),
            "platform": "hugging_face",
            "review_required_before_publish": True,
            "source_manifest": "hf/collection_manifest.json",
        },
        {
            "artifact_count": _surface_artifact_count(
                surfaces,
                "huggingface-dataset",
            ),
            "command_templates": [
                (
                    f"hf repos create {dataset_repo_id} --type={dataset_repo_type} "
                    "--private --exist-ok"
                ),
                (
                    f"hf upload {dataset_repo_id} {dataset_local_path} . "
                    f"--repo-type={dataset_repo_type} --commit-message "
                    '"Sync Agades PQC Gym Dataset"'
                ),
            ],
            "contains_credentials": False,
            "external_publication_performed": False,
            "external_url_recorded": False,
            "first_publication_target": "private_or_draft_review_surface",
            "id": "huggingface-dataset",
            "manual_review_action": None,
            "platform": "hugging_face",
            "review_required_before_publish": True,
            "source_manifest": "hf/dataset/dataset_info.json",
        },
        {
            "artifact_count": _surface_artifact_count(
                surfaces,
                "huggingface-space",
            ),
            "command_templates": [
                str(space.get("hub_create_command_template")),
                str(space.get("hub_upload_command_template")),
            ],
            "contains_credentials": False,
            "external_publication_performed": False,
            "external_url_recorded": False,
            "first_publication_target": "private_or_draft_review_surface",
            "id": "huggingface-space",
            "manual_review_action": None,
            "platform": "hugging_face",
            "review_required_before_publish": True,
            "source_manifest": "hf/space_manifest.json",
        },
        {
            "artifact_count": _surface_artifact_count(
                surfaces,
                "prime-verifiers-environment",
            ),
            "command_templates": [
                str(prime.get("hub_private_push_command")),
            ],
            "contains_credentials": False,
            "external_publication_performed": False,
            "external_url_recorded": False,
            "first_publication_target": "private_or_draft_review_surface",
            "id": "prime-verifiers-environment",
            "manual_review_action": None,
            "platform": "prime_intellect",
            "review_required_before_publish": True,
            "source_manifest": (
                "prime_intellect/verifiers_environment/prime_manifest.json"
            ),
        },
    ]
    return sorted(entries, key=lambda entry: str(entry["id"]))


def _surface_artifact_count(
    surfaces: dict[str, dict[str, Any]],
    surface_id: str,
) -> int:
    surface = _dict_or_empty(surfaces.get(surface_id))
    return len(_list_or_empty(surface.get("artifact_paths")))


def _owner_template_repo_id(repo_id: str) -> str:
    parts = repo_id.split("/", 1)
    if len(parts) != 2:
        return repo_id
    return f"<owner>/{parts[1]}"


def _ecosystem_focus(
    ecosystem: dict[str, Any],
    release_status: dict[str, Any],
) -> dict[str, Any]:
    huggingface_collection = _dict_or_empty(ecosystem.get("huggingface_collection"))
    huggingface_dataset = _dict_or_empty(ecosystem.get("huggingface_dataset"))
    huggingface_space = _dict_or_empty(ecosystem.get("huggingface_space"))
    prime = _dict_or_empty(ecosystem.get("prime_intellect"))
    release_plans = _dict_or_empty(ecosystem.get("release_plans"))
    nvidia = _dict_or_empty(ecosystem.get("nvidia"))
    return {
        "hugging_face": {
            "collection_entries": huggingface_collection.get("entry_count"),
            "dataset_valid_attack_plan_rows": huggingface_dataset.get(
                "valid_attack_plan_count"
            ),
            "space_examples": huggingface_space.get("example_count"),
        },
        "prime_intellect": {
            "environment_task_count": prime.get("task_count"),
            "family_count": prime.get("family_count"),
            "prime_hub_publication_performed": prime.get(
                "prime_hub_publication_performed"
            ),
            "source_anchors": sorted(
                _list_or_empty(release_plans.get("prime_ecosystem_anchors"))
            ),
        },
        "nvidia": {
            "current_gpu_required_workload_count": nvidia.get(
                "current_gpu_required_workload_count"
            ),
            "gpu_future_workload_count": nvidia.get("gpu_future_workload_count"),
            "workload_count": nvidia.get("workload_count"),
        },
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
    }


def _review_questions() -> list[str]:
    return [
        "Confirm external release review approval before publishing any surface.",
        "Confirm credentials and target namespaces for Hugging Face and Prime.",
        "Review every public card for no private traces and no security claims.",
        (
            "Publish credentialed surfaces as draft, private, or unlisted first "
            "when supported."
        ),
        "Record external URLs only after the publication review accepts them.",
    ]


def _release_gates() -> list[str]:
    return [
        "uv run agades-pqc external-publication-review-packet --out "
        "docs/external_publication_review_packet.json",
        "uv run agades-pqc external-publication-review-packet-verify --packet "
        "docs/external_publication_review_packet.json",
        "uv run agades-pqc publication-preflight-verify --preflight "
        "public/publication_preflight.json",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc hf-publication-handoff-verify --handoff "
        "docs/huggingface_publication_handoff.json",
        "uv run agades-pqc prime-publication-handoff-verify --handoff "
        "docs/prime_publication_handoff.json",
        "uv run agades-pqc nvidia-publication-handoff-verify --handoff "
        "docs/nvidia_publication_handoff.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]


def _verify_schema(packet: dict[str, Any], failures: list[str]) -> None:
    if packet.get("schema_version") != EXTERNAL_PUBLICATION_REVIEW_PACKET_SCHEMA:
        failures.append(
            "External publication review packet schema_version must be "
            f"{EXTERNAL_PUBLICATION_REVIEW_PACKET_SCHEMA}."
        )


def _verify_project(packet: dict[str, Any], failures: list[str]) -> None:
    if packet.get("project") != PROJECT:
        failures.append("External publication review packet project drifted.")


def _verify_inputs(
    packet: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    expected_inputs = {
        key: path.as_posix()
        for key, path in sorted(INPUT_PATHS.items(), key=lambda item: item[0])
    }
    if packet.get("inputs") != expected_inputs:
        failures.append("External publication review packet inputs drifted.")
    digests = _dict_or_empty(packet.get("input_sha256"))
    for path in INPUT_PATHS.values():
        path_text = path.as_posix()
        if digests.get(path_text) != _sha256_file(_resolve(root, path)):
            failures.append(
                "External publication review packet input digest drifted: "
                f"{path_text}."
            )


def _verify_readiness(
    packet: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    readiness = _dict_or_empty(packet.get("readiness"))
    if readiness.get("ready_for_external_publication") is not False:
        failures.append(
            "External publication review packet must remain blocked by default."
        )
    if readiness.get("external_release_review_approved") is not False:
        failures.append(
            "External publication review packet must not mark release review approved."
        )
    if readiness.get("credentials_reviewed") is not False:
        failures.append(
            "External publication review packet must not mark credentials reviewed."
        )
    blocker_ids = set(_list_or_empty(readiness.get("blocker_ids")))
    if not blocker_ids >= REQUIRED_BLOCKERS:
        failures.append(
            "External publication review packet lacks credential/review blockers."
        )
    warning_ids = _list_or_empty(readiness.get("warning_ids"))
    warning_evidence = _dict_or_empty(readiness.get("warning_evidence"))
    if any(
        not _dict_or_empty(warning_evidence.get(str(warning_id)))
        for warning_id in warning_ids
    ):
        failures.append(
            "External publication review packet warning evidence must cover every "
            "warning id."
        )
    publication_preflight = _read_json(
        _resolve(root, INPUT_PATHS["publication_preflight"])
    )
    expected_warning_evidence = _warning_evidence_by_id(
        _list_or_empty(publication_preflight.get("warnings"))
    )
    if (
        warning_ids == sorted(expected_warning_evidence)
        and len(warning_evidence) == len(expected_warning_evidence)
        and _warning_evidence_items(readiness) == len(expected_warning_evidence)
        and warning_evidence != expected_warning_evidence
    ):
        failures.append(
            "External publication review packet warning evidence is inconsistent "
            "with publication preflight."
        )


def _verify_surface_queue(packet: dict[str, Any], failures: list[str]) -> None:
    queue = packet.get("surface_review_queue")
    if not isinstance(queue, list) or not queue:
        failures.append("External publication review packet surface queue is empty.")
        return
    platforms = {
        entry.get("platform")
        for entry in queue
        if isinstance(entry, dict) and entry.get("platform")
    }
    missing = sorted(REQUIRED_ECOSYSTEM_PLATFORMS - platforms)
    if missing:
        failures.append(
            "External publication review packet is missing ecosystem platforms: "
            f"{missing}."
        )
    for entry in queue:
        if not isinstance(entry, dict):
            failures.append(
                "External publication review packet surface entry is invalid."
            )
            continue
        if entry.get("review_required_before_publish") is not True:
            failures.append(
                "External publication review packet surface lacks review gate: "
                f"{entry.get('id')}."
            )


def _verify_credential_review_queue(
    packet: dict[str, Any],
    failures: list[str],
) -> None:
    if not _credential_review_queue_complete(packet):
        failures.append(
            "External publication review packet credential queue must cover every "
            "credentialed surface."
        )
    queue = _list_or_empty(packet.get("credential_review_queue"))
    if _credential_material_included(queue):
        failures.append(
            "External publication review packet credential queue must not include "
            "credential material."
        )
    if any(
        isinstance(entry, dict)
        and entry.get("first_publication_target")
        != "private_or_draft_review_surface"
        for entry in queue
    ):
        failures.append(
            "External publication review packet credential queue must target "
            "private or draft review surfaces first."
        )
    if any(
        isinstance(entry, dict)
        and entry.get("review_required_before_publish") is not True
        for entry in queue
    ):
        failures.append(
            "External publication review packet credential queue must keep "
            "review gates."
        )


def _verify_publication_dry_run_plan(
    packet: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    if not _publication_dry_run_plan_complete(packet):
        failures.append(
            "External publication review packet dry-run plan must cover every "
            "credentialed surface."
        )
    plan = _list_or_empty(packet.get("publication_dry_run_plan"))
    if _publication_dry_run_contains_credentials(plan):
        failures.append(
            "External publication review packet dry-run plan must not contain "
            "credential material."
        )
    if _publication_dry_run_external_publication_performed(plan):
        failures.append(
            "External publication review packet dry-run plan must not claim "
            "external publication."
        )
    if not _publication_dry_run_private_first(plan):
        failures.append(
            "External publication review packet dry-run plan must keep private "
            "or draft first-publication commands."
        )
    _verify_publication_dry_run_source_manifests(packet, root, failures)
    if any(
        isinstance(entry, dict)
        and not _list_or_empty(entry.get("command_templates"))
        and not isinstance(entry.get("manual_review_action"), str)
        for entry in plan
    ):
        failures.append(
            "External publication review packet dry-run plan entries must have "
            "commands or a manual review action."
        )


def _verify_publication_dry_run_source_manifests(
    packet: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    publication_manifest = _read_json(
        _resolve(root, INPUT_PATHS["publication_manifest"])
    )
    surface_artifacts = {
        str(surface["id"]): {
            str(path)
            for path in _list_or_empty(surface.get("artifact_paths"))
            if isinstance(path, str)
        }
        for surface in _list_or_empty(publication_manifest.get("surfaces"))
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }
    for entry in _list_or_empty(packet.get("publication_dry_run_plan")):
        if not isinstance(entry, dict):
            continue
        surface_id = str(entry.get("id"))
        source_manifest = entry.get("source_manifest")
        if not isinstance(source_manifest, str) or not source_manifest:
            failures.append(
                "External publication review packet dry-run source_manifest "
                f"is missing: {surface_id}."
            )
            continue
        if source_manifest not in surface_artifacts.get(surface_id, set()):
            failures.append(
                "External publication review packet dry-run source_manifest is "
                f"not one of the surface artifacts: {surface_id}."
            )
            continue
        if not _resolve(root, Path(source_manifest)).is_file():
            failures.append(
                "External publication review packet dry-run source_manifest "
                f"is missing on disk: {source_manifest}."
            )


def _verify_family_readiness_matrix(
    packet: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    matrix = _dict_or_empty(packet.get("family_readiness_matrix"))
    publication_preflight = _read_json(
        _resolve(root, INPUT_PATHS["publication_preflight"])
    )
    expected = _dict_or_empty(publication_preflight.get("family_readiness_matrix"))
    if matrix != expected:
        failures.append(
            "External publication review packet family readiness matrix is "
            "inconsistent with publication preflight."
        )
        return

    summary = summarize_family_readiness_matrix(matrix)
    if summary["non_lattice_lattice_estimator_families"]:
        failures.append(
            "External publication review packet family readiness matrix must not "
            "enable Lattice Estimator for non-LWE/MLWE families."
        )
    if summary["schema_only_default_estimator_families"]:
        failures.append(
            "External publication review packet family readiness matrix must not "
            "assign default estimators to schema-only families."
        )
    if summary["review_required_families"] != summary["family_count"]:
        failures.append(
            "External publication review packet family readiness matrix must keep "
            "review gates for every family."
        )


def _verify_platform_review_matrix(
    packet: dict[str, Any],
    failures: list[str],
) -> None:
    matrix = _dict_or_empty(packet.get("platform_review_matrix"))
    expected = build_platform_review_matrix_from_surface_records(
        _list_or_empty(packet.get("surface_review_queue"))
    )
    if matrix != expected:
        failures.append(
            "External publication review packet platform review matrix is "
            "inconsistent with surface queue."
        )
        return
    if any(
        entry.get("review_required_surface_count") != entry.get("surface_count")
        for entry in matrix.values()
        if isinstance(entry, dict)
    ):
        failures.append(
            "External publication review packet platform review matrix must keep "
            "review gates for every surface."
        )


def _verify_reviewer_summary(
    packet: dict[str, Any],
    failures: list[str],
) -> None:
    if packet.get("reviewer_summary") != _reviewer_summary(packet):
        failures.append(
            "External publication review packet reviewer summary is inconsistent "
            "with packet evidence."
        )


def _verify_ecosystem_focus(packet: dict[str, Any], failures: list[str]) -> None:
    focus = _dict_or_empty(packet.get("ecosystem_focus"))
    prime = _dict_or_empty(focus.get("prime_intellect"))
    nvidia = _dict_or_empty(focus.get("nvidia"))
    family_support = _dict_or_empty(focus.get("family_support"))
    source_catalog_scope = _dict_or_empty(focus.get("source_catalog_scope"))
    public_private_boundary = _dict_or_empty(focus.get("public_private_boundary"))
    runbook_architecture = _dict_or_empty(focus.get("runbook_architecture"))
    redaction = _dict_or_empty(
        public_private_boundary.get("report_generator_redaction")
    )
    if prime.get("prime_hub_publication_performed") is not False:
        failures.append(
            "External publication review packet must not claim Prime publication."
        )
    if nvidia.get("current_gpu_required_workload_count") != 0:
        failures.append(
            "External publication review packet must not claim current GPU requirement."
        )
    if family_support.get("review_required_before_claims") is not True:
        failures.append(
            "External publication review packet must keep family-support review gate."
        )
    platform_support = _dict_or_empty(family_support.get("platform_support"))
    if (
        platform_support.get("family_counts_match") is not True
        or platform_support.get("missing_claim_review_gate") != []
    ):
        failures.append(
            "External publication review packet platform family-support gates "
            "are incomplete."
        )
    _verify_source_catalog_scope(source_catalog_scope, failures)
    if redaction.get("typed_trace_redaction_covered") is not True:
        failures.append(
            "External publication review packet typed TraceRecord redaction gate "
            "is incomplete."
        )
    if redaction.get("raw_mapping_redaction_covered") is not True:
        failures.append(
            "External publication review packet raw trace mapping redaction gate "
            "is incomplete."
        )
    if redaction.get("redacted_records") != 2:
        failures.append(
            "External publication review packet report redaction gate must cover "
            "two private input shapes."
        )
    failures.extend(
        runbook_architecture_evidence_failures(
            runbook_architecture,
            subject="External publication review packet",
        )
    )


def _verify_source_catalog_scope(
    source_catalog_scope: dict[str, Any],
    failures: list[str],
) -> None:
    if source_catalog_scope.get("non_lattice_toy_operator_security_claims") != 0:
        failures.append(
            "External publication review packet source catalog scope must not "
            "contain non-lattice toy security claims."
        )
    if source_catalog_scope.get("non_lattice_toy_evaluator_count") != (
        source_catalog_scope.get("source_count")
    ):
        failures.append(
            "External publication review packet source catalog scope must cover "
            "every source."
        )
    if source_catalog_scope.get("non_lattice_toy_operator_variant_count") != (
        source_catalog_scope.get("source_count")
    ):
        failures.append(
            "External publication review packet source catalog operator scope "
            "must cover every source."
        )
    platform_counts_match = source_catalog_scope.get(
        "platform_source_catalog_scope_counts_match"
    )
    if platform_counts_match is not True:
        failures.append(
            "External publication review packet platform source catalog scope "
            "must match source catalog scope."
        )
    if source_catalog_scope.get("platform_source_catalog_scope_security_claims") != 0:
        failures.append(
            "External publication review packet platform source catalog scope must "
            "not contain non-lattice toy security claims."
        )
    if source_catalog_scope.get("platform_source_catalog_scope_surfaces") != 3:
        failures.append(
            "External publication review packet platform source catalog scope must "
            "cover Prime, Hugging Face, and NVIDIA surfaces."
        )


def _verify_safety(packet: dict[str, Any], failures: list[str]) -> None:
    safety = _dict_or_empty(packet.get("safety"))
    if safety != SAFETY:
        failures.append("External publication review packet safety drifted.")
    if safety.get("claims_external_publication") is not False:
        failures.append(
            "External publication review packet must not claim publication."
        )
    if safety.get("contains_credentials") is not False:
        failures.append(
            "External publication review packet must not include credentials."
        )
    if safety.get("security_claim") is not False:
        failures.append(
            "External publication review packet must not make security claims."
        )


def _verify_release_gates(packet: dict[str, Any], failures: list[str]) -> None:
    if packet.get("release_gates") != _release_gates():
        failures.append("External publication review packet release gates drifted.")


def _summary(packet: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    readiness = _dict_or_empty(packet.get("readiness"))
    focus = _dict_or_empty(packet.get("ecosystem_focus"))
    family_support = _dict_or_empty(focus.get("family_support"))
    platform_support = _dict_or_empty(family_support.get("platform_support"))
    source_catalog_scope = _dict_or_empty(focus.get("source_catalog_scope"))
    public_private_boundary = _dict_or_empty(focus.get("public_private_boundary"))
    runbook_architecture = _dict_or_empty(focus.get("runbook_architecture"))
    redaction = _dict_or_empty(
        public_private_boundary.get("report_generator_redaction")
    )
    credential_review_queue = _list_or_empty(
        packet.get("credential_review_queue")
    )
    family_readiness_summary = summarize_family_readiness_matrix(
        _dict_or_empty(packet.get("family_readiness_matrix"))
    )
    publication_dry_run_plan = _list_or_empty(
        packet.get("publication_dry_run_plan")
    )
    platform_review_summary = summarize_platform_review_matrix(
        _dict_or_empty(packet.get("platform_review_matrix"))
    )
    queue = packet.get("surface_review_queue")
    return {
        "blockers": len(_list_or_empty(readiness.get("blocker_ids"))),
        "credential_material_included": _credential_material_included(
            credential_review_queue
        ),
        "credential_review_queue_complete": _credential_review_queue_complete(
            packet
        ),
        "credential_review_queue_items": len(credential_review_queue),
        "credentialed_surface_count": readiness.get("credentialed_surface_count"),
        "families_with_future_reviewed_adapters": len(
            _list_or_empty(family_support.get("families_with_future_reviewed_adapters"))
        ),
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
        "reviewer_summary_synced": packet.get("reviewer_summary")
        == _reviewer_summary(packet),
        "future_reviewed_adapter_sources_by_family": family_support.get(
            "future_reviewed_adapter_sources_by_family"
        ),
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
        "publication_dry_run_commands": sum(
            len(_list_or_empty(entry.get("command_templates")))
            for entry in publication_dry_run_plan
            if isinstance(entry, dict)
        ),
        "publication_dry_run_contains_credentials": (
            _publication_dry_run_contains_credentials(publication_dry_run_plan)
        ),
        "publication_dry_run_entries": len(publication_dry_run_plan),
        "publication_dry_run_external_publication_performed": (
            _publication_dry_run_external_publication_performed(
                publication_dry_run_plan
            )
        ),
        "publication_dry_run_manual_entries": sum(
            1
            for entry in publication_dry_run_plan
            if isinstance(entry, dict)
            and isinstance(entry.get("manual_review_action"), str)
        ),
        "publication_dry_run_private_first": _publication_dry_run_private_first(
            publication_dry_run_plan
        ),
        "raw_mapping_redaction_covered": redaction.get(
            "raw_mapping_redaction_covered"
        ),
        "ready_for_external_publication": readiness.get(
            "ready_for_external_publication"
        ),
        "report_redaction_records": redaction.get("redacted_records"),
        "review_required_before_claims": family_support.get(
            "review_required_before_claims"
        ),
        "review_required_surface_count": readiness.get(
            "review_required_surface_count"
        ),
        "surface_count": len(queue) if isinstance(queue, list) else 0,
        "typed_trace_redaction_covered": redaction.get(
            "typed_trace_redaction_covered"
        ),
        "warnings": len(_list_or_empty(readiness.get("warning_ids"))),
        "warning_evidence_items": _warning_evidence_items(readiness),
    }


def _reviewer_summary(packet: dict[str, Any]) -> dict[str, Any]:
    readiness = _dict_or_empty(packet.get("readiness"))
    focus = _dict_or_empty(packet.get("ecosystem_focus"))
    family_support = _dict_or_empty(focus.get("family_support"))
    platform_support = _dict_or_empty(family_support.get("platform_support"))
    source_catalog_scope = _dict_or_empty(focus.get("source_catalog_scope"))
    safety = _dict_or_empty(packet.get("safety"))
    family_readiness = _dict_or_empty(packet.get("family_readiness_matrix"))
    family_readiness_summary = summarize_family_readiness_matrix(family_readiness)
    platform_review_matrix = _dict_or_empty(packet.get("platform_review_matrix"))
    platform_review_summary = summarize_platform_review_matrix(platform_review_matrix)
    publication_dry_run_plan = _list_or_empty(packet.get("publication_dry_run_plan"))

    return {
        "blockers": len(_list_or_empty(readiness.get("blocker_ids"))),
        "claims_external_publication": safety.get("claims_external_publication"),
        "contains_credentials": safety.get("contains_credentials"),
        "contains_private_traces": safety.get("contains_private_traces"),
        "credential_review_queue_items": len(
            _list_or_empty(packet.get("credential_review_queue"))
        ),
        "credentialed_surface_count": readiness.get("credentialed_surface_count"),
        "family_count": family_readiness_summary["family_count"],
        "family_readiness_lattice_estimator_families": len(
            family_readiness_summary["lattice_estimator_families"]
        ),
        "family_readiness_non_lattice_lattice_estimator_families": len(
            family_readiness_summary["non_lattice_lattice_estimator_families"]
        ),
        "implemented_family_count": _support_level_count(
            family_readiness,
            "implemented",
        ),
        "non_lattice_toy_operator_security_claims": (
            source_catalog_scope.get("non_lattice_toy_operator_security_claims")
        ),
        "platform_count": len(platform_review_matrix),
        "platform_review_matrix_credentialed_surfaces": (
            platform_review_summary["credentialed_surfaces"]
        ),
        "platform_review_matrix_review_required_surfaces": (
            platform_review_summary["review_required_surfaces"]
        ),
        "platform_review_matrix_surfaces": platform_review_summary["surfaces"],
        "platforms_with_family_claim_review_gate": len(
            _list_or_empty(platform_support.get("platforms_with_claim_review_gate"))
        ),
        "publication_dry_run_commands": sum(
            len(_list_or_empty(entry.get("command_templates")))
            for entry in publication_dry_run_plan
            if isinstance(entry, dict)
        ),
        "publication_dry_run_entries": len(publication_dry_run_plan),
        "publication_dry_run_private_first": _publication_dry_run_private_first(
            publication_dry_run_plan
        ),
        "ready_for_external_publication": readiness.get(
            "ready_for_external_publication"
        ),
        "review_required_surface_count": readiness.get(
            "review_required_surface_count"
        ),
        "schema_only_family_count": _support_level_count(
            family_readiness,
            "schema_only",
        ),
        "security_claim": safety.get("security_claim"),
        "surface_count": len(_list_or_empty(packet.get("surface_review_queue"))),
        "toy_evaluator_family_count": _support_level_count(
            family_readiness,
            "toy_evaluator",
        ),
        "warning_evidence_items": _warning_evidence_items(readiness),
        "warnings": len(_list_or_empty(readiness.get("warning_ids"))),
    }


def _support_level_count(matrix: dict[str, Any], support_level: str) -> int:
    return sum(
        1
        for entry in matrix.values()
        if isinstance(entry, dict) and entry.get("support_level") == support_level
    )


def _warning_evidence_items(readiness: dict[str, Any]) -> int:
    warning_ids = _list_or_empty(readiness.get("warning_ids"))
    warning_evidence = _dict_or_empty(readiness.get("warning_evidence"))
    return sum(
        1
        for warning_id in warning_ids
        if _dict_or_empty(warning_evidence.get(str(warning_id)))
    )


def _credential_review_queue_complete(packet: dict[str, Any]) -> bool:
    surface_queue = _list_or_empty(packet.get("surface_review_queue"))
    expected_ids = sorted(
        str(entry["id"])
        for entry in surface_queue
        if isinstance(entry, dict)
        and entry.get("requires_credentials") is True
        and isinstance(entry.get("id"), str)
    )
    credential_queue = _list_or_empty(packet.get("credential_review_queue"))
    queue_ids = sorted(
        str(entry["id"])
        for entry in credential_queue
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    )
    if queue_ids != expected_ids:
        return False
    return all(
        isinstance(entry, dict)
        and entry.get("first_publication_target")
        == "private_or_draft_review_surface"
        and entry.get("review_required_before_publish") is True
        for entry in credential_queue
    )


def _credential_material_included(queue: list[Any]) -> bool:
    return any(
        isinstance(entry, dict)
        and entry.get("credential_material_included") is not False
        for entry in queue
    )


def _publication_dry_run_plan_complete(packet: dict[str, Any]) -> bool:
    credential_queue = _list_or_empty(packet.get("credential_review_queue"))
    expected_ids = sorted(
        str(entry["id"])
        for entry in credential_queue
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    )
    plan = _list_or_empty(packet.get("publication_dry_run_plan"))
    plan_ids = sorted(
        str(entry["id"])
        for entry in plan
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    )
    if plan_ids != expected_ids:
        return False
    return all(
        isinstance(entry, dict)
        and entry.get("review_required_before_publish") is True
        and entry.get("contains_credentials") is False
        and entry.get("external_publication_performed") is False
        and entry.get("external_url_recorded") is False
        for entry in plan
    )


def _publication_dry_run_contains_credentials(plan: list[Any]) -> bool:
    secret_markers = (
        "HF_TOKEN",
        "PRIME_API_KEY",
        "NVIDIA_API_KEY",
        "TOKEN=",
        "API_KEY=",
        "SECRET=",
    )
    for entry in plan:
        if not isinstance(entry, dict):
            return True
        if entry.get("contains_credentials") is not False:
            return True
        for command in _list_or_empty(entry.get("command_templates")):
            if not isinstance(command, str):
                return True
            if any(marker in command for marker in secret_markers):
                return True
    return False


def _publication_dry_run_external_publication_performed(plan: list[Any]) -> bool:
    return any(
        isinstance(entry, dict)
        and (
            entry.get("external_publication_performed") is not False
            or entry.get("external_url_recorded") is not False
        )
        for entry in plan
    )


def _publication_dry_run_private_first(plan: list[Any]) -> bool:
    if not plan:
        return False
    return all(
        isinstance(entry, dict)
        and entry.get("first_publication_target")
        == "private_or_draft_review_surface"
        and all(
            _command_keeps_private_or_draft_first(command)
            for command in _list_or_empty(entry.get("command_templates"))
            if isinstance(command, str)
        )
        for entry in plan
    )


def _command_keeps_private_or_draft_first(command: str) -> bool:
    if not command.strip() or command.strip().lower() == "none":
        return False
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    lower_tokens = [token.lower() for token in tokens]
    if _command_has_visibility_marker(lower_tokens, "public"):
        return False
    if _command_controls_first_publication_visibility(lower_tokens):
        return _command_has_private_or_draft_marker(lower_tokens)
    return True


def _command_controls_first_publication_visibility(tokens: list[str]) -> bool:
    return tokens[:3] in (
        ["hf", "repos", "create"],
        ["prime", "env", "push"],
    )


def _command_has_private_or_draft_marker(tokens: list[str]) -> bool:
    return (
        "--private" in tokens
        or "--draft" in tokens
        or _command_has_visibility_marker(tokens, "private")
        or _command_has_visibility_marker(tokens, "draft")
    )


def _command_has_visibility_marker(tokens: list[str], value: str) -> bool:
    expected = value.lower()
    return any(
        token in {f"--visibility={expected}", f"visibility={expected}"}
        or (
            token in {"--visibility", "visibility"}
            and index + 1 < len(tokens)
            and tokens[index + 1] == expected
        )
        for index, token in enumerate(tokens)
    )


def _read_packet(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(
            f"External publication review packet is missing: {path.as_posix()}."
        )
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            "External publication review packet is invalid JSON at line "
            f"{exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("External publication review packet must be a JSON object.")
        return {}
    return payload


def _id_list(value: Any) -> list[str]:
    return sorted(
        str(item["id"])
        for item in _list_or_empty(value)
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    )


def _list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return payload


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()
