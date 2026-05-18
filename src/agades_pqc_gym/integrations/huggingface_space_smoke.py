from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HF_SPACE_SMOKE_SCHEMA = "agades.pqc.hf_space_smoke.v1"
HF_SPACE_SMOKE_VERIFICATION_SCHEMA = "agades.pqc.hf_space_smoke_verification.v1"
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT = Path("reports/hf_space_smoke.json")

_RELEASE_GATES = (
    "uv run pytest tests/test_huggingface_space_smoke.py -q",
    "uv run agades-pqc hf-space-smoke --out reports/hf_space_smoke.json",
    "uv run agades-pqc hf-space-smoke-verify --report reports/hf_space_smoke.json",
    "uv run agades-pqc ecosystem-smoke-verify --report reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
)
_FALSE_SAFETY_FLAGS = (
    "arbitrary_code_execution",
    "contains_private_traces",
    "live_targeting",
    "publishes_private_candidates",
    "security_claim",
)


def build_huggingface_space_smoke_report(
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    app_path = project_root / "hf" / "app.py"
    failures: list[str] = []
    app = {
        "app_path": "hf/app.py",
        "imports_without_gradio": False,
        "uses_shared_verifier": False,
    }
    examples = {
        "default_label": None,
        "default_is_selectable": False,
        "example_count": 0,
    }
    evaluation = {
        "accepted": False,
        "combined_score": None,
        "evaluation_status": "not_run",
        "security_claim": None,
        "summary_contains_not_security_claim": False,
        "target_family": None,
    }

    try:
        module = _load_python_module(app_path, "agades_pqc_hf_space_smoke")
        app["imports_without_gradio"] = True
        choices = module.example_plan_choices()
        default_label = module.DEFAULT_EXAMPLE_LABEL
        default_plan = module.load_example_plan(default_label)
        summary, payload = module.evaluate_attack_plan_json(default_plan)
        verifier_result = json.loads(payload)
    except Exception as exc:  # noqa: BLE001 - smoke report must capture app issues.
        failures.append(f"Hugging Face Space smoke failed: {exc}")
    else:
        app["uses_shared_verifier"] = True
        examples = {
            "default_label": default_label,
            "default_is_selectable": default_label in choices,
            "example_count": len(choices),
        }
        safety = verifier_result.get("safety", {})
        evaluation = {
            "accepted": verifier_result.get("accepted") is True,
            "combined_score": verifier_result.get("combined_score"),
            "evaluation_status": verifier_result.get("evaluation_status"),
            "security_claim": safety.get("security_claim"),
            "summary_contains_not_security_claim": "not a security claim" in summary,
            "target_family": verifier_result.get("target_family"),
        }
        _validate_smoke_contract(app, examples, evaluation, failures)

    safety = dict.fromkeys(_FALSE_SAFETY_FLAGS, False)
    return {
        "schema_version": HF_SPACE_SMOKE_SCHEMA,
        "accepted": not failures,
        "app": app,
        "examples": examples,
        "evaluation": evaluation,
        "safety": safety,
        "release_gates": list(_RELEASE_GATES),
        "failures": failures,
    }


def write_huggingface_space_smoke_report(
    out: Path = DEFAULT_REPORT,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    report = build_huggingface_space_smoke_report(root=root)
    resolved_out = _resolve_path(out, root=root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_huggingface_space_smoke_report(
    report_path: Path = DEFAULT_REPORT,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    expected = build_huggingface_space_smoke_report(root=project_root)
    failures: list[str] = []
    report = _read_report(_resolve_path(report_path, root=project_root), failures)

    if report != expected:
        failures.append("Hugging Face Space smoke report is not in sync.")
    _verify_schema(report, failures)
    _verify_app(report, failures)
    _verify_examples(report, failures)
    _verify_evaluation(report, failures)
    _verify_safety(report, failures)
    _verify_release_gates(report, failures)

    return {
        "schema_version": HF_SPACE_SMOKE_VERIFICATION_SCHEMA,
        "report_path": _display_path(report_path, root=project_root),
        "accepted": not failures,
        "summary": _verification_summary(report, failures),
        "failures": failures,
    }


def _validate_smoke_contract(
    app: dict[str, Any],
    examples: dict[str, Any],
    evaluation: dict[str, Any],
    failures: list[str],
) -> None:
    if app["imports_without_gradio"] is not True:
        failures.append("Hugging Face Space app did not import without Gradio.")
    if app["uses_shared_verifier"] is not True:
        failures.append("Hugging Face Space app does not use the shared verifier.")
    if examples["example_count"] < 1:
        failures.append("Hugging Face Space exposes no public examples.")
    if examples["default_is_selectable"] is not True:
        failures.append("Hugging Face Space default example is not selectable.")
    if evaluation["accepted"] is not True:
        failures.append("Hugging Face Space default example is not accepted.")
    if evaluation["security_claim"] is not False:
        failures.append("Hugging Face Space verifier output makes a claim.")
    if evaluation["summary_contains_not_security_claim"] is not True:
        failures.append("Hugging Face Space summary lacks safety wording.")


def _read_report(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Hugging Face Space smoke report is missing: {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Hugging Face Space smoke report is invalid JSON at line {exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("Hugging Face Space smoke report must be a JSON object.")
        return {}
    return payload


def _verify_schema(report: dict[str, Any], failures: list[str]) -> None:
    if report.get("schema_version") != HF_SPACE_SMOKE_SCHEMA:
        failures.append(
            "Hugging Face Space smoke report schema_version must be "
            f"{HF_SPACE_SMOKE_SCHEMA}."
        )
    if report.get("accepted") is not True:
        failures.append("Hugging Face Space smoke report is not accepted.")


def _verify_app(report: dict[str, Any], failures: list[str]) -> None:
    app = report.get("app")
    if not isinstance(app, dict):
        failures.append("Hugging Face Space smoke report app must be an object.")
        return
    if app.get("app_path") != "hf/app.py":
        failures.append("Hugging Face Space smoke report app_path is incorrect.")
    if app.get("imports_without_gradio") is not True:
        failures.append(
            "Hugging Face Space smoke report requires Gradio to import."
        )
    if app.get("uses_shared_verifier") is not True:
        failures.append(
            "Hugging Face Space smoke report does not use the shared verifier."
        )


def _verify_examples(report: dict[str, Any], failures: list[str]) -> None:
    examples = report.get("examples")
    if not isinstance(examples, dict):
        failures.append("Hugging Face Space smoke report examples must be an object.")
        return
    if not isinstance(examples.get("default_label"), str):
        failures.append("Hugging Face Space smoke report lacks default label.")
    if examples.get("default_is_selectable") is not True:
        failures.append("Hugging Face Space smoke report default is not selectable.")
    if not isinstance(examples.get("example_count"), int):
        failures.append("Hugging Face Space smoke report example_count is invalid.")
    elif examples["example_count"] < 1:
        failures.append("Hugging Face Space smoke report has no examples.")


def _verify_evaluation(report: dict[str, Any], failures: list[str]) -> None:
    evaluation = report.get("evaluation")
    if not isinstance(evaluation, dict):
        failures.append("Hugging Face Space smoke report evaluation must be an object.")
        return
    if evaluation.get("accepted") is not True:
        failures.append("Hugging Face Space smoke report default is not accepted.")
    if evaluation.get("security_claim") is not False:
        failures.append("Hugging Face Space smoke report advertises a security claim.")
    if evaluation.get("summary_contains_not_security_claim") is not True:
        failures.append(
            "Hugging Face Space smoke report summary lacks safety wording."
        )


def _verify_safety(report: dict[str, Any], failures: list[str]) -> None:
    safety = report.get("safety")
    if not isinstance(safety, dict):
        failures.append("Hugging Face Space smoke report safety must be an object.")
        return
    for flag in _FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            failures.append(f"Hugging Face Space smoke report {flag} must be false.")


def _verify_release_gates(report: dict[str, Any], failures: list[str]) -> None:
    release_gates = report.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append(
            "Hugging Face Space smoke report release_gates must be a list."
        )
        return
    for gate in _RELEASE_GATES:
        if gate not in release_gates:
            failures.append(
                f"Hugging Face Space smoke report release gate missing: {gate}"
            )


def _verification_summary(
    report: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    app = report.get("app") if isinstance(report.get("app"), dict) else {}
    examples = (
        report.get("examples") if isinstance(report.get("examples"), dict) else {}
    )
    evaluation = (
        report.get("evaluation") if isinstance(report.get("evaluation"), dict) else {}
    )
    return {
        "default_label": examples.get("default_label"),
        "example_count": examples.get("example_count"),
        "failure_count": len(failures),
        "imports_without_gradio": app.get("imports_without_gradio"),
        "summary_contains_not_security_claim": evaluation.get(
            "summary_contains_not_security_claim"
        ),
        "uses_shared_verifier": app.get("uses_shared_verifier"),
    }


def _load_python_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_path(path: Path, *, root: Path | None) -> Path:
    if path.is_absolute() or root is None:
        return path
    return root / path


def _display_path(path: Path, *, root: Path) -> str:
    resolved = _resolve_path(path, root=root)
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return resolved.as_posix()
