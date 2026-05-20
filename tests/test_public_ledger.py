from __future__ import annotations

import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.traces.public_ledger import build_public_run_ledger
from agades_pqc_gym.traces.schema import TraceRecord


def test_public_run_ledger_summarizes_lattice_trace(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    public_trace_path = tmp_path / "trace_public.jsonl"
    runner = CliRunner()

    benchmark_result = runner.invoke(
        app,
        ["benchmark", "benchmarks/lattice_toy_lwe", "--out", str(trace_path)],
    )
    assert benchmark_result.exit_code == 0
    export_result = runner.invoke(
        app,
        ["export-public", str(trace_path), "--out", str(public_trace_path)],
    )
    assert export_result.exit_code == 0

    ledger = build_public_run_ledger(trace_path)

    assert ledger["schema_version"] == "agades.pqc.public_run_ledger.v1"
    assert ledger["source_trace"]["public_sha256"] == hashlib.sha256(
        public_trace_path.read_bytes()
    ).hexdigest()
    assert ledger["summary"]["total_records"] == 2
    assert ledger["summary"]["accepted_records"] == 2
    assert ledger["summary"]["redacted_records"] == 0
    assert ledger["summary"]["by_family"] == {"LWE": 2}
    assert ledger["summary"]["by_evaluation_status"] == {"ok": 2}
    assert ledger["summary"]["by_estimator"] == {"mock-lattice-estimator": 2}
    assert len(ledger["entries"]) == 2
    assert "attack_plan" not in ledger["entries"][0]
    assert ledger["safety"]["arbitrary_code_execution"] is False
    assert ledger["safety"]["security_claim"] is False


def test_public_run_ledger_keeps_private_records_minimal(tmp_path: Path) -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    record = TraceRecord.from_evaluation(
        run_id="private-run",
        candidate_id="candidate-1",
        parent_id=None,
        generation=3,
        mutation_summary="private prompt mutation",
        attack_plan=plan,
        evaluation={
            "valid": True,
            "combined_score": -90.0,
            "evaluation_status": "ok",
            "estimator_name": "mock-lattice-estimator",
            "raw_output": {"private_recipe": "do not publish"},
            "warnings": ["private warning"],
        },
        accepted=True,
        public_release_ok=False,
        redaction_reason="contains private prompt/evolution trace",
    )
    trace_path = tmp_path / "private_trace.jsonl"
    trace_path.write_text(record.model_dump_json() + "\n", encoding="utf-8")

    ledger = build_public_run_ledger(trace_path)

    assert ledger["summary"]["total_records"] == 1
    assert ledger["summary"]["redacted_records"] == 1
    assert ledger["summary"]["by_family"] == {"REDACTED": 1}
    public_trace_id = ledger["entries"][0]["trace_id"]
    assert public_trace_id != record.trace_id
    assert ledger["entries"] == [
        {
            "trace_id": public_trace_id,
            "run_id": "private-run",
            "candidate_id": "candidate-1",
            "parent_id": None,
            "generation": 3,
            "attack_plan_id": "lattice_primal_usvp_toy_v1",
            "target_family": "REDACTED",
            "attack_type": "REDACTED",
            "accepted": None,
            "evaluation_status": "redacted",
            "combined_score": None,
            "estimated_time_bits": None,
            "estimated_memory_bits": None,
            "estimator_name": None,
            "estimator_version": None,
            "public_release_ok": True,
            "redacted": True,
            "redaction_reason": "contains private prompt/evolution trace",
            "warnings": ["private evaluation redacted from public trace"],
        }
    ]


def test_public_ledger_command_writes_json(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    ledger_path = tmp_path / "ledger.json"
    runner = CliRunner()

    runner.invoke(
        app,
        [
            "evaluate",
            "examples/attack_plans/lattice_primal_usvp_toy.json",
            "--out",
            str(trace_path),
        ],
    )
    ledger_result = runner.invoke(
        app,
        ["public-ledger", str(trace_path), "--out", str(ledger_path)],
    )

    assert ledger_result.exit_code == 0
    ledger = json.loads(ledger_path.read_text())
    assert ledger["schema_version"] == "agades.pqc.public_run_ledger.v1"
    assert ledger["summary"]["total_records"] == 1


def test_public_bundle_command_writes_canonical_artifacts(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    bundle_dir = tmp_path / "bundle"
    runner = CliRunner()

    benchmark_result = runner.invoke(
        app,
        ["benchmark", "benchmarks/lattice_toy_lwe", "--out", str(trace_path)],
    )
    bundle_result = runner.invoke(
        app,
        ["public-bundle", str(trace_path), "--out", str(bundle_dir)],
    )

    assert benchmark_result.exit_code == 0
    assert bundle_result.exit_code == 0
    public_trace = bundle_dir / "trace_public.jsonl"
    ledger_path = bundle_dir / "run_ledger.json"
    readme_path = bundle_dir / "README.md"
    manifest_path = bundle_dir / "MANIFEST.sha256"
    assert public_trace.exists()
    assert ledger_path.exists()
    assert readme_path.exists()
    assert manifest_path.exists()

    ledger = json.loads(ledger_path.read_text())
    assert ledger["source_trace"]["public_sha256"] == hashlib.sha256(
        public_trace.read_bytes()
    ).hexdigest()
    assert "attack_plan" not in ledger["entries"][0]
    manifest = manifest_path.read_text()
    assert "trace_public.jsonl" in manifest
    assert "run_ledger.json" in manifest
    assert "README.md" in manifest


def test_public_bundle_is_bit_reproducible_for_same_benchmark(tmp_path: Path) -> None:
    runner = CliRunner()
    first_trace = tmp_path / "first.jsonl"
    second_trace = tmp_path / "second.jsonl"
    first_bundle = tmp_path / "first_bundle"
    second_bundle = tmp_path / "second_bundle"

    first_benchmark = runner.invoke(
        app,
        ["benchmark", "benchmarks/lattice_toy_lwe", "--out", str(first_trace)],
    )
    second_benchmark = runner.invoke(
        app,
        ["benchmark", "benchmarks/lattice_toy_lwe", "--out", str(second_trace)],
    )
    first_bundle_result = runner.invoke(
        app,
        ["public-bundle", str(first_trace), "--out", str(first_bundle)],
    )
    second_bundle_result = runner.invoke(
        app,
        ["public-bundle", str(second_trace), "--out", str(second_bundle)],
    )

    assert first_benchmark.exit_code == 0
    assert second_benchmark.exit_code == 0
    assert first_bundle_result.exit_code == 0
    assert second_bundle_result.exit_code == 0
    for filename in ("trace_public.jsonl", "run_ledger.json", "MANIFEST.sha256"):
        assert (first_bundle / filename).read_bytes() == (
            second_bundle / filename
        ).read_bytes()


def test_committed_public_run_bundles_have_matching_manifests() -> None:
    expected_summaries = {
            "code_based_toy_hqc_v0": {"CODE_BASED": 6},
        "code_based_toy_isd_v0": {"CODE_BASED": 7},
        "hash_based_toy_bound_v0": {"HASH_BASED": 3},
        "hash_based_toy_misuse_v0": {"HASH_BASED": 1},
        "hash_based_toy_signature_v0": {"HASH_BASED": 4},
            "implementation_security_toy_benchmark_v0": {
                "IMPLEMENTATION_SECURITY": 4
            },
        "implementation_security_toy_kat_v0": {"IMPLEMENTATION_SECURITY": 5},
        "implementation_security_toy_timing_v0": {"IMPLEMENTATION_SECURITY": 3},
        "isogeny_historical_toy_path_v0": {"ISOGENY_HISTORICAL": 4},
        "lattice_downscaled_lwe_instance_solve_v0": {"LWE": 3},
        "lattice_mlwe_downscaled_v0": {"MLWE": 1},
        "lattice_toy_lwe_v0": {"LWE": 2},
        "multivariate_toy_minrank_v0": {"MULTIVARIATE": 3},
        "multivariate_toy_mq_v0": {"MULTIVARIATE": 6},
    }
    root = Path("examples/public_runs")

    assert {path.name for path in root.iterdir() if path.is_dir()} >= set(
        expected_summaries
    )

    for bundle_name, expected_family_summary in expected_summaries.items():
        bundle_dir = root / bundle_name
        public_trace = bundle_dir / "trace_public.jsonl"
        ledger_path = bundle_dir / "run_ledger.json"
        manifest_path = bundle_dir / "MANIFEST.sha256"

        assert public_trace.exists()
        assert ledger_path.exists()
        assert manifest_path.exists()

        manifest = {}
        for line in manifest_path.read_text().splitlines():
            digest, relative_path = line.split("  ", maxsplit=1)
            manifest[relative_path] = digest

        for relative_path, digest in manifest.items():
            artifact = bundle_dir / relative_path
            assert artifact.exists()
            assert hashlib.sha256(artifact.read_bytes()).hexdigest() == digest

        ledger = json.loads(ledger_path.read_text())
        assert ledger["schema_version"] == "agades.pqc.public_run_ledger.v1"
        assert ledger["source_trace"]["public_sha256"] == hashlib.sha256(
            public_trace.read_bytes()
        ).hexdigest()
        assert ledger["summary"]["by_family"] == expected_family_summary
        assert ledger["summary"]["redacted_records"] == 0
        if bundle_name == "lattice_downscaled_lwe_instance_solve_v0":
            assert ledger["entries"][0]["evaluation_status"] == "ok"
