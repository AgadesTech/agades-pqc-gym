# Roadmap

## Current Public Baseline

- Family-agnostic `AttackPlan` DSL, `TargetSpec`, evaluator result,
  trace, report, redaction, and release-audit surfaces are implemented under
  `agades_pqc_gym`.
- LWE/MLWE are the first implemented verticals. The Lattice Estimator boundary
  is scoped to lattice work and is not treated as a universal PQC oracle.
- `docs/lattice_estimator_baseline_contracts.json` records
  `review_contract_ready_not_reproduced` contracts for the reviewed direct LWE
  mappings; this is not a numeric Lattice Estimator baseline reproduction and
  keeps numeric outputs, publication, and security claims blocked until expert
  review.
- `agades-pqc lattice-estimator-baseline-run` now provides the private
  pin-checked execution path for those contracts, writing numeric outputs only
  under allowed private roots and digesting raw estimator payloads instead of
  publishing them.
- `agades-pqc lattice-estimator-baseline-run-verify` now provides a standalone
  private report verifier for expert review, checking contract sync, pin
  consistency, digest-only raw payload handling, no-publication flags, and
  LWE-only scope without promoting numeric fields into public artifacts.
- `agades-pqc lattice-estimator-baseline-review-packet` now creates the private
  digest-only expert-review handoff from a verified baseline run, carrying
  source report digests, raw-output digests, upstream pin evidence, review
  questions, and no-publication flags while rejecting numeric leakage or
  public output paths.
- A local private Sage 10.8 Conda reproduction has run the five reviewed direct
  LWE mappings against the checked `malb/lattice-estimator` pin. The results
  remain private, digest raw estimator payloads, and do not create public
  reference baselines or security claims.
- Private baseline runs can now use `--estimator-source` to load a reviewed
  local `malb/lattice-estimator` checkout; the adapter verifies the checked
  HEAD, upstream origin, clean working tree, and estimator entrypoint before
  importing upstream Python.
- Private baseline runs can use legacy `--sage-command sage` for `sage -python`
  environments or `--sage-python-command <python-with-sage-all>` for conda-style
  Sage installations.
- `agades-pqc lattice-estimator-checkout-preflight` now writes a private,
  non-executing review report for local `malb/lattice-estimator` checkouts,
  proving the Git HEAD, origin, clean-tree state, and estimator entrypoint
  before any private baseline run imports upstream Python.
- Non-lattice families have public toy evaluators and validators for
  code-based, multivariate, hash-based, historical-isogeny, and
  implementation-security plans.
- Public benchmark v0 currently contains 18 public benchmark bundles and
  59 accepted public records across LWE, MLWE, code-based, multivariate,
  hash-based, historical-isogeny, and implementation-security families.
- Downscaled lattice reproduction includes three tiny public LWE fixture-solving
  records, including the ternary-secret `toy_lwe_n6_q23_ternary_instance`, plus
  a tiny MLWE fixture.
- The Hugging Face dataset/card artifacts, Hugging Face Space manifest with
  79 Hugging Face Space examples, Hugging Face collection manifest, Prime
  environment card, Prime verifier package, NVIDIA accelerator manifest, and
  publication manifest are generated and audited.
- Prime Intellect alignment currently covers 79 Prime JSON verifier tasks,
  the Prime quickstart, the autonomous speedrunning experiments repository,
  and the Auto-NanoGPT speedrun anchor through reviewed release-plan docs.
- Prime Hub publication remains credentialed and review-gated. No public push
  to Prime or Hugging Face should happen without the release checklist and
  credentials review.
- `docs/external_publication_review_packet.json` now gives reviewers one
  digest-backed public handoff for Hugging Face, Prime Intellect, and NVIDIA
  surfaces, preserving the default blocked state until credential and release
  review are explicit.
- `docs/private_run_policy.json` now records the private-run defaults,
  allowed private roots, forbidden public roots, and redaction/preflight gates
  for future private evolution traces, including disabled-by-default scheduler
  triggers, retention limits, approval gates, and execution-safety rules.
- `agades-pqc private-evolution-campaign-plan` now writes a reviewed,
  private-only, non-executing argv manifest for the long-running
  seed/archive/snapshot/held-out campaign loop before any private trace
  collection starts, including seed mutation preflight counts without
  embedding candidate payloads and a target-family compatibility preflight
  that requires held-out coverage for every seed family.
- `agades-pqc heldout-review-log` now records durable private approval
  evidence, and `agades-pqc heldout-schedule --review-log ...` turns an
  archive/source trace/held-out target set into a reviewed private schedule
  manifest that consumes that policy before any held-out batch is run.
- `agades-pqc heldout-run-schedule` now consumes reviewed private schedule
  manifests through typed Python APIs without executing stored shell command
  strings, external networking, or public trace outputs.
- `agades-pqc heldout-review-packet` now writes a private digest-only review
  handoff for scheduled held-out trace/rescore outputs, explicitly excluding
  trace payloads, AttackPlans, candidate sources, and private scores.
- `agades-pqc heldout-cron-plan` now writes private local-cron plans for
  already-reviewed `local_cron_after_review` manifests, requiring manual
  installation and preserving stable review-log, retention, no-network, and
  private-output boundaries.
- `agades-pqc archive-snapshot` now writes private digest-only archive
  snapshots after review-log approval, recording archive/source-trace digests,
  retention limits, and archive-to-trace link integrity without copying private
  trace payloads or AttackPlans into public artifacts.
- `agades-pqc deepevolve-injections` now turns public `note_only` PaperCards
  into a private review-gated hypothesis injection queue under allowed private
  roots without writing AttackPlans, executing code, changing estimator scores,
  publishing candidates, or making research claims.
- The source-contract catalog contains 18 future reviewed adapter source
  contracts, including TAPAS/LWE-benchmarking, Hugging Face PQC/SCA dataset
  anchors, HQC, BIKE, Classic McEliece, SLH-DSA, multivariate, liboqs,
  PQ Code Package, pqm4, ACVP, dudect, ctgrind, and TIMECOP/SUPERCOP
  constant-time surfaces.

## Future Reviewed Work

- Review the private Sage 10.8 baseline-run evidence with a lattice expert
  before any numeric reference is promoted beyond `private/reports/`.
- Promote selected private baseline-run outputs into public reference baselines
  only after expert review approves methodology, parameters, and claim language.
- Implement reviewed TAPAS and LWE-benchmarking adapters behind the checked
  source contracts.
- Implement reviewed implementation-security KAT, ACVP, timing, memory,
  binary-size, and benchmark adapters behind source contracts.
- Expand downscaled lattice reproduction beyond the current three tiny public
  LWE fixtures only after parameter mapping and claim boundaries are reviewed.
- Start collecting private evolution traces with held-out batch runs after the
  checked-in private-run policy, snapshot retention policy, and redaction gates
  are reviewed for the specific run.
- Prepare credentialed Prime and Hugging Face publication runs from the checked
  manifests once external review signs off.

## Expert Review Track

- Review private paper-card injection batches and promote only externally
  reviewed hypotheses into candidate AttackPlan/operator work.
- Search across several LWE/MLWE settings.
- Extend the same validator/evaluator/release-gate pattern to HQC, BIKE,
  Classic McEliece, multivariate signatures, SLH-DSA, and implementation
  security when reviewed adapters exist.
- Add independent sanity checks for every family-specific estimator before any
  security claim is made.
- Produce a public Agades technical report only after expert review.
