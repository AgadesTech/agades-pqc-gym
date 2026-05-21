from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.formal.smt_assist import (
    FORMAL_SMT_ASSIST_VERIFICATION_SCHEMA,
    build_formal_smt_assist_contract,
    verify_formal_smt_assist_contract,
    write_formal_smt_assist_contract,
)

SMT_CONTRACT_PATH = Path("docs/formal_smt_assist_contract.json")


def test_formal_smt_assist_contract_scopes_z3_to_finite_decidable_checks(
    tmp_path: Path,
) -> None:
    out = tmp_path / "formal_smt_assist_contract.json"

    contract = write_formal_smt_assist_contract(out)

    assert contract == build_formal_smt_assist_contract()
    assert json.loads(out.read_text(encoding="utf-8")) == contract
    assert contract["schema_version"] == "agades.pqc.formal.smt_assist_contract.v1"
    assert contract["backend_policy"] == {
        "primary_backend": "lean4",
        "primary_library": "mathlib",
        "assist_backend": "z3",
        "assist_role": "optional_secondary_check",
        "may_replace_primary_backend": False,
        "may_discharge_security_claims": False,
        "requires_lean_type_rule": True,
        "requires_reviewer_approval": True,
    }
    assert contract["scope"] == {
        "allowed_obligation_kinds": [
            "target_invariant",
            "operator_precondition",
        ],
        "excluded_obligation_kinds": [
            "schema_only_boundary",
            "family_applicability_boundary",
            "estimator_claim_boundary",
        ],
        "allowed_theory_fragments": [
            "quantifier_free_integer_arithmetic",
            "finite_enumeration_membership",
            "boolean_shape_constraints",
        ],
        "forbidden_uses": [
            "cryptographic_security_claim",
            "estimator_cost_model_validation",
            "replacement_for_lean_theorem",
            "replacement_for_crypto_domain_review",
            "public_claim_automation",
        ],
    }
    assert contract["summary"] == {
        "total_obligations": 22,
        "candidate_obligations": 6,
        "excluded_obligations": 16,
        "candidate_kinds": {
            "operator_precondition": 1,
            "target_invariant": 5,
        },
        "excluded_kinds": {
            "estimator_claim_boundary": 9,
            "family_applicability_boundary": 4,
            "schema_only_boundary": 3,
        },
        "security_claim_allowed": False,
    }
    assert len(contract["candidate_obligations"]) == 6
    for candidate in contract["candidate_obligations"]:
        assert candidate["obligation_type"]["kind"] in {
            "target_invariant",
            "operator_precondition",
        }
        assert candidate["smt_status"] == "candidate_not_encoded"
        assert candidate["lean_theorem"].startswith("AgadesPQC.")
        assert len(candidate["obligation_sha256"]) == 64
    assert contract["linked_artifacts"]["formal_obligation_ledger"]["path"] == (
        "docs/formal_obligation_ledger.json"
    )
    assert contract["linked_artifacts"]["formal_lean_backend"]["path"] == (
        "docs/formal_lean_backend.json"
    )


def test_committed_formal_smt_assist_contract_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "formal_smt_assist_contract.json"

    write_formal_smt_assist_contract(generated)

    assert SMT_CONTRACT_PATH.read_bytes() == generated.read_bytes()


def test_formal_smt_assist_contract_verify_accepts_committed_artifact() -> None:
    result = verify_formal_smt_assist_contract(SMT_CONTRACT_PATH)

    assert result == {
        "schema_version": FORMAL_SMT_ASSIST_VERIFICATION_SCHEMA,
        "contract_path": SMT_CONTRACT_PATH.as_posix(),
        "accepted": True,
        "summary": {
            "candidate_obligations": 6,
            "excluded_obligations": 16,
            "linked_artifacts": 5,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_formal_smt_assist_contract_rejects_smt_as_primary_backend(
    tmp_path: Path,
) -> None:
    path = tmp_path / "formal_smt_assist_contract.json"
    contract = build_formal_smt_assist_contract()
    contract["backend_policy"]["may_replace_primary_backend"] = True
    contract["backend_policy"]["may_discharge_security_claims"] = True
    path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")

    result = verify_formal_smt_assist_contract(path)

    assert result["accepted"] is False
    assert "SMT assistance must not replace Lean 4 + Mathlib." in result["failures"]
    assert "SMT assistance must not discharge security claims." in result["failures"]


def test_formal_smt_assist_contract_rejects_excluded_candidate_kind(
    tmp_path: Path,
) -> None:
    path = tmp_path / "formal_smt_assist_contract.json"
    contract = build_formal_smt_assist_contract()
    contract["candidate_obligations"][0]["obligation_type"][
        "kind"
    ] = "estimator_claim_boundary"
    path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")

    result = verify_formal_smt_assist_contract(path)

    assert result["accepted"] is False
    assert (
        "SMT candidate obligation uses a forbidden obligation kind: "
        "estimator_claim_boundary."
    ) in result["failures"]


def test_formal_smt_assist_contract_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "formal_smt_assist_contract.json"

    write_result = CliRunner().invoke(
        app,
        ["formal-smt-assist", "--out", str(out)],
    )
    verify_result = CliRunner().invoke(
        app,
        ["formal-smt-assist-verify", "--contract", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"formal_smt_assist_contract={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
