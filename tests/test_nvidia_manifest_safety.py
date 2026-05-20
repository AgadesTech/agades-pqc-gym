from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.nvidia_manifest_safety import (
    build_nvidia_manifest_safety_report,
    verify_nvidia_manifest_safety_report,
    write_nvidia_manifest_safety_report,
)


def test_nvidia_manifest_safety_report_summarizes_accelerator_boundaries(
    tmp_path: Path,
) -> None:
    out = tmp_path / "nvidia_manifest_safety.json"

    report = write_nvidia_manifest_safety_report(out)

    assert report == build_nvidia_manifest_safety_report()
    assert json.loads(out.read_text(encoding="utf-8")) == report
    assert report["schema_version"] == "agades.pqc.nvidia_manifest_safety.v1"
    assert report["accepted"] is True
    assert report["manifest"] == {
        "in_sync": True,
        "manifest_path": "nvidia/accelerator_manifest.json",
        "manifest_schema_version": "agades.pqc.nvidia_accelerator.v1",
        "project_name": "Agades PQC Gym",
    }
    assert report["runtime"] == {
        "current_gpu_required": False,
        "current_public_backend": "deterministic-python-verifier",
        "gpu_status": "future_acceleration_surface",
    }
    assert report["workloads"] == {
        "all_current_workloads_cpu": True,
        "cpu_workload_count": 26,
        "current_gpu_required_workload_count": 0,
        "current_workload_count": 26,
        "gpu_future_workload_count": 1,
        "no_current_workload_requires_gpu": True,
        "public_run_bundle_count": 18,
        "reserved_future_gpu_required_workload_count": 1,
        "reserved_future_workload_count": 1,
        "total_workload_count": 27,
        "workload_count": 27,
    }
    assert report["artifacts"] == {
        "artifact_count": 18,
        "publication_manifest": "docs/publication_manifest.json",
        "public_run_bundle_count": 18,
        "release_audit": "public/release_audit.json",
    }
    assert report["family_scope"] == {
        "family_count": 9,
        "non_lattice_toy_operator_security_claims": 0,
        "raw_mapping_redaction_covered": True,
        "report_redaction_records": 2,
        "review_required_before_claims": True,
        "typed_trace_redaction_covered": True,
    }
    assert report["safety"] == {
        "arbitrary_code_execution": False,
        "contains_private_traces": False,
        "live_targeting": False,
        "publishes_private_candidates": False,
        "security_claim": False,
    }
    assert report["release_gates"] == [
        "uv run pytest tests/test_nvidia_manifest_safety.py -q",
        "uv run agades-pqc nvidia-manifest --out "
        "nvidia/accelerator_manifest.json",
        "uv run agades-pqc nvidia-manifest-verify --manifest "
        "nvidia/accelerator_manifest.json",
        "uv run agades-pqc nvidia-manifest-safety --out "
        "reports/nvidia_manifest_safety.json",
        "uv run agades-pqc nvidia-manifest-safety-verify --report "
        "reports/nvidia_manifest_safety.json",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]
    assert report["failures"] == []


def test_committed_nvidia_manifest_safety_report_is_in_sync(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "nvidia_manifest_safety.json"
    committed = Path("reports/nvidia_manifest_safety.json")

    write_nvidia_manifest_safety_report(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_nvidia_manifest_safety_verify_accepts_committed_report() -> None:
    result = verify_nvidia_manifest_safety_report(
        Path("reports/nvidia_manifest_safety.json")
    )

    assert result == {
        "schema_version": "agades.pqc.nvidia_manifest_safety_verification.v1",
        "report_path": "reports/nvidia_manifest_safety.json",
        "accepted": True,
        "summary": {
            "all_current_workloads_cpu": True,
            "artifact_count": 18,
            "cpu_workload_count": 26,
            "current_gpu_required": False,
            "current_gpu_required_workload_count": 0,
            "current_workload_count": 26,
            "failure_count": 0,
            "gpu_future_workload_count": 1,
            "gpu_status": "future_acceleration_surface",
            "no_current_workload_requires_gpu": True,
            "public_run_bundle_count": 18,
            "reserved_future_gpu_required_workload_count": 1,
            "reserved_future_workload_count": 1,
            "security_claim": False,
            "workload_count": 27,
        },
        "failures": [],
    }


def test_nvidia_manifest_safety_verify_rejects_stale_report(
    tmp_path: Path,
) -> None:
    out = tmp_path / "nvidia_manifest_safety.json"
    report = build_nvidia_manifest_safety_report()
    report["safety"]["security_claim"] = True
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    result = verify_nvidia_manifest_safety_report(out)

    assert result["accepted"] is False
    assert "NVIDIA manifest safety report is not in sync." in result["failures"]
    assert "NVIDIA manifest safety report security_claim must be false." in result[
        "failures"
    ]


def test_nvidia_manifest_safety_cli_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "nvidia_manifest_safety.json"

    result = CliRunner().invoke(
        app,
        ["nvidia-manifest-safety", "--out", str(out)],
    )

    assert result.exit_code == 0
    assert f"nvidia_manifest_safety={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["accepted"] is True


def test_nvidia_manifest_safety_verify_cli_accepts_current_report() -> None:
    result = CliRunner().invoke(
        app,
        [
            "nvidia-manifest-safety-verify",
            "--report",
            "reports/nvidia_manifest_safety.json",
        ],
    )

    assert result.exit_code == 0
    assert "agades.pqc.nvidia_manifest_safety_verification.v1" in result.output
    assert '"accepted": true' in result.output
