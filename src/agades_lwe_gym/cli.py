from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer
from pydantic import ValidationError
from rich.console import Console

from agades_lwe_gym.dsl.examples import seed_primal_plan
from agades_lwe_gym.dsl.schema import AttackPlan, Target
from agades_lwe_gym.evaluators.cascade import CascadeEvaluator, CascadeResult
from agades_lwe_gym.reporting.report import render_report_from_jsonl
from agades_lwe_gym.traces.redaction import redact_trace_record
from agades_lwe_gym.traces.schema import TraceRecord
from agades_lwe_gym.traces.writer import JsonlTraceWriter
from agades_lwe_gym.validators.static import validate_attack_plan

app = typer.Typer(no_args_is_help=True)
console = Console()
DEFAULT_EVAL_TRACE = Path("runs/eval_trace.jsonl")
DEFAULT_BENCHMARK_TRACE = Path("runs/benchmark_trace.jsonl")
DEFAULT_PUBLIC_TRACE = Path("public/trace_public.jsonl")
DEFAULT_REPORT = Path("reports/report.md")


@app.command()
def validate(plan_path: Path) -> None:
    """Validate an AttackPlan JSON file."""
    try:
        plan = AttackPlan.model_validate_json(plan_path.read_text())
    except (OSError, ValidationError) as exc:
        console.print(f"[red]invalid[/red]: {exc}")
        raise typer.Exit(1) from exc

    result = validate_attack_plan(plan)
    if result.valid:
        console.print(f"[green]valid[/green]: {plan.attack_plan_id}")
        return

    console.print(f"[red]invalid[/red]: {plan.attack_plan_id}")
    for error in result.errors:
        console.print(f"- {error}")
    raise typer.Exit(1)


@app.command()
def evaluate(
    plan_path: Path,
    out: Annotated[Path, typer.Option("--out")] = DEFAULT_EVAL_TRACE,
) -> None:
    """Evaluate one AttackPlan and append a trace record."""
    result = evaluate_attack_plan(plan_path=plan_path, out=out)
    console.print(
        f"score={result.metrics['combined_score']} valid={result.valid} trace={out}"
    )
    if not result.valid:
        raise typer.Exit(1)


@app.command()
def benchmark(
    benchmark_path: Path,
    out: Annotated[Path, typer.Option("--out")] = DEFAULT_BENCHMARK_TRACE,
) -> None:
    """Evaluate AttackPlan files or target configs in a benchmark directory."""
    plans = load_benchmark_plans(benchmark_path)
    if not plans:
        console.print(f"[red]no benchmark inputs found[/red]: {benchmark_path}")
        raise typer.Exit(1)

    writer = JsonlTraceWriter(out)
    evaluator = CascadeEvaluator()
    for index, plan in enumerate(plans):
        result = evaluator.evaluate_plan(plan)
        record = build_trace_record(
            plan=plan,
            result=result,
            run_id=benchmark_path.name,
            candidate_id=f"{plan.attack_plan_id}-{index}",
        )
        writer.append(record)
        console.print(f"{plan.attack_plan_id}: {result.metrics['combined_score']}")


@app.command("export-public")
def export_public(
    trace_path: Path,
    out: Annotated[Path, typer.Option("--out")] = DEFAULT_PUBLIC_TRACE,
) -> None:
    """Export a sanitized public JSONL trace."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for record in read_trace_records(trace_path):
            handle.write(json.dumps(redact_trace_record(record), sort_keys=True) + "\n")
    console.print(f"exported={out}")


@app.command()
def report(
    trace_path: Path,
    out: Annotated[Path, typer.Option("--out")] = DEFAULT_REPORT,
) -> None:
    """Generate a Markdown report from a trace JSONL file."""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        render_report_from_jsonl(trace_path, title="Agades LWE Strategy Gym Report")
    )
    console.print(f"report={out}")


def evaluate_attack_plan(plan_path: Path, out: Path) -> CascadeResult:
    evaluator = CascadeEvaluator()
    result = evaluator.evaluate_path(plan_path)
    if result.plan is None:
        return result
    writer = JsonlTraceWriter(out)
    writer.append(
        build_trace_record(
            plan=result.plan,
            result=result,
            run_id="cli-evaluate",
            candidate_id=result.plan.attack_plan_id,
        )
    )
    return result


def build_trace_record(
    *,
    plan: AttackPlan,
    result: CascadeResult,
    run_id: str,
    candidate_id: str,
) -> TraceRecord:
    public_release_ok = plan.metadata.public and result.valid
    evaluation = dict(result.metrics)
    evaluation["valid"] = result.valid
    if result.estimator_result is not None:
        evaluation["estimator_name"] = result.estimator_result.estimator_name
        evaluation["estimator_version"] = result.estimator_result.estimator_version
        evaluation["warnings"] = result.estimator_result.warnings
    else:
        evaluation["warnings"] = result.warnings

    return TraceRecord.from_evaluation(
        run_id=run_id,
        candidate_id=candidate_id,
        parent_id=None,
        generation=0,
        mutation_summary="direct evaluation",
        attack_plan=plan,
        evaluation=evaluation,
        accepted=result.valid,
        public_release_ok=public_release_ok,
        redaction_reason=None if public_release_ok else "invalid or private plan",
    )


def read_trace_records(path: Path) -> list[TraceRecord]:
    return [
        TraceRecord.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def load_benchmark_plans(path: Path) -> list[AttackPlan]:
    if path.is_file():
        return [_load_attack_plan_or_seed(path)]
    plans: list[AttackPlan] = []
    for candidate in sorted(path.glob("*.json")):
        plans.append(_load_attack_plan_or_seed(candidate))
    return plans


def _load_attack_plan_or_seed(path: Path) -> AttackPlan:
    raw = path.read_text()
    try:
        return AttackPlan.model_validate_json(raw)
    except ValidationError:
        data: dict[str, Any] = json.loads(raw)
        target_data = data.get("target", data)
        target = Target.model_validate(target_data)
        return seed_primal_plan(target, attack_plan_id=f"{target.name}_primal_seed")


if __name__ == "__main__":
    app()
