from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.private_dataset_curation import (
    PRIVATE_DATASET_CURATION_VERIFICATION_SCHEMA,
    build_private_dataset_curation,
    verify_private_dataset_curation,
    write_private_dataset_curation,
)

CURATION_PATH = Path("docs/private_dataset_curation.json")


def test_private_dataset_curation_defines_private_source_controls(
    tmp_path: Path,
) -> None:
    out = tmp_path / "private_dataset_curation.json"

    payload = write_private_dataset_curation(out)

    assert payload == build_private_dataset_curation()
    assert json.loads(out.read_text(encoding="utf-8")) == payload
    assert payload["schema_version"] == "agades.pqc.private_dataset_curation.v1"
    assert payload["sources"] == {
        "facebookresearch_lwe_benchmarking": {
            "source": "facebookresearch/LWE-benchmarking",
            "upstream_url": "https://github.com/facebookresearch/LWE-benchmarking",
            "kind": "lwe_benchmark_source",
            "intended_private_use": "lwe_mlwe_task_generation_and_teacher_context",
            "license_review_status": "required_unverified",
            "ingestion_allowed_before_license_review": False,
        },
        "facebook_tapas": {
            "source": "facebook/TAPAS",
            "upstream_url": "https://huggingface.co/datasets/facebook/TAPAS",
            "kind": "lwe_learning_dataset",
            "intended_private_use": "lwe_trace_pedagogy_and_student_curriculum",
            "license_review_status": "required_unverified",
            "ingestion_allowed_before_license_review": False,
        },
        "pq_code_package": {
            "source": "pq-code-package",
            "upstream_url": "https://github.com/pq-code-package",
            "kind": "implementation_security_source_corpus",
            "intended_private_use": (
                "implementation_security_attackplan_context_after_review"
            ),
            "license_review_status": "required_unverified",
            "ingestion_allowed_before_license_review": False,
        },
    }
    assert [stage["id"] for stage in payload["pipeline"]] == [
        "source_license_review",
        "source_provenance_capture",
        "raw_ingest_to_private_storage",
        "deduplicate_and_normalize",
        "redact_sensitive_material",
        "contamination_audit",
        "curated_trace_export_gate",
    ]
    assert payload["required_controls"] == [
        "license_review",
        "provenance_tracking",
        "deduplication",
        "redaction",
        "contamination_audit",
    ]
    assert payload["outputs"] == {
        "public_manifest_only": True,
        "public_rows_allowed": False,
        "public_prompts_allowed": False,
        "public_reviewer_annotations_allowed": False,
        "public_finetuning_corpus_allowed": False,
        "private_roots": [
            "private/datasets/agades_pedagogical_rl",
            "private/reports/dataset_curation",
            "private/traces/pedagogical_rl",
        ],
        "curated_dataset_path": (
            "private/datasets/agades_pedagogical_rl/"
            "curated_attackplan_traces.jsonl"
        ),
        "provenance_manifest_path": (
            "private/reports/dataset_curation/provenance_manifest.json"
        ),
        "contamination_report_path": (
            "private/reports/dataset_curation/contamination_audit.json"
        ),
    }
    assert payload["contamination_audit"] == {
        "public_reference_roots": [
            "examples/attack_plans",
            "hf/dataset",
            "prime_intellect/verifiers_environment/data",
        ],
        "reject_exact_public_overlap": True,
        "reject_prompt_or_reviewer_annotation_leakage": True,
        "requires_hash_and_similarity_report": True,
        "requires_manual_review": True,
    }
    assert payload["publication_boundary"]["forbidden_public_artifacts"] == [
        "private_dataset_rows",
        "raw_source_rows",
        "derived_training_rows",
        "pedagogical_rl_rollouts",
        "reviewer_annotations",
        "teacher_prompts",
        "student_prompts",
        "fine_tuning_corpora",
    ]
    assert payload["linked_artifacts"]["source_catalog"]["path"] == (
        "docs/source_catalog.json"
    )
    assert payload["linked_artifacts"]["benchmark_source_contracts"]["path"] == (
        "docs/benchmark_source_contracts.json"
    )
    assert payload["linked_artifacts"]["private_run_policy"]["path"] == (
        "docs/private_run_policy.json"
    )


def test_committed_private_dataset_curation_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "private_dataset_curation.json"

    write_private_dataset_curation(generated)

    assert CURATION_PATH.read_bytes() == generated.read_bytes()


def test_private_dataset_curation_verify_accepts_committed_artifact() -> None:
    result = verify_private_dataset_curation(CURATION_PATH)

    assert result == {
        "schema_version": PRIVATE_DATASET_CURATION_VERIFICATION_SCHEMA,
        "curation_path": CURATION_PATH.as_posix(),
        "accepted": True,
        "summary": {
            "sources": 3,
            "pipeline_stages": 7,
            "required_controls": 5,
            "linked_artifacts": 3,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_private_dataset_curation_rejects_public_outputs_or_skipped_license(
    tmp_path: Path,
) -> None:
    out = tmp_path / "private_dataset_curation.json"
    payload = write_private_dataset_curation(out)
    payload["outputs"]["public_rows_allowed"] = True
    payload["sources"]["facebook_tapas"][
        "ingestion_allowed_before_license_review"
    ] = True
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    result = verify_private_dataset_curation(out)

    assert result["accepted"] is False
    assert "Private dataset rows must never be public." in result["failures"]
    assert "Dataset ingestion must wait for license review." in result["failures"]


def test_private_dataset_curation_cli_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "private_dataset_curation.json"

    write_result = CliRunner().invoke(
        app,
        ["private-dataset-curation", "--out", str(out)],
    )
    verify_result = CliRunner().invoke(
        app,
        ["private-dataset-curation-verify", "--curation", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"private_dataset_curation={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert '"accepted": true' in verify_result.output
