# Family Adapters

Each family adapter implements the same conceptual interface:

```python
class FamilyAdapter(Protocol):
    family: TargetFamily
    support_level: str

    def validate_target(self, target: TargetSpec) -> list[ValidationFinding]: ...
    def validate_plan(self, plan: AttackPlan) -> list[ValidationFinding]: ...
    def supported_operators(self) -> set[str]: ...
    def estimate(self, plan: AttackPlan) -> EstimatorResult: ...
    def reproduce_downscaled(self, plan: AttackPlan) -> ReproductionResult | None: ...
```

## Support Matrix

The machine-readable version is checked in at `docs/family_support_matrix.json`
and regenerated with:

```bash
uv run agades-pqc family-support --out docs/family_support_matrix.json
```

Each family entry also records the future reviewed source-contract IDs that
could eventually feed real adapters, separate from cross-family review sources
such as PQC instruction/migration datasets. These fields are not runtime
enablement: `family-support-verify` rejects drift, and source contracts remain
blocked from the current public verifier until their review gates pass.

The per-family operator/evaluator contract is checked in at
`docs/family_operator_catalog.json` and regenerated with:

```bash
uv run agades-pqc family-operator-catalog --out docs/family_operator_catalog.json
uv run agades-pqc family-operator-catalog-verify --catalog docs/family_operator_catalog.json
```

The plugin descriptor contract is checked in at
`docs/family_plugin_manifest.json` and regenerated with:

```bash
uv run agades-pqc family-plugin-manifest --out docs/family_plugin_manifest.json
uv run agades-pqc family-plugin-manifest-verify --manifest docs/family_plugin_manifest.json
```

The operator catalog records the validator boundary, estimator name, required
assumptions, required parameters, fixture scope, and review gate for each
reviewed public operator surface. It is a release gate specifically to prevent
the Lattice Estimator boundary from being reused as a non-lattice PQC oracle.

| Family | Status | Estimator Behavior |
| --- | --- | --- |
| LWE | Implemented MVP | Mock estimator by default; real Lattice Estimator boundary exists. |
| MLWE | Implemented MVP | Mock estimator by default; module-aware hypotheses are review-gated. |
| NTRU | Schema/router-ready | Public schema-only examples and benchmarks route to `unsupported` until mappings are reviewed. |
| SIS | Schema/router-ready | Public schema-only examples and benchmarks route to `unsupported` until mappings are reviewed. |
| CODE_BASED | Toy evaluator | `prange_toy`, `lee_brickell_toy`, `stern_toy`, `dumer_toy`, `bjmm_toy`, and `qc_rotation_toy` ISD-style work-factor models plus `hqc_repetition_toy`, `hqc_weighted_repetition_toy`, `hqc_parity_check_toy`, `hqc_circulant_syndrome_toy`, `hqc_circulant_erasure_toy`, `hqc_erasure_syndrome_toy`, `classic_mceliece_syndrome_toy`, `classic_mceliece_support_syndrome_toy`, `mdpc_bit_flip_toy`, `mdpc_black_gray_bit_flip_toy`, and `mdpc_syndrome_weight_bit_flip_toy` fixture checks for bounded toy targets; real HQC-like, Classic McEliece-like, BIKE-like, and other schema-only plans still return unsupported. |
| MULTIVARIATE | Toy evaluator | `toy_mq_search`, `toy_mq_hybrid_search`, `toy_mq_degree_bound`, `toy_minrank_search`, and `toy_uov_public_map_verify` models for bounded toy multivariate targets; schema-only real-parameter plans still return unsupported. |
| HASH_BASED | Toy evaluator | `toy_preimage_bound`, `toy_collision_bound`, `toy_wots_chain_verify`, `toy_merkle_auth_path_verify`, `toy_fors_auth_path_verify`, `toy_slh_dsa_hypertree_verify`, and `toy_hash_reused_salt` hash-bound/signature/misuse models for bounded toy targets; schema-only plans still return unsupported. |
| ISOGENY_HISTORICAL | Toy evaluator | Historical `toy_sidh_path_search`, `toy_commutative_walk_search`, and `toy_volcano_walk_search` path/graph-count models for bounded toy fixtures; schema-only plans still return unsupported. |
| IMPLEMENTATION_SECURITY | Toy evaluator | `toy_kat_digest_match`, `toy_acvp_vector_set_match`, `toy_timing_welch_t_check`, `toy_benchmark_summary_check`, `toy_binary_size_check`, `toy_memory_footprint_check`, and `toy_stack_usage_check` JSON-only models for bounded toy manifests, public timing summaries, public benchmark summaries, public binary-size summaries, public memory-footprint summaries, and public stack-usage summaries; schema-only plans still return unsupported. |

## Reproduction Status

`reproduce_downscaled` is part of the family adapter boundary because reproducibility is family-specific. The cascade accepts these statuses:

| Status | Meaning |
| --- | --- |
| `not_requested` | The AttackPlan did not request downscaled reproduction. |
| `not_applicable` | The family or target failed the adapter's applicability rules. |
| `estimator_reproduced` | A deterministic evaluator replay passed on a public toy/downscaled target. |
| `instance_solved` | A bounded public downscaled fixture was solved by a reviewed family-specific harness. |
| `failed` | The adapter attempted the smoke check and it failed or exceeded constraints. |

For the lattice MVP, `estimator_reproduced` is not a cryptanalytic success claim. It only says the estimator path is deterministic and fits the declared toy resource bounds. `instance_solved` is currently limited to tiny public family-specific fixtures: LWE under `benchmarks/lattice_downscaled_lwe_instances/`, code-based under `benchmarks/code_based_toy_isd/fixtures/`, `benchmarks/code_based_toy_hqc/fixtures/`, `benchmarks/code_based_toy_classic_mceliece/fixtures/`, and `benchmarks/code_based_toy_mdpc/fixtures/`, multivariate under `benchmarks/multivariate_toy_mq/fixtures/`, `benchmarks/multivariate_toy_minrank/fixtures/`, and `benchmarks/multivariate_toy_uov/fixtures/`, hash-based under `benchmarks/hash_based_toy_bound/fixtures/`, `benchmarks/hash_based_toy_signature/fixtures/`, or `benchmarks/hash_based_toy_misuse/fixtures/`, historical-isogeny under `benchmarks/isogeny_historical_toy_path/fixtures/`, and implementation-security under `benchmarks/implementation_security_toy_kat/fixtures/`, `benchmarks/implementation_security_toy_timing/fixtures/`, or `benchmarks/implementation_security_toy_benchmark/fixtures/`. These fixtures are mirrored as package data when needed and exist only to verify reproduction plumbing.

The code-based toy evaluator now exposes a positive reproduction status for explicit public syndrome-decoding, HQC-inspired, Classic-McEliece-inspired, and MDPC/BIKE-inspired fixture checks. It estimates only small `toy_` targets using conservative toy Prange, Lee-Brickell-style, Stern-style, Dumer-style list-merging, BJMM-style representation-merge, quasi-cyclic rotation, repetition-decoder, weighted-repetition decoder, parity-check decoder, circulant-syndrome decoder, erasure-aided syndrome decoder, binary syndrome decoder, public support-set syndrome decoder, threshold bit-flip, black-gray bit-flip, or syndrome-weight bit-flip decoder models, solves only bounded public fixtures under `benchmarks/code_based_toy_isd/fixtures/`, `benchmarks/code_based_toy_hqc/fixtures/`, `benchmarks/code_based_toy_classic_mceliece/fixtures/`, or `benchmarks/code_based_toy_mdpc/fixtures/`, and refuses larger/non-toy targets.

Public reproduction fixture paths are resolved through a shared family helper.
Adapters accept only one JSON fixture file directly under their reviewed
`benchmarks/.../fixtures/` scope, reject traversal and absolute paths, reject
symlink escapes from the checkout fixture directory, and fall back to packaged
fixture data only when the checkout fixture is absent. This keeps installed
Prime/Hugging Face verifier environments aligned with the source checkout
without allowing a public plan to read arbitrary local files.

The lattice downscaled LWE fixture path uses the same helper with the reviewed
`benchmarks/lattice_downscaled_lwe_instances/` scope, so arbitrary benchmark
files are rejected before the LWE fixture solver is invoked.

The multivariate toy evaluator now exposes positive reproduction statuses for explicit public binary MQ, MinRank, and UOV-inspired public-map fixtures. It estimates only small `toy_` MQ, MQ hybrid-search, MQ degree-bound, MinRank, and public-map verification targets using bounded toy models, verifies only bounded public `GF(2)` fixtures under `benchmarks/multivariate_toy_mq/fixtures/`, `benchmarks/multivariate_toy_minrank/fixtures/`, or `benchmarks/multivariate_toy_uov/fixtures/`, and refuses larger/non-toy targets. MQ hybrid-search reproduction is limited to the reviewed public `GF(2)` fixture path and uses a bounded guess-prefix split-search harness; degree-bound reproduction is limited to the same tiny public binary fixture and is not a Groebner proof; UOV-inspired public-map verification evaluates one fixed public signature against one fixed public map and is not a forgery or UOV/MAYO/Rainbow result; `GF(16)` and candidate-shaped MQ targets remain estimator-only or unsupported according to the adapter rules.

The hash-based toy evaluator now exposes a positive reproduction status for explicit public SHAKE256 preimage, truncated-collision, signature-chain, Merkle auth-path, FORS-inspired auth-path, and reused-salt misuse fixtures. It estimates only small `toy_` preimage-bound, collision-bound, signature-chain, auth-path, FORS auth-path, and misuse-check targets using bounded digest-size, declared-chain, declared-tree, or declared-record models, verifies only bounded public fixtures under `benchmarks/hash_based_toy_bound/fixtures/`, `benchmarks/hash_based_toy_signature/fixtures/`, or `benchmarks/hash_based_toy_misuse/fixtures/`, and refuses larger/non-toy targets.

The historical-isogeny toy evaluator now exposes a positive reproduction status for explicit public historical toy path and graph fixtures. It estimates only small historical `toy_` path fixtures for SIDH/SIKE-style, commutative-walk-style, and volcano-style toy cases, verifies only no-claim fixtures under `benchmarks/isogeny_historical_toy_path/fixtures/`, and refuses current-standard/non-toy targets.

The implementation-security toy evaluator now exposes a positive reproduction status for explicit public JSON-only ML-KEM/ML-DSA KAT, ML-KEM/ML-DSA ACVP-like vector-set, timing-summary, dudect-style summary, ctgrind-style secret-taint summary, benchmark-summary, binary-size, memory-footprint, and stack-usage fixtures. It verifies only small JSON-only `toy_` KAT payload digests, bounded ACVP-shaped vector-set manifests, bounded public timing sample arrays, bounded public dudect-style summaries, bounded public ctgrind-style secret-taint summaries, bounded public benchmark cycle summaries, bounded public binary-size summaries, bounded public memory-footprint component summaries, or bounded public stack high-water sample summaries, verifies only no-execution public fixtures under `benchmarks/implementation_security_toy_kat/fixtures/`, `benchmarks/implementation_security_toy_timing/fixtures/`, or `benchmarks/implementation_security_toy_benchmark/fixtures/`, and refuses live artifact parameters such as `binary_path`, `host`, or `trace_path`.

## Adding A Family

1. Define target fields in `core/target.py`.
2. Add finite operators in `core/operators.py`.
3. Implement `families/<family>/adapter.py`.
4. Add schema tests, adapter tests, and cascade tests.
5. Add toy examples and benchmark cards.
6. Document assumptions and unsupported cases.

No family should return a cryptanalytic estimate until its estimator model and applicability rules are reviewed.

## Current Code-Based Toy Boundary

The `CODE_BASED` adapter now has seventeen deliberately narrow implemented variants
with separate ISD and fixture-decoder operators:

| AttackPlan operator | Variant | Estimator |
| --- | --- | --- |
| `information_set_decoding` | `prange_toy` | `toy-code-based-isd-estimator` |
| `information_set_decoding` | `lee_brickell_toy` | `toy-code-based-isd-estimator` |
| `information_set_decoding` | `stern_toy` | `toy-code-based-isd-estimator` |
| `information_set_decoding` | `dumer_toy` | `toy-code-based-isd-estimator` |
| `information_set_decoding` | `bjmm_toy` | `toy-code-based-isd-estimator` |
| `information_set_decoding` | `qc_rotation_toy` | `toy-code-based-isd-estimator` |
| `decoding_fixture_check` | `hqc_repetition_toy` | `toy-code-based-repetition-decoder-estimator` |
| `decoding_fixture_check` | `hqc_weighted_repetition_toy` | `toy-code-based-weighted-repetition-decoder-estimator` |
| `decoding_fixture_check` | `hqc_parity_check_toy` | `toy-code-based-parity-check-decoder-estimator` |
| `decoding_fixture_check` | `hqc_circulant_syndrome_toy` | `toy-code-based-circulant-syndrome-decoder-estimator` |
| `decoding_fixture_check` | `hqc_erasure_syndrome_toy` | `toy-code-based-erasure-syndrome-decoder-estimator` |
| `decoding_fixture_check` | `hqc_circulant_erasure_toy` | `toy-code-based-circulant-erasure-decoder-estimator` |
| `decoding_fixture_check` | `classic_mceliece_syndrome_toy` | `toy-code-based-classic-mceliece-syndrome-estimator` |
| `decoding_fixture_check` | `classic_mceliece_support_syndrome_toy` | `toy-code-based-classic-mceliece-support-syndrome-estimator` |
| `decoding_fixture_check` | `mdpc_bit_flip_toy` | `toy-code-based-bit-flip-decoder-estimator` |
| `decoding_fixture_check` | `mdpc_black_gray_bit_flip_toy` | `toy-code-based-bit-flip-decoder-estimator` |
| `decoding_fixture_check` | `mdpc_syndrome_weight_bit_flip_toy` | `toy-code-based-bit-flip-decoder-estimator` |

Applicability rules:

- target names must start with `toy_`;
- `n <= 256` and `w <= 32`;
- `k < n` and `w < n`;
- `prange_toy` plans must include `prange_isd_combinatorial_cost_model`;
- `lee_brickell_toy` plans must include `lee_brickell_isd_partial_enumeration_model` and a positive integer `p` satisfying `1 <= p <= w`, `p <= k`, and `w-p <= n-k`;
- `stern_toy` plans must include `stern_isd_partition_collision_cost_model` and a positive integer `p` satisfying the adapter's partition bounds;
- `dumer_toy` plans must include `dumer_isd_list_merging_cost_model`, a positive integer `p`, a non-negative integer `ell`, and satisfy the adapter's partition and merge-window bounds;
- `bjmm_toy` plans must include `bjmm_isd_representation_merge_model`, a positive integer `p`, a non-negative integer `ell`, a positive integer `representation_count <= 64`, and satisfy the adapter's partition and merge-window bounds;
- `qc_rotation_toy` plans must include `toy_qc_syndrome_rotation_model`, a positive `block_size <= 64`, a positive `block_count <= 16`, `n == block_size * block_count`, `w <= block_count`, and a target name starting with `toy_qc_`;
- `hqc_repetition_toy` plans must include `toy_hqc_repetition_decoder_model`, a positive odd `repetition_factor <= 16`, `n == k * repetition_factor`, `w <= k`, and a target name starting with `toy_hqc_`;
- `hqc_parity_check_toy` plans must include `toy_hqc_parity_check_decoder_model`, a positive `max_error_weight == w`, `k < n`, `w <= n-k`, and a target name starting with `toy_hqc_`;
- `hqc_weighted_repetition_toy` plans must include `toy_hqc_weighted_repetition_decoder_model`, a positive odd `repetition_factor <= 16`, a positive `max_reliability_weight <= 16`, `n == k * repetition_factor`, `w <= k`, and a target name starting with `toy_hqc_`;
- `hqc_circulant_syndrome_toy` plans must include `toy_hqc_circulant_syndrome_decoder_model`, a positive `block_size <= 64`, a positive `max_error_weight == w`, `n == 2 * block_size`, `k == block_size`, `w <= block_size`, and a target name starting with `toy_hqc_`;
- `hqc_erasure_syndrome_toy` plans must include `toy_hqc_erasure_syndrome_decoder_model`, a positive `max_error_weight == w`, a positive `erasure_count <= n`, `erasure_count >= max_error_weight`, `k < n`, `w <= n-k`, and a target name starting with `toy_hqc_`;
- `hqc_circulant_erasure_toy` plans must include `toy_hqc_circulant_erasure_decoder_model`, a positive `block_size <= 64`, a positive `max_error_weight == w`, positive `first_block_erasure_count` and `second_block_erasure_count` parameters, `n == 2 * block_size`, `k == block_size`, `first_block_erasure_count + second_block_erasure_count >= max_error_weight`, total erasure count `<= 64`, and a target name starting with `toy_hqc_`;
- `classic_mceliece_syndrome_toy` plans must include `toy_classic_mceliece_syndrome_decoder_model`, a positive `max_error_weight == w`, `k < n`, `w <= n-k`, and a target name starting with `toy_classic_mceliece_`;
- `classic_mceliece_support_syndrome_toy` plans must include `toy_classic_mceliece_support_syndrome_decoder_model`, a positive `max_error_weight == w`, a positive `support_size <= n`, `support_size >= max_error_weight`, `k < n`, and a target name starting with `toy_classic_mceliece_`;
- `mdpc_bit_flip_toy` plans must include `toy_mdpc_bit_flip_decoder_model`, positive integer `threshold` and `max_iterations` parameters, `k < n`, `w <= n-k`, `threshold <= n-k`, `max_iterations <= 32`, and a target name starting with `toy_mdpc_`;
- `mdpc_black_gray_bit_flip_toy` plans must include `toy_mdpc_black_gray_bit_flip_decoder_model`, positive integer `black_threshold`, `gray_threshold`, and `max_iterations` parameters, `k < n`, `w <= n-k`, `gray_threshold <= black_threshold <= n-k`, `max_iterations <= 32`, and a target name starting with `toy_mdpc_`;
- `mdpc_syndrome_weight_bit_flip_toy` plans must include `toy_mdpc_syndrome_weight_bit_flip_decoder_model`, positive integer `min_syndrome_weight_drop` and `max_iterations` parameters, `k < n`, `w <= n-k`, `min_syndrome_weight_drop <= n-k`, `max_iterations <= 32`, and a target name starting with `toy_mdpc_`;
- plans must not include pre-evaluation estimate claims;
- downscaled reproduction is available only when the plan names an explicit public fixture under `benchmarks/code_based_toy_isd/fixtures/`, `benchmarks/code_based_toy_hqc/fixtures/`, `benchmarks/code_based_toy_classic_mceliece/fixtures/`, or `benchmarks/code_based_toy_mdpc/fixtures/`;

Schema-only code-based AttackPlans under `examples/attack_plans/` and
`benchmarks/code_based_schema_only/` include HQC-like, Classic McEliece-like,
and BIKE-like targets. They validate shape and routing only, then return
`evaluation_status="unsupported"` through `code-based-placeholder-estimator`
with no time or memory estimate.

This is a public plumbing model for toy code-based tasks. It must not be presented as HQC, Classic McEliece, BIKE, or deployed-parameter cryptanalytic evidence.

The checked-in `code_based_toy_isd_v0` benchmark also exercises
`solve_toy_syndrome_fixture` on
`benchmarks/code_based_toy_isd/fixtures/toy_syndrome_31_16_w3_fixture.json`
and
`benchmarks/code_based_toy_isd/fixtures/toy_syndrome_15_7_w2_fixture.json`.
That harness exhaustively enumerates the declared binary error positions. The
same bundle exercises Prange, Lee-Brickell-style, Dumer-style, and BJMM-style plans on the shared
`toy_syndrome_31_16_w3_fixture.json` no-claim fixture, and also exercises
`solve_toy_qc_rotation_fixture` on
`benchmarks/code_based_toy_isd/fixtures/toy_qc_syndrome_21_12_w2_fixture.json`,
which enumerates only the declared block rotations. Both harnesses return
`instance_solved` only for unique public no-claim solutions.

The checked-in `code_based_toy_hqc_v0` benchmark exercises
`decode_toy_hqc_repetition_fixture` on
`benchmarks/code_based_toy_hqc/fixtures/toy_hqc_repetition_21_7_w3_fixture.json`.
It also exercises `decode_toy_hqc_weighted_repetition_fixture` on
`benchmarks/code_based_toy_hqc/fixtures/toy_hqc_weighted_repetition_25_5_w4_fixture.json`.
It also exercises `decode_toy_hqc_parity_check_fixture` on
`benchmarks/code_based_toy_hqc/fixtures/toy_hqc_parity_check_15_7_w2_fixture.json`.
It also exercises `decode_toy_hqc_circulant_syndrome_fixture` on
`benchmarks/code_based_toy_hqc/fixtures/toy_hqc_circulant_syndrome_16_8_w2_fixture.json`.
It also exercises `decode_toy_hqc_erasure_syndrome_fixture` on
`benchmarks/code_based_toy_hqc/fixtures/toy_hqc_erasure_syndrome_12_6_w2_fixture.json`.
It also exercises `decode_toy_hqc_circulant_erasure_fixture` on
`benchmarks/code_based_toy_hqc/fixtures/toy_hqc_circulant_erasure_16_8_w3_fixture.json`.
These paths perform majority decoding, bounded reliability-weighted majority
decoding, bounded exact-weight syndrome search, or bounded split error-position
search over two length-8 circulant blocks, or bounded erasure-position syndrome
search on tiny public fixtures, including an erasure-constrained double-block
circulant syndrome fixture. This is HQC-inspired fixture plumbing only; it is
not an HQC result.

The checked-in `code_based_toy_classic_mceliece_v0` benchmark exercises
`solve_toy_syndrome_fixture` on
`benchmarks/code_based_toy_classic_mceliece/fixtures/toy_classic_mceliece_syndrome_17_9_w2_fixture.json`.
It also exercises `decode_toy_classic_mceliece_support_syndrome_fixture` on
`benchmarks/code_based_toy_classic_mceliece/fixtures/toy_classic_mceliece_support_syndrome_19_10_w2_fixture.json`.
These paths perform bounded exact-weight syndrome search either across the
whole tiny public code length or only across declared public support positions.
This is Classic-McEliece-inspired fixture plumbing only; it is not a Classic
McEliece result.

The checked-in `code_based_toy_mdpc_v0` benchmark exercises
`decode_toy_mdpc_bit_flip_fixture`, `decode_toy_mdpc_black_gray_fixture`, and
`decode_toy_mdpc_syndrome_weight_fixture` on fixtures under
`benchmarks/code_based_toy_mdpc/fixtures/`. These paths run bounded
deterministic threshold, black-gray, and syndrome-weight bit-flip decoders over
tiny public binary parity-check fixtures. This is MDPC/BIKE-inspired fixture
plumbing only;
it is not a BIKE result.

## Current Multivariate Toy Boundary

The `MULTIVARIATE` adapter now has five deliberately narrow implemented surfaces:

| AttackPlan operator | Model | Estimator |
| --- | --- | --- |
| `groebner_basis` | `toy_mq_search` | `toy-multivariate-estimator` |
| `groebner_basis` | `toy_mq_hybrid_search` | `toy-multivariate-estimator` |
| `groebner_basis` | `toy_mq_degree_bound` | `toy-multivariate-estimator` |
| `minrank_attack` | `toy_minrank_search` | `toy-multivariate-estimator` |
| `signature_fixture_check` | `toy_uov_public_map_verify` | `toy-multivariate-estimator` |

Applicability rules:

- target names must start with `toy_`;
- `variables <= 16` and `equations <= 16`;
- `field` must use `GF(q)` notation with field order `q <= 256`;
- MQ exhaustive-search plans must include `toy_mq_exhaustive_search_model`;
- MQ hybrid-search plans must include `toy_mq_hybrid_linearization_model` and a positive integer `guessed_variables` satisfying `1 <= guessed_variables < variables`;
- MQ degree-bound plans must include `toy_mq_degree_bound_model`, `2 <= degree_bound <= variables`, and `2.0 <= linear_algebra_omega <= 3.0`;
- MinRank plans must include `toy_minrank_exhaustive_search_model`;
- MinRank plans must declare positive `matrix_rows` and `matrix_cols`, plus `target_rank < min(matrix_rows, matrix_cols)`;
- UOV-inspired public-map plans must include `toy_uov_public_map_verification_model`, declare `signature_model="toy_uov_public_map_verify"`, positive `oil_variables` and `vinegar_variables`, `oil_variables + vinegar_variables == variables`, `field == "GF(2)"`, and target names starting with `toy_uov_`;
- plans must not include pre-evaluation estimate claims;
- downscaled reproduction is available only when the plan names an explicit public `GF(2)` fixture under the matching `benchmarks/multivariate_toy_mq/fixtures/`, `benchmarks/multivariate_toy_minrank/fixtures/`, or `benchmarks/multivariate_toy_uov/fixtures/` directory;

This is public plumbing for toy MQ, MQ hybrid-search, MQ degree-bound, MinRank, and UOV-inspired public-map verification tasks. It must not be presented as UOV, MAYO, Rainbow, Groebner-basis, MinRank, forgery, or deployed-parameter cryptanalytic evidence.

The checked-in `multivariate_toy_mq_v0` benchmark also exercises the
`toy_mq_degree_bound` `GF(16)` estimator-only path, the `GF(2)` degree-bound
reproduction wrapper, `solve_toy_mq_fixture`, and
`solve_toy_mq_hybrid_fixture` on
`benchmarks/multivariate_toy_mq/fixtures/toy_mq_gf2_v6_e4_fixture.json`.
The exhaustive harness enumerates `2^6` binary assignments. The hybrid harness
enumerates the declared guessed prefix first and then the residual binary suffix
under the same public bound. The degree-bound reproduction wrapper reuses the
same public binary fixture solver only as reproducibility plumbing. These paths
return `instance_solved` only for the unique public no-claim solution.

The checked-in `multivariate_toy_minrank_v0` benchmark also exercises
`solve_toy_minrank_fixture` on
`benchmarks/multivariate_toy_minrank/fixtures/toy_minrank_gf2_m3_r0_fixture.json`
`benchmarks/multivariate_toy_minrank/fixtures/toy_minrank_gf2_m3_r1_fixture.json`,
and
`benchmarks/multivariate_toy_minrank/fixtures/toy_minrank_gf2_m4_r2_fixture.json`.
That harness exhaustively enumerates `2^4` binary assignments and returns
`instance_solved` only for the unique public no-claim solution.

The checked-in `multivariate_toy_uov_v0` benchmark exercises
`verify_toy_uov_public_map_fixture` on
`benchmarks/multivariate_toy_uov/fixtures/toy_uov_public_map_gf2_v5_e3_fixture.json`.
That harness evaluates one fixed public signature under one fixed public
quadratic map and returns `instance_solved` only when the declared output vector
matches. This is UOV-inspired verifier plumbing only; it is not a UOV, MAYO,
Rainbow, forgery, or security result.

## Current Hash-Based Toy Boundary

The `HASH_BASED` adapter now has seven deliberately narrow implemented surfaces:

| AttackPlan operator | Model | Estimator |
| --- | --- | --- |
| `security_bound_check` | `toy_preimage_bound` | `toy-hash-bound-estimator` |
| `security_bound_check` | `toy_collision_bound` | `toy-hash-bound-estimator` |
| `hash_signature_verification` | `toy_wots_chain_verify` | `toy-hash-bound-estimator` |
| `hash_signature_verification` | `toy_merkle_auth_path_verify` | `toy-hash-bound-estimator` |
| `hash_signature_verification` | `toy_fors_auth_path_verify` | `toy-hash-bound-estimator` |
| `hash_signature_verification` | `toy_slh_dsa_hypertree_verify` | `toy-hash-bound-estimator` |
| `misuse_check` | `toy_hash_reused_salt` | `toy-hash-bound-estimator` |

Applicability rules:

- target names must start with `toy_`;
- `n <= 64` and `n` is interpreted only as a toy digest-bit bound;
- `hash_function` must use a reviewed public label such as `SHAKE256`;
- preimage-bound plans must include `toy_hash_preimage_bound_model`;
- collision-bound plans must include `toy_hash_collision_bound_model`;
- signature-chain plans must include `toy_hash_signature_chain_model` and positive `chain_count` and `max_chain_steps`;
- Merkle auth-path plans must include `toy_hash_merkle_auth_path_model`, positive `tree_height <= 16`, and `leaf_index < 2**tree_height`;
- FORS auth-path plans must include `toy_hash_fors_auth_path_model`, positive `tree_count <= 16`, positive `tree_height <= 16`, and `selected_indices` with length equal to `tree_count` and each selected index within the tree height;
- SLH-DSA-like hypertree plans must include `toy_hash_slh_dsa_hypertree_model`, positive `fors_tree_count <= 16`, `fors_tree_height <= 16`, `wots_chain_count <= 16`, `wots_max_chain_steps <= 64`, `hypertree_height <= 16`, `hypertree_leaf_index < 2**hypertree_height`, and `fors_selected_indices` with length equal to `fors_tree_count`;
- misuse-check plans must include `toy_hash_misuse_fixture_model`, `fixture="toy_hash_reused_salt"`, and positive `record_count`, `expected_reuse_groups`, and `salt_bytes`;
- plans must not include pre-evaluation estimate claims;
- downscaled reproduction is available only when a preimage, collision-bound, signature-chain, Merkle auth-path, FORS auth-path, or misuse-check plan names an explicit public fixture under `benchmarks/hash_based_toy_bound/fixtures/`, `benchmarks/hash_based_toy_signature/fixtures/`, or `benchmarks/hash_based_toy_misuse/fixtures/`;

This is a public plumbing model for toy hash-bound, signature-chain, auth-path, FORS-inspired auth-path, SLH-DSA-like hypertree, and misuse-check tasks. It must not be presented as SLH-DSA, hash-standard, collision-finding evidence, misuse exploit evidence, or deployed-parameter cryptanalytic evidence.

The checked-in `hash_based_toy_bound_v0` benchmark also exercises
`solve_toy_preimage_fixture` on
`benchmarks/hash_based_toy_bound/fixtures/toy_hash_preimage_24_fixture.json`.
That harness exhaustively enumerates 65,536 fixed-width public candidates
against a 24-bit SHAKE256 digest prefix and returns `instance_solved` only for
the unique public no-claim solution. The same hash-bound benchmark also verifies
`benchmarks/hash_based_toy_bound/fixtures/toy_hash_collision_32_fixture.json`,
where two fixed public messages share the declared 32-bit SHAKE256 digest
prefix. That collision fixture is plumbing evidence only; it is not a
collision-finding result for full-size hashes.

The checked-in `hash_based_toy_misuse_v0` benchmark exercises
`verify_toy_hash_misuse_fixture` on
`benchmarks/hash_based_toy_misuse/fixtures/toy_hash_reused_salt_24_fixture.json`.
That harness recomputes fixed public SHAKE256 digest prefixes and verifies the
declared reused-salt group only. It is misuse-detection plumbing, not exploit
evidence and not a security claim.

The checked-in `hash_based_toy_signature_v0` benchmark also exercises
`verify_toy_fors_auth_path_fixture` and
`verify_toy_slh_dsa_hypertree_fixture` on
`benchmarks/hash_based_toy_signature/fixtures/toy_hash_fors_auth_path_24_fixture.json`.
The SLH-DSA-like hypertree fixture is
`benchmarks/hash_based_toy_signature/fixtures/toy_hash_slh_dsa_hypertree_24_fixture.json`.
Those harnesses verify tiny public FORS-inspired auth paths and one public
toy_slh_dsa_hypertree_verify path with fixed SHAKE256 digest prefixes. They
are SLH-DSA-inspired fixture plumbing only; this is not an SLH-DSA result and
not a security claim.

## Current Historical-Isogeny Toy Boundary

The `ISOGENY_HISTORICAL` adapter now has three deliberately narrow implemented surfaces:

| AttackPlan operator | Case | Estimator |
| --- | --- | --- |
| `historical_isogeny_reconstruction` | `toy_sidh_path_search` | `toy-isogeny-historical-path-estimator` |
| `historical_isogeny_reconstruction` | `toy_commutative_walk_search` | `toy-isogeny-historical-path-estimator` |
| `historical_isogeny_reconstruction` | `toy_volcano_walk_search` | `toy-isogeny-historical-path-estimator` |

Applicability rules:

- target names must start with `toy_`;
- `n <= 128`;
- targets must not include `claimed_security_bits`;
- SIDH/SIKE-style path plans must include `historical_not_current_standard` and `historical_toy_isogeny_path_model`;
- commutative-walk-style plans must include `historical_not_current_standard` and `historical_toy_commutative_walk_model`;
- volcano-style graph/path plans must include `historical_not_current_standard` and `historical_toy_volcano_walk_model`;
- `walk_length` must be between 1 and 32;
- `branching_factor` must be between 2 and 8;
- `volcano_height` must be between 1 and 8 when `case="toy_volcano_walk_search"`;
- plans must not include pre-evaluation estimate claims;
- downscaled reproduction is available only when the plan names an explicit public historical toy path fixture under `benchmarks/isogeny_historical_toy_path/fixtures/`;

This is a public plumbing model for historical SIDH/SIKE-style, commutative-walk-style, and volcano-style toy path fixtures. It must not be presented as an isogeny solver, a CSIDH result, a SIDH/SIKE result, a current-standard result, or deployed-parameter cryptanalytic evidence.

The checked-in `isogeny_historical_toy_path_v0` benchmark also exercises
`verify_toy_isogeny_path_fixture` on
`benchmarks/isogeny_historical_toy_path/fixtures/toy_sidh_path_fixture.json`
and
`benchmarks/isogeny_historical_toy_path/fixtures/toy_commutative_walk_fixture.json`.
It also verifies the volcano-style graph fixture at
`benchmarks/isogeny_historical_toy_path/fixtures/toy_volcano_walk_fixture.json`.
That harness verifies the declared start/end/path shape, graph edges, and
bounded volcano levels, then returns
`instance_solved` only when the fixture is public, historical-only, no-claim, and
matches the reviewed toy target/operator parameters.

## Current Implementation-Security Toy Boundary

The `IMPLEMENTATION_SECURITY` adapter now has nine deliberately narrow implemented surfaces:

| AttackPlan operator | Model | Estimator |
| --- | --- | --- |
| `kat_conformance` | `toy_kat_digest_match` | `toy-implementation-security-estimator` |
| `kat_conformance` | `toy_acvp_vector_set_match` | `toy-implementation-security-estimator` |
| `constant_time_check` | `toy_timing_welch_t_check` | `toy-implementation-security-estimator` |
| `constant_time_check` | `toy_dudect_summary_threshold_check` | `toy-implementation-security-estimator` |
| `constant_time_check` | `toy_ctgrind_secret_taint_summary_check` | `toy-implementation-security-estimator` |
| `benchmark_harness` | `toy_benchmark_summary_check` | `toy-implementation-security-estimator` |
| `benchmark_harness` | `toy_binary_size_check` | `toy-implementation-security-estimator` |
| `benchmark_harness` | `toy_memory_footprint_check` | `toy-implementation-security-estimator` |
| `benchmark_harness` | `toy_stack_usage_check` | `toy-implementation-security-estimator` |

Applicability rules:

- target names must start with `toy_`;
- targets must not include `claimed_security_bits`;
- KAT plans must include `toy_kat_digest_manifest_model`;
- KAT `payload` must be a UTF-8 string of at most 512 bytes;
- KAT `expected_sha256` must be the SHA-256 digest of `payload`;
- KAT `vector_count` must be between 1 and 16;
- ACVP-like plans must include `toy_acvp_json_vector_set_model`;
- ACVP-like `vector_set` must be a bounded JSON object whose `algorithm` and `mode` match the operator;
- ACVP-like tests must use unique positive `tcId` values and reviewed algorithm/mode-specific lowercase hex fields: ML-KEM encapsulation requires `seed`, `ciphertext`, and `sharedSecret`; ML-DSA signature-verification requires `seed`, `message`, `publicKey`, and `signature`;
- ACVP-like `expected_vector_set_sha256` must match canonical SHA-256 over the sorted JSON `vector_set`;
- ACVP-like `test_count` must match the vector-set tests and stay between 1 and 16;
- timing plans must include `toy_timing_leakage_model`;
- timing `fixed_cycles` and `random_cycles` must be bounded public integer arrays with 2 to 64 samples;
- timing `max_abs_t` must be positive and the observed Welch-style absolute t statistic must not exceed it;
- dudect-style summary plans must include `toy_dudect_summary_model`, declare a non-empty `dudect_version`, reuse the bounded public timing sample arrays, and validate without executing dudect;
- ctgrind-style secret-taint summary plans must include `toy_ctgrind_secret_taint_summary_model`, declare a non-empty `ctgrind_version`, use bounded public integer counters, and require observed secret-dependent branch and memory-access counts to stay within declared thresholds without executing ctgrind;
- benchmark plans must include `toy_benchmark_summary_model`;
- benchmark `metric` must be `toy_cycles_per_operation`;
- benchmark `samples` must be bounded public positive integer cycle arrays with 2 to 64 samples;
- benchmark `max_median_cycles` must be positive and the sample median must not exceed it;
- binary-size plans must include `toy_binary_size_model`;
- binary-size `metric` must be `toy_binary_size_bytes`;
- binary-size `text_bytes`, `rodata_bytes`, `data_bytes`, and `bss_bytes` must be bounded public byte counts;
- binary-size `max_total_bytes` must be positive and the summed byte counts must not exceed it;
- memory-footprint plans must include `toy_memory_footprint_model`;
- memory-footprint `metric` must be `toy_memory_footprint_bytes`;
- memory-footprint `stack_bytes`, `heap_bytes`, and `code_bytes` must be bounded public byte counts;
- memory-footprint component thresholds must be positive and each observed count must not exceed its declared threshold;
- stack-usage plans must include `toy_stack_usage_model`;
- stack-usage `metric` must be `toy_stack_usage_bytes`;
- stack-usage `stack_samples` must be bounded public positive byte counts with 2 to 64 samples;
- stack-usage `max_stack_bytes` must be positive and the maximum observed sample must not exceed it;
- executable or live artifact parameters such as `binary_path`, `host`, `target_url`, and `trace_path` are rejected;
- plans must not include pre-evaluation estimate claims;
- downscaled reproduction is available only when the plan names an explicit public JSON-only fixture under the matching `benchmarks/implementation_security_toy_kat/fixtures/`, `benchmarks/implementation_security_toy_timing/fixtures/`, or `benchmarks/implementation_security_toy_benchmark/fixtures/` directory;

This is public plumbing for toy ML-KEM/ML-DSA KAT digest manifests, ML-KEM/ML-DSA ACVP-like vector sets, toy timing summaries, toy dudect-style summaries, toy ctgrind-style secret-taint summaries, toy benchmark summaries, toy binary-size summaries, toy memory-footprint summaries, and toy stack-usage summaries. It must not be presented as a real ACVP certificate, conformance certificate, performance result, binary-size result, memory-usage result, stack-usage result, constant-time result, side-channel analysis, or implementation-security claim.

The implementation-security schema-only benchmark also carries public
placeholders for PQClean KATs, liboqs tests/benchmarks, pqm4 Cortex-M4
benchmarks, PQ Code Package native ML-KEM/ML-DSA workflows,
`nist_acvp_pqc_vectors_schema`, dudect timing leakage, ctgrind secret-taint,
and TIMECOP/SUPERCOP policy checks. Those entries exist to keep source contracts
visible in Hugging Face, Prime Verifiers, and local benchmark surfaces while
returning `unsupported`; they do not execute upstream code, firmware, devices,
an ACVP server, ACVP/CAVP vector workflows, timing tools, taint tools, policy
tools, or live artifacts, and make no ACVP, conformance, side-channel, or
security claim and no constant-time, side-channel, or security claim.

The checked-in `implementation_security_toy_kat_v0` benchmark also exercises
`verify_toy_kat_fixture` on
`benchmarks/implementation_security_toy_kat/fixtures/toy_mlkem_kat_digest_fixture.json`
and
`benchmarks/implementation_security_toy_kat/fixtures/toy_mldsa_kat_digest_fixture.json`,
and `verify_toy_acvp_fixture` on
`benchmarks/implementation_security_toy_kat/fixtures/toy_acvp_mlkem_vector_set_fixture.json`
and
`benchmarks/implementation_security_toy_kat/fixtures/toy_acvp_mldsa_vector_set_fixture.json`.
Those harnesses recompute either the SHA-256 digest of a tiny public payload or
the canonical SHA-256 digest of a bounded ACVP-like public vector set, returning
`instance_solved` only when the fixture is public, no-claim, and declares
`artifact_execution=false`.

The checked-in `implementation_security_toy_timing_v0` benchmark also exercises
`verify_toy_timing_fixture` on
`benchmarks/implementation_security_toy_timing/fixtures/toy_timing_welch_fixture.json`.
That harness recomputes a Welch-style absolute t statistic from tiny public
cycle-count arrays and returns `instance_solved` only when the fixture is
public, no-claim, declares `artifact_execution=false`, and stays below the
declared toy threshold. It is not a constant-time or side-channel result.

The checked-in `implementation_security_toy_benchmark_v0` benchmark also
exercises `verify_toy_benchmark_fixture` on
`benchmarks/implementation_security_toy_benchmark/fixtures/toy_mlkem_benchmark_summary_fixture.json`
and `verify_toy_benchmark_fixture` on
`benchmarks/implementation_security_toy_benchmark/fixtures/toy_mlkem_binary_size_fixture.json`
and `verify_toy_benchmark_fixture` on
`benchmarks/implementation_security_toy_benchmark/fixtures/toy_mlkem_memory_footprint_fixture.json`
and `verify_toy_benchmark_fixture` on
`benchmarks/implementation_security_toy_benchmark/fixtures/toy_pqm4_stack_usage_fixture.json`.
That harness recomputes the median over a tiny public cycle-count array, the
sum over tiny public binary-size byte counts, or the sum over tiny public
component byte counts, or the maximum over tiny public stack high-water samples
and returns `instance_solved` only
when the fixture is public, no-claim, declares `artifact_execution=false`, and
stays below the declared toy threshold. It is not a performance, binary-size,
memory-usage, stack-usage, conformance, or side-channel result.

## Current Lattice Estimator Boundary

The optional Lattice Estimator adapter maps only explicit reviewed LWE-family operator names to estimator algorithm keys. Current direct mappings are:

| AttackPlan operator | Lattice Estimator key |
| --- | --- |
| `primal_usvp` | `usvp` |
| `bounded_distance_decoding` | `bdd` |
| `dual_attack` | `dual` |
| `dual_hybrid` | `dual_hybrid` |
| `bkw` | `bkw` |

Operators outside this table return structured `unsupported` results instead of falling back to another estimator path.

Each direct LWE mapping in this table has a checked-in public toy AttackPlan under `examples/attack_plans/` and a packaged Prime Verifiers task row. Those examples validate adapter plumbing only; they are not security claims.

`docs/lattice_estimator_manifest.json`, generated by
`agades-pqc lattice-estimator-manifest`, records the pinned upstream
`malb/lattice-estimator` commit used as the current optional-adapter reference.
The runtime adapter requires backend commit metadata to match that pin before
calling the estimator; missing or mismatched metadata returns `error` without
producing an estimate. The manifest is audited by `lattice-estimator-pin`; it
preserves the review-required/no-security-claim boundary and keeps NTRU/SIS
schema-only until separate mappings are reviewed.

NTRU and SIS have public schema-only AttackPlans and benchmark seeds under
`examples/attack_plans/` and `benchmarks/lattice_schema_only/`. They validate the
lattice plugin boundary and OSS packaging only: static schema validation passes,
the lattice router returns `evaluation_status="unsupported"`, no time or memory
estimate is emitted, and Prime rewards score those submissions as `0.0`.
