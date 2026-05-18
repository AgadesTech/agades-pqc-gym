# Code-Based Toy Classic-McEliece-Inspired Benchmark

This benchmark contains deliberately small binary syndrome-decoding fixtures
under the `CODE_BASED` family.

The evaluator uses bounded exact-weight syndrome search against tiny public
parity-check matrices, including a support-set restricted fixture that
enumerates only declared public support positions. The surface exists to
exercise Classic-McEliece-inspired code-based validation and reproduction paths
without implementing a Goppa-code decoder, a Classic McEliece parameter
estimator, or any deployed-code security claim.

The checked-in AttackPlans request reproduction against
`toy_classic_mceliece_syndrome_17_9_w2_fixture.json` and
`toy_classic_mceliece_support_syndrome_19_10_w2_fixture.json`. The fixtures are
mirrored as package data for installed public-verifier environments. Passing
reproduction only shows that the family-specific fixture plumbing is
deterministic and correctly scoped.
