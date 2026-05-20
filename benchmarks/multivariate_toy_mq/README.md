# Multivariate Toy MQ Benchmark

This benchmark exercises the bounded `MULTIVARIATE` toy MQ evaluator on small
public system shapes, including exhaustive-search, hybrid-search, and
degree-bound plumbing.

It also includes one tiny `GF(2)` reproduction fixture under `fixtures/`, solved
by bounded exhaustive search, a bounded guess-prefix hybrid split-search harness,
and the degree-bound public reproduction wrapper only to verify public
reproducibility plumbing.

It is a verifier-plumbing fixture only. The degree-bound case is not a
Groebner proof or Groebner-basis implementation, not a UOV/MAYO/Rainbow attack
claim, and not evidence about deployed
multivariate parameters.
