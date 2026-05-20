# Isogeny Historical Toy Path Benchmark

This benchmark exercises the bounded `ISOGENY_HISTORICAL` toy path evaluator on small historical SIDH/SIKE-style, commutative-walk-style, and volcano-style graph/path shapes.

It is a verifier-plumbing fixture only. It is not an isogeny solver, not a current-standard attack claim, and not evidence about deployed post-quantum parameters.

`toy_sidh_path_fixture_verify.json`,
`toy_commutative_walk_fixture_verify.json`, and
`toy_volcano_walk_fixture_verify.json` additionally verify explicit public
historical toy path fixtures under `fixtures/`. The volcano fixture checks a
tiny public graph/path and level transitions. The verifier checks declared
fixture shape and no-claim flags only; it does not solve isogeny problems.
