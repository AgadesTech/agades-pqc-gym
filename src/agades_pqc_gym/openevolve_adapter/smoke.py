from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any

OPENEVOLVE_SMOKE_SCHEMA = "agades.pqc.openevolve_smoke.v1"
OPENEVOLVE_SMOKE_VERIFICATION_SCHEMA = "agades.pqc.openevolve_smoke_verification.v1"
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT = Path("reports/openevolve_smoke.json")
DEFAULT_OPENEVOLVE_SMOKE_PLAN = Path(
    "examples/attack_plans/lattice_primal_usvp_toy.json"
)
DEFAULT_OPENEVOLVE_SMOKE_EVALUATOR = Path("examples/openevolve/evaluator.py")
PRIMARY_METRIC = "combined_score"
REQUIRED_METRIC_KEYS = (
    "combined_score",
    "fitness_schema_version",
    "evaluation_status",
    "feature_family",
    "feature_attack_type",
    "feature_operator_count",
    "feature_memory_bucket",
    "feature_assumption_bucket",
    "feature_estimator_model",
    "validity_score",
    "reproducibility_score",
    "assumption_penalty",
    "instability_penalty",
)
_RELEASE_GATES = (
    "uv run pytest tests/test_openevolve_adapter.py -q",
    "uv run agades-pqc openevolve-smoke --out reports/openevolve_smoke.json",
    "uv run agades-pqc openevolve-smoke-verify --report reports/openevolve_smoke.json",
    "uv run agades-pqc ecosystem-smoke-verify --report reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
)
_FALSE_SAFETY_FLAGS = (
    "arbitrary_code_execution",
    "python_candidates_executed",
    "security_claim",
)


def build_openevolve_smoke_report(
    *,
    plan_path: Path = DEFAULT_OPENEVOLVE_SMOKE_PLAN,
    evaluator_path: Path = DEFAULT_OPENEVOLVE_SMOKE_EVALUATOR,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or Path.cwd()).resolve()
    resolved_plan = _resolve(project_root, plan_path)
    resolved_evaluator = _resolve(project_root, evaluator_path)
    failures: list[str] = []
    metrics: dict[str, Any] = {}

    try:
        module = _load_python_module(
            resolved_evaluator,
            "agades_pqc_gym_openevolve_smoke_evaluator",
        )
        result = module.evaluate(str(resolved_plan))
    except Exception as exc:  # noqa: BLE001 - smoke report must record failures.
        failures.append(f"OpenEvolve evaluator smoke failed: {exc}.")
        result = {}

    if not isinstance(result, dict):
        failures.append("OpenEvolve evaluator must return a metrics dictionary.")
    else:
        metrics = _strict_json_metrics(result, failures)

    missing_keys = sorted(set(REQUIRED_METRIC_KEYS) - set(metrics))
    if missing_keys:
        failures.append(
            "OpenEvolve evaluator metrics missing required keys: "
            f"{', '.join(missing_keys)}."
        )

    combined_score = metrics.get(PRIMARY_METRIC)
    if not _is_finite_number(combined_score):
        failures.append("OpenEvolve evaluator combined_score must be numeric.")
    if metrics.get("fitness_schema_version") != "agades.pqc.fitness_report.v1":
        failures.append("OpenEvolve evaluator fitness schema drifted.")

    return {
        "schema_version": OPENEVOLVE_SMOKE_SCHEMA,
        "accepted": not failures,
        "evaluator_path": _display_path(evaluator_path),
        "attack_plan_path": _display_path(plan_path),
        "primary_metric": PRIMARY_METRIC,
        "required_metric_keys": list(REQUIRED_METRIC_KEYS),
        "summary": {
            "combined_score": combined_score,
            "evaluation_status": metrics.get("evaluation_status"),
            "failure_count": len(failures),
            "feature_attack_type": metrics.get("feature_attack_type"),
            "feature_family": metrics.get("feature_family"),
            "feature_memory_bucket": metrics.get("feature_memory_bucket"),
            "metric_count": len(metrics),
            "primary_metric": PRIMARY_METRIC,
            "python_candidates_executed": False,
        },
        "safety": {
            "arbitrary_code_execution": False,
            "python_candidates_executed": False,
            "security_claim": False,
        },
        "release_gates": list(_RELEASE_GATES),
        "metrics": metrics,
        "failures": failures,
    }


def write_openevolve_smoke_report(
    out: Path = DEFAULT_REPORT,
    *,
    plan_path: Path = DEFAULT_OPENEVOLVE_SMOKE_PLAN,
    evaluator_path: Path = DEFAULT_OPENEVOLVE_SMOKE_EVALUATOR,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    report = build_openevolve_smoke_report(
        plan_path=plan_path,
        evaluator_path=evaluator_path,
        root=project_root,
    )
    resolved_out = _resolve(project_root, out)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(report, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_openevolve_smoke_report(
    report_path: Path = DEFAULT_REPORT,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    expected = build_openevolve_smoke_report(root=project_root)
    failures: list[str] = []
    resolved_report = _resolve(project_root, report_path)
    report = _read_report(resolved_report, failures)
    checked_in_report_synced = report == expected

    if not checked_in_report_synced:
        failures.append("Checked OpenEvolve smoke report is not in sync.")
    if expected.get("accepted") is not True:
        failures.extend(
            failure
            for failure in expected.get("failures", [])
            if isinstance(failure, str)
        )

    _verify_schema(report, failures)
    _verify_paths(report, failures)
    _verify_summary(report, failures)
    _verify_safety(report, failures)
    _verify_release_gates(report, failures)

    return {
        "schema_version": OPENEVOLVE_SMOKE_VERIFICATION_SCHEMA,
        "report_path": _display_path(report_path),
        "accepted": not failures,
        "summary": _verification_summary(
            report,
            failures,
            checked_in_report_synced=checked_in_report_synced,
        ),
        "failures": failures,
    }


def _resolve(root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return root / path


def _display_path(path: Path) -> str:
    return path.as_posix()


def _read_report(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"OpenEvolve smoke report is missing: {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"OpenEvolve smoke report is invalid JSON at line {exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("OpenEvolve smoke report must be a JSON object.")
        return {}
    return payload


def _verify_schema(report: dict[str, Any], failures: list[str]) -> None:
    if report.get("schema_version") != OPENEVOLVE_SMOKE_SCHEMA:
        failures.append(
            f"OpenEvolve smoke report schema_version must be {OPENEVOLVE_SMOKE_SCHEMA}."
        )
    if report.get("accepted") is not True:
        failures.append("OpenEvolve smoke report is not accepted.")


def _verify_paths(report: dict[str, Any], failures: list[str]) -> None:
    if report.get("attack_plan_path") != _display_path(DEFAULT_OPENEVOLVE_SMOKE_PLAN):
        failures.append("OpenEvolve smoke report attack_plan_path drifted.")
    if report.get("evaluator_path") != _display_path(
        DEFAULT_OPENEVOLVE_SMOKE_EVALUATOR
    ):
        failures.append("OpenEvolve smoke report evaluator_path drifted.")


def _verify_summary(report: dict[str, Any], failures: list[str]) -> None:
    summary = report.get("summary")
    if not isinstance(summary, dict):
        failures.append("OpenEvolve smoke report summary must be an object.")
        return

    if summary.get("evaluation_status") != "ok":
        failures.append(
            "OpenEvolve smoke report seed plan must evaluate with ok status."
        )
    if summary.get("feature_family") != "LWE":
        failures.append("OpenEvolve smoke report seed plan family drifted.")
    if summary.get("feature_attack_type") != "primal_usvp":
        failures.append("OpenEvolve smoke report seed plan attack type drifted.")
    if summary.get("primary_metric") != PRIMARY_METRIC:
        failures.append("OpenEvolve smoke report primary_metric drifted.")
    if summary.get("python_candidates_executed") is not False:
        failures.append(
            "OpenEvolve smoke report python_candidates_executed must be false."
        )
    if summary.get("failure_count") != 0:
        failures.append("OpenEvolve smoke report must have zero recorded failures.")

    combined_score = summary.get("combined_score")
    if not _is_finite_number(combined_score):
        failures.append("OpenEvolve smoke report combined_score must be numeric.")
    elif combined_score >= 0:
        failures.append("OpenEvolve smoke report combined_score must keep cost sign.")


def _verify_safety(report: dict[str, Any], failures: list[str]) -> None:
    safety = report.get("safety")
    if not isinstance(safety, dict):
        failures.append("OpenEvolve smoke report safety must be an object.")
        return
    for flag in _FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            failures.append(f"OpenEvolve smoke report {flag} must be false.")


def _verify_release_gates(report: dict[str, Any], failures: list[str]) -> None:
    release_gates = report.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append("OpenEvolve smoke report release_gates must be a list.")
        return
    for gate in _RELEASE_GATES:
        if gate not in release_gates:
            failures.append(f"OpenEvolve smoke report release gate missing: {gate}")


def _verification_summary(
    report: dict[str, Any],
    failures: list[str],
    *,
    checked_in_report_synced: bool,
) -> dict[str, Any]:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    safety = report.get("safety") if isinstance(report.get("safety"), dict) else {}
    return {
        "arbitrary_code_execution": safety.get("arbitrary_code_execution"),
        "checked_in_report_synced": checked_in_report_synced,
        "combined_score": summary.get("combined_score"),
        "evaluation_status": summary.get("evaluation_status"),
        "failure_count": len(failures),
        "feature_attack_type": summary.get("feature_attack_type"),
        "feature_family": summary.get("feature_family"),
        "primary_metric": summary.get("primary_metric"),
        "python_candidates_executed": summary.get("python_candidates_executed"),
        "security_claim": safety.get("security_claim"),
    }


def _strict_json_metrics(
    metrics: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    try:
        return json.loads(json.dumps(metrics, allow_nan=False))
    except (TypeError, ValueError) as exc:
        failures.append(
            f"OpenEvolve evaluator metrics must be strict JSON-serializable: {exc}."
        )
        return {}


def _is_finite_number(value: Any) -> bool:
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _load_python_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
