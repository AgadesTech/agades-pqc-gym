# Downscaled LWE Instance Solve Benchmark

This benchmark runs the public toy LWE fixture solver against deliberately
tiny downscaled instances. It exercises the lattice-family reproduction harness
with real instance-solving results instead of only estimator plumbing.

The instances include binary-secret and ternary-secret public fixtures. They
are small enough for bounded exhaustive search and exist only as public
reproducibility evidence. They are not security claims, not ML-KEM evidence,
and not private evolution trace data.

`agades-pqc benchmark benchmarks/lattice_downscaled_lwe_instance_solve --out runs/lattice_downscaled_lwe_instance_solve.jsonl` evaluates this public fixture plan.
