from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

import agades_pqc_gym.rl.environment as rl_environment
from agades_pqc_gym.cli import app
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.formal.artifacts import build_attack_plan_proof_artifact_from_json
from agades_pqc_gym.rl.environment import (
    DEFAULT_ROLLOUT_PLANS,
    RL_REWARD_REPORT_SCHEMA,
    ROLLOUT_TRACE_SCHEMA,
    AgadesPQCGymEnvironment,
    build_public_rollout_examples,
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
    assert report["formal_summary"]["typed_proof_obligations"] == 4
    assert report["formal_summary"]["proof_obligation_type_rules"] == 5
    assert report["formal_summary"]["type_rule_kinds"] == [
        "estimator_claim_boundary",
        "family_applicability_boundary",
        "operator_precondition",
        "schema_only_boundary",
        "target_invariant",
    ]
    assert report["formal_summary"]["family_invariants"] == 2


def test_pedagogical_reward_blocks_untyped_formal_obligations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_info = _task_info(LATTICE_PLAN)

    def build_untyped_artifact(
        raw_json: str,
        *,
        source_label: str,
        estimator_result_path: Path | None = None,
        review_status: str = "pending_review",
        root: Path | None = None,
    ) -> dict[str, Any]:
        artifact = build_attack_plan_proof_artifact_from_json(
            raw_json,
            source_label=source_label,
            estimator_result_path=estimator_result_path,
            review_status=review_status,
            root=root,
        )
        artifact["proof_obligations"][0].pop("type_rule")
        return artifact

    monkeypatch.setattr(
        rl_environment,
        "build_attack_plan_proof_artifact_from_json",
        build_untyped_artifact,
    )

    report = score_attack_plan_candidate(
        LATTICE_PLAN.read_text(encoding="utf-8"),
        task_info=task_info,
        require_task_match=True,
    )

    assert report["reward"] == 0.0
    assert report["accepted"] is False
    assert report["blocked"] is True
    assert report["terms"]["proof_obligation_coverage"] == 0.0
    assert "proof_obligation_coverage" in report["blocking_reasons"]
    assert report["formal_summary"]["typed_proof_obligations"] == 3


def test_pedagogical_reward_blocks_forged_formal_type_rules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_info = _task_info(LATTICE_PLAN)

    def build_forged_type_rule_artifact(
        raw_json: str,
        *,
        source_label: str,
        estimator_result_path: Path | None = None,
        review_status: str = "pending_review",
        root: Path | None = None,
    ) -> dict[str, Any]:
        artifact = build_attack_plan_proof_artifact_from_json(
            raw_json,
            source_label=source_label,
            estimator_result_path=estimator_result_path,
            review_status=review_status,
            root=root,
        )
        forged_type_rule = dict(artifact["proof_obligations"][0]["type_rule"])
        forged_type_rule["lean_theorem"] = (
            "AgadesPQC.ProofObligation.forged_target_invariant_typed"
        )
        artifact["proof_obligations"][0]["type_rule"] = forged_type_rule
        return artifact

    monkeypatch.setattr(
        rl_environment,
        "build_attack_plan_proof_artifact_from_json",
        build_forged_type_rule_artifact,
    )

    report = score_attack_plan_candidate(
        LATTICE_PLAN.read_text(encoding="utf-8"),
        task_info=task_info,
        require_task_match=True,
    )

    assert report["reward"] == 0.0
    assert report["accepted"] is False
    assert report["terms"]["proof_obligation_coverage"] == 0.0
    assert report["formal_summary"]["typed_proof_obligations"] == 3


def test_pedagogical_reward_applies_spike_aware_private_signal_multiplier() -> None:
    task_info = _task_info(LATTICE_PLAN)

    report = score_attack_plan_candidate(
        LATTICE_PLAN.read_text(encoding="utf-8"),
        task_info=task_info,
        require_task_match=True,
        pedagogical_signals={
            "surprise_gaps": [0.0, 2.0],
            "student_token_logprobs": [-2.0, -8.0],
        },
    )

    expected_learnability = math.exp(
        -(1.0 / 5.0) * math.log((math.exp(5.0 * 0.0) + math.exp(5.0 * 2.0)) / 2.0)
    )
    pedagogy = report["pedagogical_reward"]
    assert report["accepted"] is True
    assert report["blocked"] is False
    assert math.isclose(report["reward"], expected_learnability)
    assert pedagogy["schema_version"] == "agades.pqc.rl.pedagogical_reward.v1"
    assert pedagogy["applied"] is True
    assert math.isclose(pedagogy["base_reward"], 1.0)
    assert math.isclose(pedagogy["learnability_score"], expected_learnability)
    assert math.isclose(pedagogy["final_reward"], expected_learnability)
    assert pedagogy["raw_private_signals_included"] is False
    assert pedagogy["assimilation_weights"]["count"] == 2
    assert 0.0 < pedagogy["assimilation_weights"]["min"] < 1.0
    assert 0.0 < pedagogy["assimilation_weights"]["max"] < 1.0
    assert "student_token_logprobs" not in json.dumps(pedagogy)
    assert "surprise_gaps" not in json.dumps(pedagogy)


def test_pedagogical_reward_blocks_invalid_private_signal_payload() -> None:
    task_info = _task_info(LATTICE_PLAN)

    report = score_attack_plan_candidate(
        LATTICE_PLAN.read_text(encoding="utf-8"),
        task_info=task_info,
        require_task_match=True,
        pedagogical_signals={"surprise_gaps": [-0.1]},
    )

    assert report["reward"] == 0.0
    assert report["accepted"] is False
    assert report["blocked"] is True
    assert "pedagogical_signals" in report["blocking_reasons"]
    assert report["pedagogical_reward"]["applied"] is False
    assert report["pedagogical_reward"]["signal_error"]


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
    binding = step["info"]["trace"]["formal_artifact_binding"]
    assert binding["schema_version"] == (
        "agades.pqc.rl.formal_artifact_binding.v1"
    )
    assert binding["attack_plan_id"] == "lattice_primal_usvp_toy_v1"
    assert binding["family"] == "LWE"
    assert len(binding["artifact_sha256"]) == 64
    assert binding["family_invariant_ids"] == [
        "lattice.dimension_modulus_positive",
        "lattice.distributions_present",
    ]
    assert binding["proof_obligation_ids"] == [
        "target.lwe.parameters.positive",
        "target.lwe.distributions.present",
        "operator.primal_usvp.beta.valid_range",
        "estimator.boundary.no_security_claim",
    ]
    assert len(binding["proof_obligation_sha256"]) == 4
    assert all(len(value) == 64 for value in binding["proof_obligation_sha256"])
    assert binding["review_status"] == "pending_review"
    assert binding["claim_allowed"] is False


def test_default_public_rollout_examples_cover_every_target_family() -> None:
    rows = build_public_rollout_examples(DEFAULT_ROLLOUT_PLANS)

    assert len(rows) == len(TargetFamily)
    assert [row["candidate"]["target_family"] for row in rows] == [
        family.value for family in TargetFamily
    ]
    assert all(
        row["formal_artifact_binding"]["claim_allowed"] is False
        for row in rows
    )
    assert all(row["private_fields_present"] is False for row in rows)


def test_write_public_rollout_examples_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "rollouts-first.jsonl"
    second = tmp_path / "rollouts-second.jsonl"

    write_public_rollout_examples(DEFAULT_ROLLOUT_PLANS, first)
    write_public_rollout_examples(DEFAULT_ROLLOUT_PLANS, second)

    rows = [
        json.loads(line) for line in first.read_text(encoding="utf-8").splitlines()
    ]
    assert first.read_bytes() == second.read_bytes()
    assert len(rows) == len(TargetFamily)
    assert all(row["schema_version"] == ROLLOUT_TRACE_SCHEMA for row in rows)
    assert all(row["private_fields_present"] is False for row in rows)


def test_committed_public_rollout_examples_are_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "rl_rollouts.jsonl"
    committed = Path("hf/dataset/rl_rollouts.jsonl")

    write_public_rollout_examples(DEFAULT_ROLLOUT_PLANS, generated)

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
