# Code-Based Packaged Fixture Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the code-based toy syndrome reproduction fixture available in installed package contexts, matching the package-data behavior already used by other non-lattice reproduction harnesses.

**Architecture:** Keep public benchmark fixture paths scoped to `benchmarks/code_based_toy_isd/fixtures/*.json` in AttackPlans. Resolve that public path from the checkout first, then from package fixtures by basename for installed environments. Reject absolute paths, traversal, wrong directory depth, and non-JSON files before resolution.

**Tech Stack:** Python, setuptools package data, pytest.

---

### Task 1: Write RED Tests

**Files:**
- Modify: `tests/test_code_based_adapter.py`
- Modify: `tests/test_package.py`

- [x] Add a test proving code-based reproduction succeeds when the checkout fixture root is unavailable but the packaged fixture exists.
- [x] Add a test proving path traversal inside the fixture path is rejected.
- [x] Add a package metadata test proving `families/code_based/fixtures/*.json` is included in package data.
- [x] Run targeted tests and confirm they fail for the missing behavior.

### Task 2: Implement Package Fixture Support

**Files:**
- Modify: `src/agades_pqc_gym/families/code_based/adapter.py`
- Modify: `pyproject.toml`
- Add: `src/agades_pqc_gym/families/code_based/fixtures/toy_syndrome_31_16_w3_fixture.json`

- [x] Add the package fixture copy.
- [x] Add code-based package-data inclusion.
- [x] Replace ad hoc path checks with strict scoped-path validation.
- [x] Resolve checkout fixture first, then packaged fixture by filename.

### Task 3: Verify

- [x] Run targeted code-based/package tests.
- [x] Run full tests, Ruff, diff checks, forbidden-name scan, and package builds.
