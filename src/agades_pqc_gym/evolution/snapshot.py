from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from agades_pqc_gym.evolution.archive import (
    EVOLUTION_ARCHIVE_SCHEMA,
    EvolutionArchive,
)
from agades_pqc_gym.evolution.scheduler import (
    HELDOUT_REVIEW_LOG_SCHEMA,
    validate_policy_private_path,
)
from agades_pqc_gym.traces.schema import TRACE_RECORD_SCHEMA, TraceRecord

PRIVATE_ARCHIVE_SNAPSHOT_SCHEMA = "agades.pqc.private_archive_snapshot.v1"
ROOT = Path(__file__).resolve().parents[3]


def build_private_archive_snapshot(
    *,
    archive_path: Path,
    source_trace_path: Path,
    review_log_path: Path,
    policy: dict[str, Any],
    root: Path | None = None,
    out: Path | None = None,
    run_id: str | None = None,
    created_at: str = "manual-snapshot-recorded",
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    if out is not None:
        validate_policy_private_path(out, policy=policy, root=project_root)
    validate_policy_private_path(
        review_log_path,
        policy=policy,
        root=project_root,
    )
    _reject_forbidden_public_input(archive_path, policy=policy, root=project_root)
    _reject_forbidden_public_input(source_trace_path, policy=policy, root=project_root)

    resolved_archive_path = _resolve_path(archive_path, project_root)
    resolved_source_trace_path = _resolve_path(source_trace_path, project_root)
    resolved_review_log_path = _resolve_path(review_log_path, project_root)

    archive = _load_archive(resolved_archive_path, archive_path)
    trace_records = _read_trace_records(resolved_source_trace_path, source_trace_path)
    review_log = _load_review_log(resolved_review_log_path, review_log_path)
    required_approvals = _required_approval_gates(policy)
    approved_gates = _approved_review_log_gates(review_log)
    missing_approvals = sorted(set(required_approvals) - set(approved_gates))
    if missing_approvals:
        raise ValueError(
            "private archive snapshot review log lacks required approvals: "
            f"{missing_approvals}"
        )

    trace_ids = {record.trace_id for record in trace_records}
    archive_trace_ids = {
        elite.trace_id for elite in archive.elites
    }
    if archive.global_best is not None:
        archive_trace_ids.add(archive.global_best.trace_id)
    missing_trace_ids = sorted(archive_trace_ids - trace_ids)
    if missing_trace_ids:
        raise ValueError(
            "private archive snapshot archive elite trace links are incomplete"
        )

    retention = _retention_policy(policy)
    execution_safety = _execution_safety(policy)
    snapshot_path = _display_path(out, project_root) if out is not None else None
    artifact_count = 3

    snapshot = {
        "schema_version": PRIVATE_ARCHIVE_SNAPSHOT_SCHEMA,
        "run_id": run_id or f"{archive.run_id}-snapshot",
        "created_at": created_at,
        "snapshot": {
            "path": snapshot_path,
            "private": True,
        },
        "inputs": {
            "archive": _file_reference(
                archive_path,
                resolved_archive_path,
                schema_version=archive.schema_version,
                root=project_root,
            ),
            "source_trace": {
                **_file_reference(
                    source_trace_path,
                    resolved_source_trace_path,
                    schema_version=TRACE_RECORD_SCHEMA,
                    root=project_root,
                ),
                "record_count": len(trace_records),
            },
            "review_log": {
                **_file_reference(
                    review_log_path,
                    resolved_review_log_path,
                    schema_version=review_log["schema_version"],
                    root=project_root,
                ),
                "approval_gates": approved_gates,
            },
        },
        "archive": {
            "run_id": archive.run_id,
            "feature_keys": list(archive.feature_keys),
            "summary": dict(archive.summary),
            "global_best_present": archive.global_best is not None,
        },
        "trace_link_integrity": {
            "archive_elite_count": len(archive.elites),
            "complete": True,
            "missing_trace_count": 0,
            "source_trace_record_count": len(trace_records),
        },
        "retention": {
            "archive_snapshot_max_age_days": retention[
                "archive_snapshot_max_age_days"
            ],
            "delete_expired_private_runs": retention[
                "delete_expired_private_runs"
            ],
            "private_trace_max_age_days": retention["private_trace_max_age_days"],
            "review_log_required": retention["review_log_required"],
        },
        "safety": {
            "arbitrary_code_execution": execution_safety[
                "arbitrary_code_execution"
            ],
            "contains_attack_plans": False,
            "contains_candidate_sources": False,
            "contains_trace_payloads": False,
            "external_network_access": execution_safety["external_network_access"],
            "publishes_private_trace_outputs": execution_safety[
                "publishes_private_trace_outputs"
            ],
            "writes_only_allowed_private_roots": execution_safety[
                "writes_only_allowed_private_roots"
            ],
        },
        "summary": {
            "artifact_count": artifact_count,
            "elite_count": len(archive.elites),
            "private_snapshot": True,
            "public_release_ok": False,
        },
    }
    _validate_snapshot_safety(snapshot)
    return snapshot


def write_private_archive_snapshot(
    out: Path,
    *,
    archive_path: Path,
    source_trace_path: Path,
    review_log_path: Path,
    policy: dict[str, Any],
    root: Path | None = None,
    run_id: str | None = None,
    created_at: str = "manual-snapshot-recorded",
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    snapshot = build_private_archive_snapshot(
        archive_path=archive_path,
        source_trace_path=source_trace_path,
        review_log_path=review_log_path,
        policy=policy,
        root=project_root,
        out=out,
        run_id=run_id,
        created_at=created_at,
    )
    resolved_out = _resolve_path(out, project_root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return snapshot


def _file_reference(
    path: Path,
    resolved_path: Path,
    *,
    schema_version: str,
    root: Path,
) -> dict[str, Any]:
    return {
        "path": _display_path(path, root),
        "schema_version": schema_version,
        "sha256": _sha256_file(resolved_path),
        "size_bytes": resolved_path.stat().st_size,
    }


def _load_archive(resolved_path: Path, original_path: Path) -> EvolutionArchive:
    try:
        archive = EvolutionArchive.model_validate_json(
            resolved_path.read_text(encoding="utf-8")
        )
    except ValidationError as exc:
        raise ValueError(
            f"invalid evolution archive at {original_path}: {exc}"
        ) from exc
    if archive.schema_version != EVOLUTION_ARCHIVE_SCHEMA:
        raise ValueError(
            "private archive snapshot requires evolution archive schema "
            f"{EVOLUTION_ARCHIVE_SCHEMA}"
        )
    return archive


def _read_trace_records(resolved_path: Path, original_path: Path) -> list[TraceRecord]:
    records: list[TraceRecord] = []
    for line_number, raw_line in enumerate(
        resolved_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not raw_line.strip():
            continue
        try:
            records.append(TraceRecord.model_validate_json(raw_line))
        except ValidationError as exc:
            raise ValueError(
                f"invalid trace record at {original_path}:{line_number}: {exc}"
            ) from exc
    return records


def _load_review_log(resolved_path: Path, original_path: Path) -> dict[str, Any]:
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(
            "private archive snapshot review log is not an object: "
            f"{original_path}"
        )
    if payload.get("schema_version") != HELDOUT_REVIEW_LOG_SCHEMA:
        raise ValueError(
            "private archive snapshot requires review log schema "
            f"{HELDOUT_REVIEW_LOG_SCHEMA}"
        )
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("private archive snapshot review log entries must be a list")
    return payload


def _approved_review_log_gates(review_log: dict[str, Any]) -> list[str]:
    approved: list[str] = []
    for entry in review_log["entries"]:
        if not isinstance(entry, dict):
            raise ValueError(
                "private archive snapshot review log entries must be objects"
            )
        if entry.get("decision") != "approved":
            continue
        gate = entry.get("gate")
        if not isinstance(gate, str) or not gate:
            raise ValueError(
                "private archive snapshot review log approval gate must be a string"
            )
        approved.append(gate)
    return sorted(set(approved))


def _required_approval_gates(policy: dict[str, Any]) -> list[str]:
    scheduler_policy = _required_mapping(policy, "scheduler_policy")
    gates = scheduler_policy.get("approval_gates")
    if not isinstance(gates, list) or not all(isinstance(gate, str) for gate in gates):
        raise ValueError("private archive snapshot policy approval gates are invalid")
    return sorted(gates)


def _retention_policy(policy: dict[str, Any]) -> dict[str, Any]:
    scheduler_policy = _required_mapping(policy, "scheduler_policy")
    retention = _required_mapping(scheduler_policy, "retention")
    expected = {
        "archive_snapshot_max_age_days": 90,
        "delete_expired_private_runs": True,
        "private_trace_max_age_days": 30,
        "review_log_required": True,
    }
    if retention != expected:
        raise ValueError("private archive snapshot retention policy is unsupported")
    return retention


def _execution_safety(policy: dict[str, Any]) -> dict[str, Any]:
    scheduler_policy = _required_mapping(policy, "scheduler_policy")
    execution_safety = _required_mapping(scheduler_policy, "execution_safety")
    expected = {
        "arbitrary_code_execution": False,
        "external_network_access": False,
        "publishes_private_trace_outputs": False,
        "writes_only_allowed_private_roots": True,
    }
    if execution_safety != expected:
        raise ValueError("private archive snapshot execution safety is unsupported")
    return execution_safety


def _validate_snapshot_safety(snapshot: dict[str, Any]) -> None:
    safety = snapshot["safety"]
    if safety["arbitrary_code_execution"] is not False:
        raise ValueError("private archive snapshot cannot execute arbitrary code")
    if safety["external_network_access"] is not False:
        raise ValueError("private archive snapshot cannot use external networking")
    if safety["publishes_private_trace_outputs"] is not False:
        raise ValueError("private archive snapshot cannot publish private traces")
    if safety["contains_trace_payloads"] is not False:
        raise ValueError("private archive snapshot cannot contain trace payloads")
    if safety["contains_attack_plans"] is not False:
        raise ValueError("private archive snapshot cannot contain AttackPlans")
    if safety["contains_candidate_sources"] is not False:
        raise ValueError("private archive snapshot cannot contain candidate sources")
    if safety["writes_only_allowed_private_roots"] is not True:
        raise ValueError("private archive snapshot must write only private roots")


def _reject_forbidden_public_input(
    path: Path,
    *,
    policy: dict[str, Any],
    root: Path,
) -> None:
    resolved_path = _resolve_path(path, root)
    forbidden_roots = policy.get("forbidden_public_roots")
    if not isinstance(forbidden_roots, list):
        raise ValueError("private archive snapshot policy public roots are invalid")
    for forbidden_root in forbidden_roots:
        if not isinstance(forbidden_root, str):
            raise ValueError("private archive snapshot public root must be a string")
        if _is_relative_to(resolved_path, (root / forbidden_root).resolve()):
            raise ValueError(
                "private archive snapshot input uses forbidden public input root: "
                f"{path}"
            )


def _required_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"private archive snapshot policy field {key} is invalid")
    return value


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _display_path(path: Path | None, root: Path) -> str | None:
    if path is None:
        return None
    resolved_path = _resolve_path(path, root)
    try:
        return resolved_path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve_path(path: Path, root: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
