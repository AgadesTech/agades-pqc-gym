# Code-Based Second Syndrome Fixture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second bounded public code-based syndrome-decoding reproduction fixture so the code-based plugin is not represented by a single solved instance.

**Architecture:** Reuse the reviewed `toy-code-based-isd-estimator` and `solve_toy_syndrome_fixture` path. Add a smaller `toy_syndrome_15_7_w2` public JSON fixture with a unique weight-2 solution, a public AttackPlan that requests reproduction, and regenerate the existing `code_based_toy_isd_v0` bundle with two accepted records.

**Tech Stack:** Python, Pydantic fixture models, pytest, JSON AttackPlans, Agades CLI artifact generators.

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_code_based_syndrome_solver.py`
- Modify: `tests/test_code_based_adapter.py`
- Modify: `tests/test_public_verifier.py`
- Modify: `tests/test_huggingface_dataset_bundle.py`
- Modify: `tests/test_huggingface_space_manifest.py`
- Modify: `tests/test_prime_verifiers_env.py`
- Modify: `tests/test_public_benchmark_manifest.py`
- Modify: `tests/test_public_ledger.py`
- Modify: `tests/test_release_audit.py`

- [x] Add a solver test for `benchmarks/code_based_toy_isd/fixtures/toy_syndrome_15_7_w2_fixture.json` expecting a unique solution `[2, 11]` and `candidate_count == 105`.
- [x] Add an adapter reproduction test for a public `toy_syndrome_15_7_w2` Prange AttackPlan with `reproduction_status == "instance_solved"`.
- [x] Add public verifier and ecosystem count expectations for one new public AttackPlan row and one additional record in `code_based_toy_isd_v0`.
- [x] Run targeted tests and confirm they fail because the fixture, example, and regenerated artifacts do not exist yet.

### Task 2: Public Fixture and Example

**Files:**
- Add: `benchmarks/code_based_toy_isd/fixtures/toy_syndrome_15_7_w2_fixture.json`
- Add: `src/agades_pqc_gym/families/code_based/fixtures/toy_syndrome_15_7_w2_fixture.json`
- Add: `benchmarks/code_based_toy_isd/toy_syndrome_15_7_w2.json`
- Add: `examples/attack_plans/code_based_prange_toy_n15.json`
- Add: `prime_intellect/verifiers_environment/data/code_based_prange_toy_n15.json`

- [x] Add the strict public fixture and mirror it as package data.
- [x] Add a benchmark AttackPlan that requests reproduction through the new fixture.
- [x] Add the public AttackPlan and Prime packaged task with matching JSON.

### Task 3: Regenerate Artifacts

**Files:**
- Regenerate: `examples/public_runs/code_based_toy_isd_v0/*`
- Regenerate: `hf/dataset/*`
- Regenerate: `hf/space_manifest.json`
- Regenerate: `prime_intellect/verifiers_environment/prime_manifest.json`
- Regenerate: `docs/family_support_matrix.json`
- Regenerate: `docs/public_benchmark_manifest.json`
- Regenerate: `docs/publication_manifest.json`
- Regenerate: `nvidia/accelerator_manifest.json`
- Regenerate: `public/release_audit.json`
- Modify: `docs/STATUS.md`

- [x] Generate the updated code-based public run bundle with two records.
- [x] Regenerate HF, Prime, NVIDIA, family support, publication, public benchmark, and audit artifacts.
- [x] Update status counts and code-based reproduction wording.

### Task 4: Verify and Publish Branch

- [x] Run targeted tests.
- [x] Run full tests, Ruff, `git diff --check`, forbidden-name scan, release audit, public benchmark verification, and package builds.
- [x] Commit, push, and verify PR checks.
