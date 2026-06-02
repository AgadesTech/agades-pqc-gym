from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.huggingface_space_remote_smoke import (
    build_huggingface_space_remote_smoke_report,
    verify_huggingface_space_remote_smoke_report,
)


@dataclass
class FakeRuntime:
    stage: str = "RUNNING"
    raw: dict[str, object] | None = field(
        default_factory=lambda: {"domains": [{"stage": "READY"}]}
    )
    sha: str = "remote-sha"


@dataclass
class FakeSpaceInfo:
    id: str = "AgadesTech/agades-pqc-gym-agent-env"
    private: bool = True
    runtime: FakeRuntime = field(default_factory=FakeRuntime)
    sha: str = "remote-sha"


class FakeApi:
    def __init__(self, info: FakeSpaceInfo) -> None:
        self.info = info

    def space_info(self, space_id: str) -> FakeSpaceInfo:
        assert space_id == self.info.id
        return self.info


class FakeClient:
    def __init__(self) -> None:
        self.plan = json.dumps(
            {
                "attack_plan_id": "lattice_primal_usvp_toy_v1",
                "target": {"family": "LWE"},
            }
        )
        self.unsupported_plan = json.dumps(
            {
                "attack_plan_id": "lattice_ntru_schema_placeholder_v1",
                "target": {"family": "NTRU"},
            }
        )

    def predict(self, *args: object, api_name: str) -> object:
        if api_name == "/load_example_plan":
            if args and args[0] == "NTRU / lattice_ntru_schema_placeholder_v1":
                return self.unsupported_plan
            return self.plan
        if api_name == "/evaluate_attack_plan_json":
            raw = str(args[0])
            if raw == "{not json":
                return (
                    "Invalid AttackPlan JSON: invalid. Toy/demo output only; "
                    "not a security claim.",
                    json.dumps({"accepted": False, "evaluation_status": "invalid"}),
                )
            if '"NTRU"' in raw:
                return (
                    "NTRU: unsupported; score=n/a. "
                    "Toy/demo output only; not a security claim.",
                    json.dumps({"accepted": False, "evaluation_status": "unsupported"}),
                )
            return (
                "LWE: ok; score=-80.9096. Toy/demo output only; "
                "not a security claim.",
                json.dumps(
                    {
                        "accepted": True,
                        "evaluation_status": "ok",
                        "target_family": "LWE",
                    }
                ),
            )
        if api_name == "/load_environment_observation":
            return json.dumps(
                {
                    "schema_version": "agades.pqc.rl.observation.v1",
                    "prompt": [{"role": "system", "content": "json only"}],
                    "task": {"target_family": "LWE"},
                }
            )
        if api_name == "/score_attack_plan_for_task":
            raw = str(args[1])
            accepted = raw not in {"{not json"} and '"NTRU"' not in raw
            summary = (
                "reward=1.0; accepted=true; reason=accepted. "
                "Toy/demo Agent Environment output only; not a security claim."
                if accepted
                else "reward=0.0; accepted=false; reason=Invalid JSON. "
                "Toy/demo Agent Environment output only; not a security claim."
            )
            return (
                summary,
                json.dumps(
                    {
                        "schema_version": "agades.pqc.rl.reward_report.v1",
                        "accepted": accepted,
                        "reward": 1.0 if accepted else 0.0,
                        "blocking_reasons": [] if accepted else ["schema_valid"],
                    }
                ),
                json.dumps(
                    {
                        "schema_version": "agades.pqc.rl.rollout_trace.v1",
                        "public_release_ok": True,
                        "private_fields_present": False,
                        "claim_boundary": {"claims_pqc_break": False},
                    }
                ),
            )
        raise AssertionError(f"unexpected api_name: {api_name}")


class FakeInvalidUnsupportedClient(FakeClient):
    def predict(self, *args: object, api_name: str) -> object:
        if api_name == "/evaluate_attack_plan_json" and '"NTRU"' in str(args[0]):
            return (
                "Invalid AttackPlan JSON: NTRU candidate malformed. "
                "Toy/demo output only; not a security claim.",
                json.dumps({"accepted": False, "evaluation_status": "invalid"}),
            )
        return super().predict(*args, api_name=api_name)


def test_remote_smoke_accepts_private_running_agent_environment() -> None:
    report = build_huggingface_space_remote_smoke_report(
        "AgadesTech/agades-pqc-gym-agent-env",
        api=FakeApi(FakeSpaceInfo()),
        client=FakeClient(),
        token_present=True,
    )

    assert report["schema_version"] == "agades.pqc.hf_space_remote_smoke.v1"
    assert report["accepted"] is True
    assert report["space"] == {
        "id": "AgadesTech/agades-pqc-gym-agent-env",
        "private": True,
        "runtime_stage": "RUNNING",
        "domain_ready": True,
        "sha": "remote-sha",
    }
    assert report["auth"] == {"token_present": True, "token_value_recorded": False}
    assert report["api"]["agent_environment_api_names_present"] is True
    assert report["accepted_path"]["reward"] == 1.0
    assert report["invalid_json_path"]["accepted"] is False
    assert report["unsupported_path"]["reward"] == 0.0
    assert report["unsupported_path"]["evaluation_status"] == "unsupported"
    assert report["safety"] == {
        "records_token_value": False,
        "records_raw_attack_plan": False,
        "records_full_payloads": False,
        "security_claim": False,
        "private_fields_present": False,
    }
    assert report["failures"] == []


def test_remote_smoke_rejects_invalid_status_for_unsupported_path() -> None:
    report = build_huggingface_space_remote_smoke_report(
        "AgadesTech/agades-pqc-gym-agent-env",
        api=FakeApi(FakeSpaceInfo()),
        client=FakeInvalidUnsupportedClient(),
        token_present=True,
    )

    assert report["accepted"] is False
    assert "Remote unsupported evaluation_status must be unsupported." in report[
        "failures"
    ]


def test_remote_smoke_rejects_non_private_space() -> None:
    report = build_huggingface_space_remote_smoke_report(
        "AgadesTech/agades-pqc-gym-agent-env",
        api=FakeApi(FakeSpaceInfo(private=False)),
        client=FakeClient(),
        token_present=True,
    )

    assert report["accepted"] is False
    assert "Hugging Face Space must be private." in report["failures"]


def test_remote_smoke_verify_rejects_missing_required_api() -> None:
    report = build_huggingface_space_remote_smoke_report(
        "AgadesTech/agades-pqc-gym-agent-env",
        api=FakeApi(FakeSpaceInfo()),
        client=FakeClient(),
        token_present=True,
    )
    report["api"]["agent_environment_api_names_present"] = False

    result = verify_huggingface_space_remote_smoke_report(report)

    assert result["accepted"] is False
    assert "Remote Agent Environment API endpoints are missing." in result["failures"]


def test_remote_smoke_cli_writes_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    out = tmp_path / "hf_space_remote_smoke.json"

    def fake_write(out_path: Path, *, space_id: str) -> dict[str, object]:
        assert out_path == out
        assert space_id == "AgadesTech/agades-pqc-gym-agent-env"
        report = build_huggingface_space_remote_smoke_report(
            space_id,
            api=FakeApi(FakeSpaceInfo()),
            client=FakeClient(),
            token_present=True,
        )
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        return report

    monkeypatch.setattr(
        "agades_pqc_gym.cli.write_huggingface_space_remote_smoke_report",
        fake_write,
    )

    result = CliRunner().invoke(
        app,
        [
            "hf-space-remote-smoke",
            "--space-id",
            "AgadesTech/agades-pqc-gym-agent-env",
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 0
    assert f"hf_space_remote_smoke={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["accepted"] is True
