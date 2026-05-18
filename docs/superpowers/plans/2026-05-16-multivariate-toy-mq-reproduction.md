# Multivariate Toy MQ Reproduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reviewed, bounded public reproduction harness for the existing `MULTIVARIATE` toy MQ surface by solving one tiny binary MQ fixture.

**Architecture:** Keep the existing `GF(16)` MQ cost estimator as estimator-only evidence. Add a separate `GF(2)` fixture solver for explicit public fixtures under `benchmarks/multivariate_toy_mq/fixtures/`. The adapter should return `instance_solved` only when a plan requests the fixture, the solved instance matches the target shape, and the fixture declares `public=true` plus `security_claim=false`.

**Tech Stack:** Python 3.12, Pydantic, pytest, Typer CLI/public benchmark artifacts.

---

### Task 1: RED Tests For Multivariate Reproduction

**Files:**
- Create: `tests/test_multivariate_mq_solver.py`
- Modify: `tests/test_multivariate_adapter.py`

- [x] **Step 1: Add a solver contract test**

Add a test that imports `solve_toy_mq_fixture`, loads `benchmarks/multivariate_toy_mq/fixtures/toy_mq_gf2_v6_e4_fixture.json`, and asserts it recovers the unique public binary assignment `[1, 0, 1, 1, 0, 1]`, reports `assignment_count == 64`, and keeps `security_claim is False`.

- [x] **Step 2: Add an adapter reproduction test**

Add a test that builds a tiny `GF(2)` toy MQ plan with `require_reproducibility_on_downscaled_instances=True` and `downscaled_reproduction_fixture="benchmarks/multivariate_toy_mq/fixtures/toy_mq_gf2_v6_e4_fixture.json"`, then asserts cascade metrics return `reproduction_status == "instance_solved"` and `reproducibility_score == 0.4`.

- [x] **Step 3: Add a fixture scope test**

Add a test that rejects reproduction fixture paths outside `benchmarks/multivariate_toy_mq/fixtures/`.

- [x] **Step 4: Run RED tests**

Run:

```bash
PYTHONPATH=src uv run pytest tests/test_multivariate_mq_solver.py tests/test_multivariate_adapter.py::test_multivariate_toy_reproduction_solves_public_mq_fixture tests/test_multivariate_adapter.py::test_multivariate_toy_reproduction_fixture_must_stay_in_fixture_dir -q
```

Expected: FAIL because the solver module, fixture, and adapter reproduction path do not exist yet.

### Task 2: Implement Bounded Binary MQ Fixture Solver

**Files:**
- Create: `src/agades_pqc_gym/families/multivariate/mq_solver.py`
- Create: `benchmarks/multivariate_toy_mq/fixtures/toy_mq_gf2_v6_e4_fixture.json`

- [x] **Step 1: Add schema-versioned fixture and solution models**

Implement a Pydantic fixture schema for binary MQ equations with `field="GF(2)"`, polynomial constants, binary linear coefficients, quadratic terms, expected solution, `public=true`, and `security_claim=false`.

- [x] **Step 2: Add bounded exhaustive solve**

Enumerate all binary assignments, cap total assignments, evaluate all equations over `GF(2)`, require a unique satisfying assignment, and return a typed solution model.

- [x] **Step 3: Verify solver test passes**

Run:

```bash
PYTHONPATH=src uv run pytest tests/test_multivariate_mq_solver.py -q
```

Expected: PASS.

### Task 3: Wire Adapter Reproduction

**Files:**
- Modify: `src/agades_pqc_gym/families/multivariate/adapter.py`
- Modify: `docs/FAMILY_ADAPTERS.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Replace blanket reproduction rejection for explicit public fixtures**

Keep rejecting reproduction requests without a fixture. For explicit relative fixtures under `benchmarks/multivariate_toy_mq/fixtures/`, call the solver.

- [x] **Step 2: Return `instance_solved` only for matching public no-claim fixtures**

Validate target name, variables, equations, field notation, `public`, and `security_claim=false` before returning a positive reproduction result.

- [x] **Step 3: Verify adapter tests pass**

Run:

```bash
PYTHONPATH=src uv run pytest tests/test_multivariate_adapter.py -q
```

Expected: PASS.

### Task 4: Regenerate Public Artifacts And Verify

**Files:**
- Modify generated public bundle/checksum artifacts for `multivariate_toy_mq_v0`
- Modify generated HF/publication/family/release manifests as needed

- [x] **Step 1: Add benchmark plan and regenerate multivariate bundle**

Run:

```bash
PYTHONPATH=src uv run agades-pqc benchmark benchmarks/multivariate_toy_mq --out runs/multivariate_toy_mq.jsonl
PYTHONPATH=src uv run agades-pqc public-bundle runs/multivariate_toy_mq.jsonl --out examples/public_runs/multivariate_toy_mq_v0
```

- [x] **Step 2: Regenerate OSS manifests**

Run the existing checked-in manifest generation commands for family support, Hugging Face dataset, public benchmark manifest, publication manifest, Prime manifest, NVIDIA manifest, and release audit.

- [x] **Step 3: Verify**

Run:

```bash
PYTHONPATH=src uv run pytest -q
PYTHONPATH=src uv run ruff check .
PYTHONPATH=src uv run agades-pqc public-benchmark-verify --manifest docs/public_benchmark_manifest.json
PYTHONPATH=src uv run agades-pqc release-audit --out public/release_audit.json
git diff --check
uv build
(cd prime_intellect/verifiers_environment && uv build)
```
