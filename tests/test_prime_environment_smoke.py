from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.prime_environment_smoke import (
    build_prime_environment_smoke_report,
    verify_prime_environment_smoke_report,
    write_prime_environment_smoke_report,
)


def test_prime_environment_smoke_report_exercises_packaged_verifier(
    tmp_path: Path,
) -> None:
    out = tmp_path / "prime_environment_smoke.json"

    report = write_prime_environment_smoke_report(out)

    assert report == build_prime_environment_smoke_report()
    assert json.loads(out.read_text(encoding="utf-8")) == report
    assert report["schema_version"] == "agades.pqc.prime_environment_smoke.v1"
    assert report["accepted"] is True
    assert report["environment"] == {
        "environment_dir": "prime_intellect/verifiers_environment",
        "entrypoint": "agades_pqc_verifier_env:load_environment",
        "imports_without_verifiers": True,
        "module_path": (
            "prime_intellect/verifiers_environment/agades_pqc_verifier_env.py"
        ),
    }
    assert report["dataset"] == {
        "data_file_count": 79,
        "dataset_rows": 79,
        "default_attack_plan_id": "lattice_primal_usvp_toy_v1",
        "families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
            "NTRU",
            "SIS",
        ],
        "mirrors_packaged_data": True,
    }
    assert report["scoring"] == {
        "accepted_score": 1.0,
        "accepted_rubric_scores": {
            "accepted_attack_plan": 1.0,
            "single_json_object": 1.0,
            "formal_validity": 1.0,
            "cryptographic_applicability": 1.0,
            "no_security_overclaim": 1.0,
            "student_readability": 1.0,
            "reproducibility": 1.0,
            "reviewer_quality": 1.0,
            "task_match": 1.0,
            "proof_obligation_coverage": 1.0,
        },
        "challenge_broken_score": 0.0,
        "challenge_repaired_score": 1.0,
        "challenge_rows": 12,
        "challenge_schema": "agades.pqc.prime.challenge_scorecard.v1",
        "challenge_types": [
            "claims_guard_repair",
            "contextual_claims_guard_decoy_repair",
            "semantic_mutation_repair",
            "wrong_family_decoy_repair",
            "multi_trap_repair",
            "contextual_multi_trap_repair",
            "implicit_operator_semantics_repair",
            "reviewer_decision",
            "operator_mismatch_repair",
            "operator_param_mismatch_repair",
            "missing_hypothesis_repair",
            "invented_complexity_repair",
        ],
        "formal_artifact_binding_schema": (
            "agades.pqc.rl.formal_artifact_binding.v1"
        ),
        "invalid_json_score": 0.0,
        "prefixed_json_score": 0.0,
        "requires_single_json_object": True,
        "review_governance_binding_schema": (
            "agades.pqc.formal.proof_artifact.reviewer_governance_binding.v1"
        ),
        "review_governance_ok": True,
        "reviewer_quality": 1.0,
        "rubric_terms": [
            "accepted_attack_plan",
            "single_json_object",
            "formal_validity",
            "cryptographic_applicability",
            "no_security_overclaim",
            "student_readability",
            "reproducibility",
            "reviewer_quality",
            "task_match",
            "proof_obligation_coverage",
        ],
        "unsupported_refusal_broken_score": 0.0,
        "unsupported_refusal_rows": 1,
        "unsupported_refusal_score": 1.0,
        "unsupported_score": 0.0,
    }
    assert report["optional_dependencies"] == {
        "load_environment_boundary_ok": True,
        "required_packages": ["datasets", "verifiers"],
    }
    assert report["safety"] == {
        "arbitrary_code_execution": False,
        "contains_private_traces": False,
        "live_targeting": False,
        "publishes_private_candidates": False,
        "security_claim": False,
    }
    assert report["release_gates"] == [
        "uv run pytest tests/test_prime_environment_smoke.py -q",
        "uv run agades-pqc prime-environment-smoke --out "
        "reports/prime_environment_smoke.json",
        "uv run agades-pqc prime-environment-smoke-verify --report "
        "reports/prime_environment_smoke.json",
        "uv build prime_intellect/verifiers_environment",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]
    assert report["failures"] == []


def test_committed_prime_environment_smoke_report_is_in_sync(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "prime_environment_smoke.json"
    committed = Path("reports/prime_environment_smoke.json")

    write_prime_environment_smoke_report(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_prime_environment_smoke_verify_accepts_committed_report() -> None:
    result = verify_prime_environment_smoke_report(
        Path("reports/prime_environment_smoke.json")
    )

    assert result == {
        "schema_version": "agades.pqc.prime_environment_smoke_verification.v1",
        "report_path": "reports/prime_environment_smoke.json",
        "accepted": True,
        "summary": {
            "accepted_score": 1.0,
            "challenge_broken_score": 0.0,
            "challenge_repaired_score": 1.0,
                "challenge_rows": 12,
            "dataset_rows": 79,
            "failure_count": 0,
            "formal_artifact_binding_schema": (
                "agades.pqc.rl.formal_artifact_binding.v1"
            ),
            "imports_without_verifiers": True,
            "load_environment_boundary_ok": True,
            "prefixed_json_score": 0.0,
            "review_governance_ok": True,
            "reviewer_quality": 1.0,
            "rubric_terms": 10,
            "unsupported_refusal_score": 1.0,
            "unsupported_score": 0.0,
        },
        "failures": [],
    }


def test_prime_environment_smoke_verify_rejects_stale_report(
    tmp_path: Path,
) -> None:
    out = tmp_path / "prime_environment_smoke.json"
    report = build_prime_environment_smoke_report()
    report["safety"]["security_claim"] = True
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    result = verify_prime_environment_smoke_report(out)

    assert result["accepted"] is False
    assert "Prime environment smoke report is not in sync." in result["failures"]
    assert "Prime environment smoke report security_claim must be false." in result[
        "failures"
    ]


def test_prime_environment_smoke_cli_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "prime_environment_smoke.json"

    result = CliRunner().invoke(
        app,
        ["prime-environment-smoke", "--out", str(out)],
    )

    assert result.exit_code == 0
    assert f"prime_environment_smoke={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["accepted"] is True


def test_prime_environment_smoke_verify_cli_accepts_current_report() -> None:
    result = CliRunner().invoke(
        app,
        [
            "prime-environment-smoke-verify",
            "--report",
            "reports/prime_environment_smoke.json",
        ],
    )

    assert result.exit_code == 0
    assert "agades.pqc.prime_environment_smoke_verification.v1" in result.output
    assert '"accepted": true' in result.output
