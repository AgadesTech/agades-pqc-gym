from __future__ import annotations

from typing import Any

from agades_lwe_gym.traces.schema import TraceRecord


def redact_trace_record(record: TraceRecord) -> dict[str, Any]:
    data = record.model_dump(mode="json")
    if not record.public_release_ok:
        data["mutation_summary"] = "[redacted]"
        data["attack_plan"] = {"attack_plan_id": record.attack_plan.attack_plan_id}
        data["redaction_reason"] = record.redaction_reason or "not public"
        data["public_release_ok"] = True
    return data

