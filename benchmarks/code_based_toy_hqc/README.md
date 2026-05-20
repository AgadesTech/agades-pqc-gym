# Code-Based Toy HQC-Inspired Benchmark

This benchmark contains deliberately small HQC-inspired decoder fixtures under
the `CODE_BASED` family.

The evaluator uses bounded majority decoding for a repetition-code fixture,
bounded reliability-weighted voting for a weighted repetition-code fixture,
bounded exact-weight syndrome search for a parity-check fixture, and bounded
double-block circulant syndrome search, bounded erasure-aided syndrome search,
and bounded erasure-constrained circulant syndrome search for HQC-inspired
fixtures. These exist to exercise code-based validation and reproduction paths
that are not ISD estimators. They are not HQC results, not Classic McEliece
results, and not deployed-code security claims.

The checked-in AttackPlans request reproduction against
`toy_hqc_repetition_21_7_w3_fixture.json`,
`toy_hqc_weighted_repetition_25_5_w4_fixture.json`,
`toy_hqc_parity_check_15_7_w2_fixture.json`,
`toy_hqc_circulant_syndrome_16_8_w2_fixture.json`, and
`toy_hqc_erasure_syndrome_12_6_w2_fixture.json`, plus
`toy_hqc_circulant_erasure_16_8_w3_fixture.json`. The fixtures are mirrored as
package data for installed public-verifier environments. Passing reproduction
only shows that the family-specific fixture plumbing is deterministic and
correctly scoped.
