from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path, PurePath
from typing import Any

from pydantic import ValidationError

from agades_pqc_gym.evolution.rescore import HELDOUT_RESCORE_SCHEMA
from agades_pqc_gym.evolution.scheduler import (
    HELDOUT_SCHEDULE_SCHEMA,
    validate_heldout_schedule,
    validate_policy_private_path,
)
from agades_pqc_gym.traces.schema import TRACE_RECORD_SCHEMA, TraceRecord

HELDOUT_REVIEW_PACKET_SCHEMA = "agades.pqc.heldout_review_packet.v1"
HELDOUT_REVIEW_PACKET_VERIFICATION_SCHEMA = (
    "agades.pqc.heldout_review_packet_verification.v1"
)
DEFAULT_HELDOUT_REVIEW_PACKET_PATH = Path(
    "private/reports/heldout_review_packet.json"
)
FORBIDDEN_HELDOUT_REVIEW_PACKET_KEYS = frozenset(
    {
        "attack_plan",
        "candidate_source",
        "candidate_sources",
        "combined_score",
        "evaluation",
        "generalization_gap",
        "heldout_max_combined_score",
        "heldout_mean_combined_score",
        "heldout_min_combined_score",
        "heldout_scores",
        "operators",
        "trace_payload",
        "trace_record",
        "train_combined_score",
    }
)
ROOT = Path(__file__).resolve().parents[3]


def build_heldout_review_packet(
    *,
    schedule_path: Path,
    policy: dict[str, Any],
    root: Path | None = None,
    out: Path | None = None,
    reviewer_label: str = "pending-expert-review",
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    if out is not None:
        validate_policy_private_path(out, policy=policy, root=project_root)
    schedule_validation = validate_heldout_schedule(
        schedule_path,
        policy=policy,
        root=project_root,
    )
    resolved_schedule_path = _resolve_path(schedule_path, project_root)
    schedule = _load_json_object(resolved_schedule_path)
    outputs = _dict_or_empty(schedule.get("outputs"))
    heldout_trace_path = _required_path(outputs, "heldout_trace")
    rescore_report_path = _required_path(outputs, "rescore_report")
    validate_policy_private_path(
        heldout_trace_path,
        policy=policy,
        root=project_root,
    )
    validate_policy_private_path(
        rescore_report_path,
        policy=policy,
        root=project_root,
    )

    resolved_trace_path = _resolve_path(heldout_trace_path, project_root)
    resolved_rescore_path = _resolve_path(rescore_report_path, project_root)
    trace_records = _read_trace_records(resolved_trace_path, heldout_trace_path)
    rescore_report = _load_rescore_report(resolved_rescore_path, rescore_report_path)
    review_log = _dict_or_empty(schedule.get("review_log"))
    execution_safety = _dict_or_empty(schedule.get("execution_safety"))
    summary = {
        "heldout_record_count": len(trace_records),
        "rescored_elite_count": _rescore_summary_count(
            rescore_report,
            "rescored_elite_count",
        ),
        "review_question_count": len(_review_questions()),
        "schedule_ready": schedule_validation["ready_to_run"],
    }

    packet = {
        "schema_version": HELDOUT_REVIEW_PACKET_SCHEMA,
        "created_at": "manual-heldout-review-packet-recorded",
        "report": {
            "path": _display_path(
                out or DEFAULT_HELDOUT_REVIEW_PACKET_PATH,
                project_root,
            ),
            "private": True,
        },
        "review_status": {
            "state": "pending_expert_review",
            "reviewer_label": reviewer_label,
            "score_promotion_allowed": False,
            "public_claim_language_approved": False,
        },
        "artifacts": {
            "schedule": _file_reference(
                schedule_path,
                resolved_schedule_path,
                schema_version=HELDOUT_SCHEDULE_SCHEMA,
                root=project_root,
            ),
            "heldout_trace": {
                **_file_reference(
                    heldout_trace_path,
                    resolved_trace_path,
                    schema_version=TRACE_RECORD_SCHEMA,
                    root=project_root,
                ),
                "record_count": len(trace_records),
            },
            "rescore_report": _file_reference(
                rescore_report_path,
                resolved_rescore_path,
                schema_version=HELDOUT_RESCORE_SCHEMA,
                root=project_root,
            ),
        },
        "review_log": {
            "path": review_log.get("path"),
            "schema_version": review_log.get("schema_version"),
            "sha256": review_log.get("sha256"),
            "approval_gates": list(review_log.get("approval_gates", [])),
        },
        "summary": summary,
        "review_questions": _review_questions(),
        "safety": {
            "arbitrary_code_execution": execution_safety.get(
                "arbitrary_code_execution"
            ),
            "contains_attack_plans": False,
            "contains_candidate_sources": False,
            "contains_private_scores": False,
            "contains_trace_payloads": False,
            "external_network_access": execution_safety.get("external_network_access"),
            "private_report": True,
            "publication_allowed": False,
            "public_release_ok": False,
            "requires_expert_review": True,
            "security_claim": False,
            "shell_commands_executed": False,
        },
    }
    _validate_packet_safety(packet)
    return packet


def write_heldout_review_packet(
    out: Path,
    *,
    schedule_path: Path,
    policy: dict[str, Any],
    root: Path | None = None,
    reviewer_label: str = "pending-expert-review",
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    validate_policy_private_path(out, policy=policy, root=project_root)
    packet = build_heldout_review_packet(
        schedule_path=schedule_path,
        policy=policy,
        root=project_root,
        out=out,
        reviewer_label=reviewer_label,
    )
    resolved_out = _resolve_path(out, project_root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return packet


def verify_heldout_review_packet(
    packet_path: Path,
    *,
    schedule_path: Path | None = None,
    policy: dict[str, Any],
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    packet = _load_packet(packet_path, failures)
    summary = {
        "contains_private_scores": None,
        "failure_count": 0,
        "heldout_record_count": 0,
        "private_report": None,
        "rescored_elite_count": 0,
        "security_claim": None,
    }

    try:
        validate_policy_private_path(packet_path, policy=policy, root=project_root)
    except ValueError as exc:
        failures.append(f"Held-out review packet path must be private: {exc}")

    if packet is not None:
        _verify_schema(packet, failures)
        _verify_report(packet, failures, summary)
        _verify_review_status(packet, failures)
        resolved_schedule_path = _packet_schedule_path(
            packet,
            explicit_schedule_path=schedule_path,
        )
        _verify_artifacts(
            packet,
            schedule_path=resolved_schedule_path,
            policy=policy,
            root=project_root,
            failures=failures,
            summary=summary,
        )
        _verify_review_log(packet, resolved_schedule_path, project_root, failures)
        _verify_summary(packet, summary, failures)
        _verify_safety(packet, failures, summary)
        _verify_no_private_payload(packet, failures, summary)

    summary["failure_count"] = len(failures)
    return {
        "schema_version": HELDOUT_REVIEW_PACKET_VERIFICATION_SCHEMA,
        "packet_path": packet_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _review_questions() -> list[str]:
    return [
        "Confirm the held-out target set is compatible with the source archive family.",
        "Review archive-to-trace parent links before trusting held-out rescore counts.",
        "Inspect private trace and rescore artifacts locally before publication.",
        "Approve or reject the trace and rescore artifact digests as review evidence.",
        "Approve public claim language separately from held-out reproducibility.",
    ]


def _verify_artifacts(
    packet: dict[str, Any],
    *,
    schedule_path: Path,
    policy: dict[str, Any],
    root: Path,
    failures: list[str],
    summary: dict[str, Any],
) -> None:
    artifacts = _dict_or_empty(packet.get("artifacts"))
    try:
        schedule_validation = validate_heldout_schedule(
            schedule_path,
            policy=policy,
            root=root,
        )
    except Exception as exc:  # noqa: BLE001 - verifier returns structured failures.
        failures.append(f"Held-out review packet schedule validation failed: {exc}")
        return

    resolved_schedule_path = _resolve_path(schedule_path, root)
    schedule = _load_json_object(resolved_schedule_path)
    outputs = _dict_or_empty(schedule.get("outputs"))
    heldout_trace_path = _required_path(outputs, "heldout_trace")
    rescore_report_path = _required_path(outputs, "rescore_report")
    resolved_trace_path = _resolve_path(heldout_trace_path, root)
    resolved_rescore_path = _resolve_path(rescore_report_path, root)
    trace_records = _read_trace_records(resolved_trace_path, heldout_trace_path)
    rescore_report = _load_rescore_report(resolved_rescore_path, rescore_report_path)

    _verify_file_reference(
        artifacts.get("schedule"),
        path=schedule_path,
        resolved_path=resolved_schedule_path,
        schema_version=HELDOUT_SCHEDULE_SCHEMA,
        root=root,
        label="schedule",
        failures=failures,
    )
    _verify_file_reference(
        artifacts.get("heldout_trace"),
        path=heldout_trace_path,
        resolved_path=resolved_trace_path,
        schema_version=TRACE_RECORD_SCHEMA,
        root=root,
        label="heldout_trace",
        failures=failures,
    )
    _verify_file_reference(
        artifacts.get("rescore_report"),
        path=rescore_report_path,
        resolved_path=resolved_rescore_path,
        schema_version=HELDOUT_RESCORE_SCHEMA,
        root=root,
        label="rescore_report",
        failures=failures,
    )

    trace_ref = _dict_or_empty(artifacts.get("heldout_trace"))
    if trace_ref.get("record_count") != len(trace_records):
        failures.append("Held-out review packet trace record count drifted.")
    summary["heldout_record_count"] = len(trace_records)
    summary["rescored_elite_count"] = _rescore_summary_count(
        rescore_report,
        "rescored_elite_count",
    )
    expected_ready = schedule_validation["ready_to_run"]
    packet_summary = _dict_or_empty(packet.get("summary"))
    if packet_summary.get("schedule_ready") != expected_ready:
        failures.append("Held-out review packet schedule_ready drifted.")


def _verify_file_reference(
    value: Any,
    *,
    path: Path,
    resolved_path: Path,
    schema_version: str,
    root: Path,
    label: str,
    failures: list[str],
) -> None:
    reference = _dict_or_empty(value)
    expected_path = _display_path(path, root)
    if reference.get("path") != expected_path:
        failures.append(f"Held-out review packet {label} path drifted.")
    if reference.get("schema_version") != schema_version:
        failures.append(f"Held-out review packet {label} schema drifted.")
    if reference.get("sha256") != _sha256_file(resolved_path):
        failures.append(f"Held-out review packet {label} digest drifted.")
    if not _is_private_path(expected_path):
        failures.append(f"Held-out review packet {label} path must be private.")


def _verify_review_log(
    packet: dict[str, Any],
    schedule_path: Path,
    root: Path,
    failures: list[str],
) -> None:
    packet_review_log = _dict_or_empty(packet.get("review_log"))
    schedule = _load_json_object(_resolve_path(schedule_path, root))
    schedule_review_log = _dict_or_empty(schedule.get("review_log"))
    expected_keys = ("approval_gates", "path", "schema_version", "sha256")
    for key in expected_keys:
        if packet_review_log.get(key) != schedule_review_log.get(key):
            failures.append(f"Held-out review packet review_log {key} drifted.")


def _verify_summary(
    packet: dict[str, Any],
    verifier_summary: dict[str, Any],
    failures: list[str],
) -> None:
    packet_summary = _dict_or_empty(packet.get("summary"))
    expected = {
        "heldout_record_count": verifier_summary["heldout_record_count"],
        "rescored_elite_count": verifier_summary["rescored_elite_count"],
        "review_question_count": len(_review_questions()),
    }
    for key, value in expected.items():
        if packet_summary.get(key) != value:
            failures.append(f"Held-out review packet summary {key} drifted.")


def _verify_schema(packet: dict[str, Any], failures: list[str]) -> None:
    if packet.get("schema_version") != HELDOUT_REVIEW_PACKET_SCHEMA:
        failures.append("Held-out review packet schema drifted.")


def _verify_report(
    packet: dict[str, Any],
    failures: list[str],
    summary: dict[str, Any],
) -> None:
    report = _dict_or_empty(packet.get("report"))
    summary["private_report"] = report.get("private")
    if report.get("private") is not True:
        failures.append("Held-out review packet must be private.")
    path = report.get("path")
    if not isinstance(path, str) or not _is_private_path(path):
        failures.append("Held-out review packet path must stay under private/.")


def _verify_review_status(packet: dict[str, Any], failures: list[str]) -> None:
    status = _dict_or_empty(packet.get("review_status"))
    expected = {
        "state": "pending_expert_review",
        "score_promotion_allowed": False,
        "public_claim_language_approved": False,
    }
    for key, value in expected.items():
        if status.get(key) != value:
            failures.append(f"Held-out review packet review_status {key} drifted.")
    if (
        not isinstance(status.get("reviewer_label"), str)
        or not status["reviewer_label"]
    ):
        failures.append("Held-out review packet reviewer label is invalid.")


def _verify_safety(
    packet: dict[str, Any],
    failures: list[str],
    summary: dict[str, Any],
) -> None:
    safety = _dict_or_empty(packet.get("safety"))
    summary["security_claim"] = safety.get("security_claim")
    expected = {
        "arbitrary_code_execution": False,
        "contains_attack_plans": False,
        "contains_candidate_sources": False,
        "contains_private_scores": False,
        "contains_trace_payloads": False,
        "external_network_access": False,
        "private_report": True,
        "publication_allowed": False,
        "public_release_ok": False,
        "requires_expert_review": True,
        "security_claim": False,
        "shell_commands_executed": False,
    }
    for key, value in expected.items():
        if safety.get(key) != value:
            failures.append(f"Held-out review packet safety {key} drifted.")


def _verify_no_private_payload(
    packet: dict[str, Any],
    failures: list[str],
    summary: dict[str, Any],
) -> None:
    forbidden = _forbidden_keys(packet)
    summary["contains_private_scores"] = bool(forbidden)
    if forbidden:
        joined = ", ".join(sorted(forbidden))
        failures.append(
            "Held-out review packet contains private score or payload key: "
            f"{joined}."
        )


def _validate_packet_safety(packet: dict[str, Any]) -> None:
    if _forbidden_keys(packet):
        raise ValueError("held-out review packet contains private payload fields")
    safety = packet["safety"]
    if safety["arbitrary_code_execution"] is not False:
        raise ValueError("held-out review packet cannot execute arbitrary code")
    if safety["external_network_access"] is not False:
        raise ValueError("held-out review packet cannot use external networking")
    if safety["contains_attack_plans"] is not False:
        raise ValueError("held-out review packet cannot contain AttackPlans")
    if safety["contains_candidate_sources"] is not False:
        raise ValueError("held-out review packet cannot contain candidate sources")
    if safety["contains_private_scores"] is not False:
        raise ValueError("held-out review packet cannot contain private scores")
    if safety["contains_trace_payloads"] is not False:
        raise ValueError("held-out review packet cannot contain trace payloads")
    if safety["public_release_ok"] is not False:
        raise ValueError("held-out review packet cannot be public-release-ready")
    if safety["security_claim"] is not False:
        raise ValueError("held-out review packet cannot make security claims")


def _load_packet(path: Path, failures: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        failures.append(f"Held-out review packet is missing: {path}.")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(
            f"Held-out review packet is invalid JSON at line {exc.lineno}: {exc.msg}."
        )
        return None
    if not isinstance(payload, dict):
        failures.append("Held-out review packet must be a JSON object.")
        return None
    return payload


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}.")
    return payload


def _load_rescore_report(resolved_path: Path, original_path: Path) -> dict[str, Any]:
    report = _load_json_object(resolved_path)
    if report.get("schema_version") != HELDOUT_RESCORE_SCHEMA:
        raise ValueError(
            f"held-out review packet requires {HELDOUT_RESCORE_SCHEMA} at "
            f"{original_path}"
        )
    return report


def _read_trace_records(resolved_path: Path, original_path: Path) -> list[TraceRecord]:
    records: list[TraceRecord] = []
    for line_number, raw_line in enumerate(
        resolved_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not raw_line.strip():
            continue
        try:
            record = TraceRecord.model_validate_json(raw_line)
        except ValidationError as exc:
            raise ValueError(
                f"invalid held-out trace record at {original_path}:{line_number}: "
                f"{exc}"
            ) from exc
        if record.public_release_ok:
            raise ValueError(
                f"held-out trace record {record.trace_id} is marked public-release-ok"
            )
        records.append(record)
    return records


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
    }


def _packet_schedule_path(
    packet: dict[str, Any],
    *,
    explicit_schedule_path: Path | None,
) -> Path:
    if explicit_schedule_path is not None:
        return explicit_schedule_path
    artifacts = _dict_or_empty(packet.get("artifacts"))
    schedule = _dict_or_empty(artifacts.get("schedule"))
    path = schedule.get("path")
    return Path(path) if isinstance(path, str) else Path("__missing_schedule__")


def _rescore_summary_count(report: dict[str, Any], key: str) -> int:
    summary = _dict_or_empty(report.get("summary"))
    value = summary.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"held-out rescore summary field {key} is invalid")
    return value


def _required_path(payload: dict[str, Any], key: str) -> Path:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"held-out review packet field {key} must be a path string")
    return Path(value)


def _forbidden_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_HELDOUT_REVIEW_PACKET_KEYS:
                found.add(key)
            found.update(_forbidden_keys(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_forbidden_keys(item))
    return found


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _display_path(path: Path, root: Path) -> str:
    if path.is_absolute():
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix()


def _is_private_path(path: str) -> bool:
    return PurePath(path).parts[:1] == ("private",)


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()
