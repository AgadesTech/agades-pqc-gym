from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.formal.family_coverage import (
    FORMAL_FAMILY_COVERAGE_VERIFICATION_SCHEMA,
    build_formal_family_coverage,
    verify_formal_family_coverage,
    write_formal_family_coverage,
)
from agades_pqc_gym.formal.review import required_reviewers_for_family

COVERAGE_PATH = Path("docs/formal_family_coverage.json")


def test_formal_family_coverage_binds_every_family_to_proof_material(
    tmp_path: Path,
) -> None:
    out = tmp_path / "formal_family_coverage.json"

    coverage = write_formal_family_coverage(out)

    assert coverage == build_formal_family_coverage()
    assert json.loads(out.read_text(encoding="utf-8")) == coverage
    assert coverage["schema_version"] == "agades.pqc.formal.family_coverage.v1"
    assert coverage["backend"] == {
        "primary": "lean4",
        "library": "mathlib",
        "smt_assist": "z3_optional_finite_decidable_obligations_only",
    }
    assert [entry["family"] for entry in coverage["families"]] == [
        family.value for family in TargetFamily
    ]
    assert coverage["summary"] == {
        "families": 9,
        "family_invariants": 12,
        "proof_obligations": 22,
        "operator_semantics": 10,
        "schema_only_families": ["NTRU", "SIS"],
        "implemented_or_toy_families": [
            "LWE",
            "MLWE",
            "CODE_BASED",
            "MULTIVARIATE",
            "HASH_BASED",
            "ISOGENY_HISTORICAL",
            "IMPLEMENTATION_SECURITY",
        ],
    }

    by_family = {entry["family"]: entry for entry in coverage["families"]}
    assert {
        family: [item["operator"] for item in entry["operator_semantics"]]
        for family, entry in by_family.items()
    } == {
        "LWE": ["primal_usvp"],
        "MLWE": [
            "module_lattice_reduction_hypothesis",
            "bkz_parameter_sweep",
        ],
        "NTRU": ["normal_form_transform"],
        "SIS": ["bkz_parameter_sweep"],
        "CODE_BASED": ["information_set_decoding"],
        "MULTIVARIATE": ["groebner_basis"],
        "HASH_BASED": ["security_bound_check"],
        "ISOGENY_HISTORICAL": ["historical_isogeny_reconstruction"],
        "IMPLEMENTATION_SECURITY": ["kat_conformance"],
    }
    assert by_family["MLWE"]["proof_obligation_ids"] == [
        "target.mlwe.parameters.positive",
        "target.mlwe.distributions.present",
        "target.mlwe.module_rank.present",
        "estimator.boundary.no_security_claim",
    ]
    assert by_family["NTRU"]["family_invariant_ids"] == [
        "lattice.ntru.schema_shape"
    ]
    assert by_family["SIS"]["proof_obligation_ids"] == [
        "family.sis.schema_only.no_estimate",
        "estimator.boundary.no_security_claim",
    ]
    assert by_family["CODE_BASED"]["required_reviewers"] == (
        required_reviewers_for_family(TargetFamily.CODE_BASED)
    )


def test_committed_formal_family_coverage_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "formal_family_coverage.json"

    write_formal_family_coverage(generated)

    assert COVERAGE_PATH.read_bytes() == generated.read_bytes()


def test_formal_family_coverage_verify_accepts_committed_artifact() -> None:
    result = verify_formal_family_coverage(COVERAGE_PATH)

    assert result == {
        "schema_version": FORMAL_FAMILY_COVERAGE_VERIFICATION_SCHEMA,
        "coverage_path": COVERAGE_PATH.as_posix(),
        "accepted": True,
        "summary": {
                "families": 9,
                "family_invariants": 12,
                "proof_obligations": 22,
                "operator_semantics": 10,
                "linked_artifacts": 2,
                "failure_count": 0,
            },
        "failures": [],
    }


def test_formal_family_coverage_rejects_missing_family(tmp_path: Path) -> None:
    path = tmp_path / "formal_family_coverage.json"
    coverage = build_formal_family_coverage()
    coverage["families"] = [
        entry
        for entry in coverage["families"]
        if entry["family"] != TargetFamily.SIS.value
    ]
    path.write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n")

    result = verify_formal_family_coverage(path)

    assert result["accepted"] is False
    assert (
        "Formal family coverage must contain one entry for each TargetFamily."
        in result["failures"]
    )


def test_formal_family_coverage_rejects_generic_fallbacks(tmp_path: Path) -> None:
    path = tmp_path / "formal_family_coverage.json"
    coverage = build_formal_family_coverage()
    coverage["families"][2]["family_invariant_ids"] = [
        "ntru.family_shape_validated"
    ]
    path.write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n")

    result = verify_formal_family_coverage(path)

    assert result["accepted"] is False
    assert (
        "Formal family coverage must not use generic fallback invariants."
        in result["failures"]
    )


def test_formal_family_coverage_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "formal_family_coverage.json"

    write_result = CliRunner().invoke(
        app,
        ["formal-family-coverage", "--out", str(out)],
    )
    verify_result = CliRunner().invoke(
        app,
        ["formal-family-coverage-verify", "--coverage", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"formal_family_coverage={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
