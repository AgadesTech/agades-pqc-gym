# Private Archive Snapshots Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a private archive snapshot manifest for reviewed evolution runs so Agades can retain run-state evidence without publishing traces or candidate content.

**Architecture:** A snapshot is a private JSON manifest that records file paths, SHA-256 digests, sizes, schema metadata, archive summary, trace-link integrity, review-log digest, and retention limits. It validates output paths against the private-run policy and stores no trace records, AttackPlans, private prompts, or candidate source.

**Tech Stack:** Python 3.12, Pydantic, Typer CLI, existing evolution archive, trace, scheduler review-log, private-run policy, and release-audit infrastructure.

---

### Task 1: Snapshot Builder

**Files:**
- Create: `src/agades_pqc_gym/evolution/snapshot.py`
- Modify: `src/agades_pqc_gym/evolution/__init__.py`
- Test: `tests/test_evolution_snapshot.py`

- [x] **Step 1: Write failing tests**

Add tests that create an archive and trace, write a private review log, then call `write_private_archive_snapshot(...)`. Assert schema `agades.pqc.private_archive_snapshot.v1`, private output path, archive/trace digests, complete elite trace links, review-log digest, retention max 90 days, and safety flags all false.

- [x] **Step 2: Run RED**

Run: `uv run pytest tests/test_evolution_snapshot.py -q`

Expected: fail because `agades_pqc_gym.evolution.snapshot` does not exist.

- [x] **Step 3: Implement minimal snapshot module**

Implement:
- `PRIVATE_ARCHIVE_SNAPSHOT_SCHEMA`
- `build_private_archive_snapshot(...)`
- `write_private_archive_snapshot(...)`

Validate output and review-log paths with `validate_policy_private_path`, reject missing/invalid archive or trace files, reject review logs that do not approve all scheduler policy gates, and do not include trace record bodies.

- [x] **Step 4: Run GREEN**

Run: `uv run pytest tests/test_evolution_snapshot.py -q`

Expected: pass.

### Task 2: CLI, Policy, and OpenEvolve Wiring

**Files:**
- Modify: `src/agades_pqc_gym/cli.py`
- Modify: `src/agades_pqc_gym/integrations/private_run_policy.py`
- Modify: `src/agades_pqc_gym/openevolve_adapter/config_templates.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_private_run_policy.py`
- Modify: `tests/test_openevolve_adapter.py`

- [x] **Step 1: Write failing tests**

Add tests for `agades-pqc archive-snapshot`, allowed private command count, and OpenEvolve template keys:
- `archive_snapshot_schema`
- `archive_snapshot_command`

- [x] **Step 2: Run RED**

Run: `uv run pytest tests/test_cli.py::test_archive_snapshot_command_writes_private_manifest tests/test_private_run_policy.py tests/test_openevolve_adapter.py -q`

Expected: fail because the CLI command/template/policy entries are missing.

- [x] **Step 3: Implement CLI/config/policy**

Wire `archive-snapshot` to the writer, add `agades-pqc archive-snapshot` to allowed private commands, and include it in the OpenEvolve private loop template.

- [x] **Step 4: Run GREEN**

Run: `uv run pytest tests/test_cli.py tests/test_private_run_policy.py tests/test_openevolve_adapter.py -q`

Expected: pass.

### Task 3: Release Audit and Docs

**Files:**
- Modify: `src/agades_pqc_gym/integrations/release_audit.py`
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/IMPLEMENT.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/STATUS.md`
- Regenerate: `docs/private_run_policy.json`
- Regenerate: `examples/openevolve/config.yaml`
- Regenerate: `docs/publication_manifest.json`
- Regenerate: `public/release_audit.json`
- Regenerate: `docs/release_status.json`
- Regenerate: `public/publication_preflight.json`

- [x] **Step 1: Write failing audit tests**

Add release-audit expectations for a blocking `evolution-archive-snapshot` smoke that proves private output, review-log attachment, trace-link integrity, digest-only evidence, retention, and no-publication safety.

- [x] **Step 2: Run RED**

Run: `uv run pytest tests/test_release_audit.py tests/test_release_status.py tests/test_publication_preflight.py -q`

Expected: fail because the audit gate and counts are not updated.

- [x] **Step 3: Implement audit/docs/artifact updates**

Add the audit gate, regenerate deterministic artifacts, and document the private snapshot command as the retention checkpoint for reviewed private runs.

- [ ] **Step 4: Run full verification**

Run:
```bash
env PYTHONPATH=src uv run pytest -q
uv run ruff check .
git diff --check
uv build
uv build prime_intellect/verifiers_environment
```

Expected: all pass.
