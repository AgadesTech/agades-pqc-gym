from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.integrations.reviewer_governance import (
    REVIEWER_GOVERNANCE_VERIFICATION_SCHEMA,
    build_reviewer_governance,
    verify_reviewer_governance,
    write_reviewer_governance,
)

GOVERNANCE_PATH = Path("docs/reviewer_governance.json")


def test_reviewer_governance_defines_family_roles_and_review_gates(
    tmp_path: Path,
) -> None:
    out = tmp_path / "reviewer_governance.json"

    governance = write_reviewer_governance(out)

    assert governance == build_reviewer_governance()
    assert json.loads(out.read_text(encoding="utf-8")) == governance
    assert governance["schema_version"] == "agades.pqc.reviewer_governance.v1"
    assert {entry["family"] for entry in governance["family_reviewers"]} == {
        family.value for family in TargetFamily
    }
    assert governance["formal_backend_policy"] == {
        "primary": {
            "backend": "lean4",
            "library": "mathlib",
            "required_for_security_claims": True,
        },
        "smt_assist": {
            "backend": "z3",
            "scope": "optional_finite_decidable_obligations_only",
            "may_replace_primary_backend": False,
        },
    }
    assert governance["approval_gates"]["formal_artifact_review_gate"] == {
        "required_role_groups": [
            "family_cryptography_reviewer",
            "formal_methods_reviewer",
            "release_boundary_reviewer",
        ],
        "security_claim_requires_review": True,
        "security_claim_allowed_without_review": False,
        "unreviewed_proof_artifact_status": "pending_review",
    }
    assert governance["private_training_review"]["publication_allowed"] is False
    assert (
        governance["private_training_review"]["train_traces_publication_allowed"]
        is False
    )
    assert governance["formal_artifact_binding"]["formal_family_coverage_path"] == (
        "docs/formal_family_coverage.json"
    )
    assert governance["formal_artifact_binding"][
        "formal_obligation_ledger_path"
    ] == "docs/formal_obligation_ledger.json"
    assert governance["formal_artifact_binding"]["formal_estimator_model_path"] == (
        "docs/formal_estimator_model.json"
    )
    assert governance["formal_artifact_binding"]["formal_operator_semantics_path"] == (
        "docs/formal_operator_semantics.json"
    )
    assert governance["formal_artifact_binding"]["mvp_vertical_proof_artifacts"] == {
        "LWE": "docs/formal_lattice_primal_usvp_proof_artifact.json",
        "MLWE": "docs/formal_lattice_mlwe_module_hypothesis_proof_artifact.json",
    }
    assert governance["review_artifact_format"] == {
        "schema_version": "agades.pqc.review_artifact.v1",
        "status_field": "review.status",
        "supported_statuses": ["pending_review", "reviewed", "rejected"],
        "required_fields": [
            "artifact_path",
            "artifact_sha256",
            "target_family",
            "review.status",
            "review.required_reviewers",
            "review.claim_boundary",
            "review.evidence.schema_version",
            "review.evidence.status",
            "review.evidence.covered_reviewer_roles",
            "review.evidence.claim_allowed",
            "review.evidence.artifact_binding",
            "review.evidence.evidence_sha256",
        ],
        "attached_evidence_contract": {
            "schema_version": "agades.pqc.formal.review_evidence.v1",
            "status": "attached",
            "claim_allowed": False,
            "hash": "stable_sha256_without_evidence_sha256",
            "artifact_binding_fields": [
                "attack_plan_id",
                "attack_plan_canonical_sha256",
                "family",
                "estimator_result_binding_status",
                "review_status",
                "required_reviewers",
                "proof_obligation_sha256",
                "claim_boundary",
            ],
        },
        "status_before_domain_claim": "reviewed",
        "unassigned_role_status": "role_required_unassigned",
    }
    assert governance["linked_artifacts"]["formal_family_coverage"]["path"] == (
        "docs/formal_family_coverage.json"
    )
    assert governance["linked_artifacts"]["formal_estimator_model"]["path"] == (
        "docs/formal_estimator_model.json"
    )
    assert governance["linked_artifacts"]["formal_obligation_ledger"]["path"] == (
        "docs/formal_obligation_ledger.json"
    )
    assert governance["linked_artifacts"]["formal_operator_semantics"]["path"] == (
        "docs/formal_operator_semantics.json"
    )
    assert governance["linked_artifacts"]["formal_lean_backend"]["path"] == (
        "docs/formal_lean_backend.json"
    )
    assert governance["linked_artifacts"]["formal_mlwe_proof_artifact"]["path"] == (
        "docs/formal_lattice_mlwe_module_hypothesis_proof_artifact.json"
    )


def test_committed_reviewer_governance_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "reviewer_governance.json"

    write_reviewer_governance(generated)

    assert GOVERNANCE_PATH.read_bytes() == generated.read_bytes()


def test_reviewer_governance_verify_accepts_committed_artifact() -> None:
    result = verify_reviewer_governance(GOVERNANCE_PATH)

    assert result == {
        "schema_version": REVIEWER_GOVERNANCE_VERIFICATION_SCHEMA,
        "governance_path": GOVERNANCE_PATH.as_posix(),
        "accepted": True,
        "summary": {
            "family_reviewers": 9,
            "role_groups": 3,
            "approval_gates": 4,
            "linked_artifacts": 12,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_reviewer_governance_rejects_missing_family_reviewer(
    tmp_path: Path,
) -> None:
    path = tmp_path / "reviewer_governance.json"
    governance = build_reviewer_governance()
    governance["family_reviewers"] = [
        entry
        for entry in governance["family_reviewers"]
        if entry["family"] != TargetFamily.CODE_BASED.value
    ]
    path.write_text(json.dumps(governance, indent=2, sort_keys=True) + "\n")

    result = verify_reviewer_governance(path)

    assert result["accepted"] is False
    assert (
        "Reviewer governance must define one family reviewer for each TargetFamily."
        in result["failures"]
    )


def test_reviewer_governance_rejects_smt_as_primary_backend(
    tmp_path: Path,
) -> None:
    path = tmp_path / "reviewer_governance.json"
    governance = build_reviewer_governance()
    governance["formal_backend_policy"]["primary"]["backend"] = "z3"
    governance["formal_backend_policy"]["smt_assist"][
        "may_replace_primary_backend"
    ] = True
    path.write_text(json.dumps(governance, indent=2, sort_keys=True) + "\n")

    result = verify_reviewer_governance(path)

    assert result["accepted"] is False
    assert (
        "Reviewer governance primary formal backend must be Lean 4 + Mathlib."
        in result["failures"]
    )
    assert (
        "SMT assistance must not replace the primary Lean backend."
        in result["failures"]
    )


def test_reviewer_governance_rejects_unreviewed_security_claims(
    tmp_path: Path,
) -> None:
    path = tmp_path / "reviewer_governance.json"
    governance = build_reviewer_governance()
    gate = governance["approval_gates"]["formal_artifact_review_gate"]
    gate["security_claim_allowed_without_review"] = True
    governance["private_training_review"]["publication_allowed"] = True
    path.write_text(json.dumps(governance, indent=2, sort_keys=True) + "\n")

    result = verify_reviewer_governance(path)

    assert result["accepted"] is False
    assert (
        "Security claims must not be allowed without domain and formal review."
        in result["failures"]
    )
    assert "Private training datasets must never be public." in result["failures"]


def test_reviewer_governance_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "reviewer_governance.json"

    write_result = CliRunner().invoke(
        app,
        ["reviewer-governance", "--out", str(out)],
    )
    verify_result = CliRunner().invoke(
        app,
        ["reviewer-governance-verify", "--governance", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"reviewer_governance={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
