# Public Run Ledger

The public run ledger is the stable publication artifact for toy/downscaled benchmark runs. It is derived from trace JSONL files and intentionally contains only compact entry summaries, not full private evolution traces.

Generate one with:

```bash
uv run agades-pqc public-ledger runs/toy_benchmark.jsonl --out public/toy_run_ledger.json
```

Generate a complete publication bundle with:

```bash
uv run agades-pqc public-bundle runs/toy_benchmark.jsonl --out public/toy_run_bundle
```

The bundle contains `trace_public.jsonl`, `run_ledger.json`, `README.md`, and `MANIFEST.sha256`. Rebuilding a bundle from equivalent benchmark trace content produces byte-identical public artifacts.

Committed public bundles include:

```text
examples/public_runs/lattice_toy_lwe_v0/
examples/public_runs/lattice_mlwe_downscaled_v0/
```

## Schema

Current schema version: `agades.pqc.public_run_ledger.v1`

Top-level fields:

- `schema_version`: ledger schema identifier.
- `ledger_version`: package version that generated the ledger.
- `source_trace`: canonical public trace artifact name, public SHA-256 hash, and record count.
- `summary`: total, accepted, redacted, family, evaluation-status, and estimator counts.
- `entries`: compact public entries keyed by `trace_id`, `run_id`, `candidate_id`, family, attack type, estimator, status, score, warnings, and redaction state.
- `safety`: fixed public-safety flags showing that the artifact does not execute arbitrary code, target live systems, or assert a security break.

## Redaction

If a `TraceRecord` is not public-release eligible, the ledger keeps only the attack-plan identifier, candidate metadata, evaluation status, score fields, estimator metadata, warnings, and redaction reason. It reports `target_family="REDACTED"` and `attack_type="REDACTED"` for that entry.

The ledger hashes the canonical public trace, not the raw source trace, so it can be published without binding the artifact to private trace bytes. It should be used for public toy benchmark reproducibility and sponsor/community review. It must not contain private prompts, unpublished candidate strategies, private evaluator recipes, or collaborator-sensitive notes.

Canonical public traces set `created_at` to `1970-01-01T00:00:00+00:00` and replace internal trace IDs with stable public IDs derived from the published record content. Internal traces still keep their original runtime timestamps and identifiers.
