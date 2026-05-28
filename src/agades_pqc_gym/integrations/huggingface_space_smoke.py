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
        "reviewer_quality": None,
        "review_governance_ok": False,
        "review_governance_binding_schema": None,
        "summary_contains_review_governance": False,
        "task_match": None,
        "trace_public_release_ok": False,
        "private_fields_present": None,
        "claims_pqc_break": None,
    }
    example_runtime = {
        "checked_example_count": 0,
        "ok_count": 0,
        "unsupported_count": 0,
        "other_status_count": 0,
        "rewarded_count": 0,
        "blocked_reward_count": 0,
        "failure_count": 0,
        "all_observations_have_prompt": False,
        "all_traces_public_release_ok": False,
        "all_private_fields_absent": False,
        "all_claims_pqc_break_false": False,
        "failures": [],
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
        example_runtime = _exercise_all_examples(module, choices)
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
            "reviewer_quality": reward_report.get("terms", {}).get(
                "reviewer_quality"
            ),
            "review_governance_ok": _dict_or_empty(
                trace.get("formal_artifact_binding")
            ).get("review_governance_ok"),
            "review_governance_binding_schema": _dict_or_empty(
                _dict_or_empty(trace.get("formal_artifact_binding")).get(
                    "review_governance"
                )
            ).get("schema_version"),
            "summary_contains_review_governance": (
                "review_governance=accepted" in reward_summary
            ),
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
            reward_summary,
            failures,
        )
        _validate_example_runtime(examples, example_runtime, failures)

    safety = dict.fromkeys(_FALSE_SAFETY_FLAGS, False)
    return {
        "schema_version": HF_SPACE_SMOKE_SCHEMA,
        "accepted": not failures,
        "app": app,
        "agent_environment": agent_environment,
        "example_runtime": example_runtime,
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
    _verify_example_runtime(report, failures)
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
    agent_environment: dict[str, Any],
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
    if agent_environment["reviewer_quality"] != 1.0:
        failures.append(
            "Hugging Face Space Agent Environment reviewer quality failed."
        )
    if agent_environment["review_governance_ok"] is not True:
        failures.append(
            "Hugging Face Space Agent Environment lacks reviewer governance."
        )
    if agent_environment["review_governance_binding_schema"] != (
        "agades.pqc.formal.proof_artifact.reviewer_governance_binding.v1"
    ):
        failures.append(
            "Hugging Face Space Agent Environment reviewer governance schema drifted."
        )
    if agent_environment["summary_contains_review_governance"] is not True:
        failures.append(
            "Hugging Face Space Agent Environment summary hides reviewer governance."
        )
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


def _exercise_all_examples(module: Any, choices: list[str]) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    checked_example_count = 0
    ok_count = 0
    unsupported_count = 0
    other_status_count = 0
    rewarded_count = 0
    blocked_reward_count = 0
    all_observations_have_prompt = True
    all_traces_public_release_ok = True
    all_private_fields_absent = True
    all_claims_pqc_break_false = True

    for label in choices:
        checked_example_count += 1
        try:
            raw_plan = module.load_example_plan(label)
            _, verifier_payload = module.evaluate_attack_plan_json(raw_plan)
            observation_payload = module.load_environment_observation(label)
            _, reward_payload, trace_payload = module.score_attack_plan_for_task(
                label,
                raw_plan,
            )
            verifier_result = json.loads(verifier_payload)
            observation = json.loads(observation_payload)
            reward_report = json.loads(reward_payload)
            trace = json.loads(trace_payload)
        except Exception as exc:  # noqa: BLE001 - smoke report must capture app issues.
            failures.append(
                {
                    "label": label,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
            continue

        status = verifier_result.get("evaluation_status")
        if status == "ok":
            ok_count += 1
        elif status == "unsupported":
            unsupported_count += 1
        else:
            other_status_count += 1

        if reward_report.get("accepted") is True:
            rewarded_count += 1
        else:
            blocked_reward_count += 1

        all_observations_have_prompt = (
            all_observations_have_prompt and bool(observation.get("prompt"))
        )
        all_traces_public_release_ok = (
            all_traces_public_release_ok and trace.get("public_release_ok") is True
        )
        all_private_fields_absent = (
            all_private_fields_absent
            and trace.get("private_fields_present") is False
        )
        all_claims_pqc_break_false = (
            all_claims_pqc_break_false
            and _dict_or_empty(trace.get("claim_boundary")).get("claims_pqc_break")
            is False
        )

    return {
        "checked_example_count": checked_example_count,
        "ok_count": ok_count,
        "unsupported_count": unsupported_count,
        "other_status_count": other_status_count,
        "rewarded_count": rewarded_count,
        "blocked_reward_count": blocked_reward_count,
        "failure_count": len(failures),
        "all_observations_have_prompt": all_observations_have_prompt,
        "all_traces_public_release_ok": all_traces_public_release_ok,
        "all_private_fields_absent": all_private_fields_absent,
        "all_claims_pqc_break_false": all_claims_pqc_break_false,
        "failures": failures,
    }


def _validate_example_runtime(
    examples: dict[str, Any],
    example_runtime: dict[str, Any],
    failures: list[str],
) -> None:
    if example_runtime.get("checked_example_count") != examples.get("example_count"):
        failures.append("Hugging Face Space did not exercise every public example.")
    if example_runtime.get("failure_count") != 0:
        failures.append("Hugging Face Space example runtime has failures.")
    if not _positive_count(example_runtime.get("ok_count")):
        failures.append("Hugging Face Space has no accepted example path.")
    if not _positive_count(example_runtime.get("unsupported_count")):
        failures.append("Hugging Face Space has no unsupported example path.")
    if example_runtime.get("other_status_count") != 0:
        failures.append("Hugging Face Space example runtime has unknown statuses.")
    if not _positive_count(example_runtime.get("rewarded_count")):
        failures.append("Hugging Face Space has no positive-reward example.")
    if not _positive_count(example_runtime.get("blocked_reward_count")):
        failures.append("Hugging Face Space has no blocked-reward safety example.")
    if example_runtime.get("all_observations_have_prompt") is not True:
        failures.append("Hugging Face Space example observations lack prompts.")
    if example_runtime.get("all_traces_public_release_ok") is not True:
        failures.append("Hugging Face Space example traces are not public-safe.")
    if example_runtime.get("all_private_fields_absent") is not True:
        failures.append("Hugging Face Space example traces expose private fields.")
    if example_runtime.get("all_claims_pqc_break_false") is not True:
        failures.append("Hugging Face Space example traces claim PQC breaks.")


def _positive_count(value: Any) -> bool:
    return isinstance(value, int) and value >= 1


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
        "reviewer_quality": 1.0,
        "review_governance_ok": True,
        "review_governance_binding_schema": (
            "agades.pqc.formal.proof_artifact.reviewer_governance_binding.v1"
        ),
        "summary_contains_review_governance": True,
        "task_match": 1.0,
        "trace_public_release_ok": True,
        "private_fields_present": False,
        "claims_pqc_break": False,
    }
    if agent_environment != expected:
        failures.append("Hugging Face Space smoke report Agent Environment drifted.")


def _verify_example_runtime(report: dict[str, Any], failures: list[str]) -> None:
    example_runtime = report.get("example_runtime")
    examples = report.get("examples")
    if not isinstance(example_runtime, dict):
        failures.append(
            "Hugging Face Space smoke report example_runtime must be an object."
        )
        return
    if not isinstance(examples, dict):
        failures.append(
            "Hugging Face Space smoke report examples must be an object."
        )
        return
    _validate_example_runtime(examples, example_runtime, failures)
    if example_runtime.get("failures") != []:
        failures.append(
            "Hugging Face Space smoke report example_runtime failures must be empty."
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
    app = report.get("app") if isinstance(report.get("app"), dict) else {}
    return {
        "default_label": examples.get("default_label"),
        "example_count": examples.get("example_count"),
        "example_runtime_failures": (
            report.get("example_runtime", {}).get("failure_count")
            if isinstance(report.get("example_runtime"), dict)
            else None
        ),
        "failure_count": len(failures),
        "imports_without_gradio": app.get("imports_without_gradio"),
        "summary_contains_not_security_claim": evaluation.get(
            "summary_contains_not_security_claim"
        ),
        "uses_rl_environment": app.get("uses_rl_environment"),
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


def _dict_or_empty(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
