from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.evolution.archive import (
    DEFAULT_ELITE_FEATURE_KEYS,
    build_evolution_archive,
    write_evolution_archive,
)
from agades_pqc_gym.traces.schema import TraceRecord


def test_archive_keeps_best_accepted_candidate_per_feature_cell() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    records = [
        _record(
            plan=plan,
            candidate_id="slow",
            score=-120.0,
            attack_type="primal_usvp",
            memory_bucket="low",
            accepted=True,
        ),
        _record(
            plan=plan,
            candidate_id="fast",
            score=-90.0,
            attack_type="primal_usvp",
            memory_bucket="low",
            accepted=True,
        ),
        _record(
            plan=plan,
            candidate_id="high-memory",
            score=-100.0,
            attack_type="primal_usvp",
            memory_bucket="high",
            accepted=True,
        ),
        _record(
            plan=plan,
            candidate_id="invalid",
            score=0.0,
            attack_type="primal_usvp",
            memory_bucket="low",
            accepted=False,
            evaluation_status="invalid",
        ),
    ]

    archive = build_evolution_archive(records, run_id="unit-evolution")

    assert archive.schema_version == "agades.pqc.evolution_archive.v1"
    assert archive.feature_keys == list(DEFAULT_ELITE_FEATURE_KEYS)
    assert archive.summary == {
        "accepted_count": 3,
        "elite_count": 2,
        "evaluated_count": 4,
        "rejected_count": 1,
    }
    assert archive.global_best is not None
    assert archive.global_best.candidate_id == "fast"
    assert archive.global_best.combined_score == -90.0
    assert {
        elite.candidate_id for elite in archive.elites
    } == {"fast", "high-memory"}


def test_write_evolution_archive_is_deterministic_json(tmp_path: Path) -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    records = [
        _record(
            plan=plan,
            candidate_id="candidate",
            score=-100.0,
            attack_type="primal_usvp",
            memory_bucket="low",
            accepted=True,
        )
    ]
    out = tmp_path / "archive.json"

    archive = write_evolution_archive(records, out, run_id="deterministic")

    assert out.read_text() == archive.model_dump_json(indent=2) + "\n"
    assert "feature_family=LWE" in out.read_text()
    assert "feature_attack_type=primal_usvp" in out.read_text()


def _record(
    *,
    plan: AttackPlan,
    candidate_id: str,
    score: float,
    attack_type: str,
    memory_bucket: str,
    accepted: bool,
    evaluation_status: str = "ok",
) -> TraceRecord:
    return TraceRecord.from_evaluation(
        run_id="unit-evolution",
        candidate_id=candidate_id,
        parent_id=None,
        generation=0,
        mutation_summary="unit test",
        attack_plan=plan,
        evaluation={
            "combined_score": score,
            "evaluation_status": evaluation_status,
            "feature_family": plan.target.family.value,
            "feature_attack_type": attack_type,
            "feature_memory_bucket": memory_bucket,
            "feature_assumption_bucket": "some",
            "feature_estimator_model": "mock-lattice-estimator",
            "valid": accepted,
        },
        accepted=accepted,
        public_release_ok=accepted,
        redaction_reason=None if accepted else "invalid",
    )
