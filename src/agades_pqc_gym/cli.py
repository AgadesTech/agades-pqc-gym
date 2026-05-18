from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer
from pydantic import ValidationError
from rich.console import Console

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.seeds import seed_plan_for_target
from agades_pqc_gym.core.target import TargetSpec
from agades_pqc_gym.core.trace_record import TraceRecord
from agades_pqc_gym.deepevolve_hooks.injection import (
    write_paper_card_injection_batch,
)
from agades_pqc_gym.evaluators.base import EstimatorAdapter
from agades_pqc_gym.evaluators.cascade import CascadeEvaluator, CascadeResult
from agades_pqc_gym.evaluators.lattice_estimator import (
    LatticeEstimatorAdapter,
    LatticeEstimatorConfig,
    SageSubprocessLatticeEstimatorBackend,
)
from agades_pqc_gym.evaluators.mock_estimator import MockEstimatorAdapter
from agades_pqc_gym.evolution.archive import EvolutionArchive, write_evolution_archive
from agades_pqc_gym.evolution.campaign import (
    verify_private_evolution_campaign_plan,
    write_private_evolution_campaign_plan,
)
from agades_pqc_gym.evolution.cron import write_heldout_cron_plan
from agades_pqc_gym.evolution.heldout import build_heldout_candidate_plans
from agades_pqc_gym.evolution.heldout_review_packet import (
    verify_heldout_review_packet,
    write_heldout_review_packet,
)
from agades_pqc_gym.evolution.mutation import (
    write_archive_candidate_mutation_batch,
    write_candidate_mutation_batch,
)
from agades_pqc_gym.evolution.rescore import write_heldout_rescore
from agades_pqc_gym.evolution.scheduler import (
    run_heldout_schedule,
    write_heldout_review_log,
    write_heldout_schedule,
)
from agades_pqc_gym.evolution.snapshot import write_private_archive_snapshot
from agades_pqc_gym.integrations.benchmark_source_contracts import (
    verify_benchmark_source_contracts,
    write_benchmark_source_contracts,
)
from agades_pqc_gym.integrations.deepevolve_research_hooks import (
    verify_deepevolve_research_hooks_manifest,
    write_deepevolve_research_hooks_manifest,
)
from agades_pqc_gym.integrations.ecosystem_smoke import (
    verify_ecosystem_smoke_report,
    write_ecosystem_smoke_report,
)
from agades_pqc_gym.integrations.ecosystem_source_graph import (
    verify_ecosystem_source_graph,
    write_ecosystem_source_graph,
)
from agades_pqc_gym.integrations.external_publication_review_packet import (
    verify_external_publication_review_packet,
    write_external_publication_review_packet,
)
from agades_pqc_gym.integrations.family_operator_catalog import (
    verify_family_operator_catalog,
    write_family_operator_catalog,
)
from agades_pqc_gym.integrations.family_plugin_manifest import (
    verify_family_plugin_manifest,
    write_family_plugin_manifest,
)
from agades_pqc_gym.integrations.family_registry_manifest import (
    verify_family_registry_manifest,
    write_family_registry_manifest,
)
from agades_pqc_gym.integrations.family_support import (
    verify_family_support_matrix,
    write_family_support_matrix,
)
from agades_pqc_gym.integrations.huggingface_collection_manifest import (
    verify_huggingface_collection_manifest,
    write_huggingface_collection_manifest,
)
from agades_pqc_gym.integrations.huggingface_dataset import (
    verify_huggingface_dataset_bundle,
    write_huggingface_dataset_bundle,
)
from agades_pqc_gym.integrations.huggingface_publication_handoff import (
    verify_huggingface_publication_handoff,
    write_huggingface_publication_handoff,
)
from agades_pqc_gym.integrations.huggingface_space_manifest import (
    verify_huggingface_space_manifest,
    write_huggingface_space_manifest,
)
from agades_pqc_gym.integrations.huggingface_space_smoke import (
    verify_huggingface_space_smoke_report,
    write_huggingface_space_smoke_report,
)
from agades_pqc_gym.integrations.lattice_estimator_baseline_contracts import (
    verify_lattice_estimator_baseline_contracts,
    write_lattice_estimator_baseline_contracts,
)
from agades_pqc_gym.integrations.lattice_estimator_baseline_run import (
    verify_lattice_estimator_baseline_run,
    write_lattice_estimator_baseline_run,
)
from agades_pqc_gym.integrations.lattice_estimator_checkout_preflight import (
    write_lattice_estimator_checkout_preflight,
)
from agades_pqc_gym.integrations.lattice_estimator_manifest import (
    LATTICE_ESTIMATOR_PINNED_COMMIT,
    verify_lattice_estimator_manifest,
    write_lattice_estimator_manifest,
)
from agades_pqc_gym.integrations.lattice_estimator_review_packet import (
    verify_lattice_estimator_baseline_review_packet,
    write_lattice_estimator_baseline_review_packet,
)
from agades_pqc_gym.integrations.lattice_estimator_runtime_preflight import (
    verify_lattice_estimator_runtime_preflight,
    write_lattice_estimator_runtime_preflight,
)
from agades_pqc_gym.integrations.nvidia_accelerator import (
    verify_nvidia_accelerator_manifest,
    write_nvidia_accelerator_manifest,
)
from agades_pqc_gym.integrations.nvidia_manifest_safety import (
    verify_nvidia_manifest_safety_report,
    write_nvidia_manifest_safety_report,
)
from agades_pqc_gym.integrations.nvidia_publication_handoff import (
    verify_nvidia_publication_handoff,
    write_nvidia_publication_handoff,
)
from agades_pqc_gym.integrations.prime_environment_manifest import (
    verify_prime_environment_manifest,
    write_prime_environment_manifest,
)
from agades_pqc_gym.integrations.prime_environment_smoke import (
    verify_prime_environment_smoke_report,
    write_prime_environment_smoke_report,
)
from agades_pqc_gym.integrations.prime_publication_handoff import (
    verify_prime_publication_handoff,
    write_prime_publication_handoff,
)
from agades_pqc_gym.integrations.prime_speedrun_handoff import (
    verify_prime_speedrun_handoff,
    write_prime_speedrun_handoff,
)
from agades_pqc_gym.integrations.prime_verifier_schemas import (
    verify_prime_verifier_schemas,
    write_prime_verifier_schemas,
)
from agades_pqc_gym.integrations.private_run_policy import (
    verify_private_run_policy,
    write_private_run_policy,
)
from agades_pqc_gym.integrations.public_benchmark_manifest import (
    verify_public_benchmark_manifest,
    write_public_benchmark_manifest,
)
from agades_pqc_gym.integrations.public_run_export import (
    verify_public_run_export,
    write_public_run_export,
)
from agades_pqc_gym.integrations.publication_manifest import (
    verify_publication_manifest,
    write_publication_manifest,
)
from agades_pqc_gym.integrations.publication_preflight import (
    verify_publication_preflight,
    write_publication_preflight,
)
from agades_pqc_gym.integrations.release_artifacts import (
    write_release_artifacts_until_stable,
)
from agades_pqc_gym.integrations.release_audit import write_release_audit
from agades_pqc_gym.integrations.release_status import (
    verify_release_status,
    write_release_status,
)
from agades_pqc_gym.integrations.runbook_audit import (
    verify_runbook_input_manifest,
    write_runbook_audit,
    write_runbook_input_manifest,
)
from agades_pqc_gym.integrations.source_catalog import (
    verify_source_catalog,
    write_source_catalog,
)
from agades_pqc_gym.openevolve_adapter.config_templates import (
    verify_default_config_template,
    write_default_config_template,
)
from agades_pqc_gym.openevolve_adapter.smoke import (
    verify_openevolve_smoke_report,
    write_openevolve_smoke_report,
)
from agades_pqc_gym.reporting.report import render_report_from_jsonl
from agades_pqc_gym.traces.public_bundle import write_public_run_bundle
from agades_pqc_gym.traces.public_ledger import (
    build_public_run_ledger,
    render_public_trace_jsonl,
)
from agades_pqc_gym.traces.writer import JsonlTraceWriter
from agades_pqc_gym.validators.static import validate_attack_plan
from agades_pqc_gym.verifier import EstimatorChoice, verify_attack_plan_path

app = typer.Typer(no_args_is_help=True)
console = Console()
DEFAULT_EVAL_TRACE = Path("runs/eval_trace.jsonl")
DEFAULT_BENCHMARK_TRACE = Path("runs/benchmark_trace.jsonl")
DEFAULT_PUBLIC_TRACE = Path("public/trace_public.jsonl")
DEFAULT_PUBLIC_LEDGER = Path("public/run_ledger.json")
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
    estimator: Annotated[
        EstimatorChoice,
        typer.Option(
            "--estimator",
            help="Lattice-family estimator backend to use.",
        ),
    ] = "mock",
    estimator_cache: Annotated[
        Path | None,
        typer.Option(
            "--estimator-cache",
            help="Optional JSON cache path for real Lattice Estimator calls.",
        ),
    ] = None,
) -> None:
    """Evaluate one AttackPlan and append a trace record."""
    result = evaluate_attack_plan(
        plan_path=plan_path,
        out=out,
        estimator=estimator,
        estimator_cache=estimator_cache,
    )
    console.print(
        f"score={result.metrics['combined_score']} valid={result.valid} trace={out}"
    )
    if not result.validation.valid:
        raise typer.Exit(1)


@app.command()
def verify(
    plan_path: Path,
    estimator: Annotated[
        EstimatorChoice,
        typer.Option(
            "--estimator",
            help="Lattice-family estimator backend to use.",
        ),
    ] = "mock",
    estimator_cache: Annotated[
        Path | None,
        typer.Option(
            "--estimator-cache",
            help="Optional JSON cache path for real Lattice Estimator calls.",
        ),
    ] = None,
) -> None:
    """Emit public verifier JSON for Prime/HF-style environments."""
    result = verify_attack_plan_path(
        plan_path,
        estimator=estimator,
        estimator_cache=estimator_cache,
    )
    console.print_json(data=result)


@app.command()
def benchmark(
    benchmark_path: Path,
    out: Annotated[Path, typer.Option("--out")] = DEFAULT_BENCHMARK_TRACE,
    estimator: Annotated[
        EstimatorChoice,
        typer.Option(
            "--estimator",
            help="Lattice-family estimator backend to use.",
        ),
    ] = "mock",
    estimator_cache: Annotated[
        Path | None,
        typer.Option(
            "--estimator-cache",
            help="Optional JSON cache path for real Lattice Estimator calls.",
        ),
    ] = None,
) -> None:
    """Evaluate AttackPlan files or target configs in a benchmark directory."""
    plans = load_benchmark_plans(benchmark_path)
    if not plans:
        console.print(f"[red]no benchmark inputs found[/red]: {benchmark_path}")
        raise typer.Exit(1)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("", encoding="utf-8")
    writer = JsonlTraceWriter(out)
    evaluator = CascadeEvaluator(
        estimator=build_lattice_estimator(
            estimator=estimator,
            estimator_cache=estimator_cache,
        )
    )
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


@app.command("evolve-batch")
def evolve_batch(
    candidates_path: Path,
    trace_out: Annotated[Path, typer.Option("--trace-out")] = Path(
        "runs/evolution_trace.jsonl"
    ),
    archive_out: Annotated[Path, typer.Option("--archive-out")] = Path(
        "runs/evolution_archive.json"
    ),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional stable evolution run id."),
    ] = None,
    estimator: Annotated[
        EstimatorChoice,
        typer.Option(
            "--estimator",
            help="Lattice-family estimator backend to use.",
        ),
    ] = "mock",
    estimator_cache: Annotated[
        Path | None,
        typer.Option(
            "--estimator-cache",
            help="Optional JSON cache path for real Lattice Estimator calls.",
        ),
    ] = None,
) -> None:
    """Evaluate a seed candidate batch and write a MAP-Elites archive."""
    plans = load_benchmark_plans(candidates_path)
    if not plans:
        console.print(f"[red]no candidates found[/red]: {candidates_path}")
        raise typer.Exit(1)

    resolved_run_id = run_id or (
        candidates_path.stem if candidates_path.is_file() else candidates_path.name
    )
    trace_out.parent.mkdir(parents=True, exist_ok=True)
    trace_out.write_text("", encoding="utf-8")
    writer = JsonlTraceWriter(trace_out)
    evaluator = CascadeEvaluator(
        estimator=build_lattice_estimator(
            estimator=estimator,
            estimator_cache=estimator_cache,
        )
    )
    records: list[TraceRecord] = []
    for index, plan in enumerate(plans):
        result = evaluator.evaluate_plan(plan)
        record = build_trace_record(
            plan=plan,
            result=result,
            run_id=resolved_run_id,
            candidate_id=f"{plan.attack_plan_id}-g0-{index}",
            generation=0,
            mutation_summary="seed candidate evaluation",
        )
        writer.append(record)
        records.append(record)
        console.print(f"{record.candidate_id}: {result.metrics['combined_score']}")

    archive = write_evolution_archive(records, archive_out, run_id=resolved_run_id)
    console.print(
        f"archive={archive_out} trace={trace_out} "
        f"elites={archive.summary['elite_count']} "
        f"evaluated={archive.summary['evaluated_count']}"
    )


@app.command("mutate-candidates")
def mutate_candidates(
    candidates_path: Path,
    out: Annotated[Path, typer.Option("--out")] = Path("runs/candidate_mutations"),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional stable mutation batch run id."),
    ] = None,
    generation: Annotated[
        int,
        typer.Option(
            "--generation",
            min=1,
            help="Generation number assigned to generated private candidates.",
        ),
    ] = 1,
    max_mutations_per_plan: Annotated[
        int,
        typer.Option(
            "--max-mutations-per-plan",
            min=1,
            help="Maximum reviewed JSON mutations to generate per source plan.",
        ),
    ] = 4,
) -> None:
    """Generate private, JSON-only AttackPlan mutations from reviewed rules."""
    plans = load_benchmark_plans(candidates_path)
    if not plans:
        console.print(f"[red]no candidates found[/red]: {candidates_path}")
        raise typer.Exit(1)

    resolved_run_id = run_id or (
        candidates_path.stem if candidates_path.is_file() else candidates_path.name
    )
    try:
        batch = write_candidate_mutation_batch(
            plans,
            out,
            run_id=resolved_run_id,
            generation=generation,
            max_mutations_per_plan=max_mutations_per_plan,
        )
    except ValueError as exc:
        console.print(f"[red]mutation batch failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    typer.echo(
        f"mutation_manifest={out / 'mutation_manifest.json'} "
        f"plans={out / 'plans'} "
        f"candidates={batch.summary['candidate_count']} "
        f"skipped={batch.summary['skipped_count']}"
    )


@app.command("mutate-archive")
def mutate_archive(
    archive_path: Path,
    source_trace_path: Path,
    out: Annotated[Path, typer.Option("--out")] = Path("runs/archive_mutations"),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional stable mutation batch run id."),
    ] = None,
    generation: Annotated[
        int | None,
        typer.Option(
            "--generation",
            min=1,
            help=(
                "Generation number assigned to generated private candidates. "
                "Defaults to max archive elite generation plus one."
            ),
        ),
    ] = None,
    max_mutations_per_elite: Annotated[
        int,
        typer.Option(
            "--max-mutations-per-elite",
            min=1,
            help="Maximum reviewed JSON mutations to generate per archive elite.",
        ),
    ] = 4,
) -> None:
    """Generate private AttackPlan mutations from MAP-Elites archive elites."""
    try:
        archive = EvolutionArchive.model_validate_json(archive_path.read_text())
        source_records = read_trace_records(source_trace_path)
        resolved_run_id = run_id or f"{archive.run_id}-archive-mutations"
        batch = write_archive_candidate_mutation_batch(
            archive,
            source_records,
            out,
            run_id=resolved_run_id,
            generation=generation,
            max_mutations_per_elite=max_mutations_per_elite,
        )
    except (OSError, ValidationError, ValueError) as exc:
        console.print(f"[red]archive mutation batch failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    typer.echo(
        f"mutation_manifest={out / 'mutation_manifest.json'} "
        f"plans={out / 'plans'} "
        f"candidates={batch.summary['candidate_count']} "
        f"skipped={batch.summary['skipped_count']}"
    )


@app.command("heldout-batch")
def heldout_batch(
    archive_path: Path,
    source_trace_path: Path,
    heldout_targets_path: Path,
    trace_out: Annotated[Path, typer.Option("--trace-out")] = Path(
        "runs/heldout_trace.jsonl"
    ),
    rescore_out: Annotated[Path, typer.Option("--rescore-out")] = Path(
        "runs/heldout_rescore.json"
    ),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional stable held-out run id."),
    ] = None,
    estimator: Annotated[
        EstimatorChoice,
        typer.Option(
            "--estimator",
            help="Lattice-family estimator backend to use.",
        ),
    ] = "mock",
    estimator_cache: Annotated[
        Path | None,
        typer.Option(
            "--estimator-cache",
            help="Optional JSON cache path for real Lattice Estimator calls.",
        ),
    ] = None,
) -> None:
    """Evaluate archive elites on compatible held-out target configs."""
    try:
        archive = EvolutionArchive.model_validate_json(archive_path.read_text())
        source_records = read_trace_records(source_trace_path)
        heldout_targets = load_heldout_targets(heldout_targets_path)
        candidates = build_heldout_candidate_plans(
            archive,
            source_records,
            heldout_targets,
        )
    except (OSError, ValidationError, ValueError) as exc:
        console.print(f"[red]invalid held-out batch input[/red]: {exc}")
        raise typer.Exit(1) from exc

    if not candidates:
        console.print("[red]no held-out candidates produced[/red]")
        raise typer.Exit(1)

    resolved_run_id = run_id or f"{archive.run_id}-heldout"
    trace_out.parent.mkdir(parents=True, exist_ok=True)
    trace_out.write_text("", encoding="utf-8")
    writer = JsonlTraceWriter(trace_out)
    evaluator = CascadeEvaluator(
        estimator=build_lattice_estimator(
            estimator=estimator,
            estimator_cache=estimator_cache,
        )
    )
    heldout_records: list[TraceRecord] = []
    for candidate in candidates:
        result = evaluator.evaluate_plan(candidate.attack_plan)
        record = build_trace_record(
            plan=candidate.attack_plan,
            result=result,
            run_id=resolved_run_id,
            candidate_id=candidate.candidate_id,
            parent_id=candidate.parent_id,
            generation=candidate.generation,
            mutation_summary=candidate.mutation_summary,
        )
        writer.append(record)
        heldout_records.append(record)
        console.print(f"{record.candidate_id}: {result.metrics['combined_score']}")

    report = write_heldout_rescore(
        archive,
        heldout_records,
        rescore_out,
        run_id=f"{resolved_run_id}-rescore",
    )
    console.print(
        f"trace={trace_out} rescore={rescore_out} "
        f"heldout={len(heldout_records)} "
        f"rescored={report.summary['rescored_elite_count']}"
    )


@app.command("heldout-schedule")
def heldout_schedule(
    archive_path: Path,
    source_trace_path: Path,
    heldout_targets_path: Path,
    out: Annotated[Path, typer.Option("--out")] = Path(
        "private/runs/heldout_schedule.json"
    ),
    review_log: Annotated[
        Path | None,
        typer.Option(
            "--review-log",
            help="Private reviewed approval log required by the scheduler policy.",
        ),
    ] = None,
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
    trace_out: Annotated[Path, typer.Option("--trace-out")] = Path(
        "private/traces/heldout_trace.jsonl"
    ),
    rescore_out: Annotated[Path, typer.Option("--rescore-out")] = Path(
        "private/reports/heldout_rescore.json"
    ),
    trigger: Annotated[
        str,
        typer.Option("--trigger", help="Reviewed private scheduler trigger."),
    ] = "manual_reviewed",
    approval: Annotated[
        list[str] | None,
        typer.Option(
            "--approval",
            help="Required scheduler approval gate. Repeat for every gate.",
        ),
    ] = None,
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional stable held-out schedule id."),
    ] = None,
) -> None:
    """Write a reviewed local held-out schedule without executing it."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        schedule = write_heldout_schedule(
            out,
            archive_path=archive_path,
            source_trace_path=source_trace_path,
            heldout_targets_path=heldout_targets_path,
            policy=policy_payload,
            trace_out=trace_out,
            rescore_out=rescore_out,
            approvals=approval or [],
            review_log_path=review_log,
            trigger=trigger,
            run_id=run_id,
            root=Path.cwd(),
        )
    except (OSError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]held-out schedule failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    typer.echo(
        f"schedule={out} ready={schedule['ready_to_run']} "
        f"scheduled={schedule['summary']['scheduled_candidates']}"
    )


@app.command("heldout-review-log")
def heldout_review_log(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "private/runs/heldout_review_log.json"
    ),
    approval: Annotated[
        list[str] | None,
        typer.Option(
            "--approval",
            help="Approved scheduler gate. Repeat for every reviewed gate.",
        ),
    ] = None,
    reviewed_by: Annotated[
        str,
        typer.Option("--reviewed-by", help="Reviewer identity for the approval log."),
    ] = "local-reviewer",
    review_id: Annotated[
        str,
        typer.Option("--review-id", help="Stable review log identifier."),
    ] = "local-heldout-review",
    reviewed_at: Annotated[
        str,
        typer.Option("--reviewed-at", help="Review timestamp or stable review label."),
    ] = "manual-review-recorded",
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
) -> None:
    """Write a private durable held-out approval log."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        review_log = write_heldout_review_log(
            out,
            approvals=approval or [],
            reviewed_by=reviewed_by,
            review_id=review_id,
            reviewed_at=reviewed_at,
            policy=policy_payload,
            root=Path.cwd(),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]held-out review log failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    typer.echo(f"review_log={out} approvals={len(review_log['entries'])}")


@app.command("rescore-archive")
def rescore_archive(
    archive_path: Path,
    heldout_trace_path: Path,
    out: Annotated[Path, typer.Option("--out")] = Path("runs/heldout_rescore.json"),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional stable held-out rescore run id."),
    ] = None,
) -> None:
    """Aggregate held-out trace records for explicit archive elites."""
    try:
        archive = EvolutionArchive.model_validate_json(archive_path.read_text())
        heldout_records = read_trace_records(heldout_trace_path)
    except (OSError, ValidationError, ValueError) as exc:
        console.print(f"[red]invalid held-out rescore input[/red]: {exc}")
        raise typer.Exit(1) from exc

    resolved_run_id = run_id or f"{archive.run_id}-heldout-rescore"
    report = write_heldout_rescore(
        archive,
        heldout_records,
        out,
        run_id=resolved_run_id,
    )
    console.print(
        f"rescore={out} elites={report.summary['elite_count']} "
        f"rescored={report.summary['rescored_elite_count']} "
        f"unmatched={report.summary['unmatched_heldout_record_count']}"
    )
    if (
        report.summary["elite_count"] > 0
        and report.summary["rescored_elite_count"] == 0
    ):
        raise typer.Exit(1)


@app.command("heldout-run-schedule")
def heldout_run_schedule(
    schedule_path: Path,
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
    estimator: Annotated[
        EstimatorChoice,
        typer.Option(
            "--estimator",
            help="Lattice-family estimator backend to use.",
        ),
    ] = "mock",
    estimator_cache: Annotated[
        Path | None,
        typer.Option(
            "--estimator-cache",
            help="Optional JSON cache path for real Lattice Estimator calls.",
        ),
    ] = None,
) -> None:
    """Run a reviewed private held-out schedule without shell execution."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        report = run_heldout_schedule(
            schedule_path,
            policy=policy_payload,
            estimator=build_lattice_estimator(
                estimator=estimator,
                estimator_cache=estimator_cache,
            ),
            root=Path.cwd(),
        )
    except (OSError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]held-out schedule run failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    typer.echo(
        f"schedule_run={report['schedule_run_id']} "
        f"trace={report['outputs']['heldout_trace']} "
        f"rescore={report['outputs']['rescore_report']} "
        f"heldout={report['summary']['heldout_records']} "
        f"rescored={report['summary']['rescored_elites']}"
    )


@app.command("heldout-review-packet")
def heldout_review_packet(
    schedule_path: Path,
    out: Annotated[Path, typer.Option("--out")] = Path(
        "private/reports/heldout_review_packet.json"
    ),
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
    reviewer_label: Annotated[
        str,
        typer.Option(
            "--reviewer-label",
            help="Stable label for the intended held-out expert-review audience.",
        ),
    ] = "pending-expert-review",
) -> None:
    """Write a private digest-only held-out review packet."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        packet = write_heldout_review_packet(
            out,
            schedule_path=schedule_path,
            policy=policy_payload,
            root=Path.cwd(),
            reviewer_label=reviewer_label,
        )
    except (OSError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]held-out review packet failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    summary = packet["summary"]
    typer.echo(
        f"heldout_review_packet={out} "
        f"heldout={summary['heldout_record_count']} "
        f"rescored={summary['rescored_elite_count']}"
    )


@app.command("heldout-review-packet-verify")
def heldout_review_packet_verify(
    packet: Annotated[Path, typer.Option("--packet")] = Path(
        "private/reports/heldout_review_packet.json"
    ),
    schedule: Annotated[
        Path | None,
        typer.Option("--schedule", help="Optional explicit held-out schedule path."),
    ] = None,
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
) -> None:
    """Verify a private digest-only held-out review packet."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        result = verify_heldout_review_packet(
            packet,
            schedule_path=schedule,
            policy=policy_payload,
            root=Path.cwd(),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]held-out review packet verify failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("private-evolution-campaign-plan")
def private_evolution_campaign_plan(
    seed_candidates_path: Path,
    heldout_targets_path: Path,
    out: Annotated[Path, typer.Option("--out")] = Path(
        "private/runs/manual-private-evolution/campaign_plan.json"
    ),
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
    review_log: Annotated[
        Path,
        typer.Option("--review-log", help="Private reviewed approval log."),
    ] = Path("private/runs/heldout_review_log.json"),
    run_id: Annotated[
        str,
        typer.Option("--run-id", help="Stable private campaign run id."),
    ] = "manual-private-evolution",
) -> None:
    """Write a private, non-executing evolution campaign plan."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        plan = write_private_evolution_campaign_plan(
            out,
            seed_candidates_path=seed_candidates_path,
            heldout_targets_path=heldout_targets_path,
            policy=policy_payload,
            review_log_path=review_log,
            root=Path.cwd(),
            run_id=run_id,
            policy_path=policy,
        )
    except (OSError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]private evolution campaign plan failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    typer.echo(
        f"private_evolution_campaign_plan={out} "
        f"steps={plan['summary']['step_count']} "
        f"seed_plans={plan['summary']['seed_plan_count']} "
        f"heldout_targets={plan['summary']['heldout_target_count']}"
    )


@app.command("private-evolution-campaign-plan-verify")
def private_evolution_campaign_plan_verify(
    plan: Annotated[
        Path,
        typer.Option("--plan"),
    ] = Path("private/runs/manual-private-evolution/campaign_plan.json"),
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
) -> None:
    """Verify a private, non-executing evolution campaign plan."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        result = verify_private_evolution_campaign_plan(
            plan,
            policy=policy_payload,
            root=Path.cwd(),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        console.print(
            f"[red]private evolution campaign plan verify failed[/red]: {exc}"
        )
        raise typer.Exit(1) from exc

    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("heldout-cron-plan")
def heldout_cron_plan(
    schedule_path: Path,
    out: Annotated[Path, typer.Option("--out")] = Path(
        "private/runs/heldout_cron_plan.json"
    ),
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
    minute: Annotated[
        int,
        typer.Option("--minute", help="Cron minute, from 0 to 59."),
    ] = 17,
    every_hours: Annotated[
        int,
        typer.Option("--every-hours", help="Cron hour interval, from 1 to 24."),
    ] = 6,
    log_path: Annotated[Path, typer.Option("--log-path")] = Path(
        "private/runs/heldout_cron.log"
    ),
) -> None:
    """Write a private local-cron plan for an already reviewed held-out schedule."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        plan = write_heldout_cron_plan(
            out,
            schedule_path=schedule_path,
            policy=policy_payload,
            policy_path=policy,
            minute=minute,
            every_hours=every_hours,
            log_path=log_path,
            root=Path.cwd(),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]held-out cron plan failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    typer.echo(
        f"cron_plan={out} schedule={plan['schedule']['path']} "
        f"expression={plan['cron']['expression']} "
        f"manual_install={plan['installation']['requires_manual_install']}"
    )


@app.command("archive-snapshot")
def archive_snapshot(
    archive_path: Path,
    source_trace_path: Path,
    out: Annotated[Path, typer.Option("--out")] = Path(
        "private/runs/archive_snapshot.json"
    ),
    review_log: Annotated[
        Path,
        typer.Option(
            "--review-log",
            help="Private review log approving the retention snapshot gates.",
        ),
    ] = Path("private/runs/heldout_review_log.json"),
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional stable archive snapshot run id."),
    ] = None,
) -> None:
    """Write a private archive snapshot manifest without trace payloads."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        snapshot = write_private_archive_snapshot(
            out,
            archive_path=archive_path,
            source_trace_path=source_trace_path,
            review_log_path=review_log,
            policy=policy_payload,
            root=Path.cwd(),
            run_id=run_id,
        )
    except (OSError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]archive snapshot failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    typer.echo(
        f"archive_snapshot={out} "
        f"archive={snapshot['inputs']['archive']['path']} "
        f"trace_records={snapshot['inputs']['source_trace']['record_count']} "
        f"trace_links_complete={snapshot['trace_link_integrity']['complete']}"
    )


@app.command("export-public")
def export_public(
    trace_path: Path,
    out: Annotated[Path, typer.Option("--out")] = DEFAULT_PUBLIC_TRACE,
) -> None:
    """Export a sanitized public JSONL trace."""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        render_public_trace_jsonl(read_trace_records(trace_path)),
        encoding="utf-8",
    )
    console.print(f"exported={out}")


@app.command("public-ledger")
def public_ledger(
    trace_path: Path,
    out: Annotated[Path, typer.Option("--out")] = DEFAULT_PUBLIC_LEDGER,
) -> None:
    """Package a deterministic public run ledger JSON from a trace JSONL file."""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(build_public_run_ledger(trace_path), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    console.print(f"ledger={out}")


@app.command("public-bundle")
def public_bundle(
    trace_path: Path,
    out: Annotated[Path, typer.Option("--out")] = Path("public/run_bundle"),
) -> None:
    """Write a public trace, run ledger, README, and checksum manifest."""
    bundle = write_public_run_bundle(trace_path, out)
    console.print(f"bundle={bundle['out_dir']}")


@app.command("public-run-export")
def public_run_export(
    out: Annotated[Path, typer.Option("--out")] = Path("public/run_export"),
) -> None:
    """Write a flat public runs export for Prime/HF/NVIDIA review surfaces."""
    write_public_run_export(out)
    typer.echo(f"public_run_export={out}")


@app.command("public-run-export-verify")
def public_run_export_verify(
    export: Annotated[Path, typer.Option("--export")] = Path("public/run_export"),
) -> None:
    """Verify the flat public runs export."""
    result = verify_public_run_export(export)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("hf-dataset")
def hf_dataset(
    out: Annotated[Path, typer.Option("--out")] = Path("public/hf_dataset"),
) -> None:
    """Write a deterministic Hugging Face dataset bundle."""
    bundle = write_huggingface_dataset_bundle(out)
    typer.echo(f"hf_dataset={bundle['out_dir']}")


@app.command("hf-dataset-verify")
def hf_dataset_verify(
    dataset: Annotated[Path, typer.Option("--dataset")] = Path("hf/dataset"),
) -> None:
    """Verify the deterministic Hugging Face dataset bundle."""
    result = verify_huggingface_dataset_bundle(dataset)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("hf-space-manifest")
def hf_space_manifest(
    out: Annotated[Path, typer.Option("--out")] = Path("hf/space_manifest.json"),
) -> None:
    """Write a deterministic Hugging Face Space manifest."""
    write_huggingface_space_manifest(out)
    typer.echo(f"hf_space_manifest={out}")


@app.command("hf-space-manifest-verify")
def hf_space_manifest_verify(
    manifest: Annotated[Path, typer.Option("--manifest")] = Path(
        "hf/space_manifest.json"
    ),
) -> None:
    """Verify the Hugging Face Space manifest safety and sync contract."""
    result = verify_huggingface_space_manifest(manifest)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("hf-space-smoke")
def hf_space_smoke(
    out: Annotated[Path, typer.Option("--out")] = Path("reports/hf_space_smoke.json"),
) -> None:
    """Write a deterministic Hugging Face Space smoke report."""
    report = write_huggingface_space_smoke_report(out)
    typer.echo(f"hf_space_smoke={out}")
    if not report["accepted"]:
        raise typer.Exit(1)


@app.command("hf-space-smoke-verify")
def hf_space_smoke_verify(
    report: Annotated[Path, typer.Option("--report")] = Path(
        "reports/hf_space_smoke.json"
    ),
) -> None:
    """Verify the checked Hugging Face Space smoke report."""
    result = verify_huggingface_space_smoke_report(report)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("hf-collection-manifest")
def hf_collection_manifest(
    out: Annotated[Path, typer.Option("--out")] = Path("hf/collection_manifest.json"),
) -> None:
    """Write a deterministic Hugging Face Collection manifest."""
    write_huggingface_collection_manifest(out)
    typer.echo(f"hf_collection_manifest={out}")


@app.command("hf-collection-manifest-verify")
def hf_collection_manifest_verify(
    manifest: Annotated[Path, typer.Option("--manifest")] = Path(
        "hf/collection_manifest.json"
    ),
) -> None:
    """Verify the Hugging Face Collection manifest safety and sync contract."""
    result = verify_huggingface_collection_manifest(manifest)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("hf-publication-handoff")
def hf_publication_handoff(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/huggingface_publication_handoff.json"
    ),
) -> None:
    """Write a deterministic Hugging Face publication handoff."""
    write_huggingface_publication_handoff(out)
    typer.echo(f"huggingface_publication_handoff={out}")


@app.command("hf-publication-handoff-verify")
def hf_publication_handoff_verify(
    handoff: Annotated[Path, typer.Option("--handoff")] = Path(
        "docs/huggingface_publication_handoff.json"
    ),
) -> None:
    """Verify the Hugging Face publication handoff safety boundary."""
    result = verify_huggingface_publication_handoff(handoff)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("nvidia-manifest")
def nvidia_manifest(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "nvidia/accelerator_manifest.json"
    ),
) -> None:
    """Write a deterministic NVIDIA/accelerator alignment manifest."""
    write_nvidia_accelerator_manifest(out)
    typer.echo(f"nvidia_manifest={out}")


@app.command("nvidia-manifest-verify")
def nvidia_manifest_verify(
    manifest: Annotated[Path, typer.Option("--manifest")] = Path(
        "nvidia/accelerator_manifest.json"
    ),
) -> None:
    """Verify the NVIDIA/accelerator manifest safety and sync contract."""
    result = verify_nvidia_accelerator_manifest(manifest)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("nvidia-manifest-safety")
def nvidia_manifest_safety(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "reports/nvidia_manifest_safety.json"
    ),
) -> None:
    """Write a deterministic NVIDIA manifest safety report."""
    report = write_nvidia_manifest_safety_report(out)
    typer.echo(f"nvidia_manifest_safety={out}")
    if not report["accepted"]:
        raise typer.Exit(1)


@app.command("nvidia-manifest-safety-verify")
def nvidia_manifest_safety_verify(
    report: Annotated[Path, typer.Option("--report")] = Path(
        "reports/nvidia_manifest_safety.json"
    ),
) -> None:
    """Verify the checked NVIDIA manifest safety report."""
    result = verify_nvidia_manifest_safety_report(report)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("nvidia-publication-handoff")
def nvidia_publication_handoff(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/nvidia_publication_handoff.json"
    ),
) -> None:
    """Write a deterministic NVIDIA review handoff without submitting externally."""
    write_nvidia_publication_handoff(out)
    typer.echo(f"nvidia_publication_handoff={out}")


@app.command("nvidia-publication-handoff-verify")
def nvidia_publication_handoff_verify(
    handoff: Annotated[Path, typer.Option("--handoff")] = Path(
        "docs/nvidia_publication_handoff.json"
    ),
) -> None:
    """Verify the NVIDIA handoff review and no-GPU-claim boundaries."""
    result = verify_nvidia_publication_handoff(handoff)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("openevolve-config")
def openevolve_config(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "examples/openevolve/config.yaml"
    ),
) -> None:
    """Write the default private JSON AttackPlan OpenEvolve loop template."""
    write_default_config_template(out)
    typer.echo(f"openevolve_config={out}")


@app.command("openevolve-config-verify")
def openevolve_config_verify(
    config: Annotated[Path, typer.Option("--config")] = Path(
        "examples/openevolve/config.yaml"
    ),
) -> None:
    """Verify the checked OpenEvolve private loop config template."""
    result = verify_default_config_template(config)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("openevolve-smoke")
def openevolve_smoke(
    out: Annotated[Path, typer.Option("--out")] = Path("reports/openevolve_smoke.json"),
    plan: Annotated[Path, typer.Option("--plan")] = Path(
        "examples/attack_plans/lattice_primal_usvp_toy.json"
    ),
    evaluator: Annotated[Path, typer.Option("--evaluator")] = Path(
        "examples/openevolve/evaluator.py"
    ),
) -> None:
    """Write a deterministic OpenEvolve evaluator smoke report."""
    report = write_openevolve_smoke_report(
        out,
        plan_path=plan,
        evaluator_path=evaluator,
    )
    typer.echo(f"openevolve_smoke={out}")
    if not report["accepted"]:
        raise typer.Exit(1)


@app.command("openevolve-smoke-verify")
def openevolve_smoke_verify(
    report: Annotated[Path, typer.Option("--report")] = Path(
        "reports/openevolve_smoke.json"
    ),
) -> None:
    """Verify the checked OpenEvolve evaluator smoke report."""
    result = verify_openevolve_smoke_report(report)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("ecosystem-smoke")
def ecosystem_smoke(
    out: Annotated[Path, typer.Option("--out")] = Path("reports/ecosystem_smoke.json"),
) -> None:
    """Write a local Prime/Hugging Face/NVIDIA ecosystem smoke report."""
    report = write_ecosystem_smoke_report(out)
    typer.echo(f"ecosystem_smoke={out}")
    if not report["accepted"]:
        raise typer.Exit(1)


@app.command("ecosystem-smoke-verify")
def ecosystem_smoke_verify(
    report: Annotated[Path, typer.Option("--report")] = Path(
        "reports/ecosystem_smoke.json"
    ),
) -> None:
    """Verify the checked-in local ecosystem smoke report."""
    result = verify_ecosystem_smoke_report(report)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("publication-manifest")
def publication_manifest(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/publication_manifest.json"
    ),
) -> None:
    """Write a deterministic OSS publication readiness manifest."""
    write_publication_manifest(out)
    typer.echo(f"publication_manifest={out}")


@app.command("publication-manifest-verify")
def publication_manifest_verify(
    manifest: Annotated[Path, typer.Option("--manifest")] = Path(
        "docs/publication_manifest.json"
    ),
) -> None:
    """Verify the multi-platform OSS publication manifest."""
    result = verify_publication_manifest(manifest)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("publication-preflight")
def publication_preflight(
    out: Annotated[
        Path,
        typer.Option("--out"),
    ] = Path("public/publication_preflight.json"),
    family_support_matrix: Annotated[
        Path,
        typer.Option("--family-support-matrix"),
    ] = Path("docs/family_support_matrix.json"),
    publication_manifest: Annotated[
        Path,
        typer.Option("--publication-manifest"),
    ] = Path("docs/publication_manifest.json"),
    release_audit: Annotated[
        Path,
        typer.Option("--release-audit"),
    ] = Path("public/release_audit.json"),
    release_status: Annotated[
        Path,
        typer.Option("--release-status"),
    ] = Path("docs/release_status.json"),
    external_release_review_approved: Annotated[
        bool,
        typer.Option("--external-release-review-approved"),
    ] = False,
    credentials_reviewed: Annotated[
        bool,
        typer.Option("--credentials-reviewed"),
    ] = False,
) -> None:
    """Write the local OSS publication preflight gate."""
    write_publication_preflight(
        out,
        family_support_matrix_path=family_support_matrix,
        publication_manifest_path=publication_manifest,
        release_audit_path=release_audit,
        release_status_path=release_status,
        external_release_review_approved=external_release_review_approved,
        credentials_reviewed=credentials_reviewed,
    )
    typer.echo(f"publication_preflight={out}")


@app.command("publication-preflight-verify")
def publication_preflight_verify(
    preflight: Annotated[
        Path,
        typer.Option("--preflight"),
    ] = Path("public/publication_preflight.json"),
    family_support_matrix: Annotated[
        Path,
        typer.Option("--family-support-matrix"),
    ] = Path("docs/family_support_matrix.json"),
    publication_manifest: Annotated[
        Path,
        typer.Option("--publication-manifest"),
    ] = Path("docs/publication_manifest.json"),
    release_audit: Annotated[
        Path,
        typer.Option("--release-audit"),
    ] = Path("public/release_audit.json"),
    release_status: Annotated[
        Path,
        typer.Option("--release-status"),
    ] = Path("docs/release_status.json"),
) -> None:
    """Verify the local OSS publication preflight gate."""
    result = verify_publication_preflight(
        preflight,
        family_support_matrix_path=family_support_matrix,
        publication_manifest_path=publication_manifest,
        release_audit_path=release_audit,
        release_status_path=release_status,
    )
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("external-publication-review-packet")
def external_publication_review_packet(
    out: Annotated[
        Path,
        typer.Option("--out"),
    ] = Path("docs/external_publication_review_packet.json"),
) -> None:
    """Write the external HF/Prime/NVIDIA publication review packet."""
    write_external_publication_review_packet(out)
    typer.echo(f"external_publication_review_packet={out}")


@app.command("external-publication-review-packet-verify")
def external_publication_review_packet_verify(
    packet: Annotated[
        Path,
        typer.Option("--packet"),
    ] = Path("docs/external_publication_review_packet.json"),
) -> None:
    """Verify the external HF/Prime/NVIDIA publication review packet."""
    result = verify_external_publication_review_packet(packet)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("private-run-policy")
def private_run_policy(
    out: Annotated[
        Path,
        typer.Option("--out"),
    ] = Path("docs/private_run_policy.json"),
) -> None:
    """Write the private evolution trace and moat holdback policy."""
    write_private_run_policy(out)
    typer.echo(f"private_run_policy={out}")


@app.command("private-run-policy-verify")
def private_run_policy_verify(
    policy: Annotated[
        Path,
        typer.Option("--policy"),
    ] = Path("docs/private_run_policy.json"),
) -> None:
    """Verify the private evolution trace and moat holdback policy."""
    result = verify_private_run_policy(policy)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("public-benchmark-manifest")
def public_benchmark_manifest(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/public_benchmark_manifest.json"
    ),
) -> None:
    """Write a deterministic public benchmark v0 readiness manifest."""
    write_public_benchmark_manifest(out)
    typer.echo(f"public_benchmark_manifest={out}")


@app.command("public-benchmark-verify")
def public_benchmark_verify(
    manifest: Annotated[Path, typer.Option("--manifest")] = Path(
        "docs/public_benchmark_manifest.json"
    ),
) -> None:
    """Verify public benchmark v0 manifest digests and no-claim boundaries."""
    result = verify_public_benchmark_manifest(manifest)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("prime-manifest")
def prime_manifest(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "prime_intellect/verifiers_environment/prime_manifest.json"
    ),
) -> None:
    """Write a deterministic Prime Verifiers environment manifest."""
    write_prime_environment_manifest(out)
    typer.echo(f"prime_manifest={out}")


@app.command("prime-manifest-verify")
def prime_manifest_verify(
    manifest: Annotated[Path, typer.Option("--manifest")] = Path(
        "prime_intellect/verifiers_environment/prime_manifest.json"
    ),
) -> None:
    """Verify the Prime Verifiers environment manifest."""
    result = verify_prime_environment_manifest(manifest)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("prime-environment-smoke")
def prime_environment_smoke(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "reports/prime_environment_smoke.json"
    ),
) -> None:
    """Write a deterministic Prime Verifiers environment smoke report."""
    report = write_prime_environment_smoke_report(out)
    typer.echo(f"prime_environment_smoke={out}")
    if not report["accepted"]:
        raise typer.Exit(1)


@app.command("prime-environment-smoke-verify")
def prime_environment_smoke_verify(
    report: Annotated[Path, typer.Option("--report")] = Path(
        "reports/prime_environment_smoke.json"
    ),
) -> None:
    """Verify the checked Prime Verifiers environment smoke report."""
    result = verify_prime_environment_smoke_report(report)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("prime-publication-handoff")
def prime_publication_handoff(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/prime_publication_handoff.json"
    ),
) -> None:
    """Write a Prime publication handoff manifest without publishing externally."""
    write_prime_publication_handoff(out)
    typer.echo(f"prime_publication_handoff={out}")


@app.command("prime-publication-handoff-verify")
def prime_publication_handoff_verify(
    handoff: Annotated[Path, typer.Option("--handoff")] = Path(
        "docs/prime_publication_handoff.json"
    ),
) -> None:
    """Verify the Prime publication handoff and review boundaries."""
    result = verify_prime_publication_handoff(handoff)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("prime-speedrun-handoff")
def prime_speedrun_handoff(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/prime_speedrun_handoff.json"
    ),
) -> None:
    """Write a Prime autonomous-speedrun handoff manifest without executing."""
    write_prime_speedrun_handoff(out)
    typer.echo(f"prime_speedrun_handoff={out}")


@app.command("prime-speedrun-handoff-verify")
def prime_speedrun_handoff_verify(
    handoff: Annotated[Path, typer.Option("--handoff")] = Path(
        "docs/prime_speedrun_handoff.json"
    ),
) -> None:
    """Verify the Prime speedrun handoff and execution boundaries."""
    result = verify_prime_speedrun_handoff(handoff)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("prime-schemas")
def prime_schemas(
    out: Annotated[Path, typer.Option("--out")] = Path("prime_intellect/schemas"),
) -> None:
    """Write Prime/HF public verifier submission and result JSON schemas."""
    write_prime_verifier_schemas(out)
    typer.echo(f"prime_schemas={out}")


@app.command("prime-schemas-verify")
def prime_schemas_verify(
    schemas: Annotated[Path, typer.Option("--schemas")] = Path(
        "prime_intellect/schemas"
    ),
) -> None:
    """Verify the Prime/HF public verifier schema bundle."""
    result = verify_prime_verifier_schemas(schemas)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("source-catalog")
def source_catalog(
    out: Annotated[Path, typer.Option("--out")] = Path("docs/source_catalog.json"),
) -> None:
    """Write a deterministic public OSS/source catalog."""
    write_source_catalog(out)
    typer.echo(f"source_catalog={out}")


@app.command("source-catalog-verify")
def source_catalog_verify(
    catalog: Annotated[Path, typer.Option("--catalog")] = Path(
        "docs/source_catalog.json"
    ),
) -> None:
    """Verify the public OSS/source catalog."""
    result = verify_source_catalog(catalog)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("deepevolve-injections")
def deepevolve_injections(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "private/candidates/paper_card_injections.json"
    ),
    paper_card_dir: Annotated[
        Path,
        typer.Option("--paper-card-dir"),
    ] = Path("examples/paper_cards"),
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
    run_id: Annotated[
        str,
        typer.Option("--run-id", help="Stable private paper-card injection run id."),
    ] = "paper-card-injection",
) -> None:
    """Write private DeepEvolve paper-card hypothesis injections."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        batch = write_paper_card_injection_batch(
            out,
            paper_card_dir=paper_card_dir,
            run_id=run_id,
            policy=policy_payload,
            root=Path.cwd(),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]DeepEvolve injection batch failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    typer.echo(
        f"deepevolve_injections={out} "
        f"injections={batch['summary']['injection_count']} "
        f"review_required={batch['summary']['all_injections_review_required']}"
    )


@app.command("deepevolve-manifest")
def deepevolve_manifest(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/deepevolve_research_hooks_manifest.json"
    ),
) -> None:
    """Write a deterministic DeepEvolve-style research hook manifest."""
    write_deepevolve_research_hooks_manifest(out)
    typer.echo(f"deepevolve_manifest={out}")


@app.command("deepevolve-manifest-verify")
def deepevolve_manifest_verify(
    manifest: Annotated[Path, typer.Option("--manifest")] = Path(
        "docs/deepevolve_research_hooks_manifest.json"
    ),
) -> None:
    """Verify DeepEvolve-style paper cards stay note-only and review-gated."""
    result = verify_deepevolve_research_hooks_manifest(manifest)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("benchmark-source-contracts")
def benchmark_source_contracts(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/benchmark_source_contracts.json"
    ),
) -> None:
    """Write review-gated future benchmark adapter contracts."""
    write_benchmark_source_contracts(out)
    typer.echo(f"benchmark_source_contracts={out}")


@app.command("benchmark-source-verify")
def benchmark_source_verify(
    contracts: Annotated[Path, typer.Option("--contracts")] = Path(
        "docs/benchmark_source_contracts.json"
    ),
) -> None:
    """Verify review-gated future benchmark adapter contracts."""
    result = verify_benchmark_source_contracts(contracts)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("family-support")
def family_support(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/family_support_matrix.json"
    ),
) -> None:
    """Write a deterministic public family support matrix."""
    write_family_support_matrix(out)
    typer.echo(f"family_support={out}")


@app.command("family-support-verify")
def family_support_verify(
    matrix: Annotated[Path, typer.Option("--matrix")] = Path(
        "docs/family_support_matrix.json"
    ),
) -> None:
    """Verify the public multi-family support matrix."""
    result = verify_family_support_matrix(matrix)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("family-registry-manifest")
def family_registry_manifest(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/family_registry_manifest.json"
    ),
) -> None:
    """Write a deterministic runtime family registry manifest."""
    write_family_registry_manifest(out)
    typer.echo(f"family_registry_manifest={out}")


@app.command("family-registry-manifest-verify")
def family_registry_manifest_verify(
    manifest: Annotated[Path, typer.Option("--manifest")] = Path(
        "docs/family_registry_manifest.json"
    ),
) -> None:
    """Verify the runtime family registry manifest."""
    result = verify_family_registry_manifest(manifest)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("family-plugin-manifest")
def family_plugin_manifest(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/family_plugin_manifest.json"
    ),
) -> None:
    """Write a deterministic family plugin descriptor manifest."""
    write_family_plugin_manifest(out)
    typer.echo(f"family_plugin_manifest={out}")


@app.command("family-plugin-manifest-verify")
def family_plugin_manifest_verify(
    manifest: Annotated[Path, typer.Option("--manifest")] = Path(
        "docs/family_plugin_manifest.json"
    ),
) -> None:
    """Verify the family plugin descriptor manifest."""
    result = verify_family_plugin_manifest(manifest)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("ecosystem-source-graph")
def ecosystem_source_graph(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/ecosystem_source_graph.json"
    ),
) -> None:
    """Write the OSS source catalog / source contract / family support graph."""
    write_ecosystem_source_graph(out)
    typer.echo(f"ecosystem_source_graph={out}")


@app.command("ecosystem-source-graph-verify")
def ecosystem_source_graph_verify(
    graph: Annotated[Path, typer.Option("--graph")] = Path(
        "docs/ecosystem_source_graph.json"
    ),
) -> None:
    """Verify the OSS source graph has no dangling review-source edges."""
    result = verify_ecosystem_source_graph(graph)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("family-operator-catalog")
def family_operator_catalog(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/family_operator_catalog.json"
    ),
) -> None:
    """Write a deterministic family operator/evaluator catalog."""
    write_family_operator_catalog(out)
    typer.echo(f"family_operator_catalog={out}")


@app.command("family-operator-catalog-verify")
def family_operator_catalog_verify(
    catalog: Annotated[Path, typer.Option("--catalog")] = Path(
        "docs/family_operator_catalog.json"
    ),
) -> None:
    """Verify the family operator/evaluator catalog."""
    result = verify_family_operator_catalog(catalog)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("lattice-estimator-manifest")
def lattice_estimator_manifest(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/lattice_estimator_manifest.json"
    ),
) -> None:
    """Write a deterministic Lattice Estimator pin and review-boundary manifest."""
    write_lattice_estimator_manifest(out)
    typer.echo(f"lattice_estimator_manifest={out}")


@app.command("lattice-estimator-manifest-verify")
def lattice_estimator_manifest_verify(
    manifest: Annotated[Path, typer.Option("--manifest")] = Path(
        "docs/lattice_estimator_manifest.json"
    ),
) -> None:
    """Verify the Lattice Estimator pin and review-boundary manifest."""
    result = verify_lattice_estimator_manifest(manifest)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("lattice-estimator-baseline-contracts")
def lattice_estimator_baseline_contracts(
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/lattice_estimator_baseline_contracts.json"
    ),
) -> None:
    """Write deterministic Lattice Estimator baseline reproduction contracts."""
    write_lattice_estimator_baseline_contracts(out)
    typer.echo(f"lattice_estimator_baseline_contracts={out}")


@app.command("lattice-estimator-baseline-contracts-verify")
def lattice_estimator_baseline_contracts_verify(
    contracts: Annotated[Path, typer.Option("--contracts")] = Path(
        "docs/lattice_estimator_baseline_contracts.json"
    ),
) -> None:
    """Verify Lattice Estimator baseline reproduction contracts."""
    result = verify_lattice_estimator_baseline_contracts(contracts)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("lattice-estimator-checkout-preflight")
def lattice_estimator_checkout_preflight(
    estimator_source: Annotated[
        Path,
        typer.Option(
            "--estimator-source",
            help="Local Lattice Estimator checkout to inspect without importing.",
        ),
    ],
    out: Annotated[Path, typer.Option("--out")] = Path(
        "private/reports/lattice_estimator_checkout_preflight.json"
    ),
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
    required_commit: Annotated[
        str,
        typer.Option(
            "--required-commit",
            help="Reviewed Lattice Estimator commit required for readiness.",
        ),
    ] = LATTICE_ESTIMATOR_PINNED_COMMIT,
) -> None:
    """Write a private, non-executing Lattice Estimator checkout preflight."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        report = write_lattice_estimator_checkout_preflight(
            out,
            source_path=estimator_source,
            policy=policy_payload,
            policy_root=Path.cwd(),
            required_commit=required_commit,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]Lattice Estimator checkout preflight failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    readiness = report["readiness"]
    typer.echo(
        f"lattice_estimator_checkout_preflight={out} "
        f"ready={readiness['ready_for_private_baseline_run']} "
        f"failures={readiness['failure_count']}"
    )
    if not readiness["ready_for_private_baseline_run"]:
        raise typer.Exit(1)


@app.command("lattice-estimator-runtime-preflight")
def lattice_estimator_runtime_preflight(
    sage_command: Annotated[
        str,
        typer.Option(
            "--sage-command",
            help="Sage executable used to probe the private estimator runtime.",
        ),
    ] = "sage",
    sage_python_command: Annotated[
        str | None,
        typer.Option(
            "--sage-python-command",
            help=(
                "Command used to run Python with sage.all importable. Defaults "
                "to '<sage-command> -python' for legacy Sage installations."
            ),
        ),
    ] = None,
    out: Annotated[Path, typer.Option("--out")] = Path(
        "private/reports/lattice_estimator_runtime_preflight.json"
    ),
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
    timeout_seconds: Annotated[
        int,
        typer.Option(
            "--timeout-seconds",
            help="Maximum seconds for each Sage runtime probe.",
            min=1,
        ),
    ] = 15,
) -> None:
    """Write a private Sage runtime preflight for Lattice Estimator imports."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        report = write_lattice_estimator_runtime_preflight(
            out,
            sage_command=sage_command,
            sage_python_command=sage_python_command,
            policy=policy_payload,
            policy_root=Path.cwd(),
            timeout_seconds=timeout_seconds,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]Lattice Estimator runtime preflight failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    readiness = report["readiness"]
    typer.echo(
        f"lattice_estimator_runtime_preflight={out} "
        f"ready={readiness['ready_for_private_lattice_estimator_import']} "
        f"failures={readiness['failure_count']}"
    )
    if not readiness["ready_for_private_lattice_estimator_import"]:
        raise typer.Exit(1)


@app.command("lattice-estimator-runtime-preflight-verify")
def lattice_estimator_runtime_preflight_verify(
    preflight: Annotated[Path, typer.Option("--preflight")] = Path(
        "private/reports/lattice_estimator_runtime_preflight.json"
    ),
) -> None:
    """Verify a private Sage runtime preflight report."""
    result = verify_lattice_estimator_runtime_preflight(preflight)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("lattice-estimator-baseline-run")
def lattice_estimator_baseline_run(
    contracts: Annotated[Path, typer.Option("--contracts")] = Path(
        "docs/lattice_estimator_baseline_contracts.json"
    ),
    contracts_root: Annotated[
        Path,
        typer.Option(
            "--contracts-root",
            help=(
                "Project root used to resolve source_path entries inside the "
                "baseline contracts."
            ),
        ),
    ] = Path("."),
    out: Annotated[Path, typer.Option("--out")] = Path(
        "private/reports/lattice_estimator_baseline_run.json"
    ),
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional stable private baseline run id."),
    ] = None,
    estimator: Annotated[
        EstimatorChoice,
        typer.Option(
            "--estimator",
            help="Lattice-family estimator backend to use for private baselines.",
        ),
    ] = "lattice",
    estimator_cache: Annotated[
        Path | None,
        typer.Option(
            "--estimator-cache",
            help="Optional JSON cache path for real Lattice Estimator calls.",
        ),
    ] = None,
    estimator_source: Annotated[
        Path | None,
        typer.Option(
            "--estimator-source",
            help=(
                "Optional local Lattice Estimator checkout. Git HEAD must match "
                "the reviewed pin before the estimator package is imported."
            ),
        ),
    ] = None,
    sage_command: Annotated[
        str | None,
        typer.Option(
            "--sage-command",
            help=(
                "Run the private Lattice Estimator checkout under this Sage "
                "executable via sage -python. Requires --estimator-source."
            ),
        ),
    ] = None,
    sage_python_command: Annotated[
        str | None,
        typer.Option(
            "--sage-python-command",
            help=(
                "Run the private Lattice Estimator checkout under this Python "
                "command with sage.all importable. Accepts command arguments "
                "without using a shell and requires --estimator-source."
            ),
        ),
    ] = None,
) -> None:
    """Write a private pin-checked Lattice Estimator baseline run report."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        report = write_lattice_estimator_baseline_run(
            out,
            contracts_path=contracts,
            policy=policy_payload,
            adapter=build_lattice_estimator(
                estimator=estimator,
                estimator_cache=estimator_cache,
                estimator_source=estimator_source,
                sage_command=sage_command,
                sage_python_command=sage_python_command,
            ),
            contracts_root=contracts_root,
            policy_root=Path.cwd(),
            run_id=run_id,
        )
    except (OSError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]Lattice Estimator baseline run failed[/red]: {exc}")
        raise typer.Exit(1) from exc

    summary = report["summary"]
    typer.echo(
        f"lattice_estimator_baseline_run={out} "
        f"ok={summary['ok_results']} "
        f"errors={summary['error_results']} "
        f"numeric={summary['numeric_result_count']}"
    )
    if summary["numeric_result_count"] == 0:
        raise typer.Exit(1)


@app.command("lattice-estimator-baseline-run-verify")
def lattice_estimator_baseline_run_verify(
    report: Annotated[Path, typer.Option("--report")] = Path(
        "private/reports/lattice_estimator_baseline_run.json"
    ),
    contracts_root: Annotated[
        Path,
        typer.Option(
            "--contracts-root",
            help=(
                "Project root used to verify the baseline contracts referenced "
                "by the private report."
            ),
        ),
    ] = Path("."),
) -> None:
    """Verify a private pin-checked Lattice Estimator baseline run report."""
    result = verify_lattice_estimator_baseline_run(
        report,
        contracts_root=contracts_root,
    )
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("lattice-estimator-baseline-review-packet")
def lattice_estimator_baseline_review_packet(
    baseline_report: Annotated[Path, typer.Option("--baseline-report")] = Path(
        "private/reports/lattice_estimator_baseline_run.json"
    ),
    out: Annotated[Path, typer.Option("--out")] = Path(
        "private/reports/lattice_estimator_baseline_review_packet.json"
    ),
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "docs/private_run_policy.json"
    ),
    contracts_root: Annotated[
        Path,
        typer.Option(
            "--contracts-root",
            help=(
                "Project root used to verify the baseline contracts referenced "
                "by the private baseline report."
            ),
        ),
    ] = Path("."),
    reviewer_label: Annotated[
        str,
        typer.Option(
            "--reviewer-label",
            help="Stable label for the intended expert-review audience.",
        ),
    ] = "pending-expert-review",
) -> None:
    """Write a private digest-only baseline review packet for expert review."""
    policy_verification = verify_private_run_policy(policy)
    if not policy_verification["accepted"]:
        console.print_json(data=policy_verification)
        raise typer.Exit(1)

    try:
        policy_payload = json.loads(policy.read_text(encoding="utf-8"))
        packet = write_lattice_estimator_baseline_review_packet(
            out,
            baseline_report_path=baseline_report,
            policy=policy_payload,
            contracts_root=contracts_root,
            policy_root=Path.cwd(),
            reviewer_label=reviewer_label,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        console.print(
            f"[red]Lattice Estimator baseline review packet failed[/red]: {exc}"
        )
        raise typer.Exit(1) from exc

    summary = packet["summary"]
    typer.echo(
        f"lattice_estimator_baseline_review_packet={out} "
        f"results={summary['result_count']} "
        f"digests={summary['raw_output_digest_count']}"
    )


@app.command("lattice-estimator-baseline-review-packet-verify")
def lattice_estimator_baseline_review_packet_verify(
    packet: Annotated[Path, typer.Option("--packet")] = Path(
        "private/reports/lattice_estimator_baseline_review_packet.json"
    ),
    baseline_report: Annotated[
        Path | None,
        typer.Option(
            "--baseline-report",
            help="Optional explicit private baseline report to verify against.",
        ),
    ] = None,
    contracts_root: Annotated[
        Path,
        typer.Option(
            "--contracts-root",
            help=(
                "Project root used to verify the baseline contracts referenced "
                "by the private baseline report."
            ),
        ),
    ] = Path("."),
) -> None:
    """Verify a private digest-only baseline review packet."""
    result = verify_lattice_estimator_baseline_review_packet(
        packet,
        baseline_report_path=baseline_report,
        contracts_root=contracts_root,
    )
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("release-audit")
def release_audit(
    out: Annotated[Path, typer.Option("--out")] = Path("public/release_audit.json"),
) -> None:
    """Write a deterministic public release safety audit."""
    audit = write_release_audit(out)
    typer.echo(f"release_audit={out}")
    if not audit["accepted"]:
        raise typer.Exit(1)


@app.command("release-artifacts")
def release_artifacts(
    root: Annotated[Path, typer.Option("--root")] = Path("."),
    max_passes: Annotated[int, typer.Option("--max-passes")] = 6,
) -> None:
    """Converge and verify cyclic public release artifacts."""
    result = write_release_artifacts_until_stable(root=root, max_passes=max_passes)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("release-status")
def release_status(
    out: Annotated[Path, typer.Option("--out")] = Path("docs/release_status.json"),
) -> None:
    """Write a deterministic OSS release status summary."""
    write_release_status(out)
    typer.echo(f"release_status={out}")


@app.command("release-status-verify")
def release_status_verify(
    status: Annotated[Path, typer.Option("--status")] = Path(
        "docs/release_status.json"
    ),
) -> None:
    """Verify the deterministic OSS release status summary."""
    result = verify_release_status(status)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command("runbook-audit")
def runbook_audit(
    out: Annotated[Path, typer.Option("--out")] = Path("public/runbook_audit.json"),
    brief: Annotated[
        Path | None,
        typer.Option(
            "--brief",
            help="Optional source long-running brief to anchor the audit.",
        ),
    ] = None,
    context: Annotated[
        Path | None,
        typer.Option(
            "--context",
            help="Optional project-context transcript to anchor the audit.",
        ),
    ] = None,
) -> None:
    """Write a deterministic runbook deliverable audit."""
    audit = write_runbook_audit(out, brief_path=brief, context_path=context)
    typer.echo(f"runbook_audit={out}")
    if not audit["accepted"]:
        raise typer.Exit(1)


@app.command("runbook-input-manifest")
def runbook_input_manifest(
    brief: Annotated[
        Path,
        typer.Option("--brief", help="Source long-running brief to anchor."),
    ],
    context: Annotated[
        Path,
        typer.Option("--context", help="Project-context transcript to anchor."),
    ],
    out: Annotated[Path, typer.Option("--out")] = Path(
        "docs/runbook_input_manifest.json"
    ),
) -> None:
    """Write a digest-only manifest for external runbook source inputs."""
    write_runbook_input_manifest(out, brief_path=brief, context_path=context)
    typer.echo(f"runbook_input_manifest={out}")


@app.command("runbook-input-manifest-verify")
def runbook_input_manifest_verify(
    manifest: Annotated[Path, typer.Option("--manifest")] = Path(
        "docs/runbook_input_manifest.json"
    ),
) -> None:
    """Verify the digest-only runbook source-input manifest."""
    result = verify_runbook_input_manifest(manifest)
    console.print_json(data=result)
    if not result["accepted"]:
        raise typer.Exit(1)


@app.command()
def report(
    trace_path: Path,
    out: Annotated[Path, typer.Option("--out")] = DEFAULT_REPORT,
) -> None:
    """Generate a Markdown report from a trace JSONL file."""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_report_from_jsonl(trace_path, title="Agades PQC Gym Report"))
    console.print(f"report={out}")


def evaluate_attack_plan(
    plan_path: Path,
    out: Path,
    estimator: EstimatorChoice = "mock",
    estimator_cache: Path | None = None,
) -> CascadeResult:
    evaluator = CascadeEvaluator(
        estimator=build_lattice_estimator(
            estimator=estimator,
            estimator_cache=estimator_cache,
        )
    )
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


def build_lattice_estimator(
    *,
    estimator: EstimatorChoice,
    estimator_cache: Path | None,
    estimator_source: Path | None = None,
    sage_command: str | None = None,
    sage_python_command: str | None = None,
) -> EstimatorAdapter:
    if estimator == "mock":
        if estimator_source is not None:
            raise ValueError("--estimator-source requires --estimator lattice")
        if sage_command is not None:
            raise ValueError("--sage-command requires --estimator lattice")
        if sage_python_command is not None:
            raise ValueError("--sage-python-command requires --estimator lattice")
        return MockEstimatorAdapter()
    if estimator == "lattice":
        if sage_command is not None or sage_python_command is not None:
            if estimator_source is None:
                raise ValueError(
                    "--sage-command/--sage-python-command requires --estimator-source"
                )
            return LatticeEstimatorAdapter(
                backend=SageSubprocessLatticeEstimatorBackend(
                    sage_command=sage_command or "sage",
                    sage_python_command=sage_python_command,
                    source_path=estimator_source,
                    required_commit=LATTICE_ESTIMATOR_PINNED_COMMIT,
                ),
                cache_path=estimator_cache,
                config=LatticeEstimatorConfig(
                    required_commit=LATTICE_ESTIMATOR_PINNED_COMMIT
                ),
            )
        return LatticeEstimatorAdapter(
            cache_path=estimator_cache,
            source_path=estimator_source,
            config=LatticeEstimatorConfig(
                required_commit=LATTICE_ESTIMATOR_PINNED_COMMIT
            ),
        )
    raise ValueError(f"unsupported estimator backend: {estimator}")


def build_trace_record(
    *,
    plan: AttackPlan,
    result: CascadeResult,
    run_id: str,
    candidate_id: str,
    parent_id: str | None = None,
    generation: int = 0,
    mutation_summary: str = "direct evaluation",
) -> TraceRecord:
    public_release_ok = plan.metadata.public and result.validation.valid
    evaluation = dict(result.metrics)
    evaluation["valid"] = result.valid
    if result.estimator_result is not None:
        evaluation["estimator_name"] = result.estimator_result.estimator_name
        evaluation["estimator_version"] = result.estimator_result.estimator_version
    evaluation["warnings"] = result.warnings

    return TraceRecord.from_evaluation(
        run_id=run_id,
        candidate_id=candidate_id,
        parent_id=parent_id,
        generation=generation,
        mutation_summary=mutation_summary,
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


def load_heldout_targets(path: Path) -> list[TargetSpec]:
    if path.is_file():
        return [_load_target_or_plan_target(path)]
    targets: list[TargetSpec] = []
    for candidate in sorted(path.glob("*.json")):
        targets.append(_load_target_or_plan_target(candidate))
    return targets


def _load_attack_plan_or_seed(path: Path) -> AttackPlan:
    raw = path.read_text()
    try:
        return AttackPlan.model_validate_json(raw)
    except ValidationError:
        data: dict[str, Any] = json.loads(raw)
        target_data = data.get("target", data)
        target = TargetSpec.model_validate(target_data)
        return seed_plan_for_target(target)


def _load_target_or_plan_target(path: Path) -> TargetSpec:
    raw = path.read_text()
    try:
        return AttackPlan.model_validate_json(raw).target
    except ValidationError:
        data: dict[str, Any] = json.loads(raw)
        target_data = data.get("target", data)
        return TargetSpec.model_validate(target_data)


if __name__ == "__main__":
    app()
