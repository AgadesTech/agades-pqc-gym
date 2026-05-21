from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

import agades_pqc_gym.formal.lean_build as lean_build
from agades_pqc_gym.cli import app


def test_formal_lean_build_smoke_report_binds_successful_lake_build(
    monkeypatch,
) -> None:
    observed: dict[str, object] = {}

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        capture_output: bool,
        text: bool,
        timeout: int,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["cwd"] = cwd
        observed["capture_output"] = capture_output
        observed["text"] = text
        observed["timeout"] = timeout
        observed["check"] = check
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="Build completed successfully.\n",
            stderr="",
        )

    monkeypatch.setattr(lean_build.subprocess, "run", fake_run)

    report = lean_build.run_formal_lean_build_smoke(timeout_seconds=15)

    assert observed == {
        "command": ["lake", "build"],
        "cwd": Path("formal/lean").resolve(),
        "capture_output": True,
        "text": True,
        "timeout": 15,
        "check": False,
    }
    assert report["schema_version"] == "agades.pqc.formal.lean_build_smoke.v1"
    assert report["accepted"] is True
    assert report["scope"] == {
        "compiles_lean_sources": True,
        "executes_cryptographic_estimators": False,
        "publishes_artifacts": False,
        "security_claim_allowed": False,
        "cryptographic_soundness_review_required": True,
    }
    assert report["lean_project"] == {
        "root": "formal/lean",
        "toolchain": "formal/lean/lean-toolchain",
        "lakefile": "formal/lean/lakefile.lean",
        "lake_manifest": "formal/lean/lake-manifest.json",
        "entry_module": "formal/lean/AgadesPQC.lean",
    }
    assert report["build"] == {
        "command": ["lake", "build"],
        "cwd": "formal/lean",
        "return_code": 0,
        "stdout_sha256": lean_build._text_sha256("Build completed successfully.\n"),
        "stderr_sha256": lean_build._text_sha256(""),
        "stdout_tail": "Build completed successfully.",
        "stderr_tail": "",
        "timed_out": False,
        "environment_exported": False,
    }
    assert report["formal_backend_manifest"]["path"] == (
        "docs/formal_lean_backend.json"
    )
    assert report["formal_backend_manifest"]["schema_version"] == (
        "agades.pqc.formal.lean_backend.v1"
    )
    assert len(report["formal_backend_manifest"]["sha256"]) == 64
    assert report["formal_backend_manifest"]["placeholder_failures"] == 0
    assert report["summary"] == {
        "accepted": True,
        "source_modules": 14,
        "theorem_declarations": report["summary"]["theorem_declarations"],
        "placeholder_failures": 0,
        "ci_lean_build_gate": True,
        "security_claim_allowed": False,
    }
    assert report["report_sha256"] == lean_build._report_sha256(report)


def test_formal_lean_build_smoke_report_records_failed_build(monkeypatch) -> None:
    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        capture_output: bool,
        text: bool,
        timeout: int,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=1,
            stdout="",
            stderr="unknown module AgadesPQC\n",
        )

    monkeypatch.setattr(lean_build.subprocess, "run", fake_run)

    report = lean_build.run_formal_lean_build_smoke()

    assert report["accepted"] is False
    assert report["build"]["return_code"] == 1
    assert report["build"]["stderr_tail"] == "unknown module AgadesPQC"
    assert report["summary"]["accepted"] is False
    assert report["scope"]["security_claim_allowed"] is False


def test_formal_lean_build_smoke_report_records_timeout(monkeypatch) -> None:
    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        capture_output: bool,
        text: bool,
        timeout: int,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(
            cmd=command,
            timeout=timeout,
            output="",
            stderr="still building\n",
        )

    monkeypatch.setattr(lean_build.subprocess, "run", fake_run)

    report = lean_build.run_formal_lean_build_smoke(timeout_seconds=1)

    assert report["accepted"] is False
    assert report["build"]["return_code"] is None
    assert report["build"]["timed_out"] is True
    assert report["build"]["stderr_tail"] == "still building"


def test_formal_lean_build_smoke_verify_accepts_written_report(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        lean_build.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="Build completed successfully.\n",
            stderr="",
        ),
    )
    out = tmp_path / "formal_lean_build_smoke.json"

    lean_build.write_formal_lean_build_smoke(out)
    verification = lean_build.verify_formal_lean_build_smoke(out)

    assert verification == {
        "schema_version": "agades.pqc.formal.lean_build_smoke_verification.v1",
        "report_path": out.as_posix(),
        "accepted": True,
        "summary": {
            "accepted": True,
            "source_modules": 14,
            "theorem_declarations": verification["summary"][
                "theorem_declarations"
            ],
            "placeholder_failures": 0,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_formal_lean_build_smoke_verify_rejects_drift(tmp_path: Path) -> None:
    report = lean_build.run_formal_lean_build_smoke(
        command=[sys.executable, "-c", "print('ok')"],
    )
    report["scope"]["security_claim_allowed"] = True
    report["formal_backend_manifest"]["sha256"] = "0" * 64
    report_path = tmp_path / "formal_lean_build_smoke.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    verification = lean_build.verify_formal_lean_build_smoke(report_path)

    assert verification["accepted"] is False
    assert "Formal Lean build smoke scope drifted." in verification["failures"]
    assert "Formal Lean build smoke backend manifest hash drifted." in (
        verification["failures"]
    )
    assert "Formal Lean build smoke report hash does not match." in (
        verification["failures"]
    )


def test_formal_lean_build_smoke_cli_round_trip(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        lean_build.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="Build completed successfully.\n",
            stderr="",
        ),
    )
    out = tmp_path / "formal_lean_build_smoke.json"
    runner = CliRunner()

    write_result = runner.invoke(
        app,
        ["formal-lean-build-smoke", "--out", str(out)],
    )
    verify_result = runner.invoke(
        app,
        ["formal-lean-build-smoke-verify", "--report", str(out)],
    )

    assert write_result.exit_code == 0, write_result.output
    assert f"formal_lean_build_smoke={out}" in write_result.output
    assert verify_result.exit_code == 0, verify_result.output
    assert '"accepted": true' in verify_result.output
