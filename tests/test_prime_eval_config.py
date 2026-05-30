from __future__ import annotations

import json
import tomllib
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.prime_eval_config import (
    PRIME_EVAL_CONFIG_VERIFICATION_SCHEMA,
    build_prime_eval_manifest,
    verify_prime_eval_config,
    write_prime_eval_config,
)

CONFIG_PATH = Path("prime_intellect/evals/agades_pqc_eval.template.toml")
MANIFEST_PATH = Path("docs/prime_eval_config_manifest.json")


def test_prime_eval_manifest_defines_credentialed_eval_boundaries(
    tmp_path: Path,
) -> None:
    config = tmp_path / "agades_pqc_eval.template.toml"
    manifest = tmp_path / "prime_eval_config_manifest.json"

    payload = write_prime_eval_config(config, manifest)

    assert payload == build_prime_eval_manifest(config_path=config)
    assert json.loads(manifest.read_text(encoding="utf-8")) == payload
    assert payload["schema_version"] == "agades.pqc.prime_eval_config.v1"
    assert payload["prime_eval"] == {
        "config_path": config.as_posix(),
        "config_sha256": payload["prime_eval"]["config_sha256"],
        "config_format": "agades.local.prime_eval_template.toml",
        "environment_id": "agades-pqc-verifier-env",
        "environment_ref_env": "AGADES_PRIME_ENV_REF",
        "model_env": "AGADES_EVAL_MODEL",
        "provider": "prime",
        "num_examples": 32,
        "rollouts_per_example": 2,
        "max_tokens": 2048,
        "local_verifiers_smoke_command": (
            "cd prime_intellect/verifiers_environment && "
            "uv run vf-eval agades-pqc-verifier-env"
        ),
        "credentialed_eval_command_template": (
            "prime eval run ${AGADES_PRIME_ENV_REF} -m ${AGADES_EVAL_MODEL} "
            "-p prime -n 32 -r 2 -t 2048 -s -A"
        ),
        "launch_readiness": (
            "blocked_until_prime_credentials_namespace_and_model_review"
        ),
    }
    assert payload["environment"]["manifest_path"] == (
        "prime_intellect/verifiers_environment/prime_manifest.json"
    )
    assert payload["environment"]["task_count"] == 79
    assert payload["environment"]["family_count"] == 9
    assert payload["environment"]["public_examples_only"] is True
    assert payload["reward_contract"] == {
        "reward_range": [0.0, 1.0],
        "accepted_reward": 1.0,
        "unsupported_reward": 0.0,
        "invalid_reward": 0.0,
        "requires_single_json_object": True,
        "requires_task_match": True,
        "accepts_executable_code": False,
    }
    assert payload["safety"] == {
        "template_only": True,
        "external_prime_execution_performed": False,
        "credentials_checked_at_generation": False,
        "credentials_present_in_artifact": False,
        "publish_outputs_publicly": False,
        "publish_private_traces": False,
        "security_claim": False,
    }


def test_prime_eval_toml_template_is_sanitized_and_parseable(
    tmp_path: Path,
) -> None:
    config = tmp_path / "agades_pqc_eval.template.toml"
    manifest = tmp_path / "prime_eval_config_manifest.json"

    write_prime_eval_config(config, manifest)
    data = tomllib.loads(config.read_text(encoding="utf-8"))

    assert data["name"] == "agades-pqc-verifier-eval"
    assert data["environment_id"] == "agades-pqc-verifier-env"
    assert data["environment_ref"] == "${AGADES_PRIME_ENV_REF}"
    assert data["model"] == "${AGADES_EVAL_MODEL}"
    assert data["env_files"] == []
    assert data["num_examples"] == 32
    assert data["rollouts_per_example"] == 2
    assert data["safety"]["template_only"] is True
    assert data["safety"]["external_prime_execution_performed"] is False
    assert data["safety"]["credentials_checked_at_generation"] is False
    assert data["safety"]["publish_private_traces"] is False
    assert data["reward_contract"]["requires_task_match"] is True
    assert data["reward_contract"]["accepts_executable_code"] is False


def test_committed_prime_eval_config_is_in_sync(tmp_path: Path) -> None:
    generated_config = tmp_path / "agades_pqc_eval.template.toml"
    generated_manifest = tmp_path / "prime_eval_config_manifest.json"

    write_prime_eval_config(generated_config, generated_manifest)
    expected_manifest = build_prime_eval_manifest(config_path=CONFIG_PATH)

    assert CONFIG_PATH.read_bytes() == generated_config.read_bytes()
    assert json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) == expected_manifest


def test_prime_eval_config_verify_accepts_committed_artifacts() -> None:
    result = verify_prime_eval_config(CONFIG_PATH, MANIFEST_PATH)

    assert result == {
        "schema_version": PRIME_EVAL_CONFIG_VERIFICATION_SCHEMA,
        "config_path": CONFIG_PATH.as_posix(),
        "manifest_path": MANIFEST_PATH.as_posix(),
        "accepted": True,
        "summary": {
            "task_count": 79,
            "family_count": 9,
            "num_examples": 32,
            "rollouts_per_example": 2,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_prime_eval_config_rejects_external_execution_claim(
    tmp_path: Path,
) -> None:
    config = tmp_path / "agades_pqc_eval.template.toml"
    manifest = tmp_path / "prime_eval_config_manifest.json"

    write_prime_eval_config(config, manifest)
    text = config.read_text(encoding="utf-8").replace(
        "external_prime_execution_performed = false",
        "external_prime_execution_performed = true",
    )
    config.write_text(text, encoding="utf-8")

    result = verify_prime_eval_config(config, manifest)

    assert result["accepted"] is False
    assert "Prime eval config must not claim external execution." in result[
        "failures"
    ]


def test_prime_eval_config_rejects_private_trace_publication(
    tmp_path: Path,
) -> None:
    config = tmp_path / "agades_pqc_eval.template.toml"
    manifest = tmp_path / "prime_eval_config_manifest.json"
    payload = write_prime_eval_config(config, manifest)
    payload["safety"]["publish_private_traces"] = True
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    result = verify_prime_eval_config(config, manifest)

    assert result["accepted"] is False
    assert "Prime eval manifest must not publish private traces." in result[
        "failures"
    ]


def test_prime_eval_config_cli_round_trip(tmp_path: Path) -> None:
    config = tmp_path / "agades_pqc_eval.template.toml"
    manifest = tmp_path / "prime_eval_config_manifest.json"

    write_result = CliRunner().invoke(
        app,
        [
            "prime-eval-config",
            "--config",
            str(config),
            "--manifest",
            str(manifest),
        ],
    )
    verify_result = CliRunner().invoke(
        app,
        [
            "prime-eval-config-verify",
            "--config",
            str(config),
            "--manifest",
            str(manifest),
        ],
    )

    assert write_result.exit_code == 0
    assert f"prime_eval_config={config}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
