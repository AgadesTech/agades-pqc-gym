from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.operators import ALLOWED_OPERATORS
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.formal.attack_plan_semantics import (
    FORMAL_ATTACKPLAN_SEMANTICS_VERIFICATION_SCHEMA,
    build_formal_attackplan_semantics,
    verify_formal_attackplan_semantics,
    write_formal_attackplan_semantics,
)
from agades_pqc_gym.utils.hashing import stable_sha256

SEMANTICS_PATH = Path("docs/formal_attackplan_semantics.json")


def test_formal_attackplan_semantics_contract_binds_schema_validation_and_claims(
    tmp_path: Path,
) -> None:
    out = tmp_path / "formal_attackplan_semantics.json"

    contract = write_formal_attackplan_semantics(out)

    assert contract == build_formal_attackplan_semantics()
    assert json.loads(out.read_text(encoding="utf-8")) == contract
    assert contract["schema_version"] == "agades.pqc.formal.attackplan_semantics.v1"
    assert contract["backend"] == {
        "primary": "lean4",
        "library": "mathlib",
        "smt_assist": "z3_optional_finite_decidable_obligations_only",
    }
    assert contract["attack_plan_schema"] == {
        "schema_version": "agades.pqc.attack_plan.schema_contract.v1",
        "model": "agades_pqc_gym.core.attack_plan.AttackPlan",
        "json_schema_sha256": stable_sha256(AttackPlan.model_json_schema()),
        "canonicalization": "json_sort_keys_minified_v1",
        "validation": "pydantic_v2_extra_forbid_family_cross_checks",
    }
    assert contract["canonicalization"] == {
        "algorithm": "json_sort_keys_minified_v1",
        "hash": "stable_sha256",
        "purpose": "bind semantically identical AttackPlan JSON to a stable digest",
    }
    assert {
        rule["rule_id"] for rule in contract["formal_rules"]
    } == {
        "attackplan.schema_contract_well_formed",
        "attackplan.canonicalization_stable",
        "attackplan.operators_nonempty",
        "attackplan.unsupported_operator_rejected",
        "attackplan.unreviewed_security_claim_forbidden",
    }
    for rule in contract["formal_rules"]:
        source = rule["lean_source"]
        assert rule["lean_theorem"].startswith("AgadesPQC.AttackPlan.")
        assert Path(source["path"]).is_file()
        assert len(source["sha256"]) == 64
    assert contract["claim_policy"] == {
        "public_interpretation": "schema_applicability_and_review_gate_only",
        "security_claim_allowed_without_review": False,
        "estimator_result_required_before_claim": True,
        "proof_obligation_required_before_claim": True,
        "human_review_required_before_claim": True,
    }
    assert contract["summary"] == {
        "required_fields": len(AttackPlan.model_json_schema()["required"]),
        "operators": len(ALLOWED_OPERATORS),
        "families": len(TargetFamily),
        "validation_rules": 7,
        "formal_rules": 5,
        "linked_artifacts": 4,
        "security_claim_allowed_without_review": False,
    }


def test_committed_formal_attackplan_semantics_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "formal_attackplan_semantics.json"

    write_formal_attackplan_semantics(generated)

    assert SEMANTICS_PATH.read_bytes() == generated.read_bytes()


def test_formal_attackplan_semantics_verify_accepts_committed_artifact() -> None:
    result = verify_formal_attackplan_semantics(SEMANTICS_PATH)

    assert result == {
        "schema_version": FORMAL_ATTACKPLAN_SEMANTICS_VERIFICATION_SCHEMA,
        "semantics_path": SEMANTICS_PATH.as_posix(),
        "accepted": True,
        "summary": {
            "validation_rules": 7,
            "formal_rules": 5,
            "linked_artifacts": 4,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_formal_attackplan_semantics_rejects_unreviewed_security_claims(
    tmp_path: Path,
) -> None:
    path = tmp_path / "formal_attackplan_semantics.json"
    contract = build_formal_attackplan_semantics()
    contract["claim_policy"]["security_claim_allowed_without_review"] = True
    path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")

    result = verify_formal_attackplan_semantics(path)

    assert result["accepted"] is False
    assert (
        "AttackPlan semantics must forbid unreviewed security claims."
        in result["failures"]
    )


def test_formal_attackplan_semantics_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "formal_attackplan_semantics.json"

    write_result = CliRunner().invoke(
        app,
        ["formal-attackplan-semantics", "--out", str(out)],
    )
    verify_result = CliRunner().invoke(
        app,
        ["formal-attackplan-semantics-verify", "--semantics", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"formal_attackplan_semantics={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
