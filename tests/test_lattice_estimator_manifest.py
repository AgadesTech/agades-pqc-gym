from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.lattice_estimator_manifest import (
    build_lattice_estimator_manifest,
    verify_lattice_estimator_manifest,
    write_lattice_estimator_manifest,
)

PINNED_COMMIT = "6019056011d10d7e9c30a0d5da2d2f729fbc2eec"


def test_lattice_estimator_manifest_pins_upstream_boundary(tmp_path: Path) -> None:
    out = tmp_path / "lattice_estimator_manifest.json"

    manifest = write_lattice_estimator_manifest(out)

    assert manifest == build_lattice_estimator_manifest()
    assert json.loads(out.read_text()) == manifest
    assert manifest["schema_version"] == "agades.pqc.lattice_estimator_manifest.v1"
    assert manifest["upstream"] == {
        "repository": "https://github.com/malb/lattice-estimator",
        "branch": "main",
        "observed_ref": "refs/heads/main",
        "pinned_commit": PINNED_COMMIT,
        "pinned_commit_url": (
            "https://github.com/malb/lattice-estimator/commit/"
            f"{PINNED_COMMIT}"
        ),
        "observed_at": "2026-05-16",
    }
    assert manifest["agades_boundary"]["reviewed_lwe_mappings"] == {
        "bounded_distance_decoding": "bdd",
        "bkw": "bkw",
        "dual_attack": "dual",
        "dual_hybrid": "dual_hybrid",
        "primal_usvp": "usvp",
    }
    assert manifest["agades_boundary"]["schema_only_lattice_families"] == [
        "NTRU",
        "SIS",
    ]
    assert manifest["agades_boundary"]["mlwe_status"] == "warning_gated_flattening"
    assert manifest["agades_boundary"]["pin_enforcement"] == {
        "runtime_required_commit": PINNED_COMMIT,
        "missing_commit_metadata": "error",
        "mismatched_commit": "error",
    }
    assert manifest["agades_boundary"]["source_checkout_backend"] == {
        "cli_option": "--estimator-source",
        "clean_tree_probe": "git status --porcelain",
        "clean_tree_verified_before_import": True,
        "commit_probe": "git rev-parse HEAD",
        "commit_verified_before_import": True,
        "dirty_checkout": "error_before_import",
        "entrypoint_verified_before_import": True,
        "mismatched_checkout_commit": "error_before_import",
        "mismatched_origin": "error_before_import",
        "origin_probe": "git remote get-url origin",
        "origin_verified_before_import": True,
        "scope": "private_lattice_estimator_baseline_runs",
    }
    assert manifest["agades_boundary"]["runtime_environment"] == {
        "ci_dependency": False,
        "missing_runtime_behavior": (
            "private_error_report_without_public_numeric_outputs"
        ),
        "private_preflight_command": (
            "uv run agades-pqc lattice-estimator-runtime-preflight "
            "--out private/reports/lattice_estimator_runtime_preflight.json "
            "--policy docs/private_run_policy.json"
        ),
        "private_preflight_verify_command": (
            "uv run agades-pqc lattice-estimator-runtime-preflight-verify "
            "--preflight private/reports/lattice_estimator_runtime_preflight.json"
        ),
        "private_baseline_sage_worker_command": (
            "uv run agades-pqc lattice-estimator-baseline-run "
            "--contracts docs/lattice_estimator_baseline_contracts.json "
            "--contracts-root . "
            "--out private/reports/lattice_estimator_baseline_run.json "
            "--policy docs/private_run_policy.json "
            "--estimator-source /path/to/lattice-estimator "
            "--sage-command sage"
        ),
        "private_baseline_sage_python_worker_command": (
            "uv run agades-pqc lattice-estimator-baseline-run "
            "--contracts docs/lattice_estimator_baseline_contracts.json "
            "--contracts-root . "
            "--out private/reports/lattice_estimator_baseline_run.json "
            "--policy docs/private_run_policy.json "
            "--estimator-source /path/to/lattice-estimator "
            "--sage-python-command '/path/to/python-with-sage-all'"
        ),
        "private_baseline_verify_command": (
            "uv run agades-pqc lattice-estimator-baseline-run-verify "
            "--report private/reports/lattice_estimator_baseline_run.json "
            "--contracts-root ."
        ),
        "private_baseline_review_packet_command": (
            "uv run agades-pqc lattice-estimator-baseline-review-packet "
            "--baseline-report private/reports/lattice_estimator_baseline_run.json "
            "--out private/reports/lattice_estimator_baseline_review_packet.json "
            "--policy docs/private_run_policy.json "
            "--contracts-root ."
        ),
        "private_baseline_review_packet_verify_command": (
            "uv run agades-pqc lattice-estimator-baseline-review-packet-verify "
            "--packet private/reports/lattice_estimator_baseline_review_packet.json "
            "--baseline-report private/reports/lattice_estimator_baseline_run.json "
            "--contracts-root ."
        ),
        "required_for_numeric_baseline": True,
        "sage_command": "sage",
        "sage_python_command_default": "sage -python",
        "sage_python_command_option": "--sage-python-command",
        "sage_python_probe": "<sage-python-command> -c 'import sage.all'",
        "sage_worker": "private_subprocess_after_checkout_preflight",
    }
    assert manifest["safety"] == {
        "arbitrary_code_execution": False,
        "live_targeting": False,
        "security_claim": False,
        "use_for_public_security_claims": False,
        "review_required_before_security_claims": True,
    }
    assert manifest["release_gates"] == [
        "uv run pytest tests/test_lattice_estimator_manifest.py -q",
        "uv run agades-pqc lattice-estimator-manifest --out "
        "docs/lattice_estimator_manifest.json",
        "uv run agades-pqc lattice-estimator-manifest-verify --manifest "
        "docs/lattice_estimator_manifest.json",
        "uv run agades-pqc family-support-verify --matrix "
        "docs/family_support_matrix.json",
        "uv run agades-pqc family-operator-catalog-verify --catalog "
        "docs/family_operator_catalog.json",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]


def test_committed_lattice_estimator_manifest_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "lattice_estimator_manifest.json"
    committed = Path("docs/lattice_estimator_manifest.json")

    write_lattice_estimator_manifest(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_lattice_estimator_manifest_verify_accepts_committed_manifest() -> None:
    result = verify_lattice_estimator_manifest(
        Path("docs/lattice_estimator_manifest.json")
    )

    assert result == {
        "schema_version": "agades.pqc.lattice_estimator_manifest_verification.v1",
        "manifest_path": "docs/lattice_estimator_manifest.json",
        "accepted": True,
        "summary": {
            "covered_algorithm_keys": ["bdd", "bkw", "dual", "dual_hybrid", "usvp"],
            "covered_attack_types": [
                "bounded_distance_decoding",
                "bkw",
                "dual_attack",
                "dual_hybrid",
                "primal_usvp",
            ],
            "failure_count": 0,
            "mapping_count": 5,
            "pinned_commit": PINNED_COMMIT,
            "release_gate_count": 7,
            "runtime_environment": True,
            "schema_only_lattice_families": ["NTRU", "SIS"],
            "security_claim": False,
            "source_checkout_backend": True,
        },
        "failures": [],
    }


def test_lattice_estimator_manifest_verify_rejects_pin_and_boundary_drift(
    tmp_path: Path,
) -> None:
    out = tmp_path / "lattice_estimator_manifest.json"
    manifest = build_lattice_estimator_manifest()
    manifest["upstream"]["pinned_commit"] = "0" * 40
    manifest["agades_boundary"]["schema_only_lattice_families"] = ["NTRU"]
    manifest["agades_boundary"]["source_checkout_backend"][
        "clean_tree_verified_before_import"
    ] = False
    manifest["agades_boundary"].pop("runtime_environment")
    manifest["safety"]["security_claim"] = True
    manifest["release_gates"] = [
        gate
        for gate in manifest["release_gates"]
        if "lattice-estimator-manifest-verify" not in gate
    ]
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_lattice_estimator_manifest(out)

    assert result["accepted"] is False
    assert "Lattice Estimator manifest is not in sync." in result["failures"]
    assert (
        "Lattice Estimator pinned commit differs from generator."
        in result["failures"]
    )
    assert (
        "Lattice Estimator manifest must keep NTRU/SIS schema-only."
        in result["failures"]
    )
    assert (
        "Lattice Estimator local checkout backend must verify checkout "
        "readiness before import."
        in result["failures"]
    )
    assert (
        "Lattice Estimator manifest must document the Sage runtime preflight."
        in result["failures"]
    )
    assert "Lattice Estimator manifest advertises a security claim." in result[
        "failures"
    ]
    assert any(
        "lattice-estimator-manifest-verify" in failure
        for failure in result["failures"]
    )


def test_lattice_estimator_manifest_verify_rejects_empty_json_object(
    tmp_path: Path,
) -> None:
    out = tmp_path / "lattice_estimator_manifest.json"
    out.write_text("{}\n", encoding="utf-8")

    result = verify_lattice_estimator_manifest(out)

    assert result["accepted"] is False
    assert "Lattice Estimator manifest is not in sync." in result["failures"]
    assert "Lattice Estimator manifest project must be an object." in result[
        "failures"
    ]


def test_lattice_estimator_manifest_cli_writes_manifest(tmp_path: Path) -> None:
    out = tmp_path / "lattice_estimator_manifest.json"

    result = CliRunner().invoke(
        app,
        ["lattice-estimator-manifest", "--out", str(out)],
    )

    assert result.exit_code == 0
    assert f"lattice_estimator_manifest={out}" in result.output
    assert json.loads(out.read_text())["upstream"]["pinned_commit"] == PINNED_COMMIT


def test_lattice_estimator_manifest_verify_cli_accepts_current_manifest() -> None:
    result = CliRunner().invoke(
        app,
        [
            "lattice-estimator-manifest-verify",
            "--manifest",
            "docs/lattice_estimator_manifest.json",
        ],
    )

    assert result.exit_code == 0
    assert "agades.pqc.lattice_estimator_manifest_verification.v1" in result.output
    assert '"accepted": true' in result.output
