# Hash-Based Toy Signature Benchmark

This benchmark contains deliberately small SHAKE256 hash-signature chain and
Merkle auth-path verification targets for the public `HASH_BASED` toy
evaluator.

The evaluator reports simple chain-verification and auth-path verification work
factors for plumbing and integration tests only. The fixtures check four short
public chains and one three-level public auth path; they never execute external
code or read live artifacts.

This is not an SLH-DSA/SPHINCS+ security claim and is not a replacement for a
reviewed hash-signature analysis.
