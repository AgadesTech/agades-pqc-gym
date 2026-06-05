# Dataset Card: Agades PQC Gym Toy AttackPlans

## Summary

This dataset contains public toy and schema-only AttackPlan examples for Agades PQC Gym.

## Contents

- LWE/MLWE toy AttackPlans with mock-estimator outputs, including one public downscaled reproduction smoke example, three tiny public LWE instance-solving fixture examples, and one tiny public linearized MLWE fixture-solving example.
- Invalid examples for validator tests.
- Bounded toy evaluator examples for code-based (`toy-code-based-isd-estimator`, including Prange, Lee-Brickell-style, Stern-style, Dumer-style list-merging, BJMM-style representation-merge, and quasi-cyclic rotation surfaces, `toy-code-based-repetition-decoder-estimator`, `toy-code-based-weighted-repetition-decoder-estimator`, `toy-code-based-parity-check-decoder-estimator`, `toy-code-based-circulant-syndrome-decoder-estimator`, `toy-code-based-erasure-syndrome-decoder-estimator`, and `toy-code-based-circulant-erasure-decoder-estimator` for HQC-inspired fixtures; not an HQC result, `toy-code-based-bit-flip-decoder-estimator` for tiny MDPC/BIKE-inspired threshold and black-gray bit-flip fixtures, plus `toy-code-based-classic-mceliece-syndrome-estimator` and `toy-code-based-classic-mceliece-support-syndrome-estimator` for tiny Classic-McEliece-inspired binary syndrome and public support-set fixtures), hash-based (`toy-hash-bound-estimator`, including preimage, collision-bound, signature-chain, Merkle auth-path, FORS-inspired auth-path, `toy_slh_dsa_hypertree_verify` SLH-DSA-like hypertree fixture plumbing, and reused-salt misuse fixtures/surfaces; not an SLH-DSA result), implementation-security (`toy-implementation-security-estimator`, including JSON-only ML-KEM/ML-DSA KAT and ACVP-like vector-set checks, timing, dudect-style public summaries such as `toy_dudect_summary_threshold_check`, ctgrind-style secret-taint summaries such as `toy_ctgrind_secret_taint_summary_check`, benchmark-summary, binary-size fixtures such as `toy_binary_size_check`, memory-footprint fixtures such as `toy_memory_footprint_check`, and stack-usage fixtures such as `toy_stack_usage_check`; the dudect-style and ctgrind-style summary surfaces validate without executing dudect and without executing ctgrind and make no constant-time, side-channel, or security claim), historical-isogeny (`toy-isogeny-historical-path-estimator`, including SIDH/SIKE-style, commutative-walk-style, and `toy_volcano_walk_search` graph/path fixture plumbing; not a CSIDH, SIDH/SIKE, current-standard, or security result), and multivariate (`toy-multivariate-estimator`, including MQ exhaustive-search, MQ hybrid-search, MinRank, and `toy_uov_public_map_verify` UOV-inspired public-map verification surfaces) surfaces.
- Schema-only placeholders for unsupported or future-reviewed family surfaces.
- Byte-reproducible public run ledger JSON and checksum manifests for toy/downscaled benchmark reproducibility.
- Public run bundles: `code_based_toy_classic_mceliece_v0`, `code_based_toy_hqc_v0`, `code_based_toy_isd_v0`, `code_based_toy_mdpc_v0`, `hash_based_toy_bound_v0`, `hash_based_toy_misuse_v0`, `hash_based_toy_signature_v0`, `implementation_security_toy_benchmark_v0`, `implementation_security_toy_kat_v0`, `implementation_security_toy_timing_v0`, `isogeny_historical_toy_path_v0`, `lattice_downscaled_lwe_instance_solve_v0`, `lattice_downscaled_mlwe_instance_solve_v0`, `lattice_mlwe_downscaled_v0`, `lattice_toy_lwe_v0`, `multivariate_toy_minrank_v0`, `multivariate_toy_mq_v0`, and `multivariate_toy_uov_v0`.
- Public benchmark v0 manifest at `docs/public_benchmark_manifest.json` with regeneration commands and public trace/checksum digests.
- Deterministic verifier outputs for each public AttackPlan example.
- Public verifier reproduction status for downscaled evaluator smoke checks and tiny bounded public fixture solvers where explicitly implemented.
- `task_metadata.jsonl` with `agades.pqc.task_metadata.v6` rows for valid public AttackPlans, recording target family, target name, support level, ordered operator types, ordered operator params, ordered operator assumptions, reproducibility requirement, public flag, source path, seed AttackPlan SHA-256 digest, seed verifier status/reward, seed estimator, and seed reproduction status so Prime-style and Hugging Face consumers can keep repair candidates on the intended task without requiring an exact `attack_plan_id` copy, changing attack parameters, or dropping required hypotheses. Semantic-mutation tasks may change operator params only when the challenge explicitly requires a semantic variant.
- `dataset_info.json` records valid, invalid, task-metadata, and Prime-eligible row counts plus a deterministic task-metadata summary by family, support level, seed verifier status/reward, seed estimator, and reproduction status so the intentional invalid validator fixture is visible in Hugging Face while remaining outside Prime Verifiers task packaging.
- No private evolution traces.

## Intended Uses

- Reproduce the public CLI smoke tests.
- Demonstrate family routing and unsupported-result semantics.
- Inspect deterministic public run summaries without private trace data.
- Seed Hugging Face Spaces or Prime-style verifier demos.

## Limitations

Mock-estimator, bounded toy estimator results, and downscaled reproduction statuses verify evaluator plumbing only. The public LWE and linearized MLWE fixtures are deliberately tiny and solved by bounded exhaustive search; they are not cryptanalytic evidence against deployed parameters. Schema-only non-lattice examples do not include cryptanalytic estimates.
