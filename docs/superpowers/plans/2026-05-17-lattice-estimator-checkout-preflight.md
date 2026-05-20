# Lattice Estimator Checkout Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a private, non-executing checkout preflight for reviewed local `malb/lattice-estimator` source trees before private baseline runs use `--estimator-source`.

**Architecture:** Create a focused integration module that inspects a local Git checkout with subprocess-only Git probes, records whether the HEAD matches the reviewed pin, verifies the estimator package entrypoint exists, and writes a private JSON report under policy-approved roots. The preflight must not import upstream Python, execute estimator code, publish numeric results, or make a security claim.

**Tech Stack:** Python 3.12, Typer CLI, subprocess Git probes, existing private-run policy validation, deterministic JSON artifacts, pytest.

---

### Task 1: Private Checkout Preflight Tests

**Files:**
- Modify: `tests/test_lattice_estimator_baseline_run.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Write failing integration tests**

Add tests that create a fake local `estimator/` package inside a Git repository and assert:
- `write_lattice_estimator_checkout_preflight()` writes a private report with `schema_version="agades.pqc.lattice_estimator_checkout_preflight.v1"`.
- A matching commit sets `ready_for_private_baseline_run=True`.
- A mismatched required commit sets `ready_for_private_baseline_run=False` and records a failure.
- A public output path is rejected through the private-run policy.
- The report safety block records `imports_upstream_python=False` and `executes_estimator=False`.

- [x] **Step 2: Write failing CLI test**

Add a CLI test for:

```bash
agades-pqc lattice-estimator-checkout-preflight \
  --estimator-source <fake-checkout> \
  --out private/reports/lattice_estimator_checkout_preflight.json \
  --policy docs/private_run_policy.json
```

Expected assertions: exit code `0`, private report written, matching commit recorded, and no import marker created by the fake estimator package.

- [x] **Step 3: Run RED**

Run:

```bash
uv run pytest tests/test_lattice_estimator_baseline_run.py tests/test_cli.py::test_lattice_estimator_checkout_preflight_command_writes_private_report -q
```

Expected: fail because the preflight module and CLI command do not exist yet.

### Task 2: Module and CLI Implementation

**Files:**
- Create: `src/agades_pqc_gym/integrations/lattice_estimator_checkout_preflight.py`
- Modify: `src/agades_pqc_gym/cli.py`

- [x] **Step 1: Implement the private preflight module**

Implement:

```python
LATTICE_ESTIMATOR_CHECKOUT_PREFLIGHT_SCHEMA = "agades.pqc.lattice_estimator_checkout_preflight.v1"
DEFAULT_CHECKOUT_PREFLIGHT_PATH = Path("private/reports/lattice_estimator_checkout_preflight.json")

def build_lattice_estimator_checkout_preflight(...)
def write_lattice_estimator_checkout_preflight(...)
```

The builder must call `git -C <source> rev-parse HEAD`, `git -C <source> status --porcelain`, and `git -C <source> remote get-url origin` with `check=False`, validate a full lowercase SHA-1 commit, check for `estimator/__init__.py` or `estimator.py`, and never import `estimator`.

- [x] **Step 2: Add the CLI command**

Add `agades-pqc lattice-estimator-checkout-preflight` with `--estimator-source`, `--out`, `--policy`, and optional `--required-commit`. Verify the private-run policy before writing. Print a short summary and exit nonzero when the preflight is not ready.

- [x] **Step 3: Run GREEN**

Run:

```bash
uv run pytest tests/test_lattice_estimator_baseline_run.py tests/test_cli.py::test_lattice_estimator_checkout_preflight_command_writes_private_report -q
```

Expected: pass.

### Task 3: Policy, Release Audit, Docs, and Artifacts

**Files:**
- Modify: `src/agades_pqc_gym/integrations/private_run_policy.py`
- Modify: `src/agades_pqc_gym/integrations/release_audit.py`
- Modify: `tests/test_private_run_policy.py`
- Modify: `tests/test_release_audit.py`
- Modify: `docs/IMPLEMENT.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/STATUS.md`
- Regenerate: `docs/private_run_policy.json`
- Regenerate: `public/release_audit.json`
- Regenerate: `docs/release_status.json`
- Regenerate: `public/publication_preflight.json`

- [x] **Step 1: Add failing policy and release-audit tests**

Assert the private-run policy allows `agades-pqc lattice-estimator-checkout-preflight`, and release audit includes a blocking `lattice-estimator-checkout-preflight-boundary` check proving private output, no import, no estimator execution, commit-pin readiness, and no public/security claim.

- [x] **Step 2: Implement generators and docs**

Update the private-run policy generator, release audit, and public docs to describe the new preflight as private review evidence before real `--estimator-source` baseline runs.

- [x] **Step 3: Regenerate deterministic artifacts**

Run:

```bash
uv run agades-pqc private-run-policy --out docs/private_run_policy.json
uv run agades-pqc release-audit --out public/release_audit.json
uv run agades-pqc release-status --out docs/release_status.json
uv run agades-pqc publication-preflight --out public/publication_preflight.json
```

Expected: generated files match tests and keep external publication blocked.

### Task 4: Verification and Publication Hygiene

**Files:**
- Verify all modified files.

- [x] **Step 1: Full local verification**

Run:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
uv build
uv build prime_intellect/verifiers_environment
```

Expected: all pass.

- [x] **Step 2: Artifact and naming verification**

Run:

```bash
uv run agades-pqc private-run-policy-verify --policy docs/private_run_policy.json
uv run agades-pqc release-status-verify --status docs/release_status.json
uv run agades-pqc publication-preflight-verify --preflight public/publication_preflight.json
rg -n "<legacy Agades cryptanalysis/crypto naming pattern>" README.md docs hf nvidia prime_intellect src tests examples pyproject.toml
```

Expected: verifiers pass and `rg` returns no matches.
