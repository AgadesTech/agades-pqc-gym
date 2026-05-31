from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.rl_environment_contract import (
    RL_ENVIRONMENT_CONTRACT_VERIFICATION_SCHEMA,
    build_rl_environment_contract,
    verify_rl_environment_contract,
    write_rl_environment_contract,
)


def test_rl_environment_contract_defines_public_and_private_tracks(
    tmp_path: Path,
) -> None:
    out = tmp_path / "rl_environment_contract.json"

    contract = write_rl_environment_contract(out)

    assert contract == build_rl_environment_contract()
    assert json.loads(out.read_text(encoding="utf-8")) == contract
    assert contract["schema_version"] == "agades.pqc.rl_environment_contract.v1"
    assert contract["surfaces"] == {
        "huggingface_agent_environment": {
            "space_id_template": "agades/agades-pqc-gym-agent-env",
            "sdk": "gradio",
            "category": "agent-environment",
            "task_dataset": "hf/dataset/task_metadata.jsonl",
            "rollout_examples": "hf/dataset/rl_rollouts.jsonl",
            "public_visibility_allowed": True,
            "private_trace_publication_allowed": False,
        },
        "prime_verifiers_environment": {
            "environment": "agades-pqc-verifier-env",
            "eval_command": "prime eval run agades-pqc-verifier-env",
            "eval_config": "docs/prime_eval_config_manifest.json",
            "credentialed_eval_command_template": (
                "prime eval run ${AGADES_PRIME_ENV_REF} -m "
                "${AGADES_EVAL_MODEL} -p prime -n 32 -r 2 -t 2048 -s -A"
            ),
            "training_stack": "prime-rl",
            "environment_hub_handoff": True,
            "hosted_training_handoff": True,
            "private_trace_publication_allowed": False,
        },
    }
    assert contract["public_track"] == {
        "purpose": "train_or_evaluate_agents_to_produce_valid_attackplans",
        "dataset_roots": [
            "hf/dataset",
            "prime_intellect/verifiers_environment/data",
        ],
        "uses_toy_or_schema_only_tasks": True,
        "allows_private_datasets": False,
        "allows_security_claims": False,
        "requires_public_redaction": True,
    }
    assert contract["private_track"]["method"] == "pedagogical_rl"
    assert contract["private_track"]["method_manifest_path"] == (
        "docs/pedagogical_rl_method.json"
    )
    assert contract["private_track"]["teacher_student_pattern"] == (
        "privileged_self_teacher_student"
    )
    assert contract["private_track"]["stage_sequence"] == [
        "privileged_self_teacher_grpo",
        "spike_aware_trajectory_filter",
        "surprisal_gated_student_assimilation",
        "optional_private_grpo_refinement",
    ]
    assert contract["private_track"]["qwen_training"]["target_model"] == (
        "Qwen/Qwen3.6-35B-A3B"
    )
    assert (
        contract["private_track"]["qwen_training"]["publish_weights_publicly"]
        is False
    )
    assert contract["private_track"]["qwen_training"]["training_path"] == (
        "lora_or_qlora_on_trainable_weights_then_private_gguf_otq_quantization"
    )
    assert contract["private_track"]["datasets"]["sources"] == [
        "facebookresearch/LWE-benchmarking",
        "facebook/TAPAS",
        "pq-code-package",
    ]
    assert contract["private_track"]["datasets"]["curation_manifest_path"] == (
        "docs/private_dataset_curation.json"
    )
    assert contract["reward_model"] == {
        "type": "pedagogical_multi_term_reward",
        "range": [0.0, 1.0],
        "pedagogy_reward": "R_agades(x,c,tau) * G_spike_student(tau|x)",
        "learnability_score": "spike_aware_logsumexp_surprise_gap",
        "assimilation_objective": "surprisal_gated_imitation",
        "terms": [
            "formal_validity",
            "cryptographic_applicability",
            "no_security_overclaim",
            "student_readability",
            "reproducibility",
            "reviewer_quality",
            "task_match",
            "proof_obligation_coverage",
        ],
        "requires_no_security_claim": True,
        "requires_reviewer_quality_signal": True,
        "requires_attackplan_semantics_contract": True,
        "requires_operator_semantics_contract": True,
        "requires_formal_estimator_model_contract": True,
    }
    assert contract["linked_artifacts"]["formal_attackplan_semantics"]["path"] == (
        "docs/formal_attackplan_semantics.json"
    )
    assert contract["linked_artifacts"]["formal_lwe_proof_artifact"]["path"] == (
        "docs/formal_lattice_primal_usvp_proof_artifact.json"
    )
    assert contract["linked_artifacts"]["formal_mlwe_proof_artifact"]["path"] == (
        "docs/formal_lattice_mlwe_module_hypothesis_proof_artifact.json"
    )
    assert contract["linked_artifacts"]["hf_rl_rollout_examples"]["path"] == (
        "hf/dataset/rl_rollouts.jsonl"
    )
    assert contract["linked_artifacts"]["prime_eval_config_manifest"]["path"] == (
        "docs/prime_eval_config_manifest.json"
    )
    assert contract["linked_artifacts"]["prime_eval_template"]["path"] == (
        "prime_intellect/evals/agades_pqc_eval.template.toml"
    )
    assert contract["linked_artifacts"]["pedagogical_rl_method"]["path"] == (
        "docs/pedagogical_rl_method.json"
    )
    assert contract["linked_artifacts"]["private_dataset_curation"]["path"] == (
        "docs/private_dataset_curation.json"
    )
    assert contract["linked_artifacts"]["reviewer_governance"]["path"] == (
        "docs/reviewer_governance.json"
    )
    assert "private_training_manifest" not in contract["linked_artifacts"]
    assert contract["linked_artifacts"]["formal_family_coverage"]["path"] == (
        "docs/formal_family_coverage.json"
    )
    assert contract["linked_artifacts"]["formal_obligation_ledger"]["path"] == (
        "docs/formal_obligation_ledger.json"
    )
    assert contract["linked_artifacts"]["formal_estimator_model"]["path"] == (
        "docs/formal_estimator_model.json"
    )
    assert contract["linked_artifacts"]["formal_operator_semantics"]["path"] == (
        "docs/formal_operator_semantics.json"
    )
    assert contract["linked_artifacts"]["formal_lean_backend"]["path"] == (
        "docs/formal_lean_backend.json"
    )
    assert (
        len(contract["linked_artifacts"]["formal_lwe_proof_artifact"]["sha256"])
        == 64
    )
    assert (
        len(contract["linked_artifacts"]["formal_mlwe_proof_artifact"]["sha256"])
        == 64
    )


def test_committed_rl_environment_contract_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "rl_environment_contract.json"
    committed = Path("docs/rl_environment_contract.json")

    write_rl_environment_contract(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_rl_environment_contract_verify_accepts_committed_contract() -> None:
    result = verify_rl_environment_contract(Path("docs/rl_environment_contract.json"))

    assert result == {
        "schema_version": RL_ENVIRONMENT_CONTRACT_VERIFICATION_SCHEMA,
        "contract_path": "docs/rl_environment_contract.json",
        "accepted": True,
        "summary": {
            "surfaces": 2,
            "reward_terms": 8,
            "private_dataset_sources": 3,
            "linked_artifacts": 19,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_rl_environment_contract_verify_rejects_public_private_traces(
    tmp_path: Path,
) -> None:
    path = tmp_path / "rl_environment_contract.json"
    contract = build_rl_environment_contract()
    contract["private_track"]["publish_training_traces_publicly"] = True
    path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")

    result = verify_rl_environment_contract(path)

    assert result["accepted"] is False
    assert "Private RL training traces must never be public." in result["failures"]


def test_rl_environment_contract_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "rl_environment_contract.json"

    write_result = CliRunner().invoke(
        app,
        ["rl-environment-contract", "--out", str(out)],
    )
    verify_result = CliRunner().invoke(
        app,
        ["rl-environment-contract-verify", "--contract", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"rl_environment_contract={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
