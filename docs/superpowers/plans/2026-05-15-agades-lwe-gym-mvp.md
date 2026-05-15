# Agades LWE Strategy Gym MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible MVP workbench for typed LWE/MLWE attack plans, deterministic estimator-backed evaluation, trace redaction, reporting, and public release artifacts.

**Architecture:** The project is a Python 3.11+ package with a narrow Pydantic DSL at the center. Validation, estimation, trace logging, OpenEvolve integration, and reporting are separated into focused modules so real estimator support can replace mock output without changing public interfaces.

**Tech Stack:** Python 3.11+, Pydantic, Typer, Rich, pytest, ruff, JSON/JSONL, YAML for paper cards.

---

### Task 1: Repository Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `.gitignore`
- Create: `.github/workflows/ci.yml`
- Create: `docs/PLAN.md`
- Create: `docs/IMPLEMENT.md`
- Create: `docs/STATUS.md`
- Create: `docs/EVAL_LOG.md`

- [ ] **Step 1: Write the initial smoke test**

```python
def test_package_imports():
    import agades_lwe_gym

    assert agades_lwe_gym.__version__ == "0.1.0"
```

- [ ] **Step 2: Run the smoke test to verify it fails**

Run: `uv run pytest tests/test_package.py::test_package_imports -q`

Expected: FAIL because the package does not exist yet.

- [ ] **Step 3: Add package metadata and the minimal package**

Create `pyproject.toml` with project metadata, runtime dependencies, pytest config, and ruff config. Create `src/agades_lwe_gym/__init__.py` exporting `__version__`.

- [ ] **Step 4: Run the smoke test to verify it passes**

Run: `uv run pytest tests/test_package.py::test_package_imports -q`

Expected: PASS.

### Task 2: DSL And Validators

**Files:**
- Create: `src/agades_lwe_gym/dsl/schema.py`
- Create: `src/agades_lwe_gym/dsl/operators.py`
- Create: `src/agades_lwe_gym/dsl/examples.py`
- Create: `src/agades_lwe_gym/validators/static.py`
- Create: `src/agades_lwe_gym/validators/assumptions.py`
- Create: `src/agades_lwe_gym/validators/consistency.py`
- Create: `examples/attack_plans/*.json`
- Create: `tests/test_schema.py`
- Create: `tests/test_validators.py`

- [ ] **Step 1: Write failing tests for valid and invalid AttackPlan JSON**

```python
def test_valid_primal_plan_loads():
    plan = AttackPlan.model_validate_json(Path("examples/attack_plans/primal_usvp_toy.json").read_text())
    assert plan.attack_plan_id == "primal_usvp_toy_v1"
```

- [ ] **Step 2: Run the tests to verify missing schema failure**

Run: `uv run pytest tests/test_schema.py -q`

Expected: FAIL because `AttackPlan` is not implemented.

- [ ] **Step 3: Implement Pydantic models and validation helpers**

Implement finite operator names, target distributions, constraints, claims, metadata, validation result types, and graceful validation errors.

- [ ] **Step 4: Verify schema and validator tests pass**

Run: `uv run pytest tests/test_schema.py tests/test_validators.py -q`

Expected: PASS.

### Task 3: Evaluator Suite

**Files:**
- Create: `src/agades_lwe_gym/evaluators/base.py`
- Create: `src/agades_lwe_gym/evaluators/mock_estimator.py`
- Create: `src/agades_lwe_gym/evaluators/lattice_estimator.py`
- Create: `src/agades_lwe_gym/evaluators/cache.py`
- Create: `src/agades_lwe_gym/evaluators/fitness.py`
- Create: `src/agades_lwe_gym/evaluators/cascade.py`
- Create: `tests/test_mock_estimator.py`
- Create: `tests/test_fitness.py`
- Create: `tests/test_cascade.py`

- [ ] **Step 1: Write failing tests for deterministic mock estimates and cascade metrics**
- [ ] **Step 2: Run evaluator tests and confirm missing implementation failures**
- [ ] **Step 3: Implement estimator interfaces, mock estimator, real adapter availability check, fitness, and cascade**
- [ ] **Step 4: Run evaluator tests to green**

### Task 4: Traces, Redaction, Reporting

**Files:**
- Create: `src/agades_lwe_gym/traces/schema.py`
- Create: `src/agades_lwe_gym/traces/writer.py`
- Create: `src/agades_lwe_gym/traces/redaction.py`
- Create: `src/agades_lwe_gym/reporting/markdown.py`
- Create: `src/agades_lwe_gym/reporting/report.py`
- Create: `tests/test_trace_redaction.py`
- Create: `tests/test_reporting.py`

- [ ] **Step 1: Write failing tests for JSONL trace writing, private-field redaction, and required report sections**
- [ ] **Step 2: Run trace/report tests and confirm failures**
- [ ] **Step 3: Implement trace schema, writer, redactor, and Markdown report generator**
- [ ] **Step 4: Run trace/report tests to green**

### Task 5: CLI, Scripts, OpenEvolve Adapter, And Artifacts

**Files:**
- Create: `src/agades_lwe_gym/cli.py`
- Create: `scripts/run_eval.py`
- Create: `scripts/run_benchmark.py`
- Create: `scripts/generate_report.py`
- Create: `scripts/export_public_trace.py`
- Create: `examples/openevolve/evaluator.py`
- Create: `examples/openevolve/config.yaml`
- Create: `benchmarks/**`
- Create: `hf/**`
- Create: `prime_intellect/**`
- Create: collaboration docs under `docs/`

- [ ] **Step 1: Write failing CLI smoke tests for validation, evaluation, trace export, and report generation**
- [ ] **Step 2: Run CLI tests and confirm failures**
- [ ] **Step 3: Implement CLI commands and script wrappers**
- [ ] **Step 4: Add docs, release cards, benchmarks, and collaboration briefs**
- [ ] **Step 5: Run `uv run pytest -q`, `uv run ruff check .`, and an end-to-end toy smoke run**

### Task 6: GitHub Publication

**Files:**
- Modify: repository metadata only

- [ ] **Step 1: Confirm GitHub organization access with `gh api orgs/AgadesTech`**
- [ ] **Step 2: Create `AgadesTech/agades-lwe-gym` only if it does not already exist**
- [ ] **Step 3: Add `origin`, push `main`, and document any permission failure in `docs/STATUS.md`**

