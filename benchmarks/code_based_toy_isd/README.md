# Code-Based Toy ISD Benchmark

This benchmark contains deliberately small binary syndrome-decoding targets for
the public `CODE_BASED` toy evaluator.

The evaluator uses conservative toy Prange, Lee-Brickell-style, Stern-style,
Dumer-style list-merging, and quasi-cyclic rotation models for plumbing and
integration tests only. It is not an HQC, Classic McEliece, or deployed-code
security claim.

The checked-in benchmark AttackPlans also request reproduction against tiny
public binary syndrome-decoding fixtures solved by bounded exhaustive search:
`toy_syndrome_31_16_w3_fixture.json` and
`toy_syndrome_15_7_w2_fixture.json`. The Lee-Brickell-style, Stern-style, and
Dumer-style toy benchmarks use the same `toy_syndrome_31_16_w3_fixture.json`
fixture with different bounded ISD work-factor models. The quasi-cyclic toy
benchmark uses `toy_qc_syndrome_21_12_w2_fixture.json` and enumerates only the
declared block rotations. The reproduction results only prove the
family-specific harness and public trace plumbing; they are not cryptanalytic
evidence for deployed parameters.
