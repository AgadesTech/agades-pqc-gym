from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.formal.lean_backend import (
    FORMAL_LEAN_BACKEND_VERIFICATION_SCHEMA,
    build_formal_lean_backend,
    verify_formal_lean_backend,
    write_formal_lean_backend,
)

BACKEND_PATH = Path("docs/formal_lean_backend.json")
CI_PATH = Path(".github/workflows/ci.yml")


def test_formal_lean_backend_manifest_binds_sources_and_ci(
    tmp_path: Path,
) -> None:
    out = tmp_path / "formal_lean_backend.json"

    manifest = write_formal_lean_backend(out)

    assert manifest == build_formal_lean_backend()
    assert json.loads(out.read_text(encoding="utf-8")) == manifest
    assert manifest["schema_version"] == "agades.pqc.formal.lean_backend.v1"
    assert manifest["backend"] == {
        "primary": "lean4",
        "library": "mathlib",
        "smt_assist": "z3_optional_finite_decidable_obligations_only",
    }
    lean_project = manifest["lean_project"]
    assert {
        key: lean_project[key]
        for key in (
            "root",
            "toolchain",
            "toolchain_value",
            "lakefile",
            "lake_manifest",
            "entry_module",
            "build_command",
        )
    } == {
        "root": "formal/lean",
        "toolchain": "formal/lean/lean-toolchain",
        "toolchain_value": "leanprover/lean4:v4.12.0",
        "lakefile": "formal/lean/lakefile.lean",
        "lake_manifest": "formal/lean/lake-manifest.json",
        "entry_module": "formal/lean/AgadesPQC.lean",
        "build_command": "lake build",
    }
    for hash_key in (
        "toolchain_sha256",
        "lakefile_sha256",
        "lake_manifest_sha256",
    ):
        assert len(lean_project[hash_key]) == 64
    packages = {
        package["name"]: package
        for package in lean_project["lake_manifest_packages"]
    }
    assert set(packages) == {
        "batteries",
        "Qq",
        "aesop",
        "proofwidgets",
        "Cli",
        "importGraph",
        "LeanSearchClient",
        "mathlib",
    }
    assert packages["mathlib"]["input_rev"] == "v4.12.0"
    assert packages["mathlib"]["url"] == (
        "https://github.com/leanprover-community/mathlib4.git"
    )
    assert manifest["ci"] == {
        "workflow_path": ".github/workflows/ci.yml",
        "job": "test",
        "step_name": "Build Lean formal backend",
        "uses": "leanprover/lean-action@v1",
        "lake_package_directory": "formal/lean",
        "build": True,
        "test": False,
        "lint": False,
    }
    assert manifest["placeholder_scan"] == {
        "contains_sorry": False,
        "contains_admit": False,
        "contains_axiom": False,
    }
    assert manifest["summary"]["source_modules"] == 11
    assert manifest["summary"]["theorem_declarations"] >= 20
    assert manifest["summary"]["ci_lean_build_gate"] is True
    assert manifest["summary"]["placeholder_failures"] == 0

    source_paths = {source["path"] for source in manifest["lean_sources"]}
    assert "formal/lean/AgadesPQC.lean" in source_paths
    assert "formal/lean/AgadesPQC/Evaluator.lean" in source_paths
    for source in manifest["lean_sources"]:
        path = Path(source["path"])
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]

    theorem_names = {
        theorem
        for source in manifest["lean_sources"]
        for theorem in source["theorems"]
    }
    assert "AgadesPQC.Evaluator.no_security_claim" in theorem_names
    assert "AgadesPQC.Lattice.Target.parameters_positive" in theorem_names


def test_ci_workflow_runs_lean_action_against_formal_backend() -> None:
    workflow = yaml.safe_load(CI_PATH.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["test"]["steps"]
    matching_steps = [
        step
        for step in steps
        if step.get("name") == "Build Lean formal backend"
    ]

    assert len(matching_steps) == 1
    step = matching_steps[0]
    assert step["uses"] == "leanprover/lean-action@v1"
    assert step["with"] == {
        "lake-package-directory": "formal/lean",
        "build": True,
        "test": False,
        "lint": False,
        "auto-config": False,
        "use-mathlib-cache": True,
    }


def test_committed_formal_lean_backend_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "formal_lean_backend.json"

    write_formal_lean_backend(generated)

    assert BACKEND_PATH.read_bytes() == generated.read_bytes()


def test_formal_lean_backend_verify_accepts_committed_artifact() -> None:
    result = verify_formal_lean_backend(BACKEND_PATH)

    assert result == {
        "schema_version": FORMAL_LEAN_BACKEND_VERIFICATION_SCHEMA,
        "backend_path": BACKEND_PATH.as_posix(),
        "accepted": True,
        "summary": {
            "source_modules": 11,
            "theorem_declarations": result["summary"]["theorem_declarations"],
            "ci_lean_build_gate": True,
            "placeholder_failures": 0,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_formal_lean_backend_verify_rejects_missing_ci_gate(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "formal_lean_backend.json"
    workflow_path = tmp_path / "ci.yml"
    manifest = build_formal_lean_backend()
    manifest["ci"]["step_name"] = "missing"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    workflow_path.write_text("name: CI\njobs:\n  test:\n    steps: []\n")

    result = verify_formal_lean_backend(
        manifest_path,
        workflow_path=workflow_path,
    )

    assert result["accepted"] is False
    assert "Lean backend CI gate is missing or misconfigured." in result["failures"]


def test_formal_lean_backend_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "formal_lean_backend.json"

    write_result = CliRunner().invoke(
        app,
        ["formal-lean-backend", "--out", str(out)],
    )
    verify_result = CliRunner().invoke(
        app,
        ["formal-lean-backend-verify", "--backend", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"formal_lean_backend={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
