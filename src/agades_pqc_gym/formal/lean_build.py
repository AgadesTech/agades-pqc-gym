from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from agades_pqc_gym.formal.lean_backend import (
    DEFAULT_BACKEND_PATH,
    FORMAL_LEAN_BACKEND_SCHEMA,
    LEAN_PROJECT,
    ROOT,
    build_formal_lean_backend,
    verify_formal_lean_backend,
)
from agades_pqc_gym.utils.hashing import stable_sha256

FORMAL_LEAN_BUILD_SMOKE_SCHEMA = "agades.pqc.formal.lean_build_smoke.v1"
FORMAL_LEAN_BUILD_SMOKE_VERIFICATION_SCHEMA = (
    "agades.pqc.formal.lean_build_smoke_verification.v1"
)
DEFAULT_LEAN_BUILD_SMOKE_PATH = Path("reports/formal_lean_build_smoke.json")
DEFAULT_LEAN_BUILD_COMMAND = ("lake", "build")
DEFAULT_TIMEOUT_SECONDS = 600
BUILD_SCOPE = {
    "compiles_lean_sources": True,
    "executes_cryptographic_estimators": False,
    "publishes_artifacts": False,
    "security_claim_allowed": False,
    "cryptographic_soundness_review_required": True,
}


def run_formal_lean_build_smoke(
    *,
    root: Path | None = None,
    command: Sequence[str] = DEFAULT_LEAN_BUILD_COMMAND,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    command_args = list(command)
    if not command_args:
        raise ValueError("formal Lean build command must not be empty")
    if timeout_seconds <= 0:
        raise ValueError("formal Lean build timeout must be positive")

    build = _run_build(
        command_args,
        cwd=project_root / LEAN_PROJECT["root"],
        root=project_root,
        timeout_seconds=timeout_seconds,
    )
    backend_verification = verify_formal_lean_backend(
        DEFAULT_BACKEND_PATH,
        root=project_root,
    )
    backend_binding = _formal_backend_manifest_binding(project_root)
    accepted = (
        build["return_code"] == 0
        and build["timed_out"] is False
        and backend_verification["accepted"] is True
    )
    backend_summary = backend_verification["summary"]
    report = {
        "schema_version": FORMAL_LEAN_BUILD_SMOKE_SCHEMA,
        "accepted": accepted,
        "scope": dict(BUILD_SCOPE),
        "lean_project": _lean_project_binding(),
        "build": build,
        "formal_backend_manifest": backend_binding,
        "formal_backend_verification": backend_verification,
        "summary": {
            "accepted": accepted,
            "source_modules": backend_summary.get("source_modules", 0),
            "theorem_declarations": backend_summary.get("theorem_declarations", 0),
            "placeholder_failures": backend_summary.get("placeholder_failures", 0),
            "ci_lean_build_gate": backend_summary.get("ci_lean_build_gate", False),
            "security_claim_allowed": False,
        },
        "notes": _build_notes(accepted=accepted),
    }
    report["report_sha256"] = _report_sha256(report)
    return report


def _build_notes(*, accepted: bool) -> list[str]:
    if accepted:
        build_status_note = (
            "This report proves that the checked Lean source bundle compiled "
            "for the configured backend; it is not a cryptographic soundness "
            "review and it does not authorize a public security claim."
        )
    else:
        build_status_note = (
            "This report proves that the checked Lean source bundle did not compile "
            "for the configured backend in the current environment; it is not a "
            "cryptographic soundness review and it does not authorize a public "
            "security claim."
        )
    return [
        build_status_note,
        (
            "No process environment is captured in this report. The CLI uses "
            "the fixed `lake build` argv; the report records command argv, "
            "cwd, return code, output hashes, and short output tails."
        ),
    ]


def write_formal_lean_build_smoke(
    out: Path = DEFAULT_LEAN_BUILD_SMOKE_PATH,
    *,
    root: Path | None = None,
    command: Sequence[str] = DEFAULT_LEAN_BUILD_COMMAND,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    report = run_formal_lean_build_smoke(
        root=project_root,
        command=command,
        timeout_seconds=timeout_seconds,
    )
    resolved = _resolve_path(out, project_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_formal_lean_build_smoke(
    report_path: Path = DEFAULT_LEAN_BUILD_SMOKE_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    resolved = _resolve_path(report_path, project_root)
    report = _read_json_object(resolved, "Formal Lean build smoke report", failures)
    if report:
        _verify_report(report, project_root, failures)

    summary_payload = report.get("summary", {}) if isinstance(report, dict) else {}
    summary = {
        "accepted": bool(summary_payload.get("accepted")),
        "source_modules": int(summary_payload.get("source_modules", 0) or 0),
        "theorem_declarations": int(
            summary_payload.get("theorem_declarations", 0) or 0
        ),
        "placeholder_failures": int(
            summary_payload.get("placeholder_failures", 0) or 0
        ),
        "failure_count": len(failures),
    }
    return {
        "schema_version": FORMAL_LEAN_BUILD_SMOKE_VERIFICATION_SCHEMA,
        "report_path": report_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _run_build(
    command: list[str],
    *,
    cwd: Path,
    root: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        return_code: int | None = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = _coerce_output(exc.output)
        stderr = _coerce_output(exc.stderr)
        return_code = None
        timed_out = True
        error: dict[str, str] | None = None
    except OSError as exc:
        stdout = ""
        command_name = command[0] if command else "<unknown>"
        stderr = f"{exc.strerror or exc.__class__.__name__}: {command_name}"
        return_code = None
        timed_out = False
        error = {
            "kind": exc.__class__.__name__,
            "message": stderr,
        }
    else:
        error = None

    build = {
        "command": command,
        "cwd": (
            cwd.relative_to(root).as_posix()
            if cwd.is_relative_to(root)
            else str(cwd)
        ),
        "return_code": return_code,
        "stdout_sha256": _text_sha256(stdout),
        "stderr_sha256": _text_sha256(stderr),
        "stdout_tail": _tail(stdout),
        "stderr_tail": _tail(stderr),
        "timed_out": timed_out,
        "environment_exported": False,
    }
    if error is not None:
        build["error"] = error
    return build


def _formal_backend_manifest_binding(root: Path) -> dict[str, Any]:
    manifest_path = root / DEFAULT_BACKEND_PATH
    expected = build_formal_lean_backend(root=root)
    raw = manifest_path.read_bytes()
    return {
        "path": DEFAULT_BACKEND_PATH.as_posix(),
        "schema_version": FORMAL_LEAN_BACKEND_SCHEMA,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "manifest_sha256": expected["manifest_sha256"],
        "source_modules": expected["summary"]["source_modules"],
        "theorem_declarations": expected["summary"]["theorem_declarations"],
        "placeholder_failures": expected["summary"]["placeholder_failures"],
        "ci_lean_build_gate": expected["summary"]["ci_lean_build_gate"],
    }


def _lean_project_binding() -> dict[str, str]:
    return {
        "root": LEAN_PROJECT["root"],
        "toolchain": LEAN_PROJECT["toolchain"],
        "lakefile": LEAN_PROJECT["lakefile"],
        "lake_manifest": LEAN_PROJECT["lake_manifest"],
        "entry_module": LEAN_PROJECT["entry_module"],
    }


def _verify_report(
    report: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    if report.get("schema_version") != FORMAL_LEAN_BUILD_SMOKE_SCHEMA:
        failures.append(
            "Formal Lean build smoke schema_version must be "
            f"{FORMAL_LEAN_BUILD_SMOKE_SCHEMA}."
        )
    if report.get("scope") != BUILD_SCOPE:
        failures.append("Formal Lean build smoke scope drifted.")
    if report.get("lean_project") != _lean_project_binding():
        failures.append("Formal Lean build smoke Lean project binding drifted.")

    build = report.get("build")
    if not isinstance(build, dict):
        failures.append("Formal Lean build smoke build entry must be an object.")
    else:
        if build.get("environment_exported") is not False:
            failures.append("Formal Lean build smoke must not export environment.")
        if build.get("timed_out") is not False:
            failures.append("Formal Lean build smoke timed out.")
        if build.get("return_code") != 0:
            failures.append("Formal Lean build smoke did not complete successfully.")
        if build.get("cwd") != LEAN_PROJECT["root"]:
            failures.append("Formal Lean build smoke cwd drifted.")

    expected_backend_binding = _formal_backend_manifest_binding(root)
    backend_binding = report.get("formal_backend_manifest")
    if not isinstance(backend_binding, dict):
        failures.append(
            "Formal Lean build smoke backend manifest binding must be an object."
        )
    else:
        for key, value in expected_backend_binding.items():
            if backend_binding.get(key) != value:
                label = "hash" if key == "sha256" else key
                failures.append(
                    f"Formal Lean build smoke backend manifest {label} drifted."
                )

    backend_verification = report.get("formal_backend_verification")
    expected_backend_verification = verify_formal_lean_backend(
        DEFAULT_BACKEND_PATH,
        root=root,
    )
    if backend_verification != expected_backend_verification:
        failures.append("Formal Lean build smoke backend verification drifted.")

    expected_summary = {
        "accepted": report.get("accepted") is True,
        "source_modules": expected_backend_verification["summary"].get(
            "source_modules", 0
        ),
        "theorem_declarations": expected_backend_verification["summary"].get(
            "theorem_declarations", 0
        ),
        "placeholder_failures": expected_backend_verification["summary"].get(
            "placeholder_failures", 0
        ),
        "ci_lean_build_gate": expected_backend_verification["summary"].get(
            "ci_lean_build_gate", False
        ),
        "security_claim_allowed": False,
    }
    if report.get("summary") != expected_summary:
        failures.append("Formal Lean build smoke summary drifted.")
    if report.get("accepted") is not True:
        failures.append("Formal Lean build smoke report is not accepted.")
    if report.get("report_sha256") != _report_sha256(report):
        failures.append("Formal Lean build smoke report hash does not match.")


def _report_sha256(report: dict[str, Any]) -> str:
    payload = {key: value for key, value in report.items() if key != "report_sha256"}
    return stable_sha256(payload)


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _tail(text: str, limit: int = 4000) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[-limit:]


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _read_json_object(
    path: Path,
    label: str,
    failures: list[str],
) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"{label} is missing: {path.as_posix()}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"{label} is invalid JSON at line {exc.lineno}.")
        return {}
    if not isinstance(payload, dict):
        failures.append(f"{label} must be a JSON object.")
        return {}
    return payload


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path
