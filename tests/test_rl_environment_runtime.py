from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.rl.environment import (
    RL_REWARD_REPORT_SCHEMA,
    ROLLOUT_TRACE_SCHEMA,
    AgadesPQCGymEnvironment,
    score_attack_plan_candidate,
    write_public_rollout_examples,
)

LATTICE_PLAN = Path("examples/attack_plans/lattice_primal_usvp_toy.json")
CODE_BASED_PLAN = Path("examples/attack_plans/code_based_prange_toy.json")


def test_pedagogical_reward_scores_all_terms_for_matching_seed() -> None:
    task_info = _task_info(LATTICE_PLAN)

    report = score_attack_plan_candidate(
        LATTICE_PLAN.read_text(encoding="utf-8"),
        task_info=task_info,
        require_task_match=True,
    )

    assert report["schema_version"] == RL_REWARD_REPORT_SCHEMA
    assert report["reward"] == 1.0
    assert report["accepted"] is True
    assert report["blocked"] is False
    assert report["terms"] == {
        "formal_validity": 1.0,
        "cryptographic_applicability": 1.0,
        "no_security_overclaim": 1.0,
        "student_readability": 1.0,
        "reproducibility": 1.0,
        "reviewer_quality": 1.0,
        "task_match": 1.0,
        "proof_obligation_coverage": 1.0,
    }
    assert report["claim_boundary"] == {
        "trains_agent_behavior": True,
        "claims_pqc_break": False,
        "requires_human_review_before_claim": True,
    }
    assert report["formal_summary"]["proof_obligations"] == 4
    assert report["formal_summary"]["family_invariants"] == 2


def test_pedagogical_reward_blocks_task_mismatch_but_keeps_term_diagnostics() -> None:
    task_info = _task_info(LATTICE_PLAN)

    report = score_attack_plan_candidate(
        CODE_BASED_PLAN.read_text(encoding="utf-8"),
        task_info=task_info,
        require_task_match=True,
    )

    assert report["reward"] == 0.0
    assert report["blocked"] is True
    assert report["terms"]["formal_validity"] == 1.0
    assert report["terms"]["task_match"] == 0.0
    assert "task_match" in report["blocking_reasons"]


def test_gym_environment_reset_step_emits_public_safe_rollout_trace() -> None:
    env = AgadesPQCGymEnvironment.from_attack_plan_paths([LATTICE_PLAN])

    observation = env.reset()
    step = env.step(LATTICE_PLAN.read_text(encoding="utf-8"))

    assert observation["schema_version"] == "agades.pqc.rl.observation.v1"
    assert observation["task"]["attack_plan_id"] == "lattice_primal_usvp_toy_v1"
    assert observation["safety"]["accepts_executable_code"] is False
    assert step["done"] is True
    assert step["reward"] == 1.0
    assert step["info"]["trace"]["schema_version"] == ROLLOUT_TRACE_SCHEMA
    assert step["info"]["trace"]["public_release_ok"] is True
    assert step["info"]["trace"]["private_fields_present"] is False
    assert step["info"]["trace"]["candidate"]["attack_plan_id"] == (
        "lattice_primal_usvp_toy_v1"
    )


def test_write_public_rollout_examples_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "rollouts-first.jsonl"
    second = tmp_path / "rollouts-second.jsonl"

    write_public_rollout_examples([LATTICE_PLAN, CODE_BASED_PLAN], first)
    write_public_rollout_examples([LATTICE_PLAN, CODE_BASED_PLAN], second)

    rows = [
        json.loads(line) for line in first.read_text(encoding="utf-8").splitlines()
    ]
    assert first.read_bytes() == second.read_bytes()
    assert len(rows) == 2
    assert all(row["schema_version"] == ROLLOUT_TRACE_SCHEMA for row in rows)
    assert all(row["private_fields_present"] is False for row in rows)


def test_committed_public_rollout_examples_are_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "rl_rollouts.jsonl"
    committed = Path("hf/dataset/rl_rollouts.jsonl")

    write_public_rollout_examples([LATTICE_PLAN, CODE_BASED_PLAN], generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_rl_rollout_examples_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "rl_rollouts.jsonl"

    result = CliRunner().invoke(
        app,
        [
            "rl-rollout-examples",
            "--out",
            str(out),
            "--plan",
            str(LATTICE_PLAN),
            "--plan",
            str(CODE_BASED_PLAN),
        ],
    )

    assert result.exit_code == 0
    assert f"rl_rollout_examples={out}" in result.output
    assert out.is_file()


def _task_info(path: Path) -> dict[str, object]:
    env = AgadesPQCGymEnvironment.from_attack_plan_paths([path])
    return env.reset()["task"]
