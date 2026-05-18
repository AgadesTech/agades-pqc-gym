import json
from pathlib import Path

import pytest

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.evaluators.mock_estimator import MockEstimatorAdapter
from agades_pqc_gym.evolution.archive import build_evolution_archive
from agades_pqc_gym.evolution.heldout_review_packet import (
    HELDOUT_REVIEW_PACKET_SCHEMA,
    verify_heldout_review_packet,
    write_heldout_review_packet,
)
from agades_pqc_gym.evolution.scheduler import (
    HELDOUT_REVIEW_LOG_SCHEMA,
    build_heldout_schedule,
    run_heldout_schedule,
    write_heldout_review_log,
    write_heldout_schedule,
)
from agades_pqc_gym.integrations.private_run_policy import build_private_run_policy
from agades_pqc_gym.traces.schema import TraceRecord


def test_build_heldout_schedule_requires_policy_approvals(
    tmp_path: Path,
) -> None:
    archive_path, source_trace_path = _archive_and_trace(tmp_path)
    policy = build_private_run_policy()

    with pytest.raises(ValueError, match="missing scheduler approval gates"):
        build_heldout_schedule(
            archive_path=archive_path,
            source_trace_path=source_trace_path,
            heldout_targets_path=Path("benchmarks/lattice_toy_lwe/lwe_n96_q769.json"),
            policy=policy,
            trace_out=Path("private/traces/heldout_trace.jsonl"),
            rescore_out=Path("private/reports/heldout_rescore.json"),
            approvals=["private-run-policy-review"],
            review_log_path=_review_log(tmp_path, policy),
            root=tmp_path,
        )


def test_build_heldout_schedule_requires_private_review_log(
    tmp_path: Path,
) -> None:
    archive_path, source_trace_path = _archive_and_trace(tmp_path)
    policy = build_private_run_policy()

    with pytest.raises(ValueError, match="review log required"):
        build_heldout_schedule(
            archive_path=archive_path,
            source_trace_path=source_trace_path,
            heldout_targets_path=Path("benchmarks/lattice_toy_lwe/lwe_n96_q769.json"),
            policy=policy,
            trace_out=Path("private/traces/heldout_trace.jsonl"),
            rescore_out=Path("private/reports/heldout_rescore.json"),
            approvals=policy["scheduler_policy"]["approval_gates"],
            root=tmp_path,
        )


def test_build_heldout_schedule_rejects_public_output_paths(
    tmp_path: Path,
) -> None:
    archive_path, source_trace_path = _archive_and_trace(tmp_path)
    policy = build_private_run_policy()

    with pytest.raises(ValueError, match="forbidden public root"):
        build_heldout_schedule(
            archive_path=archive_path,
            source_trace_path=source_trace_path,
            heldout_targets_path=Path("benchmarks/lattice_toy_lwe/lwe_n96_q769.json"),
            policy=policy,
            trace_out=Path("public/heldout_trace.jsonl"),
            rescore_out=Path("private/reports/heldout_rescore.json"),
            approvals=policy["scheduler_policy"]["approval_gates"],
            review_log_path=_review_log(tmp_path, policy),
            root=tmp_path,
        )


def test_build_heldout_schedule_rejects_public_review_log_path(
    tmp_path: Path,
) -> None:
    archive_path, source_trace_path = _archive_and_trace(tmp_path)
    policy = build_private_run_policy()
    public_review_log = tmp_path / "docs" / "review_log.json"
    write_heldout_review_log(
        public_review_log,
        approvals=policy["scheduler_policy"]["approval_gates"],
        reviewed_by="unit-test-reviewer",
        review_id="unit-test-review",
    )

    with pytest.raises(ValueError, match="forbidden public root"):
        build_heldout_schedule(
            archive_path=archive_path,
            source_trace_path=source_trace_path,
            heldout_targets_path=Path("benchmarks/lattice_toy_lwe/lwe_n96_q769.json"),
            policy=policy,
            trace_out=Path("private/traces/heldout_trace.jsonl"),
            rescore_out=Path("private/reports/heldout_rescore.json"),
            approvals=policy["scheduler_policy"]["approval_gates"],
            review_log_path=Path("docs/review_log.json"),
            root=tmp_path,
        )


def test_write_heldout_schedule_rejects_public_schedule_path(
    tmp_path: Path,
) -> None:
    archive_path, source_trace_path = _archive_and_trace(tmp_path)
    policy = build_private_run_policy()

    with pytest.raises(ValueError, match="forbidden public root"):
        write_heldout_schedule(
            Path("public/heldout_schedule.json"),
            archive_path=archive_path,
            source_trace_path=source_trace_path,
            heldout_targets_path=Path("benchmarks/lattice_toy_lwe/lwe_n96_q769.json"),
            policy=policy,
            trace_out=Path("private/traces/heldout_trace.jsonl"),
            rescore_out=Path("private/reports/heldout_rescore.json"),
            approvals=policy["scheduler_policy"]["approval_gates"],
            review_log_path=_review_log(tmp_path, policy),
            root=tmp_path,
        )


def test_build_heldout_schedule_creates_reviewed_private_schedule(
    tmp_path: Path,
) -> None:
    archive_path, source_trace_path = _archive_and_trace(tmp_path)
    policy = build_private_run_policy()

    schedule = build_heldout_schedule(
        archive_path=archive_path,
        source_trace_path=source_trace_path,
        heldout_targets_path=(
            Path.cwd() / "benchmarks" / "lattice_toy_lwe" / "lwe_n96_q769.json"
        ),
        policy=policy,
        trace_out=Path("private/traces/heldout_trace.jsonl"),
        rescore_out=Path("private/reports/heldout_rescore.json"),
        approvals=policy["scheduler_policy"]["approval_gates"],
        review_log_path=_review_log(tmp_path, policy),
        root=tmp_path,
    )

    assert schedule["schema_version"] == "agades.pqc.heldout_schedule.v1"
    assert schedule["ready_to_run"] is True
    assert schedule["trigger"] == "manual_reviewed"
    assert schedule["approval_gates"] == {
        "provided": [
            "heldout-target-review",
            "private-run-policy-review",
            "publication-export-review",
            "retention-owner-review",
        ],
        "required": [
            "heldout-target-review",
            "private-run-policy-review",
            "publication-export-review",
            "retention-owner-review",
        ],
    }
    assert schedule["review_log"]["schema_version"] == HELDOUT_REVIEW_LOG_SCHEMA
    assert schedule["review_log"]["path"] == "private/runs/review_log.json"
    assert schedule["review_log"]["approval_gates"] == [
        "heldout-target-review",
        "private-run-policy-review",
        "publication-export-review",
        "retention-owner-review",
    ]
    assert len(schedule["review_log"]["sha256"]) == 64
    assert schedule["summary"] == {
        "archive_elites": 1,
        "heldout_targets": 1,
        "scheduled_candidates": 1,
    }
    assert schedule["outputs"] == {
        "heldout_trace": "private/traces/heldout_trace.jsonl",
        "rescore_report": "private/reports/heldout_rescore.json",
    }
    assert schedule["execution_safety"] == {
        "arbitrary_code_execution": False,
        "external_network_access": False,
        "publishes_private_trace_outputs": False,
        "writes_only_allowed_private_roots": True,
    }
    assert "agades-pqc heldout-batch" in schedule["commands"]["heldout_batch"]
    assert "agades-pqc rescore-archive" in schedule["commands"]["rescore_archive"]


def test_run_heldout_schedule_consumes_manifest_without_shell_execution(
    tmp_path: Path,
) -> None:
    schedule_path, policy = _write_schedule(tmp_path)

    run_report = run_heldout_schedule(
        schedule_path,
        policy=policy,
        estimator=MockEstimatorAdapter(),
        root=tmp_path,
    )

    trace_path = tmp_path / "private" / "traces" / "heldout_trace.jsonl"
    rescore_path = tmp_path / "private" / "reports" / "heldout_rescore.json"
    trace_records = [
        TraceRecord.model_validate_json(line)
        for line in trace_path.read_text(encoding="utf-8").splitlines()
    ]
    rescore = json.loads(rescore_path.read_text(encoding="utf-8"))

    assert run_report["schema_version"] == "agades.pqc.heldout_schedule_run.v1"
    assert run_report["execution"] == {
        "arbitrary_code_execution": False,
        "external_network_access": False,
        "shell_commands_executed": False,
    }
    assert run_report["summary"] == {
        "scheduled_candidates": 1,
        "heldout_records": 1,
        "rescored_elites": 1,
    }
    assert trace_records[0].parent_id == "candidate"
    assert trace_records[0].accepted is True
    assert rescore["summary"]["rescored_elite_count"] == 1


def test_heldout_review_packet_records_digest_only_private_handoff(
    tmp_path: Path,
) -> None:
    schedule_path, policy = _write_schedule(tmp_path)
    run_heldout_schedule(
        schedule_path,
        policy=policy,
        estimator=MockEstimatorAdapter(),
        root=tmp_path,
    )
    out = Path("private/reports/heldout_review_packet.json")

    packet = write_heldout_review_packet(
        out,
        schedule_path=Path("private/runs/heldout_schedule.json"),
        policy=policy,
        root=tmp_path,
        reviewer_label="external-heldout-review",
    )

    written = json.loads((tmp_path / out).read_text(encoding="utf-8"))
    assert written == packet
    assert packet["schema_version"] == HELDOUT_REVIEW_PACKET_SCHEMA
    assert packet["review_status"] == {
        "state": "pending_expert_review",
        "reviewer_label": "external-heldout-review",
        "score_promotion_allowed": False,
        "public_claim_language_approved": False,
    }
    assert packet["artifacts"]["schedule"]["path"] == (
        "private/runs/heldout_schedule.json"
    )
    assert len(packet["artifacts"]["schedule"]["sha256"]) == 64
    assert packet["artifacts"]["heldout_trace"] == {
        "path": "private/traces/heldout_trace.jsonl",
        "schema_version": "agades.pqc.trace_record.v1",
        "sha256": packet["artifacts"]["heldout_trace"]["sha256"],
        "record_count": 1,
    }
    assert len(packet["artifacts"]["heldout_trace"]["sha256"]) == 64
    assert packet["artifacts"]["rescore_report"] == {
        "path": "private/reports/heldout_rescore.json",
        "schema_version": "agades.pqc.heldout_rescore.v1",
        "sha256": packet["artifacts"]["rescore_report"]["sha256"],
    }
    assert len(packet["artifacts"]["rescore_report"]["sha256"]) == 64
    assert packet["review_log"]["approval_gates"] == [
        "heldout-target-review",
        "private-run-policy-review",
        "publication-export-review",
        "retention-owner-review",
    ]
    assert packet["summary"] == {
        "heldout_record_count": 1,
        "rescored_elite_count": 1,
        "review_question_count": 5,
        "schedule_ready": True,
    }
    assert packet["safety"] == {
        "arbitrary_code_execution": False,
        "contains_attack_plans": False,
        "contains_candidate_sources": False,
        "contains_private_scores": False,
        "contains_trace_payloads": False,
        "external_network_access": False,
        "private_report": True,
        "publication_allowed": False,
        "public_release_ok": False,
        "requires_expert_review": True,
        "security_claim": False,
        "shell_commands_executed": False,
    }
    encoded = json.dumps(packet, sort_keys=True)
    assert '"attack_plan":' not in encoded
    assert '"operators":' not in encoded
    assert '"evaluation":' not in encoded
    assert '"combined_score":' not in encoded
    assert '"heldout_scores":' not in encoded
    assert '"generalization_gap":' not in encoded

    verification = verify_heldout_review_packet(
        tmp_path / out,
        schedule_path=tmp_path / "private/runs/heldout_schedule.json",
        policy=policy,
        root=tmp_path,
    )
    assert verification["accepted"] is True
    assert verification["failures"] == []
    assert verification["summary"] == {
        "contains_private_scores": False,
        "failure_count": 0,
        "heldout_record_count": 1,
        "private_report": True,
        "rescored_elite_count": 1,
        "security_claim": False,
    }


def test_heldout_review_packet_rejects_private_score_leakage(
    tmp_path: Path,
) -> None:
    schedule_path, policy = _write_schedule(tmp_path)
    run_heldout_schedule(
        schedule_path,
        policy=policy,
        estimator=MockEstimatorAdapter(),
        root=tmp_path,
    )
    out = Path("private/reports/heldout_review_packet.json")
    packet = write_heldout_review_packet(
        out,
        schedule_path=Path("private/runs/heldout_schedule.json"),
        policy=policy,
        root=tmp_path,
    )
    packet["score_evidence"] = {"heldout_scores": [-92.0]}
    (tmp_path / out).write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verification = verify_heldout_review_packet(
        tmp_path / out,
        schedule_path=tmp_path / "private/runs/heldout_schedule.json",
        policy=policy,
        root=tmp_path,
    )

    assert verification["accepted"] is False
    assert verification["summary"]["contains_private_scores"] is True
    assert any("private score" in failure for failure in verification["failures"])


def test_heldout_review_packet_rejects_public_output_path(
    tmp_path: Path,
) -> None:
    schedule_path, policy = _write_schedule(tmp_path)
    run_heldout_schedule(
        schedule_path,
        policy=policy,
        estimator=MockEstimatorAdapter(),
        root=tmp_path,
    )

    with pytest.raises(ValueError, match="forbidden public root"):
        write_heldout_review_packet(
            Path("public/heldout_review_packet.json"),
            schedule_path=Path("private/runs/heldout_schedule.json"),
            policy=policy,
            root=tmp_path,
        )


def test_heldout_review_packet_verifier_rejects_public_packet_path(
    tmp_path: Path,
) -> None:
    schedule_path, policy = _write_schedule(tmp_path)
    run_heldout_schedule(
        schedule_path,
        policy=policy,
        estimator=MockEstimatorAdapter(),
        root=tmp_path,
    )
    private_out = Path("private/reports/heldout_review_packet.json")
    packet = write_heldout_review_packet(
        private_out,
        schedule_path=Path("private/runs/heldout_schedule.json"),
        policy=policy,
        root=tmp_path,
    )
    public_out = tmp_path / "public/heldout_review_packet.json"
    public_out.parent.mkdir(parents=True)
    public_out.write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verification = verify_heldout_review_packet(
        public_out,
        schedule_path=tmp_path / "private/runs/heldout_schedule.json",
        policy=policy,
        root=tmp_path,
    )

    assert verification["accepted"] is False
    assert any(
        "packet path must be private" in failure
        for failure in verification["failures"]
    )


def test_run_heldout_schedule_rejects_not_ready_manifest(tmp_path: Path) -> None:
    schedule_path, policy = _write_schedule(tmp_path)
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    schedule["ready_to_run"] = False
    schedule_path.write_text(json.dumps(schedule, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="not ready"):
        run_heldout_schedule(
            schedule_path,
            policy=policy,
            estimator=MockEstimatorAdapter(),
            root=tmp_path,
        )


def test_run_heldout_schedule_rejects_command_metadata_drift(
    tmp_path: Path,
) -> None:
    schedule_path, policy = _write_schedule(tmp_path)
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    schedule["commands"]["heldout_batch"] = "python unreviewed_runner.py"
    schedule_path.write_text(json.dumps(schedule, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="does not match structured inputs"):
        run_heldout_schedule(
            schedule_path,
            policy=policy,
            estimator=MockEstimatorAdapter(),
            root=tmp_path,
        )


def test_run_heldout_schedule_rejects_review_log_digest_drift(
    tmp_path: Path,
) -> None:
    schedule_path, policy = _write_schedule(tmp_path)
    review_log_path = tmp_path / "private" / "runs" / "review_log.json"
    review_log = json.loads(review_log_path.read_text(encoding="utf-8"))
    review_log["entries"][0]["reviewer"] = "changed-after-schedule"
    review_log_path.write_text(
        json.dumps(review_log, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="review log digest drift"):
        run_heldout_schedule(
            schedule_path,
            policy=policy,
            estimator=MockEstimatorAdapter(),
            root=tmp_path,
        )


def test_run_heldout_schedule_rejects_review_log_schema_reference_drift(
    tmp_path: Path,
) -> None:
    schedule_path, policy = _write_schedule(tmp_path)
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    schedule["review_log"]["schema_version"] = "agades.pqc.heldout_review_log.v0"
    schedule_path.write_text(
        json.dumps(schedule, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="review log schema drift"):
        run_heldout_schedule(
            schedule_path,
            policy=policy,
            estimator=MockEstimatorAdapter(),
            root=tmp_path,
        )


def _write_schedule(tmp_path: Path) -> tuple[Path, dict]:
    archive_path, source_trace_path = _archive_and_trace(tmp_path)
    policy = build_private_run_policy()
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
        review_log_path=_review_log(tmp_path, policy),
        root=tmp_path,
    )
    return schedule_path, policy


def _review_log(tmp_path: Path, policy: dict) -> Path:
    review_log_path = tmp_path / "private" / "runs" / "review_log.json"
    write_heldout_review_log(
        review_log_path,
        approvals=policy["scheduler_policy"]["approval_gates"],
        reviewed_by="unit-test-reviewer",
        review_id="unit-test-review",
    )
    return Path("private/runs/review_log.json")


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
