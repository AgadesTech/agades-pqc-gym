from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.evolution.campaign import (
    PRIVATE_EVOLUTION_CAMPAIGN_PLAN_SCHEMA,
    PRIVATE_EVOLUTION_CAMPAIGN_PLAN_VERIFICATION_SCHEMA,
    build_private_evolution_campaign_plan,
    verify_private_evolution_campaign_plan,
    write_private_evolution_campaign_plan,
)
from agades_pqc_gym.evolution.scheduler import write_heldout_review_log
from agades_pqc_gym.integrations.private_run_policy import build_private_run_policy

SEED_PLAN = Path("examples/attack_plans/lattice_primal_usvp_toy.json")
HELDOUT_TARGET = Path("benchmarks/lattice_toy_lwe/lwe_n96_q769.json")
CODE_BASED_HELDOUT_TARGET = Path(
    "benchmarks/code_based_toy_isd/toy_syndrome_15_7_w2.json"
)
CODE_BASED_MUTABLE_SEED_PLAN = Path("examples/attack_plans/code_based_prange_toy.json")
SCHEMA_ONLY_SEED_PLAN = Path(
    "examples/attack_plans/lattice_ntru_schema_placeholder.json"
)


def test_private_evolution_campaign_plan_records_reviewed_nonexecuting_workflow(
    tmp_path: Path,
) -> None:
    policy = build_private_run_policy()
    review_log = _review_log(tmp_path, policy)

    plan = build_private_evolution_campaign_plan(
        seed_candidates_path=SEED_PLAN,
        heldout_targets_path=HELDOUT_TARGET,
        policy=policy,
        review_log_path=review_log,
        out=Path("private/runs/manual-campaign/campaign_plan.json"),
        root=tmp_path,
        run_id="manual-campaign",
    )

    assert plan["schema_version"] == PRIVATE_EVOLUTION_CAMPAIGN_PLAN_SCHEMA
    assert plan["run_id"] == "manual-campaign"
    assert plan["plan"] == {
        "path": "private/runs/manual-campaign/campaign_plan.json",
        "private": True,
        "requires_manual_invocation": True,
    }
    assert plan["review_log"]["path"] == "private/runs/review_log.json"
    assert len(plan["review_log"]["sha256"]) == 64
    assert plan["review_log"]["approval_gates"] == [
        "heldout-target-review",
        "private-run-policy-review",
        "publication-export-review",
        "retention-owner-review",
    ]
    assert plan["inputs"]["seed_candidates"]["path"] == SEED_PLAN.as_posix()
    assert plan["inputs"]["seed_candidates"]["json_count"] == 1
    assert len(plan["inputs"]["seed_candidates"]["sha256"]) == 64
    assert plan["inputs"]["heldout_targets"]["path"] == HELDOUT_TARGET.as_posix()
    assert plan["inputs"]["heldout_targets"]["json_count"] == 1
    assert len(plan["inputs"]["heldout_targets"]["sha256"]) == 64
    assert plan["seed_mutation_preflight"] == {
        "candidate_count": 2,
        "generation": 1,
        "max_mutations_per_plan": 4,
        "skipped_count": 0,
        "skipped_reasons": [],
        "source_count": 1,
        "target_families": ["LWE"],
    }
    assert plan["target_compatibility_preflight"] == {
        "compatible_target_families": ["LWE"],
        "coverage_complete": True,
        "heldout_target_count": 1,
        "heldout_target_families": ["LWE"],
        "seed_plan_count": 1,
        "seed_target_families": ["LWE"],
        "uncovered_seed_target_families": [],
    }
    assert plan["summary"] == {
        "compatible_target_family_count": 1,
        "heldout_target_count": 1,
        "seed_family_coverage_complete": True,
        "seed_mutation_candidate_count": 2,
        "seed_plan_count": 1,
        "step_count": 7,
    }
    assert [step["id"] for step in plan["steps"]] == [
        "seed-mutation",
        "seed-evaluation",
        "archive-mutation",
        "archive-snapshot",
        "heldout-schedule",
        "heldout-run",
        "heldout-review-packet",
    ]
    assert all(step["execution_status"] == "not_executed" for step in plan["steps"])
    assert all(isinstance(step["command"]["argv"], list) for step in plan["steps"])
    assert all("&&" not in " ".join(step["command"]["argv"]) for step in plan["steps"])
    assert plan["outputs"] == {
        "archive_mutation_dir": "private/candidates/manual-campaign/archive_mutations",
        "archive_snapshot": "private/runs/manual-campaign/archive_snapshot.json",
        "heldout_rescore": "private/reports/manual-campaign/heldout_rescore.json",
        "heldout_review_packet": (
            "private/reports/manual-campaign/heldout_review_packet.json"
        ),
        "heldout_schedule": "private/runs/manual-campaign/heldout_schedule.json",
        "heldout_trace": "private/traces/manual-campaign/heldout_trace.jsonl",
        "seed_archive": "private/runs/manual-campaign/evolution_archive.json",
        "seed_mutation_dir": "private/candidates/manual-campaign/seed_mutations",
        "seed_trace": "private/traces/manual-campaign/evolution_trace.jsonl",
    }
    assert plan["safety"] == {
        "arbitrary_code_execution": False,
        "contains_attack_plans": False,
        "contains_candidate_sources": False,
        "external_network_access": False,
        "private_plan": True,
        "public_release_ok": False,
        "publishes_private_trace_outputs": False,
        "requires_review_log": True,
        "security_claim": False,
        "shell_commands_executed": False,
        "writes_only_allowed_private_roots": True,
    }
    encoded = json.dumps(plan, sort_keys=True)
    assert '"attack_plan":' not in encoded
    assert '"operators":' not in encoded


def test_private_evolution_campaign_plan_write_and_verify(tmp_path: Path) -> None:
    policy = build_private_run_policy()
    review_log = _review_log(tmp_path, policy)
    out = Path("private/runs/manual-campaign/campaign_plan.json")

    written = write_private_evolution_campaign_plan(
        out,
        seed_candidates_path=SEED_PLAN,
        heldout_targets_path=HELDOUT_TARGET,
        policy=policy,
        review_log_path=review_log,
        root=tmp_path,
        run_id="manual-campaign",
    )
    verification = verify_private_evolution_campaign_plan(
        tmp_path / out,
        policy=policy,
        root=tmp_path,
    )

    assert json.loads((tmp_path / out).read_text(encoding="utf-8")) == written
    assert verification == {
        "schema_version": PRIVATE_EVOLUTION_CAMPAIGN_PLAN_VERIFICATION_SCHEMA,
        "plan_path": (tmp_path / out).as_posix(),
        "accepted": True,
        "summary": {
            "compatible_target_family_count": 1,
            "failure_count": 0,
            "heldout_target_count": 1,
            "private_plan": True,
            "seed_family_coverage_complete": True,
            "seed_mutation_candidate_count": 2,
            "seed_plan_count": 1,
            "step_count": 7,
        },
        "failures": [],
    }


def test_private_evolution_campaign_plan_rejects_public_output_path(
    tmp_path: Path,
) -> None:
    policy = build_private_run_policy()
    review_log = _review_log(tmp_path, policy)
    out = Path("private/runs/manual-campaign/campaign_plan.json")
    write_private_evolution_campaign_plan(
        out,
        seed_candidates_path=SEED_PLAN,
        heldout_targets_path=HELDOUT_TARGET,
        policy=policy,
        review_log_path=review_log,
        root=tmp_path,
        run_id="manual-campaign",
    )
    payload = json.loads((tmp_path / out).read_text(encoding="utf-8"))
    payload["outputs"]["seed_trace"] = "public/evolution_trace.jsonl"
    (tmp_path / out).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verification = verify_private_evolution_campaign_plan(
        tmp_path / out,
        policy=policy,
        root=tmp_path,
    )

    assert verification["accepted"] is False
    assert any(
        "forbidden public root" in failure for failure in verification["failures"]
    )


def test_private_evolution_campaign_plan_rejects_unreviewed_command(
    tmp_path: Path,
) -> None:
    policy = build_private_run_policy()
    review_log = _review_log(tmp_path, policy)
    out = Path("private/runs/manual-campaign/campaign_plan.json")
    write_private_evolution_campaign_plan(
        out,
        seed_candidates_path=SEED_PLAN,
        heldout_targets_path=HELDOUT_TARGET,
        policy=policy,
        review_log_path=review_log,
        root=tmp_path,
        run_id="manual-campaign",
    )
    payload = json.loads((tmp_path / out).read_text(encoding="utf-8"))
    payload["steps"][0]["command"]["argv"] = ["python", "unreviewed.py"]
    (tmp_path / out).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verification = verify_private_evolution_campaign_plan(
        tmp_path / out,
        policy=policy,
        root=tmp_path,
    )

    assert verification["accepted"] is False
    assert any(
        "not allowed by policy" in failure for failure in verification["failures"]
    )


def test_private_evolution_campaign_plan_rejects_allowed_command_role_drift(
    tmp_path: Path,
) -> None:
    policy = build_private_run_policy()
    review_log = _review_log(tmp_path, policy)
    out = Path("private/runs/manual-campaign/campaign_plan.json")
    write_private_evolution_campaign_plan(
        out,
        seed_candidates_path=SEED_PLAN,
        heldout_targets_path=HELDOUT_TARGET,
        policy=policy,
        review_log_path=review_log,
        root=tmp_path,
        run_id="manual-campaign",
    )
    payload = json.loads((tmp_path / out).read_text(encoding="utf-8"))
    payload["steps"][0]["command"]["argv"] = [
        "agades-pqc",
        "heldout-run-schedule",
        "private/runs/manual-campaign/heldout_schedule.json",
    ]
    payload["steps"][0]["command"]["policy_command"] = (
        "agades-pqc heldout-run-schedule"
    )
    (tmp_path / out).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verification = verify_private_evolution_campaign_plan(
        tmp_path / out,
        policy=policy,
        root=tmp_path,
    )

    assert verification["accepted"] is False
    assert any(
        "step command role drifted" in failure
        for failure in verification["failures"]
    )


def test_private_evolution_campaign_plan_rejects_unmutatable_seed(
    tmp_path: Path,
) -> None:
    policy = build_private_run_policy()
    review_log = _review_log(tmp_path, policy)

    try:
        build_private_evolution_campaign_plan(
            seed_candidates_path=SCHEMA_ONLY_SEED_PLAN,
            heldout_targets_path=HELDOUT_TARGET,
            policy=policy,
            review_log_path=review_log,
            out=Path("private/runs/manual-campaign/campaign_plan.json"),
            root=tmp_path,
            run_id="manual-campaign",
        )
    except ValueError as exc:
        assert "no reviewed seed mutations" in str(exc)
    else:
        raise AssertionError("schema-only seed should not produce a campaign plan")


def test_private_evolution_campaign_plan_rejects_incompatible_heldout_family(
    tmp_path: Path,
) -> None:
    policy = build_private_run_policy()
    review_log = _review_log(tmp_path, policy)

    try:
        build_private_evolution_campaign_plan(
            seed_candidates_path=SEED_PLAN,
            heldout_targets_path=CODE_BASED_HELDOUT_TARGET,
            policy=policy,
            review_log_path=review_log,
            out=Path("private/runs/manual-campaign/campaign_plan.json"),
            root=tmp_path,
            run_id="manual-campaign",
        )
    except ValueError as exc:
        assert "no compatible held-out target families" in str(exc)
    else:
        raise AssertionError("cross-family held-out target should be rejected")


def test_private_evolution_campaign_plan_rejects_partial_seed_family_coverage(
    tmp_path: Path,
) -> None:
    policy = build_private_run_policy()
    review_log = _review_log(tmp_path, policy)
    mixed_seeds = _seed_dir(
        tmp_path,
        "mixed-seeds",
        [SEED_PLAN, CODE_BASED_MUTABLE_SEED_PLAN],
    )

    try:
        build_private_evolution_campaign_plan(
            seed_candidates_path=mixed_seeds,
            heldout_targets_path=HELDOUT_TARGET,
            policy=policy,
            review_log_path=review_log,
            out=Path("private/runs/manual-campaign/campaign_plan.json"),
            root=tmp_path,
            run_id="manual-campaign",
        )
    except ValueError as exc:
        assert "missing held-out coverage for seed families" in str(exc)
        assert "CODE_BASED" in str(exc)
    else:
        raise AssertionError("partial seed-family coverage should be rejected")


def test_private_evolution_campaign_plan_verifier_rejects_seed_preflight_drift(
    tmp_path: Path,
) -> None:
    policy = build_private_run_policy()
    review_log = _review_log(tmp_path, policy)
    out = Path("private/runs/manual-campaign/campaign_plan.json")
    write_private_evolution_campaign_plan(
        out,
        seed_candidates_path=SEED_PLAN,
        heldout_targets_path=HELDOUT_TARGET,
        policy=policy,
        review_log_path=review_log,
        root=tmp_path,
        run_id="manual-campaign",
    )
    payload = json.loads((tmp_path / out).read_text(encoding="utf-8"))
    payload["seed_mutation_preflight"]["candidate_count"] = 0
    payload["summary"]["seed_mutation_candidate_count"] = 0
    (tmp_path / out).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verification = verify_private_evolution_campaign_plan(
        tmp_path / out,
        policy=policy,
        root=tmp_path,
    )

    assert verification["accepted"] is False
    assert any(
        "seed mutation preflight drifted" in failure
        for failure in verification["failures"]
    )


def test_private_evolution_campaign_plan_verifier_rejects_target_preflight_drift(
    tmp_path: Path,
) -> None:
    policy = build_private_run_policy()
    review_log = _review_log(tmp_path, policy)
    out = Path("private/runs/manual-campaign/campaign_plan.json")
    write_private_evolution_campaign_plan(
        out,
        seed_candidates_path=SEED_PLAN,
        heldout_targets_path=HELDOUT_TARGET,
        policy=policy,
        review_log_path=review_log,
        root=tmp_path,
        run_id="manual-campaign",
    )
    payload = json.loads((tmp_path / out).read_text(encoding="utf-8"))
    payload["target_compatibility_preflight"]["compatible_target_families"] = []
    payload["target_compatibility_preflight"]["coverage_complete"] = False
    payload["target_compatibility_preflight"]["uncovered_seed_target_families"] = [
        "LWE"
    ]
    payload["summary"]["compatible_target_family_count"] = 0
    payload["summary"]["seed_family_coverage_complete"] = False
    (tmp_path / out).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verification = verify_private_evolution_campaign_plan(
        tmp_path / out,
        policy=policy,
        root=tmp_path,
    )

    assert verification["accepted"] is False
    assert any(
        "target compatibility preflight drifted" in failure
        for failure in verification["failures"]
    )


def test_private_evolution_campaign_plan_cli_writes_and_verifies(
    tmp_path: Path,
) -> None:
    project_root = Path.cwd()
    policy = build_private_run_policy()
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        review_log = _review_log(Path.cwd(), policy)
        out = Path("private/runs/manual-campaign/campaign_plan.json")

        write_result = runner.invoke(
            app,
            [
                "private-evolution-campaign-plan",
                str(project_root / SEED_PLAN),
                str(project_root / HELDOUT_TARGET),
                "--out",
                str(out),
                "--policy",
                str(project_root / "docs" / "private_run_policy.json"),
                "--review-log",
                str(review_log),
                "--run-id",
                "manual-campaign",
            ],
        )
        verify_result = runner.invoke(
            app,
            [
                "private-evolution-campaign-plan-verify",
                "--plan",
                str(out),
                "--policy",
                str(project_root / "docs" / "private_run_policy.json"),
            ],
        )

        assert write_result.exit_code == 0, write_result.output
        assert f"private_evolution_campaign_plan={out}" in write_result.output
        assert verify_result.exit_code == 0, verify_result.output
        assert '"accepted": true' in verify_result.output


def _review_log(tmp_path: Path, policy: dict) -> Path:
    review_log_path = tmp_path / "private" / "runs" / "review_log.json"
    write_heldout_review_log(
        review_log_path,
        approvals=policy["scheduler_policy"]["approval_gates"],
        reviewed_by="unit-test-reviewer",
        review_id="unit-test-review",
    )
    return Path("private/runs/review_log.json")


def _seed_dir(tmp_path: Path, name: str, seed_paths: list[Path]) -> Path:
    project_root = Path.cwd()
    path = tmp_path / name
    path.mkdir()
    for seed_path in seed_paths:
        (path / seed_path.name).write_text(
            (project_root / seed_path).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    return path
