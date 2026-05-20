# Plan

## Milestones

1. Generic repository/package scaffold for `agades-pqc-gym`.
2. Family-agnostic `TargetSpec`, `AttackPlan`, `AttackOperator`, and family adapter interfaces.
3. Family registry and evaluator router.
4. Implemented `lattice` adapter for LWE/MLWE with mock estimator and conservative Lattice Estimator boundary.
5. Schema-only placeholder adapters for code-based, multivariate, hash-based, historical isogeny, and implementation-security families.
6. Trace logging, public redaction, OpenEvolve adapter, private candidate
   mutation batch, and report generation.
7. Hugging Face, Prime Intellect, NVIDIA/accelerator, and GitHub OSS artifacts.
8. Collaboration briefs and source map.
9. End-to-end smoke runs and final status update.
10. Deterministic public run ledger and bundle packaging for toy benchmark publication.

## Acceptance Criteria

- Tests pass with the mock estimator.
- Lint passes.
- `agades-pqc` CLI validates and evaluates LWE/MLWE toy AttackPlans.
- Non-lattice placeholder AttackPlans validate structurally and evaluate as `unsupported` without fake estimates.
- Traces can be redacted for public release.
- Trace JSONL can be packaged into a deterministic public run ledger and checksum bundle.
- Reviewed candidate mutations generate private JSON AttackPlans only and skip unsupported families.
- Reports distinguish mock, real, and unsupported estimator status.
- Public documents avoid overclaiming.
