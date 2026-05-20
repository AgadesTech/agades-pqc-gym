# Lattice Downscaled MLWE Instance Solve Benchmark

This benchmark runs tiny public MLWE-style fixture-solving plans through the
lattice adapter reproduction path.

The fixture is intentionally linearized and tiny so the verifier can perform a
bounded exhaustive search over a public module secret. It is reproducibility
plumbing only and does not claim anything about ML-KEM or deployed parameters.
