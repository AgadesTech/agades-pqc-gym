from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.huggingface_space_smoke import (
    build_huggingface_space_smoke_report,
    verify_huggingface_space_smoke_report,
    write_huggingface_space_smoke_report,
)


def test_huggingface_space_smoke_report_exercises_public_demo(
    tmp_path: Path,
) -> None:
    out = tmp_path / "hf_space_smoke.json"

    report = write_huggingface_space_smoke_report(out)

    assert report == build_huggingface_space_smoke_report()
    assert json.loads(out.read_text(encoding="utf-8")) == report
    assert report["schema_version"] == "agades.pqc.hf_space_smoke.v1"
    assert report["accepted"] is True
    assert report["app"] == {
        "app_path": "hf/app.py",
        "imports_without_gradio": True,
        "uses_rl_environment": True,
        "uses_shared_verifier": True,
    }
    assert report["examples"]["default_label"] == "LWE / lattice_primal_usvp_toy_v1"
    assert report["examples"]["example_count"] == 79
    assert report["examples"]["default_is_selectable"] is True
    assert report["evaluation"] == {
        "accepted": True,
        "combined_score": -80.9096,
        "evaluation_status": "ok",
        "summary_contains_not_security_claim": True,
        "target_family": "LWE",
        "security_claim": False,
    }
    assert report["agent_environment"] == {
        "observation_schema": "agades.pqc.rl.observation.v1",
        "reward_report_schema": "agades.pqc.rl.reward_report.v1",
        "rollout_trace_schema": "agades.pqc.rl.rollout_trace.v1",
        "has_prompt": True,
        "reward": 1.0,
        "task_match": 1.0,
        "trace_public_release_ok": True,
        "private_fields_present": False,
        "claims_pqc_break": False,
    }
    assert report["safety"] == {
        "arbitrary_code_execution": False,
        "contains_private_traces": False,
        "live_targeting": False,
        "publishes_private_candidates": False,
        "security_claim": False,
    }
    assert report["release_gates"] == [
        "uv run pytest tests/test_huggingface_space_smoke.py -q",
        "uv run agades-pqc hf-space-smoke --out reports/hf_space_smoke.json",
        "uv run agades-pqc hf-space-smoke-verify --report "
        "reports/hf_space_smoke.json",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]
    assert report["failures"] == []


def test_committed_huggingface_space_smoke_report_is_in_sync(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "hf_space_smoke.json"
    committed = Path("reports/hf_space_smoke.json")

    write_huggingface_space_smoke_report(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_huggingface_space_smoke_verify_accepts_committed_report() -> None:
    result = verify_huggingface_space_smoke_report(Path("reports/hf_space_smoke.json"))

    assert result == {
        "schema_version": "agades.pqc.hf_space_smoke_verification.v1",
        "report_path": "reports/hf_space_smoke.json",
        "accepted": True,
        "summary": {
            "default_label": "LWE / lattice_primal_usvp_toy_v1",
            "example_count": 79,
            "failure_count": 0,
            "imports_without_gradio": True,
            "summary_contains_not_security_claim": True,
            "uses_rl_environment": True,
            "uses_shared_verifier": True,
        },
        "failures": [],
    }


def test_huggingface_space_smoke_verify_rejects_stale_report(
    tmp_path: Path,
) -> None:
    out = tmp_path / "hf_space_smoke.json"
    report = build_huggingface_space_smoke_report()
    report["evaluation"]["security_claim"] = True
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    result = verify_huggingface_space_smoke_report(out)

    assert result["accepted"] is False
    assert "Hugging Face Space smoke report is not in sync." in result["failures"]
    assert "Hugging Face Space smoke report advertises a security claim." in result[
        "failures"
    ]


def test_huggingface_space_smoke_cli_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "hf_space_smoke.json"

    result = CliRunner().invoke(app, ["hf-space-smoke", "--out", str(out)])

    assert result.exit_code == 0
    assert f"hf_space_smoke={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["accepted"] is True


def test_huggingface_space_smoke_verify_cli_accepts_current_report() -> None:
    result = CliRunner().invoke(
        app,
        ["hf-space-smoke-verify", "--report", "reports/hf_space_smoke.json"],
    )

    assert result.exit_code == 0
    assert "agades.pqc.hf_space_smoke_verification.v1" in result.output
    assert '"accepted": true' in result.output
