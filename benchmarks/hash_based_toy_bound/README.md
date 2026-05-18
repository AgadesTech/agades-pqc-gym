# Hash-Based Toy Bound Benchmark

This benchmark contains deliberately small hash preimage-bound and
collision-bound targets for the public `HASH_BASED` toy evaluator.

The evaluator reports simple toy preimage and birthday-collision work factors
for plumbing and integration tests only. It is not an SLH-DSA/SPHINCS+ security
claim, not collision-finding evidence, and not a replacement for a reviewed
hash-signature analysis or implementation-security harness.

The benchmark also includes tiny SHAKE256 public fixtures under `fixtures/`: a
preimage fixture solved by bounded exhaustive search, and a truncated-collision
fixture that verifies two fixed public messages share the declared 32-bit
digest. These fixtures verify public reproducibility plumbing only. Neither
path is evidence about full-size hash preimage or collision resistance.
