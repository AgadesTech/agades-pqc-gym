# Lattice Schema-Only NTRU/SIS Public Placeholders Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add public schema-only NTRU and SIS examples plus benchmark seeds so the lattice plugin visibly includes reviewed boundaries for those families without routing them into LWE/MLWE estimators.

**Architecture:** Keep `NTRU` and `SIS` on the existing lattice adapter with `support_level="schema_only"`. The public verifier must return `evaluation_status="unsupported"` through the `lattice-family-router`, Prime rewards must score them as `0.0`, and Hugging Face/Prime/NVIDIA artifacts must expose them as public examples without creating public benchmark records or security claims.

**Tech Stack:** Python, Pydantic AttackPlan models, pytest, JSON AttackPlans, Agades CLI artifact generators.

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_public_verifier.py`
- Modify: `tests/test_family_support_matrix.py`
- Modify: `tests/test_huggingface_dataset_bundle.py`
- Modify: `tests/test_huggingface_space_manifest.py`
- Modify: `tests/test_prime_verifiers_env.py`
- Modify: `tests/test_release_audit.py`

- [x] Add public verifier assertions for `examples/attack_plans/lattice_ntru_schema_placeholder.json` and `examples/attack_plans/lattice_sis_schema_placeholder.json` returning schema-valid unsupported results with `estimator.name == "lattice-family-router"` and no time/memory estimates.
- [x] Add family support expectations that NTRU and SIS each have one public example and one benchmark while staying schema-only with no operators.
- [x] Add Hugging Face, Space, Prime, and release-audit count/family expectations for two additional public valid examples.
- [x] Run targeted tests and confirm they fail because the NTRU/SIS public JSON files and regenerated artifacts are not present yet.

### Task 2: Public Schema-Only Inputs

**Files:**
- Add: `examples/attack_plans/lattice_ntru_schema_placeholder.json`
- Add: `examples/attack_plans/lattice_sis_schema_placeholder.json`
- Add: `prime_intellect/verifiers_environment/data/lattice_ntru_schema_placeholder.json`
- Add: `prime_intellect/verifiers_environment/data/lattice_sis_schema_placeholder.json`
- Add: `benchmarks/lattice_schema_only/ntru_toy_schema.json`
- Add: `benchmarks/lattice_schema_only/sis_toy_schema.json`
- Add: `benchmarks/lattice_schema_only/README.md`

- [x] Add strict public AttackPlans for NTRU and SIS using `support_level="schema_only"`, no claims, and explicit `schema_only_no_estimator` assumptions.
- [x] Add matching Prime packaged task JSON files copied exactly from the public examples.
- [x] Add schema-only benchmark seeds for the same two families and a README stating that these are routing/boundary tests only.

### Task 3: Regenerate Artifacts

**Files:**
- Regenerate: `docs/family_support_matrix.json`
- Regenerate: `hf/dataset/*`
- Regenerate: `hf/space_manifest.json`
- Regenerate: `prime_intellect/verifiers_environment/prime_manifest.json`
- Regenerate: `nvidia/accelerator_manifest.json`
- Regenerate: `docs/publication_manifest.json`
- Regenerate: `public/release_audit.json`
- Modify: `docs/FAMILY_ADAPTERS.md`
- Modify: `docs/STATUS.md`

- [x] Regenerate family support, Hugging Face dataset/Space, Prime manifest, NVIDIA manifest, publication manifest, and release audit.
- [x] Update docs to say NTRU/SIS now have public schema-only example and benchmark coverage, while still returning unsupported until reviewed mappings exist.

### Task 4: Verify and Publish Branch

- [x] Run targeted tests.
- [x] Run full tests, Ruff, `git diff --check`, forbidden-name scan, release audit, public benchmark verification, and package builds.
- [x] Commit, push, and verify PR checks.
