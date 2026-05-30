from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

HF_SPACE_REMOTE_SMOKE_SCHEMA = "agades.pqc.hf_space_remote_smoke.v1"
HF_SPACE_REMOTE_SMOKE_VERIFICATION_SCHEMA = (
    "agades.pqc.hf_space_remote_smoke_verification.v1"
)
DEFAULT_REMOTE_SPACE_ID = "agades/agades-pqc-gym-agent-env"
DEFAULT_REMOTE_REPORT = Path("reports/hf_space_remote_smoke.json")
DEFAULT_LABEL = "LWE / lattice_primal_usvp_toy_v1"
DEFAULT_UNSUPPORTED_LABEL = "NTRU / lattice_ntru_schema_placeholder_v1"


class SpaceInfoApi(Protocol):
    def space_info(self, space_id: str) -> Any: ...


class SpaceClient(Protocol):
    def predict(self, *args: object, api_name: str) -> object: ...


def build_huggingface_space_remote_smoke_report(
    space_id: str = DEFAULT_REMOTE_SPACE_ID,
    *,
    api: SpaceInfoApi | None = None,
    client: SpaceClient | None = None,
    token_present: bool | None = None,
    label: str = DEFAULT_LABEL,
) -> dict[str, Any]:
    """Smoke-test the deployed private HF Space without recording secrets."""
    failures: list[str] = []
    token: str | None = None
    if token_present is None or api is None or client is None:
        token = _load_hf_token(failures)
    if token_present is None:
        token_present = bool(token)
    if api is None:
        api = _build_hf_api(failures)
    if client is None:
        client = _build_gradio_client(space_id, token=token, failures=failures)

    space = _space_summary(space_id)
    api_summary = {
        "load_example_plan": False,
        "evaluate_attack_plan_json": False,
        "load_environment_observation": False,
        "score_attack_plan_for_task": False,
        "agent_environment_api_names_present": False,
    }
    accepted_path = _empty_path_summary()
    invalid_json_path = _empty_path_summary()
    unsupported_path = _empty_path_summary()
    safety = {
        "records_token_value": False,
        "records_raw_attack_plan": False,
        "records_full_payloads": False,
        "security_claim": False,
        "private_fields_present": False,
    }

    if api is not None:
        space = _inspect_space(api, space_id, failures)
    if space["private"] is not True:
        failures.append("Hugging Face Space must be private.")
    if space["runtime_stage"] != "RUNNING":
        failures.append("Hugging Face Space runtime must be RUNNING.")
    if space["domain_ready"] is not True:
        failures.append("Hugging Face Space domain must be READY.")
    if token_present is not True:
        failures.append("Hugging Face auth token must be available for private Space.")

    if client is not None:
        (
            api_summary,
            accepted_path,
            invalid_json_path,
            unsupported_path,
            path_failures,
        ) = _exercise_agent_environment(client, label)
        failures.extend(path_failures)

    if _any_security_claim(accepted_path, invalid_json_path, unsupported_path):
        safety["security_claim"] = True
        failures.append("Remote Space response must not contain a security claim.")
    if _any_private_fields(accepted_path, invalid_json_path, unsupported_path):
        safety["private_fields_present"] = True
        failures.append("Remote Space trace exposes private fields.")

    report = {
        "schema_version": HF_SPACE_REMOTE_SMOKE_SCHEMA,
        "accepted": not failures,
        "space": space,
        "auth": {
            "token_present": bool(token_present),
            "token_value_recorded": False,
        },
        "api": api_summary,
        "accepted_path": accepted_path,
        "invalid_json_path": invalid_json_path,
        "unsupported_path": unsupported_path,
        "safety": safety,
        "failures": failures,
    }
    return report


def write_huggingface_space_remote_smoke_report(
    out: Path = DEFAULT_REMOTE_REPORT,
    *,
    space_id: str = DEFAULT_REMOTE_SPACE_ID,
) -> dict[str, Any]:
    report = build_huggingface_space_remote_smoke_report(space_id)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def verify_huggingface_space_remote_smoke_report(
    report: dict[str, Any] | Path = DEFAULT_REMOTE_REPORT,
) -> dict[str, Any]:
    failures: list[str] = []
    payload = _read_report(report, failures)

    if payload.get("schema_version") != HF_SPACE_REMOTE_SMOKE_SCHEMA:
        failures.append("Remote smoke report schema_version is invalid.")
    if payload.get("accepted") is not True:
        failures.append("Remote smoke report is not accepted.")
    space = _dict_or_empty(payload.get("space"))
    if space.get("private") is not True:
        failures.append("Remote Hugging Face Space is not private.")
    if space.get("runtime_stage") != "RUNNING":
        failures.append("Remote Hugging Face Space is not RUNNING.")
    if space.get("domain_ready") is not True:
        failures.append("Remote Hugging Face Space domain is not READY.")
    auth = _dict_or_empty(payload.get("auth"))
    if auth.get("token_value_recorded") is not False:
        failures.append("Remote smoke report must not record token values.")
    api = _dict_or_empty(payload.get("api"))
    if api.get("agent_environment_api_names_present") is not True:
        failures.append("Remote Agent Environment API endpoints are missing.")
    _verify_accepted_path(_dict_or_empty(payload.get("accepted_path")), failures)
    _verify_rejected_path(
        _dict_or_empty(payload.get("invalid_json_path")),
        "invalid_json_path",
        "invalid",
        failures,
    )
    _verify_rejected_path(
        _dict_or_empty(payload.get("unsupported_path")),
        "unsupported_path",
        "unsupported",
        failures,
    )
    safety = _dict_or_empty(payload.get("safety"))
    for key in (
        "records_token_value",
        "records_raw_attack_plan",
        "records_full_payloads",
        "security_claim",
        "private_fields_present",
    ):
        if safety.get(key) is not False:
            failures.append(f"Remote smoke safety flag {key} must be false.")

    return {
        "schema_version": HF_SPACE_REMOTE_SMOKE_VERIFICATION_SCHEMA,
        "accepted": not failures,
        "summary": {
            "space_id": space.get("id"),
            "runtime_stage": space.get("runtime_stage"),
            "domain_ready": space.get("domain_ready"),
            "failure_count": len(failures),
        },
        "failures": failures,
    }


def _exercise_agent_environment(
    client: SpaceClient,
    label: str,
) -> tuple[dict[str, bool], dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    failures: list[str] = []
    api = {
        "load_example_plan": False,
        "evaluate_attack_plan_json": False,
        "load_environment_observation": False,
        "score_attack_plan_for_task": False,
        "agent_environment_api_names_present": False,
    }
    accepted_path = _empty_path_summary()
    invalid_json_path = _empty_path_summary()
    unsupported_path = _empty_path_summary()

    plan = _safe_predict(client, label, api_name="/load_example_plan")
    if not isinstance(plan.value, str) or not plan.value.strip().startswith("{"):
        failures.append("Remote Space did not return an example AttackPlan JSON.")
        return api, accepted_path, invalid_json_path, unsupported_path, failures
    api["load_example_plan"] = True

    accepted_path = _evaluate_and_score(client, label, plan.value, failures)
    api["evaluate_attack_plan_json"] = accepted_path["evaluation_ran"]
    api["load_environment_observation"] = accepted_path["observation_ran"]
    api["score_attack_plan_for_task"] = accepted_path["score_ran"]
    api["agent_environment_api_names_present"] = (
        api["load_environment_observation"] and api["score_attack_plan_for_task"]
    )

    invalid_json_path = _evaluate_and_score(client, label, "{not json", failures)
    unsupported_label, unsupported_plan = _load_unsupported_example(
        client,
        fallback_label=label,
        fallback_plan=plan.value,
    )
    unsupported_path = _evaluate_and_score(
        client,
        unsupported_label,
        unsupported_plan,
        failures,
    )
    _validate_paths(accepted_path, invalid_json_path, unsupported_path, failures)
    return api, accepted_path, invalid_json_path, unsupported_path, failures


def _evaluate_and_score(
    client: SpaceClient,
    label: str,
    raw_plan: str,
    failures: list[str],
) -> dict[str, Any]:
    path = _empty_path_summary()
    evaluation = _safe_predict(
        client,
        raw_plan,
        api_name="/evaluate_attack_plan_json",
    )
    if evaluation.error is None:
        path["evaluation_ran"] = True
        summary, payload = _tuple2(evaluation.value)
        verifier = _loads_json(payload)
        path["evaluation_summary_has_no_claim"] = _has_no_claim_summary(summary)
        path["evaluation_status"] = verifier.get("evaluation_status")
        path["evaluated_accepted"] = verifier.get("accepted")

    observation = _safe_predict(
        client,
        label,
        api_name="/load_environment_observation",
    )
    if observation.error is None:
        path["observation_ran"] = True
        observed = _loads_json(str(observation.value))
        path["observation_schema"] = observed.get("schema_version")
        path["has_prompt"] = bool(observed.get("prompt"))

    score = _safe_predict(
        client,
        label,
        raw_plan,
        api_name="/score_attack_plan_for_task",
    )
    if score.error is None:
        path["score_ran"] = True
        summary, reward_payload, trace_payload = _tuple3(score.value)
        reward = _loads_json(reward_payload)
        trace = _loads_json(trace_payload)
        path["reward_summary_has_no_claim"] = _has_no_claim_summary(summary)
        path["accepted"] = reward.get("accepted")
        path["reward"] = reward.get("reward")
        path["blocking_reasons"] = reward.get("blocking_reasons")
        path["trace_schema"] = trace.get("schema_version")
        path["public_release_ok"] = trace.get("public_release_ok")
        path["private_fields_present"] = trace.get("private_fields_present")
        path["claims_pqc_break"] = _dict_or_empty(trace.get("claim_boundary")).get(
            "claims_pqc_break"
        )

    for call in (evaluation, observation, score):
        if call.error is not None:
            failures.append(call.error)
    return path


def _validate_paths(
    accepted_path: dict[str, Any],
    invalid_json_path: dict[str, Any],
    unsupported_path: dict[str, Any],
    failures: list[str],
) -> None:
    if accepted_path["evaluated_accepted"] is not True:
        failures.append("Remote accepted example evaluation must be accepted.")
    if accepted_path["accepted"] is not True or accepted_path["reward"] != 1.0:
        failures.append("Remote accepted example reward must be 1.0.")
    if accepted_path["observation_schema"] != "agades.pqc.rl.observation.v1":
        failures.append("Remote observation schema is invalid.")
    if accepted_path["has_prompt"] is not True:
        failures.append("Remote observation must include an agent prompt.")
    _validate_rejected_remote_path(
        invalid_json_path,
        "invalid JSON",
        "invalid",
        failures,
    )
    _validate_rejected_remote_path(
        unsupported_path,
        "unsupported",
        "unsupported",
        failures,
    )


def _validate_rejected_remote_path(
    path: dict[str, Any],
    label: str,
    expected_status: str,
    failures: list[str],
) -> None:
    if path["evaluated_accepted"] is not False:
        failures.append(f"Remote {label} evaluation must be rejected.")
    if path["evaluation_status"] != expected_status:
        failures.append(
            f"Remote {label} evaluation_status must be {expected_status}."
        )
    if path["accepted"] is not False or path["reward"] != 0.0:
        failures.append(f"Remote {label} reward must be 0.0.")
    if path["public_release_ok"] is not True:
        failures.append(f"Remote {label} trace must be public-release safe.")


def _verify_accepted_path(path: dict[str, Any], failures: list[str]) -> None:
    if path.get("evaluated_accepted") is not True:
        failures.append("Accepted path evaluation is not accepted.")
    if path.get("accepted") is not True:
        failures.append("Accepted path reward report is not accepted.")
    if path.get("reward") != 1.0:
        failures.append("Accepted path reward must be 1.0.")
    if path.get("observation_schema") != "agades.pqc.rl.observation.v1":
        failures.append("Accepted path observation schema is invalid.")
    if path.get("trace_schema") != "agades.pqc.rl.rollout_trace.v1":
        failures.append("Accepted path trace schema is invalid.")


def _verify_rejected_path(
    path: dict[str, Any],
    path_name: str,
    expected_status: str,
    failures: list[str],
) -> None:
    if path.get("evaluated_accepted") is not False:
        failures.append(f"{path_name} evaluation must be rejected.")
    if path.get("evaluation_status") != expected_status:
        failures.append(f"{path_name} evaluation_status must be {expected_status}.")
    if path.get("accepted") is not False:
        failures.append(f"{path_name} reward report must be rejected.")
    if path.get("reward") != 0.0:
        failures.append(f"{path_name} reward must be 0.0.")
    if path.get("public_release_ok") is not True:
        failures.append(f"{path_name} trace must be public-release safe.")


def _inspect_space(
    api: SpaceInfoApi,
    space_id: str,
    failures: list[str],
) -> dict[str, Any]:
    summary = _space_summary(space_id)
    try:
        info = api.space_info(space_id)
    except Exception as exc:  # noqa: BLE001 - report remote API diagnostics.
        failures.append(f"Hugging Face Space info failed: {_safe_error(exc)}")
        return summary
    runtime = getattr(info, "runtime", None)
    summary["private"] = getattr(info, "private", None)
    summary["runtime_stage"] = getattr(runtime, "stage", None)
    summary["domain_ready"] = _domain_ready(runtime)
    summary["sha"] = getattr(info, "sha", None) or getattr(runtime, "sha", None)
    return summary


def _domain_ready(runtime: object) -> bool | None:
    raw = getattr(runtime, "raw", None)
    if not isinstance(raw, dict):
        return None
    domains = raw.get("domains")
    if not isinstance(domains, list):
        return None
    return any(
        isinstance(domain, dict) and domain.get("stage") == "READY"
        for domain in domains
    )


def _load_unsupported_example(
    client: SpaceClient,
    *,
    fallback_label: str,
    fallback_plan: str,
) -> tuple[str, str]:
    unsupported = _safe_predict(
        client,
        DEFAULT_UNSUPPORTED_LABEL,
        api_name="/load_example_plan",
    )
    if isinstance(unsupported.value, str) and unsupported.value.strip().startswith("{"):
        return DEFAULT_UNSUPPORTED_LABEL, unsupported.value
    return fallback_label, _unsupported_family_candidate(fallback_plan)


def _unsupported_family_candidate(raw_plan: str) -> str:
    try:
        payload = json.loads(raw_plan)
    except json.JSONDecodeError:
        return raw_plan
    target = payload.get("target")
    if isinstance(target, dict):
        target["family"] = "NTRU"
    return json.dumps(payload, sort_keys=True)


def _any_security_claim(*paths: dict[str, Any]) -> bool:
    return any(
        path.get("claims_pqc_break") is True
        or path.get("evaluation_summary_has_no_claim") is False
        or path.get("reward_summary_has_no_claim") is False
        for path in paths
    )


def _any_private_fields(*paths: dict[str, Any]) -> bool:
    return any(path.get("private_fields_present") is True for path in paths)


class _Prediction:
    def __init__(self, value: object = None, error: str | None = None) -> None:
        self.value = value
        self.error = error


def _safe_predict(
    client: SpaceClient,
    *args: object,
    api_name: str,
) -> _Prediction:
    try:
        return _Prediction(client.predict(*args, api_name=api_name))
    except Exception as exc:  # noqa: BLE001 - remote smoke captures diagnostics.
        return _Prediction(error=f"{api_name} failed: {_safe_error(exc)}")


def _tuple2(value: object) -> tuple[str, str]:
    if isinstance(value, tuple) and len(value) == 2:
        return str(value[0]), str(value[1])
    if isinstance(value, list) and len(value) == 2:
        return str(value[0]), str(value[1])
    return "", "{}"


def _tuple3(value: object) -> tuple[str, str, str]:
    if isinstance(value, tuple) and len(value) == 3:
        return str(value[0]), str(value[1]), str(value[2])
    if isinstance(value, list) and len(value) == 3:
        return str(value[0]), str(value[1]), str(value[2])
    return "", "{}", "{}"


def _loads_json(payload: str) -> dict[str, Any]:
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _has_no_claim_summary(summary: str) -> bool:
    lowered = summary.lower()
    return "not a security claim" in lowered and "pqc break" not in lowered


def _read_report(report: dict[str, Any] | Path, failures: list[str]) -> dict[str, Any]:
    if isinstance(report, dict):
        return report
    try:
        payload = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"Remote smoke report could not be read: {_safe_error(exc)}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _space_summary(space_id: str) -> dict[str, Any]:
    return {
        "id": space_id,
        "private": None,
        "runtime_stage": None,
        "domain_ready": None,
        "sha": None,
    }


def _empty_path_summary() -> dict[str, Any]:
    return {
        "evaluation_ran": False,
        "evaluation_summary_has_no_claim": False,
        "evaluation_status": None,
        "evaluated_accepted": None,
        "observation_ran": False,
        "observation_schema": None,
        "has_prompt": False,
        "score_ran": False,
        "reward_summary_has_no_claim": False,
        "accepted": None,
        "reward": None,
        "blocking_reasons": None,
        "trace_schema": None,
        "public_release_ok": None,
        "private_fields_present": None,
        "claims_pqc_break": None,
    }


def _dict_or_empty(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _load_hf_token(failures: list[str]) -> str | None:
    try:
        from huggingface_hub import get_token
    except ImportError:
        failures.append("huggingface_hub is required for remote Space smoke.")
        return None
    return get_token()


def _build_hf_api(failures: list[str]) -> SpaceInfoApi | None:
    try:
        from huggingface_hub import HfApi
    except ImportError:
        failures.append("huggingface_hub is required for remote Space smoke.")
        return None
    return HfApi()


def _build_gradio_client(
    space_id: str,
    *,
    token: str | None,
    failures: list[str],
) -> SpaceClient | None:
    try:
        from gradio_client import Client
    except ImportError:
        failures.append("gradio_client is required for remote Space smoke.")
        return None
    try:
        return Client(space_id, token=token, verbose=False)
    except Exception as exc:  # noqa: BLE001 - capture remote client diagnostics.
        failures.append(f"Gradio client creation failed: {_safe_error(exc)}")
        return None


def _safe_error(exc: Exception) -> str:
    message = str(exc).strip()
    if not message:
        return exc.__class__.__name__
    return message
