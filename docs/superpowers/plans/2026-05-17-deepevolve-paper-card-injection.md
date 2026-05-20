# DeepEvolve Paper-Card Injection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic, private, review-gated DeepEvolve paper-card injection batch that turns checked-in PaperCards into non-executing hypothesis prompts for the private OpenEvolve loop.

**Architecture:** Keep PaperCards and hypothesis proposals public and note-only, but generate injection batches only under allowed private roots. The batch must never emit executable code, modify estimator scores, publish private candidates, or certify a research claim; it only queues reviewed literature-derived hypotheses for a later proposer.

**Tech Stack:** Python 3.12, Pydantic, Typer CLI, existing private-run policy and release-audit gates.

---

### Task 1: Paper-Card Injection Batch

**Files:**
- Create: `src/agades_pqc_gym/deepevolve_hooks/injection.py`
- Modify: `src/agades_pqc_gym/deepevolve_hooks/__init__.py`
- Test: `tests/test_deepevolve_hooks.py`

- [ ] **Step 1: Write failing tests**

Add tests that build a batch from `examples/paper_cards`, assert schema `agades.pqc.paper_card_injection_batch.v1`, assert 13 review-required injections, and assert all safety flags are false.

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/test_deepevolve_hooks.py::test_paper_cards_build_private_injection_batch -q`

Expected: fail because `agades_pqc_gym.deepevolve_hooks.injection` does not exist.

- [ ] **Step 3: Implement minimal batch builder/writer**

Create Pydantic models and functions:
- `build_paper_card_injection_batch(paper_card_dir, run_id)`
- `write_paper_card_injection_batch(out, paper_card_dir, run_id, policy, root)`

The writer validates `out` with `validate_policy_private_path`.

- [ ] **Step 4: Run GREEN**

Run: `uv run pytest tests/test_deepevolve_hooks.py -q`

Expected: pass.

### Task 2: CLI, Policy, and OpenEvolve Wiring

**Files:**
- Modify: `src/agades_pqc_gym/cli.py`
- Modify: `src/agades_pqc_gym/integrations/private_run_policy.py`
- Modify: `src/agades_pqc_gym/openevolve_adapter/config_templates.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_private_run_policy.py`
- Modify: `tests/test_openevolve_adapter.py`

- [ ] **Step 1: Write failing CLI/config/policy tests**

Add tests for `agades-pqc deepevolve-injections --out private/candidates/...`, private policy command count, and OpenEvolve template fields:
- `paper_card_injection_schema`
- `paper_card_injection_command`

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/test_cli.py::test_deepevolve_injections_command_writes_private_batch tests/test_private_run_policy.py::test_private_run_policy_defines_private_moat_boundaries tests/test_openevolve_adapter.py -q`

Expected: fail because the CLI command/template/policy entries are missing.

- [ ] **Step 3: Implement CLI/config/policy**

Wire `deepevolve-injections` to the writer, add `agades-pqc deepevolve-injections` to allowed private commands, and expose the command in the OpenEvolve template.

- [ ] **Step 4: Run GREEN**

Run: `uv run pytest tests/test_cli.py tests/test_private_run_policy.py tests/test_openevolve_adapter.py -q`

Expected: pass.

### Task 3: Release Audit, Docs, and Generated Artifacts

**Files:**
- Modify: `src/agades_pqc_gym/integrations/release_audit.py`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/STATUS.md`
- Modify: `README.md`
- Regenerate: `docs/private_run_policy.json`
- Regenerate: `examples/openevolve/config.yaml`
- Regenerate: `public/release_audit.json`
- Regenerate: `docs/release_status.json`
- Regenerate: `public/publication_preflight.json`

- [ ] **Step 1: Write failing audit tests**

Add a release-audit expectation for a blocking DeepEvolve injection smoke that proves the batch is private, review-required, non-executing, and not publication-safe.

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/test_release_audit.py tests/test_release_status.py tests/test_publication_preflight.py -q`

Expected: fail because the audit gate and generated counts are not updated.

- [ ] **Step 3: Implement audit/docs/artifact updates**

Add the audit gate, regenerate deterministic artifacts, and document that the research layer now has a private paper-card injection queue while public hooks remain note-only.

- [ ] **Step 4: Run full verification**

Run:
```bash
env PYTHONPATH=src uv run pytest -q
uv run ruff check .
git diff --check
uv build
uv build prime_intellect/verifiers_environment
```

Expected: all pass.
