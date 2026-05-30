# Agades PQC Gym Quickstart

This is the shortest useful path through the gym. It does not publish anything,
does not call external services, and does not make a security claim.

## 1. Install

```bash
uv sync --extra dev
```

## 2. Run The Guided Demo

```bash
uv run agades-pqc quickstart
```

The command writes these local files under `runs/quickstart/`:

- `lattice_trace.jsonl`: one toy LWE evaluation trace.
- `lattice_benchmark.jsonl`: the toy LWE benchmark trace.
- `lattice_report.md`: a Markdown report generated from the lattice trace.
- `code_based_prange_trace.jsonl`: one toy code-based evaluator trace.
- `unsupported_placeholder_trace.jsonl`: a schema-only unsupported example.

The important line in the terminal is the evaluation status:

```text
status=ok ... accepted=True ... plan_valid=True ...
```

For a family route that is intentionally not implemented yet, the gym says so
explicitly:

```text
status=unsupported score=n/a accepted=False plan_valid=True ... reason=CODE_BASED evaluator is not implemented ... not a security claim
```

`unsupported` means the JSON shape was understood, but the gym refused to invent
an estimate for a family route that has no reviewed evaluator.

## 3. Run The Core Loop Manually

Validate a toy LWE plan:

```bash
uv run agades-pqc validate examples/attack_plans/lattice_primal_usvp_toy.json
```

Evaluate it and write a trace:

```bash
uv run agades-pqc evaluate examples/attack_plans/lattice_primal_usvp_toy.json --trace runs/demo_trace.jsonl
```

Run the smallest bundled lattice benchmark:

```bash
uv run agades-pqc benchmark benchmarks/lattice_toy_lwe --trace runs/demo_benchmark.jsonl
```

Each benchmark line uses the same status fields as `evaluate`, for example
`status=ok`, `accepted=True`, `plan_valid=True`, and `trace=...`. Unsupported
benchmark rows use `status=unsupported score=n/a` and include the refusal
reason instead of printing an internal sentinel score.

Generate a report from the trace:

```bash
uv run agades-pqc report runs/demo_trace.jsonl --out reports/demo_report.md
```

## 4. Inspect Unsupported Behavior

```bash
uv run agades-pqc evaluate examples/attack_plans/code_based_isd_placeholder.json --trace runs/code_based_placeholder.jsonl
```

This should exit successfully as a CLI command but report `status=unsupported`
with `plan_valid=True` and `accepted=False` for the evaluated plan. That
distinction is deliberate: the JSON is structurally valid, but the gym refuses
to accept or estimate a route that has no reviewed evaluator.

Invalid AttackPlan JSON is different: the gym rejects it and does not claim a
trace file was written.

```bash
uv run agades-pqc evaluate examples/attack_plans/invalid_plan_should_fail.json --trace runs/invalid_trace.jsonl
```

Expected shape:

```text
status=invalid score=n/a ... trace=not_written reason=... next=...
```

## 5. List Guided Examples

```bash
uv run agades-pqc examples
```

This prints the smallest safe example set:

- `lattice-ok`: toy LWE path, expected `status=ok`.
- `code-based-toy`: bounded public Prange-style toy path, expected `status=ok`.
- `schema-only-unsupported`: placeholder path, expected `status=unsupported`.
- `invalid-plan`: expected validation failure.

## 6. Check The Formal Contract Bundle

Run the short formal verifier surface:

```bash
uv run agades-pqc formal-check
```

This checks the committed AttackPlan semantics, operator semantics, estimator
model, typed obligation ledger, family coverage, LWE/MLWE proof artifacts,
reviewer governance, and the latest Lean build smoke report.

If Lean/Lake is available and you want to refresh the compiled evidence, run:

```bash
uv run agades-pqc formal-lean-build-smoke --out reports/formal_lean_build_smoke.json
uv run agades-pqc formal-lean-build-smoke-verify --report reports/formal_lean_build_smoke.json
```

This compiles the checked Lean 4 + Mathlib source bundle under `formal/lean/`
and writes a bounded report with command argv, return code, output hashes, and
short output tails. It does not capture environment variables or credentials.

Passing this smoke check means the formal contracts compile. It is not a
cryptographic soundness review, it does not run cryptanalytic estimators, and
it does not authorize any public security claim.

## CLI Surface

`uv run agades-pqc --help` shows the core workflow commands first:

- `quickstart`
- `examples`
- `validate`
- `evaluate`
- `verify`
- `benchmark`
- `report`
- `formal-check`

Release, ecosystem, and artifact-generation commands are still available by
name, but hidden from first-screen help so a new user sees the gym workflow
before the release machinery.
