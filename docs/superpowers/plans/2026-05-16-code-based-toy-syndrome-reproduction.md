# Code-Based Toy Syndrome Reproduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reviewed, bounded public reproduction harness for the existing `CODE_BASED` toy ISD surface by solving one tiny binary syndrome-decoding fixture.

**Architecture:** Keep the Prange toy cost estimator unchanged and add a separate family-specific solver for fixtures under `benchmarks/code_based_toy_isd/`. The adapter should return `instance_solved` only when an explicit public fixture is requested, the solved instance matches the plan target, and the fixture carries `security_claim=false`.

**Tech Stack:** Python 3.12, Pydantic, pytest, Typer CLI/public benchmark artifacts.

---

### Task 1: RED Tests For Code-Based Reproduction

**Files:**
- Create: `tests/test_code_based_syndrome_solver.py`
- Modify: `tests/test_code_based_adapter.py`

- [ ] **Step 1: Add a solver contract test**

Add a test that imports `solve_toy_syndrome_fixture`, loads `benchmarks/code_based_toy_isd/fixtures/toy_syndrome_31_16_w3_fixture.json`, and asserts it recovers the unique public weight-3 error vector `[0, 3, 9]`, reports `candidate_count == 4495`, and keeps `security_claim is False`.

- [ ] **Step 2: Add an adapter reproduction test**

Add a test that builds the existing toy Prange plan with `require_reproducibility_on_downscaled_instances=True` and `downscaled_reproduction_fixture="benchmarks/code_based_toy_isd/fixtures/toy_syndrome_31_16_w3_fixture.json"`, then asserts cascade metrics return `reproduction_status == "instance_solved"` and `reproducibility_score == 0.4`.

- [ ] **Step 3: Run RED tests**

Run: `PYTHONPATH=src uv run pytest tests/test_code_based_syndrome_solver.py tests/test_code_based_adapter.py::test_code_based_toy_reproduction_solves_public_syndrome_fixture -q`

Expected: FAIL because the solver module and adapter reproduction path do not exist yet.

### Task 2: Implement Bounded Fixture Solver

**Files:**
- Create: `src/agades_pqc_gym/families/code_based/syndrome_solver.py`
- Create: `benchmarks/code_based_toy_isd/fixtures/toy_syndrome_31_16_w3_fixture.json`

- [ ] **Step 1: Add schema-versioned fixture and solution models**

Implement a Pydantic fixture schema with binary parity-check matrix rows, binary syndrome, expected error positions, `public=true`, and `security_claim=false`.

- [ ] **Step 2: Add bounded exhaustive solve**

Enumerate `itertools.combinations(range(n), w)`, cap total candidates, compute binary syndromes mod 2, require a unique matching error vector, and return a solution model.

- [ ] **Step 3: Verify solver test passes**

Run: `PYTHONPATH=src uv run pytest tests/test_code_based_syndrome_solver.py -q`

Expected: PASS.

### Task 3: Wire Adapter Reproduction

**Files:**
- Modify: `src/agades_pqc_gym/families/code_based/adapter.py`
- Modify: `docs/FAMILY_ADAPTERS.md`
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Remove the blanket reproduction rejection for explicit public fixtures**

Keep rejecting reproduction requests without a fixture. For explicit relative fixtures under `benchmarks/code_based_toy_isd/`, call the solver.

- [ ] **Step 2: Return `instance_solved` only for matching public no-claim fixtures**

Validate target name, `n`, `k`, `w`, `public`, and `security_claim=false` before returning a positive reproduction result.

- [ ] **Step 3: Verify adapter test passes**

Run: `PYTHONPATH=src uv run pytest tests/test_code_based_adapter.py -q`

Expected: PASS.

### Task 4: Regenerate Public Artifacts And Verify

**Files:**
- Modify generated public bundle/checksum artifacts for `code_based_toy_isd_v0`
- Modify generated HF/publication/family/release manifests as needed

- [ ] **Step 1: Regenerate code-based benchmark bundle**

Run:

```bash
PYTHONPATH=src uv run agades-pqc benchmark benchmarks/code_based_toy_isd --out runs/code_based_toy_isd.jsonl
PYTHONPATH=src uv run agades-pqc public-bundle runs/code_based_toy_isd.jsonl --out examples/public_runs/code_based_toy_isd_v0
```

- [ ] **Step 2: Regenerate OSS manifests**

Run the existing checked-in manifest generation commands for family support, Hugging Face dataset, public benchmark manifest, publication manifest, Prime manifest, NVIDIA manifest, and release audit.

- [ ] **Step 3: Verify**

Run:

```bash
PYTHONPATH=src uv run pytest -q
PYTHONPATH=src uv run ruff check .
PYTHONPATH=src uv run agades-pqc public-benchmark-verify --manifest docs/public_benchmark_manifest.json
PYTHONPATH=src uv run agades-pqc release-audit --out public/release_audit.json
git diff --check
```
