from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.formal.artifacts import MVP_VERTICAL_PROOF_ARTIFACT_PATHS
from agades_pqc_gym.integrations.pedagogical_rl_method import (
    ASSIMILATION_OBJECTIVE,
    ASSIMILATION_WEIGHT_FUNCTION,
    LEARNABILITY_FUNCTION,
    LEARNABILITY_SCORE,
    PEDAGOGICAL_REWARD_FUNCTION,
    PEDAGOGY_REWARD,
    STAGE_SEQUENCE,
    TEACHER_STUDENT_PATTERN,
)

PRIVATE_TRAINING_CONFIG_SCHEMA = "agades.pqc.private_training_config.v1"
PRIVATE_TRAINING_CONFIG_VERIFICATION_SCHEMA = (
    "agades.pqc.private_training_config_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = Path(
    "prime_intellect/training/private_qwen_prime_rl.template.toml"
)
DEFAULT_MANIFEST_PATH = Path("docs/private_training_config_manifest.json")
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
PRIVATE_ROOTS = [
    "private/datasets",
    "private/models",
    "private/reports",
    "private/runs",
    "private/traces",
]
LINKED_ARTIFACT_PATHS = {
    "private_run_policy": "docs/private_run_policy.json",
    "private_dataset_curation": PRIVATE_DATASET_CURATION_MANIFEST_PATH,
    "hf_rl_rollout_examples": "hf/dataset/rl_rollouts.jsonl",
    "prime_environment_manifest": "prime_intellect/verifiers_environment/"
    "prime_manifest.json",
    "prime_eval_config_manifest": "docs/prime_eval_config_manifest.json",
    "prime_eval_template": "prime_intellect/evals/agades_pqc_eval.template.toml",
    "pedagogical_rl_method": "docs/pedagogical_rl_method.json",
    "formal_lwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.LWE.value
    ],
    "formal_mlwe_proof_artifact": MVP_VERTICAL_PROOF_ARTIFACT_PATHS[
        TargetFamily.MLWE.value
    ],
    "formal_lean_backend": "docs/formal_lean_backend.json",
    "rl_pedagogy_runtime": "src/agades_pqc_gym/rl/pedagogy.py",
}
FORBIDDEN_ENV_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.private",
}
PUBLIC_QWEN_PREFIXES = ("Qwen/", "Qwen3", "Qwen2", "Alibaba-NLP/", "zlaabsi/")


def build_prime_rl_training_template() -> str:
    reward_terms = _toml_string_list(REWARD_TERMS)
    private_roots = _toml_string_list(PRIVATE_ROOTS)
    dataset_sources = _toml_string_list(PRIVATE_DATASET_SOURCES)
    dataset_controls = _toml_string_list(PRIVATE_DATASET_CONTROLS)
    target_modules = _toml_string_list(
        ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )

    return (
        '# Template only: review, fill environment variables, then launch manually.\n'
        'name = "agades-pqc-private-qwen-pedagogical-rl"\n'
        'model = "${AGADES_QWEN_BASE_MODEL}"\n'
        "max_steps = 1000\n"
        "batch_size = 8\n"
        "rollouts_per_example = 4\n"
        "learning_rate = 0.00001\n"
        "lora_alpha = 128\n"
        "env_files = []\n"
        "\n"
        "[run_config]\n"
        'method = "pedagogical_rl"\n'
        'launch_readiness = "blocked_until_private_model_and_dataset_review"\n'
        "private_outputs_only = true\n"
        "requires_license_review = true\n"
        "requires_provenance_review = true\n"
        "publish_to_hf_public = false\n"
        "publish_to_prime_public = false\n"
        f'dataset_curation_manifest = "{PRIVATE_DATASET_CURATION_MANIFEST_PATH}"\n'
        'student_model = "Qwen3.6-27B-private"\n'
        'preferred_user_artifact = "private GGUF OTQ 5-bit"\n'
        "gguf_direct_training_allowed = false\n"
        "spike_aware_pedagogy_reward = true\n"
        "surprisal_gated_imitation = true\n"
        "openevolve_after_training = true\n"
        "deepevolve_after_training = true\n"
        f"reward_terms = {reward_terms}\n"
        f"private_roots = {private_roots}\n"
        f"dataset_sources = {dataset_sources}\n"
        f"dataset_controls = {dataset_controls}\n"
        "\n"
        "[pedagogical_rl]\n"
        "privileged_self_teacher = true\n"
        'teacher_update = "grpo"\n'
        'student_update = "surprisal_gated_weighted_sft"\n'
        f'pedagogy_reward = "{PEDAGOGY_REWARD}"\n'
        f'learnability_score = "{LEARNABILITY_SCORE}"\n'
        "surprise_gap = \"log p_student(a_max|x,prefix) - "
        'log p_student(a_t|x,prefix)"\n'
        "spike_penalty_beta = 5.0\n"
        "spike_penalty_lambda = 1.0\n"
        "surprisal_gate_kappa = 2.0\n"
        "surprisal_gate_gamma = -4.0\n"
        f'reward_function = "{PEDAGOGICAL_REWARD_FUNCTION}"\n'
        f'learnability_function = "{LEARNABILITY_FUNCTION}"\n'
        f'assimilation_weight_function = "{ASSIMILATION_WEIGHT_FUNCTION}"\n'
        "raw_private_signals_publication_allowed = false\n"
        "\n"
        "[[env]]\n"
        'id = "agades-pqc-verifier-env"\n'
        "args = { num_examples = -1 }\n"
        "\n"
        "[sampling]\n"
        "max_tokens = 2048\n"
        "temperature = 0.6\n"
        "top_p = 0.95\n"
        "enable_thinking = true\n"
        "\n"
        "[eval]\n"
        "interval = 100\n"
        "num_examples = 32\n"
        "rollouts_per_example = 2\n"
        "eval_base_model = true\n"
        "\n"
        "[[eval.env]]\n"
        'id = "agades-pqc-verifier-env"\n'
        "args = { num_examples = 32 }\n"
        "\n"
        "[buffer]\n"
        "online_difficulty_filtering = true\n"
        "skip_verification = false\n"
        "min_reward = 0.2\n"
        "max_reward = 0.95\n"
        "\n"
        "[adapters]\n"
        "enabled = true\n"
        'type = "lora_or_qlora"\n'
        "rank = 64\n"
        "alpha = 128\n"
        f"target_modules = {target_modules}\n"
        "publish_publicly = false\n"
        "\n"
        "[checkpoints]\n"
        'root = "private/models/qwen3_6_27b_pedagogical_rl"\n'
        "save_interval = 100\n"
        "publish_publicly = false\n"
        "\n"
        "[infrastructure]\n"
        'provider = "prime_intellect"\n'
        'gpu_family = "review_required"\n'
        "private_storage_only = true\n"
        "\n"
        "[wandb]\n"
        'mode = "offline"\n'
        'project = "agades-pqc-private"\n'
    )


def build_private_training_manifest(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    return {
        "schema_version": PRIVATE_TRAINING_CONFIG_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "prime_training": {
            "config_path": config_path.as_posix(),
            "config_sha256": _file_sha256(_resolve_path(config_path, project_root)),
            "rl_environment_contract_path": "docs/rl_environment_contract.json",
            "eval_config_manifest_path": "docs/prime_eval_config_manifest.json",
            "dataset_curation_manifest_path": PRIVATE_DATASET_CURATION_MANIFEST_PATH,
            "launch_command_template": (
                f"prime train {config_path.as_posix()} "
                "--env-var HF_TOKEN --env-var WANDB_API_KEY"
            ),
            "eval_command": "prime eval run agades-pqc-verifier-env",
            "training_stack": "prime-rl",
            "launch_readiness": "blocked_until_private_model_and_dataset_review",
        },
        "qwen": {
            "target_model": "Qwen3.6-27B-private",
            "base_model_env": "AGADES_QWEN_BASE_MODEL",
            "preferred_user_artifact": "private GGUF OTQ 5-bit",
            "gguf_direct_training_allowed": False,
            "training_path": (
                "LoRA_or_QLoRA_on_trainable_weights_then_private_GGUF_OTQ_"
                "quantization"
            ),
            "publish_weights_publicly": False,
            "publish_adapters_publicly": False,
            "publish_trace_corpora_publicly": False,
        },
        "pedagogical_rl": {
            "method": "pedagogical_rl",
            "method_manifest_path": "docs/pedagogical_rl_method.json",
            "teacher_student_pattern": TEACHER_STUDENT_PATTERN,
            "pedagogy_reward": PEDAGOGY_REWARD,
            "learnability_score": LEARNABILITY_SCORE,
            "assimilation_objective": ASSIMILATION_OBJECTIVE,
            "stage_sequence": list(STAGE_SEQUENCE),
            "spike_aware_pedagogy_reward": True,
            "surprisal_gated_imitation": True,
            "reward_function": PEDAGOGICAL_REWARD_FUNCTION,
            "learnability_function": LEARNABILITY_FUNCTION,
            "assimilation_weight_function": ASSIMILATION_WEIGHT_FUNCTION,
            "raw_private_signals_publication_allowed": False,
            "reward_terms": list(REWARD_TERMS),
            "requires_reviewer_quality_signal": True,
            "requires_no_security_overclaim": True,
        },
        "datasets": {
            "sources": list(PRIVATE_DATASET_SOURCES),
            "curation_manifest_path": PRIVATE_DATASET_CURATION_MANIFEST_PATH,
            "required_controls": list(PRIVATE_DATASET_CONTROLS),
            "private_roots": ["private/datasets"],
            "publication_allowed": False,
            "train_traces_publication_allowed": False,
            "reviewer_annotations_publication_allowed": False,
        },
        "model_consumers": {
            "openevolve": {
                "private_qwen_allowed": True,
                "private_dataset_allowed": True,
                "public_publication_allowed": False,
            },
            "deepevolve": {
                "private_qwen_allowed": True,
                "private_dataset_allowed": True,
                "public_publication_allowed": False,
            },
        },
        "privacy_controls": {
            "public_weights_allowed": False,
            "public_adapters_allowed": False,
            "public_trace_corpora_allowed": False,
            "public_train_dataset_allowed": False,
            "env_file_upload_allowed": False,
            "allowed_env_vars": ["HF_TOKEN", "WANDB_API_KEY"],
            "private_roots": list(PRIVATE_ROOTS),
        },
        "linked_artifacts": _linked_artifacts(project_root),
        "release_gates": [
            "uv run pytest tests/test_private_training_config.py -q",
            "uv run agades-pqc private-training-config --config "
            "prime_intellect/training/private_qwen_prime_rl.template.toml "
            "--manifest docs/private_training_config_manifest.json",
            "uv run agades-pqc private-training-config-verify --config "
            "prime_intellect/training/private_qwen_prime_rl.template.toml "
            "--manifest docs/private_training_config_manifest.json",
            "uv run agades-pqc private-dataset-curation-verify --curation "
            f"{PRIVATE_DATASET_CURATION_MANIFEST_PATH}",
        ],
    }


def write_private_training_config(
    config_path: Path = DEFAULT_CONFIG_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    resolved_config_path = _resolve_path(config_path, project_root)
    resolved_manifest_path = _resolve_path(manifest_path, project_root)

    resolved_config_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_config_path.write_text(
        build_prime_rl_training_template(),
        encoding="utf-8",
    )
    manifest = build_private_training_manifest(
        config_path=config_path,
        root=project_root,
    )
    resolved_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_private_training_config(
    config_path: Path = DEFAULT_CONFIG_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    resolved_config_path = _resolve_path(config_path, project_root)
    resolved_manifest_path = _resolve_path(manifest_path, project_root)
    config_text = _read_text(resolved_config_path, "Prime RL config", failures)
    manifest = _read_manifest(resolved_manifest_path, failures)

    parsed_config: dict[str, Any] = {}
    if config_text:
        try:
            parsed_config = tomllib.loads(config_text)
        except tomllib.TOMLDecodeError as exc:
            failures.append(f"Prime RL config is invalid TOML: {exc}.")
    if parsed_config:
        _verify_training_toml(parsed_config, failures)
    if manifest:
        expected = build_private_training_manifest(
            config_path=config_path,
            root=project_root,
        )
        if manifest != expected:
            failures.append("Private training manifest is not in sync.")
        _verify_training_manifest(manifest, failures)

    summary = {
        "dataset_sources": len(manifest.get("datasets", {}).get("sources", [])),
        "dataset_controls": len(
            manifest.get("datasets", {}).get("required_controls", [])
        ),
        "reward_terms": len(
            manifest.get("pedagogical_rl", {}).get("reward_terms", [])
        ),
        "linked_artifacts": len(manifest.get("linked_artifacts", {})),
        "failure_count": len(failures),
    }
    return {
        "schema_version": PRIVATE_TRAINING_CONFIG_VERIFICATION_SCHEMA,
        "config_path": config_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _verify_training_toml(
    config: dict[str, Any],
    failures: list[str],
) -> None:
    if config.get("name") != "agades-pqc-private-qwen-pedagogical-rl":
        failures.append("Prime RL config name is incorrect.")
    model = config.get("model")
    if model != "${AGADES_QWEN_BASE_MODEL}":
        failures.append(
            "Prime RL config must use AGADES_QWEN_BASE_MODEL placeholder."
        )
    if isinstance(model, str) and model.startswith(PUBLIC_QWEN_PREFIXES):
        failures.append("Prime RL config must not pin a public Qwen model id.")
    raw_env_files = config.get("env_files", [])
    env_files = raw_env_files if isinstance(raw_env_files, list) else []
    if not isinstance(raw_env_files, list):
        failures.append("Prime RL config env_files must be a list.")
    if env_files:
        failures.append("Prime RL config must not upload env_files.")
    if any(Path(str(path)).name in FORBIDDEN_ENV_FILE_NAMES for path in env_files):
        failures.append("Prime RL config must not reference .env files.")

    run_config = _dict_or_empty(config.get("run_config"))
    if run_config.get("method") != "pedagogical_rl":
        failures.append("Prime RL config method must be pedagogical_rl.")
    if run_config.get("private_outputs_only") is not True:
        failures.append("Prime RL config must force private outputs.")
    if run_config.get("publish_to_hf_public") is not False:
        failures.append("Prime RL config must not publish to public HF.")
    if run_config.get("publish_to_prime_public") is not False:
        failures.append("Prime RL config must not publish to public Prime.")
    if run_config.get("dataset_curation_manifest") != (
        PRIVATE_DATASET_CURATION_MANIFEST_PATH
    ):
        failures.append("Prime RL config must bind the dataset curation manifest.")
    if run_config.get("reward_terms") != REWARD_TERMS:
        failures.append("Prime RL config reward terms are incorrect.")
    if run_config.get("dataset_sources") != PRIVATE_DATASET_SOURCES:
        failures.append("Prime RL config dataset sources are incorrect.")
    if run_config.get("dataset_controls") != PRIVATE_DATASET_CONTROLS:
        failures.append("Prime RL config dataset controls are incorrect.")
    if run_config.get("gguf_direct_training_allowed") is not False:
        failures.append("Prime RL config must not allow direct GGUF training.")
    pedagogical_rl = _dict_or_empty(config.get("pedagogical_rl"))
    if pedagogical_rl.get("privileged_self_teacher") is not True:
        failures.append("Prime RL config must enable privileged self-teacher.")
    if pedagogical_rl.get("teacher_update") != "grpo":
        failures.append("Prime RL config teacher update must be grpo.")
    if pedagogical_rl.get("student_update") != "surprisal_gated_weighted_sft":
        failures.append("Prime RL config student update must be surprisal-gated.")
    if pedagogical_rl.get("pedagogy_reward") != PEDAGOGY_REWARD:
        failures.append("Prime RL config pedagogy reward is incorrect.")
    if pedagogical_rl.get("learnability_score") != LEARNABILITY_SCORE:
        failures.append("Prime RL config learnability score is incorrect.")
    if pedagogical_rl.get("spike_penalty_beta") != 5.0:
        failures.append("Prime RL config spike beta is incorrect.")
    if pedagogical_rl.get("spike_penalty_lambda") != 1.0:
        failures.append("Prime RL config spike lambda is incorrect.")
    if pedagogical_rl.get("surprisal_gate_kappa") != 2.0:
        failures.append("Prime RL config surprisal kappa is incorrect.")
    if pedagogical_rl.get("surprisal_gate_gamma") != -4.0:
        failures.append("Prime RL config surprisal gamma is incorrect.")
    if pedagogical_rl.get("reward_function") != PEDAGOGICAL_REWARD_FUNCTION:
        failures.append("Prime RL config reward function is incorrect.")
    if pedagogical_rl.get("learnability_function") != LEARNABILITY_FUNCTION:
        failures.append("Prime RL config learnability function is incorrect.")
    if pedagogical_rl.get("assimilation_weight_function") != (
        ASSIMILATION_WEIGHT_FUNCTION
    ):
        failures.append("Prime RL config assimilation weight function is incorrect.")
    if pedagogical_rl.get("raw_private_signals_publication_allowed") is not False:
        failures.append("Prime RL config must not publish raw private signals.")

    env = config.get("env", [])
    first_env = env[0] if isinstance(env, list) and env else {}
    if not isinstance(first_env, dict) or first_env.get("id") != (
        "agades-pqc-verifier-env"
    ):
        failures.append("Prime RL config must target agades-pqc-verifier-env.")
    eval_env = _dict_or_empty(config.get("eval")).get("env", [])
    first_eval_env = eval_env[0] if isinstance(eval_env, list) and eval_env else {}
    if not isinstance(first_eval_env, dict) or first_eval_env.get("id") != (
        "agades-pqc-verifier-env"
    ):
        failures.append("Prime RL eval must target agades-pqc-verifier-env.")

    buffer = _dict_or_empty(config.get("buffer"))
    if buffer.get("online_difficulty_filtering") is not True:
        failures.append("Prime RL config must enable difficulty filtering.")
    if buffer.get("skip_verification") is not False:
        failures.append("Prime RL config must not skip verification.")

    adapters = _dict_or_empty(config.get("adapters"))
    if adapters.get("publish_publicly") is not False:
        failures.append("Prime RL adapters must not be public.")
    checkpoints = _dict_or_empty(config.get("checkpoints"))
    if checkpoints.get("publish_publicly") is not False:
        failures.append("Prime RL checkpoints must not be public.")
    infrastructure = _dict_or_empty(config.get("infrastructure"))
    if infrastructure.get("private_storage_only") is not True:
        failures.append("Prime RL config must require private storage.")


def _verify_training_manifest(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    if manifest.get("schema_version") != PRIVATE_TRAINING_CONFIG_SCHEMA:
        failures.append(
            "Private training manifest schema_version must be "
            f"{PRIVATE_TRAINING_CONFIG_SCHEMA}."
        )
    prime_training = _dict_or_empty(manifest.get("prime_training"))
    if prime_training.get("training_stack") != "prime-rl":
        failures.append("Private training stack must be prime-rl.")
    if prime_training.get("eval_config_manifest_path") != (
        "docs/prime_eval_config_manifest.json"
    ):
        failures.append("Private training must bind the Prime eval config manifest.")
    if prime_training.get("dataset_curation_manifest_path") != (
        PRIVATE_DATASET_CURATION_MANIFEST_PATH
    ):
        failures.append(
            "Private training must bind the dataset curation manifest."
        )
    if prime_training.get("launch_readiness") != (
        "blocked_until_private_model_and_dataset_review"
    ):
        failures.append("Private training must stay blocked until review.")

    qwen = _dict_or_empty(manifest.get("qwen"))
    if qwen.get("target_model") != "Qwen3.6-27B-private":
        failures.append("Private training Qwen target is incorrect.")
    if qwen.get("base_model_env") != "AGADES_QWEN_BASE_MODEL":
        failures.append("Private training Qwen base model must use an env var.")
    if qwen.get("gguf_direct_training_allowed") is not False:
        failures.append("Direct GGUF training must not be treated as robust.")
    if qwen.get("publish_weights_publicly") is not False:
        failures.append("Private Qwen weights must never be public.")
    if qwen.get("publish_adapters_publicly") is not False:
        failures.append("Private Qwen adapters must never be public.")
    if qwen.get("publish_trace_corpora_publicly") is not False:
        failures.append("Private Qwen trace corpora must never be public.")

    pedagogical_rl = _dict_or_empty(manifest.get("pedagogical_rl"))
    if pedagogical_rl.get("method") != "pedagogical_rl":
        failures.append("Private training method must be pedagogical_rl.")
    if pedagogical_rl.get("method_manifest_path") != "docs/pedagogical_rl_method.json":
        failures.append("Private training must bind the Pedagogical RL method.")
    if pedagogical_rl.get("teacher_student_pattern") != TEACHER_STUDENT_PATTERN:
        failures.append("Private training must use self-teacher/student traces.")
    if pedagogical_rl.get("pedagogy_reward") != PEDAGOGY_REWARD:
        failures.append("Private training pedagogy reward is incorrect.")
    if pedagogical_rl.get("learnability_score") != LEARNABILITY_SCORE:
        failures.append("Private training learnability score is incorrect.")
    if pedagogical_rl.get("assimilation_objective") != ASSIMILATION_OBJECTIVE:
        failures.append("Private training assimilation objective is incorrect.")
    if pedagogical_rl.get("stage_sequence") != STAGE_SEQUENCE:
        failures.append("Private training stage sequence is incorrect.")
    if pedagogical_rl.get("reward_terms") != REWARD_TERMS:
        failures.append("Private training reward terms are incorrect.")
    if pedagogical_rl.get("reward_function") != PEDAGOGICAL_REWARD_FUNCTION:
        failures.append("Private training reward function is incorrect.")
    if pedagogical_rl.get("learnability_function") != LEARNABILITY_FUNCTION:
        failures.append("Private training learnability function is incorrect.")
    if pedagogical_rl.get("assimilation_weight_function") != (
        ASSIMILATION_WEIGHT_FUNCTION
    ):
        failures.append("Private training assimilation weight function is incorrect.")
    if pedagogical_rl.get("raw_private_signals_publication_allowed") is not False:
        failures.append("Private training must not publish raw private signals.")

    datasets = _dict_or_empty(manifest.get("datasets"))
    if datasets.get("sources") != PRIVATE_DATASET_SOURCES:
        failures.append("Private training dataset sources are incorrect.")
    if datasets.get("curation_manifest_path") != (
        PRIVATE_DATASET_CURATION_MANIFEST_PATH
    ):
        failures.append("Private training datasets must bind curation manifest.")
    if datasets.get("required_controls") != PRIVATE_DATASET_CONTROLS:
        failures.append("Private training dataset controls are incorrect.")
    if datasets.get("publication_allowed") is not False:
        failures.append("Private training datasets must never be public.")
    if datasets.get("train_traces_publication_allowed") is not False:
        failures.append("Private training traces must never be public.")
    if datasets.get("reviewer_annotations_publication_allowed") is not False:
        failures.append("Private reviewer annotations must never be public.")

    consumers = _dict_or_empty(manifest.get("model_consumers"))
    for name in ("openevolve", "deepevolve"):
        consumer = _dict_or_empty(consumers.get(name))
        if consumer.get("private_qwen_allowed") is not True:
            failures.append(f"{name} must allow the private Qwen model.")
        if consumer.get("public_publication_allowed") is not False:
            failures.append(f"{name} must not publish private outputs.")

    privacy = _dict_or_empty(manifest.get("privacy_controls"))
    for key in (
        "public_weights_allowed",
        "public_adapters_allowed",
        "public_trace_corpora_allowed",
        "public_train_dataset_allowed",
        "env_file_upload_allowed",
    ):
        if privacy.get(key) is not False:
            failures.append(f"Privacy control {key} must be false.")
    linked = manifest.get("linked_artifacts")
    if not isinstance(linked, dict):
        failures.append("Private training linked_artifacts must be an object.")
    else:
        for name, artifact in linked.items():
            if not isinstance(artifact, dict):
                failures.append(f"Linked artifact {name} must be an object.")
                continue
            if artifact.get("sha256") is None:
                failures.append(f"Linked artifact {name} is missing SHA-256.")


def _read_text(path: Path, label: str, failures: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        failures.append(f"{label} is missing: {path.as_posix()}.")
        return ""


def _read_manifest(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Private training manifest is missing: {path.as_posix()}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Private training manifest is invalid JSON at line {exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("Private training manifest must be a JSON object.")
        return {}
    return payload


def _linked_artifacts(root: Path) -> dict[str, dict[str, str | None]]:
    return {
        name: {
            "path": path,
            "sha256": _file_sha256(root / path),
        }
        for name, path in LINKED_ARTIFACT_PATHS.items()
    }


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def _toml_string_list(values: list[str]) -> str:
    return "[" + ", ".join(json.dumps(value) for value in values) + "]"


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
