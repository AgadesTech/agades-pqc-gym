import json
from pathlib import Path

import pytest

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.evolution.archive import build_evolution_archive
from agades_pqc_gym.evolution.cron import (
    HELDOUT_CRON_PLAN_SCHEMA,
    build_heldout_cron_plan,
    write_heldout_cron_plan,
)
from agades_pqc_gym.evolution.scheduler import (
    write_heldout_review_log,
    write_heldout_schedule,
)
from agades_pqc_gym.integrations.private_run_policy import build_private_run_policy
from agades_pqc_gym.traces.schema import TraceRecord


def test_build_heldout_cron_plan_requires_reviewed_cron_trigger(
    tmp_path: Path,
) -> None:
    schedule_path, policy = _write_schedule(tmp_path, trigger="manual_reviewed")

    with pytest.raises(ValueError, match="local_cron_after_review"):
        build_heldout_cron_plan(
            schedule_path=Path("private/runs/heldout_schedule.json"),
            policy=policy,
            policy_path=Path("docs/private_run_policy.json"),
            minute=17,
            every_hours=6,
            log_path=Path("private/runs/heldout_cron.log"),
            root=tmp_path,
        )

    assert schedule_path.exists()


def test_build_heldout_cron_plan_creates_private_manual_install_plan(
    tmp_path: Path,
) -> None:
    _schedule_path, policy = _write_schedule(
        tmp_path,
        trigger="local_cron_after_review",
    )

    plan = build_heldout_cron_plan(
        schedule_path=Path("private/runs/heldout_schedule.json"),
        policy=policy,
        policy_path=Path("docs/private_run_policy.json"),
        minute=17,
        every_hours=6,
        log_path=Path("private/runs/heldout_cron.log"),
        root=tmp_path,
    )

    assert plan["schema_version"] == HELDOUT_CRON_PLAN_SCHEMA
    assert plan["schedule"] == {
        "outputs": {
            "heldout_trace": "private/traces/heldout_trace.jsonl",
            "rescore_report": "private/reports/heldout_rescore.json",
        },
        "path": "private/runs/heldout_schedule.json",
        "run_id": "training-heldout-schedule",
        "trigger": "local_cron_after_review",
        "ready_to_run": True,
        "review_log_path": "private/runs/review_log.json",
    }
    assert plan["cron"] == {
        "expression": "17 */6 * * *",
        "minute": 17,
        "every_hours": 6,
        "timezone": "local",
    }
    assert plan["command"]["argv"] == [
        "agades-pqc",
        "heldout-run-schedule",
        "private/runs/heldout_schedule.json",
        "--policy",
        "docs/private_run_policy.json",
    ]
    assert plan["command"]["working_directory"] == tmp_path.resolve().as_posix()
    assert "agades-pqc heldout-run-schedule" in plan["command"]["crontab_entry"]
    assert "private/runs/heldout_cron.log" in plan["command"]["crontab_entry"]
    assert plan["installation"] == {
        "writes_system_crontab": False,
        "requires_manual_install": True,
    }
    assert plan["execution_safety"] == {
        "arbitrary_code_execution": False,
        "external_network_access": False,
        "publishes_private_trace_outputs": False,
    }


def test_write_heldout_cron_plan_rejects_public_plan_or_log_path(
    tmp_path: Path,
) -> None:
    _schedule_path, policy = _write_schedule(
        tmp_path,
        trigger="local_cron_after_review",
    )

    with pytest.raises(ValueError, match="forbidden public root"):
        write_heldout_cron_plan(
            Path("public/heldout_cron_plan.json"),
            schedule_path=Path("private/runs/heldout_schedule.json"),
            policy=policy,
            policy_path=Path("docs/private_run_policy.json"),
            minute=17,
            every_hours=6,
            log_path=Path("private/runs/heldout_cron.log"),
            root=tmp_path,
        )

    with pytest.raises(ValueError, match="forbidden public root"):
        write_heldout_cron_plan(
            Path("private/runs/heldout_cron_plan.json"),
            schedule_path=Path("private/runs/heldout_schedule.json"),
            policy=policy,
            policy_path=Path("docs/private_run_policy.json"),
            minute=17,
            every_hours=6,
            log_path=Path("public/heldout_cron.log"),
            root=tmp_path,
        )


def test_build_heldout_cron_plan_revalidates_review_log_digest(
    tmp_path: Path,
) -> None:
    _schedule_path, policy = _write_schedule(
        tmp_path,
        trigger="local_cron_after_review",
    )
    review_log_path = tmp_path / "private" / "runs" / "review_log.json"
    review_log = json.loads(review_log_path.read_text(encoding="utf-8"))
    review_log["entries"][0]["reviewer"] = "changed-after-schedule"
    review_log_path.write_text(
        json.dumps(review_log, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="review log digest drift"):
        build_heldout_cron_plan(
            schedule_path=Path("private/runs/heldout_schedule.json"),
            policy=policy,
            policy_path=Path("docs/private_run_policy.json"),
            minute=17,
            every_hours=6,
            log_path=Path("private/runs/heldout_cron.log"),
            root=tmp_path,
        )


def test_build_heldout_cron_plan_rejects_unbounded_intervals(
    tmp_path: Path,
) -> None:
    _schedule_path, policy = _write_schedule(
        tmp_path,
        trigger="local_cron_after_review",
    )

    with pytest.raises(ValueError, match="cron minute"):
        build_heldout_cron_plan(
            schedule_path=Path("private/runs/heldout_schedule.json"),
            policy=policy,
            policy_path=Path("docs/private_run_policy.json"),
            minute=60,
            every_hours=6,
            log_path=Path("private/runs/heldout_cron.log"),
            root=tmp_path,
        )
    with pytest.raises(ValueError, match="cron hour interval"):
        build_heldout_cron_plan(
            schedule_path=Path("private/runs/heldout_schedule.json"),
            policy=policy,
            policy_path=Path("docs/private_run_policy.json"),
            minute=17,
            every_hours=25,
            log_path=Path("private/runs/heldout_cron.log"),
            root=tmp_path,
        )


def _write_schedule(tmp_path: Path, *, trigger: str) -> tuple[Path, dict]:
    archive_path, source_trace_path = _archive_and_trace(tmp_path)
    policy = build_private_run_policy()
    review_log_path = tmp_path / "private" / "runs" / "review_log.json"
    write_heldout_review_log(
        review_log_path,
        approvals=policy["scheduler_policy"]["approval_gates"],
        reviewed_by="unit-test-reviewer",
        review_id="unit-test-review",
        policy=policy,
        root=tmp_path,
    )
    schedule_path = tmp_path / "private" / "runs" / "heldout_schedule.json"
    write_heldout_schedule(
        schedule_path,
        archive_path=archive_path,
        source_trace_path=source_trace_path,
        heldout_targets_path=(
            Path.cwd() / "benchmarks" / "lattice_toy_lwe" / "lwe_n96_q769.json"
        ),
        policy=policy,
        trace_out=Path("private/traces/heldout_trace.jsonl"),
        rescore_out=Path("private/reports/heldout_rescore.json"),
        approvals=policy["scheduler_policy"]["approval_gates"],
        review_log_path=Path("private/runs/review_log.json"),
        trigger=trigger,
        root=tmp_path,
    )
    return schedule_path, policy


def _archive_and_trace(tmp_path: Path) -> tuple[Path, Path]:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    source_record = TraceRecord.from_evaluation(
        run_id="training",
        candidate_id="candidate",
        parent_id=None,
        generation=0,
        mutation_summary="unit test",
        attack_plan=plan,
        evaluation={
            "combined_score": -90.0,
            "evaluation_status": "ok",
            "feature_family": plan.target.family.value,
            "feature_attack_type": "primal_usvp",
            "feature_memory_bucket": "low",
            "feature_assumption_bucket": "some",
            "feature_estimator_model": "mock-lattice-estimator",
            "valid": True,
        },
        accepted=True,
        public_release_ok=True,
        redaction_reason=None,
    )
    archive_path = tmp_path / "archive.json"
    source_trace_path = tmp_path / "source_trace.jsonl"
    archive = build_evolution_archive([source_record], run_id="training")
    archive_path.write_text(archive.model_dump_json(indent=2) + "\n")
    source_trace_path.write_text(source_record.model_dump_json() + "\n")
    return archive_path, source_trace_path
