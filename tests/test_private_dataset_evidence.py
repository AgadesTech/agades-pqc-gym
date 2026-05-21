from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.private_dataset_curation import (
    build_private_dataset_curation,
)
from agades_pqc_gym.integrations.private_dataset_evidence import (
    PRIVATE_DATASET_EVIDENCE_VERIFICATION_SCHEMA,
    verify_private_dataset_evidence_bundle,
)


def test_private_dataset_evidence_bundle_accepts_complete_private_reports(
    tmp_path: Path,
) -> None:
    curation_path = _write_curation(tmp_path)
    _write_complete_evidence_bundle(tmp_path)

    result = verify_private_dataset_evidence_bundle(
        curation_path,
        evidence_root=tmp_path,
    )

    assert result == {
        "schema_version": PRIVATE_DATASET_EVIDENCE_VERIFICATION_SCHEMA,
        "curation_path": curation_path.as_posix(),
        "evidence_root": tmp_path.as_posix(),
        "accepted": True,
        "summary": {
            "contracts": 5,
            "present_artifacts": 5,
            "accepted_artifacts": 5,
            "missing_artifacts": 0,
            "training_eligible": True,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_private_dataset_evidence_bundle_rejects_missing_artifacts(
    tmp_path: Path,
) -> None:
    curation_path = _write_curation(tmp_path)
    _write_complete_evidence_bundle(tmp_path)
    (tmp_path / "private/reports/dataset_curation/redaction_report.json").unlink()

    result = verify_private_dataset_evidence_bundle(
        curation_path,
        evidence_root=tmp_path,
    )

    assert result["accepted"] is False
    assert result["summary"]["training_eligible"] is False
    assert result["summary"]["missing_artifacts"] == 1
    assert (
        "Private dataset evidence artifact is missing: "
        "private/reports/dataset_curation/redaction_report.json."
    ) in result["failures"]


def test_private_dataset_evidence_bundle_rejects_public_releaseable_artifacts(
    tmp_path: Path,
) -> None:
    curation_path = _write_curation(tmp_path)
    _write_complete_evidence_bundle(tmp_path)
    path = tmp_path / "private/reports/dataset_curation/license_review.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["public_release_allowed"] = True
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    result = verify_private_dataset_evidence_bundle(
        curation_path,
        evidence_root=tmp_path,
    )

    assert result["accepted"] is False
    assert (
        "Private dataset evidence license_review must not be public-releaseable."
        in result["failures"]
    )


def test_private_dataset_evidence_bundle_rejects_missing_record_fields(
    tmp_path: Path,
) -> None:
    curation_path = _write_curation(tmp_path)
    _write_complete_evidence_bundle(tmp_path)
    path = tmp_path / "private/reports/dataset_curation/provenance_manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    del payload["evidence_records"][0]["license_review_id"]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    result = verify_private_dataset_evidence_bundle(
        curation_path,
        evidence_root=tmp_path,
    )

    assert result["accepted"] is False
    assert (
        "Private dataset evidence provenance_tracking record 0 is missing "
        "required field: license_review_id."
    ) in result["failures"]


def test_private_dataset_evidence_bundle_cli_round_trip(tmp_path: Path) -> None:
    curation_path = _write_curation(tmp_path)
    _write_complete_evidence_bundle(tmp_path)

    result = CliRunner().invoke(
        app,
        [
            "private-dataset-evidence-verify",
            "--curation",
            str(curation_path),
            "--evidence-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert '"accepted": true' in result.output
    assert '"training_eligible": true' in result.output


def _write_curation(root: Path) -> Path:
    path = root / "docs/private_dataset_curation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(build_private_dataset_curation(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _write_complete_evidence_bundle(root: Path) -> None:
    curation = build_private_dataset_curation()
    for control, contract in curation["evidence_contracts"].items():
        path = root / contract["artifact_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                _evidence_payload(control, contract),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


def _evidence_payload(
    control: str,
    contract: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": contract["schema_version"],
        "control": control,
        "accepted": True,
        "public_release_allowed": False,
        "contains_private_rows": False,
        "evidence_records": [
            {
                field: _sample_value(field)
                for field in contract["required_fields"]
            }
        ],
    }


def _sample_value(field: str) -> object:
    if field in {
        "accepted",
        "allowed_private_training",
    }:
        return True
    if field in {
        "exact_hash_groups",
        "normalized_hash_groups",
        "near_duplicate_clusters",
        "restrictions",
        "remaining_findings",
    }:
        return []
    if field.endswith("_count") or field == "deduplicated_row_count":
        return 0
    if field == "similarity_threshold":
        return 0.92
    if field in {
        "license_text_sha256",
        "raw_content_sha256",
        "normalized_content_sha256",
        "transform_config_sha256",
        "removed_row_ids_sha256",
        "credential_scan_digest",
        "personal_data_scan_digest",
        "unlicensed_span_removal_digest",
        "private_path_scrub_digest",
        "public_reference_digest",
        "similarity_report_sha256",
    }:
        return "0" * 64
    if field == "private_storage_path":
        return "private/datasets/agades_pedagogical_rl/raw/example.jsonl"
    return f"example_{field}"
