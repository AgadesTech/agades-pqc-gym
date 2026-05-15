# Agades LWE Strategy Gym MVP Report

## 1. Summary

Agades LWE Strategy Gym is a Python MVP for evaluator-driven search over typed LWE/MLWE attack strategies. It demonstrates the infrastructure on toy and downscaled settings only.

The MVP does not claim any deployed post-quantum cryptographic standard is broken.

## 2. What Was Built

- Typed AttackPlan DSL with finite operators.
- Static validator suite for schema, assumptions, and basic consistency.
- Deterministic mock estimator for CI and smoke runs.
- Conservative Lattice Estimator adapter boundary.
- Cascade evaluator with OpenEvolve-compatible scalar metrics.
- JSONL trace schema, writer, and public redaction.
- Markdown report generation.
- OpenEvolve JSON adapter.
- DeepEvolve-style paper cards and hypothesis hooks.
- Hugging Face and Prime Intellect release artifacts.
- Collaboration briefs for ASI Labs, Martin Albrecht, and Leo Ducas.

## 3. Architecture

The DSL sits at the center. AttackPlan JSON is parsed into Pydantic models, validated statically, evaluated by an estimator adapter, scored by a fitness function, logged as JSONL, and optionally rendered into Markdown or redacted for public release.

The real Lattice Estimator integration is intentionally separated from the mock estimator. Unsupported real-estimator mappings raise explicit unavailability errors rather than returning fabricated cryptanalytic output.

## 4. DSL Examples

Example public plans:

- `examples/attack_plans/primal_usvp_toy.json`
- `examples/attack_plans/dual_hybrid_toy.json`
- `examples/attack_plans/mlwe_module_hypothesis_toy.json`
- `examples/attack_plans/invalid_plan_should_fail.json`

The invalid example verifies that `module_lattice_reduction_hypothesis` cannot target plain LWE.

## 5. Evaluator Cascade

Stages implemented:

1. Load and parse AttackPlan JSON.
2. Run static validation.
3. Estimate with a configured adapter.
4. Apply sanity penalties.
5. Aggregate scalar fitness and MAP-Elites feature metrics.
6. Write trace records.

## 6. Example Toy Results

Smoke command:

```bash
uv run agades-lwe benchmark benchmarks/toy_lwe --out runs/toy_benchmark.jsonl
```

Observed mock-estimator results:

| Candidate | Score | Time Bits | Memory Bits | Estimator |
| --- | ---: | ---: | ---: | --- |
| `toy_lwe_n64_q257_primal_seed-0` | -67.4696 | 63.5296 | 17.36 | `mock-lattice-estimator` |
| `toy_lwe_n96_q769_primal_seed-1` | -97.0376 | 91.1776 | 25.04 | `mock-lattice-estimator` |

These numbers validate plumbing only.

## 7. Mock Vs Real Estimator Status

The mock estimator is deterministic and clearly labels its warnings. It is suitable for tests, CI, and toy smoke runs.

The real Lattice Estimator adapter currently checks module availability and refuses unsupported mappings. A production integration must pin a specific estimator commit, map each operator through reviewed calls, and add baseline reproduction tests.

## 8. Trace Logging And Moat Separation

Every CLI evaluation can write a TraceRecord containing candidate metadata, the AttackPlan, metrics, acceptance status, and public/private release flags.

`agades-lwe export-public` redacts private mutation summaries and full private AttackPlans before writing public JSONL.

Public: schemas, examples, mock outputs, report templates, sanitized traces.

Private: real traces, prompts, evaluator weights, unpublished candidate strategies, proprietary paper notes, and collaborator-sensitive drafts.

## 9. OpenEvolve Integration

`examples/openevolve/evaluator.py` exposes:

```python
def evaluate(program_path: str) -> dict[str, float | int | str | bool | None]:
    ...
```

The MVP supports JSON AttackPlan candidates. It does not execute arbitrary Python candidates because no sandbox is implemented.

## 10. DeepEvolve Hooks

The MVP includes PaperCard and HypothesisProposal models plus example paper cards. These hooks produce review-gated hypotheses rather than truth claims.

The `module_lattice_reduction_hypothesis` operator is restricted to MLWE targets and should remain expert-review-gated.

## 11. Community Release Plan

Hugging Face artifacts:

- `hf/dataset_card.md`
- `hf/space_README.md`
- `hf/benchmark_card.md`

Prime Intellect artifacts:

- `prime_intellect/environment_card.md`
- `prime_intellect/verifier_spec.md`

## 12. Collaboration Plan

Initial briefs:

- `docs/ASI_LABS_COLLABORATION_BRIEF.md`
- `docs/MARTIN_ALBRECHT_COLLABORATION_BRIEF.md`
- `docs/LEO_DUCAS_COLLABORATION_BRIEF.md`

No outreach was sent automatically.

## 13. Limitations

- Real Lattice Estimator calls are not implemented yet.
- Mock-estimator scores are not cryptanalytic evidence.
- Downscaled reproduction is represented as a future interface, not a proof layer.
- The benchmark ladder currently covers schema, mock-estimator, CLI, trace, and reporting smoke tests.
- Public docs are based on the provided runbook source anchors and need expert review before outreach.

## 14. Next 30/60/90-Day Roadmap

30 days: pin and wire the real Lattice Estimator, reproduce known toy baselines, publish the GitHub repository, and prepare a Hugging Face toy dataset/Space.

60 days: add TAPAS/LWE-benchmarking adapters, downscaled reproduction experiments, held-out rescoring, and public benchmark v0.

90 days: add a DeepEvolve paper-card research loop, collect private evolution traces, add independent sanity checks, and prepare a reviewed public Agades technical report.

