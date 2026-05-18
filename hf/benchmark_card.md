# Benchmark Card: Agades PQC Gym

## Benchmark Type

Family-router, schema, mock-estimator, bounded toy-estimator, trace, and report smoke tests.

## Current Benchmarks

- `benchmarks/lattice_toy_lwe`
- `benchmarks/lattice_mlkem_like`
- `benchmarks/lattice_downscaled_lwe_instance_solve`
- `benchmarks/lattice_downscaled_mlwe_instance_solve`
- `benchmarks/code_based_schema_only`
- `benchmarks/code_based_toy_classic_mceliece`
- `benchmarks/code_based_toy_isd`
- `benchmarks/code_based_toy_hqc`
- `benchmarks/code_based_toy_mdpc`
- `benchmarks/multivariate_schema_only`
- `benchmarks/multivariate_toy_minrank`
- `benchmarks/multivariate_toy_mq`
- `benchmarks/multivariate_toy_uov`
- `benchmarks/hash_based_schema_only`
- `benchmarks/hash_based_toy_bound`
- `benchmarks/hash_based_toy_misuse`
- `benchmarks/hash_based_toy_signature`
- `benchmarks/isogeny_historical_schema_only`
- `benchmarks/isogeny_historical_toy_path`
- `benchmarks/implementation_security_schema_only`
- `benchmarks/implementation_security_toy_benchmark`
- `benchmarks/implementation_security_toy_kat`
- `benchmarks/implementation_security_toy_timing`

## Public Run Bundles

The checked-in `docs/public_benchmark_manifest.json` is the canonical local
public benchmark v0 map. It records bundle paths, benchmark regeneration
commands, public trace digests, checksum-manifest digests, and no-claim safety
flags. It can be verified locally with:

```bash
uv run agades-pqc public-benchmark-verify --manifest docs/public_benchmark_manifest.json
```

The current bundle set is:

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

## Metrics

- `evaluation_status`
- `combined_score`
- `estimated_time_bits`
- `estimated_memory_bits`
- `validity_score`
- MAP-Elites feature dimensions.
- Public ledger summary counts by family, evaluation status, and estimator.

## Caveats

LWE/MLWE use the lattice adapter and mock or optional Lattice Estimator boundary. Code-based, hash-based, implementation-security, historical-isogeny, and multivariate benchmarks currently use bounded toy evaluators or schema-only placeholders. The code-based HQC-inspired benchmark includes repetition, weighted-repetition, parity-check, circulant-syndrome, erasure-aided syndrome, and circulant-erasure fixture plumbing; it is not an HQC result. The hash-based signature benchmark includes `toy_slh_dsa_hypertree_verify` SLH-DSA-like hypertree fixture plumbing; it is not an SLH-DSA result. The historical-isogeny benchmark includes `toy_volcano_walk_search` graph/path fixture plumbing; it is not a CSIDH, SIDH/SIKE, current-standard, or security result. The multivariate UOV-inspired benchmark verifies one tiny public map/signature fixture only; it is not a UOV, MAYO, Rainbow, forgery, or security result. All benchmark outputs are public plumbing evidence only, not cryptanalytic, conformance, or current-standard security claims.
