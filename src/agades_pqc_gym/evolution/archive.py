from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agades_pqc_gym.core.trace_record import TraceRecord

EVOLUTION_ARCHIVE_SCHEMA = "agades.pqc.evolution_archive.v1"
DEFAULT_ELITE_FEATURE_KEYS = (
    "feature_family",
    "feature_attack_type",
    "feature_memory_bucket",
    "feature_assumption_bucket",
    "feature_estimator_model",
)

FeatureValue = str | int | float | bool | None


class EliteRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cell_key: str
    candidate_id: str
    trace_id: str
    parent_id: str | None
    generation: int = Field(ge=0)
    attack_plan_id: str
    target_family: str
    combined_score: float
    evaluation_status: str
    feature_values: dict[str, FeatureValue]
    public_release_ok: bool
    warnings: list[str] = Field(default_factory=list)


class EvolutionArchive(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = EVOLUTION_ARCHIVE_SCHEMA
    run_id: str
    feature_keys: list[str]
    summary: dict[str, int]
    global_best: EliteRecord | None
    elites: list[EliteRecord]


def build_evolution_archive(
    records: Iterable[TraceRecord],
    *,
    run_id: str,
    feature_keys: Sequence[str] = DEFAULT_ELITE_FEATURE_KEYS,
) -> EvolutionArchive:
    selected_feature_keys = list(feature_keys)
    evaluated_count = 0
    accepted_count = 0
    rejected_count = 0
    cells: dict[str, EliteRecord] = {}

    for record in records:
        evaluated_count += 1
        if not record.accepted:
            rejected_count += 1
            continue

        accepted_count += 1
        elite = _elite_from_trace(record, selected_feature_keys)
        current = cells.get(elite.cell_key)
        if current is None or _is_better_elite(elite, current):
            cells[elite.cell_key] = elite

    elites = [cells[key] for key in sorted(cells)]
    global_best = _global_best(elites)
    return EvolutionArchive(
        run_id=run_id,
        feature_keys=selected_feature_keys,
        summary={
            "accepted_count": accepted_count,
            "elite_count": len(elites),
            "evaluated_count": evaluated_count,
            "rejected_count": rejected_count,
        },
        global_best=global_best,
        elites=elites,
    )


def write_evolution_archive(
    records: Iterable[TraceRecord],
    out: Path,
    *,
    run_id: str,
    feature_keys: Sequence[str] = DEFAULT_ELITE_FEATURE_KEYS,
) -> EvolutionArchive:
    archive = build_evolution_archive(records, run_id=run_id, feature_keys=feature_keys)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(archive.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return archive


def _elite_from_trace(
    record: TraceRecord,
    feature_keys: Sequence[str],
) -> EliteRecord:
    evaluation = record.evaluation
    combined_score = _required_number(evaluation, "combined_score", record)
    evaluation_status = _required_string(evaluation, "evaluation_status", record)
    feature_values = {
        key: _required_feature_value(evaluation, key, record) for key in feature_keys
    }
    return EliteRecord(
        cell_key=_cell_key(feature_values),
        candidate_id=record.candidate_id,
        trace_id=record.trace_id,
        parent_id=record.parent_id,
        generation=record.generation,
        attack_plan_id=record.attack_plan.attack_plan_id,
        target_family=record.attack_plan.target.family.value,
        combined_score=combined_score,
        evaluation_status=evaluation_status,
        feature_values=feature_values,
        public_release_ok=record.public_release_ok,
        warnings=_warnings(evaluation),
    )


def _cell_key(feature_values: dict[str, FeatureValue]) -> str:
    return "|".join(
        f"{key}={_format_cell_value(value)}"
        for key, value in feature_values.items()
    )


def _format_cell_value(value: FeatureValue) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _is_better_elite(candidate: EliteRecord, current: EliteRecord) -> bool:
    if candidate.combined_score != current.combined_score:
        return candidate.combined_score > current.combined_score
    return candidate.candidate_id < current.candidate_id


def _global_best(elites: list[EliteRecord]) -> EliteRecord | None:
    if not elites:
        return None
    return sorted(
        elites,
        key=lambda elite: (-elite.combined_score, elite.candidate_id),
    )[0]


def _required_number(
    evaluation: dict[str, Any],
    key: str,
    record: TraceRecord,
) -> float:
    value = evaluation.get(key)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(
            f"Trace {record.trace_id} lacks numeric evaluation field {key}."
        )
    return float(value)


def _required_string(
    evaluation: dict[str, Any],
    key: str,
    record: TraceRecord,
) -> str:
    value = evaluation.get(key)
    if not isinstance(value, str):
        raise ValueError(
            f"Trace {record.trace_id} lacks string evaluation field {key}."
        )
    return value


def _required_feature_value(
    evaluation: dict[str, Any],
    key: str,
    record: TraceRecord,
) -> FeatureValue:
    value = evaluation.get(key)
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise ValueError(f"Trace {record.trace_id} has unsupported feature value {key}.")


def _warnings(evaluation: dict[str, Any]) -> list[str]:
    warnings = evaluation.get("warnings", [])
    if not isinstance(warnings, list):
        return []
    return [warning for warning in warnings if isinstance(warning, str)]
