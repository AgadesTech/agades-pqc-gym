# ISOGENY_HISTORICAL Toy Path Reproduction Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan. Keep each step small and verify the RED/GREEN boundary before broad regeneration.

**Goal:** Add a bounded public reproduction harness for the `ISOGENY_HISTORICAL` toy historical path evaluator by verifying one tiny public historical path fixture.

**Architecture:** Keep `ISOGENY_HISTORICAL` explicitly historical and no-claim. The harness verifies a declared toy path fixture only when the plan requests downscaled reproduction and references a relative JSON fixture under `benchmarks/isogeny_historical_toy_path/fixtures/`. It is not an isogeny solver, not a SIDH/SIKE break, not a current-standard claim, and not a security claim.

**Tech Stack:** Python 3.12, Pydantic, pytest, JSON fixtures, existing `CascadeEvaluator` adapter boundary.

---

### Task 1: Add RED Tests

**Files:**
- Create: `tests/test_isogeny_historical_path_fixture.py`
- Modify: `tests/test_isogeny_historical_adapter.py`

- [x] Add a fixture-verifier test that imports `verify_toy_isogeny_path_fixture` and validates the public toy path fields.
- [x] Add a package-mirror test so the benchmark fixture is distributed with the Python package.
- [x] Add adapter tests for positive reproduction, missing fixture rejection, fixture-root scope rejection, and traversal rejection.
- [x] Run the targeted tests and confirm they fail because `path_fixture.py` does not exist yet.

### Task 2: Implement The Fixture Verifier

**Files:**
- Create: `src/agades_pqc_gym/families/isogeny_historical/path_fixture.py`
- Add: `benchmarks/isogeny_historical_toy_path/fixtures/toy_sidh_path_fixture.json`
- Add: `src/agades_pqc_gym/families/isogeny_historical/fixtures/toy_sidh_path_fixture.json`
- Modify: `pyproject.toml`

- [x] Define a strict Pydantic fixture schema with `historical_not_current=true`, `current_standard_claim=false`, `public=true`, and `security_claim=false`.
- [x] Validate path length, start/end nodes, reviewed toy case, and bounded walk/branching limits.
- [x] Return a small typed result object from `verify_toy_isogeny_path_fixture`.
- [x] Package the mirrored fixture as package data.

### Task 3: Wire Reproduction Through The Adapter

**Files:**
- Modify: `src/agades_pqc_gym/families/isogeny_historical/adapter.py`

- [x] Replace the blanket reproduction rejection with explicit fixture-required and fixture-scope validations.
- [x] Resolve fixtures from the repository first and the package fixture mirror second.
- [x] Return `instance_solved` only when fixture fields match the reviewed target/operator shape and all public no-claim flags are present.
- [x] Keep schema-only and current-standard plans unsupported.

### Task 4: Add Public Benchmark Coverage

**Files:**
- Add: `benchmarks/isogeny_historical_toy_path/toy_sidh_path_fixture_verify.json`
- Modify: `benchmarks/isogeny_historical_toy_path/README.md`
- Modify support/release/public manifest tests as needed.

- [x] Add a benchmark AttackPlan that requests reproduction through the public fixture.
- [x] Update the family support matrix status for historical-isogeny reproduction.
- [x] Update public ledger, manifest, and release-audit expected counts from 13 to 14 records.

### Task 5: Regenerate And Verify

- [ ] Regenerate the historical-isogeny public run bundle and aggregate manifests.
- [ ] Run targeted tests for the adapter, fixture verifier, support matrix, public ledger, public manifest, and release audit.
- [ ] Run the full test suite, ruff, diff checks, public benchmark verification, release audit, root build, and Prime verifier environment build.
- [ ] Confirm forbidden project names are still absent.
