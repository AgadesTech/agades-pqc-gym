from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any

PRIME_EVAL_CONFIG_SCHEMA = "agades.pqc.prime_eval_config.v1"
PRIME_EVAL_CONFIG_VERIFICATION_SCHEMA = "agades.pqc.prime_eval_config_verification.v1"
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = Path("prime_intellect/evals/agades_pqc_eval.template.toml")
DEFAULT_MANIFEST_PATH = Path("docs/prime_eval_config_manifest.json")
ENVIRONMENT_MANIFEST_PATH = Path(
    "prime_intellect/verifiers_environment/prime_manifest.json"
)
SCHEMA_MANIFEST_PATH = Path("prime_intellect/schemas/schema_manifest.json")
ENVIRONMENT_ID = "agades-pqc-verifier-env"
ENVIRONMENT_REF_ENV = "AGADES_PRIME_ENV_REF"
MODEL_ENV = "AGADES_EVAL_MODEL"
PROVIDER = "prime"
NUM_EXAMPLES = 32
ROLLOUTS_PER_EXAMPLE = 2
MAX_TOKENS = 2048
LOCAL_VERIFIERS_SMOKE_COMMAND = (
    "cd prime_intellect/verifiers_environment && "
    "uv run vf-eval agades-pqc-verifier-env"
)
CREDENTIALED_EVAL_COMMAND_TEMPLATE = (
    "prime eval run ${AGADES_PRIME_ENV_REF} -m ${AGADES_EVAL_MODEL} "
    "-p prime -n 32 -r 2 -t 2048 -s -A"
)
LAUNCH_READINESS = "blocked_until_prime_credentials_namespace_and_model_review"
REQUIRED_REVIEWERS = [
    "prime_operator",
    "cryptography_domain_reviewer",
    "release_owner",
]
FORBIDDEN_ENV_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.private",
}
PUBLICATION_FALSE_SAFETY_FLAGS = (
    "external_prime_execution_performed",
    "credentials_checked_at_generation",
    "credentials_present_in_artifact",
    "publish_outputs_publicly",
    "publish_private_traces",
    "security_claim",
)


def build_prime_eval_template() -> str:
    reviewers = _toml_string_list(REQUIRED_REVIEWERS)
    return (
        "# Template only: review credentials, namespace, and model before launch.\n"
        'name = "agades-pqc-verifier-eval"\n'
        f'environment_id = "{ENVIRONMENT_ID}"\n'
        f'environment_ref = "${{{ENVIRONMENT_REF_ENV}}}"\n'
        f'model = "${{{MODEL_ENV}}}"\n'
        f'provider = "{PROVIDER}"\n'
        f"num_examples = {NUM_EXAMPLES}\n"
        f"rollouts_per_example = {ROLLOUTS_PER_EXAMPLE}\n"
        f"max_tokens = {MAX_TOKENS}\n"
        "seed = 42\n"
        "env_files = []\n"
        f'launch_readiness = "{LAUNCH_READINESS}"\n'
        "\n"
        "[commands]\n"
        f'local_verifiers_smoke = "{LOCAL_VERIFIERS_SMOKE_COMMAND}"\n'
        f'credentialed_eval_template = "{CREDENTIALED_EVAL_COMMAND_TEMPLATE}"\n'
        "\n"
        "[task_source]\n"
        f'manifest_path = "{ENVIRONMENT_MANIFEST_PATH.as_posix()}"\n'
        f'schema_manifest_path = "{SCHEMA_MANIFEST_PATH.as_posix()}"\n'
        "public_examples_only = true\n"
        "\n"
        "[reward_contract]\n"
        "reward_range = [0.0, 1.0]\n"
        "accepted_reward = 1.0\n"
        "unsupported_reward = 0.0\n"
        "invalid_reward = 0.0\n"
        "requires_single_json_object = true\n"
        "requires_task_match = true\n"
        "accepts_executable_code = false\n"
        "\n"
        "[safety]\n"
        "template_only = true\n"
        "external_prime_execution_performed = false\n"
        "credentials_checked_at_generation = false\n"
        "credentials_present_in_artifact = false\n"
        "publish_outputs_publicly = false\n"
        "publish_private_traces = false\n"
        "security_claim = false\n"
        "\n"
        "[review]\n"
        f"required_reviewers = {reviewers}\n"
        'operator_checklist = "confirm_prime_org_namespace_model_and_billing"\n'
    )


def build_prime_eval_manifest(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    environment_manifest = _read_json(project_root / ENVIRONMENT_MANIFEST_PATH)
    task_manifest = _dict_or_empty(environment_manifest.get("task_manifest"))
    scoring_contract = _dict_or_empty(environment_manifest.get("scoring_contract"))
    families = task_manifest.get("families")
    if not isinstance(families, list):
        families = []

    return {
        "schema_version": PRIME_EVAL_CONFIG_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "prime_eval": {
            "config_path": config_path.as_posix(),
            "config_sha256": _file_sha256(_resolve_path(config_path, project_root)),
            "config_format": "agades.local.prime_eval_template.toml",
            "environment_id": ENVIRONMENT_ID,
            "environment_ref_env": ENVIRONMENT_REF_ENV,
            "model_env": MODEL_ENV,
            "provider": PROVIDER,
            "num_examples": NUM_EXAMPLES,
            "rollouts_per_example": ROLLOUTS_PER_EXAMPLE,
            "max_tokens": MAX_TOKENS,
            "local_verifiers_smoke_command": LOCAL_VERIFIERS_SMOKE_COMMAND,
            "credentialed_eval_command_template": CREDENTIALED_EVAL_COMMAND_TEMPLATE,
            "launch_readiness": LAUNCH_READINESS,
        },
        "environment": {
            "manifest_path": ENVIRONMENT_MANIFEST_PATH.as_posix(),
            "manifest_sha256": _file_sha256(project_root / ENVIRONMENT_MANIFEST_PATH),
            "schema_manifest_path": SCHEMA_MANIFEST_PATH.as_posix(),
            "schema_manifest_sha256": _file_sha256(project_root / SCHEMA_MANIFEST_PATH),
            "task_count": task_manifest.get("task_count"),
            "family_count": len(families),
            "families": families,
            "support_levels": task_manifest.get("support_levels", []),
            "public_examples_only": True,
        },
        "reward_contract": {
            "reward_range": scoring_contract.get("reward_range"),
            "accepted_reward": scoring_contract.get("accepted_reward"),
            "unsupported_reward": scoring_contract.get("unsupported_reward"),
            "invalid_reward": scoring_contract.get("invalid_reward"),
            "requires_single_json_object": scoring_contract.get(
                "requires_single_json_object"
            ),
            "requires_task_match": True,
            "accepts_executable_code": scoring_contract.get("accepts_executable_code"),
        },
        "safety": {
            "template_only": True,
            "external_prime_execution_performed": False,
            "credentials_checked_at_generation": False,
            "credentials_present_in_artifact": False,
            "publish_outputs_publicly": False,
            "publish_private_traces": False,
            "security_claim": False,
        },
        "review": {
            "required_reviewers": list(REQUIRED_REVIEWERS),
            "operator_checklist": "confirm_prime_org_namespace_model_and_billing",
            "requires_prime_credentials": True,
            "requires_billing_review": True,
            "requires_model_review": True,
        },
        "release_gates": [
            "uv run pytest tests/test_prime_eval_config.py -q",
            "uv run agades-pqc prime-eval-config --config "
            "prime_intellect/evals/agades_pqc_eval.template.toml "
            "--manifest docs/prime_eval_config_manifest.json",
            "uv run agades-pqc prime-eval-config-verify --config "
            "prime_intellect/evals/agades_pqc_eval.template.toml "
            "--manifest docs/prime_eval_config_manifest.json",
            "uv run agades-pqc prime-manifest-verify --manifest "
            "prime_intellect/verifiers_environment/prime_manifest.json",
            "uv run agades-pqc prime-environment-smoke-verify --report "
            "reports/prime_environment_smoke.json",
            "uv run agades-pqc ecosystem-smoke-verify --report "
            "reports/ecosystem_smoke.json",
            "uv run agades-pqc release-audit --out public/release_audit.json",
        ],
    }


def write_prime_eval_config(
    config_path: Path = DEFAULT_CONFIG_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    resolved_config_path = _resolve_path(config_path, project_root)
    resolved_manifest_path = _resolve_path(manifest_path, project_root)

    resolved_config_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_config_path.write_text(build_prime_eval_template(), encoding="utf-8")
    manifest = build_prime_eval_manifest(config_path=config_path, root=project_root)
    resolved_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_prime_eval_config(
    config_path: Path = DEFAULT_CONFIG_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    resolved_config_path = _resolve_path(config_path, project_root)
    resolved_manifest_path = _resolve_path(manifest_path, project_root)
    config_text = _read_text(resolved_config_path, "Prime eval config", failures)
    manifest = _read_manifest(resolved_manifest_path, failures)

    parsed_config: dict[str, Any] = {}
    if config_text:
        try:
            parsed_config = tomllib.loads(config_text)
        except tomllib.TOMLDecodeError as exc:
            failures.append(f"Prime eval config is invalid TOML: {exc}.")
    if parsed_config:
        _verify_eval_toml(parsed_config, failures)
    if manifest:
        expected = build_prime_eval_manifest(
            config_path=config_path,
            root=project_root,
        )
        if manifest != expected:
            failures.append("Prime eval manifest is not in sync.")
        _verify_eval_manifest(manifest, project_root, failures)

    prime_eval = _dict_or_empty(manifest.get("prime_eval"))
    environment = _dict_or_empty(manifest.get("environment"))
    return {
        "schema_version": PRIME_EVAL_CONFIG_VERIFICATION_SCHEMA,
        "config_path": config_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "task_count": environment.get("task_count"),
            "family_count": environment.get("family_count"),
            "num_examples": prime_eval.get("num_examples"),
            "rollouts_per_example": prime_eval.get("rollouts_per_example"),
            "failure_count": len(failures),
        },
        "failures": failures,
    }


def _verify_eval_toml(config: dict[str, Any], failures: list[str]) -> None:
    if config.get("name") != "agades-pqc-verifier-eval":
        failures.append("Prime eval config name is incorrect.")
    if config.get("environment_id") != ENVIRONMENT_ID:
        failures.append("Prime eval config environment_id is incorrect.")
    if config.get("environment_ref") != f"${{{ENVIRONMENT_REF_ENV}}}":
        failures.append("Prime eval config must use AGADES_PRIME_ENV_REF.")
    if config.get("model") != f"${{{MODEL_ENV}}}":
        failures.append("Prime eval config must use AGADES_EVAL_MODEL.")
    if config.get("provider") != PROVIDER:
        failures.append("Prime eval config provider is incorrect.")
    if config.get("num_examples") != NUM_EXAMPLES:
        failures.append("Prime eval config num_examples is incorrect.")
    if config.get("rollouts_per_example") != ROLLOUTS_PER_EXAMPLE:
        failures.append("Prime eval config rollouts_per_example is incorrect.")
    if config.get("max_tokens") != MAX_TOKENS:
        failures.append("Prime eval config max_tokens is incorrect.")
    raw_env_files = config.get("env_files", [])
    env_files = raw_env_files if isinstance(raw_env_files, list) else []
    if not isinstance(raw_env_files, list):
        failures.append("Prime eval config env_files must be a list.")
    if env_files:
        failures.append("Prime eval config must not upload env_files.")
    if any(Path(str(path)).name in FORBIDDEN_ENV_FILE_NAMES for path in env_files):
        failures.append("Prime eval config must not reference .env files.")
    if config.get("launch_readiness") != LAUNCH_READINESS:
        failures.append("Prime eval config launch readiness is incorrect.")

    commands = _dict_or_empty(config.get("commands"))
    if commands.get("local_verifiers_smoke") != LOCAL_VERIFIERS_SMOKE_COMMAND:
        failures.append("Prime eval local smoke command is incorrect.")
    if commands.get("credentialed_eval_template") != (
        CREDENTIALED_EVAL_COMMAND_TEMPLATE
    ):
        failures.append("Prime eval credentialed command template is incorrect.")

    task_source = _dict_or_empty(config.get("task_source"))
    if task_source.get("manifest_path") != ENVIRONMENT_MANIFEST_PATH.as_posix():
        failures.append("Prime eval task source manifest path is incorrect.")
    if task_source.get("schema_manifest_path") != SCHEMA_MANIFEST_PATH.as_posix():
        failures.append("Prime eval schema manifest path is incorrect.")
    if task_source.get("public_examples_only") is not True:
        failures.append("Prime eval config must use public examples only.")

    reward_contract = _dict_or_empty(config.get("reward_contract"))
    if reward_contract.get("reward_range") != [0.0, 1.0]:
        failures.append("Prime eval reward range is incorrect.")
    if reward_contract.get("accepted_reward") != 1.0:
        failures.append("Prime eval accepted reward is incorrect.")
    if reward_contract.get("unsupported_reward") != 0.0:
        failures.append("Prime eval unsupported reward is incorrect.")
    if reward_contract.get("invalid_reward") != 0.0:
        failures.append("Prime eval invalid reward is incorrect.")
    if reward_contract.get("requires_single_json_object") is not True:
        failures.append("Prime eval must require a single JSON object.")
    if reward_contract.get("requires_task_match") is not True:
        failures.append("Prime eval must require task metadata matching.")
    if reward_contract.get("accepts_executable_code") is not False:
        failures.append("Prime eval must not accept executable submissions.")

    safety = _dict_or_empty(config.get("safety"))
    if safety.get("template_only") is not True:
        failures.append("Prime eval config must be marked template-only.")
    for flag in PUBLICATION_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            if flag == "external_prime_execution_performed":
                failures.append("Prime eval config must not claim external execution.")
            elif flag == "publish_private_traces":
                failures.append("Prime eval config must not publish private traces.")
            elif flag == "security_claim":
                failures.append("Prime eval config must not make security claims.")
            else:
                failures.append(f"Prime eval config safety.{flag} must be false.")

    review = _dict_or_empty(config.get("review"))
    if review.get("required_reviewers") != REQUIRED_REVIEWERS:
        failures.append("Prime eval reviewer list is incorrect.")
    if review.get("operator_checklist") != (
        "confirm_prime_org_namespace_model_and_billing"
    ):
        failures.append("Prime eval operator checklist is incorrect.")


def _verify_eval_manifest(
    manifest: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    if manifest.get("schema_version") != PRIME_EVAL_CONFIG_SCHEMA:
        failures.append(
            "Prime eval manifest schema_version must be "
            f"{PRIME_EVAL_CONFIG_SCHEMA}."
        )
    prime_eval = _dict_or_empty(manifest.get("prime_eval"))
    if prime_eval.get("config_format") != "agades.local.prime_eval_template.toml":
        failures.append("Prime eval manifest config_format is incorrect.")
    if prime_eval.get("environment_id") != ENVIRONMENT_ID:
        failures.append("Prime eval manifest environment_id is incorrect.")
    if prime_eval.get("environment_ref_env") != ENVIRONMENT_REF_ENV:
        failures.append("Prime eval manifest environment ref env is incorrect.")
    if prime_eval.get("model_env") != MODEL_ENV:
        failures.append("Prime eval manifest model env is incorrect.")
    if prime_eval.get("provider") != PROVIDER:
        failures.append("Prime eval manifest provider is incorrect.")
    if prime_eval.get("credentialed_eval_command_template") != (
        CREDENTIALED_EVAL_COMMAND_TEMPLATE
    ):
        failures.append("Prime eval manifest command template is incorrect.")
    if prime_eval.get("local_verifiers_smoke_command") != (
        LOCAL_VERIFIERS_SMOKE_COMMAND
    ):
        failures.append("Prime eval manifest local smoke command is incorrect.")
    if prime_eval.get("launch_readiness") != LAUNCH_READINESS:
        failures.append("Prime eval manifest launch readiness is incorrect.")

    environment = _dict_or_empty(manifest.get("environment"))
    if environment.get("manifest_path") != ENVIRONMENT_MANIFEST_PATH.as_posix():
        failures.append("Prime eval manifest environment manifest path is incorrect.")
    if environment.get("schema_manifest_path") != SCHEMA_MANIFEST_PATH.as_posix():
        failures.append("Prime eval manifest schema manifest path is incorrect.")
    if environment.get("public_examples_only") is not True:
        failures.append("Prime eval manifest must use public examples only.")
    if not isinstance(environment.get("task_count"), int) or (
        environment.get("task_count", 0) <= 0
    ):
        failures.append("Prime eval manifest task_count must be positive.")
    if not isinstance(environment.get("family_count"), int) or (
        environment.get("family_count", 0) <= 0
    ):
        failures.append("Prime eval manifest family_count must be positive.")

    from agades_pqc_gym.integrations.prime_environment_manifest import (
        verify_prime_environment_manifest,
    )

    environment_verification = verify_prime_environment_manifest(
        ENVIRONMENT_MANIFEST_PATH,
        root=root,
    )
    if environment_verification.get("accepted") is not True:
        failures.append("Prime eval manifest environment manifest is not accepted.")

    reward_contract = _dict_or_empty(manifest.get("reward_contract"))
    expected_reward_contract = {
        "reward_range": [0.0, 1.0],
        "accepted_reward": 1.0,
        "unsupported_reward": 0.0,
        "invalid_reward": 0.0,
        "requires_single_json_object": True,
        "requires_task_match": True,
        "accepts_executable_code": False,
    }
    if reward_contract != expected_reward_contract:
        failures.append("Prime eval manifest reward contract is incorrect.")

    safety = _dict_or_empty(manifest.get("safety"))
    if safety.get("template_only") is not True:
        failures.append("Prime eval manifest must be marked template-only.")
    for flag in PUBLICATION_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            if flag == "external_prime_execution_performed":
                failures.append(
                    "Prime eval manifest must not claim external execution."
                )
            elif flag == "publish_private_traces":
                failures.append("Prime eval manifest must not publish private traces.")
            elif flag == "security_claim":
                failures.append("Prime eval manifest must not make security claims.")
            else:
                failures.append(f"Prime eval manifest safety.{flag} must be false.")

    review = _dict_or_empty(manifest.get("review"))
    if review.get("required_reviewers") != REQUIRED_REVIEWERS:
        failures.append("Prime eval manifest reviewer list is incorrect.")
    if review.get("requires_prime_credentials") is not True:
        failures.append("Prime eval manifest must require Prime credentials.")
    if review.get("requires_billing_review") is not True:
        failures.append("Prime eval manifest must require billing review.")
    if review.get("requires_model_review") is not True:
        failures.append("Prime eval manifest must require model review.")


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
        failures.append(f"Prime eval manifest is missing: {path.as_posix()}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"Prime eval manifest is invalid JSON at line {exc.lineno}.")
        return {}
    if not isinstance(payload, dict):
        failures.append("Prime eval manifest must be a JSON object.")
        return {}
    return payload


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        msg = f"{path.as_posix()} must contain a JSON object."
        raise ValueError(msg)
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


def _toml_string_list(values: list[str]) -> str:
    return "[" + ", ".join(json.dumps(value) for value in values) + "]"
