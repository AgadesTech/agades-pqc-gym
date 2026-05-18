# Report Generator Redaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote reporting to a family-agnostic `ReportGenerator` that summarizes multi-family traces and applies the public/private redaction boundary before rendering public Markdown.

**Architecture:** Add a focused `agades_pqc_gym.reporting.generator` module responsible for normalizing legacy dict records and typed `TraceRecord` objects into report rows. Keep `agades_pqc_gym.reporting.markdown.render_report` as the compatibility wrapper used by the CLI, but route it through `ReportGenerator`.

**Tech Stack:** Python, Pydantic trace models, pytest, Typer CLI compatibility.

---

### Task 1: Write RED Tests For ReportGenerator

**Files:**
- Modify: `tests/test_reporting.py`

- [x] Add a test that imports `ReportGenerator`, renders mixed-family public records, and asserts the report includes family, target, reproduction status, and estimator summaries.
- [x] Add a test that renders a private `TraceRecord` with a sensitive target name and asserts the default public report redacts private target details while counting the redacted record.
- [x] Run the new targeted tests and confirm they fail because `agades_pqc_gym.reporting.generator.ReportGenerator` does not exist yet.

### Task 2: Implement The Generator

**Files:**
- Create: `src/agades_pqc_gym/reporting/generator.py`
- Modify: `src/agades_pqc_gym/reporting/markdown.py`
- Modify: `src/agades_pqc_gym/reporting/__init__.py`

- [x] Add `ReportGenerator.render_markdown(records)` that accepts `TraceRecord` objects and JSON-compatible dictionaries.
- [x] Preserve the public redaction boundary by hiding target/family/attack details for non-public `TraceRecord` rows unless `include_private_details=True`.
- [x] Render deterministic sections: summary, results table, public/private redaction, estimator status, reproduction status, and limitations.
- [x] Route `render_report(title, records)` through `ReportGenerator(title=title)`.

### Task 3: Verify And Document

**Files:**
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/STATUS.md`

- [x] Document that the report generator is a family-agnostic core module and public reports redact private trace details by default.
- [x] Add a blocking release-audit smoke gate for report redaction.
- [x] Regenerate checked-in Markdown reports through the new generator.
- [x] Run targeted reporting tests.
- [x] Run full tests, Ruff, diff checks, package builds, and the forbidden-name scan.
