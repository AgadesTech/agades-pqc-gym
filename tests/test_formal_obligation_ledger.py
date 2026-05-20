from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.formal.obligation_ledger import (
    FORMAL_OBLIGATION_LEDGER_VERIFICATION_SCHEMA,
    build_formal_obligation_ledger,
    verify_formal_obligation_ledger,
    write_formal_obligation_ledger,
)

LEDGER_PATH = Path("docs/formal_obligation_ledger.json")


def test_formal_obligation_ledger_binds_generated_obligations_and_invariants(
    tmp_path: Path,
) -> None:
    out = tmp_path / "formal_obligation_ledger.json"

    ledger = write_formal_obligation_ledger(out)

    assert ledger == build_formal_obligation_ledger()
    assert json.loads(out.read_text(encoding="utf-8")) == ledger
    assert ledger["schema_version"] == "agades.pqc.formal.obligation_ledger.v1"
    assert ledger["backend"] == {
        "primary": "lean4",
        "library": "mathlib",
        "smt_assist": "z3_optional_finite_decidable_obligations_only",
    }
    assert ledger["summary"] == {
        "families": 9,
        "family_invariants": 12,
        "proof_obligations": 22,
        "lean_theorems": 20,
        "reviewer_roles": 8,
        "attached_evaluator_result_families": ["LWE", "MLWE"],
        "security_claim_allowed": False,
    }
    assert [entry["family"] for entry in ledger["families"]] == [
        family.value for family in TargetFamily
    ]
    assert {
        entry["family"]: entry["representative_proof_artifact"][
            "estimator_result_binding_status"
        ]
        for entry in ledger["families"]
    } == {
        "LWE": "attached_unreviewed",
        "MLWE": "attached_unreviewed",
        "NTRU": "not_attached",
        "SIS": "not_attached",
        "CODE_BASED": "not_attached",
        "MULTIVARIATE": "not_attached",
        "HASH_BASED": "not_attached",
        "ISOGENY_HISTORICAL": "not_attached",
        "IMPLEMENTATION_SECURITY": "not_attached",
    }
    assert ledger["linked_artifacts"]["formal_lwe_evaluator_result"]["path"] == (
        "docs/formal_lattice_primal_usvp_evaluator_result.json"
    )
    assert ledger["linked_artifacts"]["formal_mlwe_evaluator_result"]["path"] == (
        "docs/formal_lattice_mlwe_module_hypothesis_evaluator_result.json"
    )

    for obligation in ledger["proof_obligations"]:
        assert obligation["status"] == "pending_review"
        assert obligation["backend"] == "lean4"
        assert obligation["review_required"] is True
        assert obligation["obligation_type"]["claim_policy"][
            "security_claim_allowed"
        ] is False
        assert obligation["lean_source"]["path"].startswith("formal/lean/")
        assert len(obligation["obligation_sha256"]) == 64
        assert len(obligation["ledger_entry_sha256"]) == 64

    for invariant in ledger["family_invariants"]:
        assert invariant["backend"] == "lean4"
        assert invariant["claim_policy"]["security_claim_allowed"] is False
        assert invariant["lean_source"]["path"].startswith("formal/lean/")
        assert len(invariant["ledger_entry_sha256"]) == 64


def test_committed_formal_obligation_ledger_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "formal_obligation_ledger.json"

    write_formal_obligation_ledger(generated)

    assert LEDGER_PATH.read_bytes() == generated.read_bytes()


def test_formal_obligation_ledger_verify_accepts_committed_artifact() -> None:
    result = verify_formal_obligation_ledger(LEDGER_PATH)

    assert result == {
        "schema_version": FORMAL_OBLIGATION_LEDGER_VERIFICATION_SCHEMA,
        "ledger_path": LEDGER_PATH.as_posix(),
        "accepted": True,
        "summary": {
            "families": 9,
            "family_invariants": 12,
            "proof_obligations": 22,
            "linked_artifacts": 8,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_formal_obligation_ledger_rejects_unreviewed_security_claim(
    tmp_path: Path,
) -> None:
    path = tmp_path / "formal_obligation_ledger.json"
    ledger = build_formal_obligation_ledger()
    ledger["proof_obligations"][0]["obligation_type"]["claim_policy"][
        "security_claim_allowed"
    ] = True
    path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")

    result = verify_formal_obligation_ledger(path)

    assert result["accepted"] is False
    assert "Formal obligation ledger is not in sync." in result["failures"]
    assert any(
        failure.startswith("Formal obligation ledger claim policy drifted:")
        for failure in result["failures"]
    )


def test_formal_obligation_ledger_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "formal_obligation_ledger.json"

    write_result = CliRunner().invoke(
        app,
        ["formal-obligation-ledger", "--out", str(out)],
    )
    verify_result = CliRunner().invoke(
        app,
        ["formal-obligation-ledger-verify", "--ledger", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"formal_obligation_ledger={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
