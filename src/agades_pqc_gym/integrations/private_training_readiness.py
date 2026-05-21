from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

PRIVATE_TRAINING_READINESS_SCHEMA = "agades.pqc.private_training_readiness.v1"
PRIVATE_TRAINING_READINESS_VERIFICATION_SCHEMA = (
    "agades.pqc.private_training_readiness_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_READINESS_PATH = Path("docs/private_training_readiness.json")
PRIVATE_DATASET_CURATION_PATH = "docs/private_dataset_curation.json"
PRIVATE_TRAINING_MANIFEST_PATH = "docs/private_training_config_manifest.json"
PEDAGOGICAL_RL_METHOD_PATH = "docs/pedagogical_rl_method.json"
REQUIRED_GITIGNORE_PATTERNS = [
    ".env",
    ".env.*",
    "private/",
]
REQUIRED_DATASET_CONTROLS = [
    "license_review",
    "provenance_tracking",
    "deduplication",
    "redaction",
    "contamination_audit",
]
PRIVATE_DATASET_SOURCES = [
    "facebookresearch/LWE-benchmarking",
    "facebook/TAPAS",
    "pq-code-package",
]
LINKED_ARTIFACT_PATHS = {
    "gitignore": ".gitignore",
    "env_template": ".env.example",
    "private_run_policy": "docs/private_run_policy.json",
    "private_dataset_curation": PRIVATE_DATASET_CURATION_PATH,
    "pedagogical_rl_method": PEDAGOGICAL_RL_METHOD_PATH,
    "private_training_manifest": PRIVATE_TRAINING_MANIFEST_PATH,
    "prime_training_template": (
        "prime_intellect/training/private_qwen_prime_rl.template.toml"
    ),
    "rl_environment_contract": "docs/rl_environment_contract.json",
    "prime_eval_config_manifest": "docs/prime_eval_config_manifest.json",
    "prime_environment_manifest": (
        "prime_intellect/verifiers_environment/prime_manifest.json"
    ),
    "openevolve_config": "examples/openevolve/config.yaml",
    "openevolve_smoke": "reports/openevolve_smoke.json",
    "deepevolve_manifest": "docs/deepevolve_research_hooks_manifest.json",
    "reviewer_governance": "docs/reviewer_governance.json",
}
READINESS_GATE_IDS = [
    "private_qwen_base_model_review",
    "private_qwen_trainable_weights_available",
    "dataset_license_review_complete",
    "dataset_provenance_manifest_complete",
    "dataset_deduplication_report_complete",
    "dataset_redaction_report_complete",
    "dataset_contamination_audit_complete",
    "pedagogical_trace_quality_review_complete",
    "prime_private_training_environment_reviewed",
    "formal_obligation_coverage_reviewed",
    "cryptography_domain_reviewers_assigned",
]
SECRET_VALUE_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        r"\bhf_[A-Za-z0-9]{20,}\b",
        r"\bsk-[A-Za-z0-9_-]{20,}\b",
        r"\bgh[pousr]_[A-Za-z0-9]{20,}\b",
        r"\bnvapi-[A-Za-z0-9_-]{20,}\b",
        r"\bpint_[A-Za-z0-9_-]{20,}\b",
    )
]


def build_private_training_readiness(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    return {
        "schema_version": PRIVATE_TRAINING_READINESS_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "classification": {
            "public_artifact_only": True,
            "contains_private_dataset_rows": False,
            "contains_private_trace_rows": False,
            "contains_secret_values": False,
            "contains_private_model_paths": False,
            "records_secret_presence": False,
        },
        "launch_status": {
            "ready": False,
            "state": "blocked",
            "reason": (
                "blocked_until_private_model_dataset_reviews_and_private_"
                "infrastructure_are_verified"
            ),
        },
        "required_inputs": {
            "qwen": {
                "target_model": "Qwen3.6-27B-private",
                "base_model_env": "AGADES_QWEN_BASE_MODEL",
                "gguf_otq_5bit_env": "AGADES_QWEN_GGUF_OTQ_5BIT_PATH",
                "lora_adapter_env": "AGADES_QWEN_LORA_ADAPTER_PATH",
                "preferred_user_artifact": "private GGUF OTQ 5-bit",
                "direct_gguf_training_allowed": False,
                "training_path": (
                    "LoRA_or_QLoRA_on_trainable_weights_then_private_GGUF_"
                    "OTQ_quantization"
                ),
                "status": "required_unverified",
                "public_release_allowed": False,
            },
            "datasets": {
                "sources": list(PRIVATE_DATASET_SOURCES),
                "curation_manifest_path": PRIVATE_DATASET_CURATION_PATH,
                "required_controls": list(REQUIRED_DATASET_CONTROLS),
                "status": (
                    "blocked_until_license_provenance_redaction_and_"
                    "contamination_review"
                ),
                "public_rows_allowed": False,
                "public_traces_allowed": False,
                "public_reviewer_annotations_allowed": False,
            },
            "pedagogical_rl": {
                "method": "pedagogical_rl",
                "method_manifest_path": PEDAGOGICAL_RL_METHOD_PATH,
                "requires_reviewer_quality_signal": True,
                "requires_no_security_overclaim": True,
                "raw_private_signals_publication_allowed": False,
            },
            "prime_intellect": {
                "api_key_env": "PRIME_API_KEY",
                "organization_env": "PRIME_ORG",
                "environment_slug_env": "PRIME_ENVIRONMENT_SLUG",
                "visibility_env": "PRIME_VISIBILITY",
                "required_visibility": "PRIVATE",
                "training_config_template": (
                    "prime_intellect/training/private_qwen_prime_rl.template.toml"
                ),
                "training_manifest": PRIVATE_TRAINING_MANIFEST_PATH,
                "status": "required_unverified",
            },
            "hugging_face": {
                "token_env": "HF_TOKEN",
                "organization_env": "HF_ORG",
                "space_visibility_env": "HF_SPACE_VISIBILITY",
                "required_private_assets": [
                    "private training traces",
                    "private curated datasets",
                    "private Qwen weights or adapters",
                ],
                "public_private_asset_upload_allowed": False,
            },
        },
        "readiness_gates": _readiness_gates(),
        "credential_policy": {
            "secret_values_recorded": False,
            "secret_presence_recorded": False,
            "reads_env_files": False,
            "reads_process_environment": False,
            "required_env_names": [
                "PRIME_API_KEY",
                "PRIME_ORG",
                "HF_TOKEN",
                "WANDB_API_KEY",
                "AGADES_QWEN_BASE_MODEL",
                "AGADES_QWEN_GGUF_OTQ_5BIT_PATH",
                "AGADES_QWEN_LORA_ADAPTER_PATH",
            ],
            "env_template_path": ".env.example",
            "required_gitignore_patterns": list(REQUIRED_GITIGNORE_PATTERNS),
        },
        "publication_boundary": {
            "public_artifact": DEFAULT_READINESS_PATH.as_posix(),
            "publish_finetuned_qwen_publicly": False,
            "publish_training_traces_publicly": False,
            "publish_curated_dataset_publicly": False,
            "publish_reviewer_annotations_publicly": False,
            "publish_secret_presence_publicly": False,
            "allowed_public_content": [
                "sanitized status",
                "environment variable names",
                "relative public artifact paths",
                "blocked readiness gates",
                "review requirements",
            ],
        },
        "linked_artifacts": _linked_artifacts(project_root),
        "release_gates": [
            "uv run pytest tests/test_private_training_readiness.py -q",
            "uv run agades-pqc private-training-readiness --out "
            "docs/private_training_readiness.json",
            "uv run agades-pqc private-training-readiness-verify --readiness "
            "docs/private_training_readiness.json",
            "uv run agades-pqc private-training-config-verify --config "
            "prime_intellect/training/private_qwen_prime_rl.template.toml "
            "--manifest docs/private_training_config_manifest.json",
            "uv run agades-pqc private-dataset-curation-verify --curation "
            "docs/private_dataset_curation.json",
        ],
    }


def write_private_training_readiness(
    out: Path = DEFAULT_READINESS_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    readiness = build_private_training_readiness(root=project_root)
    resolved_out = _resolve_path(out, project_root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(readiness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return readiness


def verify_private_training_readiness(
    readiness_path: Path = DEFAULT_READINESS_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    readiness = _read_readiness(
        _resolve_path(readiness_path, project_root),
        failures,
    )
    expected = build_private_training_readiness(root=project_root)

    if readiness:
        if readiness != expected:
            failures.append("Private training readiness artifact is not in sync.")
        _verify_no_secret_values(readiness, failures)
        _verify_classification(readiness, failures)
        _verify_launch_status(readiness, failures)
        _verify_required_inputs(readiness, failures)
        _verify_readiness_gates(readiness, failures)
        _verify_credential_policy(readiness, project_root, failures)
        _verify_publication_boundary(readiness, failures)
        _verify_linked_artifacts(readiness, expected, project_root, failures)

    summary = {
        "ready": readiness.get("launch_status", {}).get("ready") is True,
        "blocked_gates": sum(
            1
            for gate in readiness.get("readiness_gates", [])
            if isinstance(gate, dict) and gate.get("status") == "blocked"
        ),
        "linked_artifacts": len(readiness.get("linked_artifacts", {})),
        "failure_count": len(failures),
    }
    return {
        "schema_version": PRIVATE_TRAINING_READINESS_VERIFICATION_SCHEMA,
        "readiness_path": readiness_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _readiness_gates() -> list[dict[str, Any]]:
    evidence = {
        "private_qwen_base_model_review": (
            "AGADES_QWEN_BASE_MODEL must reference a private, reviewed, "
            "trainable Qwen3.6-27B source."
        ),
        "private_qwen_trainable_weights_available": (
            "GGUF OTQ 5-bit is a private target artifact; training must use "
            "reviewed trainable weights or adapters before private quantization."
        ),
        "dataset_license_review_complete": (
            "Each source in docs/private_dataset_curation.json must have a "
            "completed license review before ingestion."
        ),
        "dataset_provenance_manifest_complete": (
            "Private per-row provenance and hash manifests must exist before "
            "training."
        ),
        "dataset_deduplication_report_complete": (
            "Private exact, normalized, and near-duplicate reports must prove "
            "cross-source deduplication before training."
        ),
        "dataset_redaction_report_complete": (
            "Private redaction report must prove credentials, personal data, and "
            "unlicensed spans were removed."
        ),
        "dataset_contamination_audit_complete": (
            "Private contamination report must reject public overlap and prompt "
            "or reviewer-annotation leakage."
        ),
        "pedagogical_trace_quality_review_complete": (
            "Pedagogical RL traces require reviewer-quality and no-overclaim "
            "signals before Qwen fine-tuning."
        ),
        "prime_private_training_environment_reviewed": (
            "Prime org, environment, private storage, and visibility must be "
            "reviewed out of band."
        ),
        "formal_obligation_coverage_reviewed": (
            "Formal obligations and family invariants must be checked against "
            "the private trace task mix."
        ),
        "cryptography_domain_reviewers_assigned": (
            "Domain reviewers must be assigned before private claims or training "
            "promotion."
        ),
    }
    return [
        {
            "id": gate_id,
            "status": "blocked",
            "blocks_launch": True,
            "evidence_required": evidence[gate_id],
        }
        for gate_id in READINESS_GATE_IDS
    ]


def _verify_no_secret_values(
    readiness: dict[str, Any],
    failures: list[str],
) -> None:
    encoded = json.dumps(readiness, sort_keys=True)
    if any(pattern.search(encoded) for pattern in SECRET_VALUE_PATTERNS):
        failures.append(
            "Private training readiness artifact contains a secret-looking value."
        )


def _verify_classification(
    readiness: dict[str, Any],
    failures: list[str],
) -> None:
    classification = _dict_or_empty(readiness.get("classification"))
    expected = {
        "public_artifact_only": True,
        "contains_private_dataset_rows": False,
        "contains_private_trace_rows": False,
        "contains_secret_values": False,
        "contains_private_model_paths": False,
        "records_secret_presence": False,
    }
    if classification != expected:
        failures.append("Private training readiness classification is incorrect.")


def _verify_launch_status(
    readiness: dict[str, Any],
    failures: list[str],
) -> None:
    status = _dict_or_empty(readiness.get("launch_status"))
    if status.get("ready") is not False:
        failures.append(
            "Private training readiness must keep launch_status.ready false "
            "until private reviews are complete."
        )
    if status.get("state") != "blocked":
        failures.append("Private training readiness state must be blocked.")
    if status.get("reason") != (
        "blocked_until_private_model_dataset_reviews_and_private_"
        "infrastructure_are_verified"
    ):
        failures.append("Private training readiness block reason is incorrect.")


def _verify_required_inputs(
    readiness: dict[str, Any],
    failures: list[str],
) -> None:
    inputs = _dict_or_empty(readiness.get("required_inputs"))
    qwen = _dict_or_empty(inputs.get("qwen"))
    if qwen.get("base_model_env") != "AGADES_QWEN_BASE_MODEL":
        failures.append("Private training readiness must use AGADES_QWEN_BASE_MODEL.")
    if qwen.get("direct_gguf_training_allowed") is not False:
        failures.append("Private readiness must not allow direct GGUF training.")
    if qwen.get("public_release_allowed") is not False:
        failures.append("Private Qwen release must not be public.")

    datasets = _dict_or_empty(inputs.get("datasets"))
    if datasets.get("sources") != PRIVATE_DATASET_SOURCES:
        failures.append("Private readiness dataset sources are incorrect.")
    if datasets.get("required_controls") != REQUIRED_DATASET_CONTROLS:
        failures.append("Private readiness dataset controls are incorrect.")
    for key in (
        "public_rows_allowed",
        "public_traces_allowed",
        "public_reviewer_annotations_allowed",
    ):
        if datasets.get(key) is not False:
            failures.append(f"Private readiness dataset {key} must be false.")

    prime = _dict_or_empty(inputs.get("prime_intellect"))
    if prime.get("api_key_env") != "PRIME_API_KEY":
        failures.append("Private readiness must name PRIME_API_KEY without value.")
    if prime.get("required_visibility") != "PRIVATE":
        failures.append("Prime private training visibility must be PRIVATE.")

    hf = _dict_or_empty(inputs.get("hugging_face"))
    if hf.get("token_env") != "HF_TOKEN":
        failures.append("Private readiness must name HF_TOKEN without value.")
    if hf.get("public_private_asset_upload_allowed") is not False:
        failures.append("Private HF asset upload must not be public.")


def _verify_readiness_gates(
    readiness: dict[str, Any],
    failures: list[str],
) -> None:
    gates = readiness.get("readiness_gates")
    if not isinstance(gates, list):
        failures.append("Private training readiness gates must be a list.")
        return
    if [gate.get("id") for gate in gates if isinstance(gate, dict)] != (
        READINESS_GATE_IDS
    ):
        failures.append("Private training readiness gate sequence is incorrect.")
    for gate in gates:
        if not isinstance(gate, dict):
            failures.append("Private training readiness gate must be an object.")
            continue
        if gate.get("status") != "blocked":
            failures.append("Private training readiness gates must stay blocked.")
        if gate.get("blocks_launch") is not True:
            failures.append("Private training readiness gates must block launch.")
        if not isinstance(gate.get("evidence_required"), str):
            failures.append("Private training readiness gate needs evidence text.")


def _verify_credential_policy(
    readiness: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    policy = _dict_or_empty(readiness.get("credential_policy"))
    for key in (
        "secret_values_recorded",
        "secret_presence_recorded",
        "reads_env_files",
        "reads_process_environment",
    ):
        if policy.get(key) is not False:
            failures.append(f"Credential policy {key} must be false.")
    if policy.get("required_gitignore_patterns") != REQUIRED_GITIGNORE_PATTERNS:
        failures.append("Credential policy gitignore patterns are incorrect.")
    if policy.get("env_template_path") != ".env.example":
        failures.append("Credential policy must point to .env.example.")

    gitignore = root / ".gitignore"
    try:
        lines = {
            line.strip()
            for line in gitignore.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
    except FileNotFoundError:
        failures.append(".gitignore is missing.")
        return
    for pattern in REQUIRED_GITIGNORE_PATTERNS:
        if pattern not in lines:
            failures.append(f".gitignore must contain {pattern}.")


def _verify_publication_boundary(
    readiness: dict[str, Any],
    failures: list[str],
) -> None:
    boundary = _dict_or_empty(readiness.get("publication_boundary"))
    for key in (
        "publish_finetuned_qwen_publicly",
        "publish_training_traces_publicly",
        "publish_curated_dataset_publicly",
        "publish_reviewer_annotations_publicly",
        "publish_secret_presence_publicly",
    ):
        if boundary.get(key) is not False:
            failures.append(f"Publication boundary {key} must be false.")
    if boundary.get("public_artifact") != DEFAULT_READINESS_PATH.as_posix():
        failures.append("Publication boundary public artifact path is incorrect.")


def _verify_linked_artifacts(
    readiness: dict[str, Any],
    expected: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    linked_artifacts = readiness.get("linked_artifacts")
    if not isinstance(linked_artifacts, dict):
        failures.append("Private readiness linked_artifacts must be an object.")
        return
    if linked_artifacts != expected.get("linked_artifacts"):
        failures.append("Private readiness linked artifact hashes are not in sync.")
    for name, artifact in linked_artifacts.items():
        if not isinstance(artifact, dict):
            failures.append(f"Private readiness linked artifact {name} must be object.")
            continue
        path = artifact.get("path")
        if not isinstance(path, str) or not path:
            failures.append(
                f"Private readiness linked artifact {name} is missing path."
            )
            continue
        if not (root / path).is_file():
            failures.append(f"Private readiness linked artifact is missing: {path}.")
        if artifact.get("sha256") is None:
            failures.append(
                f"Private readiness linked artifact {name} is missing SHA-256."
            )


def _linked_artifacts(root: Path) -> dict[str, dict[str, str | None]]:
    return {
        name: {
            "path": path,
            "sha256": _file_sha256(root / path),
        }
        for name, path in LINKED_ARTIFACT_PATHS.items()
    }


def _read_readiness(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Private training readiness artifact is missing: {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Private training readiness artifact is invalid JSON at line "
            f"{exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("Private training readiness artifact must be a JSON object.")
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
