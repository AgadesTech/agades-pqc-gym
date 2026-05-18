from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agades_pqc_gym.evaluators.lattice_estimator import LATTICE_ESTIMATOR_PINNED_COMMIT
from agades_pqc_gym.evaluators.lattice_estimator_checkout import (
    LATTICE_ESTIMATOR_REPOSITORY,
)
from agades_pqc_gym.evolution.scheduler import validate_policy_private_path
from agades_pqc_gym.utils.commands import format_command, parse_command

LATTICE_ESTIMATOR_RUNTIME_PREFLIGHT_SCHEMA = (
    "agades.pqc.lattice_estimator_runtime_preflight.v1"
)
LATTICE_ESTIMATOR_RUNTIME_PREFLIGHT_VERIFICATION_SCHEMA = (
    "agades.pqc.lattice_estimator_runtime_preflight_verification.v1"
)
DEFAULT_RUNTIME_PREFLIGHT_PATH = Path(
    "private/reports/lattice_estimator_runtime_preflight.json"
)
SAGE_PYTHON_PROBE = "import sage.all"
_EXPECTED_FALSE_SAFETY_FLAGS = (
    "imports_upstream_python",
    "executes_estimator",
    "external_network_access",
    "numeric_reference_outputs_committed",
    "publication_allowed",
    "security_claim",
)


@dataclass(frozen=True)
class _ProbeResult:
    command_found: bool
    returncode: int | None
    output: str
    timed_out: bool = False


def build_lattice_estimator_runtime_preflight(
    *,
    sage_command: str = "sage",
    sage_python_command: str | None = None,
    report_path: Path | None = None,
    timeout_seconds: int = 15,
) -> dict[str, Any]:
    failures: list[str] = []
    sage_found = False
    sage_version: str | None = None
    sage_python_imports_sage = False
    sage_command_parts = parse_command(sage_command, label="sage_command")
    sage_python_command_parts = (
        parse_command(sage_python_command, label="sage_python_command")
        if sage_python_command is not None
        else [*sage_command_parts, "-python"]
    )
    sage_python_command_display = format_command(sage_python_command_parts)

    version_probe = _run_probe(
        [*sage_command_parts, "--version"],
        timeout_seconds=timeout_seconds,
    )
    if not version_probe.command_found:
        failures.append(f"Sage executable not found: {sage_command}.")
    elif version_probe.timed_out:
        sage_found = True
        failures.append(
            f"Sage version probe timed out after {timeout_seconds} seconds."
        )
    elif version_probe.returncode != 0:
        sage_found = True
        failures.append(
            "Sage version probe failed with exit code "
            f"{version_probe.returncode}: {_output_summary(version_probe.output)}"
        )
    else:
        sage_found = True
        sage_version = _first_line(version_probe.output)
        python_probe = _run_probe(
            [
                *sage_python_command_parts,
                "-c",
                f"{SAGE_PYTHON_PROBE}; print('sage-python-ok')",
            ],
            timeout_seconds=timeout_seconds,
        )
        if not python_probe.command_found:
            failures.append(
                f"Sage Python command not found: {sage_python_command_display}."
            )
        elif python_probe.timed_out:
            failures.append(
                f"Sage Python probe timed out after {timeout_seconds} seconds."
            )
        elif python_probe.returncode != 0:
            failures.append(
                "Sage Python probe failed with exit code "
                f"{python_probe.returncode}: {_output_summary(python_probe.output)}"
            )
        else:
            sage_python_imports_sage = True

    return {
        "schema_version": LATTICE_ESTIMATOR_RUNTIME_PREFLIGHT_SCHEMA,
        "created_at": "manual-runtime-preflight-recorded",
        "report": {
            "path": (report_path or DEFAULT_RUNTIME_PREFLIGHT_PATH).as_posix(),
            "private": True,
        },
        "upstream": {
            "repository": LATTICE_ESTIMATOR_REPOSITORY,
            "pinned_commit": LATTICE_ESTIMATOR_PINNED_COMMIT,
            "pin_source": "docs/lattice_estimator_manifest.json",
        },
        "runtime_environment": {
            "sage_command": sage_command,
            "sage_python_command": sage_python_command_display,
            "sage_found": sage_found,
            "sage_version": sage_version,
            "sage_python_imports_sage": sage_python_imports_sage,
            "sage_python_probe": SAGE_PYTHON_PROBE,
        },
        "readiness": {
            "ready_for_private_lattice_estimator_import": (
                sage_found and sage_python_imports_sage and not failures
            ),
            "requires_checkout_preflight": True,
            "requires_matching_lattice_estimator_pin": True,
            "failure_count": len(failures),
        },
        "safety": {
            "executes_sage_python_probe": True,
            "imports_upstream_python": False,
            "executes_estimator": False,
            "external_network_access": False,
            "numeric_reference_outputs_committed": False,
            "publication_allowed": False,
            "security_claim": False,
            "writes_only_allowed_private_roots": True,
        },
        "failures": failures,
    }


def write_lattice_estimator_runtime_preflight(
    out: Path,
    *,
    sage_command: str,
    sage_python_command: str | None = None,
    policy: dict[str, Any],
    policy_root: Path | None = None,
    timeout_seconds: int = 15,
) -> dict[str, Any]:
    output_root = (policy_root or Path.cwd()).resolve()
    validate_policy_private_path(out, policy=policy, root=output_root)
    report = build_lattice_estimator_runtime_preflight(
        sage_command=sage_command,
        sage_python_command=sage_python_command,
        report_path=out,
        timeout_seconds=timeout_seconds,
    )
    resolved_out = out if out.is_absolute() else output_root / out
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_lattice_estimator_runtime_preflight(
    preflight_path: Path,
) -> dict[str, Any]:
    failures: list[str] = []
    report = _read_runtime_preflight_report(preflight_path, failures)

    _verify_report_metadata(report, failures)
    _verify_upstream(report, failures)
    _verify_runtime_environment(report, failures)
    _verify_readiness(report, failures)
    _verify_safety(report, failures)

    runtime_environment = _object_field(report, "runtime_environment")
    readiness = _object_field(report, "readiness")
    safety = _object_field(report, "safety")
    return {
        "schema_version": LATTICE_ESTIMATOR_RUNTIME_PREFLIGHT_VERIFICATION_SCHEMA,
        "preflight_path": preflight_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "failure_count": readiness.get("failure_count"),
            "ready_for_private_lattice_estimator_import": readiness.get(
                "ready_for_private_lattice_estimator_import"
            ),
            "sage_found": runtime_environment.get("sage_found"),
            "sage_python_imports_sage": runtime_environment.get(
                "sage_python_imports_sage"
            ),
            "security_claim": safety.get("security_claim"),
        },
        "failures": failures,
    }


def _read_runtime_preflight_report(
    preflight_path: Path,
    failures: list[str],
) -> dict[str, Any]:
    try:
        payload = json.loads(preflight_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(
            f"Lattice Estimator runtime preflight is missing: {preflight_path}."
        )
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            "Lattice Estimator runtime preflight is invalid JSON at line "
            f"{exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("Lattice Estimator runtime preflight must be a JSON object.")
        return {}
    return payload


def _verify_report_metadata(report: dict[str, Any], failures: list[str]) -> None:
    if report.get("schema_version") != LATTICE_ESTIMATOR_RUNTIME_PREFLIGHT_SCHEMA:
        failures.append(
            "Lattice Estimator runtime preflight schema_version must be "
            f"{LATTICE_ESTIMATOR_RUNTIME_PREFLIGHT_SCHEMA}."
        )
    report_metadata = report.get("report")
    if not isinstance(report_metadata, dict):
        failures.append("Lattice Estimator runtime preflight report must be an object.")
        return
    if report_metadata.get("private") is not True:
        failures.append("Lattice Estimator runtime preflight report must stay private.")
    path = report_metadata.get("path")
    if not isinstance(path, str) or not path.startswith("private/"):
        failures.append(
            "Lattice Estimator runtime preflight report path must stay under private/."
        )


def _verify_upstream(report: dict[str, Any], failures: list[str]) -> None:
    upstream = report.get("upstream")
    if not isinstance(upstream, dict):
        failures.append(
            "Lattice Estimator runtime preflight upstream must be an object."
        )
        return
    if upstream.get("repository") != LATTICE_ESTIMATOR_REPOSITORY:
        failures.append(
            "Lattice Estimator runtime preflight upstream repository drifted."
        )
    if upstream.get("pinned_commit") != LATTICE_ESTIMATOR_PINNED_COMMIT:
        failures.append("Lattice Estimator runtime preflight pin drifted.")
    if upstream.get("pin_source") != "docs/lattice_estimator_manifest.json":
        failures.append("Lattice Estimator runtime preflight pin source drifted.")


def _verify_runtime_environment(
    report: dict[str, Any],
    failures: list[str],
) -> None:
    runtime_environment = report.get("runtime_environment")
    if not isinstance(runtime_environment, dict):
        failures.append(
            "Lattice Estimator runtime preflight runtime_environment must be an object."
        )
        return
    if not isinstance(runtime_environment.get("sage_command"), str):
        failures.append("Lattice Estimator runtime preflight sage_command is invalid.")
    if not isinstance(runtime_environment.get("sage_python_command"), str):
        failures.append(
            "Lattice Estimator runtime preflight sage_python_command is invalid."
        )
    if not isinstance(runtime_environment.get("sage_found"), bool):
        failures.append("Lattice Estimator runtime preflight sage_found is invalid.")
    if not isinstance(runtime_environment.get("sage_python_imports_sage"), bool):
        failures.append(
            "Lattice Estimator runtime preflight sage_python_imports_sage is invalid."
        )
    if runtime_environment.get("sage_python_probe") != SAGE_PYTHON_PROBE:
        failures.append(
            "Lattice Estimator runtime preflight Sage Python probe drifted."
        )
    sage_version = runtime_environment.get("sage_version")
    if sage_version is not None and not isinstance(sage_version, str):
        failures.append("Lattice Estimator runtime preflight sage_version is invalid.")


def _verify_readiness(report: dict[str, Any], failures: list[str]) -> None:
    readiness = report.get("readiness")
    runtime_environment = _object_field(report, "runtime_environment")
    report_failures = report.get("failures")
    if not isinstance(readiness, dict):
        failures.append(
            "Lattice Estimator runtime preflight readiness must be an object."
        )
        return
    if not isinstance(report_failures, list) or not all(
        isinstance(failure, str) for failure in report_failures
    ):
        failures.append("Lattice Estimator runtime preflight failures must be strings.")
        report_failures = []
    if readiness.get("failure_count") != len(report_failures):
        failures.append(
            "Lattice Estimator runtime preflight failure_count must match failures."
        )
    if readiness.get("requires_checkout_preflight") is not True:
        failures.append(
            "Lattice Estimator runtime preflight must require checkout preflight."
        )
    if readiness.get("requires_matching_lattice_estimator_pin") is not True:
        failures.append(
            "Lattice Estimator runtime preflight must require the reviewed pin."
        )
    expected_ready = (
        runtime_environment.get("sage_found") is True
        and runtime_environment.get("sage_python_imports_sage") is True
        and len(report_failures) == 0
    )
    ready = readiness.get("ready_for_private_lattice_estimator_import")
    if ready is not expected_ready:
        failures.append(
            "Lattice Estimator runtime preflight readiness is inconsistent with "
            "Sage probe results."
        )


def _verify_safety(report: dict[str, Any], failures: list[str]) -> None:
    safety = report.get("safety")
    if not isinstance(safety, dict):
        failures.append("Lattice Estimator runtime preflight safety must be an object.")
        return
    if safety.get("executes_sage_python_probe") is not True:
        failures.append(
            "Lattice Estimator runtime preflight must disclose the Sage Python probe."
        )
    for flag in _EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            if flag == "imports_upstream_python":
                failures.append(
                    "Lattice Estimator runtime preflight must not import "
                    "upstream Python."
                )
            else:
                failures.append(
                    f"Lattice Estimator runtime preflight safety.{flag} must be false."
                )
    if safety.get("writes_only_allowed_private_roots") is not True:
        failures.append(
            "Lattice Estimator runtime preflight must write only allowed private roots."
        )


def _object_field(report: dict[str, Any], field: str) -> dict[str, Any]:
    value = report.get(field)
    if isinstance(value, dict):
        return value
    return {}


def _run_probe(
    command: list[str],
    *,
    timeout_seconds: int,
) -> _ProbeResult:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        return _ProbeResult(command_found=False, returncode=None, output="")
    except subprocess.TimeoutExpired as exc:
        return _ProbeResult(
            command_found=True,
            returncode=None,
            output=_combine_output(exc.stdout, exc.stderr),
            timed_out=True,
        )
    return _ProbeResult(
        command_found=True,
        returncode=completed.returncode,
        output=_combine_output(completed.stdout, completed.stderr),
    )


def _combine_output(stdout: str | bytes | None, stderr: str | bytes | None) -> str:
    parts = [_decode_output(part).strip() for part in (stdout, stderr) if part]
    return "\n".join(part for part in parts if part)


def _decode_output(output: str | bytes) -> str:
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output


def _first_line(output: str) -> str | None:
    for line in output.splitlines():
        line = line.strip()
        if line:
            return line
    return None


def _output_summary(output: str) -> str:
    summary = " ".join(output.split())
    if not summary:
        return "no output"
    return summary[:240]
