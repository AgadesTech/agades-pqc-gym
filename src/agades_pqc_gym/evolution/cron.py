from __future__ import annotations

import json
from pathlib import Path
from shlex import quote
from typing import Any

from agades_pqc_gym.evolution.scheduler import (
    validate_heldout_schedule,
    validate_policy_private_path,
)

HELDOUT_CRON_PLAN_SCHEMA = "agades.pqc.heldout_cron_plan.v1"
CRON_TRIGGER = "local_cron_after_review"
DEFAULT_CRON_LOG = Path("private/runs/heldout_cron.log")


def build_heldout_cron_plan(
    *,
    schedule_path: Path,
    policy: dict[str, Any],
    policy_path: Path,
    minute: int,
    every_hours: int,
    log_path: Path = DEFAULT_CRON_LOG,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or Path.cwd()).resolve()
    _validate_cron_interval(minute=minute, every_hours=every_hours)
    validate_policy_private_path(log_path, policy=policy, root=project_root)

    schedule = validate_heldout_schedule(
        schedule_path,
        policy=policy,
        root=project_root,
    )
    if schedule["trigger"] != CRON_TRIGGER:
        raise ValueError(
            "held-out cron plan requires schedule trigger "
            f"{CRON_TRIGGER}: {schedule['trigger']}"
        )

    expression = f"{minute} */{every_hours} * * *"
    argv = [
        "agades-pqc",
        "heldout-run-schedule",
        schedule_path.as_posix(),
        "--policy",
        policy_path.as_posix(),
    ]
    crontab_entry = _crontab_entry(
        expression=expression,
        project_root=project_root,
        argv=argv,
        log_path=log_path,
    )
    execution_safety = schedule["execution_safety"]
    return {
        "schema_version": HELDOUT_CRON_PLAN_SCHEMA,
        "schedule": {
            "path": schedule_path.as_posix(),
            "run_id": schedule["run_id"],
            "trigger": schedule["trigger"],
            "ready_to_run": schedule["ready_to_run"],
            "review_log_path": schedule["review_log"]["path"],
            "outputs": schedule["outputs"],
        },
        "cron": {
            "expression": expression,
            "minute": minute,
            "every_hours": every_hours,
            "timezone": "local",
        },
        "command": {
            "argv": argv,
            "working_directory": project_root.as_posix(),
            "log_path": log_path.as_posix(),
            "crontab_entry": crontab_entry,
        },
        "installation": {
            "writes_system_crontab": False,
            "requires_manual_install": True,
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
        },
    }


def write_heldout_cron_plan(
    out: Path,
    *,
    schedule_path: Path,
    policy: dict[str, Any],
    policy_path: Path,
    minute: int,
    every_hours: int,
    log_path: Path = DEFAULT_CRON_LOG,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or Path.cwd()).resolve()
    validate_policy_private_path(out, policy=policy, root=project_root)
    plan = build_heldout_cron_plan(
        schedule_path=schedule_path,
        policy=policy,
        policy_path=policy_path,
        minute=minute,
        every_hours=every_hours,
        log_path=log_path,
        root=project_root,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return plan


def _validate_cron_interval(*, minute: int, every_hours: int) -> None:
    if minute < 0 or minute > 59:
        raise ValueError("held-out cron minute must be between 0 and 59")
    if every_hours < 1 or every_hours > 24:
        raise ValueError("held-out cron hour interval must be between 1 and 24")


def _crontab_entry(
    *,
    expression: str,
    project_root: Path,
    argv: list[str],
    log_path: Path,
) -> str:
    command = " ".join(quote(part) for part in argv)
    return (
        f"{expression} cd {quote(project_root.as_posix())} && "
        f"{command} >> {quote(log_path.as_posix())} 2>&1"
    )
