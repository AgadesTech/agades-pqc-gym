# Martin Albrecht Collaboration Brief

We are building an evaluator-driven workbench for LWE/MLWE attack-strategy search. We do not treat the Lattice Estimator as an oracle of truth; we treat it as the first analytical layer in a validation suite.

## Proposed Feedback Areas

- Whether the AttackPlan representation maps sensibly to Lattice Estimator attack models.
- Missing estimator interfaces or common pitfalls.
- Reproducibility wrappers and tests that could be useful upstream.
- Whether estimator-based search can help identify benchmark gaps without overclaiming.

## Materials To Share

- `docs/SOURCE_MAP.md`
- `examples/attack_plans/*.json`
- A concise toy report with clear limitations.

## Boundaries

Do not lead with claims about breaking ML-KEM. Lead with reproducibility, benchmark hygiene, estimator wrappers, and human review.

