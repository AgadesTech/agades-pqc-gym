from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.public_run_export import (
    verify_public_run_export,
    write_public_run_export,
)


def test_public_run_export_command_writes_prime_style_flat_export(
    tmp_path: Path,
) -> None:
    out = tmp_path / "run_export"

    result = CliRunner().invoke(app, ["public-run-export", "--out", str(out)])

    assert result.exit_code == 0, result.output
    assert f"public_run_export={out}" in result.output

    manifest_path = out / "manifest.json"
    runs_jsonl_path = out / "runs.jsonl"
    runs_csv_path = out / "runs.csv"
    checksums_path = out / "MANIFEST.sha256"
    assert manifest_path.is_file()
    assert runs_jsonl_path.is_file()
    assert runs_csv_path.is_file()
    assert checksums_path.is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "agades.pqc.public_run_export.v1"
    assert manifest["project"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "cli": "agades-pqc",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert manifest["summary"] == {
        "accepted_run_count": 59,
        "bundle_count": 18,
        "family_count": 7,
        "redacted_run_count": 0,
        "run_count": 59,
        "security_claim": False,
    }
    assert manifest["safety"] == {
        "arbitrary_code_execution": False,
        "contains_private_traces": False,
        "live_targeting": False,
        "publishes_private_candidates": False,
        "review_required_before_publish": True,
        "security_claim": False,
    }
    assert manifest["sources"]["prime_intellect"] == {
        "autonomous_speedrunning_reference": (
            "https://github.com/PrimeIntellect-ai/"
            "experiments-autonomous-speedrunning"
        ),
        "quickstart": "https://app.primeintellect.ai/dashboard/home/quickstart",
    }
    assert manifest["artifacts"] == {
        "checksums": "MANIFEST.sha256",
        "manifest": "manifest.json",
        "runs_csv": "runs.csv",
        "runs_jsonl": "runs.jsonl",
    }
    assert len(manifest["bundles"]) == 18

    runs = [
        json.loads(line)
        for line in runs_jsonl_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(runs) == 59
    assert runs == sorted(runs, key=lambda run: run["export_id"])
    first = runs[0]
    assert first == {
        "accepted": True,
        "attack_plan_id": (
            "toy_classic_mceliece_support_syndrome_19_10_w2_decode_seed"
        ),
        "attack_type": "decoding_fixture_check",
        "bundle_id": "code_based_toy_classic_mceliece_v0",
        "candidate_id": (
            "toy_classic_mceliece_support_syndrome_19_10_w2_decode_seed-0"
        ),
        "combined_score": -11.3742,
        "estimated_memory_bits": 5.1293,
        "estimated_time_bits": 7.4919,
        "estimator_name": (
            "toy-code-based-classic-mceliece-support-syndrome-estimator"
        ),
        "evaluation_status": "ok",
        "export_id": (
            "code_based_toy_classic_mceliece_v0:"
            "toy_classic_mceliece_support_syndrome_19_10_w2_decode_seed-0"
        ),
        "generation": 0,
        "public_release_ok": True,
        "redacted": False,
        "run_id": "code_based_toy_classic_mceliece",
        "source_trace": (
            "examples/public_runs/code_based_toy_classic_mceliece_v0/"
            "trace_public.jsonl"
        ),
        "target_family": "CODE_BASED",
        "trace_id": first["trace_id"],
    }
    assert all("attack_plan" not in run for run in runs)
    assert all("raw_output" not in json.dumps(run) for run in runs)
    assert all("private" not in json.dumps(run).lower() for run in runs)
    assert {run["target_family"] for run in runs} == {
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "LWE",
        "MLWE",
        "MULTIVARIATE",
    }

    with runs_csv_path.open(newline="", encoding="utf-8") as csv_file:
        csv_rows = list(csv.DictReader(csv_file))
    assert len(csv_rows) == len(runs)
    assert csv_rows[0]["export_id"] == first["export_id"]
    assert csv_rows[0]["combined_score"] == str(first["combined_score"])

    checksums = checksums_path.read_text(encoding="utf-8")
    for filename in ("manifest.json", "runs.jsonl", "runs.csv"):
        digest = hashlib.sha256((out / filename).read_bytes()).hexdigest()
        assert f"{digest}  {filename}" in checksums


def test_public_run_export_verify_accepts_checked_in_export() -> None:
    verification = verify_public_run_export(Path("public/run_export"))

    assert verification == {
        "schema_version": "agades.pqc.public_run_export_verification.v1",
        "accepted": True,
        "export_dir": "public/run_export",
        "summary": {
            "bundle_count": 18,
            "failure_count": 0,
            "run_count": 59,
        },
        "failures": [],
    }


def test_public_run_export_verify_rejects_safety_drift(tmp_path: Path) -> None:
    out = tmp_path / "run_export"
    write_public_run_export(out)
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["safety"]["contains_private_traces"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    verification = verify_public_run_export(out)

    assert verification["accepted"] is False
    assert "Public run export is not in sync." in verification["failures"]
    assert "Public run export may expose private traces." in verification["failures"]


def test_public_run_export_verify_command_accepts_checked_in_export() -> None:
    result = CliRunner().invoke(
        app,
        ["public-run-export-verify", "--export", "public/run_export"],
    )

    assert result.exit_code == 0, result.output
    verification = json.loads(result.output)
    assert verification["accepted"] is True
    assert verification["summary"] == {
        "bundle_count": 18,
        "failure_count": 0,
        "run_count": 59,
    }
