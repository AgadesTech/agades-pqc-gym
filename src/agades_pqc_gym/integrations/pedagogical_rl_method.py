from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.formal.artifacts import MVP_VERTICAL_PROOF_ARTIFACT_PATHS
from agades_pqc_gym.rl.pedagogy import PEDAGOGICAL_REWARD_REPORT_SCHEMA

PEDAGOGICAL_RL_METHOD_SCHEMA = "agades.pqc.pedagogical_rl_method.v1"
PEDAGOGICAL_RL_METHOD_VERIFICATION_SCHEMA = (
    "agades.pqc.pedagogical_rl_method_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_METHOD_PATH = Path("docs/pedagogical_rl_method.json")
PEDAGOGICAL_RL_SOURCE_URL = "https://noahziems.com/pedagogical-rl"
PEDAGOGY_REWARD = "R_agades(x,c,tau) * G_spike_student(tau|x)"
LEARNABILITY_SCORE = "spike_aware_logsumexp_surprise_gap"
ASSIMILATION_OBJECTIVE = "surprisal_gated_imitation"
TEACHER_STUDENT_PATTERN = "privileged_self_teacher_student"
PEDAGOGICAL_REWARD_FUNCTION = (
    "agades_pqc_gym.rl.pedagogy.build_pedagogical_reward_report"
)
LEARNABILITY_FUNCTION = "agades_pqc_gym.rl.pedagogy.spike_aware_learnability_score"
ASSIMILATION_WEIGHT_FUNCTION = (
    "agades_pqc_gym.rl.pedagogy.surprisal_gated_token_weights"
)
RUNTIME_BINDING = {
    "reward_report_schema": PEDAGOGICAL_REWARD_REPORT_SCHEMA,
    "reward_function": PEDAGOGICAL_REWARD_FUNCTION,
    "learnability_function": LEARNABILITY_FUNCTION,
    "assimilation_weight_function": ASSIMILATION_WEIGHT_FUNCTION,
    "raw_private_signals_publication_allowed": False,
}
STAGE_SEQUENCE = [
    "privileged_self_teacher_grpo",
    "spike_aware_trajectory_filter",
    "surprisal_gated_student_assimilation",
    "optional_private_grpo_refinement",
]
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
REWARD_TERM_DEFINITIONS = {
    "formal_validity": (
        "candidate parses as an AttackPlan and produces a proof artifact"
    ),
    "cryptographic_applicability": (
        "candidate passes the public verifier for its target family and operator"
    ),
    "no_security_overclaim": (
        "candidate does not publish unreviewed estimates, success probability, "
        "external claims, or PQC break claims"
    ),
    "student_readability": (
        "candidate is a single readable JSON object with notes that state the "
        "no-security-claim boundary"
    ),
    "reproducibility": (
        "candidate satisfies the task reproducibility requirement when present"
    ),
    "reviewer_quality": (
        "candidate proof artifact names required reviewer roles and preserves "
        "the release claim boundary"
    ),
    "task_match": (
        "candidate target family, target name, support level, and operator "
        "sequence match the task metadata"
    ),
    "proof_obligation_coverage": (
        "candidate proof artifact has family invariants, proof obligations, "
        "and every proof obligation is bound to a Lean-backed type_rule"
    ),
}
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
    "formal_obligation_ledger": "docs/formal_obligation_ledger.json",
    "formal_estimator_model": "docs/formal_estimator_model.json",
    "formal_family_coverage": "docs/formal_family_coverage.json",
    "formal_operator_semantics": "docs/formal_operator_semantics.json",
    "formal_lwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.LWE.value
    ],
    "formal_mlwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.MLWE.value
    ],
    "hf_rl_rollout_examples": "hf/dataset/rl_rollouts.jsonl",
    "prime_eval_config_manifest": "docs/prime_eval_config_manifest.json",
    "private_run_policy": "docs/private_run_policy.json",
    "rl_pedagogy_runtime": "src/agades_pqc_gym/rl/pedagogy.py",
}
FORBIDDEN_PUBLIC_CLAIMS = [
    "unreviewed_pqc_break_claims",
    "private_qwen_weights_or_adapters",
    "private_training_traces_or_reviewer_annotations",
    "private_dataset_rows_or_prompts",
]


def build_pedagogical_rl_method(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    return {
        "schema_version": PEDAGOGICAL_RL_METHOD_SCHEMA,
        "source": {
            "name": "Pedagogical RL",
            "url": PEDAGOGICAL_RL_SOURCE_URL,
            "citation_key": "chakraborty_ziems_2026_pedagogical_rl",
        },
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "method": {
            "base_paradigm": "learn_nearest_successes_from_privileged_context",
            "domain": "AttackPlan_generation_validation_and_repair",
            "teacher_student_pattern": TEACHER_STUDENT_PATTERN,
            "public_training_claim": (
                "agents learn to produce formally valid and reviewable "
                "AttackPlans, not cryptographic break claims"
            ),
            "private_outputs_only": True,
        },
        "roles": {
            "student": {
                "model": "Qwen3.6-27B-private",
                "conditioning": "attackplan_prompt_without_privileged_context",
                "privileged_context_visible": False,
                "private_outputs_only": True,
            },
            "self_teacher": {
                "model": "Qwen3.6-27B-private",
                "conditioning": "attackplan_prompt_with_privileged_context",
                "privileged_context_visible": True,
                "privileged_context": [
                    "formal_obligations",
                    "family_invariants",
                    "estimator_results",
                    "reviewer_rubric",
                    "license_and_provenance_metadata",
                ],
                "must_remain_student_learnable": True,
            },
        },
        "stages": [
            {
                "id": "privileged_self_teacher_grpo",
                "trainer": "prime-rl",
                "policy": "self_teacher",
                "objective": PEDAGOGY_REWARD,
                "uses_privileged_context": True,
                "external_publication_allowed": False,
            },
            {
                "id": "spike_aware_trajectory_filter",
                "policy": "student_scorer",
                "objective": LEARNABILITY_SCORE,
                "uses_student_logprobs": True,
                "raw_logits_publication_allowed": False,
            },
            {
                "id": "surprisal_gated_student_assimilation",
                "policy": "student",
                "objective": ASSIMILATION_OBJECTIVE,
                "update": "weighted_sft",
                "raw_teacher_tokens_publication_allowed": False,
            },
            {
                "id": "optional_private_grpo_refinement",
                "policy": "student",
                "objective": "R_agades(x,c,tau)",
                "requires_prior_method_artifact": True,
                "external_publication_allowed": False,
            },
        ],
        "reward_contract": {
            "type": "multiplicative_pedagogical_reward",
            "range": [0.0, 1.0],
            "pedagogy_reward": PEDAGOGY_REWARD,
            "success_gate": {
                "type": "agades_verifier_and_reviewer_gate",
                "required_terms": list(REWARD_TERMS),
                "term_definitions": dict(REWARD_TERM_DEFINITIONS),
                "good_answer_only_is_sufficient": False,
            },
            "learnability_score": {
                "type": LEARNABILITY_SCORE,
                "surprise_gap": (
                    "log p_student(a_max|x,prefix) - "
                    "log p_student(a_t|x,prefix)"
                ),
                "beta": 5.0,
                "lambda": 1.0,
                "formula": (
                    "exp(-(lambda/beta) * log(mean_t(exp(beta * d_t))))"
                ),
            },
            "runtime_binding": dict(RUNTIME_BINDING),
            "claim_boundary": {
                "allows_security_claims": False,
                "requires_formal_obligations": True,
                "formal_obligation_ledger_path": (
                    "docs/formal_obligation_ledger.json"
                ),
                "requires_human_crypto_review": True,
            },
        },
        "assimilation": {
            "objective": ASSIMILATION_OBJECTIVE,
            "token_weight": (
                "sigmoid(kappa * (logp_student(a_t|x,prefix) - gamma))"
            ),
            "kappa": 2.0,
            "gamma": -4.0,
            "recompute_weights_after_student_update": True,
            "raw_logits_publication_allowed": False,
        },
        "datasets": {
            "sources": list(PRIVATE_DATASET_SOURCES),
            "curation_manifest_path": PRIVATE_DATASET_CURATION_MANIFEST_PATH,
            "required_controls": list(PRIVATE_DATASET_CONTROLS),
            "private_roots": [
                "private/datasets",
                "private/traces",
                "private/reviewer_annotations",
            ],
            "public_rows_allowed": False,
        },
        "privacy": {
            "raw_rollouts_publication_allowed": False,
            "teacher_prompts_publication_allowed": False,
            "student_logprobs_publication_allowed": False,
            "reviewer_annotations_publication_allowed": False,
            "fine_tuned_weights_publication_allowed": False,
            "sanitized_metadata_cards_allowed": True,
        },
        "publication_boundary": {
            "public_claims_allowed": [
                "environment_scoring_contracts",
                "sanitized_metadata_cards",
                "toy_or_schema_only_rollout_examples",
            ],
            "forbidden_public_claims": list(FORBIDDEN_PUBLIC_CLAIMS),
        },
        "integration_bindings": {
            "prime_training_stack": "prime-rl",
            "prime_environment": "agades-pqc-verifier-env",
            "hf_public_environment_category": "agent-environment",
            "openevolve_private_serious_research_allowed": True,
            "deepevolve_private_serious_research_allowed": True,
            "public_toy_eval_private_data_allowed": False,
        },
        "linked_artifacts": _linked_artifacts(project_root),
        "release_gates": [
            "uv run pytest tests/test_pedagogical_rl_method.py -q",
            "uv run agades-pqc pedagogical-rl-method --out "
            "docs/pedagogical_rl_method.json",
            "uv run agades-pqc pedagogical-rl-method-verify --method "
            "docs/pedagogical_rl_method.json",
            "uv run agades-pqc private-dataset-curation-verify --curation "
            f"{PRIVATE_DATASET_CURATION_MANIFEST_PATH}",
            "uv run agades-pqc private-training-config-verify --config "
            "prime_intellect/training/private_qwen_prime_rl.template.toml "
            "--manifest docs/private_training_config_manifest.json",
            "uv run agades-pqc rl-environment-contract-verify --contract "
            "docs/rl_environment_contract.json",
            "uv run agades-pqc reviewer-governance-verify --governance "
            "docs/reviewer_governance.json",
            "uv run agades-pqc ecosystem-smoke-verify --report "
            "reports/ecosystem_smoke.json",
            "uv run agades-pqc release-audit --out public/release_audit.json",
        ],
    }


def write_pedagogical_rl_method(
    out: Path = DEFAULT_METHOD_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    method = build_pedagogical_rl_method(root=project_root)
    resolved_out = _resolve_path(out, project_root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(method, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return method


def verify_pedagogical_rl_method(
    method_path: Path = DEFAULT_METHOD_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    method = _read_method(_resolve_path(method_path, project_root), failures)
    expected = build_pedagogical_rl_method(root=project_root)

    if method:
        if method != expected:
            failures.append("Pedagogical RL method artifact is not in sync.")
        _verify_source(method, failures)
        _verify_roles(method, failures)
        _verify_stages(method, failures)
        _verify_reward_contract(method, failures)
        _verify_assimilation(method, failures)
        _verify_datasets(method, failures)
        _verify_privacy(method, failures)
        _verify_publication_boundary(method, failures)
        _verify_integration_bindings(method, failures)
        _verify_linked_artifacts(method, expected, project_root, failures)

    return {
        "schema_version": PEDAGOGICAL_RL_METHOD_VERIFICATION_SCHEMA,
        "method_path": method_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "stages": len(method.get("stages", [])),
            "reward_terms": len(
                method.get("reward_contract", {})
                .get("success_gate", {})
                .get("required_terms", [])
            ),
            "linked_artifacts": len(method.get("linked_artifacts", {})),
            "failure_count": len(failures),
        },
        "failures": failures,
    }


def _verify_source(method: dict[str, Any], failures: list[str]) -> None:
    source = _dict_or_empty(method.get("source"))
    if source.get("url") != PEDAGOGICAL_RL_SOURCE_URL:
        failures.append("Pedagogical RL source URL is incorrect.")
    if source.get("citation_key") != "chakraborty_ziems_2026_pedagogical_rl":
        failures.append("Pedagogical RL citation key is incorrect.")


def _verify_roles(method: dict[str, Any], failures: list[str]) -> None:
    roles = _dict_or_empty(method.get("roles"))
    student = _dict_or_empty(roles.get("student"))
    teacher = _dict_or_empty(roles.get("self_teacher"))
    if student.get("privileged_context_visible") is not False:
        failures.append("Student must not see privileged context.")
    if teacher.get("privileged_context_visible") is not True:
        failures.append("Self-teacher must see privileged context.")
    if teacher.get("must_remain_student_learnable") is not True:
        failures.append("Self-teacher must remain student-learnable.")
    required_context = {
        "formal_obligations",
        "family_invariants",
        "estimator_results",
        "reviewer_rubric",
        "license_and_provenance_metadata",
    }
    if set(teacher.get("privileged_context", [])) != required_context:
        failures.append("Self-teacher privileged context is incomplete.")


def _verify_stages(method: dict[str, Any], failures: list[str]) -> None:
    stages = method.get("stages")
    if not isinstance(stages, list):
        failures.append("Pedagogical RL stages must be a list.")
        return
    if [stage.get("id") for stage in stages if isinstance(stage, dict)] != (
        STAGE_SEQUENCE
    ):
        failures.append("Pedagogical RL stage sequence is incorrect.")
    for stage in stages:
        if not isinstance(stage, dict):
            failures.append("Pedagogical RL stage must be an object.")
            continue
        if stage.get("external_publication_allowed") is True:
            failures.append("Pedagogical RL stages must not publish externally.")


def _verify_reward_contract(method: dict[str, Any], failures: list[str]) -> None:
    reward = _dict_or_empty(method.get("reward_contract"))
    if reward.get("type") != "multiplicative_pedagogical_reward":
        failures.append("Pedagogical reward type is incorrect.")
    if reward.get("pedagogy_reward") != PEDAGOGY_REWARD:
        failures.append("Pedagogical reward must be multiplicative.")
    success_gate = _dict_or_empty(reward.get("success_gate"))
    if success_gate.get("required_terms") != REWARD_TERMS:
        failures.append("Pedagogical reward terms are incorrect.")
    if success_gate.get("term_definitions") != REWARD_TERM_DEFINITIONS:
        failures.append("Pedagogical reward term definitions are incorrect.")
    if success_gate.get("good_answer_only_is_sufficient") is not False:
        failures.append("Good answer alone must not be sufficient.")
    learnability = _dict_or_empty(reward.get("learnability_score"))
    if learnability.get("type") != LEARNABILITY_SCORE:
        failures.append("Learnability score must be spike-aware.")
    if learnability.get("beta") != 5.0 or learnability.get("lambda") != 1.0:
        failures.append("Spike-aware reward hyperparameters are incorrect.")
    if reward.get("runtime_binding") != RUNTIME_BINDING:
        failures.append("Pedagogical RL runtime binding is incorrect.")
    boundary = _dict_or_empty(reward.get("claim_boundary"))
    if boundary.get("allows_security_claims") is not False:
        failures.append("Pedagogical RL reward must forbid security claims.")
    if boundary.get("requires_formal_obligations") is not True:
        failures.append("Pedagogical RL reward must require formal obligations.")
    if boundary.get("formal_obligation_ledger_path") != (
        "docs/formal_obligation_ledger.json"
    ):
        failures.append("Pedagogical RL reward must bind the obligation ledger.")
    if boundary.get("requires_human_crypto_review") is not True:
        failures.append("Pedagogical RL reward must require human crypto review.")


def _verify_assimilation(method: dict[str, Any], failures: list[str]) -> None:
    assimilation = _dict_or_empty(method.get("assimilation"))
    if assimilation.get("objective") != ASSIMILATION_OBJECTIVE:
        failures.append("Assimilation objective must be surprisal-gated.")
    if assimilation.get("kappa") != 2.0 or assimilation.get("gamma") != -4.0:
        failures.append("Assimilation gate hyperparameters are incorrect.")
    if assimilation.get("recompute_weights_after_student_update") is not True:
        failures.append("Assimilation weights must be recomputed after updates.")
    if assimilation.get("raw_logits_publication_allowed") is not False:
        failures.append("Student raw logits must never be public.")


def _verify_datasets(method: dict[str, Any], failures: list[str]) -> None:
    datasets = _dict_or_empty(method.get("datasets"))
    if datasets.get("sources") != PRIVATE_DATASET_SOURCES:
        failures.append("Pedagogical RL dataset sources are incorrect.")
    if datasets.get("curation_manifest_path") != (
        PRIVATE_DATASET_CURATION_MANIFEST_PATH
    ):
        failures.append("Pedagogical RL datasets must bind curation manifest.")
    if datasets.get("required_controls") != PRIVATE_DATASET_CONTROLS:
        failures.append("Pedagogical RL dataset controls are incorrect.")
    if datasets.get("public_rows_allowed") is not False:
        failures.append("Private pedagogical RL dataset rows must never be public.")


def _verify_privacy(method: dict[str, Any], failures: list[str]) -> None:
    privacy = _dict_or_empty(method.get("privacy"))
    private_false_keys = (
        "raw_rollouts_publication_allowed",
        "teacher_prompts_publication_allowed",
        "student_logprobs_publication_allowed",
        "reviewer_annotations_publication_allowed",
        "fine_tuned_weights_publication_allowed",
    )
    for key in private_false_keys:
        if privacy.get(key) is not False:
            if key == "raw_rollouts_publication_allowed":
                failures.append(
                    "Private pedagogical RL raw rollouts must never be public."
                )
            else:
                failures.append(f"Pedagogical RL privacy control {key} must be false.")
    if privacy.get("sanitized_metadata_cards_allowed") is not True:
        failures.append("Sanitized metadata cards should remain allowed.")


def _verify_publication_boundary(
    method: dict[str, Any],
    failures: list[str],
) -> None:
    boundary = _dict_or_empty(method.get("publication_boundary"))
    if boundary.get("forbidden_public_claims") != FORBIDDEN_PUBLIC_CLAIMS:
        failures.append("Pedagogical RL forbidden public claims are incorrect.")
    if "toy_or_schema_only_rollout_examples" not in boundary.get(
        "public_claims_allowed",
        [],
    ):
        failures.append("Public pedagogical RL claims must stay toy/schema-only.")


def _verify_integration_bindings(
    method: dict[str, Any],
    failures: list[str],
) -> None:
    bindings = _dict_or_empty(method.get("integration_bindings"))
    if bindings.get("prime_training_stack") != "prime-rl":
        failures.append("Pedagogical RL must bind to prime-rl.")
    if bindings.get("prime_environment") != "agades-pqc-verifier-env":
        failures.append("Pedagogical RL Prime environment is incorrect.")
    if bindings.get("hf_public_environment_category") != "agent-environment":
        failures.append("Pedagogical RL HF category must be agent-environment.")
    if bindings.get("public_toy_eval_private_data_allowed") is not False:
        failures.append("Public toy eval must not use private data.")


def _verify_linked_artifacts(
    method: dict[str, Any],
    expected: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    linked_artifacts = method.get("linked_artifacts")
    if not isinstance(linked_artifacts, dict):
        failures.append("Pedagogical RL linked_artifacts must be an object.")
        return
    if linked_artifacts != expected.get("linked_artifacts"):
        failures.append("Pedagogical RL linked artifact hashes are not in sync.")
    for name, artifact in linked_artifacts.items():
        if not isinstance(artifact, dict):
            failures.append(f"Pedagogical RL linked artifact {name} must be an object.")
            continue
        path = artifact.get("path")
        if not isinstance(path, str) or not path:
            failures.append(f"Pedagogical RL linked artifact {name} is missing path.")
            continue
        if not (root / path).is_file():
            failures.append(f"Pedagogical RL linked artifact is missing: {path}.")
        if artifact.get("sha256") is None:
            failures.append(
                f"Pedagogical RL linked artifact {name} is missing SHA-256."
            )


def _linked_artifacts(root: Path) -> dict[str, dict[str, str | None]]:
    return {
        name: {
            "path": path,
            "sha256": _file_sha256(root / path),
        }
        for name, path in LINKED_ARTIFACT_PATHS.items()
    }


def _read_method(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Pedagogical RL method artifact is missing: {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Pedagogical RL method artifact is invalid JSON at line {exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("Pedagogical RL method artifact must be a JSON object.")
        return {}
    return payload


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
