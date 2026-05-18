from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from agades_pqc_gym import __version__
from agades_pqc_gym.core.trace_record import TraceRecord
from agades_pqc_gym.traces.redaction import redact_trace_record
from agades_pqc_gym.utils.hashing import stable_sha256

PUBLIC_RUN_LEDGER_SCHEMA = "agades.pqc.public_run_ledger.v1"
CANONICAL_PUBLIC_CREATED_AT = "1970-01-01T00:00:00+00:00"


def build_public_run_ledger(trace_path: Path) -> dict[str, Any]:
    records = read_trace_records(trace_path)
    return build_public_run_ledger_from_records(records)


def build_public_run_ledger_from_records(
    records: list[TraceRecord],
) -> dict[str, Any]:
    public_trace = render_public_trace_jsonl(records).encode("utf-8")
    entries = [_ledger_entry(record) for record in records]

    return {
        "schema_version": PUBLIC_RUN_LEDGER_SCHEMA,
        "ledger_version": __version__,
        "source_trace": {
            "artifact": "trace_public.jsonl",
            "public_sha256": hashlib.sha256(public_trace).hexdigest(),
            "record_count": len(records),
        },
        "summary": _summary(entries),
        "entries": entries,
        "safety": {
            "arbitrary_code_execution": False,
            "live_targeting": False,
            "security_claim": False,
        },
    }


def read_trace_records(path: Path) -> list[TraceRecord]:
    return [
        TraceRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def render_public_trace_jsonl(records: list[TraceRecord]) -> str:
    return "".join(
        json.dumps(canonical_public_trace_record(record), sort_keys=True) + "\n"
        for record in records
    )


def canonical_public_trace_record(record: TraceRecord) -> dict[str, Any]:
    public = redact_trace_record(record)
    public["created_at"] = CANONICAL_PUBLIC_CREATED_AT
    public["trace_id"] = _public_trace_id(public)
    return public


def _ledger_entry(record: TraceRecord) -> dict[str, Any]:
    redacted = not record.public_release_ok
    public = canonical_public_trace_record(record)
    evaluation = public["evaluation"]
    target_family, attack_type = _public_family_and_attack_type(public, redacted)
    warnings = evaluation.get("warnings", [])
    if warnings is None:
        warnings = []

    return {
        "trace_id": public["trace_id"],
        "run_id": public["run_id"],
        "candidate_id": public["candidate_id"],
        "parent_id": public["parent_id"],
        "generation": public["generation"],
        "attack_plan_id": public["attack_plan"]["attack_plan_id"],
        "target_family": target_family,
        "attack_type": attack_type,
        "accepted": public["accepted"],
        "evaluation_status": evaluation.get("evaluation_status", "unknown"),
        "combined_score": evaluation.get("combined_score"),
        "estimated_time_bits": evaluation.get("estimated_time_bits"),
        "estimated_memory_bits": evaluation.get("estimated_memory_bits"),
        "estimator_name": evaluation.get("estimator_name"),
        "estimator_version": evaluation.get("estimator_version"),
        "public_release_ok": public["public_release_ok"],
        "redacted": redacted,
        "redaction_reason": public["redaction_reason"],
        "warnings": warnings,
    }


def _public_trace_id(public_record: dict[str, Any]) -> str:
    material = dict(public_record)
    material.pop("trace_id", None)
    return stable_sha256(material)


def _public_family_and_attack_type(
    public_record: dict[str, Any],
    redacted: bool,
) -> tuple[str, str]:
    if redacted:
        return "REDACTED", "REDACTED"

    attack_plan = public_record["attack_plan"]
    target_family = attack_plan.get("target", {}).get("family", "UNKNOWN")
    operators = attack_plan.get("operators", [])
    attack_type = operators[0].get("type", "UNKNOWN") if operators else "UNKNOWN"
    return target_family, attack_type


def _summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total_records": len(entries),
        "accepted_records": sum(1 for entry in entries if entry["accepted"]),
        "redacted_records": sum(1 for entry in entries if entry["redacted"]),
        "by_family": _sorted_counts(entry["target_family"] for entry in entries),
        "by_evaluation_status": _sorted_counts(
            entry["evaluation_status"] for entry in entries
        ),
        "by_estimator": _sorted_counts(
            entry["estimator_name"] or "none" for entry in entries
        ),
    }


def _sorted_counts(values: Iterable[str]) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(counts)}
