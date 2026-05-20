# Publication Artifact Digests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic SHA-256 provenance to checked-in public artifacts referenced by the multi-platform publication manifest, with an explicit audited exclusion for the recursive release-audit artifact.

**Architecture:** Keep existing `artifact_paths` fields for readability and compatibility. Add `artifact_sha256` maps to publication surfaces and public run bundle entries, add an explicit `artifact_digest_exclusions` map only where hashing would create recursion, and make the release audit verify every listed path exists and either matches its digest or has a reviewed exclusion reason.

**Tech Stack:** Python, JSON manifests, pytest, release audit.

---

### Task 1: Write RED Tests For Artifact Digests

**Files:**
- Modify: `tests/test_publication_manifest.py`
- Modify: `tests/test_release_audit.py`

- [x] Add assertions that every publication surface has an `artifact_sha256` map whose keys equal `artifact_paths` and whose values match current file hashes.
- [x] Add assertions that every public run bundle has an `artifact_sha256` map whose keys equal bundle `artifact_paths` and whose values match current file hashes.
- [x] Update the custom public-run discovery test to expect digest maps.
- [x] Update release-audit expected evidence to count surface and public-run bundle artifact digests.
- [x] Run targeted tests and confirm they fail because the current manifest lacks digest maps.

### Task 2: Implement Deterministic Digests

**Files:**
- Modify: `src/agades_pqc_gym/integrations/publication_manifest.py`
- Modify: `src/agades_pqc_gym/integrations/release_audit.py`

- [x] Add a shared helper that hashes checked-in file paths relative to the project root.
- [x] Populate `artifact_sha256` for every non-recursive surface artifact.
- [x] Populate `artifact_sha256` for every public run bundle.
- [x] Make the release audit verify digest map keys, reviewed exclusions, and SHA-256 values for every listed artifact.

### Task 3: Regenerate And Verify

**Files:**
- Regenerate: `docs/publication_manifest.json`
- Regenerate: `public/release_audit.json`
- Modify: `docs/STATUS.md`

- [x] Regenerate publication and release audit manifests.
- [x] Document digest provenance in status.
- [x] Run targeted tests, full tests, Ruff, diff checks, package builds, and forbidden-name scan.
