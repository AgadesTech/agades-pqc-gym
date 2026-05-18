from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path
from typing import Any

import pytest

from agades_pqc_gym.evaluators.lattice_estimator import (
    LATTICE_ESTIMATOR_PINNED_COMMIT,
    LatticeEstimatorAdapter,
)
from agades_pqc_gym.integrations.lattice_estimator_baseline_run import (
    LATTICE_ESTIMATOR_BASELINE_RUN_SCHEMA,
    build_lattice_estimator_baseline_run,
    verify_lattice_estimator_baseline_run,
    write_lattice_estimator_baseline_run,
)
from agades_pqc_gym.integrations.lattice_estimator_checkout_preflight import (
    LATTICE_ESTIMATOR_CHECKOUT_PREFLIGHT_SCHEMA,
    build_lattice_estimator_checkout_preflight,
    write_lattice_estimator_checkout_preflight,
)
from agades_pqc_gym.integrations.lattice_estimator_review_packet import (
    LATTICE_ESTIMATOR_BASELINE_REVIEW_PACKET_SCHEMA,
    verify_lattice_estimator_baseline_review_packet,
    write_lattice_estimator_baseline_review_packet,
)
from agades_pqc_gym.integrations.lattice_estimator_runtime_preflight import (
    LATTICE_ESTIMATOR_RUNTIME_PREFLIGHT_SCHEMA,
    build_lattice_estimator_runtime_preflight,
    verify_lattice_estimator_runtime_preflight,
    write_lattice_estimator_runtime_preflight,
)
from agades_pqc_gym.integrations.private_run_policy import build_private_run_policy


def _write_fake_sage(tmp_path: Path, *, import_ok: bool = True) -> Path:
    executable = tmp_path / "sage"
    import_exit = 0 if import_ok else 1
    import_output = "sage-python-ok" if import_ok else "ModuleNotFoundError: sage"
    executable.write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env python3
            import sys

            if sys.argv[1:] == ["--version"]:
                print("SageMath version 10.4")
                raise SystemExit(0)
            if sys.argv[1:3] == ["-python", "-c"]:
                print({import_output!r})
                raise SystemExit({import_exit})
            print("unexpected fake sage invocation", sys.argv[1:])
            raise SystemExit(2)
            """
        ),
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


def _write_fake_sage_python_command(tmp_path: Path) -> Path:
    executable = tmp_path / "sage-python-runner"
    executable.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import sys

            if sys.argv[1:3] == ["--env", "-c"]:
                print("sage-python-ok")
                raise SystemExit(0)
            print("unexpected fake sage python invocation", sys.argv[1:])
            raise SystemExit(2)
            """
        ),
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


def _write_fake_lattice_estimator_checkout(tmp_path: Path) -> tuple[Path, str]:
    source = tmp_path / "fake-preflight-lattice-estimator"
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
            __version__ = "fake-preflight-checkout-0.1"
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
            "Add fake preflight estimator package",
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


class FakeBaselineBackend:
    version = "fake-baseline-0.1"
    commit = LATTICE_ESTIMATOR_PINNED_COMMIT

    def __init__(self) -> None:
        self.algorithm_keys: list[str] = []

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
        xs: Any,
        xe: Any,
        m: int,
        tag: str,
    ) -> dict[str, Any]:
        return {"n": n, "q": q, "xs": xs, "xe": xe, "m": m, "tag": tag}

    def estimate_lwe(
        self,
        *,
        params: Any,
        algorithm_key: str,
        red_cost_model: str | None,
        red_shape_model: str | None,
        jobs: int,
        catch_exceptions: bool,
    ) -> dict[str, Any]:
        del params, red_cost_model, red_shape_model, jobs, catch_exceptions
        self.algorithm_keys.append(algorithm_key)
        offset = len(self.algorithm_keys)
        return {
            algorithm_key: {
                "rop": 50.0 + offset,
                "mem": 20.0 + offset,
                "beta": 70 + offset,
            }
        }


def test_write_lattice_estimator_baseline_run_private_report(
    tmp_path: Path,
) -> None:
    backend = FakeBaselineBackend()
    out = Path("private/reports/lattice_estimator_baseline_run.json")

    report = write_lattice_estimator_baseline_run(
        out,
        contracts_path=Path("docs/lattice_estimator_baseline_contracts.json"),
        policy=build_private_run_policy(),
        adapter=LatticeEstimatorAdapter(backend=backend),
        contracts_root=Path.cwd(),
        policy_root=tmp_path,
        run_id="unit-baseline-run",
    )

    written = json.loads((tmp_path / out).read_text(encoding="utf-8"))

    assert written == report
    assert report["schema_version"] == LATTICE_ESTIMATOR_BASELINE_RUN_SCHEMA
    assert report["run_id"] == "unit-baseline-run"
    assert report["report"] == {
        "path": "private/reports/lattice_estimator_baseline_run.json",
        "private": True,
    }
    assert report["contracts"] == {
        "path": "docs/lattice_estimator_baseline_contracts.json",
        "schema_version": "agades.pqc.lattice_estimator_baseline_contracts.v1",
        "sha256": report["contracts"]["sha256"],
        "contract_count": 5,
    }
    assert len(report["contracts"]["sha256"]) == 64
    assert report["upstream"]["pinned_commit"] == LATTICE_ESTIMATOR_PINNED_COMMIT
    assert report["baseline_policy"] == {
        "numeric_reference_outputs_committed": False,
        "private_numeric_outputs": True,
        "publication_allowed": False,
        "requires_expert_review_before_publication": True,
        "security_claim": False,
    }
    assert report["summary"] == {
        "all_successful_results_from_pinned_commit": True,
        "contract_count": 5,
        "error_results": 0,
        "numeric_result_count": 5,
        "ok_results": 5,
        "public_release_ok": False,
        "security_claim": False,
        "unsupported_results": 0,
    }
    assert report["safety"] == {
        "arbitrary_candidate_code_execution": False,
        "external_network_access": False,
        "lwe_only": True,
        "numeric_reference_outputs_committed": False,
        "publishes_numeric_references": False,
        "raw_estimator_output_committed": False,
        "review_required_before_publication": True,
        "writes_only_allowed_private_roots": True,
    }
    assert [entry["algorithm_key"] for entry in report["results"]] == [
        "bdd",
        "bkw",
        "dual",
        "dual_hybrid",
        "usvp",
    ]
    assert backend.algorithm_keys == ["bdd", "bkw", "dual", "dual_hybrid", "usvp"]
    assert all(entry["evaluation_status"] == "ok" for entry in report["results"])
    assert all(
        entry["estimator_commit"] == LATTICE_ESTIMATOR_PINNED_COMMIT
        for entry in report["results"]
    )
    assert all(entry["numeric_output_private"] is True for entry in report["results"])
    assert all(entry["public_reference_output"] is False for entry in report["results"])
    assert all(len(entry["raw_output_sha256"]) == 64 for entry in report["results"])
    assert '"raw_output":' not in json.dumps(report)
    assert '"attack_plan":' not in json.dumps(report)


def test_lattice_estimator_baseline_run_verify_accepts_private_report(
    tmp_path: Path,
) -> None:
    out = Path("private/reports/lattice_estimator_baseline_run.json")
    write_lattice_estimator_baseline_run(
        out,
        contracts_path=Path("docs/lattice_estimator_baseline_contracts.json"),
        policy=build_private_run_policy(),
        adapter=LatticeEstimatorAdapter(backend=FakeBaselineBackend()),
        contracts_root=Path.cwd(),
        policy_root=tmp_path,
        run_id="unit-baseline-run-verification",
    )

    verification = verify_lattice_estimator_baseline_run(
        tmp_path / out,
        contracts_root=Path.cwd(),
    )

    assert verification["accepted"] is True
    assert verification["failures"] == []
    assert verification["summary"] == {
        "all_successful_results_from_pinned_commit": True,
        "contract_count": 5,
        "failure_count": 0,
        "lwe_only": True,
        "numeric_result_count": 5,
        "ok_results": 5,
        "private_report": True,
        "public_release_ok": False,
        "raw_output_digest_count": 5,
        "security_claim": False,
    }


def test_lattice_estimator_baseline_run_verify_rejects_publication_drift(
    tmp_path: Path,
) -> None:
    out = Path("private/reports/lattice_estimator_baseline_run.json")
    report = write_lattice_estimator_baseline_run(
        out,
        contracts_path=Path("docs/lattice_estimator_baseline_contracts.json"),
        policy=build_private_run_policy(),
        adapter=LatticeEstimatorAdapter(backend=FakeBaselineBackend()),
        contracts_root=Path.cwd(),
        policy_root=tmp_path,
        run_id="unit-baseline-run-publication-drift",
    )
    report["baseline_policy"]["publication_allowed"] = True
    report["safety"]["publishes_numeric_references"] = True
    report["results"][0]["public_reference_output"] = True
    (tmp_path / out).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verification = verify_lattice_estimator_baseline_run(
        tmp_path / out,
        contracts_root=Path.cwd(),
    )

    assert verification["accepted"] is False
    assert verification["summary"]["failure_count"] >= 3
    assert any(
        "must not allow publication" in failure
        for failure in verification["failures"]
    )
    assert any(
        "must not publish numeric references" in failure
        for failure in verification["failures"]
    )
    assert any(
        "public reference output" in failure
        for failure in verification["failures"]
    )


def test_lattice_estimator_baseline_run_verify_rejects_malformed_result(
    tmp_path: Path,
) -> None:
    out = Path("private/reports/lattice_estimator_baseline_run.json")
    report = write_lattice_estimator_baseline_run(
        out,
        contracts_path=Path("docs/lattice_estimator_baseline_contracts.json"),
        policy=build_private_run_policy(),
        adapter=LatticeEstimatorAdapter(backend=FakeBaselineBackend()),
        contracts_root=Path.cwd(),
        policy_root=tmp_path,
        run_id="unit-baseline-run-malformed-result",
    )
    del report["results"][0]["evaluation_status"]
    (tmp_path / out).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verification = verify_lattice_estimator_baseline_run(
        tmp_path / out,
        contracts_root=Path.cwd(),
    )

    assert verification["accepted"] is False
    assert any("status is invalid" in failure for failure in verification["failures"])


def test_lattice_estimator_baseline_run_rejects_public_output_path(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="forbidden public root"):
        write_lattice_estimator_baseline_run(
            Path("public/lattice_estimator_baseline_run.json"),
            contracts_path=Path("docs/lattice_estimator_baseline_contracts.json"),
            policy=build_private_run_policy(),
            adapter=LatticeEstimatorAdapter(backend=FakeBaselineBackend()),
            contracts_root=Path.cwd(),
            policy_root=tmp_path,
        )


def test_lattice_estimator_baseline_review_packet_is_digest_only_private_evidence(
    tmp_path: Path,
) -> None:
    baseline_out = Path("private/reports/lattice_estimator_baseline_run.json")
    write_lattice_estimator_baseline_run(
        baseline_out,
        contracts_path=Path("docs/lattice_estimator_baseline_contracts.json"),
        policy=build_private_run_policy(),
        adapter=LatticeEstimatorAdapter(backend=FakeBaselineBackend()),
        contracts_root=Path.cwd(),
        policy_root=tmp_path,
        run_id="unit-baseline-run-for-review",
    )
    review_out = Path("private/reports/lattice_estimator_baseline_review_packet.json")

    packet = write_lattice_estimator_baseline_review_packet(
        review_out,
        baseline_report_path=tmp_path / baseline_out,
        policy=build_private_run_policy(),
        contracts_root=Path.cwd(),
        policy_root=tmp_path,
        reviewer_label="external-lattice-review",
    )

    written = json.loads((tmp_path / review_out).read_text(encoding="utf-8"))
    assert written == packet
    assert packet["schema_version"] == LATTICE_ESTIMATOR_BASELINE_REVIEW_PACKET_SCHEMA
    assert packet["report"] == {
        "path": "private/reports/lattice_estimator_baseline_review_packet.json",
        "private": True,
    }
    assert packet["review_status"] == {
        "state": "pending_expert_review",
        "reviewer_label": "external-lattice-review",
        "numeric_promotion_allowed": False,
        "public_claim_language_approved": False,
    }
    assert packet["baseline_verification"]["accepted"] is True
    assert packet["summary"] == {
        "algorithm_keys": ["bdd", "bkw", "dual", "dual_hybrid", "usvp"],
        "contract_count": 5,
        "numeric_result_count": 5,
        "raw_output_digest_count": 5,
        "result_count": 5,
        "review_question_count": 5,
    }
    assert packet["safety"] == {
        "contains_attack_plan_payloads": False,
        "contains_numeric_values": False,
        "contains_raw_estimator_output": False,
        "private_report": True,
        "publication_allowed": False,
        "public_release_ok": False,
        "requires_expert_review": True,
        "security_claim": False,
    }
    assert [entry["algorithm_key"] for entry in packet["result_evidence"]] == [
        "bdd",
        "bkw",
        "dual",
        "dual_hybrid",
        "usvp",
    ]
    assert all(
        len(entry["raw_output_sha256"]) == 64
        for entry in packet["result_evidence"]
    )
    encoded = json.dumps(packet, sort_keys=True)
    assert '"time_bits":' not in encoded
    assert '"memory_bits":' not in encoded
    assert '"raw_output":' not in encoded
    assert '"attack_plan":' not in encoded

    verification = verify_lattice_estimator_baseline_review_packet(
        tmp_path / review_out,
        baseline_report_path=tmp_path / baseline_out,
        contracts_root=Path.cwd(),
    )
    assert verification["accepted"] is True
    assert verification["failures"] == []


def test_lattice_estimator_baseline_review_packet_rejects_numeric_leakage(
    tmp_path: Path,
) -> None:
    baseline_out = Path("private/reports/lattice_estimator_baseline_run.json")
    write_lattice_estimator_baseline_run(
        baseline_out,
        contracts_path=Path("docs/lattice_estimator_baseline_contracts.json"),
        policy=build_private_run_policy(),
        adapter=LatticeEstimatorAdapter(backend=FakeBaselineBackend()),
        contracts_root=Path.cwd(),
        policy_root=tmp_path,
        run_id="unit-baseline-run-for-review-leakage",
    )
    review_out = Path("private/reports/lattice_estimator_baseline_review_packet.json")
    packet = write_lattice_estimator_baseline_review_packet(
        review_out,
        baseline_report_path=tmp_path / baseline_out,
        policy=build_private_run_policy(),
        contracts_root=Path.cwd(),
        policy_root=tmp_path,
    )
    packet["result_evidence"][0]["time_bits"] = 57.25
    (tmp_path / review_out).write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verification = verify_lattice_estimator_baseline_review_packet(
        tmp_path / review_out,
        baseline_report_path=tmp_path / baseline_out,
        contracts_root=Path.cwd(),
    )

    assert verification["accepted"] is False
    assert any("numeric field" in failure for failure in verification["failures"])


def test_lattice_estimator_baseline_review_packet_rejects_unexpected_numeric_evidence(
    tmp_path: Path,
) -> None:
    baseline_out = Path("private/reports/lattice_estimator_baseline_run.json")
    write_lattice_estimator_baseline_run(
        baseline_out,
        contracts_path=Path("docs/lattice_estimator_baseline_contracts.json"),
        policy=build_private_run_policy(),
        adapter=LatticeEstimatorAdapter(backend=FakeBaselineBackend()),
        contracts_root=Path.cwd(),
        policy_root=tmp_path,
        run_id="unit-baseline-run-for-review-numeric-evidence",
    )
    review_out = Path("private/reports/lattice_estimator_baseline_review_packet.json")
    packet = write_lattice_estimator_baseline_review_packet(
        review_out,
        baseline_report_path=tmp_path / baseline_out,
        policy=build_private_run_policy(),
        contracts_root=Path.cwd(),
        policy_root=tmp_path,
    )
    packet["result_evidence"][0]["cost_summary"] = {"rop": 57.25}
    (tmp_path / review_out).write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verification = verify_lattice_estimator_baseline_review_packet(
        tmp_path / review_out,
        baseline_report_path=tmp_path / baseline_out,
        contracts_root=Path.cwd(),
    )

    assert verification["accepted"] is False
    assert verification["summary"]["contains_numeric_values"] is True
    assert any("cost_summary.rop" in failure for failure in verification["failures"])


def test_lattice_estimator_baseline_review_packet_rejects_public_output_path(
    tmp_path: Path,
) -> None:
    baseline_out = Path("private/reports/lattice_estimator_baseline_run.json")
    write_lattice_estimator_baseline_run(
        baseline_out,
        contracts_path=Path("docs/lattice_estimator_baseline_contracts.json"),
        policy=build_private_run_policy(),
        adapter=LatticeEstimatorAdapter(backend=FakeBaselineBackend()),
        contracts_root=Path.cwd(),
        policy_root=tmp_path,
        run_id="unit-baseline-run-for-review-public-path",
    )

    with pytest.raises(ValueError, match="forbidden public root"):
        write_lattice_estimator_baseline_review_packet(
            Path("public/lattice_estimator_baseline_review_packet.json"),
            baseline_report_path=tmp_path / baseline_out,
            policy=build_private_run_policy(),
            contracts_root=Path.cwd(),
            policy_root=tmp_path,
        )


def test_lattice_estimator_baseline_run_records_unpinned_backend_as_errors() -> None:
    backend = FakeBaselineBackend()
    backend.commit = "not-reviewed"

    report = build_lattice_estimator_baseline_run(
        contracts_path=Path("docs/lattice_estimator_baseline_contracts.json"),
        adapter=LatticeEstimatorAdapter(backend=backend),
        root=Path.cwd(),
        run_id="unit-unpinned-baseline-run",
    )

    assert report["summary"] == {
        "all_successful_results_from_pinned_commit": False,
        "contract_count": 5,
        "error_results": 5,
        "numeric_result_count": 0,
        "ok_results": 0,
        "public_release_ok": False,
        "security_claim": False,
        "unsupported_results": 0,
    }
    assert backend.algorithm_keys == []
    assert all(entry["evaluation_status"] == "error" for entry in report["results"])
    assert all(entry["time_bits"] is None for entry in report["results"])
    assert all(entry["memory_bits"] is None for entry in report["results"])
    assert all(entry["numeric_output_private"] is False for entry in report["results"])
    assert all(
        "does not match reviewed pin" in entry["warnings"][0]
        for entry in report["results"]
    )


def test_write_lattice_estimator_checkout_preflight_private_report(
    tmp_path: Path,
) -> None:
    source, commit = _write_fake_lattice_estimator_checkout(tmp_path)
    out = Path("private/reports/lattice_estimator_checkout_preflight.json")

    report = write_lattice_estimator_checkout_preflight(
        out,
        source_path=source,
        policy=build_private_run_policy(),
        policy_root=tmp_path,
        required_commit=commit,
    )

    written = json.loads((tmp_path / out).read_text(encoding="utf-8"))

    assert written == report
    assert report["schema_version"] == LATTICE_ESTIMATOR_CHECKOUT_PREFLIGHT_SCHEMA
    assert report["report"] == {
        "path": "private/reports/lattice_estimator_checkout_preflight.json",
        "private": True,
    }
    assert report["upstream"] == {
        "repository": "https://github.com/malb/lattice-estimator",
        "pinned_commit": commit,
        "pin_source": "docs/lattice_estimator_manifest.json",
    }
    assert report["source_checkout"]["path"] == source.as_posix()
    assert report["source_checkout"]["git"] == {
        "head_commit": commit,
        "head_matches_required_pin": True,
        "remote_origin": "https://github.com/malb/lattice-estimator",
        "remote_matches_upstream": True,
        "working_tree_clean": True,
    }
    assert report["source_checkout"]["python_entrypoints"] == {
        "estimator_package": True,
        "estimator_module": False,
    }
    assert report["readiness"] == {
        "ready_for_private_baseline_run": True,
        "requires_expert_review_before_publication": True,
        "failure_count": 0,
    }
    assert report["safety"] == {
        "imports_upstream_python": False,
        "executes_estimator": False,
        "numeric_reference_outputs_committed": False,
        "publication_allowed": False,
        "security_claim": False,
        "writes_only_allowed_private_roots": True,
    }
    assert report["failures"] == []
    assert not (source / "estimator" / "IMPORT_MARKER").exists()


def test_lattice_estimator_checkout_preflight_records_pin_mismatch(
    tmp_path: Path,
) -> None:
    source, commit = _write_fake_lattice_estimator_checkout(tmp_path)

    report = build_lattice_estimator_checkout_preflight(
        source_path=source,
        required_commit="0" * 40,
    )

    assert report["source_checkout"]["git"]["head_commit"] == commit
    assert report["source_checkout"]["git"]["head_matches_required_pin"] is False
    assert report["readiness"] == {
        "ready_for_private_baseline_run": False,
        "requires_expert_review_before_publication": True,
        "failure_count": 1,
    }
    assert report["failures"] == [
        (
            f"Local Lattice Estimator checkout commit {commit} does not match "
            "reviewed pin 0000000000000000000000000000000000000000."
        )
    ]
    assert not (source / "estimator" / "IMPORT_MARKER").exists()


def test_lattice_estimator_checkout_preflight_rejects_dirty_checkout(
    tmp_path: Path,
) -> None:
    source, commit = _write_fake_lattice_estimator_checkout(tmp_path)
    (source / "README.md").write_text("dirty local edit\n", encoding="utf-8")

    report = build_lattice_estimator_checkout_preflight(
        source_path=source,
        required_commit=commit,
    )

    assert report["source_checkout"]["git"] == {
        "head_commit": commit,
        "head_matches_required_pin": True,
        "remote_origin": "https://github.com/malb/lattice-estimator",
        "remote_matches_upstream": True,
        "working_tree_clean": False,
    }
    assert report["readiness"] == {
        "ready_for_private_baseline_run": False,
        "requires_expert_review_before_publication": True,
        "failure_count": 1,
    }
    assert report["failures"] == [
        "Local Lattice Estimator checkout working tree is not clean."
    ]
    assert not (source / "estimator" / "IMPORT_MARKER").exists()


def test_lattice_estimator_checkout_preflight_rejects_wrong_remote(
    tmp_path: Path,
) -> None:
    source, commit = _write_fake_lattice_estimator_checkout(tmp_path)
    subprocess.run(
        ["git", "remote", "set-url", "origin", "https://example.com/fork.git"],
        cwd=source,
        check=True,
        capture_output=True,
    )

    report = build_lattice_estimator_checkout_preflight(
        source_path=source,
        required_commit=commit,
    )

    assert report["source_checkout"]["git"] == {
        "head_commit": commit,
        "head_matches_required_pin": True,
        "remote_origin": "https://example.com/fork.git",
        "remote_matches_upstream": False,
        "working_tree_clean": True,
    }
    assert report["readiness"] == {
        "ready_for_private_baseline_run": False,
        "requires_expert_review_before_publication": True,
        "failure_count": 1,
    }
    assert report["failures"] == [
        (
            "Local Lattice Estimator checkout origin remote "
            "https://example.com/fork.git does not match reviewed upstream "
            "https://github.com/malb/lattice-estimator."
        )
    ]
    assert not (source / "estimator" / "IMPORT_MARKER").exists()


def test_lattice_estimator_checkout_preflight_rejects_public_output_path(
    tmp_path: Path,
) -> None:
    source, commit = _write_fake_lattice_estimator_checkout(tmp_path)

    with pytest.raises(ValueError, match="forbidden public root"):
        write_lattice_estimator_checkout_preflight(
            Path("docs/lattice_estimator_checkout_preflight.json"),
            source_path=source,
            policy=build_private_run_policy(),
            policy_root=tmp_path,
            required_commit=commit,
        )


def test_write_lattice_estimator_runtime_preflight_private_report(
    tmp_path: Path,
) -> None:
    sage = _write_fake_sage(tmp_path)
    out = Path("private/reports/lattice_estimator_runtime_preflight.json")

    report = write_lattice_estimator_runtime_preflight(
        out,
        sage_command=sage.as_posix(),
        policy=build_private_run_policy(),
        policy_root=tmp_path,
    )

    written = json.loads((tmp_path / out).read_text(encoding="utf-8"))

    assert written == report
    assert report["schema_version"] == LATTICE_ESTIMATOR_RUNTIME_PREFLIGHT_SCHEMA
    assert report["report"] == {
        "path": "private/reports/lattice_estimator_runtime_preflight.json",
        "private": True,
    }
    assert report["runtime_environment"] == {
        "sage_command": sage.as_posix(),
        "sage_python_command": f"{sage.as_posix()} -python",
        "sage_found": True,
        "sage_version": "SageMath version 10.4",
        "sage_python_imports_sage": True,
        "sage_python_probe": "import sage.all",
    }
    assert report["readiness"] == {
        "ready_for_private_lattice_estimator_import": True,
        "requires_checkout_preflight": True,
        "requires_matching_lattice_estimator_pin": True,
        "failure_count": 0,
    }
    assert report["safety"] == {
        "executes_sage_python_probe": True,
        "imports_upstream_python": False,
        "executes_estimator": False,
        "external_network_access": False,
        "numeric_reference_outputs_committed": False,
        "publication_allowed": False,
        "security_claim": False,
        "writes_only_allowed_private_roots": True,
    }
    assert report["failures"] == []


def test_lattice_estimator_runtime_preflight_accepts_separate_sage_python_command(
    tmp_path: Path,
) -> None:
    sage = _write_fake_sage(tmp_path)
    sage_python = _write_fake_sage_python_command(tmp_path)

    report = build_lattice_estimator_runtime_preflight(
        sage_command=sage.as_posix(),
        sage_python_command=f"{sage_python.as_posix()} --env",
    )

    assert report["runtime_environment"] == {
        "sage_command": sage.as_posix(),
        "sage_python_command": f"{sage_python.as_posix()} --env",
        "sage_found": True,
        "sage_version": "SageMath version 10.4",
        "sage_python_imports_sage": True,
        "sage_python_probe": "import sage.all",
    }
    assert report["readiness"]["ready_for_private_lattice_estimator_import"] is True
    assert report["failures"] == []


def test_lattice_estimator_runtime_preflight_records_missing_sage(
    tmp_path: Path,
) -> None:
    missing_sage = tmp_path / "missing-sage"

    report = build_lattice_estimator_runtime_preflight(
        sage_command=missing_sage.as_posix(),
    )

    assert report["runtime_environment"] == {
        "sage_command": missing_sage.as_posix(),
        "sage_python_command": f"{missing_sage.as_posix()} -python",
        "sage_found": False,
        "sage_version": None,
        "sage_python_imports_sage": False,
        "sage_python_probe": "import sage.all",
    }
    assert report["readiness"] == {
        "ready_for_private_lattice_estimator_import": False,
        "requires_checkout_preflight": True,
        "requires_matching_lattice_estimator_pin": True,
        "failure_count": 1,
    }
    assert report["failures"] == [
        f"Sage executable not found: {missing_sage.as_posix()}."
    ]


def test_lattice_estimator_runtime_preflight_records_sage_python_probe_failure(
    tmp_path: Path,
) -> None:
    sage = _write_fake_sage(tmp_path, import_ok=False)

    report = build_lattice_estimator_runtime_preflight(
        sage_command=sage.as_posix(),
    )

    assert report["runtime_environment"]["sage_found"] is True
    assert report["runtime_environment"]["sage_version"] == "SageMath version 10.4"
    assert report["runtime_environment"]["sage_python_imports_sage"] is False
    assert report["readiness"] == {
        "ready_for_private_lattice_estimator_import": False,
        "requires_checkout_preflight": True,
        "requires_matching_lattice_estimator_pin": True,
        "failure_count": 1,
    }
    assert report["failures"] == [
        (
            "Sage Python probe failed with exit code 1: "
            "ModuleNotFoundError: sage"
        )
    ]


def test_lattice_estimator_runtime_preflight_rejects_public_output_path(
    tmp_path: Path,
) -> None:
    sage = _write_fake_sage(tmp_path)

    with pytest.raises(ValueError, match="forbidden public root"):
        write_lattice_estimator_runtime_preflight(
            Path("docs/lattice_estimator_runtime_preflight.json"),
            sage_command=sage.as_posix(),
            policy=build_private_run_policy(),
            policy_root=tmp_path,
        )


def test_lattice_estimator_runtime_preflight_verify_accepts_ready_report(
    tmp_path: Path,
) -> None:
    sage = _write_fake_sage(tmp_path)
    out = tmp_path / "runtime_preflight.json"
    report = build_lattice_estimator_runtime_preflight(
        sage_command=sage.as_posix(),
        report_path=Path("private/reports/lattice_estimator_runtime_preflight.json"),
    )
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    verification = verify_lattice_estimator_runtime_preflight(out)

    assert verification == {
        "schema_version": (
            "agades.pqc.lattice_estimator_runtime_preflight_verification.v1"
        ),
        "preflight_path": out.as_posix(),
        "accepted": True,
        "summary": {
            "failure_count": 0,
            "ready_for_private_lattice_estimator_import": True,
            "sage_found": True,
            "sage_python_imports_sage": True,
            "security_claim": False,
        },
        "failures": [],
    }


def test_lattice_estimator_runtime_preflight_verify_accepts_closed_failure_report(
    tmp_path: Path,
) -> None:
    out = tmp_path / "runtime_preflight_missing_sage.json"
    missing_sage = tmp_path / "missing-sage"
    report = build_lattice_estimator_runtime_preflight(
        sage_command=missing_sage.as_posix(),
        report_path=Path("private/reports/lattice_estimator_runtime_preflight.json"),
    )
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    verification = verify_lattice_estimator_runtime_preflight(out)

    assert verification["accepted"] is True
    assert verification["summary"] == {
        "failure_count": 1,
        "ready_for_private_lattice_estimator_import": False,
        "sage_found": False,
        "sage_python_imports_sage": False,
        "security_claim": False,
    }
    assert verification["failures"] == []


def test_lattice_estimator_runtime_preflight_verify_rejects_unsafe_report(
    tmp_path: Path,
) -> None:
    out = tmp_path / "runtime_preflight_unsafe.json"
    report = build_lattice_estimator_runtime_preflight(
        sage_command=(tmp_path / "missing-sage").as_posix(),
        report_path=Path("private/reports/lattice_estimator_runtime_preflight.json"),
    )
    report["report"]["private"] = False
    report["safety"]["security_claim"] = True
    report["safety"]["imports_upstream_python"] = True
    report["readiness"]["failure_count"] = 0
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    verification = verify_lattice_estimator_runtime_preflight(out)

    assert verification["accepted"] is False
    assert (
        "Lattice Estimator runtime preflight report must stay private."
        in verification["failures"]
    )
    assert (
        "Lattice Estimator runtime preflight safety.security_claim must be false."
        in verification["failures"]
    )
    assert (
        "Lattice Estimator runtime preflight must not import upstream Python."
        in verification["failures"]
    )
    assert (
        "Lattice Estimator runtime preflight failure_count must match failures."
        in verification["failures"]
    )
