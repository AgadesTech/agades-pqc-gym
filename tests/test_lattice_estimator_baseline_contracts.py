from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.evaluators.lattice_estimator import LATTICE_ESTIMATOR_PINNED_COMMIT
from agades_pqc_gym.integrations.lattice_estimator_baseline_contracts import (
    build_lattice_estimator_baseline_contracts,
    verify_lattice_estimator_baseline_contracts,
    write_lattice_estimator_baseline_contracts,
)
from agades_pqc_gym.integrations.lattice_estimator_manifest import (
    build_lattice_estimator_manifest,
)


def test_lattice_estimator_baseline_contracts_cover_reviewed_lwe_mappings(
    tmp_path: Path,
) -> None:
    out = tmp_path / "lattice_estimator_baseline_contracts.json"

    contracts = write_lattice_estimator_baseline_contracts(out)

    assert contracts == build_lattice_estimator_baseline_contracts()
    assert json.loads(out.read_text(encoding="utf-8")) == contracts
    assert contracts["schema_version"] == (
        "agades.pqc.lattice_estimator_baseline_contracts.v1"
    )
    assert contracts["upstream"] == {
        "repository": "https://github.com/malb/lattice-estimator",
        "pinned_commit": LATTICE_ESTIMATOR_PINNED_COMMIT,
        "pin_source": "docs/lattice_estimator_manifest.json",
    }
    assert contracts["baseline_policy"] == {
        "status": "review_contract_ready_not_reproduced",
        "numeric_reference_outputs_committed": False,
        "requires_matching_lattice_estimator_pin": True,
        "requires_expert_review_before_numeric_baselines": True,
        "security_claim": False,
        "publication_allowed": False,
    }
    assert contracts["release_gates"] == [
        "uv run pytest tests/test_lattice_estimator_baseline_contracts.py -q",
        "uv run agades-pqc lattice-estimator-baseline-contracts --out "
        "docs/lattice_estimator_baseline_contracts.json",
        "uv run agades-pqc lattice-estimator-baseline-contracts-verify "
        "--contracts docs/lattice_estimator_baseline_contracts.json",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]

    mapping = build_lattice_estimator_manifest()["agades_boundary"][
        "reviewed_lwe_mappings"
    ]
    assert {
        contract["attack_type"]: contract["algorithm_key"]
        for contract in contracts["contracts"]
    } == mapping
    assert all(
        contract["target_family"] == "LWE" for contract in contracts["contracts"]
    )
    assert all(
        contract["numeric_reference_status"] == "pending_reviewed_reproduction"
        for contract in contracts["contracts"]
    )
    assert all(
        "expected_time_bits" not in contract and "expected_memory_bits" not in contract
        for contract in contracts["contracts"]
    )


def test_committed_lattice_estimator_baseline_contracts_are_in_sync(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "lattice_estimator_baseline_contracts.json"
    committed = Path("docs/lattice_estimator_baseline_contracts.json")

    write_lattice_estimator_baseline_contracts(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_baseline_contracts_verify_accepts_committed_contracts() -> None:
    result = verify_lattice_estimator_baseline_contracts(
        Path("docs/lattice_estimator_baseline_contracts.json")
    )

    assert result == {
        "schema_version": (
            "agades.pqc.lattice_estimator_baseline_contracts_verification.v1"
        ),
        "contracts_path": "docs/lattice_estimator_baseline_contracts.json",
        "accepted": True,
        "summary": {
            "contract_count": 5,
            "covered_algorithm_keys": ["bdd", "bkw", "dual", "dual_hybrid", "usvp"],
            "covered_attack_types": [
                "bounded_distance_decoding",
                "bkw",
                "dual_attack",
                "dual_hybrid",
                "primal_usvp",
            ],
            "failure_count": 0,
            "numeric_reference_outputs_committed": False,
            "pinned_commit": LATTICE_ESTIMATOR_PINNED_COMMIT,
            "security_claim": False,
        },
        "failures": [],
    }


def test_lattice_estimator_baseline_contracts_verify_rejects_numeric_claim_drift(
    tmp_path: Path,
) -> None:
    out = tmp_path / "lattice_estimator_baseline_contracts.json"
    contracts = build_lattice_estimator_baseline_contracts()
    contracts["baseline_policy"]["numeric_reference_outputs_committed"] = True
    contracts["baseline_policy"]["security_claim"] = True
    contracts["contracts"][0]["expected_time_bits"] = 42.0
    contracts["contracts"][0]["target_family"] = "MLWE"
    out.write_text(json.dumps(contracts, indent=2, sort_keys=True) + "\n")

    result = verify_lattice_estimator_baseline_contracts(out)

    assert result["accepted"] is False
    assert "Lattice Estimator baseline contracts are not in sync." in result[
        "failures"
    ]
    assert "Baseline policy must not commit numeric reference outputs yet." in result[
        "failures"
    ]
    assert "Baseline policy must not advertise security claims." in result["failures"]
    assert any(
        "must remain LWE-only" in failure for failure in result["failures"]
    )
    assert any(
        "must not contain expected_time_bits" in failure
        for failure in result["failures"]
    )


def test_lattice_estimator_baseline_contracts_cli_writes_contracts(
    tmp_path: Path,
) -> None:
    out = tmp_path / "lattice_estimator_baseline_contracts.json"

    result = CliRunner().invoke(
        app,
        ["lattice-estimator-baseline-contracts", "--out", str(out)],
    )

    assert result.exit_code == 0
    assert f"lattice_estimator_baseline_contracts={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["upstream"][
        "pinned_commit"
    ] == LATTICE_ESTIMATOR_PINNED_COMMIT


def test_baseline_contracts_verify_cli_accepts_current_contracts() -> None:
    result = CliRunner().invoke(
        app,
        [
            "lattice-estimator-baseline-contracts-verify",
            "--contracts",
            "docs/lattice_estimator_baseline_contracts.json",
        ],
    )

    assert result.exit_code == 0
    assert (
        "agades.pqc.lattice_estimator_baseline_contracts_verification.v1"
        in result.output
    )
    assert '"accepted": true' in result.output
