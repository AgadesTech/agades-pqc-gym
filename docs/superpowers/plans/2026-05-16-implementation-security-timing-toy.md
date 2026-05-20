# Implementation-Security Timing Toy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded JSON-only `IMPLEMENTATION_SECURITY` toy timing check and publish it through the public OSS surfaces without executing binaries or making constant-time/security claims.

**Architecture:** Extend the implementation-security plugin beyond KAT digest plumbing with `constant_time_check` using `model="toy_timing_welch_t_check"` and `tool="toy_welch_timing_check"`. The evaluator computes a bounded Welch-style t statistic from small public cycle-count arrays supplied in JSON. A separate fixture verifier checks one strict public timing fixture and mirrors it as package data for installed Prime/HF verifier environments.

**Tech Stack:** Python, Pydantic fixture models, pytest, JSON AttackPlans, Agades CLI artifact generators.

---

### Task 1: Write RED Tests

**Files:**
- Modify: `tests/test_implementation_security_adapter.py`
- Add: `tests/test_implementation_security_timing_fixture.py`
- Modify: `tests/test_public_verifier.py`
- Modify: `tests/test_huggingface_dataset_bundle.py`
- Modify: `tests/test_huggingface_space_manifest.py`
- Modify: `tests/test_prime_verifiers_env.py`
- Modify: `tests/test_family_support_matrix.py`
- Modify: `tests/test_public_benchmark_manifest.py`
- Modify: `tests/test_publication_manifest.py`
- Modify: `tests/test_nvidia_accelerator_manifest.py`
- Modify: `tests/test_public_release_cards.py`
- Modify: `tests/test_public_ledger.py`
- Modify: `tests/test_release_audit.py`

- [x] Add a behavior test for `constant_time_check:toy_timing_welch_t_check` scoring with explicit expected t statistic, time bits, memory bits, and raw model fields.
- [x] Add validation tests requiring `toy_timing_leakage_model`, bounded public cycle arrays, and no live artifact parameters.
- [x] Add a fixture test proving the public timing fixture verifies and the package fixture mirrors the benchmark fixture.
- [x] Add public verifier, HF dataset/Space, Prime, family-support, public-benchmark, publication, NVIDIA, and release-audit expectations for one new valid public example/task and one new public run bundle.
- [x] Run targeted tests and confirm they fail for the missing timing support and artifacts.

### Task 2: Implement Timing Support

**Files:**
- Modify: `src/agades_pqc_gym/families/implementation_security/kat_estimator.py`
- Modify: `src/agades_pqc_gym/families/implementation_security/adapter.py`
- Add: `src/agades_pqc_gym/families/implementation_security/timing_fixture.py`
- Add: `benchmarks/implementation_security_toy_timing/fixtures/toy_timing_welch_fixture.json`
- Add: `src/agades_pqc_gym/families/implementation_security/fixtures/toy_timing_welch_fixture.json`

- [x] Add constants and deterministic estimate support for `toy_timing_welch_t_check`.
- [x] Add operator-specific applicability validation and fixture path scoping for timing fixtures.
- [x] Add a no-execution timing fixture verifier with strict public/no-claim schema.

### Task 3: Add Public OSS Artifacts

**Files:**
- Add: `examples/attack_plans/implementation_security_timing_toy.json`
- Add: `prime_intellect/verifiers_environment/data/implementation_security_timing_toy.json`
- Add: `benchmarks/implementation_security_toy_timing/README.md`
- Add: `benchmarks/implementation_security_toy_timing/toy_timing_welch_verify.json`
- Add: `examples/public_runs/implementation_security_toy_timing_v0/*`
- Regenerate: `hf/dataset/*`
- Regenerate: `hf/space_manifest.json`
- Regenerate: `prime_intellect/verifiers_environment/prime_manifest.json`
- Regenerate: `docs/family_support_matrix.json`
- Regenerate: `docs/publication_manifest.json`
- Regenerate: `docs/public_benchmark_manifest.json`
- Regenerate: `nvidia/accelerator_manifest.json`
- Regenerate: `public/release_audit.json`
- Modify: `hf/dataset_card.md`
- Modify: `hf/benchmark_card.md`
- Modify: `prime_intellect/environment_card.md`
- Modify: `reports/AGADES_PQC_GYM_MVP_REPORT.md`
- Modify: `docs/HUGGINGFACE_RELEASE_PLAN.md`
- Modify: `docs/PRIME_INTELLECT_RELEASE_PLAN.md`
- Modify: `docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md`
- Modify: `docs/FAMILY_ADAPTERS.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/STATUS.md`

- [x] Add the public AttackPlan and benchmark seed using the fixture.
- [x] Generate the public run bundle and all checked-in release artifacts.
- [x] Update public cards, release plans, architecture docs, family docs, and status counts.

### Task 4: Verify and Publish Branch

- [x] Run targeted tests.
- [x] Run full tests, Ruff, `git diff --check`, forbidden-name scan, release audit, and package builds.
- [x] Commit, push, and verify PR checks.
