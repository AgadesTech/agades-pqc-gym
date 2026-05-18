# Code-Based Stern Toy Variant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second reviewed bounded code-based ISD toy variant, `stern_toy`, and expose it through the public JSON-only OSS surfaces without making security claims.

**Architecture:** Keep the `CODE_BASED` plugin limited to `toy_` syndrome-decoding targets. Extend the existing `information_set_decoding` operator with a reviewed `stern_toy` variant parameterized by a small integer `p`. Validate variant-specific assumptions and bounds before estimation. The model is a deterministic toy partition/collision work-factor approximation for evaluator plumbing only, separate from the existing `prange_toy` baseline.

**Tech Stack:** Python, pytest, JSON AttackPlan examples, Hugging Face/Prime generated manifests, release audit.

---

### Task 1: Write RED Tests

**Files:**
- Modify: `tests/test_code_based_adapter.py`
- Modify: `tests/test_public_verifier.py`
- Modify: `tests/test_huggingface_dataset_bundle.py`
- Modify: `tests/test_huggingface_space_manifest.py`
- Modify: `tests/test_prime_verifiers_env.py`
- Modify: `tests/test_release_audit.py`

- [x] Add a behavior test for `stern_toy` scoring with explicit expected time/memory bits and raw model fields.
- [x] Add validation tests for missing/invalid Stern `p` parameters and missing Stern assumptions.
- [x] Add public verifier coverage for `examples/attack_plans/code_based_stern_toy.json`.
- [x] Update HF, Space, Prime, and release-audit expectations for one new valid public example/task.
- [x] Run targeted tests and confirm they fail for the missing implementation and artifacts.

### Task 2: Implement Stern Toy Variant

**Files:**
- Modify: `src/agades_pqc_gym/families/code_based/isd_estimator.py`
- Modify: `src/agades_pqc_gym/families/code_based/adapter.py`
- Add: `examples/attack_plans/code_based_stern_toy.json`
- Add: `prime_intellect/verifiers_environment/data/code_based_stern_toy.json`

- [x] Add `stern_toy` constants and deterministic toy estimate formula.
- [x] Add variant-specific applicability validation.
- [x] Add public AttackPlan example and packaged Prime task JSON.

### Task 3: Regenerate Public Artifacts

**Files:**
- Regenerate: `hf/dataset/*`
- Regenerate: `hf/space_manifest.json`
- Regenerate: `prime_intellect/verifiers_environment/prime_manifest.json`
- Regenerate: `nvidia/accelerator_manifest.json`
- Regenerate: `docs/publication_manifest.json`
- Regenerate: `public/release_audit.json`
- Modify: `docs/STATUS.md`

- [x] Run checked-in generator commands.
- [x] Document the new variant and updated public task/example counts.

### Task 4: Verify

- [x] Run targeted tests.
- [x] Run full tests, Ruff, diff checks, forbidden-name scan, release audit, and package builds.
