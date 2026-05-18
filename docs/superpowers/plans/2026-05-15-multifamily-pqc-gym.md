# Agades PQC Gym Multi-Family Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the existing LWE-first MVP into `agades-pqc-gym`, a family-agnostic cryptanalysis workbench with `lattice` as the first implemented plugin and schema-only unsupported placeholders for other cryptographic families.

**Architecture:** Move the public package to `agades_pqc_gym`. Introduce generic `core` types (`TargetSpec`, `AttackPlan`, `AttackOperator`, `FamilyAdapter`, registry) and route all evaluation through family adapters. Preserve the current LWE/MLWE behavior inside `families/lattice`; non-lattice families validate structurally but return explicit `unsupported` evaluator results.

**Tech Stack:** Python 3.12, Pydantic, Typer, Rich, pytest, ruff, JSON/JSONL.

---

### Task 1: Write Multi-Family Contract Tests

**Files:**
- Create: `tests/test_core_schema.py`
- Create: `tests/test_family_registry.py`
- Create: `tests/test_lattice_adapter.py`
- Create: `tests/test_placeholder_adapters.py`
- Modify: existing CLI/cascade/report tests to import `agades_pqc_gym`.

- [ ] **Step 1: Add failing schema tests**

Add tests that import `TargetSpec`, `AttackPlan`, and `TargetFamily` from `agades_pqc_gym.core.attack_plan`, load `examples/attack_plans/lattice_primal_usvp_toy.json`, and assert `family == TargetFamily.LWE`.

- [ ] **Step 2: Add failing placeholder tests**

Add tests that load `examples/attack_plans/code_based_isd_placeholder.json` and assert CLI validation succeeds while cascade evaluation returns `evaluation_status == "unsupported"` and no time/memory estimate.

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_core_schema.py tests/test_family_registry.py tests/test_placeholder_adapters.py -q`

Expected: FAIL because `agades_pqc_gym` does not exist yet.

### Task 2: Rename Package And CLI

**Files:**
- Move: `src/agades_lwe_gym/` -> `src/agades_pqc_gym/`
- Modify: `pyproject.toml`
- Modify: `scripts/*.py`
- Modify: `examples/openevolve/evaluator.py`
- Modify: all tests.

- [ ] **Step 1: Rename package directory**

Use `git mv src/agades_lwe_gym src/agades_pqc_gym`.

- [ ] **Step 2: Update imports and console script**

Replace legacy package imports with `agades_pqc_gym`. Rename project metadata to `agades-pqc-gym` and console script to `agades-pqc`.

- [ ] **Step 3: Run tests**

Run: `uv run pytest -q`.

Expected: existing behavior passes again after imports are fixed.

### Task 3: Implement Core And Family Registry

**Files:**
- Create: `src/agades_pqc_gym/core/target.py`
- Create: `src/agades_pqc_gym/core/attack_plan.py`
- Create: `src/agades_pqc_gym/core/family_adapter.py`
- Create: `src/agades_pqc_gym/core/operators.py`
- Create: `src/agades_pqc_gym/core/registry.py`

- [ ] **Step 1: Implement generic schemas**

Implement `TargetFamily`, `SupportLevel`, `TargetSpec`, `AttackOperator`, `Constraints`, `Claims`, `Metadata`, and `AttackPlan`.

- [ ] **Step 2: Implement family adapter protocol**

Define `ValidationFinding`, `ReproductionResult`, and `FamilyAdapter` protocol.

- [ ] **Step 3: Implement adapter registry**

Add `FamilyRegistry` with default adapters and lookup by `TargetFamily`.

- [ ] **Step 4: Run core tests**

Run: `uv run pytest tests/test_core_schema.py tests/test_family_registry.py -q`.

Expected: PASS.

### Task 4: Implement Lattice And Placeholder Family Adapters

**Files:**
- Create/modify: `src/agades_pqc_gym/families/lattice/*`
- Create: `src/agades_pqc_gym/families/code_based/*`
- Create: `src/agades_pqc_gym/families/multivariate/*`
- Create: `src/agades_pqc_gym/families/hash_based/*`
- Create: `src/agades_pqc_gym/families/isogeny_historical/*`
- Modify: `src/agades_pqc_gym/evaluators/router.py`
- Modify: `src/agades_pqc_gym/evaluators/cascade.py`
- Modify: `src/agades_pqc_gym/evaluators/fitness.py`

- [ ] **Step 1: Move lattice-specific operator checks into `families/lattice`**

Lattice supports LWE/MLWE fully in the MVP. NTRU/SIS remain schema/placeholder until real mappings are reviewed.

- [ ] **Step 2: Add placeholder adapters**

Code-based, multivariate, hash-based, and historical isogeny adapters must validate schemas and return explicit unsupported estimator results.

- [ ] **Step 3: Route cascade through adapter registry**

The cascade must never call a lattice estimator for non-lattice families.

- [ ] **Step 4: Run family tests**

Run: `uv run pytest tests/test_lattice_adapter.py tests/test_placeholder_adapters.py tests/test_cascade.py -q`.

Expected: PASS.

### Task 5: Update Examples, Benchmarks, Docs, And OSS Surfaces

**Files:**
- Rename: `benchmarks/toy_lwe/` -> `benchmarks/lattice_toy_lwe/`
- Rename: `benchmarks/mlkem_like/` -> `benchmarks/lattice_mlkem_like/`
- Create schema-only benchmark folders for code-based, multivariate, hash-based, and isogeny historical.
- Rename LWE example files to `lattice_*`.
- Modify: `README.md`, `docs/ARCHITECTURE.md`, `docs/FAMILY_ADAPTERS.md`, `docs/STATUS.md`, `docs/EVAL_LOG.md`, `hf/*`, `prime_intellect/*`.
- Add: `docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md`.

- [ ] **Step 1: Rename examples and benchmark directories**

Use `git mv` for tracked files and update tests/README commands.

- [ ] **Step 2: Add non-lattice schema-only examples**

Add code-based ISD, multivariate MinRank, hash-based bound-check, and historical isogeny placeholder AttackPlans.

- [ ] **Step 3: Update public docs**

Document Agades PQC Gym as the product, LWE Strategy Gym as first vertical, Prime Intellect as verifier/environment surface, Hugging Face as toy dataset/Space surface, and NVIDIA as startup/agent-eval ecosystem target.

- [ ] **Step 4: Run documentation smoke commands**

Run: `uv run agades-pqc --help` and `uv run agades-pqc benchmark benchmarks/lattice_toy_lwe --out runs/v3_toy_benchmark.jsonl`.

Expected: PASS.

### Task 6: Final Verification And Publish

**Files:**
- Modify: `docs/STATUS.md`
- Modify: `reports/AGADES_PQC_GYM_MVP_REPORT.md`

- [ ] **Step 1: Run full verification**

Run:

```bash
uv run pytest -q
uv run ruff check .
uv run agades-pqc --help
uv run agades-pqc validate examples/attack_plans/lattice_primal_usvp_toy.json
uv run agades-pqc validate examples/attack_plans/code_based_isd_placeholder.json
uv run agades-pqc evaluate examples/attack_plans/code_based_isd_placeholder.json --out runs/v3_unsupported_trace.jsonl
uv run agades-pqc benchmark benchmarks/lattice_toy_lwe --out runs/v3_toy_benchmark.jsonl
uv run agades-pqc export-public runs/v3_toy_benchmark.jsonl --out public/v3_toy_benchmark_public.jsonl
uv run agades-pqc report runs/v3_toy_benchmark.jsonl --out reports/v3_toy_benchmark_report.md
```

- [ ] **Step 2: Commit and push**

Commit on `codex/multifamily-architecture` and push. Rename the GitHub repository to `AgadesTech/agades-pqc-gym` only after the branch is verified and the user-visible project is internally consistent.
