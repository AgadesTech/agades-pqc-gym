from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.core.operators import ALLOWED_OPERATORS
from agades_pqc_gym.formal.operator_semantics import (
    FORMAL_OPERATOR_SEMANTICS_VERIFICATION_SCHEMA,
    build_formal_operator_semantics,
    verify_formal_operator_semantics,
    write_formal_operator_semantics,
)

SEMANTICS_PATH = Path("docs/formal_operator_semantics.json")


def test_formal_operator_semantics_covers_all_attackplan_operators(
    tmp_path: Path,
) -> None:
    out = tmp_path / "formal_operator_semantics.json"

    semantics = write_formal_operator_semantics(out)

    assert semantics == build_formal_operator_semantics()
    assert json.loads(out.read_text(encoding="utf-8")) == semantics
    assert semantics["schema_version"] == "agades.pqc.formal.operator_semantics.v1"
    assert semantics["summary"] == {
        "operators": 24,
        "lattice_operators": 12,
        "non_lattice_operators": 12,
        "required_param_fields": 25,
        "attackplan_family_bindings": 60,
        "applicability_validator_bindings": 60,
        "schema_only_family_bindings": 24,
        "security_claim_allowed_without_review": 0,
    }
    assert {entry["operator"] for entry in semantics["operators"]} == set(
        ALLOWED_OPERATORS
    )
    assert semantics["operators"][0] == {
        "operator": "primal_usvp",
        "semantics_id": "agades.pqc.operator_semantics.lattice.primal_usvp.v1",
        "lean_namespace": "AgadesPQC.Lattice.PrimalUSVP",
        "required_params": {"beta": "int"},
        "formal_rules": semantics["operators"][0]["formal_rules"],
        "attackplan_families": ["LWE", "MLWE", "NTRU", "SIS"],
        "family_bindings": [
            {
                "family": "LWE",
                "plugin": "lattice",
                "support_level": "implemented",
                "applicability_validator": (
                    "agades_pqc_gym.families.lattice.validators."
                    "validate_lattice_plan"
                ),
                "catalog_operator_entry_count": 1,
                "catalog_support_statuses": ["implemented_mvp"],
                "schema_only": False,
            },
            {
                "family": "MLWE",
                "plugin": "lattice",
                "support_level": "implemented",
                "applicability_validator": (
                    "agades_pqc_gym.families.lattice.validators."
                    "validate_lattice_plan"
                ),
                "catalog_operator_entry_count": 0,
                "catalog_support_statuses": [],
                "schema_only": False,
            },
            {
                "family": "NTRU",
                "plugin": "lattice",
                "support_level": "schema_only",
                "applicability_validator": (
                    "agades_pqc_gym.families.lattice.validators."
                    "validate_lattice_plan"
                ),
                "catalog_operator_entry_count": 0,
                "catalog_support_statuses": [],
                "schema_only": True,
            },
            {
                "family": "SIS",
                "plugin": "lattice",
                "support_level": "schema_only",
                "applicability_validator": (
                    "agades_pqc_gym.families.lattice.validators."
                    "validate_lattice_plan"
                ),
                "catalog_operator_entry_count": 0,
                "catalog_support_statuses": [],
                "schema_only": True,
            },
        ],
        "runtime_claim_boundary": (
            "operator semantics define AttackPlan applicability and routing, "
            "not cryptographic break evidence"
        ),
        "claim_policy": {
            "security_claim_allowed_without_review": False,
            "proof_obligation_required_before_claim": True,
            "estimator_result_required_before_claim": True,
            "human_review_required_before_claim": True,
        },
        "entry_sha256": semantics["operators"][0]["entry_sha256"],
    }
    assert semantics["operators"][0]["formal_rules"] == [
        {
            "rule_id": "operator.required_params_present",
            "statement": (
                "The AttackPlan operator is only applicable when every required "
                "parameter declared by the operator schema is present."
            ),
            "lean_theorem": "AgadesPQC.OperatorSemantics.required_parameter_bound",
            "lean_source": semantics["operators"][0]["formal_rules"][0][
                "lean_source"
            ],
        },
        {
            "rule_id": "operator.family_binding_valid",
            "statement": (
                "The operator may only be routed through families listed in its "
                "AttackPlan family binding."
            ),
            "lean_theorem": "AgadesPQC.OperatorSemantics.family_binding_valid",
            "lean_source": semantics["operators"][0]["formal_rules"][1][
                "lean_source"
            ],
        },
        {
            "rule_id": "operator.unreviewed_security_claim_forbidden",
            "statement": (
                "Unreviewed operator semantics may support applicability and "
                "routing checks, but cannot authorize a cryptographic security "
                "claim."
            ),
            "lean_theorem": (
                "AgadesPQC.OperatorSemantics.unreviewed_security_claim_forbidden"
            ),
            "lean_source": semantics["operators"][0]["formal_rules"][2][
                "lean_source"
            ],
        },
    ]
    for rule in semantics["operators"][0]["formal_rules"]:
        assert rule["lean_source"] == {
            "path": "formal/lean/AgadesPQC/OperatorSemantics.lean",
            "sha256": semantics["operators"][0]["formal_rules"][0][
                "lean_source"
            ]["sha256"],
        }
        assert len(rule["lean_source"]["sha256"]) == 64
    assert semantics["operators"][-1]["operator"] == "benchmark_harness"
    assert semantics["operators"][-1]["required_params"] == {"metric": "str"}
    assert semantics["operators"][-1]["formal_rules"] == semantics["operators"][0][
        "formal_rules"
    ]

    by_operator = {entry["operator"]: entry for entry in semantics["operators"]}
    assert by_operator["normal_form_transform"]["required_params"] == {}
    assert by_operator["dual_hybrid"]["required_params"] == {
        "beta": "int",
        "zeta": "int",
    }
    assert by_operator["information_set_decoding"]["attackplan_families"] == [
        "CODE_BASED"
    ]
    assert by_operator["historical_isogeny_reconstruction"][
        "attackplan_families"
    ] == ["ISOGENY_HISTORICAL"]


def test_committed_formal_operator_semantics_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "formal_operator_semantics.json"

    write_formal_operator_semantics(generated)

    assert SEMANTICS_PATH.read_bytes() == generated.read_bytes()


def test_formal_operator_semantics_verify_accepts_committed_artifact() -> None:
    result = verify_formal_operator_semantics(SEMANTICS_PATH)

    assert result == {
        "schema_version": FORMAL_OPERATOR_SEMANTICS_VERIFICATION_SCHEMA,
        "semantics_path": SEMANTICS_PATH.as_posix(),
        "accepted": True,
        "summary": {
            "operators": 24,
            "required_param_fields": 25,
            "linked_artifacts": 2,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_formal_operator_semantics_rejects_missing_operator(tmp_path: Path) -> None:
    path = tmp_path / "formal_operator_semantics.json"
    semantics = build_formal_operator_semantics()
    semantics["operators"] = [
        entry
        for entry in semantics["operators"]
        if entry["operator"] != "benchmark_harness"
    ]
    path.write_text(json.dumps(semantics, indent=2, sort_keys=True) + "\n")

    result = verify_formal_operator_semantics(path)

    assert result["accepted"] is False
    assert (
        "Formal operator semantics must cover every ALLOWED_OPERATORS entry."
        in result["failures"]
    )


def test_formal_operator_semantics_rejects_param_schema_drift(
    tmp_path: Path,
) -> None:
    path = tmp_path / "formal_operator_semantics.json"
    semantics = build_formal_operator_semantics()
    semantics["operators"][0]["required_params"] = {}
    path.write_text(json.dumps(semantics, indent=2, sort_keys=True) + "\n")

    result = verify_formal_operator_semantics(path)

    assert result["accepted"] is False
    assert (
        "Formal operator semantics parameter schemas are not in sync."
        in result["failures"]
    )


def test_formal_operator_semantics_rejects_family_binding_drift(
    tmp_path: Path,
) -> None:
    path = tmp_path / "formal_operator_semantics.json"
    semantics = build_formal_operator_semantics()
    semantics["operators"][0]["family_bindings"][0]["applicability_validator"] = (
        "agades_pqc_gym.families.fake.validators.validate_fake_plan"
    )
    path.write_text(json.dumps(semantics, indent=2, sort_keys=True) + "\n")

    result = verify_formal_operator_semantics(path)

    assert result["accepted"] is False
    assert (
        "Formal operator semantics family validator bindings are not in sync."
        in result["failures"]
    )


def test_formal_operator_semantics_rejects_formal_rule_drift(
    tmp_path: Path,
) -> None:
    path = tmp_path / "formal_operator_semantics.json"
    semantics = build_formal_operator_semantics()
    semantics["operators"][0]["formal_rules"][0]["lean_theorem"] = (
        "AgadesPQC.OperatorSemantics.missing"
    )
    path.write_text(json.dumps(semantics, indent=2, sort_keys=True) + "\n")

    result = verify_formal_operator_semantics(path)

    assert result["accepted"] is False
    assert "Formal operator semantics formal rules are not in sync." in result[
        "failures"
    ]


def test_formal_operator_semantics_rejects_unreviewed_security_claims(
    tmp_path: Path,
) -> None:
    path = tmp_path / "formal_operator_semantics.json"
    semantics = build_formal_operator_semantics()
    semantics["operators"][0]["claim_policy"][
        "security_claim_allowed_without_review"
    ] = True
    path.write_text(json.dumps(semantics, indent=2, sort_keys=True) + "\n")

    result = verify_formal_operator_semantics(path)

    assert result["accepted"] is False
    assert (
        "Formal operator semantics must not allow unreviewed security claims."
        in result["failures"]
    )


def test_formal_operator_semantics_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "formal_operator_semantics.json"

    write_result = CliRunner().invoke(
        app,
        ["formal-operator-semantics", "--out", str(out)],
    )
    verify_result = CliRunner().invoke(
        app,
        ["formal-operator-semantics-verify", "--semantics", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"formal_operator_semantics={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
