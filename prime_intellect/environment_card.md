# Environment Card: Agades PQC Gym

## Summary

Agades PQC Gym is a verifier-style environment where an agent submits an AttackPlan JSON and receives validation, routing, estimator status, fitness metrics, and trace metadata.

This is designed to fit Prime Intellect's environment/evaluation surface: deterministic tasks, explicit verifier outputs, run ledgers, and later distributed search.

## Observation

- Target family and target parameters.
- Allowed operators for the selected family.
- Constraints, assumptions, and support level.
- Prior public toy results.
- Responsible research boundaries.

## Action

Submit a modified AttackPlan JSON file. The MVP does not execute arbitrary Python candidates.

Executable wrapper:

```bash
python prime_intellect/verifier.py examples/attack_plans/lattice_primal_usvp_toy.json
```

Prime Verifiers environment package:

```bash
cd prime_intellect/verifiers_environment
uv pip install -e .
prime eval run agades-pqc-verifier-env
```

Credentialed eval template:

```bash
uv run agades-pqc prime-eval-config --config prime_intellect/evals/agades_pqc_eval.template.toml --manifest docs/prime_eval_config_manifest.json
uv run agades-pqc prime-eval-config-verify --config prime_intellect/evals/agades_pqc_eval.template.toml --manifest docs/prime_eval_config_manifest.json
```

The template is review-gated and uses `AGADES_PRIME_ENV_REF` plus
`AGADES_EVAL_MODEL`; it does not include credentials and does not claim external
Prime execution.

Prime quickstart alignment for credentialed review:

```bash
uv tool install -U prime
prime login
prime lab setup
prime eval run primeintellect/reverse-text -m openai/gpt-oss-20b -p prime -n 1 -r 1 -t 512 -s -A
prime eval run primeintellect/aime2026 -m openai/gpt-oss-20b -p prime -n 1 -r 1 -t 2048 -s -A
prime eval run <owner>/agades-pqc-verifier-env
```

The checked-in handoff records these commands as public Quickstart references;
external Prime execution has not been performed, and no credential material is
read or stored by Agades artifacts.

The packaged environment embeds all valid public AttackPlan examples as
single-turn tasks, not just the lattice MVP seed. Bounded toy evaluator
families receive normal verifier scores when their applicability rules pass.
Unsupported schema-only tasks remain useful as routing/safety checks and
receive zero reward instead of fabricated cryptanalytic estimates.
Rewards are task-aware through `agades.pqc.task_metadata.v6`: each task records
the seed AttackPlan SHA-256 digest, and a candidate must still match the current
task's target family, target name, support level, ordered operator types,
ordered operator params, and ordered operator assumptions.
Rows also expose seed verifier status, seed reward, seed estimator, and seed
reproduction status, so unsupported schema-only seeds are explicit `0.0`-reward
tasks and fixture-backed seeds are inspectable rather than ambiguous accepted
examples. This allows renaming inside the same task while preventing a rollout
from scoring by pasting an unrelated valid public AttackPlan or changing attack
parameters in repair tasks. Semantic-mutation tasks may change operator params
only when the challenge explicitly requires a semantic variant.
The generated Prime manifest includes the same deterministic task summary by
family, support level, seed verifier status/reward, seed estimator, and
reproduction status that the Hugging Face dataset publishes, making packaged
task coverage auditable without replaying the full verifier.

Public run ledger packaging:

```bash
uv run agades-pqc public-ledger runs/toy_benchmark.jsonl --out public/toy_run_ledger.json
uv run agades-pqc public-bundle runs/toy_benchmark.jsonl --out public/toy_run_bundle
```

Stable verifier JSON schemas:

```bash
uv run agades-pqc prime-schemas --out prime_intellect/schemas
```

The checked-in schema bundle contains `attack_plan.schema.json`,
`task_metadata.schema.json`, `verifier_result.schema.json`, and
`schema_manifest.json`. These files define the single-object AttackPlan
submission contract, shared task metadata constraints, and deterministic
verifier result contract used by Prime, Hugging Face, and the CLI wrapper.

Public benchmark v0 manifest:

```bash
uv run agades-pqc public-benchmark-manifest --out docs/public_benchmark_manifest.json
```

The checked-in benchmark manifest records all current public run bundles,
regeneration commands, public trace digests, checksum-manifest digests, and
no-claim safety flags for Prime-facing review.

The current public bundle set is `code_based_toy_classic_mceliece_v0`,
`code_based_toy_hqc_v0`, `code_based_toy_isd_v0`,
`code_based_toy_mdpc_v0`, `hash_based_toy_bound_v0`,
`hash_based_toy_misuse_v0`, `hash_based_toy_signature_v0`,
`implementation_security_toy_benchmark_v0`,
`implementation_security_toy_kat_v0`,
`implementation_security_toy_timing_v0`, `isogeny_historical_toy_path_v0`,
`lattice_downscaled_lwe_instance_solve_v0`,
`lattice_downscaled_mlwe_instance_solve_v0`, `lattice_mlwe_downscaled_v0`,
`lattice_toy_lwe_v0`, `multivariate_toy_minrank_v0`,
`multivariate_toy_mq_v0`, and `multivariate_toy_uov_v0`.

```bash
uv run agades-pqc public-benchmark-verify --manifest docs/public_benchmark_manifest.json
```

## Reward

Prime reward is binary and task-aware: `1.0` only for a single JSON AttackPlan that is accepted by the verifier and matches the current task constraints; otherwise `0.0`. The verifier still returns `combined_score` for implemented families. Unsupported schema-only families return `evaluation_status="unsupported"` and `combined_score=-1e9` without fake time/memory estimates.

## Current Families

- LWE/MLWE: implemented MVP through the lattice adapter.
- code-based: bounded toy Prange, Lee-Brickell-style, Stern-style, Dumer-style list-merging, BJMM-style representation-merge, quasi-cyclic rotation, HQC-inspired repetition/weighted-repetition/parity-check/circulant-syndrome/erasure-aided syndrome/circulant-erasure decoders, tiny Classic-McEliece-inspired binary syndrome and public support-set syndrome decoders, and tiny MDPC/BIKE-inspired threshold, black-gray, and syndrome-weight bit-flip fixture decoders through `toy-code-based-isd-estimator`, `toy-code-based-repetition-decoder-estimator`, `toy-code-based-weighted-repetition-decoder-estimator`, `toy-code-based-parity-check-decoder-estimator`, `toy-code-based-circulant-syndrome-decoder-estimator`, `toy-code-based-erasure-syndrome-decoder-estimator`, `toy-code-based-circulant-erasure-decoder-estimator`, `toy-code-based-classic-mceliece-syndrome-estimator`, `toy-code-based-classic-mceliece-support-syndrome-estimator`, and `toy-code-based-bit-flip-decoder-estimator`; the HQC-inspired decoders are not an HQC result.
- hash-based: bounded toy preimage, collision-bound, signature-chain, Merkle auth-path, FORS-inspired auth-path, `toy_slh_dsa_hypertree_verify` SLH-DSA-like hypertree fixture plumbing, and reused-salt misuse surfaces through `toy-hash-bound-estimator`; the hypertree surface is not an SLH-DSA result.
- implementation-security: JSON-only toy KAT, ACVP-like vector-set, timing-summary, dudect-style public summaries through `toy_dudect_summary_threshold_check`, ctgrind-style secret-taint summaries through `toy_ctgrind_secret_taint_summary_check`, benchmark-summary, binary-size, memory-footprint, and stack-usage surfaces through `toy-implementation-security-estimator`, including `toy_binary_size_check` for bounded public binary-size summaries, `toy_memory_footprint_check` for bounded public component-byte summaries, and `toy_stack_usage_check` for bounded public high-water stack samples. The dudect-style and ctgrind-style summaries validate without executing dudect and without executing ctgrind and make no constant-time, side-channel, or security claim.
- historical-isogeny: historical SIDH/SIKE-style, commutative-walk-style, and `toy_volcano_walk_search` graph/path fixture surfaces through `toy-isogeny-historical-path-estimator`; not CSIDH, SIDH/SIKE, current-standard, or security results.
- multivariate: bounded toy MQ exhaustive-search, MQ hybrid-search, MinRank, and `toy_uov_public_map_verify` UOV-inspired public-map verification surfaces through `toy-multivariate-estimator`.
- NTRU/SIS and unsupported public placeholders remain schema-only until reviewed.

## Prime Intellect Roadmap

1. Test the Verifiers environment with Prime CLI credentials.
2. Publish the checked-in public toy/downscaled run bundle artifacts from `docs/public_benchmark_manifest.json` after release review.
3. Keep the checked-in Prime schema bundle synchronized through CI and release audit.
4. Keep serious private evolution traces out of public uploads.
