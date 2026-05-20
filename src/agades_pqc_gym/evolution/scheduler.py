from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from agades_pqc_gym.core.target import TargetSpec
from agades_pqc_gym.evaluators.base import EstimatorAdapter
from agades_pqc_gym.evaluators.cascade import CascadeEvaluator, CascadeResult
from agades_pqc_gym.evolution.archive import EvolutionArchive
from agades_pqc_gym.evolution.heldout import (
    HeldoutCandidatePlan,
    build_heldout_candidate_plans,
)
from agades_pqc_gym.evolution.rescore import write_heldout_rescore
from agades_pqc_gym.traces.schema import TraceRecord
from agades_pqc_gym.traces.writer import JsonlTraceWriter

HELDOUT_SCHEDULE_SCHEMA = "agades.pqc.heldout_schedule.v1"
HELDOUT_SCHEDULE_RUN_SCHEMA = "agades.pqc.heldout_schedule_run.v1"
HELDOUT_REVIEW_LOG_SCHEMA = "agades.pqc.heldout_review_log.v1"
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TRIGGER = "manual_reviewed"


def build_heldout_schedule(
    *,
    archive_path: Path,
    source_trace_path: Path,
    heldout_targets_path: Path,
    policy: dict[str, Any],
    trace_out: Path,
    rescore_out: Path,
    approvals: list[str],
    review_log_path: Path | None = None,
    trigger: str = DEFAULT_TRIGGER,
    root: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    scheduler_policy = _scheduler_policy(policy)
    retention = _policy_mapping(scheduler_policy, "retention")
    execution_safety = _policy_mapping(scheduler_policy, "execution_safety")
    allowed_private_roots, forbidden_public_roots = _private_root_lists(policy)
    required_approvals = sorted(_string_list(scheduler_policy, "approval_gates"))
    provided_approvals = sorted(set(approvals))
    review_log = _build_review_log_reference(
        review_log_path,
        policy=policy,
        project_root=project_root,
        required_approvals=required_approvals,
        provided_approvals=provided_approvals,
        allowed_private_roots=allowed_private_roots,
        forbidden_public_roots=forbidden_public_roots,
    )

    _validate_scheduler_policy(
        scheduler_policy=scheduler_policy,
        trigger=trigger,
        required_approvals=required_approvals,
        provided_approvals=provided_approvals,
        execution_safety=execution_safety,
    )
    _validate_private_output_path(
        trace_out,
        project_root=project_root,
        allowed_private_roots=allowed_private_roots,
        forbidden_public_roots=forbidden_public_roots,
    )
    _validate_private_output_path(
        rescore_out,
        project_root=project_root,
        allowed_private_roots=allowed_private_roots,
        forbidden_public_roots=forbidden_public_roots,
    )

    archive = EvolutionArchive.model_validate_json(
        _resolve_path(archive_path, project_root).read_text(encoding="utf-8")
    )
    source_records = _read_trace_records(source_trace_path, project_root)
    heldout_targets = _load_heldout_targets(heldout_targets_path, project_root)
    candidates = build_heldout_candidate_plans(
        archive,
        source_records,
        heldout_targets,
    )
    resolved_run_id = run_id or f"{archive.run_id}-heldout-schedule"

    return {
        "schema_version": HELDOUT_SCHEDULE_SCHEMA,
        "run_id": resolved_run_id,
        "archive_run_id": archive.run_id,
        "trigger": trigger,
        "ready_to_run": True,
        "policy": {
            "schema_version": policy.get("schema_version"),
            "scheduler_enabled_by_default": scheduler_policy.get(
                "scheduler_enabled_by_default"
            ),
        },
        "approval_gates": {
            "required": required_approvals,
            "provided": provided_approvals,
        },
        "review_log": review_log,
        "retention": {
            "private_trace_max_age_days": retention.get(
                "private_trace_max_age_days"
            ),
            "archive_snapshot_max_age_days": retention.get(
                "archive_snapshot_max_age_days"
            ),
            "review_log_required": retention.get("review_log_required"),
            "delete_expired_private_runs": retention.get(
                "delete_expired_private_runs"
            ),
        },
        "execution_safety": {
            "arbitrary_code_execution": execution_safety.get(
                "arbitrary_code_execution"
            ),
            "external_network_access": execution_safety.get(
                "external_network_access"
            ),
            "publishes_private_trace_outputs": execution_safety.get(
                "publishes_private_trace_outputs"
            ),
            "writes_only_allowed_private_roots": execution_safety.get(
                "writes_only_allowed_private_roots"
            ),
        },
        "inputs": {
            "archive": archive_path.as_posix(),
            "source_trace": source_trace_path.as_posix(),
            "heldout_targets": heldout_targets_path.as_posix(),
        },
        "outputs": {
            "heldout_trace": trace_out.as_posix(),
            "rescore_report": rescore_out.as_posix(),
        },
        "commands": {
            "heldout_batch": _heldout_batch_command(
                archive_path,
                source_trace_path,
                heldout_targets_path,
                trace_out,
                rescore_out,
                resolved_run_id,
            ),
            "rescore_archive": _rescore_archive_command(
                archive_path,
                trace_out,
                rescore_out,
                resolved_run_id,
            ),
        },
        "summary": {
            "archive_elites": len(archive.elites),
            "heldout_targets": len(heldout_targets),
            "scheduled_candidates": len(candidates),
        },
    }


def write_heldout_schedule(
    out: Path,
    *,
    archive_path: Path,
    source_trace_path: Path,
    heldout_targets_path: Path,
    policy: dict[str, Any],
    trace_out: Path,
    rescore_out: Path,
    approvals: list[str],
    review_log_path: Path | None = None,
    trigger: str = DEFAULT_TRIGGER,
    root: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    allowed_private_roots, forbidden_public_roots = _private_root_lists(policy)
    _validate_private_output_path(
        out,
        project_root=project_root,
        allowed_private_roots=allowed_private_roots,
        forbidden_public_roots=forbidden_public_roots,
    )
    schedule = build_heldout_schedule(
        archive_path=archive_path,
        source_trace_path=source_trace_path,
        heldout_targets_path=heldout_targets_path,
        policy=policy,
        trace_out=trace_out,
        rescore_out=rescore_out,
        approvals=approvals,
        review_log_path=review_log_path,
        trigger=trigger,
        root=project_root,
        run_id=run_id,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(schedule, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return schedule


def write_heldout_review_log(
    out: Path,
    *,
    approvals: list[str],
    reviewed_by: str,
    review_id: str,
    reviewed_at: str = "manual-review-recorded",
    policy: dict[str, Any] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    if policy is not None:
        allowed_private_roots, forbidden_public_roots = _private_root_lists(policy)
        _validate_private_output_path(
            out,
            project_root=project_root,
            allowed_private_roots=allowed_private_roots,
            forbidden_public_roots=forbidden_public_roots,
        )
    if not reviewed_by.strip():
        raise ValueError("held-out review log reviewer must be non-empty")
    if not review_id.strip():
        raise ValueError("held-out review log id must be non-empty")
    approved_gates = sorted(set(approvals))
    if not approved_gates:
        raise ValueError("held-out review log must approve at least one gate")

    review_log = {
        "schema_version": HELDOUT_REVIEW_LOG_SCHEMA,
        "review_id": review_id,
        "reviewed_at": reviewed_at,
        "entries": [
            {
                "decision": "approved",
                "gate": gate,
                "reviewer": reviewed_by,
            }
            for gate in approved_gates
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(review_log, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return review_log


def run_heldout_schedule(
    schedule_path: Path,
    *,
    policy: dict[str, Any],
    estimator: EstimatorAdapter,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    schedule = _load_schedule(schedule_path)
    run_config = _validate_schedule_for_run(
        schedule,
        schedule_path=schedule_path,
        policy=policy,
        project_root=project_root,
    )
    archive = EvolutionArchive.model_validate_json(
        run_config["archive_path"].read_text(encoding="utf-8")
    )
    source_records = _read_trace_records(
        Path(run_config["source_trace_path"]),
        project_root,
    )
    heldout_targets = _load_heldout_targets(
        Path(run_config["heldout_targets_path"]),
        project_root,
    )
    candidates = build_heldout_candidate_plans(
        archive,
        source_records,
        heldout_targets,
    )
    expected_candidate_count = schedule["summary"]["scheduled_candidates"]
    if len(candidates) != expected_candidate_count:
        raise ValueError(
            "held-out schedule candidate count drift: "
            f"{len(candidates)} != {expected_candidate_count}"
        )

    heldout_records = _write_heldout_trace(
        candidates,
        trace_out=run_config["trace_out"],
        estimator=estimator,
        run_id=schedule["run_id"],
    )
    rescore_report = write_heldout_rescore(
        archive,
        heldout_records,
        run_config["rescore_out"],
        run_id=f"{schedule['run_id']}-rescore",
    )

    return {
        "schema_version": HELDOUT_SCHEDULE_RUN_SCHEMA,
        "schedule_run_id": schedule["run_id"],
        "archive_run_id": archive.run_id,
        "schedule_path": schedule_path.as_posix(),
        "inputs": schedule["inputs"],
        "outputs": schedule["outputs"],
        "review_log": schedule["review_log"],
        "execution": {
            "arbitrary_code_execution": False,
            "external_network_access": False,
            "shell_commands_executed": False,
        },
        "summary": {
            "scheduled_candidates": expected_candidate_count,
            "heldout_records": len(heldout_records),
            "rescored_elites": rescore_report.summary["rescored_elite_count"],
        },
    }


def validate_heldout_schedule(
    schedule_path: Path,
    *,
    policy: dict[str, Any],
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    schedule = _load_schedule(_resolve_path(schedule_path, project_root))
    run_config = _validate_schedule_for_run(
        schedule,
        schedule_path=schedule_path,
        policy=policy,
        project_root=project_root,
    )
    return {
        "schema_version": schedule["schema_version"],
        "schedule_path": schedule_path.as_posix(),
        "run_id": schedule["run_id"],
        "trigger": schedule["trigger"],
        "ready_to_run": schedule["ready_to_run"],
        "review_log": dict(schedule["review_log"]),
        "inputs": dict(schedule["inputs"]),
        "outputs": dict(schedule["outputs"]),
        "resolved_outputs": {
            "heldout_trace": str(run_config["trace_out"]),
            "rescore_report": str(run_config["rescore_out"]),
        },
        "execution_safety": dict(schedule["execution_safety"]),
    }


def validate_policy_private_path(
    path: Path,
    *,
    policy: dict[str, Any],
    root: Path | None = None,
) -> None:
    project_root = (root or ROOT).resolve()
    allowed_private_roots, forbidden_public_roots = _private_root_lists(policy)
    _validate_private_output_path(
        path,
        project_root=project_root,
        allowed_private_roots=allowed_private_roots,
        forbidden_public_roots=forbidden_public_roots,
    )


def _validate_scheduler_policy(
    *,
    scheduler_policy: dict[str, Any],
    trigger: str,
    required_approvals: list[str],
    provided_approvals: list[str],
    execution_safety: dict[str, Any],
) -> None:
    if scheduler_policy.get("scheduler_enabled_by_default") is not False:
        raise ValueError("held-out scheduler must be disabled by default")
    allowed_triggers = _string_list(scheduler_policy, "allowed_triggers")
    if trigger not in allowed_triggers:
        raise ValueError(f"held-out scheduler trigger is not allowed: {trigger}")
    missing = sorted(set(required_approvals) - set(provided_approvals))
    if missing:
        raise ValueError(f"missing scheduler approval gates: {missing}")
    if execution_safety.get("external_network_access") is not False:
        raise ValueError("held-out scheduler cannot use external networking")
    if execution_safety.get("arbitrary_code_execution") is not False:
        raise ValueError("held-out scheduler cannot execute arbitrary code")
    if execution_safety.get("publishes_private_trace_outputs") is not False:
        raise ValueError("held-out scheduler cannot publish private trace outputs")
    if execution_safety.get("writes_only_allowed_private_roots") is not True:
        raise ValueError("held-out scheduler must write only private roots")


def _validate_private_output_path(
    path: Path,
    *,
    project_root: Path,
    allowed_private_roots: list[str],
    forbidden_public_roots: list[str],
) -> None:
    resolved = _resolve_path(path, project_root)
    for forbidden in forbidden_public_roots:
        if _is_relative_to(resolved, (project_root / forbidden).resolve()):
            raise ValueError(
                "held-out schedule output uses forbidden public root: "
                f"{path}"
            )
    if not any(
        _is_relative_to(resolved, (project_root / allowed).resolve())
        for allowed in allowed_private_roots
    ):
        raise ValueError(
            "held-out schedule output is outside allowed private roots: "
            f"{path}"
        )


def _read_trace_records(path: Path, project_root: Path) -> list[TraceRecord]:
    resolved = _resolve_path(path, project_root)
    records: list[TraceRecord] = []
    for line_number, raw_line in enumerate(
        resolved.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not raw_line.strip():
            continue
        try:
            records.append(TraceRecord.model_validate_json(raw_line))
        except ValidationError as exc:
            raise ValueError(
                f"invalid trace record at {path}:{line_number}: {exc}"
            ) from exc
    return records


def _load_heldout_targets(path: Path, project_root: Path) -> list[TargetSpec]:
    resolved = _resolve_path(path, project_root)
    target_paths = sorted(resolved.glob("*.json")) if resolved.is_dir() else [resolved]
    targets: list[TargetSpec] = []
    for target_path in target_paths:
        raw = target_path.read_text(encoding="utf-8")
        try:
            targets.append(TargetSpec.model_validate_json(raw))
        except ValidationError:
            targets.append(
                TargetSpec.model_validate_json(
                    json.dumps(json.loads(raw).get("target", {}))
                )
            )
    return targets


def _build_review_log_reference(
    review_log_path: Path | None,
    *,
    policy: dict[str, Any],
    project_root: Path,
    required_approvals: list[str],
    provided_approvals: list[str],
    allowed_private_roots: list[str],
    forbidden_public_roots: list[str],
) -> dict[str, Any]:
    retention = _policy_mapping(_scheduler_policy(policy), "retention")
    if retention.get("review_log_required") is True and review_log_path is None:
        raise ValueError("held-out schedule review log required by policy")
    if review_log_path is None:
        return {
            "approval_gates": [],
            "path": None,
            "schema_version": None,
            "sha256": None,
        }

    _validate_private_output_path(
        review_log_path,
        project_root=project_root,
        allowed_private_roots=allowed_private_roots,
        forbidden_public_roots=forbidden_public_roots,
    )
    resolved = _resolve_path(review_log_path, project_root)
    review_log = _load_review_log(resolved)
    approved_gates = _approved_review_log_gates(review_log)
    missing_required = sorted(set(required_approvals) - set(approved_gates))
    missing_provided = sorted(set(provided_approvals) - set(approved_gates))
    if missing_required:
        raise ValueError(
            f"held-out review log lacks required approvals: {missing_required}"
        )
    if missing_provided:
        raise ValueError(
            f"held-out review log lacks provided approvals: {missing_provided}"
        )
    return {
        "approval_gates": approved_gates,
        "path": review_log_path.as_posix(),
        "schema_version": review_log["schema_version"],
        "sha256": _sha256_file(resolved),
    }


def _write_heldout_trace(
    candidates: list[HeldoutCandidatePlan],
    *,
    trace_out: Path,
    estimator: EstimatorAdapter,
    run_id: str,
) -> list[TraceRecord]:
    trace_out.parent.mkdir(parents=True, exist_ok=True)
    trace_out.write_text("", encoding="utf-8")
    writer = JsonlTraceWriter(trace_out)
    evaluator = CascadeEvaluator(estimator=estimator)
    heldout_records: list[TraceRecord] = []
    for candidate in candidates:
        result = evaluator.evaluate_plan(candidate.attack_plan)
        record = _trace_record_from_result(
            candidate,
            result=result,
            run_id=run_id,
        )
        writer.append(record)
        heldout_records.append(record)
    return heldout_records


def _trace_record_from_result(
    candidate: HeldoutCandidatePlan,
    *,
    result: CascadeResult,
    run_id: str,
) -> TraceRecord:
    public_release_ok = (
        candidate.attack_plan.metadata.public and result.validation.valid
    )
    evaluation = dict(result.metrics)
    evaluation["valid"] = result.valid
    if result.estimator_result is not None:
        evaluation["estimator_name"] = result.estimator_result.estimator_name
        evaluation["estimator_version"] = result.estimator_result.estimator_version
    evaluation["warnings"] = result.warnings
    return TraceRecord.from_evaluation(
        run_id=run_id,
        candidate_id=candidate.candidate_id,
        parent_id=candidate.parent_id,
        generation=candidate.generation,
        mutation_summary=candidate.mutation_summary,
        attack_plan=candidate.attack_plan,
        evaluation=evaluation,
        accepted=result.valid,
        public_release_ok=public_release_ok,
        redaction_reason=None if public_release_ok else "invalid or private plan",
    )


def _load_schedule(schedule_path: Path) -> dict[str, Any]:
    payload = json.loads(schedule_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("held-out schedule must be a JSON object")
    return payload


def _validate_schedule_for_run(
    schedule: dict[str, Any],
    *,
    schedule_path: Path,
    policy: dict[str, Any],
    project_root: Path,
) -> dict[str, Path | str]:
    if schedule.get("schema_version") != HELDOUT_SCHEDULE_SCHEMA:
        raise ValueError("held-out schedule schema is unsupported")
    if schedule.get("ready_to_run") is not True:
        raise ValueError("held-out schedule is not ready to run")
    if not isinstance(schedule.get("run_id"), str) or not schedule["run_id"]:
        raise ValueError("held-out schedule run_id must be a non-empty string")
    _validate_schedule_approvals(schedule, policy)
    _validate_schedule_execution_safety(schedule, policy)

    allowed_private_roots, forbidden_public_roots = _private_root_lists(policy)
    _validate_schedule_review_log(
        schedule,
        policy=policy,
        project_root=project_root,
        allowed_private_roots=allowed_private_roots,
        forbidden_public_roots=forbidden_public_roots,
    )
    _validate_private_output_path(
        schedule_path,
        project_root=project_root,
        allowed_private_roots=allowed_private_roots,
        forbidden_public_roots=forbidden_public_roots,
    )
    inputs = _policy_mapping(schedule, "inputs")
    outputs = _policy_mapping(schedule, "outputs")
    archive_path = _resolve_path(_required_path(inputs, "archive"), project_root)
    source_trace_path = _resolve_path(
        _required_path(inputs, "source_trace"),
        project_root,
    )
    heldout_targets_path = _resolve_path(
        _required_path(inputs, "heldout_targets"),
        project_root,
    )
    trace_out = _required_path(outputs, "heldout_trace")
    rescore_out = _required_path(outputs, "rescore_report")
    _validate_private_output_path(
        trace_out,
        project_root=project_root,
        allowed_private_roots=allowed_private_roots,
        forbidden_public_roots=forbidden_public_roots,
    )
    _validate_private_output_path(
        rescore_out,
        project_root=project_root,
        allowed_private_roots=allowed_private_roots,
        forbidden_public_roots=forbidden_public_roots,
    )
    resolved_trace_out = _resolve_path(trace_out, project_root)
    resolved_rescore_out = _resolve_path(rescore_out, project_root)
    _validate_schedule_commands(
        schedule,
        archive_path=Path(inputs["archive"]),
        source_trace_path=Path(inputs["source_trace"]),
        heldout_targets_path=Path(inputs["heldout_targets"]),
        trace_out=trace_out,
        rescore_out=rescore_out,
        run_id=schedule["run_id"],
    )
    summary = _policy_mapping(schedule, "summary")
    if not isinstance(summary.get("scheduled_candidates"), int):
        raise ValueError("held-out schedule summary lacks scheduled_candidates")

    return {
        "archive_path": archive_path,
        "source_trace_path": source_trace_path.as_posix(),
        "heldout_targets_path": heldout_targets_path.as_posix(),
        "trace_out": resolved_trace_out,
        "rescore_out": resolved_rescore_out,
    }


def _validate_schedule_review_log(
    schedule: dict[str, Any],
    *,
    policy: dict[str, Any],
    project_root: Path,
    allowed_private_roots: list[str],
    forbidden_public_roots: list[str],
) -> None:
    retention = _policy_mapping(_scheduler_policy(policy), "retention")
    review_log_reference = _policy_mapping(schedule, "review_log")
    if retention.get("review_log_required") is not True:
        return
    path_value = review_log_reference.get("path")
    if not isinstance(path_value, str) or not path_value:
        raise ValueError("held-out schedule review log required by policy")
    review_log_path = Path(path_value)
    _validate_private_output_path(
        review_log_path,
        project_root=project_root,
        allowed_private_roots=allowed_private_roots,
        forbidden_public_roots=forbidden_public_roots,
    )
    resolved = _resolve_path(review_log_path, project_root)
    current_digest = _sha256_file(resolved)
    if review_log_reference.get("sha256") != current_digest:
        raise ValueError("held-out schedule review log digest drift")
    review_log = _load_review_log(resolved)
    if review_log_reference.get("schema_version") != review_log["schema_version"]:
        raise ValueError("held-out schedule review log schema drift")
    approved_gates = _approved_review_log_gates(review_log)
    if approved_gates != sorted(_string_list(review_log_reference, "approval_gates")):
        raise ValueError("held-out schedule review log approval drift")
    required = sorted(
        _string_list(_policy_mapping(schedule, "approval_gates"), "required")
    )
    missing = sorted(set(required) - set(approved_gates))
    if missing:
        raise ValueError(f"held-out review log lacks required approvals: {missing}")


def _validate_schedule_approvals(
    schedule: dict[str, Any],
    policy: dict[str, Any],
) -> None:
    schedule_approvals = _policy_mapping(schedule, "approval_gates")
    required = sorted(_string_list(schedule_approvals, "required"))
    provided = sorted(_string_list(schedule_approvals, "provided"))
    policy_required = sorted(
        _string_list(_scheduler_policy(policy), "approval_gates")
    )
    if required != policy_required:
        raise ValueError("held-out schedule approval gates drift from policy")
    missing = sorted(set(required) - set(provided))
    if missing:
        raise ValueError(f"held-out schedule is missing approvals: {missing}")


def _validate_schedule_execution_safety(
    schedule: dict[str, Any],
    policy: dict[str, Any],
) -> None:
    schedule_safety = _policy_mapping(schedule, "execution_safety")
    policy_safety = _policy_mapping(_scheduler_policy(policy), "execution_safety")
    if schedule_safety != policy_safety:
        raise ValueError("held-out schedule execution safety drift from policy")
    if schedule_safety.get("external_network_access") is not False:
        raise ValueError("held-out schedule cannot use external networking")
    if schedule_safety.get("arbitrary_code_execution") is not False:
        raise ValueError("held-out schedule cannot execute arbitrary code")
    if schedule_safety.get("publishes_private_trace_outputs") is not False:
        raise ValueError("held-out schedule cannot publish private trace outputs")


def _validate_schedule_commands(
    schedule: dict[str, Any],
    *,
    archive_path: Path,
    source_trace_path: Path,
    heldout_targets_path: Path,
    trace_out: Path,
    rescore_out: Path,
    run_id: str,
) -> None:
    commands = _policy_mapping(schedule, "commands")
    expected_heldout = _heldout_batch_command(
        archive_path,
        source_trace_path,
        heldout_targets_path,
        trace_out,
        rescore_out,
        run_id,
    )
    expected_rescore = _rescore_archive_command(
        archive_path,
        trace_out,
        rescore_out,
        run_id,
    )
    if commands.get("heldout_batch") != expected_heldout:
        raise ValueError("held-out batch command does not match structured inputs")
    if commands.get("rescore_archive") != expected_rescore:
        raise ValueError("held-out rescore command does not match structured inputs")


def _required_path(payload: dict[str, Any], key: str) -> Path:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"held-out schedule field {key} must be a path string")
    return Path(value)


def _load_review_log(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("held-out review log must be a JSON object")
    if payload.get("schema_version") != HELDOUT_REVIEW_LOG_SCHEMA:
        raise ValueError("held-out review log schema is unsupported")
    if not isinstance(payload.get("review_id"), str) or not payload["review_id"]:
        raise ValueError("held-out review log id must be a non-empty string")
    if not isinstance(payload.get("entries"), list):
        raise ValueError("held-out review log entries must be a list")
    return payload


def _approved_review_log_gates(review_log: dict[str, Any]) -> list[str]:
    gates: list[str] = []
    for entry in review_log["entries"]:
        if not isinstance(entry, dict):
            raise ValueError("held-out review log entry must be an object")
        gate = entry.get("gate")
        reviewer = entry.get("reviewer")
        if not isinstance(gate, str) or not gate:
            raise ValueError("held-out review log entry gate must be non-empty")
        if not isinstance(reviewer, str) or not reviewer:
            raise ValueError("held-out review log entry reviewer must be non-empty")
        if entry.get("decision") == "approved":
            gates.append(gate)
    return sorted(set(gates))


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _heldout_batch_command(
    archive_path: Path,
    source_trace_path: Path,
    heldout_targets_path: Path,
    trace_out: Path,
    rescore_out: Path,
    run_id: str,
) -> str:
    return (
        "agades-pqc heldout-batch "
        f"{archive_path.as_posix()} {source_trace_path.as_posix()} "
        f"{heldout_targets_path.as_posix()} --trace-out {trace_out.as_posix()} "
        f"--rescore-out {rescore_out.as_posix()} --run-id {run_id}"
    )


def _rescore_archive_command(
    archive_path: Path,
    trace_out: Path,
    rescore_out: Path,
    run_id: str,
) -> str:
    return (
        "agades-pqc rescore-archive "
        f"{archive_path.as_posix()} {trace_out.as_posix()} "
        f"--out {rescore_out.as_posix()} --run-id {run_id}-rescore"
    )


def _scheduler_policy(policy: dict[str, Any]) -> dict[str, Any]:
    return _policy_mapping(policy, "scheduler_policy")


def _private_root_lists(policy: dict[str, Any]) -> tuple[list[str], list[str]]:
    return (
        _string_list(policy, "allowed_private_roots"),
        _string_list(policy, "forbidden_public_roots"),
    )


def _policy_mapping(policy: dict[str, Any], key: str) -> dict[str, Any]:
    value = policy.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"private run policy field {key} must be an object")
    return value


def _string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise ValueError(f"private run policy field {key} must be a string list")
    return list(value)


def _resolve_path(path: Path, project_root: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (project_root / path).resolve()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
