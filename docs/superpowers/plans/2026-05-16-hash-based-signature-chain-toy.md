# Hash-Based Signature Chain Toy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded `HASH_BASED` toy signature-chain verification path and publish it through the JSON-only OSS surfaces without making security claims.

**Architecture:** Extend the hash-based plugin with a reviewed `hash_signature_verification` operator using a `toy_wots_chain_verify` model. The estimator reports deterministic toy chain-verification work only; a separate fixture verifier checks a small public SHAKE256 chain fixture for reproducibility. The public verifier, Prime environment, Hugging Face dataset/Space, public benchmark bundle, publication manifest, and release audit must stay generated and synchronized.

**Tech Stack:** Python, Pydantic fixture models, pytest, JSON AttackPlans, Agades CLI artifact generators.

---

### Task 1: Write RED Tests

**Files:**
- Modify: `tests/test_hash_based_adapter.py`
- Add: `tests/test_hash_based_signature_fixture.py`
- Modify: `tests/test_public_verifier.py`
- Modify: `tests/test_huggingface_dataset_bundle.py`
- Modify: `tests/test_huggingface_space_manifest.py`
- Modify: `tests/test_prime_verifiers_env.py`
- Modify: `tests/test_family_support_matrix.py`
- Modify: `tests/test_public_benchmark_manifest.py`
- Modify: `tests/test_release_audit.py`

- [x] Add a behavior test for `hash_signature_verification:toy_wots_chain_verify` scoring with explicit expected time/memory bits and raw model fields.
- [x] Add validation tests requiring positive `chain_count`, positive `max_chain_steps`, and `toy_hash_signature_chain_model`.
- [x] Add a fixture test proving the public signature chain fixture verifies and the package fixture mirrors the benchmark fixture.
- [x] Add public verifier, HF dataset/Space, Prime, family-support, public-benchmark, and release-audit expectations for one new valid public example/task and one new public run bundle.
- [x] Run targeted tests and confirm they fail for the missing operator, fixture verifier, example, bundle, and regenerated artifacts.

### Task 2: Implement Signature Chain Support

**Files:**
- Modify: `src/agades_pqc_gym/core/operators.py`
- Modify: `src/agades_pqc_gym/families/hash_based/bound_estimator.py`
- Modify: `src/agades_pqc_gym/families/hash_based/adapter.py`
- Add: `src/agades_pqc_gym/families/hash_based/signature_fixture.py`
- Add: `benchmarks/hash_based_toy_signature/fixtures/toy_hash_signature_chain_24_fixture.json`
- Add: `src/agades_pqc_gym/families/hash_based/fixtures/toy_hash_signature_chain_24_fixture.json`

- [x] Add `hash_signature_verification` to the hash-based operator surface with required `signature_model`.
- [x] Add deterministic toy estimate support for `toy_wots_chain_verify`.
- [x] Add variant-specific applicability validation and fixture path scoping.
- [x] Add a no-execution SHAKE256 chain verifier with strict public/no-claim fixture schema.

### Task 3: Add Public OSS Artifacts

**Files:**
- Add: `examples/attack_plans/hash_based_signature_toy.json`
- Add: `prime_intellect/verifiers_environment/data/hash_based_signature_toy.json`
- Add: `benchmarks/hash_based_toy_signature/README.md`
- Add: `benchmarks/hash_based_toy_signature/toy_hash_signature_chain_24_verify.json`
- Add: `examples/public_runs/hash_based_toy_signature_v0/*`
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
- Modify: `docs/STATUS.md`

- [x] Add the public AttackPlan and benchmark seed using the fixture.
- [x] Generate the public run bundle and all checked-in release artifacts.
- [x] Update public cards, release plans, and status counts to mention the new bundle.

### Task 4: Verify and Publish Branch

- [x] Run targeted tests.
- [x] Run full tests, Ruff, `git diff --check`, forbidden-name scan, release audit, and package builds.
- [x] Commit, push, and verify PR checks.
