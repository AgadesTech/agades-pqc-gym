# Evaluation Log

## 2026-05-15 — Toy LWE Smoke Benchmark

Command:

```bash
uv run agades-pqc benchmark benchmarks/lattice_toy_lwe --out runs/toy_benchmark.jsonl
```

Results:

| Candidate | Score | Time Bits | Memory Bits | Estimator |
| --- | ---: | ---: | ---: | --- |
| `toy_lwe_n64_q257_primal_seed-0` | -67.4696 | 63.5296 | 17.36 | `mock-lattice-estimator` |
| `toy_lwe_n96_q769_primal_seed-1` | -97.0376 | 91.1776 | 25.04 | `mock-lattice-estimator` |

Failure mode:

- None for the smoke run. The results are mock-estimator plumbing outputs only.

What changed:

- Added target configs and seed-plan benchmark path.

Whether it helped:

- Yes. The CLI produced deterministic trace output, public export, and Markdown report artifacts.

Public ledger:

```bash
uv run agades-pqc public-ledger runs/toy_benchmark.jsonl --out public/toy_run_ledger.json
uv run agades-pqc public-bundle runs/toy_benchmark.jsonl --out public/toy_run_bundle
```

## 2026-05-15 — MLKEM-Like Downscaled Smoke Benchmark

Command:

```bash
uv run agades-pqc benchmark benchmarks/lattice_mlkem_like --out runs/mlkem_like_benchmark.jsonl
```

Result:

| Candidate | Score | Estimator |
| --- | ---: | --- |
| `mlkem768_like_downscaled_primal_seed-0` | -409.7515 | `mock-lattice-estimator` |

Failure mode:

- None for the smoke run. No real ML-KEM claim is made.

## 2026-05-15 — v3 Code-Based Unsupported Smoke

Command:

```bash
uv run agades-pqc evaluate examples/attack_plans/code_based_isd_placeholder.json --out runs/v3_unsupported_trace.jsonl
```

Result:

| Candidate | Status | Score | Estimator |
| --- | --- | ---: | --- |
| `code_based_isd_placeholder_v1` | `unsupported` | -1000000000.0 | `code-based-placeholder-estimator` |

Failure mode:

- No failure. This is the intended behavior for schema-only non-lattice families: validate structure, route to family adapter, return `unsupported`, and do not fabricate time/memory estimates.

## 2026-05-15 — v3 Lattice Toy Benchmark

Command:

```bash
uv run agades-pqc benchmark benchmarks/lattice_toy_lwe --out runs/v3_toy_benchmark.jsonl
```

Result:

| Candidate | Status | Score | Estimator |
| --- | --- | ---: | --- |
| `toy_lwe_n64_q257_primal_seed-0` | `ok` | -67.4696 | `mock-lattice-estimator` |
| `toy_lwe_n96_q769_primal_seed-1` | `ok` | -97.0376 | `mock-lattice-estimator` |

Failure mode:

- None. Results remain mock-estimator plumbing outputs only.

## 2026-05-15 — v3 Implementation-Security Unsupported Smoke

Command:

```bash
uv run agades-pqc benchmark benchmarks/implementation_security_schema_only --out runs/v3_implementation_security_schema.jsonl
```

Result:

| Candidate | Status | Score | Estimator |
| --- | --- | ---: | --- |
| `kyber_reference_constant_time_schema_schema_placeholder_seed-0` | `unsupported` | -1000000000.0 | `implementation-security-placeholder-evaluator` |

Failure mode:

- No failure. The benchmark verifies routing and unsupported-result behavior for implementation-security placeholders. It does not perform side-channel or conformance analysis.
