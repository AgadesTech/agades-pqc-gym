# Evaluation Log

## 2026-05-15 — Toy LWE Smoke Benchmark

Command:

```bash
uv run agades-lwe benchmark benchmarks/toy_lwe --out runs/toy_benchmark.jsonl
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

## 2026-05-15 — MLKEM-Like Downscaled Smoke Benchmark

Command:

```bash
uv run agades-lwe benchmark benchmarks/mlkem_like --out runs/mlkem_like_benchmark.jsonl
```

Result:

| Candidate | Score | Estimator |
| --- | ---: | --- |
| `mlkem768_like_downscaled_primal_seed-0` | -409.7515 | `mock-lattice-estimator` |

Failure mode:

- None for the smoke run. No real ML-KEM claim is made.
