from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HF_SPACE_SMOKE_SCHEMA = "agades.pqc.hf_space_smoke.v1"
HF_SPACE_SMOKE_VERIFICATION_SCHEMA = "agades.pqc.hf_space_smoke_verification.v1"
HF_SPACE_LAUNCH_SMOKE_SCHEMA = "agades.pqc.hf_space_launch_smoke.v1"
HF_SPACE_LAUNCH_SMOKE_VERIFICATION_SCHEMA = (
    "agades.pqc.hf_space_launch_smoke_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT = Path("reports/hf_space_smoke.json")
DEFAULT_LAUNCH_REPORT = Path("reports/hf_space_launch_smoke.json")

_RELEASE_GATES = (
    "uv run --extra dev pytest tests/test_huggingface_space_smoke.py -q",
    "uv run --extra dev agades-pqc hf-space-smoke --out "
    "reports/hf_space_smoke.json",
    "uv run --extra dev agades-pqc hf-space-smoke-verify --report "
    "reports/hf_space_smoke.json",
    "uv run --extra dev agades-pqc hf-space-launch-smoke --out "
    "reports/hf_space_launch_smoke.json",
    "uv run --extra dev agades-pqc hf-space-launch-smoke-verify --report "
    "reports/hf_space_launch_smoke.json",
    "uv run --extra dev agades-pqc ecosystem-smoke-verify --report "
    "reports/ecosystem_smoke.json",
    "uv run --extra dev agades-pqc release-audit --out public/release_audit.json",
)
_FALSE_SAFETY_FLAGS = (
    "arbitrary_code_execution",
    "contains_private_traces",
    "live_targeting",
    "publishes_private_candidates",
    "security_claim",
)
_LAUNCH_FALSE_SAFETY_FLAGS = (
    "contains_private_traces",
    "publishes_private_candidates",
    "security_claim",
)
_REQUIRED_API_NAMES = (
    "load_example_plan",
    "evaluate_attack_plan_json",
    "load_example_plan_1",
    "load_environment_observation",
    "score_attack_plan_for_task",
)
_AGENT_ENVIRONMENT_API_NAMES = (
    "load_environment_observation",
    "score_attack_plan_for_task",
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
        "uses_rl_environment": False,
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
    agent_environment = {
        "observation_schema": None,
        "reward_report_schema": None,
        "rollout_trace_schema": None,
        "has_prompt": False,
        "reward": None,
        "task_match": None,
        "trace_public_release_ok": False,
        "private_fields_present": None,
        "claims_pqc_break": None,
    }
    unsupported_behavior = {
        "invalid_json_evaluation_summary_has_reason": False,
        "invalid_json_reward_summary_has_reason": False,
        "unsupported_family_evaluation_summary_has_reason": False,
        "unsupported_family_reward_summary_has_reason": False,
        "unsupported_family_accepted": None,
        "unsupported_family_reward": None,
    }

    try:
        module = _load_python_module(app_path, "agades_pqc_hf_space_smoke")
        app["imports_without_gradio"] = True
        choices = module.example_plan_choices()
        default_label = module.DEFAULT_EXAMPLE_LABEL
        default_plan = module.load_example_plan(default_label)
        summary, payload = module.evaluate_attack_plan_json(default_plan)
        verifier_result = json.loads(payload)
        observation_payload = module.load_environment_observation(default_label)
        (
            reward_summary,
            reward_payload,
            trace_payload,
        ) = module.score_attack_plan_for_task(default_label, default_plan)
        observation = json.loads(observation_payload)
        reward_report = json.loads(reward_payload)
        trace = json.loads(trace_payload)
        unsupported_behavior = _unsupported_behavior(
            module=module,
            default_label=default_label,
            default_plan=default_plan,
        )
    except Exception as exc:  # noqa: BLE001 - smoke report must capture app issues.
        failures.append(f"Hugging Face Space smoke failed: {exc}")
    else:
        app["uses_shared_verifier"] = True
        app["uses_rl_environment"] = True
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
        agent_environment = {
            "observation_schema": observation.get("schema_version"),
            "reward_report_schema": reward_report.get("schema_version"),
            "rollout_trace_schema": trace.get("schema_version"),
            "has_prompt": bool(observation.get("prompt")),
            "reward": reward_report.get("reward"),
            "task_match": reward_report.get("terms", {}).get("task_match"),
            "trace_public_release_ok": trace.get("public_release_ok"),
            "private_fields_present": trace.get("private_fields_present"),
            "claims_pqc_break": trace.get("claim_boundary", {}).get(
                "claims_pqc_break"
            ),
        }
        _validate_smoke_contract(
            app,
            examples,
            evaluation,
            agent_environment,
            unsupported_behavior,
            reward_summary,
            failures,
        )

    safety = dict.fromkeys(_FALSE_SAFETY_FLAGS, False)
    return {
        "schema_version": HF_SPACE_SMOKE_SCHEMA,
        "accepted": not failures,
        "app": app,
        "agent_environment": agent_environment,
        "unsupported_behavior": unsupported_behavior,
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
    _verify_agent_environment(report, failures)
    _verify_unsupported_behavior(report, failures)
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


def build_huggingface_space_launch_smoke_report(
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    app_path = project_root / "hf" / "app.py"
    failures: list[str] = []
    gradio = {
        "available": False,
        "demo_class": None,
        "title": None,
        "component_count": 0,
    }
    api = {
        "api_names": [],
        "required_api_names_present": False,
        "agent_environment_api_names_present": False,
    }
    backend_smoke_report = build_huggingface_space_smoke_report(root=project_root)
    backend_smoke = {
        "accepted": backend_smoke_report.get("accepted") is True,
        "default_label": backend_smoke_report.get("examples", {}).get(
            "default_label"
        ),
        "example_count": backend_smoke_report.get("examples", {}).get(
            "example_count"
        ),
        "reward": backend_smoke_report.get("agent_environment", {}).get("reward"),
        "trace_public_release_ok": backend_smoke_report.get(
            "agent_environment", {}
        ).get("trace_public_release_ok"),
        "claims_pqc_break": backend_smoke_report.get("agent_environment", {}).get(
            "claims_pqc_break"
        ),
    }

    try:
        module = _load_python_module(app_path, "agades_pqc_hf_space_launch_smoke")
        demo = module.build_demo()
        config = demo.get_config_file()
    except Exception as exc:  # noqa: BLE001 - launch smoke must report UI failures.
        failures.append(f"Hugging Face Space launch smoke failed: {exc}")
    else:
        api_names = _api_names_from_gradio_config(config)
        gradio = {
            "available": True,
            "demo_class": type(demo).__name__,
            "title": config.get("title"),
            "component_count": len(config.get("components", [])),
        }
        api = {
            "api_names": api_names,
            "required_api_names_present": all(
                name in api_names for name in _REQUIRED_API_NAMES
            ),
            "agent_environment_api_names_present": all(
                name in api_names for name in _AGENT_ENVIRONMENT_API_NAMES
            ),
        }

    safety = dict.fromkeys(_LAUNCH_FALSE_SAFETY_FLAGS, False)
    _validate_launch_smoke_contract(gradio, api, backend_smoke, safety, failures)
    return {
        "schema_version": HF_SPACE_LAUNCH_SMOKE_SCHEMA,
        "accepted": not failures,
        "gradio": gradio,
        "api": api,
        "backend_smoke": backend_smoke,
        "safety": safety,
        "failures": failures,
    }


def write_huggingface_space_launch_smoke_report(
    out: Path = DEFAULT_LAUNCH_REPORT,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    report = build_huggingface_space_launch_smoke_report(root=root)
    resolved_out = _resolve_path(out, root=root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_huggingface_space_launch_smoke_report(
    report_path: Path = DEFAULT_LAUNCH_REPORT,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    expected = build_huggingface_space_launch_smoke_report(root=project_root)
    failures: list[str] = []
    report = _read_launch_report(
        _resolve_path(report_path, root=project_root),
        failures,
    )

    if report != expected:
        failures.append("Hugging Face Space launch smoke report is not in sync.")
    _verify_launch_schema(report, failures)
    _verify_launch_gradio(report, failures)
    _verify_launch_api(report, failures)
    _verify_launch_backend_smoke(report, failures)
    _verify_launch_safety(report, failures)

    return {
        "schema_version": HF_SPACE_LAUNCH_SMOKE_VERIFICATION_SCHEMA,
        "report_path": _display_path(report_path, root=project_root),
        "accepted": not failures,
        "summary": _launch_verification_summary(report, failures),
        "failures": failures,
    }


def _validate_smoke_contract(
    app: dict[str, Any],
    examples: dict[str, Any],
    evaluation: dict[str, Any],
    agent_environment: dict[str, Any],
    unsupported_behavior: dict[str, Any],
    reward_summary: str,
    failures: list[str],
) -> None:
    if app["imports_without_gradio"] is not True:
        failures.append("Hugging Face Space app did not import without Gradio.")
    if app["uses_shared_verifier"] is not True:
        failures.append("Hugging Face Space app does not use the shared verifier.")
    if app["uses_rl_environment"] is not True:
        failures.append("Hugging Face Space app does not expose the RL environment.")
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
    if agent_environment["observation_schema"] != "agades.pqc.rl.observation.v1":
        failures.append("Hugging Face Space Agent Environment observation drifted.")
    if agent_environment["reward_report_schema"] != "agades.pqc.rl.reward_report.v1":
        failures.append("Hugging Face Space Agent Environment reward schema drifted.")
    if agent_environment["rollout_trace_schema"] != "agades.pqc.rl.rollout_trace.v1":
        failures.append("Hugging Face Space Agent Environment trace schema drifted.")
    if agent_environment["has_prompt"] is not True:
        failures.append("Hugging Face Space Agent Environment lacks a task prompt.")
    if agent_environment["reward"] != 1.0:
        failures.append("Hugging Face Space Agent Environment default reward failed.")
    if agent_environment["task_match"] != 1.0:
        failures.append("Hugging Face Space Agent Environment task match failed.")
    if agent_environment["trace_public_release_ok"] is not True:
        failures.append("Hugging Face Space Agent Environment trace is not public.")
    if agent_environment["private_fields_present"] is not False:
        failures.append("Hugging Face Space Agent Environment exposes private fields.")
    if agent_environment["claims_pqc_break"] is not False:
        failures.append("Hugging Face Space Agent Environment claims a PQC break.")
    if "not a security claim" not in reward_summary:
        failures.append("Hugging Face Space Agent Environment summary lacks boundary.")
    if unsupported_behavior["invalid_json_evaluation_summary_has_reason"] is not True:
        failures.append("Hugging Face Space invalid JSON summary lacks reason.")
    if unsupported_behavior["invalid_json_reward_summary_has_reason"] is not True:
        failures.append("Hugging Face Space invalid JSON reward lacks reason.")
    if (
        unsupported_behavior["unsupported_family_evaluation_summary_has_reason"]
        is not True
    ):
        failures.append("Hugging Face Space unsupported family summary lacks reason.")
    if unsupported_behavior["unsupported_family_reward_summary_has_reason"] is not True:
        failures.append("Hugging Face Space unsupported family reward lacks reason.")
    if unsupported_behavior["unsupported_family_accepted"] is not False:
        failures.append("Hugging Face Space unsupported family must not be accepted.")
    if unsupported_behavior["unsupported_family_reward"] != 0.0:
        failures.append("Hugging Face Space unsupported family reward must be zero.")


def _validate_launch_smoke_contract(
    gradio: dict[str, Any],
    api: dict[str, Any],
    backend_smoke: dict[str, Any],
    safety: dict[str, Any],
    failures: list[str],
) -> None:
    if gradio["available"] is not True:
        failures.append("Hugging Face Space launch smoke requires Gradio.")
    if gradio["demo_class"] != "Blocks":
        failures.append("Hugging Face Space launch smoke did not build Blocks.")
    if gradio["title"] != "Agades PQC Gym":
        failures.append("Hugging Face Space launch smoke title drifted.")
    if gradio["component_count"] < 1:
        failures.append("Hugging Face Space launch smoke has no components.")
    if api["required_api_names_present"] is not True:
        failures.append("Hugging Face Space launch smoke API names drifted.")
    if api["agent_environment_api_names_present"] is not True:
        failures.append(
            "Hugging Face Space launch smoke lacks Agent Environment endpoints."
        )
    if backend_smoke["accepted"] is not True:
        failures.append("Hugging Face Space backend smoke is not accepted.")
    if backend_smoke["reward"] != 1.0:
        failures.append("Hugging Face Space launch smoke reward drifted.")
    if backend_smoke["trace_public_release_ok"] is not True:
        failures.append("Hugging Face Space launch smoke trace is not public.")
    if backend_smoke["claims_pqc_break"] is not False:
        failures.append("Hugging Face Space launch smoke claims a PQC break.")
    for flag in _LAUNCH_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            failures.append(f"Hugging Face Space launch smoke {flag} must be false.")


def _unsupported_behavior(
    *,
    module: Any,
    default_label: str,
    default_plan: str,
) -> dict[str, Any]:
    invalid_summary, _ = module.evaluate_attack_plan_json("{not json")
    invalid_reward_summary, _, _ = module.score_attack_plan_for_task(
        default_label,
        "{not json",
    )
    unsupported_plan = json.loads(default_plan)
    unsupported_plan["target"]["family"] = "NTRU"
    unsupported_raw = json.dumps(unsupported_plan)
    unsupported_summary, _ = module.evaluate_attack_plan_json(unsupported_raw)
    (
        unsupported_reward_summary,
        unsupported_reward_payload,
        _unsupported_trace_payload,
    ) = module.score_attack_plan_for_task(default_label, unsupported_raw)
    unsupported_reward = json.loads(unsupported_reward_payload)
    return {
        "invalid_json_evaluation_summary_has_reason": (
            "Invalid JSON" in invalid_summary
        ),
        "invalid_json_reward_summary_has_reason": (
            "Invalid JSON" in invalid_reward_summary
        ),
        "unsupported_family_evaluation_summary_has_reason": (
            "NTRU targets are schema_only" in unsupported_summary
        ),
        "unsupported_family_reward_summary_has_reason": (
            "NTRU targets are schema_only" in unsupported_reward_summary
        ),
        "unsupported_family_accepted": unsupported_reward.get("accepted"),
        "unsupported_family_reward": unsupported_reward.get("reward"),
    }


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


def _read_launch_report(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Hugging Face Space launch smoke report is missing: {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            "Hugging Face Space launch smoke report is invalid JSON at "
            f"line {exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("Hugging Face Space launch smoke report must be a JSON object.")
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
    if app.get("uses_rl_environment") is not True:
        failures.append(
            "Hugging Face Space smoke report does not expose the RL environment."
        )


def _verify_agent_environment(report: dict[str, Any], failures: list[str]) -> None:
    agent_environment = report.get("agent_environment")
    if not isinstance(agent_environment, dict):
        failures.append(
            "Hugging Face Space smoke report agent_environment must be an object."
        )
        return
    expected = {
        "observation_schema": "agades.pqc.rl.observation.v1",
        "reward_report_schema": "agades.pqc.rl.reward_report.v1",
        "rollout_trace_schema": "agades.pqc.rl.rollout_trace.v1",
        "has_prompt": True,
        "reward": 1.0,
        "task_match": 1.0,
        "trace_public_release_ok": True,
        "private_fields_present": False,
        "claims_pqc_break": False,
    }
    if agent_environment != expected:
        failures.append("Hugging Face Space smoke report Agent Environment drifted.")


def _verify_unsupported_behavior(
    report: dict[str, Any],
    failures: list[str],
) -> None:
    unsupported_behavior = report.get("unsupported_behavior")
    if not isinstance(unsupported_behavior, dict):
        failures.append(
            "Hugging Face Space smoke report unsupported_behavior must be an object."
        )
        return
    expected = {
        "invalid_json_evaluation_summary_has_reason": True,
        "invalid_json_reward_summary_has_reason": True,
        "unsupported_family_evaluation_summary_has_reason": True,
        "unsupported_family_reward_summary_has_reason": True,
        "unsupported_family_accepted": False,
        "unsupported_family_reward": 0.0,
    }
    if unsupported_behavior != expected:
        failures.append(
            "Hugging Face Space smoke report unsupported behavior drifted."
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


def _verify_launch_schema(report: dict[str, Any], failures: list[str]) -> None:
    if report.get("schema_version") != HF_SPACE_LAUNCH_SMOKE_SCHEMA:
        failures.append(
            "Hugging Face Space launch smoke report schema_version must be "
            f"{HF_SPACE_LAUNCH_SMOKE_SCHEMA}."
        )
    if report.get("accepted") is not True:
        failures.append("Hugging Face Space launch smoke report is not accepted.")


def _verify_launch_gradio(report: dict[str, Any], failures: list[str]) -> None:
    gradio = report.get("gradio")
    if not isinstance(gradio, dict):
        failures.append("Hugging Face Space launch smoke gradio must be an object.")
        return
    expected = {
        "available": True,
        "demo_class": "Blocks",
        "title": "Agades PQC Gym",
        "component_count": 22,
    }
    if gradio != expected:
        failures.append("Hugging Face Space launch smoke Gradio contract drifted.")


def _verify_launch_api(report: dict[str, Any], failures: list[str]) -> None:
    api = report.get("api")
    if not isinstance(api, dict):
        failures.append("Hugging Face Space launch smoke api must be an object.")
        return
    expected = {
        "api_names": list(_REQUIRED_API_NAMES),
        "required_api_names_present": True,
        "agent_environment_api_names_present": True,
    }
    if api != expected:
        failures.append("Hugging Face Space launch smoke API contract drifted.")


def _verify_launch_backend_smoke(
    report: dict[str, Any],
    failures: list[str],
) -> None:
    backend_smoke = report.get("backend_smoke")
    if not isinstance(backend_smoke, dict):
        failures.append(
            "Hugging Face Space launch smoke backend_smoke must be an object."
        )
        return
    expected = {
        "accepted": True,
        "default_label": "LWE / lattice_primal_usvp_toy_v1",
        "example_count": 79,
        "reward": 1.0,
        "trace_public_release_ok": True,
        "claims_pqc_break": False,
    }
    if backend_smoke != expected:
        failures.append("Hugging Face Space launch smoke backend contract drifted.")


def _verify_launch_safety(report: dict[str, Any], failures: list[str]) -> None:
    safety = report.get("safety")
    if not isinstance(safety, dict):
        failures.append("Hugging Face Space launch smoke safety must be an object.")
        return
    for flag in _LAUNCH_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            failures.append(f"Hugging Face Space launch smoke {flag} must be false.")


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
    app = report.get("app") if isinstance(report.get("app"), dict) else {}
    return {
        "default_label": examples.get("default_label"),
        "example_count": examples.get("example_count"),
        "failure_count": len(failures),
        "imports_without_gradio": app.get("imports_without_gradio"),
        "summary_contains_not_security_claim": evaluation.get(
            "summary_contains_not_security_claim"
        ),
        "uses_rl_environment": app.get("uses_rl_environment"),
        "uses_shared_verifier": app.get("uses_shared_verifier"),
    }


def _launch_verification_summary(
    report: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    gradio = report.get("gradio") if isinstance(report.get("gradio"), dict) else {}
    api = report.get("api") if isinstance(report.get("api"), dict) else {}
    return {
        "agent_environment_api_names_present": api.get(
            "agent_environment_api_names_present"
        ),
        "component_count": gradio.get("component_count"),
        "demo_class": gradio.get("demo_class"),
        "failure_count": len(failures),
        "gradio_available": gradio.get("available"),
        "required_api_names_present": api.get("required_api_names_present"),
        "title": gradio.get("title"),
    }


def _load_python_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _api_names_from_gradio_config(config: dict[str, Any]) -> list[str]:
    dependencies = config.get("dependencies", [])
    if not isinstance(dependencies, list):
        return []
    api_names: list[str] = []
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            continue
        api_name = dependency.get("api_name")
        if isinstance(api_name, str) and api_name:
            api_names.append(api_name)
    return api_names


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
