import json
from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.evolution.archive import build_evolution_archive
from agades_pqc_gym.evolution.rescore import (
    HELDOUT_RESCORE_SCHEMA,
    build_heldout_rescore,
    write_heldout_rescore,
)
from agades_pqc_gym.traces.schema import TraceRecord


def test_heldout_rescore_aggregates_scores_for_archive_elites() -> None:
    plan = _toy_plan()
    training_records = [
        _record(
            plan=plan,
            run_id="training",
            candidate_id="fast",
            parent_id=None,
            score=-90.0,
            accepted=True,
        ),
        _record(
            plan=plan,
            run_id="training",
            candidate_id="slow",
            parent_id=None,
            score=-120.0,
            accepted=True,
        ),
    ]
    archive = build_evolution_archive(training_records, run_id="training")
    heldout_records = [
        _record(
            plan=plan,
            run_id="heldout",
            candidate_id="fast-heldout-a",
            parent_id="fast",
            score=-100.0,
            accepted=True,
        ),
        _record(
            plan=plan,
            run_id="heldout",
            candidate_id="fast-heldout-b",
            parent_id="fast",
            score=-110.0,
            accepted=True,
        ),
        _record(
            plan=plan,
            run_id="heldout",
            candidate_id="unrelated-heldout",
            parent_id="not-an-elite",
            score=-1.0,
            accepted=True,
        ),
    ]

    report = build_heldout_rescore(
        archive,
        heldout_records,
        run_id="heldout-rescore",
    )

    assert report.schema_version == HELDOUT_RESCORE_SCHEMA
    assert report.summary == {
        "elite_count": 1,
        "heldout_record_count": 3,
        "matched_heldout_record_count": 2,
        "unmatched_heldout_record_count": 1,
        "rescored_elite_count": 1,
        "missing_heldout_elite_count": 0,
        "no_accepted_heldout_elite_count": 0,
    }
    assert report.global_best_by_heldout is not None
    assert report.global_best_by_heldout.candidate_id == "fast"
    rescore = report.records[0]
    assert rescore.candidate_id == "fast"
    assert rescore.heldout_status == "rescored"
    assert rescore.heldout_scores == [-100.0, -110.0]
    assert rescore.heldout_mean_combined_score == -105.0
    assert rescore.heldout_min_combined_score == -110.0
    assert rescore.heldout_max_combined_score == -100.0
    assert rescore.generalization_gap == 15.0


def test_heldout_rescore_reports_missing_and_rejected_evaluations() -> None:
    plan = _toy_plan()
    training_records = [
        _record(
            plan=plan,
            run_id="training",
            candidate_id="no-accepted",
            parent_id=None,
            score=-90.0,
            accepted=True,
            memory_bucket="low",
        ),
        _record(
            plan=plan,
            run_id="training",
            candidate_id="missing",
            parent_id=None,
            score=-95.0,
            accepted=True,
            memory_bucket="high",
        ),
    ]
    archive = build_evolution_archive(training_records, run_id="training")
    heldout_records = [
        _record(
            plan=plan,
            run_id="heldout",
            candidate_id="no-accepted-heldout",
            parent_id="no-accepted",
            score=-1_000_000_000.0,
            accepted=False,
            evaluation_status="invalid",
            memory_bucket="low",
        ),
    ]

    report = build_heldout_rescore(
        archive,
        heldout_records,
        run_id="heldout-rescore",
    )

    assert report.global_best_by_heldout is None
    assert report.summary["rescored_elite_count"] == 0
    assert report.summary["missing_heldout_elite_count"] == 1
    assert report.summary["no_accepted_heldout_elite_count"] == 1
    by_candidate = {record.candidate_id: record for record in report.records}
    assert by_candidate["missing"].heldout_status == "missing_heldout"
    assert by_candidate["no-accepted"].heldout_status == "no_accepted_heldout"


def test_write_heldout_rescore_is_deterministic_json(tmp_path: Path) -> None:
    plan = _toy_plan()
    archive = build_evolution_archive(
        [
            _record(
                plan=plan,
                run_id="training",
                candidate_id="candidate",
                parent_id=None,
                score=-90.0,
                accepted=True,
            )
        ],
        run_id="training",
    )
    heldout_records = [
        _record(
            plan=plan,
            run_id="heldout",
            candidate_id="candidate-heldout",
            parent_id="candidate",
            score=-92.0,
            accepted=True,
        )
    ]
    out = tmp_path / "heldout_rescore.json"

    report = write_heldout_rescore(
        archive,
        heldout_records,
        out,
        run_id="heldout-rescore",
    )

    assert json.loads(out.read_text()) == report.model_dump(mode="json")
    assert out.read_text() == report.model_dump_json(indent=2) + "\n"


def _toy_plan() -> AttackPlan:
    return AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )


def _record(
    *,
    plan: AttackPlan,
    run_id: str,
    candidate_id: str,
    parent_id: str | None,
    score: float,
    accepted: bool,
    evaluation_status: str = "ok",
    memory_bucket: str = "low",
) -> TraceRecord:
    return TraceRecord.from_evaluation(
        run_id=run_id,
        candidate_id=candidate_id,
        parent_id=parent_id,
        generation=0,
        mutation_summary="unit test",
        attack_plan=plan,
        evaluation={
            "combined_score": score,
            "evaluation_status": evaluation_status,
            "feature_family": plan.target.family.value,
            "feature_attack_type": "primal_usvp",
            "feature_memory_bucket": memory_bucket,
            "feature_assumption_bucket": "some",
            "feature_estimator_model": "mock-lattice-estimator",
            "valid": accepted,
        },
        accepted=accepted,
        public_release_ok=accepted,
        redaction_reason=None if accepted else "invalid",
    )
