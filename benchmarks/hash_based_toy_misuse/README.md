# Hash-Based Toy Misuse Benchmark

This benchmark contains a deliberately small JSON-only reused-salt fixture for
the public `HASH_BASED` toy evaluator.

The evaluator recomputes toy SHAKE256 digest prefixes and checks whether the
same public salt appears on distinct messages. It is misuse-detection plumbing
only, not exploit evidence and not a security claim.
