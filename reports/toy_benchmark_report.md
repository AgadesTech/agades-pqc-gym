# Agades LWE Strategy Gym Report

## Summary

This report summarizes toy/downscaled AttackPlan evaluations.

## Results

| Candidate | Valid | Score | Time Bits | Memory Bits | Estimator |
| --- | --- | ---: | ---: | ---: | --- |
| toy_lwe_n64_q257_primal_seed-0 | True | -67.4696 | 63.5296 | 17.36 | mock-lattice-estimator |
| toy_lwe_n96_q769_primal_seed-1 | True | -97.0376 | 91.1776 | 25.04 | mock-lattice-estimator |

## Mock Vs Real Estimator Status

At least one result uses the mock estimator. Mock output is not a security claim and exists only to verify evaluator plumbing.

## Limitations

Estimator outputs are hypotheses requiring independent review. This report is not a security claim, does not target live systems, and does not imply a break of any deployed post-quantum cryptographic standard.
