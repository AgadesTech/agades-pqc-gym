from __future__ import annotations

from typing import Any

from agades_pqc_gym.core.trace_record import TraceRecord

PRIVATE_EVALUATION_REDACTION_WARNING = "private evaluation redacted from public trace"


def redact_trace_record(record: TraceRecord) -> dict[str, Any]:
    data = record.model_dump(mode="json")
    if not record.public_release_ok:
        data["accepted"] = None
        data["mutation_summary"] = "[redacted]"
        data["attack_plan"] = {"attack_plan_id": record.attack_plan.attack_plan_id}
        data["evaluation"] = redacted_evaluation()
        data["redaction_reason"] = record.redaction_reason or "not public"
        data["public_release_ok"] = True
    return data


def redacted_evaluation() -> dict[str, Any]:
    return {
        "valid": None,
        "evaluation_status": "redacted",
        "combined_score": None,
        "estimated_time_bits": None,
        "estimated_memory_bits": None,
        "estimator_name": None,
        "estimator_version": None,
        "warnings": [PRIVATE_EVALUATION_REDACTION_WARNING],
    }
