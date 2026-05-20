from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from statistics import fmean
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from agades_pqc_gym.core.trace_record import TraceRecord
from agades_pqc_gym.evolution.archive import EliteRecord, EvolutionArchive

HELDOUT_RESCORE_SCHEMA = "agades.pqc.heldout_rescore.v1"
HeldoutStatus = Literal["missing_heldout", "no_accepted_heldout", "rescored"]


class HeldoutRescoreRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cell_key: str
    candidate_id: str
    trace_id: str
    attack_plan_id: str
    target_family: str
    train_combined_score: float
    heldout_status: HeldoutStatus
    heldout_evaluations: int = Field(ge=0)
    heldout_accepted_count: int = Field(ge=0)
    heldout_rejected_count: int = Field(ge=0)
    heldout_scores: list[float]
    heldout_mean_combined_score: float | None
    heldout_min_combined_score: float | None
    heldout_max_combined_score: float | None
    generalization_gap: float | None
    heldout_trace_ids: list[str]
    warnings: list[str] = Field(default_factory=list)


class HeldoutRescoreReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = HELDOUT_RESCORE_SCHEMA
    run_id: str
    archive_run_id: str
    summary: dict[str, int]
    global_best_by_heldout: HeldoutRescoreRecord | None
    records: list[HeldoutRescoreRecord]


def build_heldout_rescore(
    archive: EvolutionArchive,
    heldout_records: Iterable[TraceRecord],
    *,
    run_id: str,
) -> HeldoutRescoreReport:
    heldout_records_list = list(heldout_records)
    elite_ids = {elite.candidate_id for elite in archive.elites}
    by_parent: dict[str, list[TraceRecord]] = {elite_id: [] for elite_id in elite_ids}
    unmatched_count = 0

    for record in heldout_records_list:
        if record.parent_id in elite_ids:
            by_parent[record.parent_id].append(record)
        else:
            unmatched_count += 1

    rescored_records = [
        _build_rescore_record(elite, by_parent[elite.candidate_id])
        for elite in archive.elites
    ]
    global_best = _global_best_by_heldout(rescored_records)
    matched_count = sum(record.heldout_evaluations for record in rescored_records)
    return HeldoutRescoreReport(
        run_id=run_id,
        archive_run_id=archive.run_id,
        summary={
            "elite_count": len(archive.elites),
            "heldout_record_count": len(heldout_records_list),
            "matched_heldout_record_count": matched_count,
            "unmatched_heldout_record_count": unmatched_count,
            "rescored_elite_count": sum(
                1
                for record in rescored_records
                if record.heldout_status == "rescored"
            ),
            "missing_heldout_elite_count": sum(
                1
                for record in rescored_records
                if record.heldout_status == "missing_heldout"
            ),
            "no_accepted_heldout_elite_count": sum(
                1
                for record in rescored_records
                if record.heldout_status == "no_accepted_heldout"
            ),
        },
        global_best_by_heldout=global_best,
        records=rescored_records,
    )


def write_heldout_rescore(
    archive: EvolutionArchive,
    heldout_records: Iterable[TraceRecord],
    out: Path,
    *,
    run_id: str,
) -> HeldoutRescoreReport:
    report = build_heldout_rescore(archive, heldout_records, run_id=run_id)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return report


def _build_rescore_record(
    elite: EliteRecord,
    heldout_records: list[TraceRecord],
) -> HeldoutRescoreRecord:
    accepted_scores = [
        _required_heldout_score(record)
        for record in heldout_records
        if record.accepted
    ]
    if not heldout_records:
        status = "missing_heldout"
    elif not accepted_scores:
        status = "no_accepted_heldout"
    else:
        status = "rescored"

    heldout_mean = _rounded_mean(accepted_scores)
    return HeldoutRescoreRecord(
        cell_key=elite.cell_key,
        candidate_id=elite.candidate_id,
        trace_id=elite.trace_id,
        attack_plan_id=elite.attack_plan_id,
        target_family=elite.target_family,
        train_combined_score=elite.combined_score,
        heldout_status=status,
        heldout_evaluations=len(heldout_records),
        heldout_accepted_count=len(accepted_scores),
        heldout_rejected_count=len(heldout_records) - len(accepted_scores),
        heldout_scores=accepted_scores,
        heldout_mean_combined_score=heldout_mean,
        heldout_min_combined_score=round(min(accepted_scores), 4)
        if accepted_scores
        else None,
        heldout_max_combined_score=round(max(accepted_scores), 4)
        if accepted_scores
        else None,
        generalization_gap=round(elite.combined_score - heldout_mean, 4)
        if heldout_mean is not None
        else None,
        heldout_trace_ids=[record.trace_id for record in heldout_records],
        warnings=_heldout_warnings(heldout_records),
    )


def _required_heldout_score(record: TraceRecord) -> float:
    value: Any = record.evaluation.get("combined_score")
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(
            f"Accepted held-out trace {record.trace_id} lacks numeric "
            "evaluation field combined_score."
        )
    return round(float(value), 4)


def _rounded_mean(scores: list[float]) -> float | None:
    if not scores:
        return None
    return round(float(fmean(scores)), 4)


def _heldout_warnings(records: list[TraceRecord]) -> list[str]:
    warnings: list[str] = []
    for record in records:
        raw_warnings = record.evaluation.get("warnings", [])
        if isinstance(raw_warnings, list):
            warnings.extend(
                warning for warning in raw_warnings if isinstance(warning, str)
            )
        if not record.accepted and record.redaction_reason:
            warnings.append(record.redaction_reason)
    return sorted(set(warnings))


def _global_best_by_heldout(
    records: list[HeldoutRescoreRecord],
) -> HeldoutRescoreRecord | None:
    rescored = [
        record
        for record in records
        if record.heldout_mean_combined_score is not None
    ]
    if not rescored:
        return None
    return sorted(
        rescored,
        key=lambda record: (
            -record.heldout_mean_combined_score,
            record.candidate_id,
        ),
    )[0]
