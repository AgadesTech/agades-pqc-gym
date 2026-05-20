from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.publication_manifest import (
    build_publication_manifest,
)

PUBLIC_BENCHMARK_MANIFEST_SCHEMA = "agades.pqc.public_benchmark_manifest.v1"
PUBLIC_BENCHMARK_VERIFICATION_SCHEMA = "agades.pqc.public_benchmark_verification.v1"
ROOT = Path(__file__).resolve().parents[3]


def build_public_benchmark_manifest(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    publication_manifest = build_publication_manifest(root=project_root)
    bundles = [
        _public_benchmark_bundle(project_root, bundle)
        for bundle in publication_manifest["public_run_bundles"]
    ]
    families = sorted({bundle["family"] for bundle in bundles})
    record_count = sum(bundle["record_count"] for bundle in bundles)
    security_claim = any(bundle["security_claim"] for bundle in bundles)

    return {
        "schema_version": PUBLIC_BENCHMARK_MANIFEST_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "package": "agades_pqc_gym",
            "cli": "agades-pqc",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
        },
        "benchmark": {
            "id": "agades-pqc-public-benchmark-v0",
            "name": "Agades PQC Gym Public Benchmark v0",
            "publication_status": "local_artifact_ready_review_required",
            "scope": "toy_and_downscaled_public_verifier_bundles",
        },
        "summary": {
            "bundle_count": len(bundles),
            "families": families,
            "record_count": record_count,
            "security_claim": security_claim,
        },
        "bundles": bundles,
        "safety": {
            "contains_private_traces": False,
            "publishes_private_candidates": False,
            "arbitrary_code_execution": False,
            "live_targeting": False,
            "security_claim": security_claim,
            "review_required_before_publish": True,
        },
        "release_audit_gate": "public-benchmark-manifest",
        "release_gates": [
            "uv run pytest tests/test_public_benchmark_manifest.py -q",
            "uv run agades-pqc public-benchmark-manifest --out "
            "docs/public_benchmark_manifest.json",
            "uv run agades-pqc public-benchmark-verify --manifest "
            "docs/public_benchmark_manifest.json",
            "uv run agades-pqc ecosystem-smoke-verify --report "
            "reports/ecosystem_smoke.json",
            "uv run agades-pqc release-audit --out public/release_audit.json",
        ],
    }


def write_public_benchmark_manifest(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    manifest = build_public_benchmark_manifest(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_public_benchmark_manifest(
    manifest_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    if not manifest_path.is_file():
        return _verification_result(
            manifest_path,
            bundles=[],
            record_count=0,
            failures=[
                f"Public benchmark manifest is missing: {manifest_path.as_posix()}."
            ],
        )

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _verification_result(
            manifest_path,
            bundles=[],
            record_count=0,
            failures=[
                f"Public benchmark manifest is not valid JSON: "
                f"{manifest_path.as_posix()}."
            ],
        )

    if not isinstance(manifest, dict):
        return _verification_result(
            manifest_path,
            bundles=[],
            record_count=0,
            failures=["Public benchmark manifest must be a JSON object."],
        )

    expected = build_public_benchmark_manifest(root=project_root)
    failures: list[str] = []

    if manifest != expected:
        failures.append("Public benchmark manifest is not in sync.")

    summary = manifest.get("summary", {})
    safety = manifest.get("safety", {})
    bundles = manifest.get("bundles", [])
    if not isinstance(bundles, list):
        bundles = []
        failures.append("Public benchmark bundles must be a list.")

    if safety.get("contains_private_traces") is not False:
        failures.append("Public benchmark manifest may expose private traces.")
    if safety.get("publishes_private_candidates") is not False:
        failures.append("Public benchmark manifest may publish private candidates.")
    if safety.get("security_claim") is not False:
        failures.append("Public benchmark manifest advertises a security claim.")

    observed_records = 0
    observed_families: set[str] = set()
    for bundle in bundles:
        if not isinstance(bundle, dict):
            failures.append("Public benchmark manifest contains a non-object bundle.")
            continue
        observed_records += _int_value(bundle.get("record_count"))
        family = bundle.get("family")
        if isinstance(family, str):
            observed_families.add(family)
        failures.extend(_verify_public_benchmark_bundle(project_root, bundle))

    if summary.get("bundle_count") != len(bundles):
        failures.append("Public benchmark summary bundle_count is inconsistent.")
    if summary.get("record_count") != observed_records:
        failures.append("Public benchmark summary record_count is inconsistent.")
    if summary.get("families") != sorted(observed_families):
        failures.append("Public benchmark summary families are inconsistent.")
    if summary.get("security_claim") is not False:
        failures.append("Public benchmark summary advertises a security claim.")

    return _verification_result(
        manifest_path,
        bundles=bundles,
        record_count=observed_records,
        failures=failures,
    )


def _public_benchmark_bundle(
    root: Path,
    publication_bundle: dict[str, Any],
) -> dict[str, Any]:
    bundle_id = publication_bundle["id"]
    bundle_path = root / "examples" / "public_runs" / bundle_id
    ledger_path = bundle_path / "run_ledger.json"
    manifest_path = bundle_path / "MANIFEST.sha256"

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    entries = ledger.get("entries", [])
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"Public benchmark bundle {bundle_id} has no entries.")

    run_ids = {
        entry.get("run_id")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("run_id"), str)
    }
    if len(run_ids) != 1:
        raise ValueError(
            f"Public benchmark bundle {bundle_id} must contain exactly one run_id."
        )
    run_id = next(iter(run_ids))
    summary = ledger.get("summary", {})
    source_trace = ledger.get("source_trace", {})
    benchmark_path = publication_bundle["benchmark_path"]

    return {
        "id": bundle_id,
        "family": publication_bundle["family"],
        "run_id": run_id,
        "benchmark_path": benchmark_path,
        "bundle_path": bundle_path.relative_to(root).as_posix(),
        "record_count": int(summary.get("total_records", len(entries))),
        "accepted_records": int(summary.get("accepted_records", 0)),
        "redacted_records": int(summary.get("redacted_records", 0)),
        "evaluation_statuses": sorted(
            _string_keys(summary.get("by_evaluation_status", {}))
        ),
        "estimators": sorted(_string_keys(summary.get("by_estimator", {}))),
        "trace_public_sha256": source_trace.get("public_sha256"),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "regenerate_commands": [
            f"uv run agades-pqc benchmark {benchmark_path} --out runs/{run_id}.jsonl",
            (
                f"uv run agades-pqc public-bundle runs/{run_id}.jsonl "
                f"--out examples/public_runs/{bundle_id}"
            ),
        ],
        "security_claim": bool(publication_bundle["security_claim"]),
        "publishes_private_candidates": bool(
            publication_bundle["publishes_private_candidates"]
        ),
    }


def _string_keys(value: Any) -> set[str]:
    if not isinstance(value, dict):
        return set()
    return {key for key in value if isinstance(key, str)}


def _verify_public_benchmark_bundle(root: Path, bundle: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    bundle_id = str(bundle.get("id"))
    bundle_path, bundle_path_failures = _confined_manifest_path(
        root,
        bundle.get("bundle_path"),
        label="bundle",
        bundle_id=bundle_id,
    )
    if bundle_path_failures:
        return bundle_path_failures

    if not bundle_path.is_dir():
        failures.append(f"Public benchmark bundle path is missing: {bundle_id}.")
        return failures

    benchmark_path, benchmark_path_failures = _confined_manifest_path(
        root,
        bundle.get("benchmark_path"),
        label="input",
        bundle_id=bundle_id,
    )
    failures.extend(benchmark_path_failures)
    if benchmark_path is not None and not benchmark_path.is_dir():
        failures.append(f"Public benchmark input path is missing: {bundle_id}.")

    manifest_file = bundle_path / "MANIFEST.sha256"
    trace_file = bundle_path / "trace_public.jsonl"
    ledger_file = bundle_path / "run_ledger.json"
    artifact_failures = False
    for required in (manifest_file, trace_file, ledger_file):
        if not required.is_file():
            artifact_failures = True
            failures.append(
                f"Public benchmark bundle artifact is missing: "
                f"{required.relative_to(root).as_posix()}."
            )

    if not artifact_failures:
        manifest_sha = hashlib.sha256(manifest_file.read_bytes()).hexdigest()
        if bundle.get("manifest_sha256") != manifest_sha:
            failures.append(f"manifest_sha256 mismatch for {bundle_id}.")

        trace_sha = hashlib.sha256(trace_file.read_bytes()).hexdigest()
        if bundle.get("trace_public_sha256") != trace_sha:
            failures.append(f"trace_public_sha256 mismatch for {bundle_id}.")

        try:
            ledger = json.loads(ledger_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            failures.append(f"ledger is not valid JSON for {bundle_id}.")
        else:
            if ledger.get("source_trace", {}).get("public_sha256") != trace_sha:
                failures.append(f"ledger source trace digest mismatch for {bundle_id}.")
            if ledger.get("safety", {}).get("security_claim") is not False:
                failures.append(f"ledger advertises a security claim for {bundle_id}.")
            if _int_value(ledger.get("summary", {}).get("total_records")) != _int_value(
                bundle.get("record_count")
            ):
                failures.append(f"record_count mismatch for {bundle_id}.")

        failures.extend(_verify_sha256_manifest(bundle_path, manifest_file, bundle_id))

    if bundle.get("security_claim") is not False:
        failures.append(f"Public benchmark bundle makes a claim: {bundle_id}.")
    if bundle.get("publishes_private_candidates") is not False:
        failures.append(
            f"Public benchmark bundle may publish private candidates: {bundle_id}."
        )
    if bundle.get("redacted_records") != 0:
        failures.append(f"Public benchmark bundle has redacted records: {bundle_id}.")
    return failures


def _verification_result(
    manifest_path: Path,
    *,
    bundles: list[Any],
    record_count: int,
    failures: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_BENCHMARK_VERIFICATION_SCHEMA,
        "accepted": not failures,
        "manifest_path": manifest_path.as_posix(),
        "summary": {
            "bundle_count": len(bundles),
            "failure_count": len(failures),
            "record_count": record_count,
        },
        "failures": failures,
    }


def _confined_manifest_path(
    root: Path,
    value: Any,
    *,
    label: str,
    bundle_id: str,
) -> tuple[Path | None, list[str]]:
    if not isinstance(value, str) or value == "":
        return None, [f"Public benchmark {label} path is invalid: {bundle_id}."]
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None, [
            f"Public benchmark {label} path escapes repository: {bundle_id}."
        ]
    return path, []


def _verify_sha256_manifest(
    bundle_path: Path,
    manifest_file: Path,
    bundle_id: str,
) -> list[str]:
    failures: list[str] = []
    for line_number, line in enumerate(
        manifest_file.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        parsed = line.split("  ", maxsplit=1)
        if len(parsed) != 2 or len(parsed[0]) != 64:
            failures.append(
                f"Malformed checksum line for {bundle_id}:{line_number}."
            )
            continue
        expected_digest, relative_path = parsed
        target = (bundle_path / relative_path).resolve()
        try:
            target.relative_to(bundle_path.resolve())
        except ValueError:
            failures.append(
                f"Checksum target escapes bundle for {bundle_id}:{line_number}."
            )
            continue
        if not target.is_file():
            failures.append(
                f"Checksum target missing for {bundle_id}:{line_number}."
            )
            continue
        actual_digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            failures.append(
                f"Checksum mismatch for {bundle_id}:{relative_path}."
            )
    return failures


def _int_value(value: Any) -> int:
    if isinstance(value, int):
        return value
    return 0
