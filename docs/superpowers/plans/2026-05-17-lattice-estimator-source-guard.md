# Lattice Estimator Source Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the real `--estimator-source` execution path enforce the same reviewed checkout boundary as the private checkout preflight before importing upstream Python.

**Architecture:** Extract checkout inspection into a shared evaluator-side module used by both the non-executing preflight and the import path. The adapter must reject dirty working trees, missing or wrong upstream remotes, missing estimator entrypoints, and pin mismatches before `import estimator` can run.

**Tech Stack:** Python 3.12, subprocess Git probes, existing Lattice Estimator adapter, private preflight report generator, pytest, deterministic release-audit artifacts.

---

### Task 1: Adapter RED Tests

**Files:**
- Modify: `tests/test_lattice_estimator_adapter.py`

- [x] **Step 1: Add realistic checkout origin to the fake checkout helper**

Add:

```python
subprocess.run(
    ["git", "remote", "add", "origin", "https://github.com/malb/lattice-estimator"],
    cwd=source,
    check=True,
    capture_output=True,
)
```

- [x] **Step 2: Add dirty-checkout rejection test**

Add a test that writes an untracked `README.md`, runs `LatticeEstimatorAdapter(source_path=source, required_commit=commit)`, and expects `evaluation_status="error"`, warning `Local Lattice Estimator checkout working tree is not clean.`, and no `IMPORT_MARKER`.

- [x] **Step 3: Add wrong-origin rejection test**

Add a test that sets `origin` to `https://example.com/fork.git`, runs the adapter, and expects `evaluation_status="error"`, warning that the origin remote does not match `https://github.com/malb/lattice-estimator`, and no `IMPORT_MARKER`.

- [x] **Step 4: Run RED**

Run:

```bash
uv run pytest tests/test_lattice_estimator_adapter.py::test_lattice_estimator_adapter_rejects_dirty_local_checkout_before_import tests/test_lattice_estimator_adapter.py::test_lattice_estimator_adapter_rejects_wrong_origin_before_import -q
```

Expected: both tests fail because the adapter still imports after only checking the commit.

### Task 2: Shared Checkout Inspection

**Files:**
- Create: `src/agades_pqc_gym/evaluators/lattice_estimator_checkout.py`
- Modify: `src/agades_pqc_gym/evaluators/lattice_estimator.py`
- Modify: `src/agades_pqc_gym/integrations/lattice_estimator_checkout_preflight.py`

- [x] **Step 1: Create shared inspection module**

Implement subprocess-only helpers that return a typed inspection object with `head_commit`, `head_matches_required_pin`, `remote_origin`, `remote_matches_upstream`, `working_tree_clean`, estimator entrypoint booleans, and failures.

- [x] **Step 2: Use inspection in preflight**

Replace duplicated Git probing in `lattice_estimator_checkout_preflight.py` with the shared inspection while preserving the JSON schema and report shape.

- [x] **Step 3: Require clean inspection before adapter import**

Call the shared inspection from `_load_estimator_module()` before `_import_estimator_from_checkout()`. Raise `EstimatorUnavailable` with the first inspection failure, before importing upstream Python.

- [x] **Step 4: Run GREEN**

Run:

```bash
uv run pytest tests/test_lattice_estimator_adapter.py tests/test_lattice_estimator_baseline_run.py::test_write_lattice_estimator_checkout_preflight_private_report -q
```

Expected: all pass.

### Task 3: Release Evidence and Docs

**Files:**
- Modify: `src/agades_pqc_gym/integrations/lattice_estimator_manifest.py`
- Modify: `src/agades_pqc_gym/integrations/release_audit.py`
- Modify: `tests/test_lattice_estimator_manifest.py`
- Modify: `tests/test_release_audit.py`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/STATUS.md`
- Regenerate: `docs/lattice_estimator_manifest.json`
- Regenerate: `public/release_audit.json`
- Regenerate: `docs/release_status.json`
- Regenerate: `docs/publication_manifest.json`
- Regenerate: `public/publication_preflight.json`

- [x] **Step 1: Add release-audit expectations**

Assert `source_checkout_backend` records dirty-checkout and wrong-origin rejection before import.

- [x] **Step 2: Update manifest generator and docs**

Record the stronger `--estimator-source` guard in the checked manifest and docs.

- [x] **Step 3: Regenerate deterministic artifacts**

Run generator commands for the changed manifests and derived artifacts.

### Task 4: Verification, Commit, Push

**Files:**
- Verify all modified files.

- [x] **Step 1: Full verification**

Run:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
uv build
uv build prime_intellect/verifiers_environment
```

- [x] **Step 2: Artifact and naming gates**

Run release/status/publication verifiers and the legacy-name scan.

- [ ] **Step 3: Commit, push, and check CI**

Commit the coherent tranche, push `codex/multifamily-architecture`, and verify PR checks.
