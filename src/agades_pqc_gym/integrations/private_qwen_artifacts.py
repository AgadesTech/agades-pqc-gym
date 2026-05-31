from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

PRIVATE_QWEN_ARTIFACT_PLAN_SCHEMA = "agades.pqc.private_qwen_artifact_plan.v1"
PRIVATE_QWEN_ARTIFACT_VERIFICATION_SCHEMA = (
    "agades.pqc.private_qwen_artifact_verification.v1"
)
PRIVATE_QWEN_ARTIFACT_PLAN_ENV = "AGADES_QWEN_ARTIFACT_PLAN"
PRIVATE_QWEN_ARTIFACT_PLAN_TEMPLATE = "private/reports/qwen/artifact_plan.json"
PRIVATE_QWEN_ARTIFACT_VERIFICATION_COMMAND = (
    "uv run agades-pqc private-qwen-artifacts-verify --plan "
    f"{PRIVATE_QWEN_ARTIFACT_PLAN_TEMPLATE}"
)
PRIVATE_QWEN_ARTIFACT_VERIFIER = (
    "agades_pqc_gym.integrations.private_qwen_artifacts."
    "verify_private_qwen_artifact_plan"
)
PRIVATE_QWEN_TARGET_MODEL = "Qwen/Qwen3.6-35B-A3B"
PRIVATE_QWEN_PRIME_INFERENCE_MODEL = "qwen/qwen3.6-35b-a3b"
PRIVATE_QWEN_MODEL_LABEL = "Qwen3.6-35B-A3B MoE"
PRIVATE_QWEN_TRAINING_PATH = (
    "LoRA_or_QLoRA_on_trainable_weights_then_private_GGUF_OTQ_quantization"
)
REQUIRED_ARTIFACTS = {
    "trainable_base": {
        "kind": "trainable_weights",
        "derived_flag": None,
    },
    "lora_adapter": {
        "kind": "lora_or_qlora_adapter",
        "derived_flag": "derived_from_trainable_base",
    },
    "gguf_otq_5bit": {
        "kind": "private_quantized_gguf_otq_5bit",
        "derived_flag": "derived_from_lora_adapter",
        "quantization": "GGUF_OTQ_5BIT",
    },
}
PUBLICATION_FLAGS = [
    "publish_weights_to_hf_public",
    "publish_adapters_to_hf_public",
    "publish_to_prime_public",
    "publish_training_traces_public",
    "publish_private_model_paths_public",
]
REVIEW_FLAGS = [
    "model_license_reviewed",
    "private_storage_reviewed",
    "quantization_reviewed",
    "release_boundary_reviewed",
]


def verify_private_qwen_artifact_plan(plan_path: Path) -> dict[str, Any]:
    failures: list[str] = []
    plan = _read_json_object(plan_path, failures)
    artifacts = _dict_or_empty(plan.get("artifacts"))
    publication = _dict_or_empty(plan.get("publication"))
    review = _dict_or_empty(plan.get("review"))

    if plan.get("schema_version") != PRIVATE_QWEN_ARTIFACT_PLAN_SCHEMA:
        failures.append("Private Qwen artifact plan schema is incorrect.")
    if plan.get("target_model") != PRIVATE_QWEN_TARGET_MODEL:
        failures.append("Private Qwen target model is incorrect.")
    if plan.get("training_path") != PRIVATE_QWEN_TRAINING_PATH:
        failures.append("Private Qwen training path is incorrect.")
    if plan.get("direct_gguf_training_attempted") is not False:
        failures.append("Private Qwen plan must not use direct GGUF training.")

    for name, expected in REQUIRED_ARTIFACTS.items():
        artifact = _dict_or_empty(artifacts.get(name))
        _verify_artifact(name, artifact, expected, failures)

    for flag in PUBLICATION_FLAGS:
        if publication.get(flag) is not False:
            failures.append(f"Private Qwen publication flag {flag} must be false.")
    for flag in REVIEW_FLAGS:
        if review.get(flag) is not True:
            failures.append(f"Private Qwen review flag {flag} must be true.")

    return {
        "schema_version": PRIVATE_QWEN_ARTIFACT_VERIFICATION_SCHEMA,
        "plan_path": plan_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "target_model": plan.get("target_model"),
            "trainable_base_present": bool(artifacts.get("trainable_base")),
            "adapter_present": bool(artifacts.get("lora_adapter")),
            "private_quantization_present": bool(artifacts.get("gguf_otq_5bit")),
            "direct_gguf_training_attempted": plan.get(
                "direct_gguf_training_attempted",
            ),
            "public_release_allowed": any(
                publication.get(flag) is True for flag in PUBLICATION_FLAGS
            ),
            "failure_count": len(failures),
        },
        "failures": failures,
    }


def _verify_artifact(
    name: str,
    artifact: dict[str, Any],
    expected: Mapping[str, Any],
    failures: list[str],
) -> None:
    if not artifact:
        failures.append(f"Private Qwen artifact {name} is missing.")
        return
    if artifact.get("kind") != expected.get("kind"):
        failures.append(f"Private Qwen artifact {name} kind is incorrect.")
    path = artifact.get("path")
    if not _is_private_relative_path(path):
        failures.append(f"Private Qwen artifact {name} path must stay private.")
    if not _is_sha256(artifact.get("sha256")):
        failures.append(f"Private Qwen artifact {name} is missing SHA-256.")
    if artifact.get("public_release_allowed") is not False:
        failures.append(f"Private Qwen artifact {name} must not be public-releaseable.")
    derived_flag = expected.get("derived_flag")
    if isinstance(derived_flag, str) and artifact.get(derived_flag) is not True:
        failures.append(f"Private Qwen artifact {name} derivation is not verified.")
    expected_quantization = expected.get("quantization")
    if (
        isinstance(expected_quantization, str)
        and artifact.get("quantization") != expected_quantization
    ):
        failures.append(f"Private Qwen artifact {name} quantization is incorrect.")


def _read_json_object(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Private Qwen artifact plan is missing: {path.as_posix()}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Private Qwen artifact plan is invalid JSON at line {exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("Private Qwen artifact plan must be a JSON object.")
        return {}
    return payload


def _dict_or_empty(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_private_relative_path(value: object) -> bool:
    if not isinstance(value, str):
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and len(path.parts) > 1
        and path.parts[0] == "private"
        and ".." not in path.parts
    )
