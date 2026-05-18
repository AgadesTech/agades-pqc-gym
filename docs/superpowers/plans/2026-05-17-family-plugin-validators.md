# Family Plugin Validators Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose explicit family-specific validator modules for every non-lattice plugin, so the v3 multi-family architecture does not rely on implicit adapter-class validation paths.

**Architecture:** Add `validators.py` modules to `code_based`, `multivariate`, `hash_based`, `isogeny_historical`, and `implementation_security`. Each module exposes `validate_<family>_target()` and `validate_<family>_plan()` as the plugin-level applicability contract, delegating to the current reviewed adapter behavior to avoid semantic drift. Update family operator/registry manifests to point at those explicit validator functions.

**Tech Stack:** Python 3.12, existing `FamilyAdapter` validation API, deterministic family manifests, pytest, Typer artifact generators.

---

### Task 1: Validator Contract RED Tests

**Files:**
- Modify: `tests/test_family_operator_catalog.py`
- Modify: `tests/test_family_registry_manifest.py`

- [x] **Step 1: Add expected validator-path map**

Require:

```python
{
    "CODE_BASED": "agades_pqc_gym.families.code_based.validators.validate_code_based_plan",
    "MULTIVARIATE": "agades_pqc_gym.families.multivariate.validators.validate_multivariate_plan",
    "HASH_BASED": "agades_pqc_gym.families.hash_based.validators.validate_hash_based_plan",
    "ISOGENY_HISTORICAL": "agades_pqc_gym.families.isogeny_historical.validators.validate_isogeny_historical_plan",
    "IMPLEMENTATION_SECURITY": "agades_pqc_gym.families.implementation_security.validators.validate_implementation_security_plan",
}
```

- [x] **Step 2: Add importability and behavior parity test**

Load each function by dotted path, validate one public example per family, and assert its findings equal `default_family_registry().get(TargetFamily(...)).validate_plan(plan)`.

- [x] **Step 3: Run RED**

Run:

```bash
uv run pytest tests/test_family_operator_catalog.py::test_family_operator_catalog_imports_plugin_validators tests/test_family_registry_manifest.py::test_family_registry_manifest_describes_runtime_registry -q
```

Expected: fail because non-lattice `validators.py` modules and manifest paths do not exist yet.

### Task 2: Validator Modules and Manifest Generators

**Files:**
- Add: `src/agades_pqc_gym/families/code_based/validators.py`
- Add: `src/agades_pqc_gym/families/multivariate/validators.py`
- Add: `src/agades_pqc_gym/families/hash_based/validators.py`
- Add: `src/agades_pqc_gym/families/isogeny_historical/validators.py`
- Add: `src/agades_pqc_gym/families/implementation_security/validators.py`
- Modify: `src/agades_pqc_gym/integrations/family_operator_catalog.py`

- [x] **Step 1: Add validator modules**

Each module exposes `validate_*_target(target: TargetSpec)` and `validate_*_plan(plan: AttackPlan)` and delegates to its plugin adapter.

- [x] **Step 2: Update `VALIDATOR_BY_FAMILY`**

Point each non-lattice family at the new `validators.validate_*_plan` dotted path.

- [x] **Step 3: Run GREEN**

Run:

```bash
uv run pytest tests/test_family_operator_catalog.py::test_family_operator_catalog_imports_plugin_validators tests/test_family_registry_manifest.py::test_family_registry_manifest_describes_runtime_registry -q
```

Expected: pass.

### Task 3: Artifacts and Release Evidence

**Files:**
- Regenerate: `docs/family_operator_catalog.json`
- Regenerate: `docs/family_registry_manifest.json`
- Regenerate: `docs/publication_manifest.json`
- Regenerate: `public/release_audit.json`
- Regenerate: `docs/release_status.json`
- Regenerate: `public/publication_preflight.json`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Regenerate manifests**

Run family operator/registry generators and derived release/publication artifacts.

- [x] **Step 2: Update docs**

Document that every plugin now exposes an explicit validator module path.

### Task 4: Verification, Commit, Push

**Files:**
- Verify all modified files.

- [x] **Step 1: Full verification**

Run:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
uv build
uv build prime_intellect/verifiers_environment
```

- [x] **Step 2: Artifact and naming gates**

Run family/publication/release verifiers, release/runbook audits, and the legacy-name scan.

- [x] **Step 3: Commit, push, and check CI**

Commit, push `codex/multifamily-architecture`, and verify PR checks.
