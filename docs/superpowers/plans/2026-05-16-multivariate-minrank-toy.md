# Multivariate MinRank Toy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded `MULTIVARIATE` toy MinRank verification path and publish it through the JSON-only OSS surfaces without making UOV/MAYO/Rainbow or deployed-parameter claims.

**Architecture:** Extend the multivariate plugin beyond the current MQ toy path with `minrank_attack` using `model="toy_minrank_search"`. The estimator reports deterministic exhaustive coefficient-search plumbing for tiny public GF(2) matrices only. A separate fixture verifier checks one strict public MinRank fixture and mirrors it as package data for installed Prime/HF verifier environments.

**Tech Stack:** Python, Pydantic fixture models, pytest, JSON AttackPlans, Agades CLI artifact generators.

---

### Task 1: Write RED Tests

**Files:**
- Modify: `tests/test_multivariate_adapter.py`
- Add: `tests/test_multivariate_minrank_solver.py`
- Modify: `tests/test_public_verifier.py`
- Modify: `tests/test_huggingface_dataset_bundle.py`
- Modify: `tests/test_huggingface_space_manifest.py`
- Modify: `tests/test_prime_verifiers_env.py`
- Modify: `tests/test_family_support_matrix.py`
- Modify: `tests/test_public_benchmark_manifest.py`
- Modify: `tests/test_publication_manifest.py`
- Modify: `tests/test_nvidia_accelerator_manifest.py`
- Modify: `tests/test_release_audit.py`

- [x] Add a behavior test for `minrank_attack:toy_minrank_search` scoring with explicit expected time/memory bits and raw model fields.
- [x] Add validation tests requiring `toy_minrank_search`, `toy_minrank_exhaustive_search_model`, and positive matrix dimensions/target rank bounds.
- [x] Add a fixture test proving the public MinRank fixture solves uniquely and the package fixture mirrors the benchmark fixture.
- [x] Add public verifier, HF dataset/Space, Prime, family-support, public-benchmark, publication, NVIDIA, and release-audit expectations for one new valid public example/task and one new public run bundle.
- [x] Run targeted tests and confirm they fail for the missing MinRank support and artifacts.

### Task 2: Implement MinRank Support

**Files:**
- Modify: `src/agades_pqc_gym/families/multivariate/mq_estimator.py`
- Modify: `src/agades_pqc_gym/families/multivariate/adapter.py`
- Add: `src/agades_pqc_gym/families/multivariate/minrank_solver.py`
- Add: `benchmarks/multivariate_toy_minrank/fixtures/toy_minrank_gf2_m3_r0_fixture.json`
- Add: `src/agades_pqc_gym/families/multivariate/fixtures/toy_minrank_gf2_m3_r0_fixture.json`

- [x] Add constants and deterministic estimate support for `toy_minrank_search`.
- [x] Add variant-specific applicability validation and fixture path scoping.
- [x] Add a no-execution GF(2) MinRank solver with strict public/no-claim fixture schema.

### Task 3: Add Public OSS Artifacts

**Files:**
- Add: `examples/attack_plans/multivariate_minrank_toy.json`
- Add: `prime_intellect/verifiers_environment/data/multivariate_minrank_toy.json`
- Add: `benchmarks/multivariate_toy_minrank/README.md`
- Add: `benchmarks/multivariate_toy_minrank/toy_minrank_gf2_m3_r0_verify.json`
- Add: `examples/public_runs/multivariate_toy_minrank_v0/*`
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
- [ ] Commit, push, and verify PR checks.
