from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.formal.artifacts import (
    build_attack_plan_proof_artifact,
    verify_attack_plan_proof_artifact,
    write_attack_plan_proof_artifact,
)


def test_lattice_attack_plan_proof_artifact_binds_plan_obligations_and_lean() -> None:
    artifact = build_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json")
    )

    assert artifact["schema_version"] == "agades.pqc.formal.proof_artifact.v1"
    assert artifact["backend"] == {
        "primary": "lean4",
        "library": "mathlib",
        "smt_assist": "z3_optional_finite_decidable_obligations_only",
    }
    assert artifact["attack_plan"]["id"] == "lattice_primal_usvp_toy_v1"
    assert len(artifact["attack_plan"]["sha256"]) == 64
    assert artifact["family"] == "LWE"
    assert artifact["operator_semantics"][0] == {
        "operator": "primal_usvp",
        "semantics_id": "agades.pqc.operator_semantics.lattice.primal_usvp.v1",
        "lean_namespace": "AgadesPQC.Lattice.PrimalUSVP",
    }
    assert {
        obligation["obligation_id"] for obligation in artifact["proof_obligations"]
    } == {
        "target.lwe.parameters.positive",
        "target.lwe.distributions.present",
        "operator.primal_usvp.beta.valid_range",
        "estimator.boundary.no_security_claim",
    }
    assert artifact["attack_plan"]["canonical_sha256"]
    assert artifact["estimator_result_binding"] == {
        "status": "not_attached",
        "path": None,
        "sha256": None,
        "canonical_sha256": None,
        "claim_allowed": False,
        "notes": (
            "No estimator result is attached; the artifact cannot support a "
            "security claim."
        ),
    }
    assert artifact["proof_obligations"][0]["status"] == "pending_review"
    assert artifact["review"]["required_reviewers"] == [
        "lattice_cryptographer",
        "formal_methods_reviewer",
        "release_boundary_reviewer",
    ]
    assert artifact["artifact_sha256"] == artifact["artifact_sha256"]


def test_schema_only_code_based_proof_artifact_refuses_fake_estimator_obligations(
) -> None:
    artifact = build_attack_plan_proof_artifact(
        Path("examples/attack_plans/code_based_isd_placeholder.json")
    )

    assert artifact["family"] == "CODE_BASED"
    assert artifact["estimator_model"]["status"] == "unsupported"
    assert artifact["estimator_model"]["no_fake_estimate"] is True
    assert any(
        obligation["obligation_id"] == "family.code_based.schema_only.no_estimate"
        for obligation in artifact["proof_obligations"]
    )


def test_write_and_verify_attack_plan_proof_artifact(tmp_path: Path) -> None:
    out = tmp_path / "proof_artifact.json"

    artifact = write_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
        out,
    )
    result = verify_attack_plan_proof_artifact(out)

    assert json.loads(out.read_text(encoding="utf-8")) == artifact
    assert result == {
        "schema_version": "agades.pqc.formal.proof_artifact_verification.v1",
        "artifact_path": out.as_posix(),
        "accepted": True,
        "summary": {
            "operator_semantics": 1,
            "family_invariants": 2,
            "proof_obligations": 4,
            "lean_theorems": 4,
            "estimator_result_attached": False,
            "required_reviewers": 3,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_committed_lattice_proof_artifact_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "proof_artifact.json"
    committed = Path("docs/formal_lattice_primal_usvp_proof_artifact.json")

    write_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
        generated,
    )

    assert committed.read_bytes() == generated.read_bytes()


def test_verify_attack_plan_proof_artifact_rejects_tampering(
    tmp_path: Path,
) -> None:
    out = tmp_path / "proof_artifact.json"
    artifact = write_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
        out,
    )
    artifact["proof_obligations"][0]["lean_theorem"] = "AgadesPQC.Fake.theorem"
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")

    result = verify_attack_plan_proof_artifact(out)

    assert result["accepted"] is False
    assert "Proof artifact hash does not match its payload." in result["failures"]
    assert "Proof obligations do not match the AttackPlan." in result["failures"]


def test_formal_proof_artifact_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "proof_artifact.json"

    write_result = CliRunner().invoke(
        app,
        [
            "formal-proof-artifact",
            "examples/attack_plans/lattice_primal_usvp_toy.json",
            "--out",
            str(out),
        ],
    )
    verify_result = CliRunner().invoke(
        app,
        ["formal-proof-artifact-verify", "--artifact", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"formal_proof_artifact={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
