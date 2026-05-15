# Agades LWE Strategy Gym

Agades LWE Strategy Gym is an evaluator-driven workbench for typed LWE/MLWE attack-strategy search on toy, downscaled, and public benchmark settings.

It is not a claim that any deployed post-quantum cryptographic standard is broken. Estimator output is treated as an analytical hypothesis that requires independent validation.

## Install

```bash
uv sync --extra dev
```

## Run

```bash
uv run agades-lwe validate examples/attack_plans/primal_usvp_toy.json
uv run agades-lwe evaluate examples/attack_plans/primal_usvp_toy.json --out runs/demo_trace.jsonl
uv run agades-lwe report runs/demo_trace.jsonl --out reports/demo_report.md
```

## Public And Private Artifacts

Public artifacts include the DSL schema, toy examples, mock evaluator output, benchmark cards, report templates, and sanitized traces.

Private artifacts include real evolution traces, private prompts, evaluator weights, unpublished candidate strategies, proprietary paper notes, and collaborator-sensitive drafts.

## Responsible Research

Use this project only on public, toy, downscaled, or explicitly authorized targets. Do not target live third-party systems, do not generate exploit chains, and do not treat estimator-only output as proof of a security break.

