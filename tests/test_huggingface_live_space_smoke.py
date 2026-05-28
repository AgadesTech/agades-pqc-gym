from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.huggingface_live_space_smoke import (
    build_huggingface_live_space_smoke_report,
    verify_huggingface_live_space_smoke_report,
)


def test_huggingface_live_space_smoke_uses_gradio_call_api(
    monkeypatch,
) -> None:
    monkeypatch.setenv("HF_TOKEN", "hf_secret_for_test")
    runner = FakeGradioRunner()

    report = build_huggingface_live_space_smoke_report(
        space_url="https://example-space.hf.space",
        use_token_cache=False,
        request_runner=runner,
    )

    assert report["accepted"] is True
    assert report["schema_version"] == "agades.pqc.hf_live_space_smoke.v1"
    assert report["auth"] == {
        "token_available": True,
        "token_env": "HF_TOKEN",
        "token_source": "env",
    }
    assert report["routes"] == {
        "call_route_template": "/gradio_api/call/<api_name>",
        "legacy_run_route_used": False,
    }
    assert report["config"]["api_prefix"] == "/gradio_api"
    assert report["config"]["required_api_names_present"] is True
    assert report["evaluation"]["evaluation_status"] == "ok"
    assert report["score"]["reward"] == 1.0
    assert report["unsupported_score"]["reward"] == 0.0
    assert "/run/" not in " ".join(call["url"] for call in runner.calls)
    assert all(
        "/gradio_api/call/" in call["url"] or call["url"].endswith("/config")
        for call in runner.calls
    )
    assert "hf_secret_for_test" not in json.dumps(report)


def test_huggingface_live_space_smoke_verify_accepts_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("HF_TOKEN", "hf_secret_for_test")
    report_path = tmp_path / "hf_live_space_smoke.json"
    report = build_huggingface_live_space_smoke_report(
        space_url="https://example-space.hf.space",
        use_token_cache=False,
        request_runner=FakeGradioRunner(),
    )
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    result = verify_huggingface_live_space_smoke_report(report_path)

    assert result == {
        "schema_version": "agades.pqc.hf_live_space_smoke_verification.v1",
        "report_path": str(report_path),
        "accepted": True,
        "summary": {
            "space_url": "https://example-space.hf.space",
            "api_prefix": "/gradio_api",
            "protocol": "sse_v3",
            "failure_count": 0,
            "token_available": True,
            "evaluation_status": "ok",
            "score_reward": 1.0,
            "unsupported_reward": 0.0,
        },
        "failures": [],
    }


def test_huggingface_live_space_smoke_verify_rejects_legacy_route(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("HF_TOKEN", "hf_secret_for_test")
    report_path = tmp_path / "hf_live_space_smoke.json"
    report = build_huggingface_live_space_smoke_report(
        space_url="https://example-space.hf.space",
        use_token_cache=False,
        request_runner=FakeGradioRunner(),
    )
    report["routes"]["legacy_run_route_used"] = True
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    result = verify_huggingface_live_space_smoke_report(report_path)

    assert result["accepted"] is False
    assert "Hugging Face live Space smoke report used legacy /run route." in result[
        "failures"
    ]


class FakeGradioRunner:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self._events: dict[str, list[Any]] = {}

    def __call__(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: float,
    ) -> str:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "body": body,
                "timeout": timeout,
            }
        )
        if url.endswith("/config"):
            return json.dumps(
                {
                    "api_prefix": "/gradio_api",
                    "protocol": "sse_v3",
                    "version": "6.15.1",
                    "dependencies": [
                        {"api_name": "evaluate_attack_plan_json"},
                        {"api_name": "load_environment_observation"},
                        {"api_name": "score_attack_plan_for_task"},
                    ],
                }
            )
        if method == "POST" and "/gradio_api/call/" in url:
            api_name = url.rsplit("/", 1)[-1]
            event_id = f"evt_{len(self._events)}"
            self._events[event_id] = self._payload_for(api_name, body)
            return json.dumps({"event_id": event_id})
        if method == "GET" and "/gradio_api/call/" in url:
            event_id = url.rsplit("/", 1)[-1]
            return "event: complete\n" + (
                "data: " + json.dumps(self._events[event_id]) + "\n\n"
            )
        raise AssertionError(f"unexpected request: {method} {url}")

    def _payload_for(self, api_name: str, body: bytes | None) -> list[Any]:
        request = json.loads((body or b"{}").decode("utf-8"))
        if api_name == "evaluate_attack_plan_json":
            return [
                "LWE: ok; score=-80.9096. Toy/demo output only; not a security claim.",
                json.dumps(
                    {
                        "accepted": True,
                        "evaluation_status": "ok",
                        "safety": {"security_claim": False},
                        "target_family": "LWE",
                    }
                ),
            ]
        if api_name == "load_environment_observation":
            return [
                json.dumps(
                    {
                        "schema_version": "agades.pqc.rl.observation.v1",
                        "prompt": [{"role": "system", "content": "Return JSON."}],
                    }
                )
            ]
        if api_name == "score_attack_plan_for_task":
            expected_accepted = "code_based_isd_placeholder" not in request["data"][1]
            reward = 1.0 if expected_accepted else 0.0
            return [
                (
                    f"reward={reward}; accepted={str(expected_accepted).lower()}; "
                    "review_governance=accepted. Toy/demo Agent Environment output "
                    "only; not a security claim."
                ),
                json.dumps(
                    {
                        "schema_version": "agades.pqc.rl.reward_report.v1",
                        "reward": reward,
                        "accepted": expected_accepted,
                    }
                ),
                json.dumps(
                    {
                        "schema_version": "agades.pqc.rl.rollout_trace.v1",
                        "formal_artifact_binding": {
                            "review_governance_ok": True,
                        },
                        "private_fields_present": False,
                        "claim_boundary": {"claims_pqc_break": False},
                    }
                ),
            ]
        raise AssertionError(f"unexpected api_name: {api_name}")
