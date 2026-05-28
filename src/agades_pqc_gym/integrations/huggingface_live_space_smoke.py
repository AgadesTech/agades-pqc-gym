from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HF_LIVE_SPACE_SMOKE_SCHEMA = "agades.pqc.hf_live_space_smoke.v1"
HF_LIVE_SPACE_SMOKE_VERIFICATION_SCHEMA = (
    "agades.pqc.hf_live_space_smoke_verification.v1"
)
DEFAULT_SPACE_URL = "https://agades-agades-pqc-gym-agent-env.hf.space"
DEFAULT_REPORT = Path("reports/hf_live_space_smoke.json")
DEFAULT_TOKEN_ENV = "HF_TOKEN"
ROOT = Path(__file__).resolve().parents[3]
REQUIRED_API_NAMES = (
    "evaluate_attack_plan_json",
    "load_environment_observation",
    "score_attack_plan_for_task",
)

RequestRunner = Callable[
    [str, str, Mapping[str, str], bytes | None, float],
    str,
]


def build_huggingface_live_space_smoke_report(
    *,
    space_url: str = DEFAULT_SPACE_URL,
    token_env: str = DEFAULT_TOKEN_ENV,
    use_token_cache: bool = True,
    timeout: float = 60.0,
    root: Path | None = None,
    request_runner: RequestRunner | None = None,
) -> dict[str, Any]:
    """Exercise a deployed private HF Space through the current Gradio API."""
    project_root = (root or ROOT).resolve()
    runner = request_runner or _urlopen_text
    token_resolution = _resolve_hf_token(
        token_env=token_env,
        use_token_cache=use_token_cache,
    )
    headers = _auth_headers(token_resolution["token"])
    failures: list[str] = []

    config_report: dict[str, Any] = {
        "ok": False,
        "api_prefix": None,
        "protocol": None,
        "version": None,
        "required_api_names_present": False,
        "api_names": [],
    }
    route_report: dict[str, Any] = {
        "call_route_template": None,
        "legacy_run_route_used": False,
    }
    evaluation_report: dict[str, Any] = _empty_endpoint_report()
    observation_report: dict[str, Any] = _empty_endpoint_report()
    score_report: dict[str, Any] = _empty_endpoint_report()
    unsupported_report: dict[str, Any] = _empty_endpoint_report()

    try:
        client = _GradioSseClient(
            space_url=space_url,
            headers=headers,
            timeout=timeout,
            request_runner=runner,
        )
        config = client.fetch_config()
        api_names = _api_names(config)
        api_prefix = _api_prefix(config)
        route_report = {
            "call_route_template": f"{api_prefix}/call/<api_name>",
            "legacy_run_route_used": False,
        }
        config_report = {
            "ok": True,
            "api_prefix": api_prefix,
            "protocol": config.get("protocol"),
            "version": config.get("version"),
            "required_api_names_present": all(
                api_name in api_names for api_name in REQUIRED_API_NAMES
            ),
            "api_names": api_names,
        }
        _validate_config(config_report, failures)

        default_plan = _read_example(
            project_root / "examples" / "attack_plans" / "lattice_primal_usvp_toy.json"
        )
        unsupported_plan = _read_example(
            project_root
            / "examples"
            / "attack_plans"
            / "code_based_isd_placeholder.json"
        )
        default_label = "LWE / lattice_primal_usvp_toy_v1"

        evaluation_report = _exercise_evaluation(client, default_plan)
        observation_report = _exercise_observation(client, default_label)
        score_report = _exercise_score(client, default_label, default_plan)
        unsupported_report = _exercise_unsupported_score(
            client,
            default_label,
            unsupported_plan,
        )
        _validate_endpoint_reports(
            evaluation_report=evaluation_report,
            observation_report=observation_report,
            score_report=score_report,
            unsupported_report=unsupported_report,
            failures=failures,
        )
    except Exception as exc:  # noqa: BLE001 - live smoke must capture deployment failures.
        failures.append(f"Hugging Face live Space smoke failed: {exc}")

    return {
        "schema_version": HF_LIVE_SPACE_SMOKE_SCHEMA,
        "accepted": not failures,
        "space_url": space_url.rstrip("/"),
        "auth": {
            "token_env": token_env,
            "token_available": token_resolution["available"],
            "token_source": token_resolution["source"],
        },
        "config": config_report,
        "routes": route_report,
        "evaluation": evaluation_report,
        "observation": observation_report,
        "score": score_report,
        "unsupported_score": unsupported_report,
        "safety": {
            "contains_token_value": False,
            "contains_private_traces": False,
            "publishes_private_candidates": False,
            "security_claim": False,
        },
        "failures": failures,
    }


def write_huggingface_live_space_smoke_report(
    out: Path = DEFAULT_REPORT,
    *,
    space_url: str = DEFAULT_SPACE_URL,
    token_env: str = DEFAULT_TOKEN_ENV,
    use_token_cache: bool = True,
    timeout: float = 60.0,
    root: Path | None = None,
) -> dict[str, Any]:
    report = build_huggingface_live_space_smoke_report(
        space_url=space_url,
        token_env=token_env,
        use_token_cache=use_token_cache,
        timeout=timeout,
        root=root,
    )
    resolved_out = _resolve_path(out, root=root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_huggingface_live_space_smoke_report(
    report_path: Path = DEFAULT_REPORT,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    report = _read_report(_resolve_path(report_path, root=project_root), failures)
    _verify_report(report, failures)
    return {
        "schema_version": HF_LIVE_SPACE_SMOKE_VERIFICATION_SCHEMA,
        "report_path": _display_path(report_path, root=project_root),
        "accepted": not failures,
        "summary": {
            "space_url": report.get("space_url"),
            "api_prefix": _dict_or_empty(report.get("config")).get("api_prefix"),
            "protocol": _dict_or_empty(report.get("config")).get("protocol"),
            "failure_count": len(failures),
            "token_available": _dict_or_empty(report.get("auth")).get(
                "token_available"
            ),
            "evaluation_status": _dict_or_empty(report.get("evaluation")).get(
                "evaluation_status"
            ),
            "score_reward": _dict_or_empty(report.get("score")).get("reward"),
            "unsupported_reward": _dict_or_empty(
                report.get("unsupported_score")
            ).get("reward"),
        },
        "failures": failures,
    }


class _GradioSseClient:
    def __init__(
        self,
        *,
        space_url: str,
        headers: Mapping[str, str],
        timeout: float,
        request_runner: RequestRunner,
    ) -> None:
        self._space_url = space_url.rstrip("/")
        self._headers = dict(headers)
        self._timeout = timeout
        self._request_runner = request_runner
        self._api_prefix: str | None = None

    def fetch_config(self) -> dict[str, Any]:
        payload = self._request_json("GET", f"{self._space_url}/config")
        self._api_prefix = _api_prefix(payload)
        return payload

    def call(self, api_name: str, data: list[Any]) -> list[Any]:
        api_prefix = self._api_prefix or "/gradio_api"
        start = self._request_json(
            "POST",
            f"{self._space_url}{api_prefix}/call/{api_name}",
            payload={"data": data},
        )
        event_id = start.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            raise ValueError(f"Gradio call did not return an event_id for {api_name}")
        stream = self._request_text(
            "GET",
            f"{self._space_url}{api_prefix}/call/{api_name}/{event_id}",
            accept="text/event-stream",
        )
        result = _parse_sse_complete(stream)
        if not isinstance(result, list):
            raise ValueError(f"Gradio call {api_name} returned non-list data")
        return result

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = self._request_text(method, url, payload=payload)
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"invalid JSON response from {url}: line {exc.lineno}"
            ) from exc
        if not isinstance(decoded, dict):
            raise ValueError(f"JSON response from {url} must be an object")
        return decoded

    def _request_text(
        self,
        method: str,
        url: str,
        *,
        payload: dict[str, Any] | None = None,
        accept: str = "application/json",
    ) -> str:
        body = None
        headers = dict(self._headers)
        headers["Accept"] = accept
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload).encode("utf-8")
        return self._request_runner(method, url, headers, body, self._timeout)


def _exercise_evaluation(client: _GradioSseClient, raw_plan: str) -> dict[str, Any]:
    data = client.call("evaluate_attack_plan_json", [raw_plan])
    if len(data) != 2:
        raise ValueError("evaluate_attack_plan_json returned an unexpected shape")
    verifier = _json_object(data[1], "verifier JSON")
    safety = _dict_or_empty(verifier.get("safety"))
    return {
        "ok": True,
        "evaluation_status": verifier.get("evaluation_status"),
        "accepted": verifier.get("accepted"),
        "summary_contains_not_security_claim": "not a security claim" in str(data[0]),
        "security_claim": safety.get("security_claim"),
        "target_family": verifier.get("target_family"),
    }


def _exercise_observation(client: _GradioSseClient, label: str) -> dict[str, Any]:
    data = client.call("load_environment_observation", [label])
    if len(data) != 1:
        raise ValueError("load_environment_observation returned an unexpected shape")
    observation = _json_object(data[0], "observation JSON")
    return {
        "ok": True,
        "schema_version": observation.get("schema_version"),
        "has_prompt": bool(observation.get("prompt")),
    }


def _exercise_score(
    client: _GradioSseClient,
    label: str,
    raw_plan: str,
) -> dict[str, Any]:
    data = client.call("score_attack_plan_for_task", [label, raw_plan])
    return _score_endpoint_report(data, expected_accepted=True)


def _exercise_unsupported_score(
    client: _GradioSseClient,
    label: str,
    raw_plan: str,
) -> dict[str, Any]:
    data = client.call("score_attack_plan_for_task", [label, raw_plan])
    return _score_endpoint_report(data, expected_accepted=False)


def _score_endpoint_report(
    data: list[Any],
    *,
    expected_accepted: bool,
) -> dict[str, Any]:
    if len(data) != 3:
        raise ValueError("score_attack_plan_for_task returned an unexpected shape")
    reward = _json_object(data[1], "reward JSON")
    trace = _json_object(data[2], "trace JSON")
    formal_binding = _dict_or_empty(trace.get("formal_artifact_binding"))
    claim_boundary = _dict_or_empty(trace.get("claim_boundary"))
    return {
        "ok": True,
        "reward": reward.get("reward"),
        "accepted": reward.get("accepted"),
        "expected_accepted": expected_accepted,
        "reward_schema": reward.get("schema_version"),
        "trace_schema": trace.get("schema_version"),
        "summary_contains_not_security_claim": "not a security claim" in str(data[0]),
        "review_governance_ok": formal_binding.get("review_governance_ok"),
        "private_fields_present": trace.get("private_fields_present"),
        "claims_pqc_break": claim_boundary.get("claims_pqc_break"),
    }


def _validate_config(config: dict[str, Any], failures: list[str]) -> None:
    if config["ok"] is not True:
        failures.append("Hugging Face live Space config was not fetched.")
    if config["api_prefix"] != "/gradio_api":
        failures.append("Hugging Face live Space does not expose /gradio_api.")
    if config["required_api_names_present"] is not True:
        failures.append("Hugging Face live Space is missing required named APIs.")


def _validate_endpoint_reports(
    *,
    evaluation_report: dict[str, Any],
    observation_report: dict[str, Any],
    score_report: dict[str, Any],
    unsupported_report: dict[str, Any],
    failures: list[str],
) -> None:
    if evaluation_report.get("evaluation_status") != "ok":
        failures.append("Hugging Face live Space default evaluation is not ok.")
    if evaluation_report.get("accepted") is not True:
        failures.append("Hugging Face live Space default evaluation is not accepted.")
    if evaluation_report.get("summary_contains_not_security_claim") is not True:
        failures.append("Hugging Face live Space evaluation lacks safety wording.")
    if evaluation_report.get("security_claim") is not False:
        failures.append("Hugging Face live Space evaluation makes a security claim.")
    if observation_report.get("schema_version") != "agades.pqc.rl.observation.v1":
        failures.append("Hugging Face live Space observation schema drifted.")
    if observation_report.get("has_prompt") is not True:
        failures.append("Hugging Face live Space observation lacks prompt.")
    _validate_score_report(score_report, expected_accepted=True, failures=failures)
    _validate_score_report(
        unsupported_report,
        expected_accepted=False,
        failures=failures,
    )
    if unsupported_report.get("reward") != 0.0:
        failures.append("Hugging Face live Space unsupported example is rewarded.")


def _validate_score_report(
    report: dict[str, Any],
    *,
    expected_accepted: bool,
    failures: list[str],
) -> None:
    label = "default" if expected_accepted else "unsupported"
    if report.get("accepted") is not expected_accepted:
        failures.append(f"Hugging Face live Space {label} score acceptance drifted.")
    if expected_accepted and report.get("reward") != 1.0:
        failures.append("Hugging Face live Space default score reward failed.")
    if report.get("reward_schema") != "agades.pqc.rl.reward_report.v1":
        failures.append(f"Hugging Face live Space {label} reward schema drifted.")
    if report.get("trace_schema") != "agades.pqc.rl.rollout_trace.v1":
        failures.append(f"Hugging Face live Space {label} trace schema drifted.")
    if report.get("summary_contains_not_security_claim") is not True:
        failures.append(f"Hugging Face live Space {label} score lacks boundary.")
    if report.get("review_governance_ok") is not True:
        failures.append(
            f"Hugging Face live Space {label} score lacks reviewer governance."
        )
    if report.get("private_fields_present") is not False:
        failures.append(f"Hugging Face live Space {label} score exposes private data.")
    if report.get("claims_pqc_break") is not False:
        failures.append(f"Hugging Face live Space {label} score claims a PQC break.")


def _verify_report(report: dict[str, Any], failures: list[str]) -> None:
    if report.get("schema_version") != HF_LIVE_SPACE_SMOKE_SCHEMA:
        failures.append(
            "Hugging Face live Space smoke report schema_version must be "
            f"{HF_LIVE_SPACE_SMOKE_SCHEMA}."
        )
    if report.get("accepted") is not True:
        failures.append("Hugging Face live Space smoke report is not accepted.")
    auth = _dict_or_empty(report.get("auth"))
    if auth.get("token_available") is not True:
        failures.append("Hugging Face live Space smoke report lacks private auth.")
    routes = _dict_or_empty(report.get("routes"))
    if routes.get("call_route_template") != "/gradio_api/call/<api_name>":
        failures.append("Hugging Face live Space smoke report uses wrong API route.")
    if routes.get("legacy_run_route_used") is not False:
        failures.append("Hugging Face live Space smoke report used legacy /run route.")
    config = _dict_or_empty(report.get("config"))
    _validate_config(config, failures)
    _validate_endpoint_reports(
        evaluation_report=_dict_or_empty(report.get("evaluation")),
        observation_report=_dict_or_empty(report.get("observation")),
        score_report=_dict_or_empty(report.get("score")),
        unsupported_report=_dict_or_empty(report.get("unsupported_score")),
        failures=failures,
    )
    safety = _dict_or_empty(report.get("safety"))
    for key in (
        "contains_token_value",
        "contains_private_traces",
        "publishes_private_candidates",
        "security_claim",
    ):
        if safety.get(key) is not False:
            failures.append(
                f"Hugging Face live Space smoke report {key} must be false."
            )


def _auth_headers(token: str | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _resolve_hf_token(*, token_env: str, use_token_cache: bool) -> dict[str, Any]:
    token = os.environ.get(token_env, "").strip() if token_env else ""
    if token:
        return {"available": True, "source": "env", "token": token}
    if use_token_cache:
        token_path = _hf_token_cache_path()
        if token_path.is_file():
            cached = token_path.read_text(encoding="utf-8").strip()
            if cached:
                return {"available": True, "source": "cache", "token": cached}
    return {"available": False, "source": "missing", "token": None}


def _hf_token_cache_path() -> Path:
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        return Path(hf_home).expanduser() / "token"
    return Path.home() / ".cache" / "huggingface" / "token"


def _urlopen_text(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes | None,
    timeout: float,
) -> str:
    request = Request(url, data=body, headers=dict(headers), method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"{method} {url} failed with HTTP {exc.code}: {detail[:300]}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc.reason}") from exc


def _parse_sse_complete(stream: str) -> Any:
    for event in _parse_sse_events(stream):
        if event["event"] == "complete":
            data = event["data"]
            try:
                return json.loads(data)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Gradio complete event contained invalid JSON at line {exc.lineno}"
                ) from exc
        if event["event"] == "error":
            raise RuntimeError(f"Gradio returned an error event: {event['data']}")
    raise ValueError("Gradio SSE stream did not contain a complete event")


def _parse_sse_events(stream: str) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    for block in stream.split("\n\n"):
        if not block.strip():
            continue
        event_name = "message"
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith("event:"):
                event_name = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data_lines.append(line.split(":", 1)[1].strip())
        events.append({"event": event_name, "data": "\n".join(data_lines)})
    return events


def _api_prefix(config: Mapping[str, Any]) -> str:
    prefix = config.get("api_prefix")
    if isinstance(prefix, str) and prefix.startswith("/"):
        return prefix
    return "/gradio_api"


def _api_names(config: Mapping[str, Any]) -> list[str]:
    names: list[str] = []
    dependencies = config.get("dependencies")
    if not isinstance(dependencies, list):
        return names
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            continue
        api_name = dependency.get("api_name")
        if isinstance(api_name, str) and api_name:
            names.append(api_name)
    return names


def _read_example(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read example plan {path}") from exc


def _json_object(value: Any, label: str) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{label} is invalid JSON at line {exc.lineno}") from exc
    else:
        decoded = value
    if not isinstance(decoded, dict):
        raise ValueError(f"{label} must be a JSON object")
    return decoded


def _empty_endpoint_report() -> dict[str, Any]:
    return {"ok": False}


def _read_report(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Hugging Face live Space smoke report is missing: {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            "Hugging Face live Space smoke report is invalid JSON at "
            f"line {exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("Hugging Face live Space smoke report must be a JSON object.")
        return {}
    return payload


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
