from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.traces.public_ledger import (
    build_public_run_ledger_from_records,
    read_trace_records,
    render_public_trace_jsonl,
)

PUBLIC_TRACE_FILENAME = "trace_public.jsonl"
PUBLIC_LEDGER_FILENAME = "run_ledger.json"
PUBLIC_README_FILENAME = "README.md"
PUBLIC_MANIFEST_FILENAME = "MANIFEST.sha256"


def write_public_run_bundle(trace_path: Path, out_dir: Path) -> dict[str, Any]:
    records = read_trace_records(trace_path)
    ledger = build_public_run_ledger_from_records(records)

    out_dir.mkdir(parents=True, exist_ok=True)
    public_trace_path = out_dir / PUBLIC_TRACE_FILENAME
    ledger_path = out_dir / PUBLIC_LEDGER_FILENAME
    readme_path = out_dir / PUBLIC_README_FILENAME
    manifest_path = out_dir / PUBLIC_MANIFEST_FILENAME

    public_trace_path.write_text(render_public_trace_jsonl(records), encoding="utf-8")
    ledger_path.write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    readme_path.write_text(_bundle_readme(ledger), encoding="utf-8")
    manifest_path.write_text(
        _manifest(
            out_dir,
            [
                public_trace_path,
                ledger_path,
                readme_path,
            ],
        ),
        encoding="utf-8",
    )
    return {
        "out_dir": out_dir,
        "public_trace": public_trace_path,
        "ledger": ledger_path,
        "readme": readme_path,
        "manifest": manifest_path,
    }


def _bundle_readme(ledger: dict[str, Any]) -> str:
    summary = ledger["summary"]
    return "\n".join(
        [
            "# Agades PQC Gym Public Run Bundle",
            "",
            "This bundle contains public toy/downscaled benchmark artifacts only.",
            "",
            "Files:",
            "",
            f"- `{PUBLIC_TRACE_FILENAME}`: canonical redacted TraceRecord JSONL.",
            f"- `{PUBLIC_LEDGER_FILENAME}`: compact run ledger.",
            f"- `{PUBLIC_MANIFEST_FILENAME}`: SHA-256 checksums for published files.",
            "",
            "Summary:",
            "",
            f"- schema: `{ledger['schema_version']}`",
            f"- records: {summary['total_records']}",
            f"- accepted: {summary['accepted_records']}",
            f"- redacted: {summary['redacted_records']}",
            "",
            "Outputs are toy/downscaled mock-evaluator plumbing evidence only.",
            "They are not security claims.",
            "",
        ]
    )


def _manifest(root: Path, paths: list[Path]) -> str:
    lines = []
    for path in sorted(paths):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
    return "\n".join(lines) + "\n"
