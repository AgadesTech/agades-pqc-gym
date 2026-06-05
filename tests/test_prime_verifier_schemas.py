from __future__ import annotations

import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.prime_verifier_schemas import (
    build_prime_verifier_schemas,
    verify_prime_verifier_schemas,
    write_prime_verifier_schemas,
)
from agades_pqc_gym.integrations.task_metadata import (
    TASK_METADATA_SCHEMA,
    TaskMetadata,
)
from agades_pqc_gym.verifier import (
    VerifierResult,
    verify_attack_plan_path,
)


def test_prime_verifier_schemas_describe_submission_and_result_contracts(
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "schemas"

    bundle = write_prime_verifier_schemas(out_dir)

    assert bundle == build_prime_verifier_schemas()
    manifest = json.loads((out_dir / "schema_manifest.json").read_text())
    attack_plan_schema = json.loads(
        (out_dir / "attack_plan.schema.json").read_text()
    )
    result_schema = json.loads(
        (out_dir / "verifier_result.schema.json").read_text()
    )
    task_metadata_schema = json.loads(
        (out_dir / "task_metadata.schema.json").read_text()
    )

    assert manifest["schema_version"] == "agades.pqc.prime_verifier_schemas.v1"
    assert manifest["contract"]["evaluator_result_schema_version"] == (
        "agades.pqc.evaluator_result.v1"
    )
    assert manifest["contract"]["task_metadata_schema_version"] == (
        TASK_METADATA_SCHEMA
    )
    assert manifest["schemas"] == {
        "submission": "attack_plan.schema.json",
        "task_metadata": "task_metadata.schema.json",
        "result": "verifier_result.schema.json",
    }
    assert manifest["safety"] == {
        "accepts_arbitrary_code": False,
        "accepts_live_targets": False,
        "security_claim": False,
        "publishes_private_candidates": False,
    }
    assert manifest["release_gates"] == [
        "uv run pytest tests/test_prime_verifier_schemas.py -q",
        "uv run agades-pqc prime-schemas --out prime_intellect/schemas",
        "uv run agades-pqc prime-schemas-verify --schemas prime_intellect/schemas",
        "uv run agades-pqc prime-manifest-verify --manifest "
        "prime_intellect/verifiers_environment/prime_manifest.json",
        "uv run agades-pqc publication-manifest-verify --manifest "
        "docs/publication_manifest.json",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]
    assert attack_plan_schema["$id"].endswith("/attack_plan.schema.json")
    assert attack_plan_schema["title"] == "Agades PQC Gym AttackPlan Submission"
    assert "target" in attack_plan_schema["properties"]
    assert "operators" in attack_plan_schema["properties"]
    assert result_schema["$id"].endswith("/verifier_result.schema.json")
    assert result_schema["title"] == "Agades PQC Gym Verifier Result"
    assert "schema_version" in result_schema["required"]
    assert "accepted" in result_schema["required"]
    assert "evaluation_status" in result_schema["required"]
    assert "safety" in result_schema["properties"]
    assert task_metadata_schema["$id"].endswith("/task_metadata.schema.json")
    assert task_metadata_schema["title"] == "Agades PQC Gym Task Metadata"
    assert task_metadata_schema["properties"]["schema_version"]["title"] == (
        "Schema Version"
    )
    assert "operator_types" in task_metadata_schema["required"]
    assert "operator_assumptions" in task_metadata_schema["required"]
    assert "seed_attack_plan_sha256" in task_metadata_schema["required"]
    assert "seed_accepted" in task_metadata_schema["required"]
    assert "seed_evaluation_status" in task_metadata_schema["required"]
    assert "seed_estimator_name" in task_metadata_schema["required"]
    assert "seed_reproduction_attempted" in task_metadata_schema["required"]
    assert "seed_reproduction_status" in task_metadata_schema["required"]
    assert "seed_reproduction_success" in task_metadata_schema["required"]
    assert "seed_reward" in task_metadata_schema["required"]

    seed_path = Path("examples/attack_plans/lattice_primal_usvp_toy.json")
    seed_text = seed_path.read_text()
    result = verify_attack_plan_path(seed_path)
    assert VerifierResult.model_validate(result).model_dump(mode="json") == result
    metadata = {
        "schema_version": TASK_METADATA_SCHEMA,
        "source_path": "examples/attack_plans/lattice_primal_usvp_toy.json",
        "seed_attack_plan_sha256": hashlib.sha256(
            seed_text.encode("utf-8")
        ).hexdigest(),
        "attack_plan_id": "lattice_primal_usvp_toy_v1",
        "target_family": "LWE",
        "target_name": "toy_lwe_n64_q257",
        "support_level": "implemented",
        "operator_types": ["primal_usvp"],
        "operator_assumptions": [["lattice_estimator_default_cost_model"]],
        "requires_reproducibility": False,
        "public": True,
        "seed_accepted": True,
        "seed_evaluation_status": "ok",
        "seed_estimator_name": "mock-lattice-estimator",
        "seed_reproduction_attempted": False,
        "seed_reproduction_status": "not_requested",
        "seed_reproduction_success": None,
        "seed_reward": 1.0,
    }
    assert TaskMetadata.model_validate(metadata).model_dump(mode="json") == metadata


def test_committed_prime_verifier_schemas_are_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "schemas"
    committed = Path("prime_intellect/schemas")

    write_prime_verifier_schemas(generated)

    for filename in (
        "attack_plan.schema.json",
        "schema_manifest.json",
        "task_metadata.schema.json",
        "verifier_result.schema.json",
    ):
        assert (committed / filename).read_bytes() == (
            generated / filename
        ).read_bytes()


def test_prime_schemas_verify_accepts_committed_schema_bundle() -> None:
    result = verify_prime_verifier_schemas(Path("prime_intellect/schemas"))

    assert result == {
        "schema_version": "agades.pqc.prime_verifier_schemas_verification.v1",
        "schema_dir": "prime_intellect/schemas",
        "accepted": True,
        "summary": {
            "evaluator_result_schema_version": "agades.pqc.evaluator_result.v1",
            "failure_count": 0,
            "release_gate_count": 7,
            "result_required_fields": [
                "accepted",
                "evaluation_status",
                "schema_valid",
                "schema_version",
            ],
            "schema_files": [
                "attack_plan.schema.json",
                "schema_manifest.json",
                "task_metadata.schema.json",
                "verifier_result.schema.json",
            ],
            "security_claim": False,
            "submission_required_fields": [
                "attack_plan_id",
                "metadata",
                "operators",
                "target",
            ],
            "task_metadata_required_fields": [
                "operator_assumptions",
                "operator_types",
                "seed_attack_plan_sha256",
                "seed_accepted",
                "seed_evaluation_status",
                "seed_estimator_name",
                "seed_reproduction_attempted",
                "seed_reproduction_status",
                "seed_reproduction_success",
                "seed_reward",
            ],
            "task_metadata_schema_version": TASK_METADATA_SCHEMA,
        },
        "failures": [],
    }


def test_prime_schemas_verify_rejects_schema_and_safety_drift(
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "schemas"
    bundle = write_prime_verifier_schemas(out_dir)
    manifest = bundle["schema_manifest.json"]
    manifest["safety"]["accepts_arbitrary_code"] = True
    manifest["release_gates"] = [
        gate
        for gate in manifest["release_gates"]
        if "prime-schemas-verify" not in gate
    ]
    (out_dir / "schema_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result_schema = bundle["verifier_result.schema.json"]
    result_schema["required"].remove("schema_valid")
    (out_dir / "verifier_result.schema.json").write_text(
        json.dumps(result_schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = verify_prime_verifier_schemas(out_dir)

    assert result["accepted"] is False
    assert "Prime verifier schema is not in sync: schema_manifest.json." in result[
        "failures"
    ]
    assert (
        "Prime verifier schema is not in sync: verifier_result.schema.json."
        in result["failures"]
    )
    assert "Prime schema manifest allows arbitrary code." in result["failures"]
    assert "Prime result schema does not require schema_valid." in result["failures"]
    assert any("prime-schemas-verify" in failure for failure in result["failures"])


def test_prime_schemas_verify_rejects_missing_schema_bundle(
    tmp_path: Path,
) -> None:
    result = verify_prime_verifier_schemas(tmp_path / "missing-schemas")

    assert result["accepted"] is False
    assert "Prime verifier schema directory is missing." in result["failures"]
    assert "Prime verifier schema is missing: schema_manifest.json." in result[
        "failures"
    ]


def test_prime_schemas_cli_writes_schema_bundle(tmp_path: Path) -> None:
    out_dir = tmp_path / "schemas"

    result = CliRunner().invoke(app, ["prime-schemas", "--out", str(out_dir)])

    assert result.exit_code == 0
    assert f"prime_schemas={out_dir}" in result.output
    assert json.loads((out_dir / "schema_manifest.json").read_text())[
        "schema_version"
    ] == "agades.pqc.prime_verifier_schemas.v1"


def test_prime_schemas_verify_cli_accepts_current_schema_bundle() -> None:
    result = CliRunner().invoke(
        app,
        [
            "prime-schemas-verify",
            "--schemas",
            "prime_intellect/schemas",
        ],
    )

    assert result.exit_code == 0
    assert "agades.pqc.prime_verifier_schemas_verification.v1" in result.output
    assert '"accepted": true' in result.output
