from __future__ import annotations

import csv
import hashlib
import json
from io import StringIO
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.public_benchmark_manifest import (
    build_public_benchmark_manifest,
)

PUBLIC_RUN_EXPORT_SCHEMA = "agades.pqc.public_run_export.v1"
PUBLIC_RUN_EXPORT_VERIFICATION_SCHEMA = "agades.pqc.public_run_export_verification.v1"
ROOT = Path(__file__).resolve().parents[3]
MANIFEST_FILENAME = "manifest.json"
RUNS_JSONL_FILENAME = "runs.jsonl"
RUNS_CSV_FILENAME = "runs.csv"
CHECKSUMS_FILENAME = "MANIFEST.sha256"
CSV_FIELDS = [
    "export_id",
    "bundle_id",
    "run_id",
    "trace_id",
    "candidate_id",
    "generation",
    "attack_plan_id",
    "target_family",
    "attack_type",
    "accepted",
    "evaluation_status",
    "combined_score",
    "estimated_time_bits",
    "estimated_memory_bits",
    "estimator_name",
    "public_release_ok",
    "redacted",
    "source_trace",
]


def build_public_run_export(*, root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    benchmark = build_public_benchmark_manifest(root=project_root)
    bundles = _bundles(project_root, benchmark)
    runs = _runs(project_root, bundles)
    families = sorted({run["target_family"] for run in runs})
    security_claim = bool(benchmark["summary"]["security_claim"])

    return {
        "manifest": {
            "schema_version": PUBLIC_RUN_EXPORT_SCHEMA,
            "project": {
                "name": "Agades PQC Gym",
                "package": "agades_pqc_gym",
                "cli": "agades-pqc",
                "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            },
            "export": {
                "id": "agades-pqc-public-run-export-v0",
                "format": "prime_style_flat_public_runs",
                "publication_status": "local_artifact_ready_review_required",
                "scope": "toy_and_downscaled_public_verifier_bundles",
            },
            "summary": {
                "accepted_run_count": sum(
                    1 for run in runs if run["accepted"] is True
                ),
                "bundle_count": len(bundles),
                "family_count": len(families),
                "redacted_run_count": sum(
                    1 for run in runs if run["redacted"] is True
                ),
                "run_count": len(runs),
                "security_claim": security_claim,
            },
            "artifacts": {
                "checksums": CHECKSUMS_FILENAME,
                "manifest": MANIFEST_FILENAME,
                "runs_csv": RUNS_CSV_FILENAME,
                "runs_jsonl": RUNS_JSONL_FILENAME,
            },
            "bundles": bundles,
            "families": families,
            "sources": {
                "prime_intellect": {
                    "autonomous_speedrunning_reference": (
                        "https://github.com/PrimeIntellect-ai/"
                        "experiments-autonomous-speedrunning"
                    ),
                    "quickstart": (
                        "https://app.primeintellect.ai/dashboard/home/quickstart"
                    ),
                },
                "hugging_face": {
                    "dataset_bundle": "hf/dataset",
                    "space_manifest": "hf/space_manifest.json",
                },
                "nvidia": {
                    "accelerator_manifest": "nvidia/accelerator_manifest.json",
                },
            },
            "safety": {
                "arbitrary_code_execution": False,
                "contains_private_traces": False,
                "live_targeting": False,
                "publishes_private_candidates": False,
                "review_required_before_publish": True,
                "security_claim": security_claim,
            },
        },
        "runs": runs,
    }


def write_public_run_export(
    out_dir: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    export = build_public_run_export(root=root)
    manifest = export["manifest"]
    runs = export["runs"]

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / MANIFEST_FILENAME
    runs_jsonl_path = out_dir / RUNS_JSONL_FILENAME
    runs_csv_path = out_dir / RUNS_CSV_FILENAME
    checksums_path = out_dir / CHECKSUMS_FILENAME

    runs_jsonl_path.write_text(_runs_jsonl(runs), encoding="utf-8")
    _write_runs_csv(runs_csv_path, runs)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    checksums_path.write_text(
        _checksum_manifest(out_dir, [manifest_path, runs_jsonl_path, runs_csv_path]),
        encoding="utf-8",
    )
    return manifest


def verify_public_run_export(
    export_dir: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    resolved_export_dir = (
        export_dir if export_dir.is_absolute() else project_root / export_dir
    )
    manifest_path = resolved_export_dir / MANIFEST_FILENAME
    runs_jsonl_path = resolved_export_dir / RUNS_JSONL_FILENAME
    runs_csv_path = resolved_export_dir / RUNS_CSV_FILENAME
    checksums_path = resolved_export_dir / CHECKSUMS_FILENAME
    required_paths = [manifest_path, runs_jsonl_path, runs_csv_path, checksums_path]
    failures = [
        f"Public run export artifact is missing: {path.as_posix()}."
        for path in required_paths
        if not path.is_file()
    ]
    if failures:
        return _verification_result(export_dir, manifest={}, failures=failures)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _verification_result(
            export_dir,
            manifest={},
            failures=["Public run export manifest is not valid JSON."],
        )
    if not isinstance(manifest, dict):
        return _verification_result(
            export_dir,
            manifest={},
            failures=["Public run export manifest must be a JSON object."],
        )

    expected = build_public_run_export(root=project_root)
    expected_manifest = expected["manifest"]
    expected_runs = expected["runs"]

    if manifest != expected_manifest:
        failures.append("Public run export is not in sync.")
    if runs_jsonl_path.read_text(encoding="utf-8") != _runs_jsonl(expected_runs):
        failures.append("Public run export runs.jsonl is not in sync.")
    if runs_csv_path.read_text(encoding="utf-8") != _runs_csv(expected_runs):
        failures.append("Public run export runs.csv is not in sync.")
    expected_checksums = _checksum_manifest(
        resolved_export_dir,
        [manifest_path, runs_jsonl_path, runs_csv_path],
    )
    if checksums_path.read_text(encoding="utf-8") != expected_checksums:
        failures.append("Public run export MANIFEST.sha256 is not in sync.")
    failures.extend(_verify_csv(runs_csv_path, expected_runs))
    failures.extend(_verify_checksum_manifest(resolved_export_dir, checksums_path))
    failures.extend(_verify_safety(manifest))

    return _verification_result(export_dir, manifest=manifest, failures=failures)


def _bundles(root: Path, benchmark: dict[str, Any]) -> list[dict[str, Any]]:
    bundles = []
    for bundle in sorted(benchmark["bundles"], key=lambda item: item["id"]):
        bundle_path = root / bundle["bundle_path"]
        bundles.append(
            {
                "id": bundle["id"],
                "family": bundle["family"],
                "run_id": bundle["run_id"],
                "bundle_path": bundle["bundle_path"],
                "trace_public": f"{bundle['bundle_path']}/trace_public.jsonl",
                "trace_public_sha256": bundle["trace_public_sha256"],
                "record_count": bundle["record_count"],
                "accepted_records": bundle["accepted_records"],
                "redacted_records": bundle["redacted_records"],
                "ledger_sha256": hashlib.sha256(
                    (bundle_path / "run_ledger.json").read_bytes()
                ).hexdigest(),
            }
        )
    return bundles


def _runs(root: Path, bundles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for bundle in bundles:
        ledger_path = root / bundle["bundle_path"] / "run_ledger.json"
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        entries = ledger.get("entries", [])
        if not isinstance(entries, list):
            raise ValueError(f"Public run ledger entries are invalid: {ledger_path}")
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"Public run ledger entry is invalid: {ledger_path}")
            runs.append(_run_row(bundle, entry))
    return sorted(runs, key=lambda run: run["export_id"])


def _run_row(bundle: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "accepted": entry.get("accepted"),
        "attack_plan_id": entry.get("attack_plan_id"),
        "attack_type": entry.get("attack_type"),
        "bundle_id": bundle["id"],
        "candidate_id": entry.get("candidate_id"),
        "combined_score": entry.get("combined_score"),
        "estimated_memory_bits": entry.get("estimated_memory_bits"),
        "estimated_time_bits": entry.get("estimated_time_bits"),
        "estimator_name": entry.get("estimator_name"),
        "evaluation_status": entry.get("evaluation_status"),
        "export_id": f"{bundle['id']}:{entry.get('candidate_id')}",
        "generation": entry.get("generation"),
        "public_release_ok": entry.get("public_release_ok"),
        "redacted": entry.get("redacted"),
        "run_id": entry.get("run_id"),
        "source_trace": bundle["trace_public"],
        "target_family": entry.get("target_family"),
        "trace_id": entry.get("trace_id"),
    }


def _runs_jsonl(runs: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(run, allow_nan=False, sort_keys=True) + "\n" for run in runs
    )


def _write_runs_csv(path: Path, runs: list[dict[str, Any]]) -> None:
    path.write_text(_runs_csv(runs), encoding="utf-8")


def _runs_csv(runs: list[dict[str, Any]]) -> str:
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for run in runs:
        writer.writerow({field: run.get(field) for field in CSV_FIELDS})
    return csv_buffer.getvalue()


def _checksum_manifest(root: Path, paths: list[Path]) -> str:
    lines = []
    for path in sorted(paths):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
    return "\n".join(lines) + "\n"


def _verify_csv(path: Path, expected_runs: list[dict[str, Any]]) -> list[str]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    failures: list[str] = []
    if len(rows) != len(expected_runs):
        failures.append("Public run export runs.csv row count is not in sync.")
        return failures
    expected_ids = [run["export_id"] for run in expected_runs]
    observed_ids = [row.get("export_id") for row in rows]
    if observed_ids != expected_ids:
        failures.append("Public run export runs.csv export_id order is not in sync.")
    return failures


def _verify_checksum_manifest(export_dir: Path, checksums_path: Path) -> list[str]:
    failures: list[str] = []
    for line_number, line in enumerate(
        checksums_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        parsed = line.split("  ", maxsplit=1)
        if len(parsed) != 2 or len(parsed[0]) != 64:
            failures.append(f"Malformed public run export checksum line {line_number}.")
            continue
        expected_digest, relative_path = parsed
        target = (export_dir / relative_path).resolve()
        try:
            target.relative_to(export_dir.resolve())
        except ValueError:
            failures.append(
                f"Public run export checksum target escapes export dir: {line_number}."
            )
            continue
        if not target.is_file():
            failures.append(
                f"Public run export checksum target is missing: {line_number}."
            )
            continue
        actual_digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            failures.append(f"Public run export checksum mismatch: {relative_path}.")
    return failures


def _verify_safety(manifest: dict[str, Any]) -> list[str]:
    failures = []
    safety = manifest.get("safety", {})
    if not isinstance(safety, dict):
        return ["Public run export safety section must be an object."]
    if safety.get("contains_private_traces") is not False:
        failures.append("Public run export may expose private traces.")
    if safety.get("publishes_private_candidates") is not False:
        failures.append("Public run export may publish private candidates.")
    if safety.get("security_claim") is not False:
        failures.append("Public run export advertises a security claim.")
    if safety.get("arbitrary_code_execution") is not False:
        failures.append("Public run export may execute arbitrary code.")
    if safety.get("live_targeting") is not False:
        failures.append("Public run export may target live systems.")
    return failures


def _verification_result(
    export_dir: Path,
    *,
    manifest: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    summary = manifest.get("summary", {}) if isinstance(manifest, dict) else {}
    return {
        "schema_version": PUBLIC_RUN_EXPORT_VERIFICATION_SCHEMA,
        "accepted": not failures,
        "export_dir": export_dir.as_posix(),
        "summary": {
            "bundle_count": int(summary.get("bundle_count", 0)),
            "failure_count": len(failures),
            "run_count": int(summary.get("run_count", 0)),
        },
        "failures": failures,
    }
