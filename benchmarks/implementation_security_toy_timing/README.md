# Implementation-Security Toy Timing Benchmark

This benchmark contains public JSON-only timing-summary verifier fixtures for
the `IMPLEMENTATION_SECURITY` plugin.

The checked surface is intentionally narrow:

- operator: `constant_time_check`
- tool: `toy_welch_timing_check`
- model: `toy_timing_welch_t_check`
- fixture: `fixtures/toy_timing_welch_fixture.json`
- tool: `toy_dudect_summary_check`
- model: `toy_dudect_summary_threshold_check`
- fixture: `fixtures/toy_dudect_mlkem_summary_fixture.json`
- tool: `toy_ctgrind_secret_taint_summary_check`
- model: `toy_ctgrind_secret_taint_summary_check`
- fixture: `fixtures/toy_ctgrind_mlkem_secret_taint_fixture.json`

The evaluator computes bounded Welch-style absolute t statistics from the small
cycle-count arrays already present in JSON. The dudect-style fixture is a
summary contract only: it does not execute dudect. The ctgrind-style fixture is
a bounded secret-taint summary contract only: it does not execute ctgrind. The
benchmark does not execute binaries, read trace files, connect to devices,
perform side-channel analysis, certify constant-time behavior, or make an
implementation-security claim.
