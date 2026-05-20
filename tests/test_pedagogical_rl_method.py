from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.pedagogical_rl_method import (
    PEDAGOGICAL_RL_METHOD_VERIFICATION_SCHEMA,
    build_pedagogical_rl_method,
    verify_pedagogical_rl_method,
    write_pedagogical_rl_method,
)

METHOD_PATH = Path("docs/pedagogical_rl_method.json")


def test_pedagogical_rl_method_defines_agades_teacher_student_pipeline(
    tmp_path: Path,
) -> None:
    out = tmp_path / "pedagogical_rl_method.json"

    payload = write_pedagogical_rl_method(out)

    assert payload == build_pedagogical_rl_method()
    assert json.loads(out.read_text(encoding="utf-8")) == payload
    assert payload["schema_version"] == "agades.pqc.pedagogical_rl_method.v1"
    assert payload["source"] == {
        "name": "Pedagogical RL",
        "url": "https://noahziems.com/pedagogical-rl",
        "citation_key": "chakraborty_ziems_2026_pedagogical_rl",
    }
    assert payload["roles"]["student"] == {
        "model": "Qwen3.6-27B-private",
        "conditioning": "attackplan_prompt_without_privileged_context",
        "privileged_context_visible": False,
        "private_outputs_only": True,
    }
    assert payload["roles"]["self_teacher"]["privileged_context_visible"] is True
    assert payload["roles"]["self_teacher"]["privileged_context"] == [
        "formal_obligations",
        "family_invariants",
        "estimator_results",
        "reviewer_rubric",
        "license_and_provenance_metadata",
    ]
    assert [stage["id"] for stage in payload["stages"]] == [
        "privileged_self_teacher_grpo",
        "spike_aware_trajectory_filter",
        "surprisal_gated_student_assimilation",
        "optional_private_grpo_refinement",
    ]
    assert payload["reward_contract"]["pedagogy_reward"] == (
        "R_agades(x,c,tau) * G_spike_student(tau|x)"
    )
    assert payload["reward_contract"]["success_gate"]["required_terms"] == [
        "formal_validity",
        "cryptographic_applicability",
        "no_security_overclaim",
        "student_readability",
        "reproducibility",
        "reviewer_quality",
        "task_match",
        "proof_obligation_coverage",
    ]
    assert payload["reward_contract"]["learnability_score"] == {
        "type": "spike_aware_logsumexp_surprise_gap",
        "surprise_gap": (
            "log p_student(a_max|x,prefix) - log p_student(a_t|x,prefix)"
        ),
        "beta": 5.0,
        "lambda": 1.0,
        "formula": (
            "exp(-(lambda/beta) * log(mean_t(exp(beta * d_t))))"
        ),
    }
    assert payload["reward_contract"]["runtime_binding"] == {
        "reward_report_schema": "agades.pqc.rl.pedagogical_reward.v1",
        "reward_function": "agades_pqc_gym.rl.pedagogy.build_pedagogical_reward_report",
        "learnability_function": (
            "agades_pqc_gym.rl.pedagogy.spike_aware_learnability_score"
        ),
        "assimilation_weight_function": (
            "agades_pqc_gym.rl.pedagogy.surprisal_gated_token_weights"
        ),
        "raw_private_signals_publication_allowed": False,
    }
    assert payload["assimilation"]["objective"] == "surprisal_gated_imitation"
    assert payload["assimilation"]["token_weight"] == (
        "sigmoid(kappa * (logp_student(a_t|x,prefix) - gamma))"
    )
    assert payload["assimilation"]["raw_logits_publication_allowed"] is False
    assert payload["datasets"]["curation_manifest_path"] == (
        "docs/private_dataset_curation.json"
    )
    assert payload["privacy"]["raw_rollouts_publication_allowed"] is False
    assert payload["privacy"]["teacher_prompts_publication_allowed"] is False
    assert payload["publication_boundary"]["public_claims_allowed"] == [
        "environment_scoring_contracts",
        "sanitized_metadata_cards",
        "toy_or_schema_only_rollout_examples",
    ]
    assert payload["publication_boundary"]["forbidden_public_claims"] == [
        "unreviewed_pqc_break_claims",
        "private_qwen_weights_or_adapters",
        "private_training_traces_or_reviewer_annotations",
        "private_dataset_rows_or_prompts",
    ]
    assert payload["linked_artifacts"]["rl_pedagogy_runtime"]["path"] == (
        "src/agades_pqc_gym/rl/pedagogy.py"
    )


def test_committed_pedagogical_rl_method_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "pedagogical_rl_method.json"

    write_pedagogical_rl_method(generated)

    assert METHOD_PATH.read_bytes() == generated.read_bytes()


def test_pedagogical_rl_method_verify_accepts_committed_artifact() -> None:
    result = verify_pedagogical_rl_method(METHOD_PATH)

    assert result == {
        "schema_version": PEDAGOGICAL_RL_METHOD_VERIFICATION_SCHEMA,
        "method_path": METHOD_PATH.as_posix(),
        "accepted": True,
        "summary": {
            "stages": 4,
            "reward_terms": 8,
            "linked_artifacts": 9,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_pedagogical_rl_method_rejects_additive_or_public_trace_variants(
    tmp_path: Path,
) -> None:
    out = tmp_path / "pedagogical_rl_method.json"
    payload = write_pedagogical_rl_method(out)
    payload["reward_contract"]["pedagogy_reward"] = (
        "R_agades(x,c,tau) + G_spike_student(tau|x)"
    )
    payload["privacy"]["raw_rollouts_publication_allowed"] = True
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    result = verify_pedagogical_rl_method(out)

    assert result["accepted"] is False
    assert "Pedagogical reward must be multiplicative." in result["failures"]
    assert "Private pedagogical RL raw rollouts must never be public." in (
        result["failures"]
    )


def test_pedagogical_rl_method_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "pedagogical_rl_method.json"

    write_result = CliRunner().invoke(
        app,
        ["pedagogical-rl-method", "--out", str(out)],
    )
    verify_result = CliRunner().invoke(
        app,
        ["pedagogical-rl-method-verify", "--method", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"pedagogical_rl_method={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
