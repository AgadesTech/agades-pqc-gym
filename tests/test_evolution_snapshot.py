import json
from pathlib import Path

import pytest

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.evolution.archive import build_evolution_archive
from agades_pqc_gym.evolution.scheduler import write_heldout_review_log
from agades_pqc_gym.evolution.snapshot import (
    PRIVATE_ARCHIVE_SNAPSHOT_SCHEMA,
    build_private_archive_snapshot,
    write_private_archive_snapshot,
)
from agades_pqc_gym.integrations.private_run_policy import build_private_run_policy
from agades_pqc_gym.traces.schema import TraceRecord


def test_write_private_archive_snapshot_records_digest_only_manifest(
    tmp_path: Path,
) -> None:
    archive_path, trace_path = _archive_and_trace(tmp_path)
    policy = build_private_run_policy()
    review_log_path = _review_log(tmp_path, policy)
    out = Path("private/runs/archive_snapshot.json")

    snapshot = write_private_archive_snapshot(
        out,
        archive_path=archive_path,
        source_trace_path=trace_path,
        review_log_path=review_log_path,
        policy=policy,
        root=tmp_path,
        run_id="training-snapshot",
    )

    written = json.loads((tmp_path / out).read_text(encoding="utf-8"))

    assert written == snapshot
    assert snapshot["schema_version"] == PRIVATE_ARCHIVE_SNAPSHOT_SCHEMA
    assert snapshot["run_id"] == "training-snapshot"
    assert snapshot["snapshot"] == {
        "path": "private/runs/archive_snapshot.json",
        "private": True,
    }
    assert snapshot["inputs"]["archive"]["path"] == (
        "private/runs/evolution_archive.json"
    )
    assert snapshot["inputs"]["archive"]["schema_version"] == (
        "agades.pqc.evolution_archive.v1"
    )
    assert len(snapshot["inputs"]["archive"]["sha256"]) == 64
    assert snapshot["inputs"]["archive"]["size_bytes"] > 0
    assert snapshot["inputs"]["source_trace"]["path"] == (
        "private/traces/evolution_trace.jsonl"
    )
    assert snapshot["inputs"]["source_trace"]["schema_version"] == (
        "agades.pqc.trace_record.v1"
    )
    assert snapshot["inputs"]["source_trace"]["record_count"] == 1
    assert len(snapshot["inputs"]["source_trace"]["sha256"]) == 64
    assert snapshot["inputs"]["review_log"]["path"] == "private/runs/review_log.json"
    assert snapshot["inputs"]["review_log"]["schema_version"] == (
        "agades.pqc.heldout_review_log.v1"
    )
    assert snapshot["inputs"]["review_log"]["approval_gates"] == [
        "heldout-target-review",
        "private-run-policy-review",
        "publication-export-review",
        "retention-owner-review",
    ]
    assert len(snapshot["inputs"]["review_log"]["sha256"]) == 64
    assert snapshot["trace_link_integrity"] == {
        "archive_elite_count": 1,
        "complete": True,
        "missing_trace_count": 0,
        "source_trace_record_count": 1,
    }
    assert snapshot["retention"] == {
        "archive_snapshot_max_age_days": 90,
        "delete_expired_private_runs": True,
        "private_trace_max_age_days": 30,
        "review_log_required": True,
    }
    assert snapshot["safety"] == {
        "arbitrary_code_execution": False,
        "contains_attack_plans": False,
        "contains_candidate_sources": False,
        "contains_trace_payloads": False,
        "external_network_access": False,
        "publishes_private_trace_outputs": False,
        "writes_only_allowed_private_roots": True,
    }
    encoded_snapshot = json.dumps(snapshot)
    assert '"attack_plan":' not in encoded_snapshot
    assert '"operators":' not in encoded_snapshot
    assert snapshot["summary"] == {
        "artifact_count": 3,
        "elite_count": 1,
        "private_snapshot": True,
        "public_release_ok": False,
    }


def test_private_archive_snapshot_rejects_public_output_path(
    tmp_path: Path,
) -> None:
    archive_path, trace_path = _archive_and_trace(tmp_path)
    policy = build_private_run_policy()

    with pytest.raises(ValueError, match="forbidden public root"):
        write_private_archive_snapshot(
            Path("public/archive_snapshot.json"),
            archive_path=archive_path,
            source_trace_path=trace_path,
            review_log_path=_review_log(tmp_path, policy),
            policy=policy,
            root=tmp_path,
        )


def test_private_archive_snapshot_rejects_review_log_without_required_gates(
    tmp_path: Path,
) -> None:
    archive_path, trace_path = _archive_and_trace(tmp_path)
    policy = build_private_run_policy()
    partial_review_log = Path("private/runs/partial_review_log.json")
    write_heldout_review_log(
        tmp_path / partial_review_log,
        approvals=["private-run-policy-review"],
        reviewed_by="unit-test-reviewer",
        review_id="partial-review",
    )

    with pytest.raises(ValueError, match="review log lacks required approvals"):
        build_private_archive_snapshot(
            archive_path=archive_path,
            source_trace_path=trace_path,
            review_log_path=partial_review_log,
            policy=policy,
            root=tmp_path,
        )


def test_private_archive_snapshot_rejects_missing_elite_trace_link(
    tmp_path: Path,
) -> None:
    archive_path, trace_path = _archive_and_trace(tmp_path)
    policy = build_private_run_policy()
    archive = json.loads((tmp_path / archive_path).read_text(encoding="utf-8"))
    archive["elites"][0]["trace_id"] = "missing-trace"
    archive["global_best"]["trace_id"] = "missing-trace"
    (tmp_path / archive_path).write_text(
        json.dumps(archive, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="archive elite trace links are incomplete"):
        build_private_archive_snapshot(
            archive_path=archive_path,
            source_trace_path=trace_path,
            review_log_path=_review_log(tmp_path, policy),
            policy=policy,
            root=tmp_path,
        )


def test_private_archive_snapshot_rejects_public_input_artifact(
    tmp_path: Path,
) -> None:
    archive_path, trace_path = _archive_and_trace(tmp_path)
    policy = build_private_run_policy()
    public_trace = Path("docs/evolution_trace.jsonl")
    (tmp_path / "docs").mkdir()
    (tmp_path / public_trace).write_text(
        (tmp_path / trace_path).read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="forbidden public input root"):
        build_private_archive_snapshot(
            archive_path=archive_path,
            source_trace_path=public_trace,
            review_log_path=_review_log(tmp_path, policy),
            policy=policy,
            root=tmp_path,
        )


def _review_log(tmp_path: Path, policy: dict) -> Path:
    review_log_path = Path("private/runs/review_log.json")
    write_heldout_review_log(
        tmp_path / review_log_path,
        approvals=policy["scheduler_policy"]["approval_gates"],
        reviewed_by="unit-test-reviewer",
        review_id="unit-test-review",
    )
    return review_log_path


def _archive_and_trace(tmp_path: Path) -> tuple[Path, Path]:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text(
            encoding="utf-8"
        )
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
    archive_path = Path("private/runs/evolution_archive.json")
    trace_path = Path("private/traces/evolution_trace.jsonl")
    archive = build_evolution_archive([source_record], run_id="training")
    (tmp_path / archive_path).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / trace_path).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / archive_path).write_text(
        archive.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    (tmp_path / trace_path).write_text(
        source_record.model_dump_json() + "\n",
        encoding="utf-8",
    )
    return archive_path, trace_path
