from pathlib import Path

from typer.testing import CliRunner

from agades_lwe_gym.cli import app


def test_validate_command_accepts_valid_plan() -> None:
    result = CliRunner().invoke(
        app,
        ["validate", "examples/attack_plans/primal_usvp_toy.json"],
    )

    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_evaluate_export_and_report_commands(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    public_path = tmp_path / "public.jsonl"
    report_path = tmp_path / "report.md"
    runner = CliRunner()

    eval_result = runner.invoke(
        app,
        [
            "evaluate",
            "examples/attack_plans/primal_usvp_toy.json",
            "--out",
            str(trace_path),
        ],
    )
    export_result = runner.invoke(
        app,
        ["export-public", str(trace_path), "--out", str(public_path)],
    )
    report_result = runner.invoke(
        app,
        ["report", str(trace_path), "--out", str(report_path)],
    )

    assert eval_result.exit_code == 0
    assert export_result.exit_code == 0
    assert report_result.exit_code == 0
    assert trace_path.exists()
    assert public_path.exists()
    assert "Mock Vs Real Estimator Status" in report_path.read_text()

