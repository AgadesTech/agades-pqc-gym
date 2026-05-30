# Agades PQC Gym

Agades PQC Gym is a family-agnostic, evaluator-driven workbench for
post-quantum cryptanalysis research workflows.

The first implemented vertical is **Agades LWE Strategy Gym**: LWE/MLWE
`AttackPlan` objects routed through the `lattice` family adapter. CI uses a
deterministic mock estimator. Reviewed private runs may use the optional
Lattice Estimator adapter for LWE-family mappings such as primal uSVP, BDD,
dual, dual-hybrid, and BKW.

This repository does not claim that any deployed post-quantum standard is
broken. Estimator output is treated as an analytical hypothesis that requires
independent review.

## Current Scope

Family-agnostic core API:

- `TargetSpec`, `AttackPlan`, `AttackOperator`, `AssumptionSet`
- `FamilyAdapter`, `FamilyPluginDescriptor`, `FamilyRegistry`
- `EvaluatorResult`, `FitnessReport`, `TraceRecord`
- `ReportGenerator` and public/private redaction

Family plugins:

- `families/lattice`: implemented LWE/MLWE MVP. NTRU/SIS remain schema-only
  until reviewed mappings exist.
- `families/code_based`: bounded ISD-style and fixture decoders for public toy
  targets, including `circulant-erasure` plumbing. This is not an HQC result.
- `families/multivariate`: bounded toy MQ, MinRank, and UOV public-map
  verifier surfaces.
- `families/hash_based`: bounded toy preimage, collision, signature-chain, and
  `toy_slh_dsa_hypertree_verify` SLH-DSA-like hypertree surfaces; this is
  not an SLH-DSA result.
- `families/isogeny_historical`: bounded historical toy path/graph fixtures.
- `families/implementation_security`: JSON-only public checks such as
  `toy_memory_footprint_check`, `toy_binary_size_check`,
  `toy_dudect_summary_threshold_check`, and
  `toy_ctgrind_secret_taint_summary_check` for memory-footprint, binary-size,
  dudect-style, and ctgrind-style public summaries.

The implementation-security dudect-style and ctgrind-style summaries are
verified without executing dudect and without executing ctgrind. They make no
constant-time, side-channel, or security claim.

Real PQClean, liboqs, pqm4, PQ Code Package, dudect, ctgrind,
TIMECOP/SUPERCOP, and `nist_acvp_pqc_vectors_schema` workflows are schema-only
or future reviewed-adapter work. They make no ACVP, conformance, side-channel,
or security claim, no constant-time, side-channel, or security claim, and no
ACVP server interaction.

The router never uses a lattice evaluator for non-lattice families.
Unsupported routes return structured `unsupported` results rather than fake
estimates.

## Install

```bash
uv sync --extra dev
```

## Quick Start

```bash
uv run agades-pqc quickstart
```

The quickstart runs the short core loop and writes local artifacts under
`runs/quickstart/`:

- `lattice_trace.jsonl`: one toy LWE evaluation trace.
- `lattice_benchmark.jsonl`: the toy LWE benchmark trace.
- `lattice_report.md`: a Markdown report generated from the trace.
- `code_based_prange_trace.jsonl`: a toy code-based evaluator trace.
- `unsupported_placeholder_trace.jsonl`: a schema-only unsupported example.

To choose the output directory, use either `--out-dir` or the shorter `--out`
alias:

```bash
uv run agades-pqc quickstart --out runs/my_quickstart
```

See `docs/QUICKSTART.md` for the guided walkthrough.

Manual core-loop commands:

```bash
uv run agades-pqc examples
uv run agades-pqc validate examples/attack_plans/lattice_primal_usvp_toy.json
uv run agades-pqc run examples/attack_plans/lattice_primal_usvp_toy.json --trace runs/demo_trace.jsonl
uv run agades-pqc benchmark benchmarks/lattice_toy_lwe --trace runs/demo_benchmark.jsonl
uv run agades-pqc report runs/demo_trace.jsonl --out reports/demo_report.md
```

`run` is the short alias for `evaluate`. `run`/`evaluate` and `benchmark`
print the same concise status fields:
`status`, `score`, `accepted`, `plan_valid`, and `trace`.

Schema-only examples validate structurally but return `status=unsupported`
with `accepted=False` instead of cryptanalytic estimates:

```bash
uv run agades-pqc validate examples/attack_plans/code_based_isd_placeholder.json
uv run agades-pqc run examples/attack_plans/code_based_isd_placeholder.json --trace runs/code_based_placeholder.jsonl
```

Optional formal check:

```bash
uv run agades-pqc formal-check
```

This checks the committed AttackPlan semantics, operator semantics, estimator
model, typed obligation ledger, family coverage, proof artifacts, reviewer
governance, and latest Lean build smoke report.

To refresh the compiled Lean evidence:

```bash
uv run agades-pqc formal-lean-build-smoke --out reports/formal_lean_build_smoke.json
uv run agades-pqc formal-lean-build-smoke-verify --report reports/formal_lean_build_smoke.json
```

Refreshing runs `lake build` for the Lean 4 + Mathlib source bundle and records
a bounded local report. Passing means the checked formal contracts compile; it
is not a cryptographic soundness review and does not create a security claim.

## Release Checks

The public release packet is deterministic and review-gated:

```bash
uv run agades-pqc formal-lean-backend --out docs/formal_lean_backend.json
uv run agades-pqc formal-lean-backend-verify --backend docs/formal_lean_backend.json
uv run agades-pqc formal-lean-build-smoke --out reports/formal_lean_build_smoke.json
uv run agades-pqc formal-lean-build-smoke-verify --report reports/formal_lean_build_smoke.json
uv run agades-pqc openevolve-config --out examples/openevolve/config.yaml
uv run agades-pqc openevolve-config-verify --config examples/openevolve/config.yaml
uv run agades-pqc hf-space-smoke --out reports/hf_space_smoke.json
uv run agades-pqc hf-space-smoke-verify --report reports/hf_space_smoke.json
uv run agades-pqc hf-space-launch-smoke --out reports/hf_space_launch_smoke.json
uv run agades-pqc hf-space-launch-smoke-verify --report reports/hf_space_launch_smoke.json
uv run agades-pqc nvidia-manifest-safety --out reports/nvidia_manifest_safety.json
uv run agades-pqc nvidia-manifest-safety-verify --report reports/nvidia_manifest_safety.json
uv run agades-pqc openevolve-smoke --out reports/openevolve_smoke.json
uv run agades-pqc openevolve-smoke-verify --report reports/openevolve_smoke.json
uv run agades-pqc prime-environment-smoke --out reports/prime_environment_smoke.json
uv run agades-pqc prime-environment-smoke-verify --report reports/prime_environment_smoke.json
uv run agades-pqc ecosystem-smoke --out reports/ecosystem_smoke.json
uv run agades-pqc ecosystem-smoke-verify --report reports/ecosystem_smoke.json
uv run agades-pqc release-artifacts --max-passes 6
```

Optional private live check after uploading the Space:

```bash
uv run agades-pqc hf-live-space-smoke --out reports/hf_live_space_smoke.json
uv run agades-pqc hf-live-space-smoke-verify --report reports/hf_live_space_smoke.json
```

The live check exercises the deployed Gradio API through
`/gradio_api/call/<api_name>`. The report is intentionally Git-ignored because
it proves access to a private Space and may contain deployment metadata.

Additional checked artifacts:

- `docs/family_support_matrix.json`
- `docs/family_plugin_manifest.json`
- `docs/family_registry_manifest.json`
- `docs/family_operator_catalog.json`
- `docs/source_catalog.json`
- `docs/benchmark_source_contracts.json`
- `docs/publication_manifest.json`
- `public/release_audit.json`
- `public/publication_preflight.json`
- `public/runbook_audit.json`

## Prime, Hugging Face, And NVIDIA

The repository includes credential-free local handoffs for ecosystem review:

- Hugging Face dataset, Space, Collection, and publication handoff manifests.
- Prime Intellect verifier wrapper, packaged verifier environment, schemas,
  publication handoff, and speedrun handoff.
- NVIDIA accelerator manifest, safety report, and publication handoff.

These artifacts are local and review-required. They do not publish to the
Hugging Face Hub, Prime Environments Hub, or NVIDIA-facing channels without
explicit credential and release review.

## Lattice Estimator Boundary

`docs/lattice_estimator_baseline_contracts.json` records
`review_contract_ready_not_reproduced` LWE mapping contracts. This is not a numeric Lattice Estimator baseline reproduction.

For Sage-backed private reproductions, run:

```bash
uv run agades-pqc lattice-estimator-runtime-preflight \
  --out private/reports/lattice_estimator_runtime_preflight.json \
  --policy docs/private_run_policy.json
uv run agades-pqc lattice-estimator-runtime-preflight-verify \
  --preflight private/reports/lattice_estimator_runtime_preflight.json
uv run agades-pqc lattice-estimator-checkout-preflight \
  --estimator-source <path> \
  --out private/reports/lattice_estimator_checkout_preflight.json \
  --policy docs/private_run_policy.json
uv run agades-pqc lattice-estimator-baseline-run \
  --estimator-source <path> \
  --sage-command sage \
  --out private/reports/lattice_estimator_baseline_run.json \
  --policy docs/private_run_policy.json
uv run agades-pqc lattice-estimator-baseline-run \
  --estimator-source <path> \
  --sage-python-command <python-with-sage-all> \
  --out private/reports/lattice_estimator_baseline_run.json \
  --policy docs/private_run_policy.json
uv run agades-pqc lattice-estimator-baseline-run-verify \
  --report private/reports/lattice_estimator_baseline_run.json \
  --contracts-root .
```

Legacy Sage installs can use `sage -python`; conda-style installs can pass an
explicit Python command with `sage.all` importable. Reports stay under
`private/reports/`, publish no public numeric outputs, and keep the
no-security-claim boundary.

## Public And Private Artifacts

Public artifacts include schemas, interfaces, toy examples, mock evaluator
output, benchmark cards, report templates, Hugging Face/Prime Intellect
skeletons, and sanitized traces.

`public/run_export/` flattens checked-in public run ledgers into deterministic
`manifest.json`, `runs.jsonl`, `runs.csv`, and `MANIFEST.sha256` files for
Prime-style autonomous-run review and OSS inspection. It is derived only from
public toy/downscaled bundles, contains no private traces, and creates no
security claim.

Private artifacts include serious evolution traces, prompts, evaluator weights,
unpublished candidate strategies, proprietary paper notes, and
collaborator-sensitive drafts. `docs/private_run_policy.json` defines the
checked policy for keeping those artifacts out of public roots.

## Docs

- `docs/ARCHITECTURE.md`: product architecture and plugin boundaries.
- `docs/FAMILY_ADAPTERS.md`: per-family target and validator details.
- `docs/IMPLEMENT.md`: full command runbook.
- `docs/ROADMAP.md`: current public baseline and future reviewed work.
- `reports/AGADES_PQC_GYM_MVP_REPORT.md`: current public MVP report.

## Test

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check .
```

## Responsible Research

Use this project only on public, toy, downscaled, or explicitly authorized
targets. Do not target live third-party systems, do not generate exploit
chains, and do not treat estimator-only output as proof of a security break.
