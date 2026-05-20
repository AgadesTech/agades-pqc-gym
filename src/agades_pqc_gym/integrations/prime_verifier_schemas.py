from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.evaluator_result import EVALUATOR_RESULT_SCHEMA
from agades_pqc_gym.integrations.task_metadata import (
    TASK_METADATA_SCHEMA,
    TaskMetadata,
)
from agades_pqc_gym.verifier import VerifierResult

PRIME_VERIFIER_SCHEMAS_SCHEMA = "agades.pqc.prime_verifier_schemas.v1"
PRIME_VERIFIER_SCHEMAS_VERIFICATION_SCHEMA = (
    "agades.pqc.prime_verifier_schemas_verification.v1"
)
SCHEMA_BASE_ID = "https://agades.tech/schemas/agades-pqc-gym"
ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILES = {
    "submission": "attack_plan.schema.json",
    "task_metadata": "task_metadata.schema.json",
    "result": "verifier_result.schema.json",
}
_EXPECTED_PROJECT = {
    "name": "Agades PQC Gym",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    "package": "agades_pqc_gym",
    "cli": "agades-pqc",
}
_EXPECTED_FALSE_SAFETY_FLAGS = (
    "accepts_arbitrary_code",
    "accepts_live_targets",
    "security_claim",
    "publishes_private_candidates",
)
_REQUIRED_RELEASE_GATES = (
    "uv run pytest tests/test_prime_verifier_schemas.py -q",
    "uv run agades-pqc prime-schemas --out prime_intellect/schemas",
    "uv run agades-pqc prime-schemas-verify --schemas prime_intellect/schemas",
    "uv run agades-pqc prime-manifest-verify --manifest "
    "prime_intellect/verifiers_environment/prime_manifest.json",
    "uv run agades-pqc publication-manifest-verify --manifest "
    "docs/publication_manifest.json",
    "uv run agades-pqc ecosystem-smoke-verify --report "
    "reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
)
_REQUIRED_SUBMISSION_FIELDS = (
    "attack_plan_id",
    "metadata",
    "operators",
    "target",
)
_REQUIRED_RESULT_FIELDS = (
    "accepted",
    "evaluation_status",
    "schema_valid",
    "schema_version",
)
_REQUIRED_TASK_METADATA_FIELDS = (
    "operator_types",
    "seed_attack_plan_sha256",
    "seed_accepted",
    "seed_evaluation_status",
    "seed_estimator_name",
    "seed_reproduction_attempted",
    "seed_reproduction_status",
    "seed_reproduction_success",
    "seed_reward",
)


def build_prime_verifier_schemas() -> dict[str, dict[str, Any]]:
    attack_plan_schema = _schema_document(
        AttackPlan.model_json_schema(),
        schema_id=f"{SCHEMA_BASE_ID}/{SCHEMA_FILES['submission']}",
        title="Agades PQC Gym AttackPlan Submission",
        description=(
            "Single JSON AttackPlan object accepted by Agades PQC Gym public "
            "verifier surfaces, including Prime Verifiers tasks and Hugging "
            "Face demos. This schema does not permit executable code."
        ),
    )
    verifier_result_schema = _schema_document(
        VerifierResult.model_json_schema(),
        schema_id=f"{SCHEMA_BASE_ID}/{SCHEMA_FILES['result']}",
        title="Agades PQC Gym Verifier Result",
        description=(
            "Deterministic public verifier result emitted by agades-pqc verify, "
            "Prime verifier wrappers, and Hugging Face demo adapters."
        ),
    )
    task_metadata_schema = _schema_document(
        TaskMetadata.model_json_schema(),
        schema_id=f"{SCHEMA_BASE_ID}/{SCHEMA_FILES['task_metadata']}",
        title="Agades PQC Gym Task Metadata",
        description=(
            "Versioned task constraints shared by Prime Verifiers and Hugging "
            "Face dataset rows. Reward environments use these fields to keep "
            "candidate AttackPlan mutations on the intended family, target, "
            "support level, and operator sequence without requiring an exact "
            "attack_plan_id copy. Seed AttackPlan digest, estimator, "
            "reproduction, status, and reward fields make unsupported "
            "schema-only tasks explicit zero-reward safety checks while "
            "keeping reproducible fixture tasks inspectable."
        ),
    )
    manifest = {
        "schema_version": PRIME_VERIFIER_SCHEMAS_SCHEMA,
        "project": {
            **_EXPECTED_PROJECT,
        },
        "schemas": dict(SCHEMA_FILES),
        "contract": {
            "submission_shape": "single_attack_plan_json_object",
            "result_schema_version": "agades.pqc.verifier.v1",
            "task_metadata_schema_version": TASK_METADATA_SCHEMA,
            "evaluator_result_schema_version": EVALUATOR_RESULT_SCHEMA,
            "reward_surface": (
                "Prime scoring uses schema_valid, accepted, and task metadata "
                "matching fields."
            ),
            "compatible_surfaces": [
                "prime-verifiers-environment",
                "huggingface-space",
                "agades-pqc-cli",
            ],
        },
        "safety": {
            "accepts_arbitrary_code": False,
            "accepts_live_targets": False,
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "release": {
            "review_required_before_publish": True,
            "generator_command": (
                "uv run agades-pqc prime-schemas --out prime_intellect/schemas"
            ),
            "audit_gate": "prime-verifier-schemas",
        },
        "release_gates": [
            *_REQUIRED_RELEASE_GATES,
        ],
    }
    return {
        SCHEMA_FILES["submission"]: attack_plan_schema,
        SCHEMA_FILES["task_metadata"]: task_metadata_schema,
        SCHEMA_FILES["result"]: verifier_result_schema,
        "schema_manifest.json": manifest,
    }


def write_prime_verifier_schemas(out_dir: Path) -> dict[str, dict[str, Any]]:
    bundle = build_prime_verifier_schemas()
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, document in bundle.items():
        (out_dir / filename).write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return bundle


def verify_prime_verifier_schemas(
    schema_dir: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    resolved_schema_dir = schema_dir if schema_dir.is_absolute() else (
        project_root / schema_dir
    )
    failures: list[str] = []
    documents: dict[str, dict[str, Any]] = {}
    expected = build_prime_verifier_schemas()
    expected_schema_files = sorted(expected)

    if not resolved_schema_dir.is_dir():
        failures.append("Prime verifier schema directory is missing.")

    for filename, expected_document in expected.items():
        document, missing = _read_schema_document(
            resolved_schema_dir / filename,
            failures,
        )
        if missing:
            failures.append(f"Prime verifier schema is missing: {filename}.")
        if document is None:
            documents[filename] = {}
            continue
        documents[filename] = document
        if document != expected_document:
            failures.append(f"Prime verifier schema is not in sync: {filename}.")

    actual_schema_files = (
        sorted(path.name for path in resolved_schema_dir.glob("*.json"))
        if resolved_schema_dir.is_dir()
        else []
    )
    if actual_schema_files != expected_schema_files:
        failures.append("Prime verifier schema file set does not match the manifest.")

    manifest = documents.get("schema_manifest.json", {})
    _verify_manifest(manifest, failures)
    _verify_schema_documents(documents, failures)

    return _verification_result(
        schema_dir,
        documents,
        actual_schema_files,
        failures,
    )


def _read_schema_document(
    path: Path,
    failures: list[str],
) -> tuple[dict[str, Any] | None, bool]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, True
    except json.JSONDecodeError as exc:
        failures.append(
            f"Prime verifier schema invalid JSON in {path.name} at line {exc.lineno}."
        )
        return None, False

    if not isinstance(payload, dict):
        failures.append(f"Prime verifier schema must be a JSON object: {path.name}.")
        return None, False
    return payload, False


def _verify_manifest(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    if not manifest:
        return

    if manifest.get("schema_version") != PRIME_VERIFIER_SCHEMAS_SCHEMA:
        failures.append(
            "Prime schema manifest schema_version must be "
            f"{PRIME_VERIFIER_SCHEMAS_SCHEMA}."
        )

    project = manifest.get("project")
    if not isinstance(project, dict):
        failures.append("Prime schema manifest project must be an object.")
    else:
        for key, expected in _EXPECTED_PROJECT.items():
            if project.get(key) != expected:
                failures.append(f"Prime schema manifest project.{key} drifted.")

    if manifest.get("schemas") != SCHEMA_FILES:
        failures.append("Prime schema manifest file mapping drifted.")

    _verify_contract(manifest, failures)
    _verify_safety(manifest, failures)
    _verify_release(manifest, failures)
    _verify_release_gates(manifest, failures)


def _verify_contract(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    contract = manifest.get("contract")
    if not isinstance(contract, dict):
        failures.append("Prime schema manifest contract must be an object.")
        return
    if contract.get("submission_shape") != "single_attack_plan_json_object":
        failures.append("Prime schema submission shape drifted.")
    if contract.get("result_schema_version") != "agades.pqc.verifier.v1":
        failures.append("Prime result schema version drifted.")
    if contract.get("task_metadata_schema_version") != TASK_METADATA_SCHEMA:
        failures.append("Prime task metadata schema version drifted.")
    if contract.get("evaluator_result_schema_version") != EVALUATOR_RESULT_SCHEMA:
        failures.append("Prime evaluator result schema version drifted.")
    compatible_surfaces = contract.get("compatible_surfaces")
    if compatible_surfaces != [
        "prime-verifiers-environment",
        "huggingface-space",
        "agades-pqc-cli",
    ]:
        failures.append("Prime schema compatible surfaces drifted.")


def _verify_safety(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        failures.append("Prime schema manifest safety must be an object.")
        return
    for flag in _EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            if flag == "accepts_arbitrary_code":
                failures.append("Prime schema manifest allows arbitrary code.")
            elif flag == "accepts_live_targets":
                failures.append("Prime schema manifest allows live targets.")
            elif flag == "security_claim":
                failures.append("Prime schema manifest advertises a security claim.")
            elif flag == "publishes_private_candidates":
                failures.append(
                    "Prime schema manifest may publish private candidates."
                )


def _verify_release(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    release = manifest.get("release")
    if not isinstance(release, dict):
        failures.append("Prime schema manifest release must be an object.")
        return
    if release.get("review_required_before_publish") is not True:
        failures.append("Prime schema manifest lacks publication review gate.")
    if release.get("generator_command") != _REQUIRED_RELEASE_GATES[1]:
        failures.append("Prime schema generator command drifted.")
    if release.get("audit_gate") != "prime-verifier-schemas":
        failures.append("Prime schema audit gate drifted.")


def _verify_release_gates(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    release_gates = manifest.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append("Prime schema release_gates must be a list.")
        return
    for required_gate in _REQUIRED_RELEASE_GATES:
        if required_gate not in release_gates:
            failures.append(f"Prime schema release gate missing: {required_gate}")


def _verify_schema_documents(
    documents: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    submission_schema = documents.get(SCHEMA_FILES["submission"], {})
    result_schema = documents.get(SCHEMA_FILES["result"], {})
    task_metadata_schema = documents.get(SCHEMA_FILES["task_metadata"], {})

    _verify_required_fields(
        submission_schema,
        _REQUIRED_SUBMISSION_FIELDS,
        "Prime submission schema",
        failures,
    )
    _verify_required_fields(
        result_schema,
        _REQUIRED_RESULT_FIELDS,
        "Prime result schema",
        failures,
    )
    _verify_required_fields(
        task_metadata_schema,
        _REQUIRED_TASK_METADATA_FIELDS,
        "Prime task metadata schema",
        failures,
    )


def _verify_required_fields(
    schema: dict[str, Any],
    required_fields: tuple[str, ...],
    label: str,
    failures: list[str],
) -> None:
    if not schema:
        return
    required = schema.get("required")
    if not isinstance(required, list):
        failures.append(f"{label} required fields must be a list.")
        return
    for field in required_fields:
        if field not in required:
            failures.append(f"{label} does not require {field}.")


def _verification_result(
    schema_dir: Path,
    documents: dict[str, dict[str, Any]],
    actual_schema_files: list[str],
    failures: list[str],
) -> dict[str, Any]:
    manifest = documents.get("schema_manifest.json", {})
    if not isinstance(manifest, dict):
        manifest = {}
    contract = manifest.get("contract", {})
    if not isinstance(contract, dict):
        contract = {}
    safety = manifest.get("safety", {})
    if not isinstance(safety, dict):
        safety = {}
    release_gates = manifest.get("release_gates", [])
    if not isinstance(release_gates, list):
        release_gates = []

    return {
        "schema_version": PRIME_VERIFIER_SCHEMAS_VERIFICATION_SCHEMA,
        "schema_dir": schema_dir.as_posix(),
        "accepted": not failures,
        "summary": {
            "evaluator_result_schema_version": contract.get(
                "evaluator_result_schema_version"
            ),
            "failure_count": len(failures),
            "release_gate_count": len(release_gates),
            "result_required_fields": list(_REQUIRED_RESULT_FIELDS),
            "schema_files": actual_schema_files,
            "security_claim": safety.get("security_claim"),
            "submission_required_fields": list(_REQUIRED_SUBMISSION_FIELDS),
            "task_metadata_required_fields": list(_REQUIRED_TASK_METADATA_FIELDS),
            "task_metadata_schema_version": contract.get(
                "task_metadata_schema_version"
            ),
        },
        "failures": failures,
    }


def _schema_document(
    schema: dict[str, Any],
    *,
    schema_id: str,
    title: str,
    description: str,
) -> dict[str, Any]:
    document = dict(schema)
    document["$id"] = schema_id
    document["title"] = title
    document["description"] = description
    document.setdefault("$schema", "https://json-schema.org/draft/2020-12/schema")
    return document
