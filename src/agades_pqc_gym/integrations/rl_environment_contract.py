from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.formal.artifacts import MVP_VERTICAL_PROOF_ARTIFACT_PATHS
from agades_pqc_gym.integrations.pedagogical_rl_method import (
    ASSIMILATION_OBJECTIVE,
    LEARNABILITY_SCORE,
    PEDAGOGY_REWARD,
    STAGE_SEQUENCE,
    TEACHER_STUDENT_PATTERN,
)

RL_ENVIRONMENT_CONTRACT_SCHEMA = "agades.pqc.rl_environment_contract.v1"
RL_ENVIRONMENT_CONTRACT_VERIFICATION_SCHEMA = (
    "agades.pqc.rl_environment_contract_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
REWARD_TERMS = [
    "formal_validity",
    "cryptographic_applicability",
    "no_security_overclaim",
    "student_readability",
    "reproducibility",
    "reviewer_quality",
    "task_match",
    "proof_obligation_coverage",
]
PRIVATE_DATASET_SOURCES = [
    "facebookresearch/LWE-benchmarking",
    "facebook/TAPAS",
    "pq-code-package",
]
PRIVATE_DATASET_CONTROLS = [
    "license_review",
    "provenance_tracking",
    "deduplication",
    "redaction",
    "contamination_audit",
]
PRIVATE_DATASET_CURATION_MANIFEST_PATH = "docs/private_dataset_curation.json"
LINKED_ARTIFACT_PATHS = {
    "hf_space_manifest": "hf/space_manifest.json",
    "hf_rl_rollout_examples": "hf/dataset/rl_rollouts.jsonl",
    "prime_environment_manifest": "prime_intellect/verifiers_environment/"
    "prime_manifest.json",
    "prime_eval_config_manifest": "docs/prime_eval_config_manifest.json",
    "prime_eval_template": "prime_intellect/evals/agades_pqc_eval.template.toml",
    "private_run_policy": "docs/private_run_policy.json",
    "private_dataset_curation": PRIVATE_DATASET_CURATION_MANIFEST_PATH,
    "prime_rl_training_template": "prime_intellect/training/"
    "private_qwen_prime_rl.template.toml",
    "pedagogical_rl_method": "docs/pedagogical_rl_method.json",
    "formal_attackplan_semantics": "docs/formal_attackplan_semantics.json",
    "formal_obligation_ledger": "docs/formal_obligation_ledger.json",
    "formal_estimator_model": "docs/formal_estimator_model.json",
    "formal_family_coverage": "docs/formal_family_coverage.json",
    "formal_operator_semantics": "docs/formal_operator_semantics.json",
    "formal_lean_backend": "docs/formal_lean_backend.json",
    "formal_lwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.LWE.value
    ],
    "formal_mlwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.MLWE.value
    ],
    "reviewer_governance": "docs/reviewer_governance.json",
    "prime_schema_manifest": "prime_intellect/schemas/schema_manifest.json",
}


def build_rl_environment_contract(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    return {
        "schema_version": RL_ENVIRONMENT_CONTRACT_SCHEMA,
        "project": {
            "name": "Agades PQC Gym RL Environment",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "surfaces": {
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
        },
        "public_track": {
            "purpose": "train_or_evaluate_agents_to_produce_valid_attackplans",
            "dataset_roots": [
                "hf/dataset",
                "prime_intellect/verifiers_environment/data",
            ],
            "uses_toy_or_schema_only_tasks": True,
            "allows_private_datasets": False,
            "allows_security_claims": False,
            "requires_public_redaction": True,
        },
        "private_track": {
            "method": "pedagogical_rl",
            "method_manifest_path": "docs/pedagogical_rl_method.json",
            "teacher_student_pattern": TEACHER_STUDENT_PATTERN,
            "stage_sequence": list(STAGE_SEQUENCE),
            "spike_aware_pedagogy_reward": True,
            "surprisal_gated_imitation": True,
            "publish_training_traces_publicly": False,
            "publish_reviewer_annotations_publicly": False,
            "publish_prompts_publicly": False,
            "publish_finetuned_model_publicly": False,
            "datasets": {
                "sources": list(PRIVATE_DATASET_SOURCES),
                "curation_manifest_path": PRIVATE_DATASET_CURATION_MANIFEST_PATH,
                "required_controls": list(PRIVATE_DATASET_CONTROLS),
                "private_roots": [
                    "private/datasets",
                    "private/traces",
                    "private/models",
                ],
                "publication_allowed": False,
            },
            "qwen_training": {
                "target_model": "Qwen3.6-27B-private",
                "preferred_user_artifact": "private GGUF OTQ 5-bit",
                "training_path": (
                    "lora_or_qlora_on_trainable_weights_then_private_"
                    "gguf_otq_quantization"
                ),
                "gguf_direct_training_allowed": False,
                "publish_weights_publicly": False,
                "publish_trace_corpora_publicly": False,
                "public_card_metadata_only": True,
            },
        },
        "reward_model": {
            "type": "pedagogical_multi_term_reward",
            "range": [0.0, 1.0],
            "pedagogy_reward": PEDAGOGY_REWARD,
            "learnability_score": LEARNABILITY_SCORE,
            "assimilation_objective": ASSIMILATION_OBJECTIVE,
            "terms": list(REWARD_TERMS),
            "requires_no_security_claim": True,
            "requires_reviewer_quality_signal": True,
            "requires_attackplan_semantics_contract": True,
        },
        "claim_boundary": {
            "agent_task": (
                "produce, critique, repair, or validate AttackPlan JSON and "
                "proof obligations"
            ),
            "not_a_task": "claiming practical PQC breaks without formal/domain review",
            "human_review_required_before_claim": True,
            "formal_obligations_required_before_claim": True,
            "formal_obligation_ledger_path": "docs/formal_obligation_ledger.json",
        },
        "evolution_loops": {
            "public_toy_eval": {
                "openevolve_allowed": True,
                "deepevolve_allowed": True,
                "private_data_allowed": False,
                "security_claims_allowed": False,
            },
            "private_serious_research": {
                "openevolve_allowed": True,
                "deepevolve_allowed": True,
                "private_qwen_allowed": True,
                "requires_private_run_policy": True,
                "requires_human_review": True,
                "publication_allowed": False,
            },
        },
        "linked_artifacts": _linked_artifacts(project_root),
        "release_gates": [
            "uv run pytest tests/test_rl_environment_contract.py -q",
            "uv run agades-pqc rl-environment-contract --out "
            "docs/rl_environment_contract.json",
            "uv run agades-pqc rl-environment-contract-verify --contract "
            "docs/rl_environment_contract.json",
            "uv run agades-pqc private-run-policy-verify --policy "
            "docs/private_run_policy.json",
            "uv run agades-pqc private-dataset-curation-verify --curation "
            f"{PRIVATE_DATASET_CURATION_MANIFEST_PATH}",
            "uv run agades-pqc formal-proof-artifact-verify --artifact "
            f"{MVP_VERTICAL_PROOF_ARTIFACT_PATHS[TargetFamily.LWE.value]}",
            "uv run agades-pqc formal-proof-artifact-verify --artifact "
            f"{MVP_VERTICAL_PROOF_ARTIFACT_PATHS[TargetFamily.MLWE.value]}",
            "uv run agades-pqc formal-obligation-ledger-verify --ledger "
            "docs/formal_obligation_ledger.json",
            "uv run agades-pqc reviewer-governance-verify --governance "
            "docs/reviewer_governance.json",
        ],
    }


def write_rl_environment_contract(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    contract = build_rl_environment_contract(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return contract


def verify_rl_environment_contract(
    contract_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    contract = _read_contract(contract_path, project_root, failures)
    expected = build_rl_environment_contract(root=project_root)

    if contract and contract != expected:
        failures.append("RL environment contract is not in sync.")
    if contract:
        _verify_surfaces(contract, failures)
        _verify_public_track(contract, failures)
        _verify_private_track(contract, failures)
        _verify_reward_model(contract, failures)
        _verify_claim_boundary(contract, failures)
        _verify_evolution_loops(contract, failures)
        _verify_linked_artifacts(contract, expected, project_root, failures)

    summary = {
        "surfaces": len(contract.get("surfaces", {})),
        "reward_terms": len(contract.get("reward_model", {}).get("terms", [])),
        "private_dataset_sources": len(
            contract.get("private_track", {})
            .get("datasets", {})
            .get("sources", [])
        ),
        "linked_artifacts": len(contract.get("linked_artifacts", {})),
        "failure_count": len(failures),
    }
    return {
        "schema_version": RL_ENVIRONMENT_CONTRACT_VERIFICATION_SCHEMA,
        "contract_path": contract_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _linked_artifacts(root: Path) -> dict[str, dict[str, str | None]]:
    return {
        name: {
            "path": path,
            "sha256": _file_sha256(root / path),
        }
        for name, path in LINKED_ARTIFACT_PATHS.items()
    }


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def _read_contract(
    contract_path: Path,
    root: Path,
    failures: list[str],
) -> dict[str, Any]:
    path = contract_path if contract_path.is_absolute() else root / contract_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"RL environment contract is missing: {contract_path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"RL environment contract is invalid JSON at line {exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("RL environment contract must be a JSON object.")
        return {}
    return payload


def _verify_surfaces(contract: dict[str, Any], failures: list[str]) -> None:
    surfaces = contract.get("surfaces")
    if not isinstance(surfaces, dict):
        failures.append("RL environment surfaces must be an object.")
        return
    hf = surfaces.get("huggingface_agent_environment", {})
    prime = surfaces.get("prime_verifiers_environment", {})
    if hf.get("category") != "agent-environment":
        failures.append("Hugging Face Space must be an Agent Environment.")
    if hf.get("private_trace_publication_allowed") is not False:
        failures.append(
            "Hugging Face Agent Environment must not publish private traces."
        )
    if prime.get("eval_command") != "prime eval run agades-pqc-verifier-env":
        failures.append("Prime eval command is incorrect.")
    if prime.get("eval_config") != "docs/prime_eval_config_manifest.json":
        failures.append("Prime eval config manifest is incorrect.")
    if prime.get("credentialed_eval_command_template") != (
        "prime eval run ${AGADES_PRIME_ENV_REF} -m ${AGADES_EVAL_MODEL} "
        "-p prime -n 32 -r 2 -t 2048 -s -A"
    ):
        failures.append("Prime credentialed eval command template is incorrect.")
    if prime.get("training_stack") != "prime-rl":
        failures.append("Prime training stack must be prime-rl.")
    if prime.get("private_trace_publication_allowed") is not False:
        failures.append("Prime environment must not publish private traces.")


def _verify_public_track(contract: dict[str, Any], failures: list[str]) -> None:
    public_track = contract.get("public_track")
    if not isinstance(public_track, dict):
        failures.append("RL public track must be an object.")
        return
    if public_track.get("allows_private_datasets") is not False:
        failures.append("Public RL track must not use private datasets.")
    if public_track.get("allows_security_claims") is not False:
        failures.append("Public RL track must not allow security claims.")
    if public_track.get("uses_toy_or_schema_only_tasks") is not True:
        failures.append("Public RL track must stay toy/schema-only.")


def _verify_private_track(contract: dict[str, Any], failures: list[str]) -> None:
    private_track = contract.get("private_track")
    if not isinstance(private_track, dict):
        failures.append("RL private track must be an object.")
        return
    if private_track.get("method") != "pedagogical_rl":
        failures.append("Private RL method must be pedagogical_rl.")
    if private_track.get("method_manifest_path") != "docs/pedagogical_rl_method.json":
        failures.append("Private RL must bind the Pedagogical RL method.")
    if private_track.get("teacher_student_pattern") != TEACHER_STUDENT_PATTERN:
        failures.append("Private RL must use privileged self-teacher/student.")
    if private_track.get("stage_sequence") != STAGE_SEQUENCE:
        failures.append("Private RL stage sequence is incorrect.")
    for key in (
        "publish_training_traces_publicly",
        "publish_reviewer_annotations_publicly",
        "publish_prompts_publicly",
        "publish_finetuned_model_publicly",
    ):
        if private_track.get(key) is not False:
            if key == "publish_training_traces_publicly":
                failures.append("Private RL training traces must never be public.")
            else:
                failures.append(f"Private RL {key} must be false.")
    datasets = private_track.get("datasets", {})
    if datasets.get("sources") != PRIVATE_DATASET_SOURCES:
        failures.append("Private RL dataset sources are incorrect.")
    if datasets.get("curation_manifest_path") != (
        PRIVATE_DATASET_CURATION_MANIFEST_PATH
    ):
        failures.append("Private RL datasets must bind curation manifest.")
    if datasets.get("required_controls") != PRIVATE_DATASET_CONTROLS:
        failures.append("Private RL dataset controls are incorrect.")
    if datasets.get("publication_allowed") is not False:
        failures.append("Private RL datasets must not be publishable.")
    qwen = private_track.get("qwen_training", {})
    if qwen.get("target_model") != "Qwen3.6-27B-private":
        failures.append("Private RL Qwen target model is incorrect.")
    if qwen.get("gguf_direct_training_allowed") is not False:
        failures.append("GGUF direct training must not be treated as robust.")
    if qwen.get("publish_weights_publicly") is not False:
        failures.append("Private Qwen weights must never be public.")
    if qwen.get("publish_trace_corpora_publicly") is not False:
        failures.append("Private Qwen trace corpora must never be public.")


def _verify_reward_model(contract: dict[str, Any], failures: list[str]) -> None:
    reward_model = contract.get("reward_model")
    if not isinstance(reward_model, dict):
        failures.append("RL reward model must be an object.")
        return
    if reward_model.get("terms") != REWARD_TERMS:
        failures.append("RL reward terms are incorrect.")
    if reward_model.get("pedagogy_reward") != PEDAGOGY_REWARD:
        failures.append("RL pedagogy reward is incorrect.")
    if reward_model.get("learnability_score") != LEARNABILITY_SCORE:
        failures.append("RL learnability score is incorrect.")
    if reward_model.get("assimilation_objective") != ASSIMILATION_OBJECTIVE:
        failures.append("RL assimilation objective is incorrect.")
    if reward_model.get("requires_no_security_claim") is not True:
        failures.append("RL reward must enforce no-overclaim behavior.")
    if reward_model.get("requires_reviewer_quality_signal") is not True:
        failures.append("RL reward must include reviewer-quality signal.")
    if reward_model.get("requires_attackplan_semantics_contract") is not True:
        failures.append("RL reward must bind the AttackPlan semantics contract.")


def _verify_claim_boundary(contract: dict[str, Any], failures: list[str]) -> None:
    claim_boundary = contract.get("claim_boundary")
    if not isinstance(claim_boundary, dict):
        failures.append("RL claim boundary must be an object.")
        return
    if claim_boundary.get("human_review_required_before_claim") is not True:
        failures.append("RL claims must require human review.")
    if claim_boundary.get("formal_obligations_required_before_claim") is not True:
        failures.append("RL claims must require formal obligations.")
    if claim_boundary.get("formal_obligation_ledger_path") != (
        "docs/formal_obligation_ledger.json"
    ):
        failures.append("RL contract must bind the formal obligation ledger.")
    if "PQC breaks" not in claim_boundary.get("not_a_task", ""):
        failures.append("RL contract must forbid unreviewed PQC break claims.")


def _verify_evolution_loops(contract: dict[str, Any], failures: list[str]) -> None:
    loops = contract.get("evolution_loops")
    if not isinstance(loops, dict):
        failures.append("RL evolution loops must be an object.")
        return
    public_loop = loops.get("public_toy_eval", {})
    private_loop = loops.get("private_serious_research", {})
    if public_loop.get("private_data_allowed") is not False:
        failures.append("Public evolution loop must not use private data.")
    if public_loop.get("security_claims_allowed") is not False:
        failures.append("Public evolution loop must not allow security claims.")
    if private_loop.get("publication_allowed") is not False:
        failures.append("Private serious research loop must not be public.")
    if private_loop.get("requires_human_review") is not True:
        failures.append("Private serious research loop must require human review.")


def _verify_linked_artifacts(
    contract: dict[str, Any],
    expected: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    linked_artifacts = contract.get("linked_artifacts")
    if not isinstance(linked_artifacts, dict):
        failures.append("RL linked artifacts must be an object.")
        return
    if linked_artifacts != expected.get("linked_artifacts"):
        failures.append("RL linked artifact hashes are not in sync.")
    for name, artifact in linked_artifacts.items():
        if not isinstance(artifact, dict):
            failures.append(f"RL linked artifact {name} must be an object.")
            continue
        path = artifact.get("path")
        if not isinstance(path, str) or not path:
            failures.append(f"RL linked artifact {name} is missing path.")
            continue
        if not (root / path).is_file():
            failures.append(f"RL linked artifact is missing: {path}.")
        if artifact.get("sha256") is None:
            failures.append(f"RL linked artifact {name} is missing SHA-256.")
