from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.evaluator_result import EvaluatorResult
from agades_pqc_gym.formal.artifacts import (
    build_attack_plan_proof_artifact,
    verify_attack_plan_proof_artifact,
    write_attack_plan_proof_artifact,
)
from agades_pqc_gym.utils.hashing import stable_sha256

LWE_PROOF_ARTIFACT_PATH = Path("docs/formal_lattice_primal_usvp_proof_artifact.json")
MLWE_PROOF_ARTIFACT_PATH = Path(
    "docs/formal_lattice_mlwe_module_hypothesis_proof_artifact.json"
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
    assert artifact["attack_plan"]["schema_contract"] == {
        "schema_version": "agades.pqc.attack_plan.schema_contract.v1",
        "model": "agades_pqc_gym.core.attack_plan.AttackPlan",
        "json_schema_sha256": stable_sha256(AttackPlan.model_json_schema()),
        "canonicalization": "json_sort_keys_minified_v1",
        "validation": "pydantic_v2_extra_forbid_family_cross_checks",
    }
    assert len(artifact["attack_plan"]["schema_contract"]["json_schema_sha256"]) == 64
    assert artifact["formal_backend"]["root"] == "formal/lean"
    assert artifact["formal_backend"]["toolchain"] == "formal/lean/lean-toolchain"
    assert artifact["formal_backend"]["lakefile"] == "formal/lean/lakefile.lean"
    assert artifact["formal_backend"]["lake_manifest"] == (
        "formal/lean/lake-manifest.json"
    )
    assert artifact["formal_backend"]["entry_module"] == "formal/lean/AgadesPQC.lean"
    assert artifact["formal_backend"]["build_command"] == "lake build"
    assert artifact["formal_backend"]["execution_status"] == (
        "ci_build_gate_required"
    )
    backend_manifest = artifact["formal_backend"]["backend_manifest"]
    assert backend_manifest["path"] == "docs/formal_lean_backend.json"
    assert backend_manifest["schema_version"] == "agades.pqc.formal.lean_backend.v1"
    assert len(backend_manifest["sha256"]) == 64
    assert len(backend_manifest["manifest_sha256"]) == 64
    assert backend_manifest["source_modules"] == 11
    assert backend_manifest["theorem_declarations"] >= 20
    assert backend_manifest["ci_lean_build_gate"] is True
    assert backend_manifest["placeholder_failures"] == 0
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
    obligation_types = {
        obligation["obligation_id"]: obligation["obligation_type"]
        for obligation in artifact["proof_obligations"]
    }
    assert obligation_types["target.lwe.parameters.positive"] == {
        "schema_version": "agades.pqc.formal.proof_obligation_type.v1",
        "kind": "target_invariant",
        "subject": {
            "family": "LWE",
            "scope": "target",
            "target_family": "LWE",
        },
        "claim_policy": {
            "public_interpretation": "applicability_check_only",
            "review_required_before_claim": True,
            "security_claim_allowed": False,
        },
    }
    assert obligation_types["operator.primal_usvp.beta.valid_range"] == {
        "schema_version": "agades.pqc.formal.proof_obligation_type.v1",
        "kind": "operator_precondition",
        "subject": {
            "family": "LWE",
            "operator": "primal_usvp",
            "scope": "operator",
        },
        "claim_policy": {
            "public_interpretation": "applicability_check_only",
            "review_required_before_claim": True,
            "security_claim_allowed": False,
        },
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
    first_obligation_source = artifact["proof_obligations"][0]["lean_source"]
    assert first_obligation_source["path"] == (
        "formal/lean/AgadesPQC/Lattice/Target.lean"
    )
    assert first_obligation_source["declaration"] == "parameters_positive"
    assert len(first_obligation_source["sha256"]) == 64
    assert artifact["proof_obligations"][0]["status"] == "pending_review"
    assert artifact["review"]["required_reviewers"] == [
        "lattice_cryptographer",
        "formal_methods_reviewer",
        "release_boundary_reviewer",
    ]
    assert artifact["review"]["evidence"] == {
        "schema_version": "agades.pqc.formal.review_evidence.v1",
        "status": "not_attached",
        "required_for_statuses": ["reviewed", "rejected"],
        "covered_reviewer_roles": [],
        "claim_allowed": False,
        "notes": (
            "No reviewer attestation is attached; this artifact must remain "
            "pending_review."
        ),
    }
    assert artifact["artifact_sha256"] == artifact["artifact_sha256"]


def test_lattice_proof_artifact_binds_existing_lean_sources() -> None:
    artifact = build_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json")
    )

    lean_sources = [
        invariant["lean_source"] for invariant in artifact["family_invariants"]
    ] + [
        obligation["lean_source"] for obligation in artifact["proof_obligations"]
    ]

    for source in lean_sources:
        path = Path(source["path"])
        raw = path.read_bytes()
        assert path.is_file()
        assert hashlib.sha256(raw).hexdigest() == source["sha256"]
        assert f"theorem {source['declaration']}" in raw.decode("utf-8")


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
    assert artifact["review"]["required_reviewers"] == [
        "code_based_cryptographer",
        "formal_methods_reviewer",
        "release_boundary_reviewer",
    ]


def test_mlwe_proof_artifact_uses_mlwe_specific_obligations() -> None:
    artifact = build_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_mlwe_module_hypothesis_toy.json")
    )

    invariant_ids = {
        invariant["invariant_id"] for invariant in artifact["family_invariants"]
    }
    obligation_ids = {
        obligation["obligation_id"] for obligation in artifact["proof_obligations"]
    }

    assert artifact["family"] == "MLWE"
    assert "lattice.mlwe.module_rank_present" in invariant_ids
    assert "target.mlwe.parameters.positive" in obligation_ids
    assert "target.mlwe.distributions.present" in obligation_ids
    assert "target.mlwe.module_rank.present" in obligation_ids
    assert "target.lwe.parameters.positive" not in obligation_ids
    assert all(
        obligation["obligation_type"]["subject"]["family"] == "MLWE"
        for obligation in artifact["proof_obligations"]
    )
    assert {
        obligation["obligation_type"]["kind"]
        for obligation in artifact["proof_obligations"]
    } == {"target_invariant", "estimator_claim_boundary"}


@pytest.mark.parametrize(
    ("plan_path", "family", "invariant_id", "obligation_id", "lean_path"),
    [
        (
            "examples/attack_plans/lattice_ntru_schema_placeholder.json",
            "NTRU",
            "lattice.ntru.schema_shape",
            "family.ntru.schema_only.no_estimate",
            "formal/lean/AgadesPQC/Lattice/Target.lean",
        ),
        (
            "examples/attack_plans/lattice_sis_schema_placeholder.json",
            "SIS",
            "lattice.sis.schema_shape",
            "family.sis.schema_only.no_estimate",
            "formal/lean/AgadesPQC/Lattice/Target.lean",
        ),
        (
            "examples/attack_plans/code_based_isd_placeholder.json",
            "CODE_BASED",
            "code_based.length_dimension_weight_positive",
            "family.code_based.schema_only.no_estimate",
            "formal/lean/AgadesPQC/CodeBased/Target.lean",
        ),
        (
            "examples/attack_plans/multivariate_mq_toy.json",
            "MULTIVARIATE",
            "multivariate.variables_equations_field_present",
            "family.multivariate.applicability_shape",
            "formal/lean/AgadesPQC/Multivariate/Target.lean",
        ),
        (
            "examples/attack_plans/hash_based_collision_toy.json",
            "HASH_BASED",
            "hash_based.hash_function_and_security_parameter_present",
            "family.hash_based.bound_check_is_not_attack_claim",
            "formal/lean/AgadesPQC/HashBased/Target.lean",
        ),
        (
            "examples/attack_plans/isogeny_historical_toy.json",
            "ISOGENY_HISTORICAL",
            "isogeny_historical.dimension_positive_historical_scope",
            "family.isogeny_historical.historical_only",
            "formal/lean/AgadesPQC/IsogenyHistorical/Target.lean",
        ),
        (
            "examples/attack_plans/implementation_security_kat_toy.json",
            "IMPLEMENTATION_SECURITY",
            "implementation_security.review_scope_declared",
            "family.implementation_security.no_conformance_claim",
            "formal/lean/AgadesPQC/ImplementationSecurity/Target.lean",
        ),
    ],
)
def test_family_specific_proof_artifacts_do_not_use_generic_fallback(
    plan_path: str,
    family: str,
    invariant_id: str,
    obligation_id: str,
    lean_path: str,
) -> None:
    artifact = build_attack_plan_proof_artifact(Path(plan_path))

    invariant_ids = {
        invariant["invariant_id"] for invariant in artifact["family_invariants"]
    }
    obligation_ids = {
        obligation["obligation_id"] for obligation in artifact["proof_obligations"]
    }
    lean_paths = {
        invariant["lean_source"]["path"]
        for invariant in artifact["family_invariants"]
    } | {
        obligation["lean_source"]["path"]
        for obligation in artifact["proof_obligations"]
    }

    assert artifact["family"] == family
    assert invariant_id in invariant_ids
    assert obligation_id in obligation_ids
    assert lean_path in lean_paths
    assert "generic.family_shape_validated" not in invariant_ids
    assert all(
        not item["semantics_id"].startswith("agades.pqc.operator_semantics.generic.")
        for item in artifact["operator_semantics"]
    )
    assert all(
        obligation["obligation_type"]["subject"]["family"] == family
        for obligation in artifact["proof_obligations"]
    )
    assert all(
        obligation["obligation_type"]["claim_policy"][
            "security_claim_allowed"
        ]
        is False
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


def test_build_attack_plan_proof_artifact_rejects_reviewed_without_evidence() -> None:
    with pytest.raises(
        ValueError,
        match="review evidence is required for non-pending proof artifacts",
    ):
        build_attack_plan_proof_artifact(
            Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
            review_status="reviewed",
        )


def test_attached_estimator_result_binding_includes_evaluator_schema_contract(
    tmp_path: Path,
) -> None:
    result_path = _write_estimator_result(tmp_path)

    artifact = build_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
        estimator_result_path=result_path,
    )

    assert artifact["estimator_result_binding"]["status"] == "attached_unreviewed"
    assert artifact["estimator_result_binding"]["schema_contract"] == {
        "schema_version": "agades.pqc.evaluator_result.schema_contract.v1",
        "model": "agades_pqc_gym.core.evaluator_result.EvaluatorResult",
        "json_schema_sha256": stable_sha256(EvaluatorResult.model_json_schema()),
        "canonicalization": "json_sort_keys_minified_v1",
        "validation": "pydantic_v2_extra_forbid_status_payload_checks",
    }
    assert artifact["estimator_result_binding"]["parsed_result"] == {
        "schema_version": "agades.pqc.evaluator_result.v1",
        "evaluator_name": "mock-lattice-estimator",
        "evaluator_version": "0.1.0",
        "evaluator_commit": None,
        "evaluation_status": "ok",
        "attack_type": "primal_usvp",
        "claim_allowed": False,
    }
    assert artifact["estimator_result_binding"]["attack_plan_compatibility"] == {
        "attack_plan_id": "lattice_primal_usvp_toy_v1",
        "target_family": "LWE",
        "operator_types": ["primal_usvp"],
        "evaluator_attack_type": "primal_usvp",
        "compatible": True,
        "compatibility_rule": "exact_operator_or_colon_variant_v1",
    }


def test_committed_lattice_proof_artifact_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "proof_artifact.json"

    write_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
        generated,
    )

    assert LWE_PROOF_ARTIFACT_PATH.read_bytes() == generated.read_bytes()


def test_committed_mlwe_proof_artifact_is_in_sync_and_verifiable(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "proof_artifact.json"

    artifact = write_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_mlwe_module_hypothesis_toy.json"),
        generated,
    )
    result = verify_attack_plan_proof_artifact(MLWE_PROOF_ARTIFACT_PATH)

    assert MLWE_PROOF_ARTIFACT_PATH.read_bytes() == generated.read_bytes()
    assert artifact["family"] == "MLWE"
    assert {
        obligation["obligation_id"] for obligation in artifact["proof_obligations"]
    } == {
        "target.mlwe.parameters.positive",
        "target.mlwe.distributions.present",
        "target.mlwe.module_rank.present",
        "estimator.boundary.no_security_claim",
    }
    assert result == {
        "schema_version": "agades.pqc.formal.proof_artifact_verification.v1",
        "artifact_path": MLWE_PROOF_ARTIFACT_PATH.as_posix(),
        "accepted": True,
        "summary": {
            "operator_semantics": 2,
            "family_invariants": 3,
            "proof_obligations": 4,
            "lean_theorems": 4,
            "estimator_result_attached": False,
            "required_reviewers": 3,
            "failure_count": 0,
        },
        "failures": [],
    }


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


def test_verify_attack_plan_proof_artifact_rejects_stale_formal_backend_binding(
    tmp_path: Path,
) -> None:
    out = tmp_path / "proof_artifact.json"
    artifact = write_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
        out,
    )
    artifact["formal_backend"]["backend_manifest"]["sha256"] = "0" * 64
    artifact["artifact_sha256"] = artifact["artifact_sha256"]
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")

    result = verify_attack_plan_proof_artifact(out)

    assert result["accepted"] is False
    assert "Proof artifact formal_backend is not in sync." in result["failures"]


def test_verify_attack_plan_proof_artifact_rejects_stale_attack_plan_schema_contract(
    tmp_path: Path,
) -> None:
    out = tmp_path / "proof_artifact.json"
    artifact = write_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
        out,
    )
    artifact["attack_plan"]["schema_contract"]["json_schema_sha256"] = "0" * 64
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")

    result = verify_attack_plan_proof_artifact(out)

    assert result["accepted"] is False
    assert (
        "AttackPlan schema binding does not match current core schema."
        in result["failures"]
    )


def test_verify_rejects_reviewed_status_without_reviewer_evidence(
    tmp_path: Path,
) -> None:
    out = tmp_path / "proof_artifact.json"
    artifact = write_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
        out,
    )
    artifact["review"]["status"] = "reviewed"
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")

    result = verify_attack_plan_proof_artifact(out)

    assert result["accepted"] is False
    assert (
        "Non-pending proof artifact review statuses require attached review "
        "evidence covering all required reviewers."
    ) in result["failures"]


def test_verify_rejects_stale_estimator_result_schema_contract(
    tmp_path: Path,
) -> None:
    result_path = _write_estimator_result(tmp_path)
    out = tmp_path / "proof_artifact.json"
    artifact = write_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
        out,
        estimator_result_path=result_path,
    )
    artifact["estimator_result_binding"]["schema_contract"][
        "json_schema_sha256"
    ] = "0" * 64
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")

    result = verify_attack_plan_proof_artifact(out)

    assert result["accepted"] is False
    assert (
        "Estimator result schema binding does not match current core schema."
        in result["failures"]
    )


def test_verify_attack_plan_proof_artifact_rejects_invalid_attached_estimator_result(
    tmp_path: Path,
) -> None:
    result_path = _write_estimator_result(tmp_path)
    out = tmp_path / "proof_artifact.json"
    write_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
        out,
        estimator_result_path=result_path,
    )
    result_path.write_text(
        json.dumps(
            {
                "schema_version": "agades.pqc.evaluator_result.v1",
                "evaluator_name": "mock-lattice-estimator",
                "evaluator_version": "0.1.0",
                "evaluator_commit": None,
                "evaluation_status": "unsupported",
                "attack_type": "primal_usvp",
                "time_bits": 75.0,
                "memory_bits": 25.0,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    result = verify_attack_plan_proof_artifact(out)

    assert result["accepted"] is False
    assert any(
        failure.startswith("Bound estimator result is invalid:")
        for failure in result["failures"]
    )


def test_build_attack_plan_proof_artifact_rejects_incompatible_estimator_result(
    tmp_path: Path,
) -> None:
    result_path = _write_estimator_result(
        tmp_path,
        {"attack_type": "module_lattice_reduction_hypothesis"},
    )

    with pytest.raises(
        ValueError,
        match="estimator result attack_type is incompatible",
    ):
        build_attack_plan_proof_artifact(
            Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
            estimator_result_path=result_path,
        )


def test_verify_rejects_stale_estimator_attack_plan_compatibility(
    tmp_path: Path,
) -> None:
    result_path = _write_estimator_result(tmp_path)
    out = tmp_path / "proof_artifact.json"
    artifact = write_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
        out,
        estimator_result_path=result_path,
    )
    artifact["estimator_result_binding"]["attack_plan_compatibility"][
        "evaluator_attack_type"
    ] = "module_lattice_reduction_hypothesis"
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")

    result = verify_attack_plan_proof_artifact(out)

    assert result["accepted"] is False
    assert (
        "Estimator result AttackPlan compatibility does not match bound files."
        in result["failures"]
    )


def test_verify_attack_plan_proof_artifact_rejects_claim_enabled_obligation_type(
    tmp_path: Path,
) -> None:
    out = tmp_path / "proof_artifact.json"
    artifact = write_attack_plan_proof_artifact(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
        out,
    )
    artifact["proof_obligations"][0]["obligation_type"]["claim_policy"][
        "security_claim_allowed"
    ] = True
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")

    result = verify_attack_plan_proof_artifact(out)

    assert result["accepted"] is False
    assert (
        "Proof obligation type must forbid security claims: "
        "target.lwe.parameters.positive."
    ) in result["failures"]


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


def _write_estimator_result(
    tmp_path: Path,
    overrides: dict[str, object] | None = None,
) -> Path:
    result_path = tmp_path / "estimator_result.json"
    payload = _valid_estimator_result_payload()
    if overrides:
        payload.update(overrides)
    result_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result_path


def _valid_estimator_result_payload() -> dict[str, object]:
    return {
        "schema_version": "agades.pqc.evaluator_result.v1",
        "evaluator_name": "mock-lattice-estimator",
        "evaluator_version": "0.1.0",
        "evaluator_commit": None,
        "evaluation_status": "ok",
        "attack_type": "primal_usvp",
        "time_bits": 75.0,
        "memory_bits": 25.0,
        "success_probability": None,
        "raw_output": {"source": "unit-test"},
        "warnings": ["Mock estimator output is not cryptanalytic evidence."],
    }
