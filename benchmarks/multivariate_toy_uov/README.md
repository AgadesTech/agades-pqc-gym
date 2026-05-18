# Multivariate Toy UOV Public-Map Benchmark

This benchmark exercises a bounded `MULTIVARIATE` UOV-inspired public-map
verification fixture on a tiny public `GF(2)` target.

The fixture evaluates a fixed public signature under a fixed public quadratic
map and checks the declared output vector. It is verifier plumbing only: it is
not a UOV, MAYO, Rainbow, Groebner-basis, forgery, or deployed-parameter
security result.
