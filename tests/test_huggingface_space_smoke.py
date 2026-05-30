from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.huggingface_space_smoke import (
    build_huggingface_space_launch_smoke_report,
    build_huggingface_space_smoke_report,
    verify_huggingface_space_launch_smoke_report,
    verify_huggingface_space_smoke_report,
    write_huggingface_space_launch_smoke_report,
    write_huggingface_space_smoke_report,
)


def test_huggingface_space_smoke_report_exercises_public_demo(
    tmp_path: Path,
) -> None:
    out = tmp_path / "hf_space_smoke.json"

    report = write_huggingface_space_smoke_report(out)

    assert report == build_huggingface_space_smoke_report()
    assert json.loads(out.read_text(encoding="utf-8")) == report
    assert report["schema_version"] == "agades.pqc.hf_space_smoke.v1"
    assert report["accepted"] is True
    assert report["app"] == {
        "app_path": "hf/app.py",
        "imports_without_gradio": True,
        "uses_rl_environment": True,
        "uses_shared_verifier": True,
    }
    assert report["examples"]["default_label"] == "LWE / lattice_primal_usvp_toy_v1"
    assert report["examples"]["example_count"] == 79
    assert report["examples"]["default_is_selectable"] is True
    assert report["evaluation"] == {
        "accepted": True,
        "combined_score": -80.9096,
        "evaluation_status": "ok",
        "summary_contains_not_security_claim": True,
        "target_family": "LWE",
        "security_claim": False,
    }
    assert report["agent_environment"] == {
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
    assert report["unsupported_behavior"] == {
        "invalid_json_evaluation_summary_has_reason": True,
        "invalid_json_reward_summary_has_reason": True,
        "unsupported_family_evaluation_summary_has_reason": True,
        "unsupported_family_reward_summary_has_reason": True,
        "unsupported_family_accepted": False,
        "unsupported_family_reward": 0.0,
    }
    assert report["safety"] == {
        "arbitrary_code_execution": False,
        "contains_private_traces": False,
        "live_targeting": False,
        "publishes_private_candidates": False,
        "security_claim": False,
    }
    assert report["release_gates"] == [
        "uv run pytest tests/test_huggingface_space_smoke.py -q",
        "uv run agades-pqc hf-space-smoke --out reports/hf_space_smoke.json",
        "uv run agades-pqc hf-space-smoke-verify --report "
        "reports/hf_space_smoke.json",
        "uv run agades-pqc hf-space-launch-smoke --out "
        "reports/hf_space_launch_smoke.json",
        "uv run agades-pqc hf-space-launch-smoke-verify --report "
        "reports/hf_space_launch_smoke.json",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]
    assert report["failures"] == []


def test_committed_huggingface_space_smoke_report_is_in_sync(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "hf_space_smoke.json"
    committed = Path("reports/hf_space_smoke.json")

    write_huggingface_space_smoke_report(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_huggingface_space_smoke_verify_accepts_committed_report() -> None:
    result = verify_huggingface_space_smoke_report(Path("reports/hf_space_smoke.json"))

    assert result == {
        "schema_version": "agades.pqc.hf_space_smoke_verification.v1",
        "report_path": "reports/hf_space_smoke.json",
        "accepted": True,
        "summary": {
            "default_label": "LWE / lattice_primal_usvp_toy_v1",
            "example_count": 79,
            "failure_count": 0,
            "imports_without_gradio": True,
            "summary_contains_not_security_claim": True,
            "uses_rl_environment": True,
            "uses_shared_verifier": True,
        },
        "failures": [],
    }


def test_huggingface_space_smoke_verify_rejects_stale_report(
    tmp_path: Path,
) -> None:
    out = tmp_path / "hf_space_smoke.json"
    report = build_huggingface_space_smoke_report()
    report["evaluation"]["security_claim"] = True
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    result = verify_huggingface_space_smoke_report(out)

    assert result["accepted"] is False
    assert "Hugging Face Space smoke report is not in sync." in result["failures"]
    assert "Hugging Face Space smoke report advertises a security claim." in result[
        "failures"
    ]


def test_huggingface_space_summaries_explain_invalid_and_unsupported_inputs() -> None:
    spec = importlib.util.spec_from_file_location("hf_app_test", Path("hf/app.py"))
    assert spec is not None
    assert spec.loader is not None
    hf_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hf_app)

    invalid_summary, _ = hf_app.evaluate_attack_plan_json("{not json")
    invalid_reward_summary, _, _ = hf_app.score_attack_plan_for_task(
        hf_app.DEFAULT_EXAMPLE_LABEL,
        "{not json",
    )
    unsupported_plan = json.loads(hf_app.DEFAULT_PLAN)
    unsupported_plan["target"]["family"] = "NTRU"
    unsupported_raw = json.dumps(unsupported_plan)

    unsupported_summary, _ = hf_app.evaluate_attack_plan_json(unsupported_raw)
    unsupported_reward_summary, _, _ = hf_app.score_attack_plan_for_task(
        hf_app.DEFAULT_EXAMPLE_LABEL,
        unsupported_raw,
    )

    assert "Invalid JSON" in invalid_summary
    assert "Invalid JSON" in invalid_reward_summary
    assert "NTRU targets are schema_only" in unsupported_summary
    assert "NTRU targets are schema_only" in unsupported_reward_summary
    assert "blocked=schema_valid" in unsupported_reward_summary
    assert "not a security claim" in unsupported_summary
    assert "not a security claim" in unsupported_reward_summary


def test_huggingface_space_score_handler_falls_back_when_runtime_step_raises(
    monkeypatch,
) -> None:
    spec = importlib.util.spec_from_file_location(
        "hf_app_fallback_test",
        Path("hf/app.py"),
    )
    assert spec is not None
    assert spec.loader is not None
    hf_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hf_app)

    class RaisingEnvironment:
        def __init__(self, tasks: list[dict[str, object]]) -> None:
            self.tasks = tasks

        def reset(self) -> dict[str, object]:
            return {"task": self.tasks[0]}

        def step(self, candidate_json: str) -> dict[str, object]:
            raise RuntimeError("private runtime traceback should not be exposed")

    monkeypatch.setattr(hf_app, "AgadesPQCGymEnvironment", RaisingEnvironment)

    summary, reward_payload, trace_payload = hf_app.score_attack_plan_for_task(
        hf_app.DEFAULT_EXAMPLE_LABEL,
        "{not json",
    )

    reward = json.loads(reward_payload)
    trace = json.loads(trace_payload)
    assert reward["accepted"] is False
    assert reward["reward"] == 0.0
    assert "Invalid JSON" in summary
    assert "private runtime traceback" not in summary
    assert trace["schema_version"] == "agades.pqc.rl.rollout_trace.v1"
    assert trace["public_release_ok"] is True
    assert trace["private_fields_present"] is False
    assert trace["claim_boundary"]["claims_pqc_break"] is False


def test_huggingface_space_smoke_cli_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "hf_space_smoke.json"

    result = CliRunner().invoke(app, ["hf-space-smoke", "--out", str(out)])

    assert result.exit_code == 0
    assert f"hf_space_smoke={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["accepted"] is True


def test_huggingface_space_smoke_verify_cli_accepts_current_report() -> None:
    result = CliRunner().invoke(
        app,
        ["hf-space-smoke-verify", "--report", "reports/hf_space_smoke.json"],
    )

    assert result.exit_code == 0
    assert "agades.pqc.hf_space_smoke_verification.v1" in result.output
    assert '"accepted": true' in result.output


def test_huggingface_space_launch_smoke_builds_gradio_agent_environment(
    tmp_path: Path,
) -> None:
    out = tmp_path / "hf_space_launch_smoke.json"

    report = write_huggingface_space_launch_smoke_report(out)

    assert report == build_huggingface_space_launch_smoke_report()
    assert json.loads(out.read_text(encoding="utf-8")) == report
    assert report["schema_version"] == "agades.pqc.hf_space_launch_smoke.v1"
    assert report["accepted"] is True
    assert report["gradio"] == {
        "available": True,
        "demo_class": "Blocks",
        "title": "Agades PQC Gym",
        "component_count": 22,
    }
    assert report["api"] == {
        "api_names": [
            "load_example_plan",
            "evaluate_attack_plan_json",
            "load_example_plan_1",
            "load_environment_observation",
            "score_attack_plan_for_task",
        ],
        "required_api_names_present": True,
        "agent_environment_api_names_present": True,
    }
    assert report["backend_smoke"] == {
        "accepted": True,
        "default_label": "LWE / lattice_primal_usvp_toy_v1",
        "example_count": 79,
        "reward": 1.0,
        "trace_public_release_ok": True,
        "claims_pqc_break": False,
    }
    assert report["safety"] == {
        "contains_private_traces": False,
        "publishes_private_candidates": False,
        "security_claim": False,
    }
    assert report["failures"] == []


def test_huggingface_space_launch_smoke_verify_accepts_committed_report() -> None:
    result = verify_huggingface_space_launch_smoke_report(
        Path("reports/hf_space_launch_smoke.json")
    )

    assert result == {
        "schema_version": "agades.pqc.hf_space_launch_smoke_verification.v1",
        "report_path": "reports/hf_space_launch_smoke.json",
        "accepted": True,
        "summary": {
            "agent_environment_api_names_present": True,
            "component_count": 22,
            "demo_class": "Blocks",
            "failure_count": 0,
            "gradio_available": True,
            "required_api_names_present": True,
            "title": "Agades PQC Gym",
        },
        "failures": [],
    }


def test_huggingface_space_launch_smoke_cli_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "hf_space_launch_smoke.json"

    result = CliRunner().invoke(app, ["hf-space-launch-smoke", "--out", str(out)])

    assert result.exit_code == 0
    assert f"hf_space_launch_smoke={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["accepted"] is True


def test_huggingface_space_launch_smoke_verify_cli_accepts_current_report() -> None:
    result = CliRunner().invoke(
        app,
        [
            "hf-space-launch-smoke-verify",
            "--report",
            "reports/hf_space_launch_smoke.json",
        ],
    )

    assert result.exit_code == 0
    assert "agades.pqc.hf_space_launch_smoke_verification.v1" in result.output
    assert '"accepted": true' in result.output
