# Implementation Runbook

Follow `docs/PLAN.md` milestone by milestone.

## Rules

- Keep diffs scoped.
- Use TDD for behavior-bearing code.
- Do not execute arbitrary LLM-generated Python candidates without sandboxing.
- Use the mock estimator when Sage or the Lattice Estimator is unavailable.
- Mark mock output clearly in traces and reports.
- Keep private traces, prompts, evaluator recipes, and candidate discoveries out of public exports.

## Validation Commands

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check .
uv run agades-lwe --help
```

