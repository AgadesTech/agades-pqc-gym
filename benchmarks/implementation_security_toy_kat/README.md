# Implementation-Security Toy KAT Benchmark

Bounded JSON-only smoke benchmark for toy `kat_conformance` digest and
ML-KEM/ML-DSA ACVP-like vector-set checkers. It does not execute binaries, read live
artifacts, or certify implementation conformance.

It also includes tiny JSON-only public ML-KEM/ML-DSA KAT and ACVP-like fixtures under
`fixtures/`, verified only to exercise reproducibility plumbing. The fixtures
declare no artifact execution and make no ACVP certificate, conformance,
side-channel, or security claim.
