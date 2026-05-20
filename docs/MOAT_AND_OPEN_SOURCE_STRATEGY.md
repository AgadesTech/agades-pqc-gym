# Moat And Open Source Strategy

## Open Source

- Core schemas and family adapter interfaces.
- Lattice MVP adapter and mock estimator.
- Schema-only non-lattice placeholders.
- Toy benchmarks.
- Report templates.
- Public benchmark cards.
- Hugging Face Space/dataset skeletons.
- Prime Intellect verifier/environment skeletons.
- NVIDIA/accelerator positioning docs.
- Sanitized examples and public trace exports.
- Deterministic public release audits over checked-in OSS artifacts and multi-family plugin readiness.
- A checked-in private-run policy that documents which private evolution artifacts must stay out of public roots.

## Private

- Full real evolution traces.
- Tuned prompts and prompt-selection policies.
- Evaluator weights and anti-gaming heuristics.
- Unpublished candidate strategies.
- Proprietary paper notes.
- Collaborator drafts and sensitive correspondence.
- Non-public benchmark results.
- Responsible-disclosure material.

## Release Rule

Publish interfaces, schemas, toy evidence, and verifier scaffolding. Hold back traces, prompts, weights, unpublished candidates, and collaborator-sensitive context.

Run:

```bash
uv run agades-pqc private-run-policy --out docs/private_run_policy.json
uv run agades-pqc private-run-policy-verify --policy docs/private_run_policy.json
uv run agades-pqc release-audit --out public/release_audit.json
```

before publishing or mirroring public artifacts. A blocking failed check means
the public surface is not release-ready.
