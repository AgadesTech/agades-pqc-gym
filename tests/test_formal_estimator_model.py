from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.formal.estimator_model import (
    FORMAL_ESTIMATOR_MODEL_VERIFICATION_SCHEMA,
    build_formal_estimator_model,
    verify_formal_estimator_model,
    write_formal_estimator_model,
)
from agades_pqc_gym.formal.review import required_reviewers_for_family

ESTIMATOR_MODEL_PATH = Path("docs/formal_estimator_model.json")


def test_formal_estimator_model_binds_families_to_claim_policy(
    tmp_path: Path,
) -> None:
    out = tmp_path / "formal_estimator_model.json"

    model = write_formal_estimator_model(out)

    assert model == build_formal_estimator_model()
    assert json.loads(out.read_text(encoding="utf-8")) == model
    assert model["schema_version"] == "agades.pqc.formal.estimator_model.v1"
    assert model["backend"] == {
        "primary": "lean4",
        "library": "mathlib",
        "smt_assist": "z3_optional_finite_decidable_obligations_only",
    }
    assert model["summary"] == {
        "families": 9,
        "runtime_operator_count": 36,
        "result_binding_required_before_claim": 7,
        "schema_only_no_estimator": 2,
        "security_claim_allowed_without_review": 0,
    }
    assert [entry["family"] for entry in model["families"]] == [
        family.value for family in TargetFamily
    ]
    assert model["proof_artifact_binding"] == {
        "estimator_result_binding_required_before_claim": True,
        "accepted_public_binding_statuses": [
            "not_attached",
            "attached_unreviewed",
        ],
        "security_claim_status_without_review": "disallowed",
        "lean_theorem": "AgadesPQC.Evaluator.no_security_claim",
    }
    assert [binding["lean_theorem"] for binding in model["lean_bindings"]] == [
        "AgadesPQC.Evaluator.attached_unreviewed_no_security_claim",
        "AgadesPQC.Evaluator.no_security_claim",
        "AgadesPQC.Evaluator.schema_only_no_estimator_no_security_claim",
    ]

    by_family = {entry["family"]: entry for entry in model["families"]}
    assert by_family["LWE"]["estimator_model"]["model_id"] == (
        "mock-lattice-estimator"
    )
    assert by_family["MLWE"]["estimator_model"]["model_id"] == (
        "mock-lattice-estimator"
    )
    assert by_family["NTRU"]["estimator_model"] == {
        "model_id": "schema_only_no_estimator",
        "status": "schema_only_no_estimator",
        "result_binding_required_before_claim": False,
        "security_claim_allowed_without_review": False,
        "toy_or_mock_result": False,
    }
    assert by_family["SIS"]["runtime_operator_count"] == 0
    assert by_family["CODE_BASED"]["estimator_model"]["model_id"] == (
        "toy-code-based-isd-estimator"
    )
    assert by_family["IMPLEMENTATION_SECURITY"]["estimator_model"]["model_id"] == (
        "toy-implementation-security-estimator"
    )
    assert by_family["CODE_BASED"]["required_reviewers"] == (
        required_reviewers_for_family(TargetFamily.CODE_BASED)
    )
    assert all(
        not entry["claim_policy"]["security_claim_allowed_without_review"]
        for entry in model["families"]
    )


def test_committed_formal_estimator_model_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "formal_estimator_model.json"

    write_formal_estimator_model(generated)

    assert ESTIMATOR_MODEL_PATH.read_bytes() == generated.read_bytes()


def test_formal_estimator_model_verify_accepts_committed_artifact() -> None:
    result = verify_formal_estimator_model(ESTIMATOR_MODEL_PATH)

    assert result == {
        "schema_version": FORMAL_ESTIMATOR_MODEL_VERIFICATION_SCHEMA,
        "model_path": ESTIMATOR_MODEL_PATH.as_posix(),
        "accepted": True,
        "summary": {
            "families": 9,
            "runtime_operator_count": 36,
            "linked_artifacts": 3,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_formal_estimator_model_rejects_public_claim_without_review(
    tmp_path: Path,
) -> None:
    path = tmp_path / "formal_estimator_model.json"
    model = build_formal_estimator_model()
    model["families"][0]["claim_policy"][
        "security_claim_allowed_without_review"
    ] = True
    path.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n")

    result = verify_formal_estimator_model(path)

    assert result["accepted"] is False
    assert (
        "Formal estimator model must not allow unreviewed security claims."
        in result["failures"]
    )


def test_formal_estimator_model_rejects_schema_only_fake_estimator(
    tmp_path: Path,
) -> None:
    path = tmp_path / "formal_estimator_model.json"
    model = build_formal_estimator_model()
    model["families"][2]["estimator_model"]["model_id"] = "mock-lattice-estimator"
    path.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n")

    result = verify_formal_estimator_model(path)

    assert result["accepted"] is False
    assert (
        "Formal estimator model schema-only families must not name runtime "
        "estimators."
        in result["failures"]
    )


def test_formal_estimator_model_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "formal_estimator_model.json"

    write_result = CliRunner().invoke(
        app,
        ["formal-estimator-model", "--out", str(out)],
    )
    verify_result = CliRunner().invoke(
        app,
        ["formal-estimator-model-verify", "--model", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"formal_estimator_model={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
