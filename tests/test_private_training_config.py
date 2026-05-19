from __future__ import annotations

import json
import tomllib
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.private_training_config import (
    PRIVATE_TRAINING_CONFIG_VERIFICATION_SCHEMA,
    build_private_training_manifest,
    verify_private_training_config,
    write_private_training_config,
)

CONFIG_PATH = Path("prime_intellect/training/private_qwen_prime_rl.template.toml")
MANIFEST_PATH = Path("docs/private_training_config_manifest.json")


def test_private_training_manifest_defines_prime_rl_qwen_and_dataset_controls(
    tmp_path: Path,
) -> None:
    config = tmp_path / "private_qwen_prime_rl.template.toml"
    manifest = tmp_path / "private_training_config_manifest.json"

    payload = write_private_training_config(config, manifest)

    assert payload == build_private_training_manifest(config_path=config)
    assert json.loads(manifest.read_text(encoding="utf-8")) == payload
    assert payload["schema_version"] == "agades.pqc.private_training_config.v1"
    assert payload["prime_training"]["config_sha256"]
    assert payload["prime_training"] == {
        "config_path": config.as_posix(),
        "config_sha256": payload["prime_training"]["config_sha256"],
        "rl_environment_contract_path": "docs/rl_environment_contract.json",
        "launch_command_template": (
            f"prime train {config.as_posix()} "
            "--env-var HF_TOKEN --env-var WANDB_API_KEY"
        ),
        "eval_command": "prime eval run agades-pqc-verifier-env",
        "training_stack": "prime-rl",
        "launch_readiness": "blocked_until_private_model_and_dataset_review",
    }
    assert payload["qwen"] == {
        "target_model": "Qwen3.6-27B-private",
        "base_model_env": "AGADES_QWEN_BASE_MODEL",
        "preferred_user_artifact": "private GGUF OTQ 5-bit",
        "gguf_direct_training_allowed": False,
        "training_path": (
            "LoRA_or_QLoRA_on_trainable_weights_then_private_GGUF_OTQ_quantization"
        ),
        "publish_weights_publicly": False,
        "publish_adapters_publicly": False,
        "publish_trace_corpora_publicly": False,
    }
    assert payload["datasets"]["sources"] == [
        "facebookresearch/LWE-benchmarking",
        "facebook/TAPAS",
        "pq-code-package",
    ]
    assert payload["datasets"]["required_controls"] == [
        "license_review",
        "provenance_tracking",
        "deduplication",
        "redaction",
        "contamination_audit",
    ]
    assert payload["datasets"]["publication_allowed"] is False
    assert payload["model_consumers"]["openevolve"]["private_qwen_allowed"] is True
    assert payload["model_consumers"]["deepevolve"]["private_qwen_allowed"] is True
    assert payload["linked_artifacts"]["formal_lean_backend"]["path"] == (
        "docs/formal_lean_backend.json"
    )


def test_private_prime_rl_toml_template_is_sanitized_and_parseable(
    tmp_path: Path,
) -> None:
    config = tmp_path / "private_qwen_prime_rl.template.toml"
    manifest = tmp_path / "private_training_config_manifest.json"

    write_private_training_config(config, manifest)
    data = tomllib.loads(config.read_text(encoding="utf-8"))

    assert data["name"] == "agades-pqc-private-qwen-pedagogical-rl"
    assert data["model"] == "${AGADES_QWEN_BASE_MODEL}"
    assert data["env"][0]["id"] == "agades-pqc-verifier-env"
    assert data["env"][0]["args"] == {"num_examples": -1}
    assert data["eval"]["env"][0]["id"] == "agades-pqc-verifier-env"
    assert data["buffer"]["online_difficulty_filtering"] is True
    assert data["buffer"]["skip_verification"] is False
    assert data["run_config"]["method"] == "pedagogical_rl"
    assert data["run_config"]["private_outputs_only"] is True
    assert data["run_config"]["publish_to_hf_public"] is False
    assert data["run_config"]["publish_to_prime_public"] is False
    assert data["run_config"]["reward_terms"] == [
        "formal_validity",
        "cryptographic_applicability",
        "no_security_overclaim",
        "student_readability",
        "reproducibility",
        "reviewer_quality",
        "task_match",
        "proof_obligation_coverage",
    ]
    assert data.get("env_files", []) == []


def test_committed_private_training_config_is_in_sync(tmp_path: Path) -> None:
    generated_config = tmp_path / "private_qwen_prime_rl.template.toml"
    generated_manifest = tmp_path / "private_training_config_manifest.json"

    write_private_training_config(generated_config, generated_manifest)
    expected_manifest = build_private_training_manifest(config_path=CONFIG_PATH)

    assert CONFIG_PATH.read_bytes() == generated_config.read_bytes()
    assert json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) == expected_manifest


def test_private_training_config_verify_accepts_committed_artifacts() -> None:
    result = verify_private_training_config(CONFIG_PATH, MANIFEST_PATH)

    assert result == {
        "schema_version": PRIVATE_TRAINING_CONFIG_VERIFICATION_SCHEMA,
        "config_path": CONFIG_PATH.as_posix(),
        "manifest_path": MANIFEST_PATH.as_posix(),
        "accepted": True,
        "summary": {
            "dataset_sources": 3,
            "dataset_controls": 5,
            "reward_terms": 8,
            "linked_artifacts": 6,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_private_training_config_rejects_public_weight_publication(
    tmp_path: Path,
) -> None:
    config = tmp_path / "private_qwen_prime_rl.template.toml"
    manifest = tmp_path / "private_training_config_manifest.json"
    payload = write_private_training_config(config, manifest)
    payload["qwen"]["publish_weights_publicly"] = True
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    result = verify_private_training_config(config, manifest)

    assert result["accepted"] is False
    assert "Private Qwen weights must never be public." in result["failures"]


def test_private_training_config_rejects_public_dataset_publication(
    tmp_path: Path,
) -> None:
    config = tmp_path / "private_qwen_prime_rl.template.toml"
    manifest = tmp_path / "private_training_config_manifest.json"
    payload = write_private_training_config(config, manifest)
    payload["datasets"]["publication_allowed"] = True
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    result = verify_private_training_config(config, manifest)

    assert result["accepted"] is False
    assert "Private training datasets must never be public." in result["failures"]


def test_private_training_config_rejects_env_file_upload(
    tmp_path: Path,
) -> None:
    config = tmp_path / "private_qwen_prime_rl.template.toml"
    manifest = tmp_path / "private_training_config_manifest.json"

    write_private_training_config(config, manifest)
    text = config.read_text(encoding="utf-8").replace(
        "env_files = []",
        'env_files = [".env"]',
    )
    config.write_text(text, encoding="utf-8")

    result = verify_private_training_config(config, manifest)

    assert result["accepted"] is False
    assert "Prime RL config must not upload env_files." in result["failures"]
    assert "Prime RL config must not reference .env files." in result["failures"]


def test_private_training_config_cli_round_trip(tmp_path: Path) -> None:
    config = tmp_path / "private_qwen_prime_rl.template.toml"
    manifest = tmp_path / "private_training_config_manifest.json"

    write_result = CliRunner().invoke(
        app,
        [
            "private-training-config",
            "--config",
            str(config),
            "--manifest",
            str(manifest),
        ],
    )
    verify_result = CliRunner().invoke(
        app,
        [
            "private-training-config-verify",
            "--config",
            str(config),
            "--manifest",
            str(manifest),
        ],
    )

    assert write_result.exit_code == 0
    assert f"private_training_config={config}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
