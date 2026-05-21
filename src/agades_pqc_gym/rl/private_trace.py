from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from agades_pqc_gym.rl.environment import (
    FORMAL_ARTIFACT_BINDING_SCHEMA,
    RL_REWARD_REPORT_SCHEMA,
    build_formal_artifact_binding,
)
from agades_pqc_gym.rl.pedagogy import PEDAGOGICAL_REWARD_REPORT_SCHEMA
from agades_pqc_gym.utils.hashing import stable_sha256

PRIVATE_PEDAGOGICAL_TRACE_SCHEMA = "agades.pqc.rl.private_pedagogical_trace.v1"
PRIVATE_PEDAGOGICAL_TRACE_VERIFICATION_SCHEMA = (
    "agades.pqc.rl.private_pedagogical_trace_verification.v1"
)
PRIVATE_TRACE_DATASET_CURATION_GATE_SCHEMA = (
    "agades.pqc.rl.private_trace_dataset_curation_gate.v1"
)
PRIVATE_TRACE_DATASET_CURATION_MANIFEST_PATH = "docs/private_dataset_curation.json"
PRIVATE_TRACE_STORAGE_ROOTS = [
    "private/traces/pedagogical_rl",
    "private/datasets/agades_pedagogical_rl",
]
PRIVATE_TRACE_REQUIRED_DATASET_CONTROLS = [
    "license_review",
    "provenance_tracking",
    "deduplication",
    "redaction",
    "contamination_audit",
]
PRIVATE_TRACE_DATASET_PROMOTION_BLOCKERS = [
    "dataset_license_review_complete",
    "dataset_provenance_manifest_complete",
    "dataset_deduplication_report_complete",
    "dataset_redaction_report_complete",
    "dataset_contamination_audit_complete",
]
PRIVATE_TRACE_APPROVED_LICENSE_REVIEW_STATUSES = {
    "approved_private_training",
    "approved_private_training_with_restrictions",
}
PRIVATE_TRACE_REQUIRED_RECORD_FIELDS = [
    "trace_id",
    "task_digest",
    "candidate_digest",
    "reward_report_digest",
    "pedagogical_reward",
    "formal_artifact_binding",
    "dataset_curation_digest",
    "dataset_curation_gate",
    "review_gate",
    "privacy_boundary",
]
PRIVATE_TRACE_FORBIDDEN_PUBLIC_FIELDS = [
    "teacher_prompt",
    "teacher_completion",
    "student_prompt",
    "student_token_logprobs",
    "surprise_gaps",
    "reviewer_annotations",
    "raw_dataset_rows",
]
PRIVATE_TRACE_QUALITY_GATES = [
    "attackplan_schema_valid",
    "formal_artifact_attached",
    "proof_obligations_typed",
    "dataset_license_reviewed",
    "provenance_captured",
    "human_crypto_review_required",
    "publication_boundary_review_required",
]
PRIVATE_TRACE_REVIEW_GATE = {
    "human_crypto_review_required": True,
    "formal_methods_review_required": True,
    "publication_boundary_review_required": True,
    "claim_allowed_without_review": False,
}
PRIVATE_TRACE_PRIVACY_BOUNDARY = {
    "public_release_ok": False,
    "raw_private_signals_included": False,
    "contains_teacher_prompt": False,
    "contains_student_prompt": False,
    "contains_student_token_logprobs": False,
    "contains_raw_dataset_rows": False,
}


def private_pedagogical_trace_contract() -> dict[str, Any]:
    return {
        "schema_version": PRIVATE_PEDAGOGICAL_TRACE_SCHEMA,
        "record_kind": "private_teacher_student_trace",
        "storage_roots": list(PRIVATE_TRACE_STORAGE_ROOTS),
        "public_release_ok": False,
        "raw_private_signals_included": False,
        "required_bindings": {
            "reward_report_schema": RL_REWARD_REPORT_SCHEMA,
            "pedagogical_reward_schema": PEDAGOGICAL_REWARD_REPORT_SCHEMA,
            "formal_artifact_binding_schema": FORMAL_ARTIFACT_BINDING_SCHEMA,
            "dataset_curation_manifest_path": "docs/private_dataset_curation.json",
            "reviewer_governance_manifest_path": "docs/reviewer_governance.json",
            "formal_obligation_ledger_path": "docs/formal_obligation_ledger.json",
        },
        "required_record_fields": list(PRIVATE_TRACE_REQUIRED_RECORD_FIELDS),
        "forbidden_public_fields": list(PRIVATE_TRACE_FORBIDDEN_PUBLIC_FIELDS),
        "quality_gates": list(PRIVATE_TRACE_QUALITY_GATES),
    }


def build_private_pedagogical_trace_record(
    *,
    task: Mapping[str, Any],
    candidate_json: str,
    reward_report: Mapping[str, Any],
    dataset_curation_manifest_path: Path,
) -> dict[str, Any]:
    pedagogical_reward = _mapping_or_error(
        reward_report.get("pedagogical_reward"),
        "reward_report.pedagogical_reward",
    )
    formal_artifact_binding = build_formal_artifact_binding(candidate_json)
    dataset_curation_gate = _dataset_curation_gate(dataset_curation_manifest_path)
    record = {
        "schema_version": PRIVATE_PEDAGOGICAL_TRACE_SCHEMA,
        "record_kind": "private_teacher_student_trace",
        "trace_id": "",
        "task_digest": stable_sha256(dict(task)),
        "candidate_digest": hashlib.sha256(
            candidate_json.encode("utf-8"),
        ).hexdigest(),
        "reward_report_digest": stable_sha256(dict(reward_report)),
        "pedagogical_reward": dict(pedagogical_reward),
        "formal_artifact_binding": formal_artifact_binding,
        "dataset_curation_digest": _file_sha256(dataset_curation_manifest_path),
        "dataset_curation_gate": dataset_curation_gate,
        "review_gate": dict(PRIVATE_TRACE_REVIEW_GATE),
        "privacy_boundary": dict(PRIVATE_TRACE_PRIVACY_BOUNDARY),
        "quality_gates": list(PRIVATE_TRACE_QUALITY_GATES),
    }
    record["trace_id"] = _trace_id(record)
    return record


def verify_private_pedagogical_trace_record(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    if record.get("schema_version") != PRIVATE_PEDAGOGICAL_TRACE_SCHEMA:
        failures.append("Private pedagogical trace schema_version is incorrect.")
    if record.get("record_kind") != "private_teacher_student_trace":
        failures.append("Private pedagogical trace record_kind is incorrect.")

    for field in PRIVATE_TRACE_REQUIRED_RECORD_FIELDS:
        if field not in record:
            failures.append(f"Private pedagogical trace is missing field: {field}.")
    for field in PRIVATE_TRACE_FORBIDDEN_PUBLIC_FIELDS:
        if _contains_exact_key(record, field):
            failures.append(
                f"Private pedagogical trace contains forbidden field: {field}."
            )

    privacy_boundary = _dict_or_empty(record.get("privacy_boundary"))
    if privacy_boundary.get("public_release_ok") is not False:
        failures.append("Private pedagogical trace must not be public-releaseable.")
    if privacy_boundary.get("raw_private_signals_included") is not False:
        failures.append("Private pedagogical trace must not expose raw signals.")

    pedagogical_reward = _dict_or_empty(record.get("pedagogical_reward"))
    if pedagogical_reward.get("schema_version") != PEDAGOGICAL_REWARD_REPORT_SCHEMA:
        failures.append("Private pedagogical trace reward schema is incorrect.")
    if pedagogical_reward.get("raw_private_signals_included") is not False:
        failures.append("Private pedagogical trace reward must be signal-free.")

    formal_artifact_binding = _dict_or_empty(record.get("formal_artifact_binding"))
    if formal_artifact_binding.get("schema_version") != FORMAL_ARTIFACT_BINDING_SCHEMA:
        failures.append("Private pedagogical trace formal binding schema is incorrect.")
    if formal_artifact_binding.get("claim_allowed") is not False:
        failures.append("Private pedagogical trace must not allow claims.")

    dataset_curation_gate = _dict_or_empty(record.get("dataset_curation_gate"))
    _verify_dataset_curation_gate(dataset_curation_gate, failures)

    if record.get("review_gate") != PRIVATE_TRACE_REVIEW_GATE:
        failures.append("Private pedagogical trace review gate is incorrect.")
    if record.get("quality_gates") != PRIVATE_TRACE_QUALITY_GATES:
        failures.append("Private pedagogical trace quality gates are incorrect.")

    for field in (
        "trace_id",
        "task_digest",
        "candidate_digest",
        "reward_report_digest",
        "dataset_curation_digest",
    ):
        if not _is_sha256(record.get(field)):
            failures.append(f"Private pedagogical trace {field} is not a SHA-256.")
    if _is_sha256(record.get("trace_id")) and record.get("trace_id") != _trace_id(
        record,
    ):
        failures.append("Private pedagogical trace trace_id is not synchronized.")

    return {
        "schema_version": PRIVATE_PEDAGOGICAL_TRACE_VERIFICATION_SCHEMA,
        "accepted": not failures,
        "summary": {
            "has_formal_artifact_binding": bool(formal_artifact_binding),
            "has_pedagogical_reward": bool(pedagogical_reward),
            "training_eligible": dataset_curation_gate.get("training_eligible"),
            "public_release_ok": privacy_boundary.get("public_release_ok"),
            "raw_private_signals_included": privacy_boundary.get(
                "raw_private_signals_included",
            ),
            "failure_count": len(failures),
        },
        "failures": failures,
    }


def _dataset_curation_gate(dataset_curation_manifest_path: Path) -> dict[str, Any]:
    curation = _read_json_object(dataset_curation_manifest_path)
    sources = _dict_or_empty(curation.get("sources"))
    source_statuses = {
        source_id: _dict_or_empty(source).get("license_review_status")
        for source_id, source in sorted(sources.items())
    }
    all_sources_license_reviewed = bool(source_statuses) and all(
        status in PRIVATE_TRACE_APPROVED_LICENSE_REVIEW_STATUSES
        for status in source_statuses.values()
    )
    completed_controls = {
        item
        for item in _list_or_empty(_dict_or_empty(curation.get("review")).get(
            "completed_controls"
        ))
        if isinstance(item, str)
    }
    promotion_blockers = [
        blocker
        for control, blocker in zip(
            PRIVATE_TRACE_REQUIRED_DATASET_CONTROLS,
            PRIVATE_TRACE_DATASET_PROMOTION_BLOCKERS,
            strict=True,
        )
        if control not in completed_controls
    ]
    if not all_sources_license_reviewed and (
        "dataset_license_review_complete" not in promotion_blockers
    ):
        promotion_blockers.insert(0, "dataset_license_review_complete")
    training_eligible = (
        all_sources_license_reviewed
        and not promotion_blockers
        and _dict_or_empty(curation.get("review")).get("review_status")
        == "approved_private_training"
    )
    return {
        "schema_version": PRIVATE_TRACE_DATASET_CURATION_GATE_SCHEMA,
        "curation_manifest_path": PRIVATE_TRACE_DATASET_CURATION_MANIFEST_PATH,
        "source_count": len(source_statuses),
        "required_controls": list(PRIVATE_TRACE_REQUIRED_DATASET_CONTROLS),
        "source_license_review_statuses": source_statuses,
        "all_sources_license_reviewed": all_sources_license_reviewed,
        "training_eligible": training_eligible,
        "promotion_blockers": promotion_blockers,
    }


def _verify_dataset_curation_gate(
    gate: dict[str, Any],
    failures: list[str],
) -> None:
    if gate.get("schema_version") != PRIVATE_TRACE_DATASET_CURATION_GATE_SCHEMA:
        failures.append("Private pedagogical trace dataset gate schema is incorrect.")
    if (
        gate.get("curation_manifest_path")
        != PRIVATE_TRACE_DATASET_CURATION_MANIFEST_PATH
    ):
        failures.append(
            "Private pedagogical trace dataset gate manifest path is wrong."
        )
    if gate.get("required_controls") != PRIVATE_TRACE_REQUIRED_DATASET_CONTROLS:
        failures.append("Private pedagogical trace dataset controls are incorrect.")

    source_statuses = _dict_or_empty(gate.get("source_license_review_statuses"))
    if gate.get("source_count") != len(source_statuses) or not source_statuses:
        failures.append(
            "Private pedagogical trace dataset source statuses are invalid."
        )
    all_sources_license_reviewed = bool(source_statuses) and all(
        status in PRIVATE_TRACE_APPROVED_LICENSE_REVIEW_STATUSES
        for status in source_statuses.values()
    )
    if gate.get("all_sources_license_reviewed") is not all_sources_license_reviewed:
        failures.append("Private pedagogical trace dataset review status drifted.")

    promotion_blockers = gate.get("promotion_blockers")
    if not isinstance(promotion_blockers, list) or not all(
        isinstance(item, str) for item in promotion_blockers
    ):
        failures.append("Private pedagogical trace dataset blockers are invalid.")
        promotion_blockers = []
    if gate.get("training_eligible") is True and (
        not all_sources_license_reviewed or promotion_blockers
    ):
        failures.append(
            "Private pedagogical trace dataset gate cannot mark unreviewed "
            "sources training eligible."
        )
    if gate.get("training_eligible") is False and not promotion_blockers:
        failures.append(
            "Private pedagogical trace dataset gate must explain why training "
            "is blocked."
        )


def _trace_id(record: Mapping[str, Any]) -> str:
    material = {
        key: value
        for key, value in record.items()
        if key != "trace_id"
    }
    return stable_sha256(material)


def _mapping_or_error(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _dict_or_empty(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list_or_empty(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _contains_exact_key(value: object, key: str) -> bool:
    if isinstance(value, Mapping):
        return key in value or any(
            _contains_exact_key(child, key) for child in value.values()
        )
    if isinstance(value, list):
        return any(_contains_exact_key(child, key) for child in value)
    return False
