from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from agades_pqc_gym.core.trace_record import TraceRecord
from agades_pqc_gym.traces.redaction import (
    redact_trace_record,
    redacted_evaluation,
)


@dataclass(frozen=True)
class ReportGenerator:
    """Family-agnostic Markdown report generator for public trace summaries."""

    title: str = "Agades PQC Gym Report"
    include_private_details: bool = False

    def render_markdown(
        self,
        records: Iterable[TraceRecord | Mapping[str, Any]],
    ) -> str:
        rows = [self._row(record) for record in records]
        return _render_markdown(self.title, rows)

    def _row(self, record: TraceRecord | Mapping[str, Any]) -> _ReportRow:
        data, redacted = self._record_data(record)
        evaluation = _mapping_value(data.get("evaluation"))

        if redacted:
            return _ReportRow(
                candidate_id=_text(data.get("candidate_id", "unknown")),
                target="[redacted]",
                family="[redacted]",
                attack_type="[redacted]",
                status=_text(evaluation.get("evaluation_status", "unknown")),
                accepted=_text(
                    data.get("accepted", evaluation.get("valid", "unknown"))
                ),
                score=_text(evaluation.get("combined_score", "unknown")),
                time_bits=_text(evaluation.get("estimated_time_bits", "unknown")),
                memory_bits=_text(
                    evaluation.get("estimated_memory_bits", "unknown")
                ),
                estimator=_text(evaluation.get("estimator_name", "unknown")),
                reproduction_status=_text(
                    evaluation.get("reproduction_status", "not_requested")
                ),
                redacted=True,
            )

        attack_plan = _mapping_value(data.get("attack_plan"))
        target = _mapping_value(attack_plan.get("target"))
        family = evaluation.get("feature_family") or target.get("family", "unknown")

        return _ReportRow(
            candidate_id=_text(data.get("candidate_id", "unknown")),
            target=_text(target.get("name", "unknown")),
            family=_text(family),
            attack_type=_text(
                evaluation.get("feature_attack_type")
                or evaluation.get("attack_type", "unknown")
            ),
            status=_text(evaluation.get("evaluation_status", "unknown")),
            accepted=_text(data.get("accepted", evaluation.get("valid", "unknown"))),
            score=_text(evaluation.get("combined_score", "unknown")),
            time_bits=_text(evaluation.get("estimated_time_bits", "unknown")),
            memory_bits=_text(evaluation.get("estimated_memory_bits", "unknown")),
            estimator=_text(evaluation.get("estimator_name", "unknown")),
            reproduction_status=_text(
                evaluation.get("reproduction_status", "not_requested")
            ),
            redacted=False,
        )

    def _record_data(
        self,
        record: TraceRecord | Mapping[str, Any],
    ) -> tuple[dict[str, Any], bool]:
        if isinstance(record, TraceRecord):
            redacted = (
                not record.public_release_ok and not self.include_private_details
            )
            if redacted:
                return redact_trace_record(record), True
            return record.model_dump(mode="json"), False

        raw = dict(record)
        trace = _trace_record_from_mapping(raw)
        if trace is not None:
            return self._record_data(trace)

        public_release_ok = bool(raw.get("public_release_ok", True))
        redacted = not public_release_ok and not self.include_private_details
        if not redacted:
            return raw, False

        redacted_data = dict(raw)
        attack_plan = _mapping_value(raw.get("attack_plan"))
        attack_plan_id = attack_plan.get("attack_plan_id", "redacted")
        redacted_data["attack_plan"] = {"attack_plan_id": attack_plan_id}
        redacted_data["evaluation"] = redacted_evaluation()
        redacted_data["mutation_summary"] = "[redacted]"
        redacted_data["public_release_ok"] = True
        redacted_data["redaction_reason"] = raw.get("redaction_reason") or "not public"
        return redacted_data, True


@dataclass(frozen=True)
class _ReportRow:
    candidate_id: str
    target: str
    family: str
    attack_type: str
    status: str
    accepted: str
    score: str
    time_bits: str
    memory_bits: str
    estimator: str
    reproduction_status: str
    redacted: bool


def _render_markdown(title: str, rows: list[_ReportRow]) -> str:
    family_counts = Counter(row.family for row in rows if not row.redacted)
    status_counts = Counter(row.status for row in rows)
    reproduction_counts = Counter(row.reproduction_status for row in rows)
    estimator_names = {row.estimator for row in rows}

    total_records = len(rows)
    redacted_records = sum(1 for row in rows if row.redacted)
    public_records = total_records - redacted_records

    table = (
        "\n".join(_table_row(row) for row in rows)
        if rows
        else "| none | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |"
    )

    estimator_status = _estimator_status(estimator_names, status_counts)
    reproduction_status = _reproduction_status(reproduction_counts)

    return (
        f"# {title}\n\n"
        "## Summary\n\n"
        "This report summarizes toy/downscaled AttackPlan evaluations.\n\n"
        f"- Records: {total_records}\n"
        f"- Public records: {public_records}\n"
        f"- Private records redacted: {redacted_records}\n"
        f"- Family Summary: {_counter_text(family_counts)}\n"
        f"- Evaluation Status: {_counter_text(status_counts)}\n\n"
        "## Results\n\n"
        "| Candidate | Family | Target | Status | Reproduction | Accepted | Score | "
        "Time Bits | Memory Bits | Estimator |\n"
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |\n"
        f"{table}\n\n"
        "## Public/Private Redaction\n\n"
        f"{_redaction_status(redacted_records)}\n\n"
        "## Mock Vs Real Estimator Status\n\n"
        f"{estimator_status}\n\n"
        "## Reproduction Status\n\n"
        f"{reproduction_status}\n\n"
        "## Limitations\n\n"
        "Estimator outputs are hypotheses requiring independent review. This report is "
        "not a security claim, does not target live systems, and does not imply a "
        "break of any deployed post-quantum cryptographic standard.\n"
    )


def _table_row(row: _ReportRow) -> str:
    return (
        f"| {_cell(row.candidate_id)} | {_cell(row.family)} | {_cell(row.target)} | "
        f"{_cell(row.status)} | {_cell(row.reproduction_status)} | "
        f"{_cell(row.accepted)} | {_cell(row.score)} | {_cell(row.time_bits)} | "
        f"{_cell(row.memory_bits)} | {_cell(row.estimator)} |"
    )


def _estimator_status(
    estimator_names: set[str],
    status_counts: Counter[str],
) -> str:
    status = (
        "At least one result uses the mock estimator. Mock output is not a security "
        "claim and exists only to verify evaluator plumbing."
        if any("mock" in name for name in estimator_names)
        else "No mock estimator records were detected in this report."
    )
    if status_counts.get("unsupported", 0) > 0:
        status += (
            " No cryptanalytic estimate was produced for at least one unsupported "
            "family/operator combination."
        )
    return status


def _reproduction_status(reproduction_counts: Counter[str]) -> str:
    if not reproduction_counts:
        return "No reproduction records were present."
    summary = _counter_text(reproduction_counts)
    if reproduction_counts.get("instance_solved", 0) > 0:
        return (
            f"Reproduction Summary: {summary}. `instance_solved` is limited to "
            "bounded public toy/downscaled fixtures and is not a deployed-parameter "
            "security claim."
        )
    return f"Reproduction Summary: {summary}."


def _redaction_status(redacted_records: int) -> str:
    if redacted_records == 0:
        return "No private trace records were redacted for this report."
    return (
        f"Private records redacted: {redacted_records}. Public reports hide private "
        "target, family, attack, and mutation details by default."
    )


def _counter_text(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return ", ".join(
        f"`{key}`: {counter[key]}" for key in sorted(counter)
    )


def _trace_record_from_mapping(data: Mapping[str, Any]) -> TraceRecord | None:
    try:
        return TraceRecord.model_validate(data)
    except ValidationError:
        return None


def _mapping_value(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: Any) -> str:
    if value is None:
        return "unknown"
    return str(value)


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
