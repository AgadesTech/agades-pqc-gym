from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.private_dataset_curation import (
    EVIDENCE_CONTRACTS,
    REQUIRED_CONTROLS,
)

PRIVATE_DATASET_EVIDENCE_VERIFICATION_SCHEMA = (
    "agades.pqc.private_dataset_evidence_verification.v1"
)
DEFAULT_CURATION_PATH = Path("docs/private_dataset_curation.json")
ROOT = Path(__file__).resolve().parents[3]


def verify_private_dataset_evidence_bundle(
    curation_path: Path = DEFAULT_CURATION_PATH,
    *,
    evidence_root: Path = Path("."),
    root: Path | None = None,
) -> dict[str, Any]:
    """Verify private curation evidence without echoing private evidence values."""

    project_root = (root or ROOT).resolve()
    resolved_curation_path = _resolve_path(curation_path, project_root)
    resolved_evidence_root = _resolve_path(evidence_root, project_root)
    failures: list[str] = []
    curation = _read_json_object(
        resolved_curation_path,
        "Private dataset curation",
        failures,
    )
    contracts = _contracts_from_curation(curation, failures)

    present_artifacts = 0
    accepted_artifacts = 0
    missing_artifacts = 0
    for control in REQUIRED_CONTROLS:
        contract = contracts.get(control)
        if not isinstance(contract, Mapping):
            failures.append(
                f"Private dataset evidence contract is missing: {control}."
            )
            continue
        artifact_path = contract.get("artifact_path")
        if not isinstance(artifact_path, str) or not artifact_path.startswith(
            "private/"
        ):
            failures.append(
                f"Private dataset evidence contract {control} path must stay private."
            )
            continue
        payload_path = resolved_evidence_root / artifact_path
        if not payload_path.is_file():
            missing_artifacts += 1
            failures.append(
                f"Private dataset evidence artifact is missing: {artifact_path}."
            )
            continue
        present_artifacts += 1
        payload = _read_json_object(
            payload_path,
            f"Private dataset evidence {control}",
            failures,
        )
        if _verify_evidence_payload(control, contract, payload, failures):
            accepted_artifacts += 1

    training_eligible = (
        not failures
        and len(contracts) == len(REQUIRED_CONTROLS)
        and present_artifacts == len(REQUIRED_CONTROLS)
        and accepted_artifacts == len(REQUIRED_CONTROLS)
    )
    return {
        "schema_version": PRIVATE_DATASET_EVIDENCE_VERIFICATION_SCHEMA,
        "curation_path": curation_path.as_posix(),
        "evidence_root": evidence_root.as_posix(),
        "accepted": not failures,
        "summary": {
            "contracts": len(contracts),
            "present_artifacts": present_artifacts,
            "accepted_artifacts": accepted_artifacts,
            "missing_artifacts": missing_artifacts,
            "training_eligible": training_eligible,
            "failure_count": len(failures),
        },
        "failures": failures,
    }


def _contracts_from_curation(
    curation: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    contracts = curation.get("evidence_contracts")
    if contracts != EVIDENCE_CONTRACTS:
        failures.append("Private dataset evidence contracts are not synchronized.")
    return dict(contracts) if isinstance(contracts, Mapping) else {}


def _verify_evidence_payload(
    control: str,
    contract: Mapping[str, Any],
    payload: dict[str, Any],
    failures: list[str],
) -> bool:
    if payload.get("schema_version") != contract.get("schema_version"):
        failures.append(f"Private dataset evidence {control} schema is incorrect.")
    if payload.get("control") != control:
        failures.append(f"Private dataset evidence {control} control is incorrect.")
    if payload.get("public_release_allowed") is not False:
        failures.append(
            f"Private dataset evidence {control} must not be public-releaseable."
        )
    if payload.get("contains_private_rows") is not False:
        failures.append(
            f"Private dataset evidence {control} must not expose private rows."
        )

    evidence_records = payload.get("evidence_records")
    if not isinstance(evidence_records, list) or not evidence_records:
        failures.append(f"Private dataset evidence {control} records are missing.")
        evidence_records = []
    required_fields = _string_list(contract.get("required_fields"))
    for index, record in enumerate(evidence_records):
        if not isinstance(record, Mapping):
            failures.append(
                f"Private dataset evidence {control} record {index} must be object."
            )
            continue
        for field in required_fields:
            if field not in record:
                failures.append(
                    f"Private dataset evidence {control} record {index} is "
                    f"missing required field: {field}."
                )
        _verify_record_private_paths(control, index, record, failures)

    accepted = payload.get("accepted") is True
    if not accepted:
        failures.append(f"Private dataset evidence {control} is not accepted.")
    return accepted


def _verify_record_private_paths(
    control: str,
    index: int,
    record: Mapping[str, Any],
    failures: list[str],
) -> None:
    private_storage_path = record.get("private_storage_path")
    if private_storage_path is not None and (
        not isinstance(private_storage_path, str)
        or not private_storage_path.startswith("private/")
    ):
        failures.append(
            f"Private dataset evidence {control} record {index} storage path "
            "must stay private."
        )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _read_json_object(
    path: Path,
    label: str,
    failures: list[str],
) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"{label} artifact is missing: {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"{label} artifact is invalid JSON at line {exc.lineno}.")
        return {}
    if not isinstance(payload, dict):
        failures.append(f"{label} artifact must be a JSON object.")
        return {}
    return payload


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path
