# Private Evaluation Redaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure public exports never retain private evaluator scores, estimator labels, raw outputs, warnings, or feature fields from non-public `TraceRecord` objects.

**Architecture:** Strengthen the existing public/private redaction layer in `agades_pqc_gym.traces.redaction`. Public records remain unchanged. Non-public records keep only stable run linkage and a minimal redacted evaluation envelope; public ledgers and reports consume that redacted envelope.

**Tech Stack:** Python, Pydantic trace models, pytest, deterministic JSONL public exports, release audit.

---

### Task 1: Write RED Tests For Private Evaluation Redaction

**Files:**
- Modify: `tests/test_trace_redaction.py`
- Modify: `tests/test_public_ledger.py`
- Modify: `tests/test_reporting.py`
- Modify: `tests/test_release_audit.py`

- [x] Add a redaction test proving private evaluation scores, estimator names, raw outputs, warnings, and feature fields are removed.
- [x] Update the private public-ledger test so redacted entries expose `evaluation_status="redacted"` and no private score or estimator.
- [x] Update report/release-audit expectations so private reports do not expose private scores or evaluator output.
- [x] Run targeted tests and confirm they fail against the current permissive redaction behavior.

### Task 2: Implement Strict Private Evaluation Redaction

**Files:**
- Modify: `src/agades_pqc_gym/traces/redaction.py`
- Modify: `src/agades_pqc_gym/integrations/release_audit.py`

- [x] Replace private evaluation dictionaries with a minimal redacted envelope.
- [x] Set private top-level `accepted` to `None` in public redacted records so acceptance/rejection is not leaked.
- [x] Keep public records byte-compatible except for canonical trace IDs computed from the unchanged public payload.
- [x] Strengthen the release-audit report-redaction smoke to check private score and evaluator-output absence.

### Task 3: Verify And Document

**Files:**
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/STATUS.md`
- Regenerate: `public/release_audit.json`

- [x] Document the strict evaluation redaction boundary.
- [x] Run targeted redaction/ledger/report/audit tests.
- [x] Run full tests, Ruff, diff checks, package builds, and forbidden-name scan.
