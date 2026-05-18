from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.target import TargetSpec
from agades_pqc_gym.evolution.mutation import build_candidate_mutation_batch
from agades_pqc_gym.evolution.scheduler import (
    HELDOUT_REVIEW_LOG_SCHEMA,
    validate_policy_private_path,
)

PRIVATE_EVOLUTION_CAMPAIGN_PLAN_SCHEMA = (
    "agades.pqc.private_evolution_campaign_plan.v1"
)
PRIVATE_EVOLUTION_CAMPAIGN_PLAN_VERIFICATION_SCHEMA = (
    "agades.pqc.private_evolution_campaign_plan_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY_PATH = Path("docs/private_run_policy.json")
REQUIRED_STEP_COMMANDS = {
    "seed-mutation": "agades-pqc mutate-candidates",
    "seed-evaluation": "agades-pqc evolve-batch",
    "archive-mutation": "agades-pqc mutate-archive",
    "archive-snapshot": "agades-pqc archive-snapshot",
    "heldout-schedule": "agades-pqc heldout-schedule",
    "heldout-run": "agades-pqc heldout-run-schedule",
    "heldout-review-packet": "agades-pqc heldout-review-packet",
}
REQUIRED_STEP_IDS = list(REQUIRED_STEP_COMMANDS)


def build_private_evolution_campaign_plan(
    *,
    seed_candidates_path: Path,
    heldout_targets_path: Path,
    policy: dict[str, Any],
    review_log_path: Path,
    out: Path | None = None,
    root: Path | None = None,
    run_id: str = "manual-private-evolution",
    policy_path: Path = DEFAULT_POLICY_PATH,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    if out is not None:
        validate_policy_private_path(out, policy=policy, root=project_root)
    validate_policy_private_path(
        review_log_path,
        policy=policy,
        root=project_root,
    )

    outputs = _default_outputs(run_id)
    for path in outputs.values():
        validate_policy_private_path(Path(path), policy=policy, root=project_root)

    seed_plans = _load_attack_plans(seed_candidates_path, project_root=project_root)
    seed_reference = _attack_plan_input_reference(
        seed_candidates_path,
        plans=seed_plans,
        project_root=project_root,
    )
    seed_mutation_preflight = _seed_mutation_preflight(
        seed_plans,
        run_id=f"{run_id}-seed-mutations",
    )
    heldout_targets = _load_heldout_targets(
        heldout_targets_path,
        project_root=project_root,
    )
    heldout_reference = _heldout_target_input_reference(
        heldout_targets_path,
        targets=heldout_targets,
        project_root=project_root,
    )
    target_compatibility_preflight = _target_compatibility_preflight(
        seed_plans,
        heldout_targets,
    )
    review_log = _review_log_reference(
        review_log_path,
        policy=policy,
        project_root=project_root,
    )
    steps = _campaign_steps(
        seed_candidates_path=seed_candidates_path,
        heldout_targets_path=heldout_targets_path,
        review_log_path=review_log_path,
        outputs=outputs,
        run_id=run_id,
        policy_path=policy_path,
    )
    _validate_steps_against_policy(steps, policy)

    plan = {
        "schema_version": PRIVATE_EVOLUTION_CAMPAIGN_PLAN_SCHEMA,
        "run_id": run_id,
        "plan": {
            "path": _display_path(out, project_root) if out is not None else None,
            "private": True,
            "requires_manual_invocation": True,
        },
        "review_log": review_log,
        "inputs": {
            "seed_candidates": seed_reference,
            "heldout_targets": heldout_reference,
        },
        "seed_mutation_preflight": seed_mutation_preflight,
        "target_compatibility_preflight": target_compatibility_preflight,
        "outputs": outputs,
        "steps": steps,
        "safety": _safety(),
        "summary": {
            "compatible_target_family_count": len(
                target_compatibility_preflight["compatible_target_families"]
            ),
            "heldout_target_count": heldout_reference["json_count"],
            "seed_family_coverage_complete": target_compatibility_preflight[
                "coverage_complete"
            ],
            "seed_mutation_candidate_count": seed_mutation_preflight[
                "candidate_count"
            ],
            "seed_plan_count": seed_reference["json_count"],
            "step_count": len(steps),
        },
    }
    _validate_plan_shape(plan, policy=policy, root=project_root)
    return plan


def write_private_evolution_campaign_plan(
    out: Path,
    *,
    seed_candidates_path: Path,
    heldout_targets_path: Path,
    policy: dict[str, Any],
    review_log_path: Path,
    root: Path | None = None,
    run_id: str = "manual-private-evolution",
    policy_path: Path = DEFAULT_POLICY_PATH,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    plan = build_private_evolution_campaign_plan(
        seed_candidates_path=seed_candidates_path,
        heldout_targets_path=heldout_targets_path,
        policy=policy,
        review_log_path=review_log_path,
        out=out,
        root=project_root,
        run_id=run_id,
        policy_path=policy_path,
    )
    resolved_out = _resolve_path(out, project_root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return plan


def verify_private_evolution_campaign_plan(
    plan_path: Path,
    *,
    policy: dict[str, Any],
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    try:
        validate_policy_private_path(plan_path, policy=policy, root=project_root)
    except ValueError as exc:
        failures.append(f"private evolution campaign plan path must be private: {exc}")

    plan = _read_plan(_resolve_path(plan_path, project_root), failures)
    if plan:
        _verify_plan(plan, policy=policy, root=project_root, failures=failures)

    summary = _summary(plan, failures)
    return {
        "schema_version": PRIVATE_EVOLUTION_CAMPAIGN_PLAN_VERIFICATION_SCHEMA,
        "plan_path": plan_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _default_outputs(run_id: str) -> dict[str, str]:
    base_run = f"private/runs/{run_id}"
    base_trace = f"private/traces/{run_id}"
    base_report = f"private/reports/{run_id}"
    base_candidates = f"private/candidates/{run_id}"
    return {
        "archive_mutation_dir": f"{base_candidates}/archive_mutations",
        "archive_snapshot": f"{base_run}/archive_snapshot.json",
        "heldout_rescore": f"{base_report}/heldout_rescore.json",
        "heldout_review_packet": f"{base_report}/heldout_review_packet.json",
        "heldout_schedule": f"{base_run}/heldout_schedule.json",
        "heldout_trace": f"{base_trace}/heldout_trace.jsonl",
        "seed_archive": f"{base_run}/evolution_archive.json",
        "seed_mutation_dir": f"{base_candidates}/seed_mutations",
        "seed_trace": f"{base_trace}/evolution_trace.jsonl",
    }


def _campaign_steps(
    *,
    seed_candidates_path: Path,
    heldout_targets_path: Path,
    review_log_path: Path,
    outputs: dict[str, str],
    run_id: str,
    policy_path: Path,
) -> list[dict[str, Any]]:
    seed_mutation_plans = f"{outputs['seed_mutation_dir']}/plans"
    return [
        _step(
            "seed-mutation",
            [
                "agades-pqc",
                "mutate-candidates",
                seed_candidates_path.as_posix(),
                "--out",
                outputs["seed_mutation_dir"],
                "--run-id",
                f"{run_id}-seed-mutations",
            ],
            outputs=["seed_mutation_dir"],
        ),
        _step(
            "seed-evaluation",
            [
                "agades-pqc",
                "evolve-batch",
                seed_mutation_plans,
                "--trace-out",
                outputs["seed_trace"],
                "--archive-out",
                outputs["seed_archive"],
                "--run-id",
                run_id,
            ],
            outputs=["seed_trace", "seed_archive"],
        ),
        _step(
            "archive-mutation",
            [
                "agades-pqc",
                "mutate-archive",
                outputs["seed_archive"],
                outputs["seed_trace"],
                "--out",
                outputs["archive_mutation_dir"],
                "--run-id",
                f"{run_id}-archive-mutations",
            ],
            outputs=["archive_mutation_dir"],
        ),
        _step(
            "archive-snapshot",
            [
                "agades-pqc",
                "archive-snapshot",
                outputs["seed_archive"],
                outputs["seed_trace"],
                "--out",
                outputs["archive_snapshot"],
                "--review-log",
                review_log_path.as_posix(),
                "--policy",
                policy_path.as_posix(),
                "--run-id",
                f"{run_id}-snapshot",
            ],
            outputs=["archive_snapshot"],
        ),
        _step(
            "heldout-schedule",
            [
                "agades-pqc",
                "heldout-schedule",
                outputs["seed_archive"],
                outputs["seed_trace"],
                heldout_targets_path.as_posix(),
                "--out",
                outputs["heldout_schedule"],
                "--trace-out",
                outputs["heldout_trace"],
                "--rescore-out",
                outputs["heldout_rescore"],
                "--review-log",
                review_log_path.as_posix(),
                "--policy",
                policy_path.as_posix(),
                "--trigger",
                "manual_reviewed",
                "--approval",
                "private-run-policy-review",
                "--approval",
                "heldout-target-review",
                "--approval",
                "retention-owner-review",
                "--approval",
                "publication-export-review",
                "--run-id",
                f"{run_id}-heldout-schedule",
            ],
            outputs=["heldout_schedule"],
        ),
        _step(
            "heldout-run",
            [
                "agades-pqc",
                "heldout-run-schedule",
                outputs["heldout_schedule"],
                "--policy",
                policy_path.as_posix(),
            ],
            outputs=["heldout_trace", "heldout_rescore"],
        ),
        _step(
            "heldout-review-packet",
            [
                "agades-pqc",
                "heldout-review-packet",
                outputs["heldout_schedule"],
                "--out",
                outputs["heldout_review_packet"],
                "--policy",
                policy_path.as_posix(),
                "--reviewer-label",
                "pending-expert-review",
            ],
            outputs=["heldout_review_packet"],
        ),
    ]


def _step(
    step_id: str,
    argv: list[str],
    *,
    outputs: list[str],
) -> dict[str, Any]:
    return {
        "id": step_id,
        "command": {
            "argv": argv,
            "policy_command": _policy_command_for_argv(argv),
        },
        "execution_status": "not_executed",
        "outputs": outputs,
    }


def _attack_plan_input_reference(
    path: Path,
    *,
    plans: list[AttackPlan],
    project_root: Path,
) -> dict[str, Any]:
    files = _json_files(path, project_root)
    if len(files) != len(plans):
        raise ValueError("private evolution campaign seed plan count drifted")
    return _input_reference(path, files, project_root=project_root)


def _load_attack_plans(path: Path, *, project_root: Path) -> list[AttackPlan]:
    plans: list[AttackPlan] = []
    for file_path in _json_files(path, project_root):
        try:
            plans.append(
                AttackPlan.model_validate_json(
                    file_path.read_text(encoding="utf-8")
                )
            )
        except ValidationError as exc:
            raise ValueError(
                f"private evolution campaign seed is not an AttackPlan: {file_path}"
            ) from exc
    return plans


def _seed_mutation_preflight(
    plans: list[AttackPlan],
    *,
    run_id: str,
    generation: int = 1,
    max_mutations_per_plan: int = 4,
) -> dict[str, Any]:
    batch = build_candidate_mutation_batch(
        plans,
        run_id=run_id,
        generation=generation,
        max_mutations_per_plan=max_mutations_per_plan,
    )
    if batch.summary["candidate_count"] < 1:
        reasons = sorted({skipped.reason for skipped in batch.skipped})
        raise ValueError(
            "private evolution campaign has no reviewed seed mutations: "
            f"{reasons}"
        )
    return {
        "candidate_count": batch.summary["candidate_count"],
        "generation": generation,
        "max_mutations_per_plan": max_mutations_per_plan,
        "skipped_count": batch.summary["skipped_count"],
        "skipped_reasons": sorted({skipped.reason for skipped in batch.skipped}),
        "source_count": batch.summary["source_count"],
        "target_families": sorted({plan.target.family.value for plan in plans}),
    }


def _heldout_target_input_reference(
    path: Path,
    *,
    targets: list[TargetSpec],
    project_root: Path,
) -> dict[str, Any]:
    files = _json_files(path, project_root)
    if len(files) != len(targets):
        raise ValueError("private evolution campaign held-out target count drifted")
    return _input_reference(path, files, project_root=project_root)


def _load_heldout_targets(path: Path, *, project_root: Path) -> list[TargetSpec]:
    targets: list[TargetSpec] = []
    files = _json_files(path, project_root)
    for file_path in files:
        targets.append(_load_heldout_target(file_path))
    return targets


def _load_heldout_target(file_path: Path) -> TargetSpec:
    raw = file_path.read_text(encoding="utf-8")
    try:
        return TargetSpec.model_validate_json(raw)
    except ValidationError:
        try:
            return TargetSpec.model_validate_json(json.dumps(json.loads(raw)["target"]))
        except (KeyError, TypeError, ValidationError) as exc:
            raise ValueError(
                "private evolution campaign held-out input is not a "
                f"TargetSpec or benchmark target: {file_path}"
            ) from exc


def _target_compatibility_preflight(
    seed_plans: list[AttackPlan],
    heldout_targets: list[TargetSpec],
) -> dict[str, Any]:
    seed_families = sorted({plan.target.family.value for plan in seed_plans})
    heldout_families = sorted({target.family.value for target in heldout_targets})
    compatible_families = sorted(set(seed_families) & set(heldout_families))
    uncovered_seed_families = sorted(set(seed_families) - set(heldout_families))
    if not compatible_families:
        raise ValueError(
            "private evolution campaign has no compatible held-out target "
            f"families: seed={seed_families}, heldout={heldout_families}"
        )
    if uncovered_seed_families:
        raise ValueError(
            "private evolution campaign is missing held-out coverage for seed "
            f"families: {uncovered_seed_families}"
        )
    return {
        "compatible_target_families": compatible_families,
        "coverage_complete": True,
        "heldout_target_count": len(heldout_targets),
        "heldout_target_families": heldout_families,
        "seed_plan_count": len(seed_plans),
        "seed_target_families": seed_families,
        "uncovered_seed_target_families": uncovered_seed_families,
    }


def _input_reference(
    path: Path,
    files: list[Path],
    *,
    project_root: Path,
) -> dict[str, Any]:
    return {
        "path": _display_path(path, project_root),
        "json_count": len(files),
        "sha256": _input_digest(files, project_root=project_root),
    }


def _review_log_reference(
    path: Path,
    *,
    policy: dict[str, Any],
    project_root: Path,
) -> dict[str, Any]:
    resolved = _resolve_path(path, project_root)
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("private evolution campaign review log must be an object")
    if payload.get("schema_version") != HELDOUT_REVIEW_LOG_SCHEMA:
        raise ValueError(
            "private evolution campaign requires held-out review log schema "
            f"{HELDOUT_REVIEW_LOG_SCHEMA}"
        )
    approvals = _approved_review_log_gates(payload)
    required = _required_approval_gates(policy)
    missing = sorted(set(required) - set(approvals))
    if missing:
        raise ValueError(
            "private evolution campaign review log lacks required approvals: "
            f"{missing}"
        )
    return {
        "path": _display_path(path, project_root),
        "schema_version": payload["schema_version"],
        "approval_gates": approvals,
        "sha256": _sha256_file(resolved),
    }


def _verify_plan(
    plan: dict[str, Any],
    *,
    policy: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    if plan.get("schema_version") != PRIVATE_EVOLUTION_CAMPAIGN_PLAN_SCHEMA:
        failures.append(
            "Private evolution campaign plan schema_version must be "
            f"{PRIVATE_EVOLUTION_CAMPAIGN_PLAN_SCHEMA}."
        )
    _validate_plan_shape(plan, policy=policy, root=root, failures=failures)
    _verify_seed_mutation_preflight(plan, root=root, failures=failures)
    _verify_target_compatibility_preflight(plan, root=root, failures=failures)
    review_log = _dict_or_empty(plan.get("review_log"))
    review_log_path = review_log.get("path")
    if isinstance(review_log_path, str):
        try:
            current = _review_log_reference(
                Path(review_log_path),
                policy=policy,
                project_root=root,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            failures.append(f"Private evolution campaign review log invalid: {exc}")
        else:
            if review_log != current:
                failures.append(
                    "Private evolution campaign review log reference drifted."
                )
    else:
        failures.append("Private evolution campaign review log path is missing.")


def _verify_seed_mutation_preflight(
    plan: dict[str, Any],
    *,
    root: Path,
    failures: list[str],
) -> None:
    inputs = _dict_or_empty(plan.get("inputs"))
    seed_candidates = _dict_or_empty(inputs.get("seed_candidates"))
    seed_path = seed_candidates.get("path")
    run_id = plan.get("run_id")
    if not isinstance(seed_path, str) or not isinstance(run_id, str):
        failures.append("Private evolution campaign seed preflight inputs are missing.")
        return
    try:
        expected = _seed_mutation_preflight(
            _load_attack_plans(Path(seed_path), project_root=root),
            run_id=f"{run_id}-seed-mutations",
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"Private evolution campaign seed preflight invalid: {exc}")
        return
    if plan.get("seed_mutation_preflight") != expected:
        failures.append("Private evolution campaign seed mutation preflight drifted.")
    summary = _dict_or_empty(plan.get("summary"))
    if summary.get("seed_mutation_candidate_count") != expected["candidate_count"]:
        failures.append(
            "Private evolution campaign seed mutation summary drifted."
        )


def _verify_target_compatibility_preflight(
    plan: dict[str, Any],
    *,
    root: Path,
    failures: list[str],
) -> None:
    inputs = _dict_or_empty(plan.get("inputs"))
    seed_candidates = _dict_or_empty(inputs.get("seed_candidates"))
    heldout_targets = _dict_or_empty(inputs.get("heldout_targets"))
    seed_path = seed_candidates.get("path")
    heldout_path = heldout_targets.get("path")
    if not isinstance(seed_path, str) or not isinstance(heldout_path, str):
        failures.append(
            "Private evolution campaign target compatibility inputs are missing."
        )
        return
    try:
        expected = _target_compatibility_preflight(
            _load_attack_plans(Path(seed_path), project_root=root),
            _load_heldout_targets(Path(heldout_path), project_root=root),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(
            f"Private evolution campaign target compatibility invalid: {exc}"
        )
        return
    if plan.get("target_compatibility_preflight") != expected:
        failures.append(
            "Private evolution campaign target compatibility preflight drifted."
        )
    summary = _dict_or_empty(plan.get("summary"))
    if (
        summary.get("compatible_target_family_count")
        != len(expected["compatible_target_families"])
    ):
        failures.append(
            "Private evolution campaign target compatibility summary drifted."
        )
    if summary.get("seed_family_coverage_complete") != expected["coverage_complete"]:
        failures.append(
            "Private evolution campaign target coverage summary drifted."
        )


def _validate_plan_shape(
    plan: dict[str, Any],
    *,
    policy: dict[str, Any],
    root: Path,
    failures: list[str] | None = None,
) -> None:
    errors: list[str] = []
    plan_meta = _dict_or_empty(plan.get("plan"))
    if plan_meta.get("private") is not True:
        errors.append("Private evolution campaign plan must be private.")
    if plan_meta.get("requires_manual_invocation") is not True:
        errors.append(
            "Private evolution campaign plan must require manual invocation."
        )
    safety = _dict_or_empty(plan.get("safety"))
    if safety != _safety():
        errors.append("Private evolution campaign safety metadata drifted.")

    outputs = _dict_or_empty(plan.get("outputs"))
    for key, value in sorted(outputs.items()):
        if not isinstance(value, str):
            errors.append(f"Private evolution campaign output path is invalid: {key}.")
            continue
        try:
            validate_policy_private_path(Path(value), policy=policy, root=root)
        except ValueError as exc:
            errors.append(
                "Private evolution campaign output uses forbidden public root "
                f"or non-private path for {key}: {exc}"
            )

    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("Private evolution campaign steps must be a non-empty list.")
    else:
        errors.extend(_validate_steps_against_policy(steps, policy))

    if failures is not None:
        failures.extend(errors)
        return
    if errors:
        raise ValueError("; ".join(errors))


def _validate_steps_against_policy(
    steps: list[Any],
    policy: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    allowed = set(_string_list(policy, "allowed_private_commands"))
    step_ids = [
        step.get("id") if isinstance(step, dict) else None
        for step in steps
    ]
    if step_ids != REQUIRED_STEP_IDS:
        errors.append("Private evolution campaign step order drifted.")
    for step in steps:
        if not isinstance(step, dict):
            errors.append("Private evolution campaign step must be an object.")
            continue
        step_id = step.get("id")
        if step.get("execution_status") != "not_executed":
            errors.append(
                f"Private evolution campaign step executed unexpectedly: "
                f"{step_id}."
            )
        command = _dict_or_empty(step.get("command"))
        argv = command.get("argv")
        if not isinstance(argv, list) or not all(isinstance(arg, str) for arg in argv):
            errors.append(
                f"Private evolution campaign step command argv is invalid: "
                f"{step_id}."
            )
            continue
        policy_command = _policy_command_for_argv(argv)
        if command.get("policy_command") != policy_command:
            errors.append(
                f"Private evolution campaign step policy command drifted: "
                f"{step_id}."
            )
        expected_command = REQUIRED_STEP_COMMANDS.get(str(step_id))
        if expected_command is not None and policy_command != expected_command:
            errors.append(
                f"Private evolution campaign step command role drifted: "
                f"{step_id}."
            )
        if policy_command not in allowed:
            errors.append(
                f"Private evolution campaign command not allowed by policy: "
                f"{policy_command}."
            )
    return errors


def _safety() -> dict[str, Any]:
    return {
        "arbitrary_code_execution": False,
        "contains_attack_plans": False,
        "contains_candidate_sources": False,
        "external_network_access": False,
        "private_plan": True,
        "public_release_ok": False,
        "publishes_private_trace_outputs": False,
        "requires_review_log": True,
        "security_claim": False,
        "shell_commands_executed": False,
        "writes_only_allowed_private_roots": True,
    }


def _read_plan(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(
            f"Private evolution campaign plan is missing: {path.as_posix()}."
        )
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            "Private evolution campaign plan is invalid JSON at line "
            f"{exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("Private evolution campaign plan must be a JSON object.")
        return {}
    return payload


def _summary(plan: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    summary = _dict_or_empty(plan.get("summary"))
    safety = _dict_or_empty(plan.get("safety"))
    return {
        "compatible_target_family_count": summary.get(
            "compatible_target_family_count"
        ),
        "failure_count": len(failures),
        "heldout_target_count": summary.get("heldout_target_count"),
        "private_plan": safety.get("private_plan"),
        "seed_family_coverage_complete": summary.get(
            "seed_family_coverage_complete"
        ),
        "seed_mutation_candidate_count": summary.get(
            "seed_mutation_candidate_count"
        ),
        "seed_plan_count": summary.get("seed_plan_count"),
        "step_count": summary.get("step_count"),
    }


def _json_files(path: Path, project_root: Path) -> list[Path]:
    resolved = _resolve_existing_input(path, project_root)
    if resolved.is_dir():
        files = sorted(file for file in resolved.glob("*.json") if file.is_file())
    elif resolved.is_file():
        files = [resolved]
    else:
        files = []
    if not files:
        raise ValueError(f"private evolution campaign input has no JSON files: {path}")
    return files


def _resolve_existing_input(path: Path, project_root: Path) -> Path:
    if path.is_absolute():
        return path
    for base in (project_root, ROOT, Path.cwd()):
        candidate = (base / path).resolve()
        if candidate.exists():
            return candidate
    return (project_root / path).resolve()


def _input_digest(files: list[Path], *, project_root: Path) -> str:
    if len(files) == 1:
        return _sha256_file(files[0])
    digest_rows = [
        f"{_display_path(path, project_root)} {_sha256_file(path)}"
        for path in files
    ]
    return sha256(("\n".join(digest_rows) + "\n").encode("utf-8")).hexdigest()


def _approved_review_log_gates(review_log: dict[str, Any]) -> list[str]:
    entries = review_log.get("entries")
    if not isinstance(entries, list):
        raise ValueError("private evolution campaign review log entries invalid")
    return sorted(
        str(entry["gate"])
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("decision") == "approved"
        and isinstance(entry.get("gate"), str)
    )


def _required_approval_gates(policy: dict[str, Any]) -> list[str]:
    scheduler = _dict_or_empty(policy.get("scheduler_policy"))
    return sorted(_string_list(scheduler, "approval_gates"))


def _policy_command_for_argv(argv: list[str]) -> str:
    if len(argv) < 2:
        return " ".join(argv)
    return f"{argv[0]} {argv[1]}"


def _string_list(mapping: dict[str, Any], key: str) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _display_path(path: Path | None, root: Path) -> str | None:
    if path is None:
        return None
    resolved = _resolve_path(path, root)
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()
