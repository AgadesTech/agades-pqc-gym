from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.private_qwen_artifacts import (
    PRIVATE_QWEN_ARTIFACT_VERIFICATION_SCHEMA,
    verify_private_qwen_artifact_plan,
)


def test_private_qwen_artifact_plan_accepts_lora_then_private_gguf(
    tmp_path: Path,
) -> None:
    plan_path = _write_plan(tmp_path, _valid_plan())

    result = verify_private_qwen_artifact_plan(plan_path)

    assert result == {
        "schema_version": PRIVATE_QWEN_ARTIFACT_VERIFICATION_SCHEMA,
        "plan_path": plan_path.as_posix(),
        "accepted": True,
        "summary": {
            "target_model": "Qwen3.6-27B-private",
            "trainable_base_present": True,
            "adapter_present": True,
            "private_quantization_present": True,
            "direct_gguf_training_attempted": False,
            "public_release_allowed": False,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_private_qwen_artifact_plan_rejects_direct_gguf_training(
    tmp_path: Path,
) -> None:
    payload = _valid_plan()
    payload["training_path"] = "direct_gguf_otq_training"
    payload["direct_gguf_training_attempted"] = True
    plan_path = _write_plan(tmp_path, payload)

    result = verify_private_qwen_artifact_plan(plan_path)

    assert result["accepted"] is False
    assert "Private Qwen plan must not use direct GGUF training." in (
        result["failures"]
    )


def test_private_qwen_artifact_plan_rejects_public_publication(
    tmp_path: Path,
) -> None:
    payload = _valid_plan()
    payload["publication"]["publish_weights_to_hf_public"] = True
    payload["artifacts"]["lora_adapter"]["public_release_allowed"] = True
    plan_path = _write_plan(tmp_path, payload)

    result = verify_private_qwen_artifact_plan(plan_path)

    assert result["accepted"] is False
    assert (
        "Private Qwen publication flag publish_weights_to_hf_public must be false."
    ) in result["failures"]
    assert "Private Qwen artifact lora_adapter must not be public-releaseable." in (
        result["failures"]
    )


def test_private_qwen_artifact_plan_rejects_non_private_paths(
    tmp_path: Path,
) -> None:
    payload = _valid_plan()
    payload["artifacts"]["trainable_base"]["path"] = "models/qwen-base"
    payload["artifacts"]["gguf_otq_5bit"]["path"] = "hf/qwen.gguf"
    plan_path = _write_plan(tmp_path, payload)

    result = verify_private_qwen_artifact_plan(plan_path)

    assert result["accepted"] is False
    assert "Private Qwen artifact trainable_base path must stay private." in (
        result["failures"]
    )
    assert "Private Qwen artifact gguf_otq_5bit path must stay private." in (
        result["failures"]
    )


def test_private_qwen_artifact_plan_rejects_private_path_traversal(
    tmp_path: Path,
) -> None:
    payload = _valid_plan()
    payload["artifacts"]["lora_adapter"]["path"] = "private/../public/adapter"
    plan_path = _write_plan(tmp_path, payload)

    result = verify_private_qwen_artifact_plan(plan_path)

    assert result["accepted"] is False
    assert "Private Qwen artifact lora_adapter path must stay private." in (
        result["failures"]
    )


def test_private_qwen_artifact_plan_rejects_missing_adapter_hash(
    tmp_path: Path,
) -> None:
    payload = _valid_plan()
    del payload["artifacts"]["lora_adapter"]["sha256"]
    plan_path = _write_plan(tmp_path, payload)

    result = verify_private_qwen_artifact_plan(plan_path)

    assert result["accepted"] is False
    assert "Private Qwen artifact lora_adapter is missing SHA-256." in (
        result["failures"]
    )


def test_private_qwen_artifact_plan_cli_round_trip(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path, _valid_plan())

    result = CliRunner().invoke(
        app,
        ["private-qwen-artifacts-verify", "--plan", str(plan_path)],
    )

    assert result.exit_code == 0
    assert '"accepted": true' in result.output
    assert '"private_quantization_present": true' in result.output


def _write_plan(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "private/reports/qwen/artifact_plan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def _valid_plan() -> dict[str, object]:
    return {
        "schema_version": "agades.pqc.private_qwen_artifact_plan.v1",
        "target_model": "Qwen3.6-27B-private",
        "training_path": (
            "LoRA_or_QLoRA_on_trainable_weights_then_private_GGUF_OTQ_"
            "quantization"
        ),
        "direct_gguf_training_attempted": False,
        "artifacts": {
            "trainable_base": {
                "kind": "trainable_weights",
                "path": "private/models/qwen3_6_27b/base",
                "sha256": "1" * 64,
                "public_release_allowed": False,
            },
            "lora_adapter": {
                "kind": "lora_or_qlora_adapter",
                "path": "private/models/qwen3_6_27b/adapters/agades-lora",
                "sha256": "2" * 64,
                "public_release_allowed": False,
                "derived_from_trainable_base": True,
            },
            "gguf_otq_5bit": {
                "kind": "private_quantized_gguf_otq_5bit",
                "path": "private/models/qwen3_6_27b/quantized/agades-qwen.otq5.gguf",
                "sha256": "3" * 64,
                "public_release_allowed": False,
                "derived_from_lora_adapter": True,
                "quantization": "GGUF_OTQ_5BIT",
            },
        },
        "publication": {
            "publish_weights_to_hf_public": False,
            "publish_adapters_to_hf_public": False,
            "publish_to_prime_public": False,
            "publish_training_traces_public": False,
            "publish_private_model_paths_public": False,
        },
        "review": {
            "model_license_reviewed": True,
            "private_storage_reviewed": True,
            "quantization_reviewed": True,
            "release_boundary_reviewed": True,
        },
    }
