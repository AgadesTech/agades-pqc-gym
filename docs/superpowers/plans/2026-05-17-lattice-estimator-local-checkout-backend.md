# Lattice Estimator Local Checkout Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a private Lattice Estimator backend path that loads a local upstream checkout only after proving its Git commit matches the reviewed pin.

**Architecture:** Extend the existing `LatticeEstimatorAdapter` with an optional source checkout path. When a checkout path is provided, the adapter must read `git rev-parse HEAD` first, reject mismatches before importing Python, and then import `estimator` from that checkout for private baseline runs. Public artifacts still publish no numeric Lattice Estimator baselines and make no security claim.

**Tech Stack:** Python 3.12, Typer CLI, subprocess Git commit verification, existing Lattice Estimator adapter, deterministic manifest/release-audit JSON.

---

### Task 1: Local Checkout Backend Tests

**Files:**
- Modify: `tests/test_lattice_estimator_adapter.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Write failing adapter tests**

Add a temporary fake `estimator` package inside a Git repository and test that:
- `LatticeEstimatorAdapter(source_path=..., config=LatticeEstimatorConfig(required_commit=<repo-head>))` imports it.
- `result.estimator_commit` is the Git HEAD, not a module `__commit__` attribute.
- a mismatched `required_commit` rejects before a successful estimate.
- a source directory without Git metadata produces an `error` result.

- [x] **Step 2: Write failing CLI test**

Add a `lattice-estimator-baseline-run --estimator-source <checkout>` CLI test that writes a private report using the fake checkout and asserts five pinned numeric private results.

- [x] **Step 3: Run RED**

Run:

```bash
uv run pytest tests/test_lattice_estimator_adapter.py tests/test_cli.py::test_lattice_estimator_baseline_run_command_accepts_estimator_source_checkout -q
```

Expected: fail because `source_path` / `--estimator-source` are not supported.

### Task 2: Backend and CLI Implementation

**Files:**
- Modify: `src/agades_pqc_gym/evaluators/lattice_estimator.py`
- Modify: `src/agades_pqc_gym/cli.py`

- [x] **Step 1: Implement local checkout backend**

Add `source_path` support to `LatticeEstimatorAdapter` and `ImportedLatticeEstimatorBackend`. The backend must run `git -C <source_path> rev-parse HEAD`, compare it to the required commit before import when a required commit is configured, then import `estimator` from that checkout.

- [x] **Step 2: Implement CLI option**

Add `--estimator-source` to `agades-pqc lattice-estimator-baseline-run` and pass it to the lattice adapter. Keep the default path unchanged for installed-module use.

- [x] **Step 3: Run GREEN**

Run:

```bash
uv run pytest tests/test_lattice_estimator_adapter.py tests/test_cli.py::test_lattice_estimator_baseline_run_command_accepts_estimator_source_checkout -q
```

Expected: pass.

### Task 3: Manifest, Docs, Audit, and Artifacts

**Files:**
- Modify: `src/agades_pqc_gym/integrations/lattice_estimator_manifest.py`
- Modify: `src/agades_pqc_gym/integrations/release_audit.py`
- Modify: `README.md`
- Modify: `docs/IMPLEMENT.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/STATUS.md`
- Regenerate: `docs/lattice_estimator_manifest.json`
- Regenerate: `docs/publication_manifest.json`
- Regenerate: `public/release_audit.json`
- Regenerate: `docs/release_status.json`
- Regenerate: `public/publication_preflight.json`

- [x] **Step 1: Write failing manifest/audit expectations**

Update tests so the Lattice Estimator manifest and release audit prove the local-checkout backend verifies Git HEAD before import and keeps the source path private/review-only.

- [x] **Step 2: Run RED**

Run:

```bash
uv run pytest tests/test_lattice_estimator_manifest.py tests/test_release_audit.py tests/test_release_status.py tests/test_publication_preflight.py -q
```

Expected: fail until manifest/audit/docs/artifacts are updated.

- [x] **Step 3: Update manifest/docs/artifacts**

Regenerate deterministic artifacts after updating generators and docs.

- [x] **Step 4: Full verification**

Run:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
uv build
uv build prime_intellect/verifiers_environment
```

Expected: all pass.
