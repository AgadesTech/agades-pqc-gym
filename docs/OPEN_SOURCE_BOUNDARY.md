# Open Source Boundary

Agades PQC Gym is released as an open-core research substrate. This page lists what is public in this repository and what stays out of it.

## Open Source

- Core schemas and family adapter interfaces.
- Lattice MVP adapter and mock estimator.
- Schema-only non-lattice placeholders.
- Toy benchmarks.
- Report templates.
- Public benchmark cards.
- Hugging Face Space/dataset skeletons.
- Prime Intellect verifier/environment skeletons.
- Accelerator release plan and manifest.
- Sanitized examples and public trace exports.
- Deterministic public release audits over checked-in OSS artifacts and multi-family plugin readiness.
- A checked-in private-run policy that documents which private evolution artifacts must stay out of public roots.

## Private

- Full real evolution traces.
- Tuned prompts and prompt-selection policies.
- Evaluator weights and anti-gaming heuristics.
- Unpublished candidate strategies.
- Unpublished research notes.
- Non-public benchmark results.
- Responsible-disclosure material.

## Release Rule

Publish interfaces, schemas, toy evidence, and verifier scaffolding. Hold back traces, prompts, weights, unpublished candidates, and unpublished research notes.

Run:

```bash
uv run agades-pqc private-run-policy --out docs/private_run_policy.json
uv run agades-pqc private-run-policy-verify --policy docs/private_run_policy.json
uv run agades-pqc release-audit --out public/release_audit.json
```

before publishing or mirroring public artifacts. A blocking failed check means
the public surface is not release-ready.
