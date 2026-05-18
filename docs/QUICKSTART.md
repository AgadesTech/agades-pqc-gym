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
status=ok ... valid=True ...
```

For a family route that is intentionally not implemented yet, the gym says so
explicitly:

```text
status=unsupported ... valid=False ... reason=CODE_BASED evaluator is not implemented
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
uv run agades-pqc evaluate examples/attack_plans/lattice_primal_usvp_toy.json --out runs/demo_trace.jsonl
```

Generate a report from the trace:

```bash
uv run agades-pqc report runs/demo_trace.jsonl --out reports/demo_report.md
```

## 4. Inspect Unsupported Behavior

```bash
uv run agades-pqc evaluate examples/attack_plans/code_based_isd_placeholder.json --out runs/code_based_placeholder.jsonl
```

This should exit successfully as a CLI command but report `status=unsupported`
and `valid=False` for the evaluated plan. That distinction is deliberate: the
tool can record unsupported routes without pretending they are valid
cryptanalytic results.

## CLI Surface

`uv run agades-pqc --help` shows the core workflow commands first:

- `quickstart`
- `validate`
- `evaluate`
- `verify`
- `benchmark`
- `report`

Release, ecosystem, and artifact-generation commands are still available by
name, but hidden from first-screen help so a new user sees the gym workflow
before the release machinery.
