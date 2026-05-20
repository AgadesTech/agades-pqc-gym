import json
import subprocess
import sys
import textwrap
from pathlib import Path

import yaml
from typer.testing import CliRunner

from agades_pqc_gym import cli
from agades_pqc_gym.cli import app
from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.evaluators.lattice_estimator import (
    LATTICE_ESTIMATOR_PINNED_COMMIT,
    LatticeEstimatorAdapter,
    LatticeEstimatorConfig,
)
from agades_pqc_gym.evolution.archive import write_evolution_archive
from agades_pqc_gym.integrations import lattice_estimator_baseline_run
from agades_pqc_gym.integrations.lattice_estimator_runtime_preflight import (
    write_lattice_estimator_runtime_preflight,
)
from agades_pqc_gym.integrations.private_run_policy import build_private_run_policy
from agades_pqc_gym.traces.schema import TraceRecord


def test_validate_command_accepts_valid_plan() -> None:
    result = CliRunner().invoke(
        app,
        ["validate", "examples/attack_plans/lattice_primal_usvp_toy.json"],
    )

    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_help_prioritizes_core_gym_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "quickstart" in result.output
    assert "validate" in result.output
    assert "evaluate" in result.output
    assert "benchmark" in result.output
    assert "report" in result.output
    assert "publication-manifest" not in result.output
    assert "lattice-estimator-baseline-review-packet-verify" not in result.output


def test_quickstart_command_runs_guided_gym_demo(tmp_path: Path) -> None:
    out_dir = tmp_path / "quickstart"

    result = CliRunner().invoke(
        app,
        [
            "quickstart",
            "--out-dir",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "quickstart complete" in result.output.lower()
    assert "lattice_primal_usvp_toy_v1" in result.output
    assert "unsupported example" in result.output.lower()
    assert (out_dir / "lattice_trace.jsonl").exists()
    assert (out_dir / "lattice_report.md").exists()
    assert (out_dir / "lattice_benchmark.jsonl").exists()
    assert (out_dir / "code_based_prange_trace.jsonl").exists()
    assert (out_dir / "unsupported_placeholder_trace.jsonl").exists()
    assert "Mock Vs Real Estimator Status" in (
        out_dir / "lattice_report.md"
    ).read_text(encoding="utf-8")


def test_evaluate_export_and_report_commands(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    public_path = tmp_path / "public.jsonl"
    report_path = tmp_path / "report.md"
    runner = CliRunner()

    eval_result = runner.invoke(
        app,
        [
            "evaluate",
            "examples/attack_plans/lattice_primal_usvp_toy.json",
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


def test_evaluate_command_explains_unsupported_results(tmp_path: Path) -> None:
    trace_path = tmp_path / "unsupported.jsonl"

    result = CliRunner().invoke(
        app,
        [
            "evaluate",
            "examples/attack_plans/code_based_isd_placeholder.json",
            "--out",
            str(trace_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "status=unsupported" in result.output
    assert "valid=False" in result.output
    assert "CODE_BASED evaluator is not implemented" in result.output
    assert trace_path.exists()


def test_verify_command_outputs_public_verifier_json() -> None:
    result = CliRunner().invoke(
        app,
        ["verify", "examples/attack_plans/lattice_primal_usvp_toy.json"],
    )

    assert result.exit_code == 0
    assert '"schema_version": "agades.pqc.verifier.v1"' in result.output
    assert '"evaluation_status": "ok"' in result.output


def test_openevolve_config_command_writes_private_loop_template(tmp_path: Path) -> None:
    out = tmp_path / "openevolve.yaml"

    result = CliRunner().invoke(
        app,
        ["openevolve-config", "--out", str(out)],
    )

    assert result.exit_code == 0, result.output
    assert f"openevolve_config={out}" in result.output
    config = yaml.safe_load(out.read_text())
    assert config["mutation_batch_schema"] == ("agades.pqc.candidate_mutation_batch.v1")
    assert config["paper_card_injection_schema"] == (
        "agades.pqc.paper_card_injection_batch.v1"
    )
    assert "agades-pqc deepevolve-injections" in config["paper_card_injection_command"]
    assert config["archive_schema"] == "agades.pqc.evolution_archive.v1"
    assert "agades-pqc mutate-archive" in config["archive_mutation_command"]
    assert config["archive_snapshot_schema"] == (
        "agades.pqc.private_archive_snapshot.v1"
    )
    assert "agades-pqc archive-snapshot" in config["archive_snapshot_command"]
    assert "agades-pqc heldout-review-log" in config["heldout_review_log_command"]
    assert "agades-pqc heldout-cron-plan" in config["heldout_cron_plan_command"]
    assert "agades-pqc heldout-batch" in config["heldout_batch_command"]
    assert "agades-pqc heldout-run-schedule" in config["heldout_run_schedule_command"]
    assert config["safety"]["arbitrary_code_execution"] is False
    assert config["safety"]["publishes_private_candidates"] is False
    assert config["safety"]["security_claim"] is False
    assert any("Python candidates" in note for note in config["notes"])


def test_openevolve_config_verify_command_accepts_checked_template(
    tmp_path: Path,
) -> None:
    out = tmp_path / "openevolve.yaml"
    runner = CliRunner()

    write_result = runner.invoke(app, ["openevolve-config", "--out", str(out)])
    verify_result = runner.invoke(
        app,
        ["openevolve-config-verify", "--config", str(out)],
    )

    assert write_result.exit_code == 0, write_result.output
    assert verify_result.exit_code == 0, verify_result.output
    verification = json.loads(verify_result.output)
    assert verification["schema_version"] == (
        "agades.pqc.openevolve_config_template_verification.v1"
    )
    assert verification["accepted"] is True
    assert verification["summary"]["checked_config_synced"] is True
    assert verification["summary"]["python_candidates_executed"] is False


def test_openevolve_smoke_command_writes_reproducible_report(tmp_path: Path) -> None:
    out = tmp_path / "openevolve_smoke.json"

    result = CliRunner().invoke(
        app,
        [
            "openevolve-smoke",
            "--out",
            str(out),
            "--plan",
            "examples/attack_plans/lattice_primal_usvp_toy.json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert f"openevolve_smoke={out}" in result.output
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["schema_version"] == "agades.pqc.openevolve_smoke.v1"
    assert report["accepted"] is True
    assert report["summary"] == {
        "combined_score": -80.9096,
        "evaluation_status": "ok",
        "failure_count": 0,
        "feature_attack_type": "primal_usvp",
        "feature_family": "LWE",
        "feature_memory_bucket": "low",
        "metric_count": 23,
        "primary_metric": "combined_score",
        "python_candidates_executed": False,
    }
    assert report["safety"] == {
        "arbitrary_code_execution": False,
        "python_candidates_executed": False,
        "security_claim": False,
    }
    assert report["metrics"]["fitness_schema_version"] == (
        "agades.pqc.fitness_report.v1"
    )


def test_openevolve_smoke_verify_command_accepts_checked_report(
    tmp_path: Path,
) -> None:
    out = tmp_path / "openevolve_smoke.json"
    runner = CliRunner()

    write_result = runner.invoke(app, ["openevolve-smoke", "--out", str(out)])
    verify_result = runner.invoke(
        app,
        ["openevolve-smoke-verify", "--report", str(out)],
    )

    assert write_result.exit_code == 0, write_result.output
    assert verify_result.exit_code == 0, verify_result.output
    verification = json.loads(verify_result.output)
    assert verification["schema_version"] == (
        "agades.pqc.openevolve_smoke_verification.v1"
    )
    assert verification["accepted"] is True
    assert verification["summary"]["checked_in_report_synced"] is True
    assert verification["summary"]["security_claim"] is False


def test_ecosystem_smoke_command_writes_local_oss_surface_report(
    tmp_path: Path,
) -> None:
    out = tmp_path / "ecosystem_smoke.json"

    result = CliRunner().invoke(app, ["ecosystem-smoke", "--out", str(out)])

    assert result.exit_code == 0, result.output
    assert f"ecosystem_smoke={out}" in result.output
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["schema_version"] == "agades.pqc.ecosystem_smoke.v1"
    assert report["accepted"] is True
    assert report["summary"]["prime_tasks"] == 79
    assert report["summary"]["hf_valid_attack_plan_rows"] == 79
    assert report["summary"]["nvidia_current_gpu_required_workloads"] == 0
    assert report["summary"]["external_publication_ready"] is False
    assert report["safety"]["external_publication_performed"] is False


def test_ecosystem_smoke_verify_command_reports_json() -> None:
    result = CliRunner().invoke(
        app,
        [
            "ecosystem-smoke-verify",
            "--report",
            "reports/ecosystem_smoke.json",
        ],
    )

    assert result.exit_code == 0, result.output
    verification = json.loads(result.output)
    assert verification["schema_version"] == (
        "agades.pqc.ecosystem_smoke_verification.v1"
    )
    assert verification["accepted"] is True
    assert verification["summary"]["checked_in_report_synced"] is True


class _CliBaselineBackend:
    version = "fake-cli-baseline-0.1"
    commit = LATTICE_ESTIMATOR_PINNED_COMMIT

    def make_binary_distribution(self) -> tuple[str]:
        return ("binary",)

    def make_sparse_binary_distribution(self, hamming_weight: int) -> tuple[str, int]:
        return ("sparse_binary", hamming_weight)

    def make_centered_binomial_distribution(self, eta: int) -> tuple[str, int]:
        return ("centered_binomial", eta)

    def make_discrete_gaussian_distribution(self, sigma: float) -> tuple[str, float]:
        return ("discrete_gaussian", sigma)

    def make_lwe_parameters(
        self,
        *,
        n: int,
        q: int,
        xs: object,
        xe: object,
        m: int,
        tag: str,
    ) -> dict[str, object]:
        return {"n": n, "q": q, "xs": xs, "xe": xe, "m": m, "tag": tag}

    def estimate_lwe(
        self,
        *,
        params: object,
        algorithm_key: str,
        red_cost_model: str | None,
        red_shape_model: str | None,
        jobs: int,
        catch_exceptions: bool,
    ) -> dict[str, object]:
        del params, red_cost_model, red_shape_model, jobs, catch_exceptions
        return {algorithm_key: {"rop": 57.25, "mem": 19.5, "beta": 72}}


def _clear_estimator_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "estimator" or module_name.startswith("estimator."):
            del sys.modules[module_name]


def _write_cli_fake_lattice_estimator_checkout(tmp_path: Path) -> tuple[Path, str]:
    source = tmp_path / "fake-cli-lattice-estimator"
    package = source / "estimator"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path

            Path(__file__).with_name("IMPORT_MARKER").write_text(
                "imported",
                encoding="utf-8",
            )
            __version__ = "fake-cli-checkout-0.1"

            class ND:
                Binary = ("binary",)

                @staticmethod
                def SparseBinary(hamming_weight):
                    return ("sparse_binary", hamming_weight)

                @staticmethod
                def CenteredBinomial(eta):
                    return ("centered_binomial", eta)

                @staticmethod
                def DiscreteGaussian(sigma):
                    return ("discrete_gaussian", sigma)

            class RC:
                ADPS16 = "ADPS16"

            class LWE:
                @staticmethod
                def Parameters(*, n, q, Xs, Xe, m, tag):
                    return {"n": n, "q": q, "Xs": Xs, "Xe": Xe, "m": m, "tag": tag}

                @staticmethod
                def estimate(params, **kwargs):
                    del params
                    algorithms = {
                        "arora-gb",
                        "bkw",
                        "usvp",
                        "bdd",
                        "bdd_hybrid",
                        "bdd_mitm_hybrid",
                        "dual",
                        "dual_hybrid",
                    }
                    algorithm_key = sorted(algorithms - set(kwargs["deny_list"]))[0]
                    return {algorithm_key: {"rop": 64.0, "mem": 22.0, "beta": 74}}
            """
        ).lstrip(),
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=source, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/malb/lattice-estimator"],
        cwd=source,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "add", "estimator/__init__.py"],
        cwd=source,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=tests@example.com",
            "-c",
            "user.name=Agades Tests",
            "commit",
            "-m",
            "Add fake CLI estimator package",
        ],
        cwd=source,
        check=True,
        capture_output=True,
    )
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=source,
        text=True,
    ).strip()
    return source, commit


def _write_cli_fake_sage_python_runner(tmp_path: Path) -> Path:
    executable = tmp_path / "sage"
    executable.write_text(
        textwrap.dedent(
            """
            #!/usr/bin/env python3
            import os
            import pathlib
            import sys

            if sys.argv[1:2] == ["-python"]:
                marker = os.environ.get("AGADES_FAKE_SAGE_MARKER")
                if marker:
                    pathlib.Path(marker).write_text("used", encoding="utf-8")
                os.execv(sys.executable, [sys.executable, *sys.argv[2:]])
            raise SystemExit(f"unexpected fake sage invocation: {sys.argv[1:]}")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


def _write_cli_fake_sage_python_command_runner(tmp_path: Path) -> Path:
    executable = tmp_path / "sage-python-runner"
    executable.write_text(
        textwrap.dedent(
            """
            #!/usr/bin/env python3
            import os
            import pathlib
            import sys

            if sys.argv[1:2] == ["--python-env"]:
                marker = os.environ.get("AGADES_FAKE_SAGE_MARKER")
                if marker:
                    pathlib.Path(marker).write_text("used", encoding="utf-8")
                os.execv(sys.executable, [sys.executable, *sys.argv[2:]])
            raise SystemExit(
                f"unexpected fake sage python invocation: {sys.argv[1:]}"
            )
            """
        ).lstrip(),
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


def test_lattice_estimator_baseline_run_command_writes_private_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    runner = CliRunner()

    def fake_build_lattice_estimator(
        *,
        estimator,
        estimator_cache,
        estimator_source=None,
        sage_command=None,
        sage_python_command=None,
    ) -> LatticeEstimatorAdapter:
        del estimator, estimator_cache, estimator_source, sage_command
        del sage_python_command
        return LatticeEstimatorAdapter(backend=_CliBaselineBackend())

    monkeypatch.setattr(
        cli,
        "build_lattice_estimator",
        fake_build_lattice_estimator,
    )

    with runner.isolated_filesystem(temp_dir=tmp_path):
        out = Path("private/reports/lattice_estimator_baseline_run.json")

        result = runner.invoke(
            app,
            [
                "lattice-estimator-baseline-run",
                "--contracts",
                str(project_root / "docs/lattice_estimator_baseline_contracts.json"),
                "--contracts-root",
                str(project_root),
                "--out",
                str(out),
                "--policy",
                str(project_root / "docs/private_run_policy.json"),
                "--run-id",
                "cli-baseline-run",
            ],
        )

        assert result.exit_code == 0, result.output
        assert f"lattice_estimator_baseline_run={out}" in result.output
        payload = json.loads(out.read_text())
        assert payload["schema_version"] == (
            "agades.pqc.lattice_estimator_baseline_run.v1"
        )
        assert payload["run_id"] == "cli-baseline-run"
        assert payload["summary"]["ok_results"] == 5
        assert payload["summary"]["numeric_result_count"] == 5
        assert payload["summary"]["public_release_ok"] is False


def test_lattice_estimator_baseline_run_verify_command_accepts_private_report(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        out = Path("private/reports/lattice_estimator_baseline_run.json")
        lattice_estimator_baseline_run.write_lattice_estimator_baseline_run(
            out,
            contracts_path=Path("docs/lattice_estimator_baseline_contracts.json"),
            policy=build_private_run_policy(),
            adapter=LatticeEstimatorAdapter(backend=_CliBaselineBackend()),
            contracts_root=project_root,
            policy_root=Path.cwd(),
            run_id="cli-baseline-run-verification",
        )

        result = runner.invoke(
            app,
            [
                "lattice-estimator-baseline-run-verify",
                "--report",
                str(out),
                "--contracts-root",
                str(project_root),
            ],
        )

        assert result.exit_code == 0, result.output
        assert '"accepted": true' in result.output
        assert '"numeric_result_count": 5' in result.output
        assert '"raw_output_digest_count": 5' in result.output


def test_lattice_estimator_baseline_review_packet_command_writes_private_packet(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        baseline = Path("private/reports/lattice_estimator_baseline_run.json")
        lattice_estimator_baseline_run.write_lattice_estimator_baseline_run(
            baseline,
            contracts_path=Path("docs/lattice_estimator_baseline_contracts.json"),
            policy=build_private_run_policy(),
            adapter=LatticeEstimatorAdapter(backend=_CliBaselineBackend()),
            contracts_root=project_root,
            policy_root=Path.cwd(),
            run_id="cli-baseline-run-review-packet",
        )
        out = Path("private/reports/lattice_estimator_baseline_review_packet.json")

        result = runner.invoke(
            app,
            [
                "lattice-estimator-baseline-review-packet",
                "--baseline-report",
                str(baseline),
                "--out",
                str(out),
                "--policy",
                str(project_root / "docs/private_run_policy.json"),
                "--contracts-root",
                str(project_root),
                "--reviewer-label",
                "external-lattice-review",
            ],
        )

        assert result.exit_code == 0, result.output
        assert f"lattice_estimator_baseline_review_packet={out}" in result.output
        packet = json.loads(out.read_text(encoding="utf-8"))
        assert packet["schema_version"] == (
            "agades.pqc.lattice_estimator_baseline_review_packet.v1"
        )
        assert packet["summary"]["raw_output_digest_count"] == 5
        assert packet["safety"]["contains_numeric_values"] is False
        assert '"time_bits":' not in json.dumps(packet, sort_keys=True)

        verify_result = runner.invoke(
            app,
            [
                "lattice-estimator-baseline-review-packet-verify",
                "--packet",
                str(out),
                "--baseline-report",
                str(baseline),
                "--contracts-root",
                str(project_root),
            ],
        )
        assert verify_result.exit_code == 0, verify_result.output
        assert '"accepted": true' in verify_result.output


def test_lattice_estimator_baseline_run_command_accepts_estimator_source_checkout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    source, commit = _write_cli_fake_lattice_estimator_checkout(tmp_path)
    runner = CliRunner()
    captured: dict[str, Path | None] = {}
    _clear_estimator_modules()

    def fake_build_lattice_estimator(
        *,
        estimator,
        estimator_cache,
        estimator_source=None,
        sage_command=None,
        sage_python_command=None,
    ) -> LatticeEstimatorAdapter:
        del estimator, estimator_cache, sage_command, sage_python_command
        captured["estimator_source"] = estimator_source
        return LatticeEstimatorAdapter(
            source_path=estimator_source,
            config=LatticeEstimatorConfig(required_commit=commit),
        )

    monkeypatch.setattr(cli, "build_lattice_estimator", fake_build_lattice_estimator)
    monkeypatch.setattr(
        lattice_estimator_baseline_run,
        "LATTICE_ESTIMATOR_PINNED_COMMIT",
        commit,
    )

    with runner.isolated_filesystem(temp_dir=tmp_path):
        out = Path("private/reports/lattice_estimator_baseline_run.json")

        result = runner.invoke(
            app,
            [
                "lattice-estimator-baseline-run",
                "--contracts",
                str(project_root / "docs/lattice_estimator_baseline_contracts.json"),
                "--contracts-root",
                str(project_root),
                "--out",
                str(out),
                "--policy",
                str(project_root / "docs/private_run_policy.json"),
                "--estimator-source",
                str(source),
                "--run-id",
                "cli-source-baseline-run",
            ],
        )

        assert result.exit_code == 0, result.output
        assert captured["estimator_source"] == source
        payload = json.loads(out.read_text())
        assert payload["run_id"] == "cli-source-baseline-run"
        assert payload["summary"]["ok_results"] == 5
        assert payload["summary"]["numeric_result_count"] == 5
        assert all(entry["estimator_commit"] == commit for entry in payload["results"])
        assert all(
            entry["estimator_version"] == "fake-cli-checkout-0.1"
            for entry in payload["results"]
        )


def test_lattice_estimator_baseline_run_command_accepts_sage_python_checkout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    source, commit = _write_cli_fake_lattice_estimator_checkout(tmp_path)
    sage = _write_cli_fake_sage_python_runner(tmp_path)
    sage_marker = tmp_path / "sage-python-used"
    monkeypatch.setenv("AGADES_FAKE_SAGE_MARKER", sage_marker.as_posix())
    monkeypatch.setattr(cli, "LATTICE_ESTIMATOR_PINNED_COMMIT", commit)
    monkeypatch.setattr(
        lattice_estimator_baseline_run,
        "LATTICE_ESTIMATOR_PINNED_COMMIT",
        commit,
    )
    runner = CliRunner()
    _clear_estimator_modules()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        out = Path("private/reports/lattice_estimator_baseline_run.json")

        result = runner.invoke(
            app,
            [
                "lattice-estimator-baseline-run",
                "--contracts",
                str(project_root / "docs/lattice_estimator_baseline_contracts.json"),
                "--contracts-root",
                str(project_root),
                "--out",
                str(out),
                "--policy",
                str(project_root / "docs/private_run_policy.json"),
                "--estimator-source",
                str(source),
                "--sage-command",
                str(sage),
                "--run-id",
                "cli-sage-baseline-run",
            ],
        )

        assert result.exit_code == 0, result.output
        assert sage_marker.read_text(encoding="utf-8") == "used"
        payload = json.loads(out.read_text())
        assert payload["run_id"] == "cli-sage-baseline-run"
        assert payload["summary"]["ok_results"] == 5
        assert payload["summary"]["numeric_result_count"] == 5
        assert all(entry["estimator_commit"] == commit for entry in payload["results"])
        assert all(
            entry["estimator_version"] == "fake-cli-checkout-0.1"
            for entry in payload["results"]
        )


def test_lattice_estimator_baseline_run_command_accepts_sage_python_command(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    source, commit = _write_cli_fake_lattice_estimator_checkout(tmp_path)
    sage_python = _write_cli_fake_sage_python_command_runner(tmp_path)
    sage_marker = tmp_path / "sage-python-command-used"
    monkeypatch.setenv("AGADES_FAKE_SAGE_MARKER", sage_marker.as_posix())
    monkeypatch.setattr(cli, "LATTICE_ESTIMATOR_PINNED_COMMIT", commit)
    monkeypatch.setattr(
        lattice_estimator_baseline_run,
        "LATTICE_ESTIMATOR_PINNED_COMMIT",
        commit,
    )
    runner = CliRunner()
    _clear_estimator_modules()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        out = Path("private/reports/lattice_estimator_baseline_run.json")

        result = runner.invoke(
            app,
            [
                "lattice-estimator-baseline-run",
                "--contracts",
                str(project_root / "docs/lattice_estimator_baseline_contracts.json"),
                "--contracts-root",
                str(project_root),
                "--out",
                str(out),
                "--policy",
                str(project_root / "docs/private_run_policy.json"),
                "--estimator-source",
                str(source),
                "--sage-python-command",
                f"{sage_python.as_posix()} --python-env",
                "--run-id",
                "cli-sage-python-command-baseline-run",
            ],
        )

        assert result.exit_code == 0, result.output
        assert sage_marker.read_text(encoding="utf-8") == "used"
        payload = json.loads(out.read_text())
        assert payload["run_id"] == "cli-sage-python-command-baseline-run"
        assert payload["summary"]["ok_results"] == 5
        assert payload["summary"]["numeric_result_count"] == 5
        assert all(entry["estimator_commit"] == commit for entry in payload["results"])
        assert all(
            entry["estimator_version"] == "fake-cli-checkout-0.1"
            for entry in payload["results"]
        )


def test_lattice_estimator_checkout_preflight_command_writes_private_report(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    source, commit = _write_cli_fake_lattice_estimator_checkout(tmp_path)
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        out = Path("private/reports/lattice_estimator_checkout_preflight.json")

        result = runner.invoke(
            app,
            [
                "lattice-estimator-checkout-preflight",
                "--estimator-source",
                str(source),
                "--out",
                str(out),
                "--policy",
                str(project_root / "docs/private_run_policy.json"),
                "--required-commit",
                commit,
            ],
        )

        assert result.exit_code == 0, result.output
        assert f"lattice_estimator_checkout_preflight={out}" in result.output
        payload = json.loads(out.read_text())
        assert payload["schema_version"] == (
            "agades.pqc.lattice_estimator_checkout_preflight.v1"
        )
        assert payload["source_checkout"]["git"]["head_commit"] == commit
        assert payload["source_checkout"]["git"]["head_matches_required_pin"] is True
        assert payload["readiness"]["ready_for_private_baseline_run"] is True
        assert payload["safety"]["imports_upstream_python"] is False
        assert payload["safety"]["executes_estimator"] is False
        assert not (source / "estimator" / "IMPORT_MARKER").exists()


def test_lattice_estimator_runtime_preflight_command_writes_private_report(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    sage = tmp_path / "sage"
    sage.write_text(
        (
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "if sys.argv[1:] == ['--version']:\n"
            "    print('SageMath version 10.4')\n"
            "    raise SystemExit(0)\n"
            "if sys.argv[1:3] == ['-python', '-c']:\n"
            "    print('sage-python-ok')\n"
            "    raise SystemExit(0)\n"
            "raise SystemExit(2)\n"
        ),
        encoding="utf-8",
    )
    sage.chmod(0o755)
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        out = Path("private/reports/lattice_estimator_runtime_preflight.json")

        result = runner.invoke(
            app,
            [
                "lattice-estimator-runtime-preflight",
                "--sage-command",
                str(sage),
                "--out",
                str(out),
                "--policy",
                str(project_root / "docs/private_run_policy.json"),
            ],
        )

        assert result.exit_code == 0, result.output
        assert f"lattice_estimator_runtime_preflight={out}" in result.output
        payload = json.loads(out.read_text())
        assert payload["schema_version"] == (
            "agades.pqc.lattice_estimator_runtime_preflight.v1"
        )
        assert payload["runtime_environment"]["sage_found"] is True
        assert payload["runtime_environment"]["sage_version"] == "SageMath version 10.4"
        assert (
            payload["readiness"]["ready_for_private_lattice_estimator_import"] is True
        )
        assert payload["safety"]["imports_upstream_python"] is False
        assert payload["safety"]["executes_estimator"] is False


def test_lattice_estimator_runtime_preflight_verify_command_accepts_report(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        out = Path("private/reports/lattice_estimator_runtime_preflight.json")

        write_lattice_estimator_runtime_preflight(
            out,
            sage_command=(tmp_path / "missing-sage").as_posix(),
            policy=json.loads(
                (project_root / "docs/private_run_policy.json").read_text(
                    encoding="utf-8"
                )
            ),
            policy_root=Path.cwd(),
        )

        result = runner.invoke(
            app,
            [
                "lattice-estimator-runtime-preflight-verify",
                "--preflight",
                str(out),
            ],
        )

        assert result.exit_code == 0, result.output
        assert "agades.pqc.lattice_estimator_runtime_preflight_verification.v1" in (
            result.output
        )
        assert '"accepted": true' in result.output
        assert '"ready_for_private_lattice_estimator_import": false' in result.output


def test_deepevolve_injections_command_writes_private_batch(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        out = Path("private/candidates/paper_card_injections.json")

        result = runner.invoke(
            app,
            [
                "deepevolve-injections",
                "--out",
                str(out),
                "--paper-card-dir",
                str(project_root / "examples" / "paper_cards"),
                "--policy",
                str(project_root / "docs" / "private_run_policy.json"),
                "--run-id",
                "cli-paper-card-review",
            ],
        )

        assert result.exit_code == 0, result.output
        assert f"deepevolve_injections={out}" in result.output
        payload = json.loads(out.read_text())
        assert payload["schema_version"] == ("agades.pqc.paper_card_injection_batch.v1")
        assert payload["run_id"] == "cli-paper-card-review"
        assert payload["summary"]["injection_count"] == 13
        assert payload["safety"]["writes_attack_plans"] is False


def test_benchmark_command_overwrites_existing_trace_file(tmp_path: Path) -> None:
    trace_path = tmp_path / "benchmark.jsonl"
    runner = CliRunner()
    args = [
        "benchmark",
        "benchmarks/lattice_downscaled_lwe_instance_solve",
        "--out",
        str(trace_path),
    ]

    first = runner.invoke(app, args)
    second = runner.invoke(app, args)

    assert first.exit_code == 0
    assert second.exit_code == 0
    records = [line for line in trace_path.read_text().splitlines() if line.strip()]
    assert len(records) == 3


def test_implementation_security_source_contract_benchmark_stays_schema_only(
    tmp_path: Path,
) -> None:
    trace_path = tmp_path / "implementation_security_schema.jsonl"

    result = CliRunner().invoke(
        app,
        [
            "benchmark",
            "benchmarks/implementation_security_schema_only",
            "--out",
            str(trace_path),
        ],
    )

    assert result.exit_code == 0, result.output
    records = [
        TraceRecord.model_validate_json(line)
        for line in trace_path.read_text().splitlines()
        if line.strip()
    ]
    assert len(records) == 9
    assert all(
        record.attack_plan.target.family.value == "IMPLEMENTATION_SECURITY"
        for record in records
    )
    assert all(record.accepted is False for record in records)
    assert {
        record.attack_plan.attack_plan_id
        for record in records
        if record.attack_plan.attack_plan_id
        in {
            "implementation_security_pqclean_schema_v1",
            "implementation_security_liboqs_schema_v1",
            "implementation_security_pqm4_schema_v1",
            "implementation_security_pq_code_package_schema_v1",
            "implementation_security_nist_acvp_schema_v1",
            "implementation_security_dudect_schema_v1",
            "implementation_security_ctgrind_schema_v1",
            "implementation_security_timecop_schema_v1",
        }
    } == {
        "implementation_security_pqclean_schema_v1",
        "implementation_security_liboqs_schema_v1",
        "implementation_security_pqm4_schema_v1",
        "implementation_security_pq_code_package_schema_v1",
        "implementation_security_nist_acvp_schema_v1",
        "implementation_security_dudect_schema_v1",
        "implementation_security_ctgrind_schema_v1",
        "implementation_security_timecop_schema_v1",
    }
    assert {record.evaluation["evaluation_status"] for record in records} == {
        "unsupported"
    }
    assert all(record.evaluation["estimated_time_bits"] is None for record in records)


def test_evolve_batch_writes_trace_and_elite_archive(tmp_path: Path) -> None:
    trace_path = tmp_path / "evolution_trace.jsonl"
    archive_path = tmp_path / "evolution_archive.json"

    result = CliRunner().invoke(
        app,
        [
            "evolve-batch",
            "benchmarks/lattice_downscaled_lwe_instance_solve",
            "--trace-out",
            str(trace_path),
            "--archive-out",
            str(archive_path),
        ],
    )

    assert result.exit_code == 0
    assert "elites=1" in result.output
    trace_lines = trace_path.read_text().splitlines()
    assert len(trace_lines) == 3
    archive = json.loads(archive_path.read_text())
    assert archive["schema_version"] == "agades.pqc.evolution_archive.v1"
    assert archive["run_id"] == "lattice_downscaled_lwe_instance_solve"
    assert archive["summary"] == {
        "accepted_count": 3,
        "elite_count": 1,
        "evaluated_count": 3,
        "rejected_count": 0,
    }
    assert archive["global_best"]["evaluation_status"] == "ok"
    assert archive["global_best"]["feature_values"]["feature_family"] == "LWE"


def test_mutate_candidates_command_writes_private_plan_batch(tmp_path: Path) -> None:
    out_dir = tmp_path / "candidate_mutations"

    result = CliRunner().invoke(
        app,
        [
            "mutate-candidates",
            "examples/attack_plans/lattice_primal_usvp_toy.json",
            "--out",
            str(out_dir),
            "--run-id",
            "unit-cli-mutation",
            "--generation",
            "1",
            "--max-mutations-per-plan",
            "2",
        ],
    )

    assert result.exit_code == 0, result.output
    assert f"mutation_manifest={out_dir / 'mutation_manifest.json'}" in result.output
    assert "candidates=2" in result.output
    assert "skipped=0" in result.output

    plan_files = sorted((out_dir / "plans").glob("*.json"))
    assert [path.name for path in plan_files] == [
        "lattice_primal_usvp_toy_v1__g1__beta_minus_4.json",
        "lattice_primal_usvp_toy_v1__g1__beta_plus_4.json",
    ]
    plans = [json.loads(path.read_text()) for path in plan_files]
    assert all(plan["metadata"]["public"] is False for plan in plans)
    assert plans[0]["operators"][0]["params"]["beta"] == 44
    assert plans[1]["operators"][0]["params"]["beta"] == 52


def test_mutate_archive_command_writes_parent_linked_private_plan_batch(
    tmp_path: Path,
) -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    archive_path = tmp_path / "archive.json"
    source_trace_path = tmp_path / "source.jsonl"
    out_dir = tmp_path / "archive_mutations"
    source_record = _trace_record(
        plan=plan,
        run_id="training",
        candidate_id="elite-candidate",
        parent_id=None,
        score=-90.0,
        accepted=True,
    )
    source_trace_path.write_text(
        source_record.model_dump_json() + "\n",
        encoding="utf-8",
    )
    write_evolution_archive([source_record], archive_path, run_id="training")

    result = CliRunner().invoke(
        app,
        [
            "mutate-archive",
            str(archive_path),
            str(source_trace_path),
            "--out",
            str(out_dir),
            "--run-id",
            "unit-cli-archive-mutation",
            "--max-mutations-per-elite",
            "2",
        ],
    )

    assert result.exit_code == 0, result.output
    assert f"mutation_manifest={out_dir / 'mutation_manifest.json'}" in result.output
    assert "candidates=2" in result.output
    assert "skipped=0" in result.output

    manifest = json.loads((out_dir / "mutation_manifest.json").read_text())
    assert manifest["summary"] == {
        "candidate_count": 2,
        "source_count": 1,
        "skipped_count": 0,
    }
    assert manifest["candidates"][0]["parent_candidate_id"] == "elite-candidate"
    assert manifest["candidates"][0]["parent_trace_id"] == source_record.trace_id
    plan_files = sorted((out_dir / "plans").glob("*.json"))
    assert [path.name for path in plan_files] == [
        "lattice_primal_usvp_toy_v1__g1__beta_minus_4.json",
        "lattice_primal_usvp_toy_v1__g1__beta_plus_4.json",
    ]
    plans = [json.loads(path.read_text()) for path in plan_files]
    assert all(plan["metadata"]["public"] is False for plan in plans)


def test_rescore_archive_command_writes_heldout_report(tmp_path: Path) -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    archive_path = tmp_path / "archive.json"
    heldout_trace_path = tmp_path / "heldout.jsonl"
    rescore_path = tmp_path / "heldout_rescore.json"
    write_evolution_archive(
        [
            _trace_record(
                plan=plan,
                run_id="training",
                candidate_id="candidate",
                parent_id=None,
                score=-90.0,
                accepted=True,
            )
        ],
        archive_path,
        run_id="training",
    )
    heldout_trace = _trace_record(
        plan=plan,
        run_id="heldout",
        candidate_id="candidate-heldout",
        parent_id="candidate",
        score=-92.0,
        accepted=True,
    )
    heldout_trace_path.write_text(
        heldout_trace.model_dump_json() + "\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "rescore-archive",
            str(archive_path),
            str(heldout_trace_path),
            "--out",
            str(rescore_path),
        ],
    )

    assert result.exit_code == 0
    assert "rescored=1" in result.output
    report = json.loads(rescore_path.read_text())
    assert report["schema_version"] == "agades.pqc.heldout_rescore.v1"
    assert report["summary"]["rescored_elite_count"] == 1
    assert report["global_best_by_heldout"]["generalization_gap"] == 2.0


def test_heldout_batch_command_writes_linked_trace_and_rescore(tmp_path: Path) -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    archive_path = tmp_path / "archive.json"
    source_trace_path = tmp_path / "source.jsonl"
    heldout_trace_path = tmp_path / "heldout.jsonl"
    rescore_path = tmp_path / "heldout_rescore.json"
    source_record = _trace_record(
        plan=plan,
        run_id="training",
        candidate_id="candidate",
        parent_id=None,
        score=-90.0,
        accepted=True,
    )
    source_trace_path.write_text(
        source_record.model_dump_json() + "\n",
        encoding="utf-8",
    )
    write_evolution_archive([source_record], archive_path, run_id="training")

    result = CliRunner().invoke(
        app,
        [
            "heldout-batch",
            str(archive_path),
            str(source_trace_path),
            "benchmarks/lattice_toy_lwe/lwe_n96_q769.json",
            "--trace-out",
            str(heldout_trace_path),
            "--rescore-out",
            str(rescore_path),
        ],
    )

    assert result.exit_code == 0
    assert "heldout=1" in result.output
    assert "rescored=1" in result.output
    heldout_records = [
        json.loads(line) for line in heldout_trace_path.read_text().splitlines()
    ]
    assert len(heldout_records) == 1
    heldout_record = heldout_records[0]
    assert heldout_record["parent_id"] == "candidate"
    assert heldout_record["candidate_id"] == "candidate-heldout-toy_lwe_n96_q769-0"
    assert heldout_record["attack_plan"]["target"]["name"] == "toy_lwe_n96_q769"
    assert heldout_record["attack_plan"]["metadata"]["public"] is False
    report = json.loads(rescore_path.read_text())
    assert report["summary"]["rescored_elite_count"] == 1


def test_heldout_schedule_command_writes_reviewed_private_schedule(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    plan = AttackPlan.model_validate_json(
        (
            project_root / "examples" / "attack_plans" / "lattice_primal_usvp_toy.json"
        ).read_text()
    )
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        archive_path = Path("archive.json")
        source_trace_path = Path("source.jsonl")
        schedule_path = Path("private/runs/schedule.json")
        review_log_path = Path("private/runs/review_log.json")
        source_record = _trace_record(
            plan=plan,
            run_id="training",
            candidate_id="candidate",
            parent_id=None,
            score=-90.0,
            accepted=True,
        )
        source_trace_path.write_text(
            source_record.model_dump_json() + "\n",
            encoding="utf-8",
        )
        write_evolution_archive([source_record], archive_path, run_id="training")

        review_log_result = runner.invoke(
            app,
            [
                "heldout-review-log",
                "--out",
                str(review_log_path),
                "--policy",
                str(project_root / "docs" / "private_run_policy.json"),
                "--review-id",
                "cli-review",
                "--reviewed-by",
                "cli-reviewer",
                "--approval",
                "private-run-policy-review",
                "--approval",
                "heldout-target-review",
                "--approval",
                "retention-owner-review",
                "--approval",
                "publication-export-review",
            ],
        )
        result = runner.invoke(
            app,
            [
                "heldout-schedule",
                str(archive_path),
                str(source_trace_path),
                str(
                    project_root
                    / "benchmarks"
                    / "lattice_toy_lwe"
                    / "lwe_n96_q769.json"
                ),
                "--policy",
                str(project_root / "docs" / "private_run_policy.json"),
                "--out",
                str(schedule_path),
                "--review-log",
                str(review_log_path),
                "--trace-out",
                "private/traces/heldout_trace.jsonl",
                "--rescore-out",
                "private/reports/heldout_rescore.json",
                "--approval",
                "private-run-policy-review",
                "--approval",
                "heldout-target-review",
                "--approval",
                "retention-owner-review",
                "--approval",
                "publication-export-review",
            ],
        )

        assert review_log_result.exit_code == 0, review_log_result.output
        assert "review_log=" in review_log_result.output
        assert result.exit_code == 0
        assert "schedule=" in result.output
        assert "scheduled=1" in result.output
        schedule = json.loads(schedule_path.read_text())
        assert schedule["ready_to_run"] is True
        assert schedule["summary"]["scheduled_candidates"] == 1
        assert schedule["outputs"]["heldout_trace"] == (
            "private/traces/heldout_trace.jsonl"
        )
        assert schedule["review_log"]["path"] == "private/runs/review_log.json"


def test_heldout_run_schedule_command_consumes_reviewed_schedule(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    plan = AttackPlan.model_validate_json(
        (
            project_root / "examples" / "attack_plans" / "lattice_primal_usvp_toy.json"
        ).read_text()
    )
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        archive_path = Path("archive.json")
        source_trace_path = Path("source.jsonl")
        schedule_path = Path("private/runs/schedule.json")
        review_log_path = Path("private/runs/review_log.json")
        trace_path = Path("private/traces/heldout_trace.jsonl")
        rescore_path = Path("private/reports/heldout_rescore.json")
        source_record = _trace_record(
            plan=plan,
            run_id="training",
            candidate_id="candidate",
            parent_id=None,
            score=-90.0,
            accepted=True,
        )
        source_trace_path.write_text(
            source_record.model_dump_json() + "\n",
            encoding="utf-8",
        )
        write_evolution_archive([source_record], archive_path, run_id="training")

        review_log_result = runner.invoke(
            app,
            [
                "heldout-review-log",
                "--out",
                str(review_log_path),
                "--policy",
                str(project_root / "docs" / "private_run_policy.json"),
                "--review-id",
                "cli-review",
                "--reviewed-by",
                "cli-reviewer",
                "--approval",
                "private-run-policy-review",
                "--approval",
                "heldout-target-review",
                "--approval",
                "retention-owner-review",
                "--approval",
                "publication-export-review",
            ],
        )
        schedule_result = runner.invoke(
            app,
            [
                "heldout-schedule",
                str(archive_path),
                str(source_trace_path),
                str(
                    project_root
                    / "benchmarks"
                    / "lattice_toy_lwe"
                    / "lwe_n96_q769.json"
                ),
                "--policy",
                str(project_root / "docs" / "private_run_policy.json"),
                "--out",
                str(schedule_path),
                "--review-log",
                str(review_log_path),
                "--trace-out",
                str(trace_path),
                "--rescore-out",
                str(rescore_path),
                "--approval",
                "private-run-policy-review",
                "--approval",
                "heldout-target-review",
                "--approval",
                "retention-owner-review",
                "--approval",
                "publication-export-review",
            ],
        )
        run_result = runner.invoke(
            app,
            [
                "heldout-run-schedule",
                str(schedule_path),
                "--policy",
                str(project_root / "docs" / "private_run_policy.json"),
            ],
        )

        assert review_log_result.exit_code == 0, review_log_result.output
        assert schedule_result.exit_code == 0, schedule_result.output
        assert run_result.exit_code == 0, run_result.output
        assert "schedule_run=" in run_result.output
        assert "heldout=1" in run_result.output
        assert "rescored=1" in run_result.output
        assert trace_path.exists()
        assert rescore_path.exists()


def test_heldout_review_packet_command_writes_private_digest_handoff(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    policy_path = project_root / "docs" / "private_run_policy.json"
    plan = AttackPlan.model_validate_json(
        (
            project_root / "examples" / "attack_plans" / "lattice_primal_usvp_toy.json"
        ).read_text()
    )
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        archive_path = Path("archive.json")
        source_trace_path = Path("source.jsonl")
        schedule_path = Path("private/runs/schedule.json")
        review_log_path = Path("private/runs/review_log.json")
        trace_path = Path("private/traces/heldout_trace.jsonl")
        rescore_path = Path("private/reports/heldout_rescore.json")
        packet_path = Path("private/reports/heldout_review_packet.json")
        source_record = _trace_record(
            plan=plan,
            run_id="training",
            candidate_id="candidate",
            parent_id=None,
            score=-90.0,
            accepted=True,
        )
        source_trace_path.write_text(
            source_record.model_dump_json() + "\n",
            encoding="utf-8",
        )
        write_evolution_archive([source_record], archive_path, run_id="training")

        review_log_result = runner.invoke(
            app,
            [
                "heldout-review-log",
                "--out",
                str(review_log_path),
                "--policy",
                str(policy_path),
                "--review-id",
                "cli-review",
                "--reviewed-by",
                "cli-reviewer",
                "--approval",
                "private-run-policy-review",
                "--approval",
                "heldout-target-review",
                "--approval",
                "retention-owner-review",
                "--approval",
                "publication-export-review",
            ],
        )
        schedule_result = runner.invoke(
            app,
            [
                "heldout-schedule",
                str(archive_path),
                str(source_trace_path),
                str(
                    project_root
                    / "benchmarks"
                    / "lattice_toy_lwe"
                    / "lwe_n96_q769.json"
                ),
                "--policy",
                str(policy_path),
                "--out",
                str(schedule_path),
                "--review-log",
                str(review_log_path),
                "--trace-out",
                str(trace_path),
                "--rescore-out",
                str(rescore_path),
                "--approval",
                "private-run-policy-review",
                "--approval",
                "heldout-target-review",
                "--approval",
                "retention-owner-review",
                "--approval",
                "publication-export-review",
            ],
        )
        run_result = runner.invoke(
            app,
            [
                "heldout-run-schedule",
                str(schedule_path),
                "--policy",
                str(policy_path),
            ],
        )
        packet_result = runner.invoke(
            app,
            [
                "heldout-review-packet",
                str(schedule_path),
                "--out",
                str(packet_path),
                "--policy",
                str(policy_path),
                "--reviewer-label",
                "cli-heldout-review",
            ],
        )
        verify_result = runner.invoke(
            app,
            [
                "heldout-review-packet-verify",
                "--packet",
                str(packet_path),
                "--schedule",
                str(schedule_path),
                "--policy",
                str(policy_path),
            ],
        )

        assert review_log_result.exit_code == 0, review_log_result.output
        assert schedule_result.exit_code == 0, schedule_result.output
        assert run_result.exit_code == 0, run_result.output
        assert packet_result.exit_code == 0, packet_result.output
        assert f"heldout_review_packet={packet_path}" in packet_result.output
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        assert packet["schema_version"] == "agades.pqc.heldout_review_packet.v1"
        assert packet["summary"]["heldout_record_count"] == 1
        assert packet["safety"]["contains_private_scores"] is False
        assert '"combined_score":' not in json.dumps(packet, sort_keys=True)
        assert verify_result.exit_code == 0, verify_result.output
        assert '"accepted": true' in verify_result.output


def test_heldout_cron_plan_command_writes_reviewed_private_cron_plan(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    plan = AttackPlan.model_validate_json(
        (
            project_root / "examples" / "attack_plans" / "lattice_primal_usvp_toy.json"
        ).read_text()
    )
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        archive_path = Path("archive.json")
        source_trace_path = Path("source.jsonl")
        schedule_path = Path("private/runs/schedule.json")
        review_log_path = Path("private/runs/review_log.json")
        cron_plan_path = Path("private/runs/heldout_cron_plan.json")
        source_record = _trace_record(
            plan=plan,
            run_id="training",
            candidate_id="candidate",
            parent_id=None,
            score=-90.0,
            accepted=True,
        )
        source_trace_path.write_text(
            source_record.model_dump_json() + "\n",
            encoding="utf-8",
        )
        write_evolution_archive([source_record], archive_path, run_id="training")

        review_log_result = runner.invoke(
            app,
            [
                "heldout-review-log",
                "--out",
                str(review_log_path),
                "--policy",
                str(project_root / "docs" / "private_run_policy.json"),
                "--review-id",
                "cli-review",
                "--reviewed-by",
                "cli-reviewer",
                "--approval",
                "private-run-policy-review",
                "--approval",
                "heldout-target-review",
                "--approval",
                "retention-owner-review",
                "--approval",
                "publication-export-review",
            ],
        )
        schedule_result = runner.invoke(
            app,
            [
                "heldout-schedule",
                str(archive_path),
                str(source_trace_path),
                str(
                    project_root
                    / "benchmarks"
                    / "lattice_toy_lwe"
                    / "lwe_n96_q769.json"
                ),
                "--policy",
                str(project_root / "docs" / "private_run_policy.json"),
                "--out",
                str(schedule_path),
                "--review-log",
                str(review_log_path),
                "--trace-out",
                "private/traces/heldout_trace.jsonl",
                "--rescore-out",
                "private/reports/heldout_rescore.json",
                "--trigger",
                "local_cron_after_review",
                "--approval",
                "private-run-policy-review",
                "--approval",
                "heldout-target-review",
                "--approval",
                "retention-owner-review",
                "--approval",
                "publication-export-review",
            ],
        )
        cron_result = runner.invoke(
            app,
            [
                "heldout-cron-plan",
                str(schedule_path),
                "--out",
                str(cron_plan_path),
                "--policy",
                str(project_root / "docs" / "private_run_policy.json"),
                "--minute",
                "17",
                "--every-hours",
                "6",
            ],
        )

        assert review_log_result.exit_code == 0, review_log_result.output
        assert schedule_result.exit_code == 0, schedule_result.output
        assert cron_result.exit_code == 0, cron_result.output
        assert "cron_plan=" in cron_result.output
        cron_plan = json.loads(cron_plan_path.read_text())
        assert cron_plan["cron"]["expression"] == "17 */6 * * *"
        assert cron_plan["schedule"]["trigger"] == "local_cron_after_review"
        assert cron_plan["installation"]["writes_system_crontab"] is False
        assert (
            "agades-pqc heldout-run-schedule" in cron_plan["command"]["crontab_entry"]
        )


def test_archive_snapshot_command_writes_private_manifest(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    plan = AttackPlan.model_validate_json(
        (
            project_root / "examples" / "attack_plans" / "lattice_primal_usvp_toy.json"
        ).read_text()
    )
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        archive_path = Path("runs/evolution_archive.json")
        trace_path = Path("runs/evolution_trace.jsonl")
        review_log_path = Path("private/runs/review_log.json")
        snapshot_path = Path("private/runs/archive_snapshot.json")
        source_record = _trace_record(
            plan=plan,
            run_id="training",
            candidate_id="candidate",
            parent_id=None,
            score=-90.0,
            accepted=True,
        )
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.write_text(
            source_record.model_dump_json() + "\n",
            encoding="utf-8",
        )
        write_evolution_archive([source_record], archive_path, run_id="training")

        review_log_result = runner.invoke(
            app,
            [
                "heldout-review-log",
                "--out",
                str(review_log_path),
                "--policy",
                str(project_root / "docs" / "private_run_policy.json"),
                "--review-id",
                "cli-snapshot-review",
                "--reviewed-by",
                "cli-reviewer",
                "--approval",
                "private-run-policy-review",
                "--approval",
                "heldout-target-review",
                "--approval",
                "retention-owner-review",
                "--approval",
                "publication-export-review",
            ],
        )
        snapshot_result = runner.invoke(
            app,
            [
                "archive-snapshot",
                str(archive_path),
                str(trace_path),
                "--out",
                str(snapshot_path),
                "--review-log",
                str(review_log_path),
                "--policy",
                str(project_root / "docs" / "private_run_policy.json"),
                "--run-id",
                "cli-archive-snapshot",
            ],
        )

        assert review_log_result.exit_code == 0, review_log_result.output
        assert snapshot_result.exit_code == 0, snapshot_result.output
        assert f"archive_snapshot={snapshot_path}" in snapshot_result.output
        assert "trace_links_complete=True" in snapshot_result.output
        snapshot = json.loads(snapshot_path.read_text())
        assert snapshot["schema_version"] == ("agades.pqc.private_archive_snapshot.v1")
        assert snapshot["run_id"] == "cli-archive-snapshot"
        assert snapshot["inputs"]["archive"]["path"] == "runs/evolution_archive.json"
        assert snapshot["inputs"]["source_trace"]["path"] == (
            "runs/evolution_trace.jsonl"
        )
        assert snapshot["inputs"]["review_log"]["path"] == (
            "private/runs/review_log.json"
        )
        assert snapshot["trace_link_integrity"]["complete"] is True
        assert snapshot["safety"]["contains_trace_payloads"] is False
        assert '"attack_plan":' not in json.dumps(snapshot)


def _trace_record(
    *,
    plan: AttackPlan,
    run_id: str,
    candidate_id: str,
    parent_id: str | None,
    score: float,
    accepted: bool,
) -> TraceRecord:
    return TraceRecord.from_evaluation(
        run_id=run_id,
        candidate_id=candidate_id,
        parent_id=parent_id,
        generation=0,
        mutation_summary="unit test",
        attack_plan=plan,
        evaluation={
            "combined_score": score,
            "evaluation_status": "ok" if accepted else "invalid",
            "feature_family": plan.target.family.value,
            "feature_attack_type": "primal_usvp",
            "feature_memory_bucket": "low",
            "feature_assumption_bucket": "some",
            "feature_estimator_model": "mock-lattice-estimator",
            "valid": accepted,
        },
        accepted=accepted,
        public_release_ok=accepted,
        redaction_reason=None if accepted else "invalid",
    )
