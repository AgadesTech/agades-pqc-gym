# Architecture

Agades PQC Gym is a multi-family cryptanalysis workbench. The product is not lattice-only; lattice is the first executable vertical because LWE/MLWE has the strongest public estimator substrate.

## Runtime Flow

```text
TargetSpec
  -> AttackPlan
  -> AssumptionSet
  -> schema validation
  -> family router
  -> family-specific applicability validation
  -> estimator adapter
  -> EvaluatorResult
  -> sanity checks
  -> fitness metrics
  -> TraceRecord
  -> evolution archive / MAP-Elites cell update
  -> public/private redaction
  -> report generator
```

Every implemented or planned family plugin exposes an explicit
`families/<plugin>/validators.py` module for applicability checks. The runtime
adapters still own evaluation, but machine-readable catalogs point at these
validator functions so reviewers can distinguish family validation from the
lattice/LWE estimator boundary.

Each family plugin also exposes an importable `families/<plugin>/plugin.py`
descriptor. These descriptors declare the plugin-owned `TargetFamily` values,
adapter class path, support level, and applicability validator path consumed by
the operator catalog and runtime registry manifest, avoiding a separate
lattice-centric source of truth for plugin boundaries.

The checked-in `docs/family_plugin_manifest.json` is the public contract for
that descriptor layer. It is regenerated with `agades-pqc
family-plugin-manifest` and verified with `agades-pqc
family-plugin-manifest-verify`, which checks plugin/family coverage, importable
descriptor, adapter, and validator paths, and rejects non-lattice plugins that
drift toward lattice validators or the Lattice Estimator boundary.

## Core

- `agades_pqc_gym.core.target`: family-aware `TargetSpec`.
- `agades_pqc_gym.core.attack_plan`: typed `AttackPlan` and finite `AttackOperator` list.
- `agades_pqc_gym.core.assumptions`: deterministic `AssumptionSet` summaries, risk scoring, and fingerprints for evaluator features.
- `agades_pqc_gym.core.evaluator_result`: schema-versioned family-agnostic
  `EvaluatorResult` contract emitted by lattice and non-lattice evaluators.
  The legacy `EstimatorResult` import is an alias of this core model.
- `agades_pqc_gym.core.fitness`: schema-versioned `FitnessReport` contract emitted by evaluator cascades and trace metrics.
- `agades_pqc_gym.core.trace_record`: schema-versioned family-agnostic
  `TraceRecord` contract for evaluation traces and public/private trace
  export. The legacy `agades_pqc_gym.traces.schema.TraceRecord` import is an
  alias of this core model.
- `agades_pqc_gym.core.family_adapter`: adapter protocol and validation finding types.
- `agades_pqc_gym.core.registry`: default registry for family adapters.
- `agades_pqc_gym.reporting.generator`: family-agnostic `ReportGenerator`
  that normalizes typed `TraceRecord` objects or JSON-compatible trace rows,
  summarizes family/reproduction/estimator status, and redacts private trace
  target, family, attack, and mutation details by default.
- `agades_pqc_gym.traces.redaction`: public/private redaction boundary for
  `TraceRecord` export. Public records are preserved; private records keep only
  stable run linkage, a minimal AttackPlan id, generic redaction reason, and a
  redacted evaluation envelope with no score, estimator label, raw output,
  warnings, feature fields, or accepted/rejected signal.

## First Vertical

`families/lattice` supports LWE/MLWE in the MVP using a deterministic mock estimator by default. The Lattice Estimator adapter is conservative and must not fabricate unsupported mappings.

The checked-in Lattice Estimator baseline contracts remain public and non-numeric. `agades-pqc lattice-estimator-baseline-run` consumes those contracts only under allowed private roots, requires the reviewed upstream commit pin for successful numeric results, stores raw estimator payloads by digest only, and keeps publication/security flags false until expert review promotes a result.

For reviewed private reproductions, `agades-pqc lattice-estimator-checkout-preflight` first records a private, non-executing readiness report for a local `malb/lattice-estimator` checkout. Readiness requires the checked Git HEAD, an upstream origin remote, a clean working tree, and an `estimator` entrypoint without importing upstream Python. The baseline runner can then load the checkout with `--estimator-source`; the adapter reuses the same checkout inspection and rejects pin, origin, dirty-tree, or entrypoint failures before importing the upstream `estimator` package, so a local path cannot silently replace or modify the checked estimator source. When `--sage-command` or `--sage-python-command` is supplied, that import and LWE estimate run inside a separate no-shell JSON worker under Python with `sage.all` importable; legacy Sage installs can use the default `sage -python` command, while conda-style installs can provide an explicit environment-aware Python command. This matches the runtime preflight and avoids assuming Sage is importable from the project’s ordinary `uv` Python.

## Non-Lattice Toy Evaluators

`families/code_based` includes bounded toy evaluators for public integration: `information_set_decoding` with `variant="prange_toy"`, `variant="lee_brickell_toy"`, `variant="stern_toy"`, `variant="dumer_toy"`, `variant="bjmm_toy"`, or `variant="qc_rotation_toy"` on small `toy_` syndrome-decoding targets, plus `decoding_fixture_check` with `variant="hqc_repetition_toy"`, `variant="hqc_weighted_repetition_toy"`, `variant="hqc_parity_check_toy"`, `variant="hqc_circulant_syndrome_toy"`, `variant="hqc_erasure_syndrome_toy"`, `variant="classic_mceliece_syndrome_toy"`, `variant="classic_mceliece_support_syndrome_toy"`, `variant="mdpc_bit_flip_toy"`, or `variant="mdpc_black_gray_bit_flip_toy"` for tiny HQC-inspired, Classic-McEliece-inspired, or MDPC/BIKE-inspired fixture checks. These variants use conservative work-factor or fixture-decoder models and exist to prove that non-lattice families have their own validator and estimator boundary.

This evaluator is intentionally not a production code-based cryptanalysis oracle. It rejects larger/non-toy targets, keeps real HQC, Classic McEliece, and BIKE parameter mappings schema-only/review-gated, and emits warnings that the output is not an HQC, Classic McEliece, BIKE, or security result.

`families/multivariate` includes bounded toy evaluators for public integration: `groebner_basis` with `model="toy_mq_search"`, `model="toy_mq_hybrid_search"`, or `model="toy_mq_degree_bound"` on small `toy_` multivariate quadratic targets, `minrank_attack` with `model="toy_minrank_search"` on tiny public matrix-pencil fixtures, and `signature_fixture_check` with `signature_model="toy_uov_public_map_verify"` on a tiny UOV-inspired public-map verification fixture. They compute simple exhaustive-search, hybrid linearization-style, degree-bound, MinRank, or public-map verification toy estimates from the declared field order and target shape so the multivariate family exercises its own validator, estimator result, public trace, Hugging Face, Prime, NVIDIA, and publication paths.

These evaluators are intentionally not production MQ, Groebner-basis, MinRank, UOV, MAYO, or Rainbow cryptanalysis oracles. They reject larger/non-toy targets, keep real UOV/MAYO/Rainbow parameter mappings schema-only, and emit warnings that the output is not a security claim.

`families/hash_based` includes bounded toy evaluators for public integration: `security_bound_check` with `bound_model="toy_preimage_bound"` or `bound_model="toy_collision_bound"` on small `toy_` hash-bound targets, `hash_signature_verification` with `signature_model="toy_wots_chain_verify"`, `signature_model="toy_merkle_auth_path_verify"`, `signature_model="toy_fors_auth_path_verify"`, or `signature_model="toy_slh_dsa_hypertree_verify"` for tiny public chain/auth-path/FORS-inspired/SLH-DSA-like hypertree verification fixtures, and `misuse_check` with `fixture="toy_hash_reused_salt"` for a public JSON-only reused-salt fixture. These compute simple preimage, birthday-collision, chain-verification, Merkle auth-path, FORS auth-path, SLH-DSA-like hypertree, or reused-salt signals from declared toy parameters so the hash family exercises its own validator, estimator result, public trace, Hugging Face, Prime, NVIDIA, and publication paths.

This evaluator is intentionally not a production hash-based cryptanalysis oracle. It rejects larger/non-toy targets, keeps real SLH-DSA-style placeholders schema-only, and emits warnings that the output is not an SLH-DSA result and not a security claim.

`families/implementation_security` includes bounded toy evaluators for public integration: `kat_conformance` with `model="toy_kat_digest_match"` on small JSON-only `toy_` KAT digest manifests, `kat_conformance` with `model="toy_acvp_vector_set_match"` on bounded ACVP-like vector-set manifests, `constant_time_check` with `model="toy_timing_welch_t_check"` on bounded public timing summary arrays, `constant_time_check` with `model="toy_dudect_summary_threshold_check"` on public dudect-style JSON summaries, `constant_time_check` with `model="toy_ctgrind_secret_taint_summary_check"` on public ctgrind-style secret-taint JSON summaries, and `benchmark_harness` with `model="toy_benchmark_summary_check"`, `model="toy_binary_size_check"`, `model="toy_memory_footprint_check"`, or `model="toy_stack_usage_check"` on bounded public benchmark, binary-size, memory-footprint, or stack-usage summary arrays. These surfaces recompute only public JSON summaries, refuse live artifact parameters, and exercise the implementation-security validator, estimator result, public trace, Hugging Face, Prime, NVIDIA, and publication paths without executing code; the dudect-style and ctgrind-style summary surfaces validate without executing dudect and without executing ctgrind.

This evaluator is intentionally not a production conformance, benchmark, constant-time, side-channel, or implementation-security oracle. It rejects live targets and larger/non-toy inputs, keeps real benchmark-harness, dudect, ctgrind, and policy-tool execution outside the public verifier, and emits warnings that the output is not a security claim. Public schema-only placeholders for `nist_acvp_pqc_vectors_schema`, real dudect timing leakage, real ctgrind secret-taint analysis, and TIMECOP/SUPERCOP keep the future source contracts visible without executing an ACVP server, timing tools, taint tools, or policy tools; they make no ACVP, conformance, side-channel, or security claim and no constant-time, side-channel, or security claim.

## Downscaled Reproduction Boundary

The cascade can request a family adapter to run `reproduce_downscaled(plan)` when an AttackPlan sets `constraints.require_reproducibility_on_downscaled_instances=true`.

For the lattice MVP, this path is deliberately narrow:

- the plan metadata must be public;
- the target family must be LWE or MLWE;
- the target name must be marked as `toy` or `downscaled`;
- the flattened lattice dimension must stay at or below 1024.

For non-lattice toy plugins, positive reproduction requires an explicit public
fixture scoped to that family's benchmark fixture directory. Code-based,
multivariate, hash-based, historical-isogeny, and implementation-security
fixtures have separate validators and no-claim boundaries.

`reproduction_status="estimator_reproduced"` means the deterministic evaluator
output was replayed twice under the declared time and memory constraints.
`reproduction_status="instance_solved"` is currently limited to tiny public
fixtures solved or verified by reviewed family-specific harnesses. Both statuses
are public plumbing evidence only, not deployed-parameter security claims. Other
PQC families must define their own applicability checks and reproduction
semantics before returning a positive reproduction status.

## Evolution Archive

`agades_pqc_gym.evolution.archive` builds a deterministic MAP-Elites-style
archive from `TraceRecord` objects. The default cell dimensions are family,
attack type, memory bucket, assumption bucket, and estimator model. Invalid or
unsupported candidates remain in the trace, but only accepted evaluations can
become elites. Ties are broken deterministically by candidate id.

`agades_pqc_gym.evolution.heldout` builds private held-out candidate plans from
an archive, the source trace that produced that archive, and reviewed held-out
target configs. It only rebases same-family `TargetSpec` values, refuses
pre-evaluation claims and target-specific reproduction constraints, marks
rebased plans private, and preserves explicit parent links back to archive
elites. `agades_pqc_gym.evolution.rescore` then builds a deterministic held-out
report from an archive plus already-produced held-out `TraceRecord` objects. A
held-out record only applies to an elite when `TraceRecord.parent_id` equals the
elite candidate id. `agades_pqc_gym.evolution.scheduler` writes a reviewed
private schedule manifest from `docs/private_run_policy.json` before automated
held-out work is allowed. `agades_pqc_gym.evolution.cron` can then write a
private local-cron plan for manual installation without editing the system
crontab. `agades_pqc_gym.evolution.snapshot` writes a private digest-only
archive snapshot manifest that records file hashes, review-log evidence,
retention limits, and archive-to-trace link integrity without copying trace
records, AttackPlans, or private candidate payloads. The rescore layer
aggregates accepted held-out scores and reports
missing or rejected held-out evaluations; it does not synthesize targets,
publish private traces, or execute arbitrary code.

The local batch command:

```bash
uv run agades-pqc evolve-batch benchmarks/lattice_toy_lwe \
  --trace-out runs/evolution_trace.jsonl \
  --archive-out runs/evolution_archive.json

uv run agades-pqc deepevolve-injections \
  --out private/candidates/paper_card_injections.json \
  --policy docs/private_run_policy.json \
  --paper-card-dir examples/paper_cards

uv run agades-pqc heldout-review-log \
  --out private/runs/heldout_review_log.json \
  --approval private-run-policy-review \
  --approval heldout-target-review \
  --approval retention-owner-review \
  --approval publication-export-review

uv run agades-pqc archive-snapshot runs/evolution_archive.json \
  runs/evolution_trace.jsonl \
  --out private/runs/archive_snapshot.json \
  --review-log private/runs/heldout_review_log.json \
  --policy docs/private_run_policy.json

uv run agades-pqc heldout-schedule runs/evolution_archive.json \
  runs/evolution_trace.jsonl \
  benchmarks/lattice_toy_lwe \
  --out private/runs/heldout_schedule.json \
  --trace-out private/traces/heldout_trace.jsonl \
  --rescore-out private/reports/heldout_rescore.json \
  --review-log private/runs/heldout_review_log.json \
  --trigger local_cron_after_review \
  --approval private-run-policy-review \
  --approval heldout-target-review \
  --approval retention-owner-review \
  --approval publication-export-review

uv run agades-pqc heldout-cron-plan private/runs/heldout_schedule.json \
  --out private/runs/heldout_cron_plan.json \
  --policy docs/private_run_policy.json \
  --minute 17 \
  --every-hours 6 \
  --log-path private/runs/heldout_cron.log

uv run agades-pqc heldout-run-schedule private/runs/heldout_schedule.json \
  --policy docs/private_run_policy.json

uv run agades-pqc heldout-batch runs/evolution_archive.json \
  runs/evolution_trace.jsonl \
  benchmarks/lattice_toy_lwe \
  --trace-out runs/heldout_trace.jsonl \
  --rescore-out runs/heldout_rescore.json

uv run agades-pqc rescore-archive runs/evolution_archive.json \
  runs/heldout_trace.jsonl \
  --out runs/heldout_rescore.json
```

This is a local search substrate, not a public claim surface. Serious evolution
traces remain private unless explicitly redacted into public bundles.

## Reporting Boundary

`ReportGenerator` is part of the family-agnostic core surface. Public reports
are rendered from typed traces or JSONL rows, include family, target,
reproduction, estimator, and status summaries for public records, and count
private rows without exposing private target names, family labels, attack
details, mutation summaries, scores, estimator names, raw outputs, or
accepted/rejected status. `render_report` remains as the CLI-compatible wrapper
around the generator.

## Placeholder Families

NTRU/SIS in the lattice plugin validate public schema-only targets and return `evaluation_status="unsupported"` until reviewed mappings exist. Historical isogeny plugins validate schemas and return `evaluation_status="unsupported"` outside their historical toy surface. Code-based, multivariate, hash-based, and implementation-security still return unsupported for schema-only placeholders outside their bounded toy surfaces. This preserves extensibility without pretending to have estimators, conformance engines, or side-channel harnesses that do not exist yet.

## Invariant

Never reuse a lattice estimator as if it applied to another family.
