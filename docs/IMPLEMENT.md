# Implementation Runbook

Follow `docs/PLAN.md` milestone by milestone.

## Rules

- Keep diffs scoped.
- Use TDD for behavior-bearing code.
- Do not execute arbitrary LLM-generated Python candidates without sandboxing.
- Use the mock estimator when Sage or the Lattice Estimator is unavailable.
- Mark mock output clearly in traces and reports.
- Route every AttackPlan through the family registry. Never reuse a lattice estimator for a non-lattice family.
- Return structured `unsupported` results for schema-only family adapters.
- Keep private traces, prompts, evaluator recipes, and candidate discoveries out of public exports.

## Validation Commands

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check .
git diff --check
uv run agades-pqc --help
uv run agades-pqc source-catalog --out docs/source_catalog.json
uv run agades-pqc family-registry-manifest --out docs/family_registry_manifest.json
uv run agades-pqc family-registry-manifest-verify --manifest docs/family_registry_manifest.json
uv run agades-pqc family-support --out docs/family_support_matrix.json
uv run agades-pqc family-operator-catalog --out docs/family_operator_catalog.json
uv run agades-pqc family-operator-catalog-verify --catalog docs/family_operator_catalog.json
uv run agades-pqc formal-lean-backend --out docs/formal_lean_backend.json
uv run agades-pqc formal-lean-backend-verify --backend docs/formal_lean_backend.json
uv run agades-pqc formal-lean-build-smoke --out reports/formal_lean_build_smoke.json
uv run agades-pqc formal-lean-build-smoke-verify --report reports/formal_lean_build_smoke.json
uv run agades-pqc lattice-estimator-manifest --out docs/lattice_estimator_manifest.json
uv run agades-pqc lattice-estimator-manifest-verify --manifest docs/lattice_estimator_manifest.json
uv run agades-pqc lattice-estimator-runtime-preflight --out private/reports/lattice_estimator_runtime_preflight.json --policy docs/private_run_policy.json
uv run agades-pqc lattice-estimator-runtime-preflight-verify --preflight private/reports/lattice_estimator_runtime_preflight.json
uv run agades-pqc lattice-estimator-checkout-preflight --estimator-source /path/to/lattice-estimator --out private/reports/lattice_estimator_checkout_preflight.json --policy docs/private_run_policy.json
uv run agades-pqc hf-dataset --out hf/dataset
uv run agades-pqc hf-dataset-verify --dataset hf/dataset
uv run agades-pqc hf-space-manifest --out hf/space_manifest.json
uv run agades-pqc hf-space-manifest-verify --manifest hf/space_manifest.json
uv run agades-pqc hf-space-smoke --out reports/hf_space_smoke.json
uv run agades-pqc hf-space-smoke-verify --report reports/hf_space_smoke.json
uv run agades-pqc hf-space-launch-smoke --out reports/hf_space_launch_smoke.json
uv run agades-pqc hf-space-launch-smoke-verify --report reports/hf_space_launch_smoke.json
uv run agades-pqc hf-space-remote-smoke --space-id agades/agades-pqc-gym-agent-env --out reports/hf_space_remote_smoke.json
uv run agades-pqc hf-space-remote-smoke-verify --report reports/hf_space_remote_smoke.json
uv run agades-pqc hf-collection-manifest --out hf/collection_manifest.json
uv run agades-pqc hf-collection-manifest-verify --manifest hf/collection_manifest.json
uv run agades-pqc nvidia-manifest --out nvidia/accelerator_manifest.json
uv run agades-pqc nvidia-manifest-verify --manifest nvidia/accelerator_manifest.json
uv run agades-pqc nvidia-manifest-safety --out reports/nvidia_manifest_safety.json
uv run agades-pqc nvidia-manifest-safety-verify --report reports/nvidia_manifest_safety.json
uv run agades-pqc prime-manifest --out prime_intellect/verifiers_environment/prime_manifest.json
uv run agades-pqc prime-manifest-verify --manifest prime_intellect/verifiers_environment/prime_manifest.json
uv run agades-pqc prime-environment-smoke --out reports/prime_environment_smoke.json
uv run agades-pqc prime-environment-smoke-verify --report reports/prime_environment_smoke.json
uv run agades-pqc prime-schemas --out prime_intellect/schemas
uv run agades-pqc prime-schemas-verify --schemas prime_intellect/schemas
uv run agades-pqc private-run-policy --out docs/private_run_policy.json
uv run agades-pqc private-run-policy-verify --policy docs/private_run_policy.json
uv run agades-pqc public-run-export --out public/run_export
uv run agades-pqc public-run-export-verify --export public/run_export
uv run agades-pqc publication-manifest --out docs/publication_manifest.json
uv run agades-pqc publication-manifest-verify --manifest docs/publication_manifest.json
uv run agades-pqc release-audit --out public/release_audit.json
uv run agades-pqc release-status --out docs/release_status.json
uv run agades-pqc release-status-verify --status docs/release_status.json
uv run agades-pqc publication-preflight --out public/publication_preflight.json
uv run agades-pqc publication-preflight-verify --preflight public/publication_preflight.json
uv run agades-pqc external-publication-review-packet --out docs/external_publication_review_packet.json
uv run agades-pqc external-publication-review-packet-verify --packet docs/external_publication_review_packet.json
uv run agades-pqc openevolve-config --out examples/openevolve/config.yaml
uv run agades-pqc openevolve-config-verify --config examples/openevolve/config.yaml
uv run agades-pqc openevolve-smoke --out reports/openevolve_smoke.json
uv run agades-pqc openevolve-smoke-verify --report reports/openevolve_smoke.json
uv run agades-pqc ecosystem-smoke --out reports/ecosystem_smoke.json
uv run agades-pqc ecosystem-smoke-verify --report reports/ecosystem_smoke.json
uv run agades-pqc release-artifacts --max-passes 6
uv run agades-pqc runbook-audit --out /tmp/agades_runbook_audit.json
uv run agades-pqc runbook-audit --brief /path/to/brief.md --out /tmp/agades_runbook_audit_with_brief.json
uv run agades-pqc runbook-audit --brief /path/to/brief.md --context /path/to/context.md --out /tmp/agades_runbook_audit_with_inputs.json
git diff --exit-code -- docs/source_catalog.json docs/family_registry_manifest.json docs/family_support_matrix.json docs/family_operator_catalog.json docs/private_run_policy.json public/run_export docs/publication_manifest.json docs/external_publication_review_packet.json examples/openevolve/config.yaml nvidia/accelerator_manifest.json reports/hf_space_smoke.json reports/hf_space_remote_smoke.json reports/nvidia_manifest_safety.json reports/openevolve_smoke.json reports/prime_environment_smoke.json reports/ecosystem_smoke.json public/release_audit.json docs/release_status.json public/publication_preflight.json
uv run agades-pqc benchmark benchmarks/lattice_toy_lwe --out runs/toy_benchmark.jsonl
uv run agades-pqc deepevolve-injections --out private/candidates/paper_card_injections.json --policy docs/private_run_policy.json --paper-card-dir examples/paper_cards
uv run agades-pqc mutate-candidates benchmarks/lattice_toy_lwe/lwe_n64_q257.json --out runs/candidate_mutations
uv run agades-pqc evolve-batch runs/candidate_mutations/plans --trace-out runs/evolution_trace.jsonl --archive-out runs/evolution_archive.json
uv run agades-pqc heldout-review-log --out private/runs/heldout_review_log.json --approval private-run-policy-review --approval heldout-target-review --approval retention-owner-review --approval publication-export-review
uv run agades-pqc private-evolution-campaign-plan benchmarks/lattice_toy_lwe/lwe_n64_q257.json benchmarks/lattice_toy_lwe/lwe_n96_q769.json --out private/runs/private_evolution_campaign/campaign_plan.json --policy docs/private_run_policy.json --review-log private/runs/heldout_review_log.json --run-id private-evolution-campaign
uv run agades-pqc private-evolution-campaign-plan-verify --plan private/runs/private_evolution_campaign/campaign_plan.json --policy docs/private_run_policy.json
uv run agades-pqc archive-snapshot runs/evolution_archive.json runs/evolution_trace.jsonl --out private/runs/archive_snapshot.json --review-log private/runs/heldout_review_log.json --policy docs/private_run_policy.json
uv run agades-pqc heldout-schedule runs/evolution_archive.json runs/evolution_trace.jsonl benchmarks/lattice_toy_lwe/lwe_n96_q769.json --out private/runs/heldout_schedule.json --trace-out private/traces/heldout_trace.jsonl --rescore-out private/reports/heldout_rescore.json --review-log private/runs/heldout_review_log.json --trigger local_cron_after_review --approval private-run-policy-review --approval heldout-target-review --approval retention-owner-review --approval publication-export-review
uv run agades-pqc heldout-cron-plan private/runs/heldout_schedule.json --out private/runs/heldout_cron_plan.json --policy docs/private_run_policy.json --minute 17 --every-hours 6 --log-path private/runs/heldout_cron.log
uv run agades-pqc heldout-run-schedule private/runs/heldout_schedule.json --policy docs/private_run_policy.json
uv run agades-pqc heldout-review-packet private/runs/heldout_schedule.json --out private/reports/heldout_review_packet.json --policy docs/private_run_policy.json --reviewer-label local-heldout-review
uv run agades-pqc heldout-review-packet-verify --packet private/reports/heldout_review_packet.json --schedule private/runs/heldout_schedule.json --policy docs/private_run_policy.json
uv build
uv build prime_intellect/verifiers_environment
```

## Private Lattice Estimator Baseline Runs

The private baseline-run command requires an importable Lattice Estimator backend
whose commit metadata matches `docs/lattice_estimator_manifest.json`. It writes
only under allowed private roots and exits nonzero if no pinned numeric result is
produced:

```bash
uv run agades-pqc lattice-estimator-baseline-run \
  --contracts docs/lattice_estimator_baseline_contracts.json \
  --contracts-root . \
  --out private/reports/lattice_estimator_baseline_run.json \
  --policy docs/private_run_policy.json
```

For a reviewed local checkout of `malb/lattice-estimator`, add:

```bash
uv run agades-pqc lattice-estimator-runtime-preflight \
  --out private/reports/lattice_estimator_runtime_preflight.json \
  --policy docs/private_run_policy.json

uv run agades-pqc lattice-estimator-runtime-preflight-verify \
  --preflight private/reports/lattice_estimator_runtime_preflight.json

uv run agades-pqc lattice-estimator-checkout-preflight \
  --estimator-source /path/to/lattice-estimator \
  --out private/reports/lattice_estimator_checkout_preflight.json \
  --policy docs/private_run_policy.json

uv run agades-pqc lattice-estimator-baseline-run \
  --contracts docs/lattice_estimator_baseline_contracts.json \
  --contracts-root . \
  --out private/reports/lattice_estimator_baseline_run.json \
  --policy docs/private_run_policy.json \
  --estimator-source /path/to/lattice-estimator \
  --sage-command sage

uv run agades-pqc lattice-estimator-baseline-run-verify \
  --report private/reports/lattice_estimator_baseline_run.json \
  --contracts-root .

uv run agades-pqc lattice-estimator-baseline-review-packet \
  --baseline-report private/reports/lattice_estimator_baseline_run.json \
  --out private/reports/lattice_estimator_baseline_review_packet.json \
  --policy docs/private_run_policy.json \
  --contracts-root . \
  --reviewer-label local-lattice-expert-review

uv run agades-pqc lattice-estimator-baseline-review-packet-verify \
  --packet private/reports/lattice_estimator_baseline_review_packet.json \
  --baseline-report private/reports/lattice_estimator_baseline_run.json \
  --contracts-root .
```

For Sage distributions that expose `sage.all` through an activated environment
Python instead of legacy `sage -python`, pass an explicit no-shell Sage Python
command to both the runtime preflight and the private baseline run:

```bash
uv run agades-pqc lattice-estimator-runtime-preflight \
  --sage-command "/path/to/sage" \
  --sage-python-command "/path/to/python-with-sage-all" \
  --out private/reports/lattice_estimator_runtime_preflight.json \
  --policy docs/private_run_policy.json

uv run agades-pqc lattice-estimator-baseline-run \
  --contracts docs/lattice_estimator_baseline_contracts.json \
  --contracts-root . \
  --out private/reports/lattice_estimator_baseline_run.json \
  --policy docs/private_run_policy.json \
  --estimator-source /path/to/lattice-estimator \
  --sage-python-command "/path/to/python-with-sage-all"

uv run agades-pqc lattice-estimator-baseline-run-verify \
  --report private/reports/lattice_estimator_baseline_run.json \
  --contracts-root .

uv run agades-pqc lattice-estimator-baseline-review-packet \
  --baseline-report private/reports/lattice_estimator_baseline_run.json \
  --out private/reports/lattice_estimator_baseline_review_packet.json \
  --policy docs/private_run_policy.json \
  --contracts-root . \
  --reviewer-label local-lattice-expert-review

uv run agades-pqc lattice-estimator-baseline-review-packet-verify \
  --packet private/reports/lattice_estimator_baseline_review_packet.json \
  --baseline-report private/reports/lattice_estimator_baseline_run.json \
  --contracts-root .
```

The runtime preflight probes only `<sage-command> --version` and
`<sage-python-command> -c 'import sage.all'`. It does not import upstream
Lattice Estimator Python, execute estimator code, run candidates, contact the
network, or write outside the private roots allowed by
`docs/private_run_policy.json`. If Sage is absent or the Sage Python probe
fails, the private report records the reason and exits nonzero before any
numeric baseline attempt.

When `--sage-command` or `--sage-python-command` is supplied to the private
baseline run, Agades executes a small JSON worker under Python with `sage.all`
importable after the checkout preflight has already verified the reviewed Git
pin, upstream origin, clean tree, and estimator entrypoint. This avoids relying
on the `uv` Python environment to import `sage.all`; the public report still
receives only digest/minimal numeric fields under `private/reports/` and remains
blocked from publication.

`agades-pqc lattice-estimator-baseline-run-verify` is the standalone check for
that private report. It re-verifies the referenced baseline contracts, upstream
pin, LWE-only result mapping, private/no-publication policy, raw-output digest
shape, summary counters, and absence of raw estimator or AttackPlan payloads.
It does not promote numeric fields to a public artifact and is intended as the
local gate before expert review.

`agades-pqc lattice-estimator-baseline-review-packet` turns an already verified
private baseline report into the digest-only handoff for expert review. The
packet keeps result identifiers, algorithm keys, upstream pin evidence, source
report digest, raw-output digests, and review questions, while rejecting public
output paths and excluding numeric values, raw estimator payloads, and
AttackPlan payloads. `agades-pqc lattice-estimator-baseline-review-packet-verify`
re-checks those boundaries before the packet is shared with a lattice reviewer.

The checkout path is accepted only after the shared checkout inspection verifies
`git rev-parse HEAD`, `git remote get-url origin`, `git status --porcelain`,
and the estimator entrypoint. Pin mismatch, wrong origin, dirty tree, or missing
entrypoint are rejected before importing the upstream Python package.

The checkout preflight is a private, non-executing review artifact. It records
the local Git HEAD, working-tree cleanliness, origin URL, and estimator package
entrypoint presence without importing `estimator` or running the Lattice
Estimator. Readiness requires the reviewed commit, a clean working tree, and an
origin matching `malb/lattice-estimator`; otherwise the report exits nonzero.
If the subsequent private baseline run cannot import the upstream checkout
(for example because Sage is missing), the private report records a short
exception type/message summary while still writing no public numeric outputs.
