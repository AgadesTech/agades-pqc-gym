# Private Lattice Estimator Baseline Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a private, pin-checked Lattice Estimator baseline-run report that evaluates the existing reviewed LWE contracts without committing numeric reference outputs to public artifacts.

**Architecture:** Keep public `docs/lattice_estimator_baseline_contracts.json` as the non-numeric contract. Add a separate private report writer that consumes those contracts, runs the existing `LatticeEstimatorAdapter`, records pinned-commit status plus minimal numeric time/memory fields under allowed private roots only, and omits raw estimator payloads from committed public artifacts.

**Tech Stack:** Python 3.12, Typer CLI, existing Lattice Estimator adapter, private-run policy path validation, release-audit infrastructure, Pydantic-style JSON contracts.

---

### Task 1: Private Baseline Run Report

**Files:**
- Create: `src/agades_pqc_gym/integrations/lattice_estimator_baseline_run.py`
- Test: `tests/test_lattice_estimator_baseline_run.py`

- [x] **Step 1: Write failing tests**

Add tests that build a fake pinned Lattice Estimator backend, run all checked baseline contracts, and assert:
- schema `agades.pqc.lattice_estimator_baseline_run.v1`
- private output path under `private/reports/`
- five LWE contract results
- all successful results use the checked pin
- numeric outputs are private and not marked as public reference outputs
- raw estimator output is represented by digest only
- public output paths are rejected
- unpinned backend results do not produce successful numeric baselines

- [x] **Step 2: Run RED**

Run: `uv run pytest tests/test_lattice_estimator_baseline_run.py -q`

Expected: fail because `agades_pqc_gym.integrations.lattice_estimator_baseline_run` does not exist.

- [x] **Step 3: Implement minimal report module**

Implement:
- `LATTICE_ESTIMATOR_BASELINE_RUN_SCHEMA`
- `build_lattice_estimator_baseline_run(...)`
- `write_lattice_estimator_baseline_run(...)`

The writer must validate output paths against `docs/private_run_policy.json`, consume only verified LWE contracts, enforce the pinned commit for successful numeric results, keep publication/security flags false, and never write under public roots.

- [x] **Step 4: Run GREEN**

Run: `uv run pytest tests/test_lattice_estimator_baseline_run.py -q`

Expected: pass.

### Task 2: CLI and Private Policy Wiring

**Files:**
- Modify: `src/agades_pqc_gym/cli.py`
- Modify: `src/agades_pqc_gym/integrations/private_run_policy.py`
- Modify: `tests/test_private_run_policy.py`
- Optionally modify: `tests/test_cli.py`

- [x] **Step 1: Write failing tests**

Add policy assertions for `agades-pqc lattice-estimator-baseline-run` and update the allowed private command count.

- [x] **Step 2: Run RED**

Run: `uv run pytest tests/test_private_run_policy.py -q`

Expected: fail because the new command is not yet allowed.

- [x] **Step 3: Implement CLI/policy**

Add CLI command:

```bash
agades-pqc lattice-estimator-baseline-run \
  --contracts docs/lattice_estimator_baseline_contracts.json \
  --out private/reports/lattice_estimator_baseline_run.json \
  --policy docs/private_run_policy.json
```

The command should write the private report and exit nonzero when no pinned numeric baseline result is produced, while still leaving the private report for diagnosis.

- [x] **Step 4: Run GREEN**

Run: `uv run pytest tests/test_private_run_policy.py -q`

Expected: pass.

### Task 3: Release Audit, Docs, and Generated Artifacts

**Files:**
- Modify: `src/agades_pqc_gym/integrations/release_audit.py`
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/IMPLEMENT.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/STATUS.md`
- Regenerate: `docs/private_run_policy.json`
- Regenerate: `docs/publication_manifest.json`
- Regenerate: `public/release_audit.json`
- Regenerate: `docs/release_status.json`
- Regenerate: `public/publication_preflight.json`

- [x] **Step 1: Write failing audit tests**

Add release-audit expectations for a blocking `lattice-estimator-baseline-run-boundary` check using a fake pinned backend. Assert it proves private-only numeric outputs, no raw estimator payload publication, LWE-only contracts, pinned commit, and no security claim.

- [x] **Step 2: Run RED**

Run: `uv run pytest tests/test_release_audit.py tests/test_release_status.py tests/test_publication_preflight.py -q`

Expected: fail because the audit gate and counts are missing.

- [x] **Step 3: Implement audit/docs/artifact updates**

Add the audit gate, update docs, regenerate deterministic artifacts, and keep the public baseline contracts non-numeric.

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
