from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.private_training_readiness import (
    PRIVATE_TRAINING_READINESS_VERIFICATION_SCHEMA,
    build_private_training_readiness,
    verify_private_training_readiness,
    write_private_training_readiness,
)

READINESS_PATH = Path("docs/private_training_readiness.json")


def test_private_training_readiness_blocks_unreviewed_private_launch(
    tmp_path: Path,
) -> None:
    out = tmp_path / "private_training_readiness.json"

    payload = write_private_training_readiness(out)

    assert payload == build_private_training_readiness()
    assert json.loads(out.read_text(encoding="utf-8")) == payload
    assert payload["schema_version"] == "agades.pqc.private_training_readiness.v1"
    assert payload["classification"] == {
        "public_artifact_only": True,
        "contains_private_dataset_rows": False,
        "contains_private_trace_rows": False,
        "contains_secret_values": False,
        "contains_private_model_paths": False,
        "records_secret_presence": False,
    }
    assert payload["launch_status"] == {
        "ready": False,
        "state": "blocked",
        "reason": (
            "blocked_until_private_model_dataset_reviews_and_private_"
            "infrastructure_are_verified"
        ),
    }
    assert {gate["status"] for gate in payload["readiness_gates"]} == {"blocked"}
    assert all(gate["blocks_launch"] is True for gate in payload["readiness_gates"])
    assert payload["required_inputs"]["qwen"]["base_model_env"] == (
        "AGADES_QWEN_BASE_MODEL"
    )
    assert payload["required_inputs"]["qwen"]["direct_gguf_training_allowed"] is False
    assert payload["required_inputs"]["prime_intellect"]["api_key_env"] == (
        "PRIME_API_KEY"
    )
    assert payload["credential_policy"]["secret_values_recorded"] is False
    assert payload["credential_policy"]["secret_presence_recorded"] is False
    assert payload["publication_boundary"]["publish_finetuned_qwen_publicly"] is False
    assert payload["linked_artifacts"]["private_training_manifest"]["path"] == (
        "docs/private_training_config_manifest.json"
    )


def test_private_training_readiness_verify_accepts_committed_artifact() -> None:
    result = verify_private_training_readiness(READINESS_PATH)

    assert result == {
        "schema_version": PRIVATE_TRAINING_READINESS_VERIFICATION_SCHEMA,
        "readiness_path": READINESS_PATH.as_posix(),
        "accepted": True,
        "summary": {
            "ready": False,
            "blocked_gates": 11,
            "linked_artifacts": 14,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_private_training_readiness_rejects_ready_claim_without_reviews(
    tmp_path: Path,
) -> None:
    out = tmp_path / "private_training_readiness.json"
    payload = write_private_training_readiness(out)
    payload["launch_status"]["ready"] = True
    payload["launch_status"]["state"] = "ready"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    result = verify_private_training_readiness(out)

    assert result["accepted"] is False
    assert (
        "Private training readiness must keep launch_status.ready false "
        "until private reviews are complete."
    ) in result["failures"]


def test_private_training_readiness_rejects_embedded_secret_values(
    tmp_path: Path,
) -> None:
    out = tmp_path / "private_training_readiness.json"
    payload = write_private_training_readiness(out)
    payload["required_inputs"]["prime_intellect"]["leaked_example"] = (
        "hf_" + "abcdefghijklmnopqrstuvwxyz123456"
    )
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    result = verify_private_training_readiness(out)

    assert result["accepted"] is False
    assert "Private training readiness artifact contains a secret-looking value." in (
        result["failures"]
    )


def test_private_training_readiness_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "private_training_readiness.json"

    write_result = CliRunner().invoke(
        app,
        ["private-training-readiness", "--out", str(out)],
    )
    verify_result = CliRunner().invoke(
        app,
        ["private-training-readiness-verify", "--readiness", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"private_training_readiness={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
