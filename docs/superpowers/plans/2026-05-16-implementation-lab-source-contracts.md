# Implementation Lab Source Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add machine-readable, review-gated source contracts for future Agades PQC Implementation Lab anchors without enabling heavyweight implementation-security execution in the current public verifier.

**Architecture:** Extend `benchmark_source_contracts` from lattice-only TAPAS/LWE anchors to include implementation-security sources. Keep every new source blocked from `current_public_verifier`, `prime_json_only_reward_environment`, and `public_benchmark_v0_claim_surface`; expose only the review gates and future surfaces needed for Prime/HF/NVIDIA planning.

**Tech Stack:** Python, JSON manifest generation, Typer CLI, pytest, release audit.

---

### Task 1: Write RED Tests For Implementation-Security Contracts

**Files:**
- Modify: `tests/test_benchmark_source_contracts.py`
- Modify: `tests/test_source_catalog.py`
- Modify: `tests/test_release_audit.py`

- [x] Add assertions for `liboqs-implementation-harness`, `pqm4-cortexm4-benchmarking`, and `nist-acvp-pqc-vectors` contracts.
- [x] Add source catalog assertions for `pqm4` and `nist-acvp`.
- [x] Update release audit expected benchmark-source-contract evidence to the new contract counts.
- [x] Run the targeted tests and confirm they fail because the implementation-security contracts are not implemented.

### Task 2: Implement Source Contracts

**Files:**
- Modify: `src/agades_pqc_gym/integrations/benchmark_source_contracts.py`
- Modify: `src/agades_pqc_gym/integrations/source_catalog.py`

- [x] Add future-reviewed contracts for liboqs, pqm4, and NIST ACVP PQC vectors.
- [x] Keep `current_runtime_enabled=false` and `public_verifier_allowed=false` for every new source.
- [x] Add review gates for toolchain pinning, KAT/ACVP vector provenance, device/simulator isolation, timing/constant-time interpretation, redaction, and expert review before claims.
- [x] Add catalog anchors for pqm4 and NIST ACVP, leaving them as future reviewed implementation-security sources.

### Task 3: Regenerate And Verify

**Files:**
- Regenerate: `docs/benchmark_source_contracts.json`
- Regenerate: `docs/source_catalog.json`
- Regenerate: `nvidia/accelerator_manifest.json`
- Regenerate: `public/release_audit.json`
- Modify docs/status text as needed.

- [x] Run `agades-pqc benchmark-source-contracts`.
- [x] Run `agades-pqc source-catalog`.
- [x] Run `agades-pqc nvidia-manifest`.
- [x] Run `agades-pqc release-audit`.
- [x] Run targeted tests, full tests, ruff, diff checks, package builds, forbidden-name scan, PR checks.
