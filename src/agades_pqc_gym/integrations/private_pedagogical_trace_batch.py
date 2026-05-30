from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.evolution.scheduler import validate_policy_private_path
from agades_pqc_gym.rl.environment import (
    AgadesPQCGymEnvironment,
    score_attack_plan_candidate,
)
from agades_pqc_gym.rl.private_trace import (
    PRIVATE_TRACE_FORBIDDEN_PUBLIC_FIELDS,
    PRIVATE_TRACE_PRIVACY_BOUNDARY,
    PRIVATE_TRACE_REVIEW_GATE,
    build_private_pedagogical_trace_record,
    verify_private_pedagogical_trace_record,
)
from agades_pqc_gym.utils.hashing import stable_sha256

PRIVATE_PEDAGOGICAL_TRACE_BATCH_SCHEMA = (
    "agades.pqc.rl.private_pedagogical_trace_batch.v1"
)
PRIVATE_PEDAGOGICAL_TRACE_BATCH_VERIFICATION_SCHEMA = (
    "agades.pqc.rl.private_pedagogical_trace_batch_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TRACE_BATCH_PATH = Path(
    "private/traces/pedagogical_rl/trace_records.jsonl"
)
DEFAULT_POLICY_PATH = Path("docs/private_run_policy.json")
DEFAULT_DATASET_CURATION_PATH = Path("docs/private_dataset_curation.json")


def write_private_pedagogical_trace_batch(
    plan_paths: list[Path],
    out: Path = DEFAULT_TRACE_BATCH_PATH,
    *,
    dataset_curation_manifest_path: Path = DEFAULT_DATASET_CURATION_PATH,
    policy_path: Path = DEFAULT_POLICY_PATH,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    if not plan_paths:
        raise ValueError("private pedagogical trace batch requires at least one plan")

    policy = _read_policy(_resolve_path(policy_path, project_root))
    manifest_path = _manifest_path_for(out)
    _validate_private_outputs(out, manifest_path, policy=policy, root=project_root)

    resolved_dataset_curation = _resolve_path(
        dataset_curation_manifest_path,
        project_root,
    )
    records = [
        _record_for_plan(
            plan_path,
            dataset_curation_manifest_path=resolved_dataset_curation,
            root=project_root,
        )
        for plan_path in plan_paths
    ]
    for index, record in enumerate(records):
        verification = verify_private_pedagogical_trace_record(record)
        if verification["accepted"] is not True:
            failures = ", ".join(verification["failures"])
            raise ValueError(
                f"private trace record {index} failed verification: {failures}"
            )

    trace_bytes = _jsonl_bytes(records)
    manifest = _batch_manifest(
        records,
        trace_path=out,
        manifest_path=manifest_path,
        trace_bytes=trace_bytes,
        root=project_root,
    )
    resolved_out = _resolve_path(out, project_root)
    resolved_manifest = _resolve_path(manifest_path, project_root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_bytes(trace_bytes)
    resolved_manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_private_pedagogical_trace_batch(
    trace_path: Path = DEFAULT_TRACE_BATCH_PATH,
    *,
    manifest_path: Path | None = None,
    policy_path: Path = DEFAULT_POLICY_PATH,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    resolved_manifest_path = manifest_path or _manifest_path_for(trace_path)
    failures: list[str] = []
    records: list[dict[str, Any]] = []
    manifest: dict[str, Any] = {}
    manifest_in_sync = False

    try:
        policy = _read_policy(_resolve_path(policy_path, project_root))
        _validate_private_outputs(
            trace_path,
            resolved_manifest_path,
            policy=policy,
            root=project_root,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append("Private pedagogical trace batch path must be private.")
        failures.append(str(exc))
        return _verification_result(
            trace_path=trace_path,
            manifest_path=resolved_manifest_path,
            records=records,
            manifest_in_sync=manifest_in_sync,
            failures=failures,
            root=project_root,
        )

    resolved_trace = _resolve_path(trace_path, project_root)
    try:
        trace_bytes = resolved_trace.read_bytes()
    except OSError as exc:
        failures.append(f"Private pedagogical trace batch is missing: {trace_path}.")
        trace_bytes = b""
        failures.append(str(exc))
    else:
        records = _read_records(trace_bytes, trace_path, failures)
        for index, record in enumerate(records):
            record_verification = verify_private_pedagogical_trace_record(record)
            if record_verification["accepted"] is not True:
                failures.append(
                    "Private pedagogical trace batch record "
                    f"{index} failed verification."
                )
                failures.extend(record_verification["failures"])

    try:
        manifest = json.loads(
            _resolve_path(resolved_manifest_path, project_root).read_text(
                encoding="utf-8",
            )
        )
    except OSError as exc:
        failures.append(
            "Private pedagogical trace batch manifest is missing: "
            f"{resolved_manifest_path}."
        )
        failures.append(str(exc))
    except json.JSONDecodeError as exc:
        failures.append(
            "Private pedagogical trace batch manifest is invalid JSON at "
            f"line {exc.lineno}."
        )
    else:
        expected_manifest = _batch_manifest(
            records,
            trace_path=trace_path,
            manifest_path=resolved_manifest_path,
            trace_bytes=trace_bytes,
            root=project_root,
        )
        manifest_in_sync = manifest == expected_manifest
        if not manifest_in_sync:
            failures.append("Private pedagogical trace batch manifest is not in sync.")
        _verify_manifest_safety(manifest, failures)

    return _verification_result(
        trace_path=trace_path,
        manifest_path=resolved_manifest_path,
        records=records,
        manifest_in_sync=manifest_in_sync,
        failures=failures,
        root=project_root,
    )


def _record_for_plan(
    plan_path: Path,
    *,
    dataset_curation_manifest_path: Path,
    root: Path,
) -> dict[str, Any]:
    resolved_plan = _resolve_path(plan_path, root)
    candidate_json = resolved_plan.read_text(encoding="utf-8")
    env = AgadesPQCGymEnvironment.from_attack_plan_paths(
        [resolved_plan],
        root=root,
    )
    task = env.reset()["task"]
    reward_report = score_attack_plan_candidate(
        candidate_json,
        task_info=task,
        require_task_match=True,
    )
    return build_private_pedagogical_trace_record(
        task=task,
        candidate_json=candidate_json,
        reward_report=reward_report,
        dataset_curation_manifest_path=dataset_curation_manifest_path,
    )


def _batch_manifest(
    records: list[dict[str, Any]],
    *,
    trace_path: Path,
    manifest_path: Path,
    trace_bytes: bytes,
    root: Path,
) -> dict[str, Any]:
    return {
        "schema_version": PRIVATE_PEDAGOGICAL_TRACE_BATCH_SCHEMA,
        "trace_path": _display_path(trace_path, root),
        "manifest_path": _display_path(manifest_path, root),
        "trace_sha256": hashlib.sha256(trace_bytes).hexdigest(),
        "record_set_sha256": stable_sha256(records),
        "trace_ids": [record["trace_id"] for record in records],
        "summary": {
            "trace_count": len(records),
            "accepted_records": sum(
                1
                for record in records
                if verify_private_pedagogical_trace_record(record)["accepted"]
                is True
            ),
            "training_eligible_records": _training_eligible_record_count(records),
            "public_release_ok": False,
            "raw_private_signals_included": False,
        },
        "review_gate": dict(PRIVATE_TRACE_REVIEW_GATE),
        "privacy_boundary": dict(PRIVATE_TRACE_PRIVACY_BOUNDARY),
        "safety": {
            "private": True,
            "public_release_ok": False,
            "contains_raw_private_signals": False,
            "contains_forbidden_public_fields": any(
                _contains_exact_key(record, field)
                for record in records
                for field in PRIVATE_TRACE_FORBIDDEN_PUBLIC_FIELDS
            ),
            "training_eligible": (
                bool(records)
                and _training_eligible_record_count(records) == len(records)
            ),
            "requires_private_review_before_training": True,
            "writes_only_allowed_private_roots": True,
        },
    }


def _verify_manifest_safety(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    if manifest.get("schema_version") != PRIVATE_PEDAGOGICAL_TRACE_BATCH_SCHEMA:
        failures.append("Private pedagogical trace batch schema is incorrect.")
    if manifest.get("review_gate") != PRIVATE_TRACE_REVIEW_GATE:
        failures.append("Private pedagogical trace batch review gate is incorrect.")
    if manifest.get("privacy_boundary") != PRIVATE_TRACE_PRIVACY_BOUNDARY:
        failures.append(
            "Private pedagogical trace batch privacy boundary is incorrect."
        )
    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        failures.append("Private pedagogical trace batch safety block is missing.")
        return
    expected_false = (
        "public_release_ok",
        "contains_raw_private_signals",
        "contains_forbidden_public_fields",
    )
    for key in expected_false:
        if safety.get(key) is not False:
            failures.append(f"Private pedagogical trace batch safety.{key} is unsafe.")
    if safety.get("private") is not True:
        failures.append("Private pedagogical trace batch must be private.")
    summary = _dict_or_empty(manifest.get("summary"))
    expected_training_eligible = (
        isinstance(summary.get("trace_count"), int)
        and summary.get("trace_count") > 0
        and summary.get("training_eligible_records") == summary.get("trace_count")
    )
    if safety.get("training_eligible") is not expected_training_eligible:
        failures.append(
            "Private pedagogical trace batch training eligibility is not in sync."
        )
    if safety.get("requires_private_review_before_training") is not True:
        failures.append(
            "Private pedagogical trace batch must require private review before "
            "training."
        )
    if safety.get("writes_only_allowed_private_roots") is not True:
        failures.append(
            "Private pedagogical trace batch must write only allowed private roots."
        )


def _verification_result(
    *,
    trace_path: Path,
    manifest_path: Path,
    records: list[dict[str, Any]],
    manifest_in_sync: bool,
    failures: list[str],
    root: Path,
) -> dict[str, Any]:
    accepted_records = sum(
        1
        for record in records
        if verify_private_pedagogical_trace_record(record)["accepted"] is True
    )
    return {
        "schema_version": PRIVATE_PEDAGOGICAL_TRACE_BATCH_VERIFICATION_SCHEMA,
        "trace_path": _display_path(trace_path, root),
        "manifest_path": _display_path(manifest_path, root),
        "accepted": not failures,
        "summary": {
            "trace_count": len(records),
            "accepted_records": accepted_records,
            "training_eligible_records": _training_eligible_record_count(records),
            "failure_count": len(failures),
            "manifest_in_sync": manifest_in_sync,
            "public_release_ok": False,
        },
        "failures": failures,
    }


def _read_records(
    trace_bytes: bytes,
    trace_path: Path,
    failures: list[str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(
        trace_bytes.decode("utf-8").splitlines(),
        start=1,
    ):
        if not raw_line.strip():
            continue
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            failures.append(
                f"Invalid private trace JSON at {trace_path}:{line_number}: "
                f"{exc.msg}."
            )
            continue
        if not isinstance(payload, dict):
            failures.append(
                f"Private trace record at {trace_path}:{line_number} "
                "must be a JSON object."
            )
            continue
        records.append(payload)
    return records


def _jsonl_bytes(records: list[dict[str, Any]]) -> bytes:
    payload = "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
    return payload.encode("utf-8")


def _training_eligible_record_count(records: list[dict[str, Any]]) -> int:
    return sum(
        1
        for record in records
        if _dict_or_empty(record.get("dataset_curation_gate")).get(
            "training_eligible"
        )
        is True
    )


def _validate_private_outputs(
    trace_path: Path,
    manifest_path: Path,
    *,
    policy: dict[str, Any],
    root: Path,
) -> None:
    validate_policy_private_path(trace_path, policy=policy, root=root)
    validate_policy_private_path(manifest_path, policy=policy, root=root)


def _manifest_path_for(trace_path: Path) -> Path:
    return trace_path.with_suffix(".manifest.json")


def _read_policy(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("private run policy must be a JSON object")
    return payload


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _display_path(path: Path, root: Path) -> str:
    resolved = _resolve_path(path, root).resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _contains_exact_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(
            _contains_exact_key(child, key) for child in value.values()
        )
    if isinstance(value, list):
        return any(_contains_exact_key(child, key) for child in value)
    return False


def _dict_or_empty(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
