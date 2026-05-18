# Code-Based Toy MDPC Bit-Flip Benchmark

This benchmark contains tiny public binary parity-check fixtures for bounded
MDPC/BIKE-inspired bit-flip decoders. It includes a simple threshold variant,
a black-gray threshold variant, and a syndrome-weight descent variant, only to
verify JSON AttackPlan-to-fixture plumbing for the `code_based` family.

The fixture is deliberately small, public, and non-cryptanalytic. It does not
claim anything about BIKE, MDPC security, deployed parameters, or real decoding
costs.
