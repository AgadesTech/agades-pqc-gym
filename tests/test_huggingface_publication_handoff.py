from __future__ import annotations

import json
from pathlib import Path

from expected_family_support_summary import EXPECTED_FAMILY_SUPPORT_SUMMARY
from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.huggingface_publication_handoff import (
    build_huggingface_publication_handoff,
    verify_huggingface_publication_handoff,
    write_huggingface_publication_handoff,
)

EXPECTED_HF_ARTIFACT_PATHS = [
    "hf/dataset/README.md",
    "hf/dataset/dataset_info.json",
    "hf/dataset/attack_plans.jsonl",
    "hf/dataset/task_metadata.jsonl",
    "hf/dataset/verifier_outputs.jsonl",
    "hf/dataset/MANIFEST.sha256",
    "hf/README.md",
    "hf/app.py",
    "hf/requirements.txt",
    "hf/space_README.md",
    "hf/space_manifest.json",
    "hf/dataset_card.md",
    "hf/benchmark_card.md",
    "hf/collection_manifest.json",
    "docs/source_catalog.json",
    "docs/public_benchmark_manifest.json",
    "public/run_export/manifest.json",
    "docs/HUGGINGFACE_RELEASE_PLAN.md",
]
EXPECTED_SOURCE_CATALOG_SCOPE = {
    "non_lattice_toy_evaluator_count": 41,
    "non_lattice_toy_operator_families": [
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "MULTIVARIATE",
    ],
    "non_lattice_toy_operator_security_claims": 0,
    "non_lattice_toy_operator_variant_count": 41,
    "source_count": 41,
}


def test_huggingface_publication_handoff_records_review_boundaries(
    tmp_path: Path,
) -> None:
    out = tmp_path / "huggingface_publication_handoff.json"

    handoff = write_huggingface_publication_handoff(out)

    assert handoff == build_huggingface_publication_handoff()
    assert json.loads(out.read_text(encoding="utf-8")) == handoff
    assert handoff["schema_version"] == "agades.pqc.hf_publication_handoff.v1"
    assert handoff["project"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "cli": "agades-pqc",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert handoff["platform"] == {
        "ecosystem": "hugging_face",
        "handoff_status": "local_artifacts_ready_external_publication_blocked",
        "dataset_repo_type": "dataset",
        "dataset_suggested_repo_id": "agades/pqc-gym-toy",
        "space_repo_type": "space",
        "space_suggested_repo_id": "AgadesTech/agades-pqc-gym-agent-env",
        "collection_suggested_slug": "agades/pqc-gym",
        "release_plan": "docs/HUGGINGFACE_RELEASE_PLAN.md",
    }
    assert handoff["readiness"] == {
        "dataset_bundle_accepted": True,
        "space_manifest_accepted": True,
        "collection_manifest_accepted": True,
        "attack_plan_count": 80,
        "valid_attack_plan_count": 79,
        "invalid_attack_plan_count": 1,
        "task_metadata_rows": 79,
        "space_example_count": 79,
        "collection_entry_count": 7,
        "public_run_bundles": 18,
        "requires_credentials": True,
        "credentials_checked_at_generation": False,
        "credentials_present_in_artifact": False,
        "external_publication_requires_review": True,
        "hf_hub_publication_performed": False,
    }
    assert handoff["publication_commands"] == {
        "dataset_private_create": (
            "hf repo create <owner>/pqc-gym-toy --repo-type=dataset "
            "--private --exist-ok"
        ),
        "dataset_upload": (
            "hf upload <owner>/pqc-gym-toy hf/dataset . --repo-type=dataset "
            '--commit-message "Sync Agades PQC Gym dataset"'
        ),
        "space_private_create": (
            "hf repo create AgadesTech/agades-pqc-gym-agent-env --repo-type=space "
            "--space_sdk gradio "
            "--private --exist-ok"
        ),
        "space_upload": (
            "hf upload AgadesTech/agades-pqc-gym-agent-env hf . --repo-type=space "
            '--commit-message "Sync Agades PQC Gym Agent Environment"'
        ),
        "collection_manual_review_required": True,
    }
    assert handoff["source_anchors"] == [
        {
            "id": "agades-hf-dataset",
            "source_catalog_required": True,
            "current_use": "current_public_artifact",
        },
        {
            "id": "agades-hf-space",
            "source_catalog_required": True,
            "current_use": "current_public_gradio_space_contract",
        },
        {
            "id": "agades-hf-collection",
            "source_catalog_required": True,
            "current_use": "current_public_collection_contract",
        },
        {
            "id": "hf-post-quantum-crypto-en",
            "source_catalog_required": True,
            "current_use": "future_pqc_instruction_eval_seed",
        },
        {
            "id": "hf-post-quantum-crypto-fr",
            "source_catalog_required": True,
            "current_use": "future_pqc_instruction_eval_seed",
        },
        {
            "id": "hf-pqc-ssl-scans",
            "source_catalog_required": True,
            "current_use": "future_pqc_migration_scoring_anchor",
        },
        {
            "id": "hf-sc2026-side-channel",
            "source_catalog_required": True,
            "current_use": "future_side_channel_research_anchor",
        },
    ]
    assert handoff["family_support"] == EXPECTED_FAMILY_SUPPORT_SUMMARY
    assert handoff["source_catalog_scope"] == EXPECTED_SOURCE_CATALOG_SCOPE
    assert handoff["local_artifacts"]["artifact_paths"] == EXPECTED_HF_ARTIFACT_PATHS
    assert sorted(handoff["local_artifacts"]["artifact_sha256"]) == sorted(
        EXPECTED_HF_ARTIFACT_PATHS
    )
    assert handoff["safety"] == {
        "contains_private_traces": False,
        "publishes_private_candidates": False,
        "arbitrary_code_execution": False,
        "live_targeting": False,
        "security_claim": False,
        "claims_external_publication": False,
        "credentials_present_in_artifact": False,
    }
    assert handoff["review_required_before_publish"] == [
        "Confirm Hugging Face account, organization, and target namespaces.",
        "Create or update dataset and Space as private first.",
        (
            "Run dataset, Space, Collection, release audit, and publication "
            "preflight gates."
        ),
        (
            "Review cards for no private traces, no executable submissions, "
            "and no security claims."
        ),
        "Record external Hugging Face URLs only after credentialed review.",
    ]
    assert handoff["release_gates"] == [
        "uv run pytest tests/test_huggingface_publication_handoff.py -q",
        "uv run agades-pqc hf-publication-handoff --out "
        "docs/huggingface_publication_handoff.json",
        "uv run agades-pqc hf-publication-handoff-verify --handoff "
        "docs/huggingface_publication_handoff.json",
        "uv run agades-pqc hf-dataset-verify --dataset hf/dataset",
        "uv run agades-pqc hf-space-manifest-verify --manifest hf/space_manifest.json",
        "uv run agades-pqc hf-collection-manifest-verify --manifest "
        "hf/collection_manifest.json",
        "uv run agades-pqc publication-preflight-verify --preflight "
        "public/publication_preflight.json",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]


def test_committed_huggingface_publication_handoff_is_in_sync(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "huggingface_publication_handoff.json"
    committed = Path("docs/huggingface_publication_handoff.json")

    write_huggingface_publication_handoff(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_huggingface_publication_handoff_verify_accepts_committed_handoff() -> None:
    result = verify_huggingface_publication_handoff(
        Path("docs/huggingface_publication_handoff.json")
    )

    assert result == {
        "schema_version": "agades.pqc.hf_publication_handoff_verification.v1",
        "handoff_path": "docs/huggingface_publication_handoff.json",
        "accepted": True,
        "summary": {
            "artifact_count": 18,
            "attack_plan_count": 80,
            "collection_entry_count": 7,
            "external_publication_requires_review": True,
            "failure_count": 0,
            "family_count": 9,
            "family_support_review_required_before_claims": True,
            "implemented_families": ["LWE", "MLWE"],
            "non_lattice_toy_evaluator_count": 41,
            "non_lattice_toy_operator_security_claims": 0,
            "non_lattice_toy_operator_variant_count": 41,
            "public_run_bundles": 18,
            "space_example_count": 79,
            "task_metadata_rows": 79,
            "valid_attack_plan_count": 79,
        },
        "failures": [],
    }


def test_huggingface_publication_handoff_verify_rejects_external_publication_claim(
    tmp_path: Path,
) -> None:
    handoff = build_huggingface_publication_handoff()
    handoff["readiness"]["hf_hub_publication_performed"] = True
    handoff["safety"]["claims_external_publication"] = True
    out = tmp_path / "huggingface_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_huggingface_publication_handoff(out)

    assert result["accepted"] is False
    assert "Hugging Face publication handoff is not in sync." in result["failures"]
    assert "Hugging Face handoff must not claim Hub publication." in result[
        "failures"
    ]
    assert "Hugging Face handoff claims external publication." in result["failures"]


def test_huggingface_publication_handoff_verify_rejects_credential_leak(
    tmp_path: Path,
) -> None:
    handoff = build_huggingface_publication_handoff()
    handoff["readiness"]["credentials_present_in_artifact"] = True
    handoff["safety"]["credentials_present_in_artifact"] = True
    out = tmp_path / "huggingface_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_huggingface_publication_handoff(out)

    assert result["accepted"] is False
    assert "Hugging Face handoff must not include credential evidence." in result[
        "failures"
    ]


def test_huggingface_publication_handoff_verify_rejects_source_scope_claim(
    tmp_path: Path,
) -> None:
    handoff = build_huggingface_publication_handoff()
    handoff["source_catalog_scope"]["non_lattice_toy_operator_security_claims"] = 1
    out = tmp_path / "huggingface_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_huggingface_publication_handoff(out)

    assert result["accepted"] is False
    assert "Hugging Face publication handoff is not in sync." in result["failures"]
    assert (
        "Hugging Face handoff source catalog scope must not contain "
        "non-lattice toy security claims."
    ) in result["failures"]


def test_huggingface_publication_handoff_verify_rejects_family_support_claim_gate(
    tmp_path: Path,
) -> None:
    handoff = build_huggingface_publication_handoff()
    handoff["family_support"]["review_required_before_claims"] = False
    out = tmp_path / "huggingface_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_huggingface_publication_handoff(out)

    assert result["accepted"] is False
    assert "Hugging Face publication handoff is not in sync." in result["failures"]
    assert (
        "Hugging Face handoff family_support.review_required_before_claims "
        "must be true."
    ) in result["failures"]


def test_huggingface_publication_handoff_cli_writes_handoff(tmp_path: Path) -> None:
    out = tmp_path / "huggingface_publication_handoff.json"

    result = CliRunner().invoke(
        app,
        ["hf-publication-handoff", "--out", str(out)],
    )

    assert result.exit_code == 0
    assert f"huggingface_publication_handoff={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["schema_version"] == (
        "agades.pqc.hf_publication_handoff.v1"
    )


def test_huggingface_publication_handoff_verify_cli_accepts_committed_handoff() -> None:
    result = CliRunner().invoke(
        app,
        [
            "hf-publication-handoff-verify",
            "--handoff",
            "docs/huggingface_publication_handoff.json",
        ],
    )

    assert result.exit_code == 0
    assert "agades.pqc.hf_publication_handoff_verification.v1" in result.output
    assert '"accepted": true' in result.output
