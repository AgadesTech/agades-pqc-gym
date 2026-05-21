from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.deepevolve_research_hooks import (
    DEEPEVOLVE_RESEARCH_HOOKS_SCHEMA,
    DEEPEVOLVE_RESEARCH_HOOKS_VERIFICATION_SCHEMA,
    build_deepevolve_research_hooks_manifest,
    verify_deepevolve_research_hooks_manifest,
    write_deepevolve_research_hooks_manifest,
)
from agades_pqc_gym.integrations.private_training_config import (
    PRIVATE_TRAINING_REQUIRED_ENV_VARS,
)


def test_deepevolve_manifest_describes_review_gated_paper_cards(
    tmp_path: Path,
) -> None:
    out = tmp_path / "deepevolve_research_hooks_manifest.json"

    manifest = write_deepevolve_research_hooks_manifest(out)

    assert manifest == build_deepevolve_research_hooks_manifest()
    assert json.loads(out.read_text()) == manifest
    assert manifest["schema_version"] == DEEPEVOLVE_RESEARCH_HOOKS_SCHEMA
    assert manifest["safety"] == {
        "arbitrary_code_execution": False,
        "contains_private_traces": False,
        "modifies_estimator_scores": False,
        "publishes_private_candidates": False,
        "research_claim": False,
        "review_required_before_implementation": True,
    }
    assert manifest["private_qwen_research_binding"] == {
        "model": "Qwen3.6-27B-private",
        "base_model_env": "AGADES_QWEN_BASE_MODEL",
        "lora_adapter_env": "AGADES_QWEN_LORA_ADAPTER_PATH",
        "gguf_otq_5bit_env": "AGADES_QWEN_GGUF_OTQ_5BIT_PATH",
        "artifact_plan_env": "AGADES_QWEN_ARTIFACT_PLAN",
        "artifact_plan_template": "private/reports/qwen/artifact_plan.json",
        "artifact_plan_schema": "agades.pqc.private_qwen_artifact_plan.v1",
        "artifact_verification_schema": (
            "agades.pqc.private_qwen_artifact_verification.v1"
        ),
        "artifact_verification_command": (
            "uv run agades-pqc private-qwen-artifacts-verify --plan "
            "private/reports/qwen/artifact_plan.json"
        ),
        "required_env_vars": PRIVATE_TRAINING_REQUIRED_ENV_VARS,
        "training_manifest": "docs/private_training_config_manifest.json",
        "training_readiness": "docs/private_training_readiness.json",
        "pedagogical_rl_method": "docs/pedagogical_rl_method.json",
        "dataset_curation_manifest": "docs/private_dataset_curation.json",
        "public_model_id_allowed": False,
        "proposal_roles": [
            "generate_attackplan",
            "mutate_attackplan",
            "critique_attackplan",
            "repair_attackplan",
            "draft_proof_obligations",
            "draft_family_invariants",
            "propose_evaluation_strategy",
        ],
        "proposal_gate": {
            "attackplan_validation_required": True,
            "proof_obligation_generation_required": True,
            "private_qwen_artifact_verification_required": True,
            "estimator_compatibility_required": True,
            "human_review_required_before_claim": True,
        },
        "public_publication_allowed": False,
    }
    assert manifest["summary"] == {
        "all_cards_note_only": True,
        "all_proposals_review_required": True,
        "card_count": 8,
        "families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
        ],
        "operator_count": 13,
        "proposal_count": 13,
    }
    assert all(
        card["implementation_status"] == "note_only"
        for card in manifest["paper_cards"]
    )
    assert all(
        proposal["review_required"] is True
        for proposal in manifest["hypothesis_proposals"]
    )
    assert {
        proposal["target_family"]
        for proposal in manifest["hypothesis_proposals"]
    } >= {
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "MULTIVARIATE",
    }


def test_committed_deepevolve_manifest_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "deepevolve_research_hooks_manifest.json"
    committed = Path("docs/deepevolve_research_hooks_manifest.json")

    write_deepevolve_research_hooks_manifest(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_deepevolve_manifest_verify_accepts_committed_manifest() -> None:
    result = verify_deepevolve_research_hooks_manifest(
        Path("docs/deepevolve_research_hooks_manifest.json")
    )

    assert result["schema_version"] == DEEPEVOLVE_RESEARCH_HOOKS_VERIFICATION_SCHEMA
    assert result["accepted"] is True
    assert result["summary"] == {
        "card_count": 8,
        "failure_count": 0,
        "proposal_count": 13,
        "private_qwen_bound": True,
    }


def test_deepevolve_manifest_verify_rejects_unreviewed_proposal(
    tmp_path: Path,
) -> None:
    manifest = build_deepevolve_research_hooks_manifest()
    manifest["hypothesis_proposals"][0]["review_required"] = False
    path = tmp_path / "bad_manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    result = verify_deepevolve_research_hooks_manifest(path)

    assert result["accepted"] is False
    assert any("review_required" in failure for failure in result["failures"])


def test_deepevolve_manifest_verify_rejects_incomplete_qwen_runtime_contract(
    tmp_path: Path,
) -> None:
    manifest = build_deepevolve_research_hooks_manifest()
    manifest["private_qwen_research_binding"]["required_env_vars"] = ["HF_TOKEN"]
    path = tmp_path / "bad_qwen_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_deepevolve_research_hooks_manifest(path)

    assert result["accepted"] is False
    assert "DeepEvolve private Qwen runtime contract is incomplete." in (
        result["failures"]
    )


def test_deepevolve_manifest_verify_rejects_missing_qwen_artifact_gate(
    tmp_path: Path,
) -> None:
    manifest = build_deepevolve_research_hooks_manifest()
    manifest["private_qwen_research_binding"]["proposal_gate"][
        "private_qwen_artifact_verification_required"
    ] = False
    path = tmp_path / "bad_qwen_gate_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_deepevolve_research_hooks_manifest(path)

    assert result["accepted"] is False
    assert (
        "private_qwen_research_binding.private_qwen_artifact_verification_required "
        "must be true."
    ) in result["failures"]


def test_deepevolve_manifest_verify_rejects_runtime_manifest_drift(
    tmp_path: Path,
) -> None:
    manifest = build_deepevolve_research_hooks_manifest()
    manifest["project"]["name"] = "Other PQC Gym"
    path = tmp_path / "stale_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_deepevolve_research_hooks_manifest(path)

    assert result["accepted"] is False
    assert result["failures"] == [
        "DeepEvolve research hook manifest is not in sync."
    ]


def test_deepevolve_manifest_cli_writes_manifest(tmp_path: Path) -> None:
    out = tmp_path / "deepevolve_research_hooks_manifest.json"

    result = CliRunner().invoke(app, ["deepevolve-manifest", "--out", str(out)])

    assert result.exit_code == 0
    assert f"deepevolve_manifest={out}" in result.output
    assert json.loads(out.read_text())["schema_version"] == (
        DEEPEVOLVE_RESEARCH_HOOKS_SCHEMA
    )


def test_deepevolve_manifest_verify_cli_rejects_bad_manifest(tmp_path: Path) -> None:
    path = tmp_path / "bad_manifest.json"
    path.write_text(
        json.dumps({"schema_version": DEEPEVOLVE_RESEARCH_HOOKS_SCHEMA}),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        ["deepevolve-manifest-verify", "--manifest", str(path)],
    )

    assert result.exit_code == 1
    assert "accepted" in result.output
