# Agades PQC Gym MVP Report

## 1. Summary

Agades PQC Gym is now structured as a family-agnostic workbench for evaluator-driven cryptanalytic strategy search. Agades LWE Strategy Gym remains the first implemented vertical through the `lattice` adapter.

The MVP demonstrates architecture and reproducible toy evaluation. It does not claim any deployed post-quantum cryptographic standard is broken.

## 2. What Was Built

- Generic `TargetSpec`, `AttackPlan`, and `AttackOperator` schemas.
- Family adapter protocol and default registry.
- Lattice adapter for LWE/MLWE with deterministic mock estimator support.
- Conservative Lattice Estimator boundary.
- Bounded toy evaluator adapters for code-based (`toy-code-based-isd-estimator`, HQC-inspired fixture decoders including circulant-syndrome and erasure-aided syndrome plumbing, Classic-McEliece-inspired binary syndrome and public support-set syndrome plumbing, and `toy-code-based-bit-flip-decoder-estimator`), hash-based (`toy-hash-bound-estimator`), implementation-security (`toy-implementation-security-estimator`), historical-isogeny (`toy-isogeny-historical-path-estimator`, including `toy_volcano_walk_search` graph/path plumbing), and multivariate (`toy-multivariate-estimator`) families.
- Schema-only unsupported placeholders for NTRU/SIS and family/operator combinations without reviewed semantics.
- Cascade evaluator routed by target family.
- Structured unsupported results for families without reviewed estimators.
- JSONL traces, deterministic local evolution archive, archive-driven private mutation batches, public redaction, reporting, CLI, scripts, OpenEvolve adapter, DeepEvolve hooks, and OSS release artifacts.

## 3. Architecture

The runtime flow is:

```text
TargetSpec -> AttackPlan -> schema validation -> family router
  -> family adapter -> estimator result -> fitness metrics
  -> TraceRecord -> public/private redaction -> report
```

The router never uses the lattice estimator for non-lattice families.

## 4. DSL Examples

Implemented lattice examples:

- `examples/attack_plans/lattice_primal_usvp_toy.json`
- `examples/attack_plans/lattice_bdd_toy.json`
- `examples/attack_plans/lattice_dual_attack_toy.json`
- `examples/attack_plans/lattice_dual_hybrid_toy.json`
- `examples/attack_plans/lattice_bkw_toy.json`
- `examples/attack_plans/lattice_downscaled_lwe_instance_solve_toy.json`
- `examples/attack_plans/lattice_downscaled_lwe_instance_solve_n5_q19_toy.json`
- `examples/attack_plans/lattice_downscaled_lwe_instance_solve_n6_q23_ternary_toy.json`
- `examples/attack_plans/lattice_mlwe_module_hypothesis_toy.json`

Toy evaluator examples:

- `examples/attack_plans/code_based_lee_brickell_toy.json`
- `examples/attack_plans/code_based_bjmm_toy.json`
- `examples/attack_plans/code_based_classic_mceliece_support_syndrome_toy.json`
- `examples/attack_plans/code_based_hqc_circulant_erasure_toy.json`
- `examples/attack_plans/code_based_hqc_circulant_syndrome_toy.json`
- `examples/attack_plans/code_based_hqc_erasure_syndrome_toy.json`
- `examples/attack_plans/code_based_hqc_parity_check_toy.json`
- `examples/attack_plans/code_based_hqc_repetition_toy.json`
- `examples/attack_plans/code_based_hqc_weighted_repetition_toy.json`
- `examples/attack_plans/code_based_mdpc_bit_flip_toy.json`
- `examples/attack_plans/code_based_mdpc_black_gray_toy.json`
- `examples/attack_plans/code_based_prange_toy.json`
- `examples/attack_plans/hash_based_preimage_toy.json`
- `examples/attack_plans/hash_based_collision_toy.json`
- `examples/attack_plans/hash_based_fors_auth_path_toy.json`
- `examples/attack_plans/hash_based_signature_toy.json`
- `examples/attack_plans/implementation_security_kat_toy.json`
- `examples/attack_plans/implementation_security_memory_toy.json`
- `examples/attack_plans/implementation_security_timing_toy.json`
- `examples/attack_plans/isogeny_historical_toy.json`
- `examples/attack_plans/isogeny_historical_volcano_walk_toy.json`
- `examples/attack_plans/multivariate_minrank_toy.json`
- `examples/attack_plans/multivariate_mq_hybrid_toy.json`
- `examples/attack_plans/multivariate_mq_toy.json`
- `examples/attack_plans/multivariate_uov_public_map_toy.json`

Schema-only placeholders:

- `examples/attack_plans/code_based_isd_placeholder.json`
- `examples/attack_plans/multivariate_mayo_schema_placeholder.json`
- `examples/attack_plans/multivariate_minrank_placeholder.json`
- `examples/attack_plans/multivariate_rainbow_historical_schema_placeholder.json`
- `examples/attack_plans/hash_based_bound_placeholder.json`
- `examples/attack_plans/isogeny_historical_placeholder.json`
- `examples/attack_plans/implementation_security_constant_time_placeholder.json`

## 5. Evaluator Cascade

Stages implemented:

1. Load and parse AttackPlan JSON.
2. Static validation.
3. Family router lookup.
4. Family-specific estimation or structured unsupported result.
5. Sanity and instability penalties.
6. Scalar fitness and MAP-Elites feature metrics.
7. Trace writing and report generation.

## 6. Example Toy Results

The lattice toy benchmark uses `mock-lattice-estimator` and validates plumbing only.

Code-based, hash-based, implementation-security, historical-isogeny, and multivariate toy examples return bounded toy-estimator output when their `toy_` applicability rules pass. Unsupported schema-only examples return `evaluation_status="unsupported"` with no time/memory estimate.

Public run bundles:

- `code_based_toy_classic_mceliece_v0`
- `code_based_toy_isd_v0`
- `code_based_toy_hqc_v0`
- `code_based_toy_mdpc_v0`
- `hash_based_toy_bound_v0`
- `hash_based_toy_misuse_v0`
- `hash_based_toy_signature_v0`
- `implementation_security_toy_benchmark_v0`
- `implementation_security_toy_kat_v0`
- `implementation_security_toy_timing_v0`
- `isogeny_historical_toy_path_v0`
- `lattice_downscaled_lwe_instance_solve_v0`
- `lattice_downscaled_mlwe_instance_solve_v0`
- `lattice_mlwe_downscaled_v0`
- `lattice_toy_lwe_v0`
- `multivariate_toy_minrank_v0`
- `multivariate_toy_mq_v0`
- `multivariate_toy_uov_v0`

## 7. Mock Vs Real Estimator Status

Mock estimator output is explicitly labeled and is not cryptanalytic evidence.

The optional Lattice Estimator adapter maps reviewed LWE-family operators to explicit estimator algorithm keys, including `primal_usvp -> usvp`, `bounded_distance_decoding -> bdd`, `dual_attack -> dual`, `dual_hybrid -> dual_hybrid`, and `bkw -> bkw`. It supports JSON caching and refuses unsupported mappings. The current upstream pin is recorded in `docs/lattice_estimator_manifest.json`; external expert review and baseline reproduction tests are still required before any public security claim.

The toy non-lattice estimators are intentionally narrow public verifier surfaces. Code-based Prange, Lee-Brickell-style, Stern-style, Dumer-style list-merging, BJMM-style representation-merge, quasi-cyclic rotation, HQC-inspired repetition/weighted-repetition/parity-check/circulant-syndrome/erasure-aided syndrome/circulant-erasure fixture-decoder, Classic-McEliece-inspired binary syndrome and public support-set syndrome fixtures, and MDPC/BIKE-inspired threshold and black-gray bit-flip decoder outputs are evaluator plumbing only; the HQC-inspired fixture decoders are not an HQC result. Hash-based preimage, collision-bound, signature-chain, Merkle auth-path, FORS-inspired auth-path, and `toy_slh_dsa_hypertree_verify` SLH-DSA-like hypertree outputs are evaluator plumbing only and not an SLH-DSA result. Implementation-security KAT, ACVP-like, timing-summary, dudect-style public summary outputs such as `toy_dudect_summary_threshold_check`, ctgrind-style secret-taint summary outputs such as `toy_ctgrind_secret_taint_summary_check`, benchmark-summary, binary-size outputs such as `toy_binary_size_check`, memory-footprint outputs such as `toy_memory_footprint_check`, and stack-usage outputs such as `toy_stack_usage_check` are JSON-only evaluator plumbing; the dudect-style and ctgrind-style summaries validate without executing dudect and without executing ctgrind and make no constant-time, side-channel, or security claim. Historical-isogeny SIDH/SIKE-style, commutative-walk-style, and `toy_volcano_walk_search` graph/path outputs are historical toy fixture plumbing only and not CSIDH, SIDH/SIKE, current-standard, or security results. Multivariate MQ exhaustive-search, MQ hybrid-search, MinRank, and `toy_uov_public_map_verify` UOV-inspired public-map verification outputs are evaluator plumbing only. They are not substitutes for reviewed code-based, hash-based, multivariate, implementation-security, or historical-isogeny research estimators.

## 8. Trace Logging And Moat Separation

Public exports may include schemas, toy traces, benchmark cards, and reports. Private traces, prompts, evaluator weights, unpublished candidates, proprietary paper notes, and collaborator-sensitive drafts remain private.

## 9. OpenEvolve Integration

`examples/openevolve/evaluator.py` evaluates JSON AttackPlan candidates.
`agades-pqc mutate-candidates` generates deterministic private JSON-only
candidate plans from reviewed LWE/MLWE mutation rules for `beta`, `block_size`,
`q_prime`, and `zeta`; reviewed code-based toy ISD knobs including `p`, `ell`,
`representation_count`, and Prange toy target weight `w`; reviewed multivariate
toy MQ knobs including `variables`, `equations`, `guessed_variables`, and
`degree_bound`; reviewed hash-based, implementation-security, and
historical-isogeny toy knobs; and skips schema-only or unsupported families
instead of inventing cross-family operators. The generated plans are marked
`metadata.public=false`, carry no pre-evaluation claims, and can be fed into
`agades-pqc evolve-batch`.

`agades-pqc evolve-batch` evaluates candidate batches, writes trace JSONL, and
builds a deterministic `agades.pqc.evolution_archive.v1` archive that keeps the
best accepted candidate per MAP-Elites feature cell. Python candidate execution
remains unsupported until sandboxing exists.

`agades-pqc mutate-archive` generates the next private mutation batch from
archive elites by resolving each elite back to its exact source `TraceRecord`.
Generated candidates retain `parent_candidate_id` and `parent_trace_id` links,
advance the generation number, clear pre-evaluation claims, and remain
`metadata.public=false`.

`agades-pqc heldout-batch` re-evaluates archive elites on same-family held-out
targets, marks rebased plans private, writes a held-out trace, and immediately
emits an `agades.pqc.heldout_rescore.v1` report. `agades-pqc rescore-archive`
can also aggregate already-produced held-out traces against archive elites.
Held-out records must link to an elite with `TraceRecord.parent_id`; the commands
do not execute arbitrary candidate code or publish private traces.

## 10. DeepEvolve Hooks

PaperCard and HypothesisProposal models support research-layer hypothesis injection. YAML paper cards are loaded from `examples/paper_cards/` and currently cover LWE, MLWE, code-based ISD/HQC-boundary, multivariate MinRank/Groebner-style, hash-based SLH-DSA-boundary, implementation-security harness, and historical-isogeny directions. Hypotheses remain review-gated and do not certify estimator truth.

## 11. Community Release Plan

- Hugging Face: toy dataset, Space skeleton, Collection manifest, benchmark card, public benchmark v0 manifest, and linked flat public run export.
- Prime Intellect: executable verifier wrapper, environment card, public benchmark v0 bundle map, flat public run export, benchmark source contracts, and future run-ledger compatibility.
- NVIDIA/accelerators: evaluator/agent harness positioning, benchmark manifest/export pointers, and future TAPAS/LWE-benchmarking plus implementation-security source contracts, not private-trace publication.

## 12. Collaboration Plan

Initial collaboration briefs remain focused on ASI Labs, Martin Albrecht, and Leo Ducas. No outreach has been sent automatically.

## 13. Limitations

- Optional real Lattice Estimator calls exist for reviewed LWE-family mappings; MLWE flattening remains warning-gated for expert review.
- Non-lattice implemented surfaces are bounded toy evaluators only; unsupported or non-toy public placeholders remain schema-only.
- Downscaled reproduction has three tiny public LWE fixture-solving cases in the bounded exhaustive-search harness, including the ternary-secret `toy_lwe_n6_q23_ternary_instance`; broader TAPAS/LWE-benchmarking-style reproduction and real implementation-security KAT/ACVP/timing/benchmark execution, including PQ Code Package native implementation workflows, the `nist_acvp_pqc_vectors_schema` ACVP server/vector-source placeholder, plus dudect, ctgrind, and TIMECOP/SUPERCOP constant-time source contracts, are represented only as future reviewed schema-only benchmark source contracts with no ACVP, conformance, side-channel, or security claim and no constant-time, side-channel, or security claim.
- Mock scores are not evidence.

## 14. Next 30/60/90-Day Roadmap

30 days: complete external review of the pinned Lattice Estimator mapping, package Prime/HF demo artifacts, and publish the checked public benchmark v0 card/manifest after release review.

60 days: reproduce known LWE estimator baselines, implement reviewed TAPAS/LWE-benchmarking and real implementation-security KAT/ACVP/timing/benchmark adapters behind the checked benchmark source contracts, including PQ Code Package native implementation gates, NIST ACVP vector-provenance and ACVP server review gates, plus dudect, ctgrind, and TIMECOP/SUPERCOP methodology gates, and expand downscaled reproduction beyond the current tiny public fixtures.

90 days: run a private DeepEvolve-style research loop, collect private traces, add independent sanity checks, and prepare a reviewed public report.
