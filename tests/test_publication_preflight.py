from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.publication_preflight import (
    PUBLICATION_PREFLIGHT_VERIFICATION_SCHEMA,
    build_publication_preflight,
    verify_publication_preflight,
    write_publication_preflight,
)

EXPECTED_FAMILY_SUPPORT_PUBLICATION_GATE = {
    "family_count": 9,
    "implemented": ["LWE", "MLWE"],
    "schema_only": ["NTRU", "SIS"],
    "toy_evaluators": [
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "MULTIVARIATE",
    ],
    "families_with_future_reviewed_adapters": [
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "LWE",
        "MLWE",
        "MULTIVARIATE",
        "NTRU",
        "SIS",
    ],
    "future_reviewed_adapter_sources_by_family": 21,
    "unique_future_reviewed_adapter_source_count": 15,
    "review_required_before_claims": True,
    "platform_support": {
        "family_counts_match": True,
        "missing_claim_review_gate": [],
        "platforms": [
            "huggingface_collection",
            "nvidia",
            "prime_intellect",
        ],
        "platforms_with_claim_review_gate": [
            "huggingface_collection",
            "nvidia",
            "prime_intellect",
        ],
        "surface_count": 3,
    },
}
EXPECTED_PUBLIC_PRIVATE_BOUNDARY = {
    "report_generator_redaction": {
        "blocking": True,
        "check_id": "report-generator-redaction",
        "private_evaluator_output_absent": True,
        "private_mapping_evaluator_output_absent": True,
        "private_mapping_score_absent": True,
        "private_mapping_target_absent": True,
        "private_mutation_absent": True,
        "private_score_absent": True,
        "raw_mapping_redaction_covered": True,
        "redacted_records": 2,
        "sensitive_target_absent": True,
        "status": "passed",
        "typed_trace_redaction_covered": True,
    }
}
EXPECTED_SOURCE_CATALOG_PUBLICATION_SCOPE = {
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
    "platform_source_catalog_scope_counts_match": True,
    "platform_source_catalog_scope_security_claims": 0,
    "platform_source_catalog_scope_surfaces": 3,
    "source_count": 41,
}
EXPECTED_PRIME_HUB_WARNING_EVIDENCE = {
    "external_execution_requires_review": True,
    "external_publication_requires_review": True,
    "local_package_ready": True,
    "prime_hub_publication_performed": False,
    "publication_artifact_count": 12,
    "publication_family_count": 9,
    "publication_task_count": 79,
    "requires_credentials": True,
    "speedrun_artifact_count": 11,
    "speedrun_bundle_count": 18,
    "speedrun_family_count": 9,
    "speedrun_run_count": 59,
    "speedrun_task_count": 79,
}
EXPECTED_EXTERNAL_REVIEW = {
    "blockers": 2,
    "credential_material_included": False,
    "credential_review_queue_complete": True,
    "credential_review_queue_items": 4,
    "credentialed_surface_count": 4,
    "ready_for_external_publication": False,
    "review_required_before_claims": True,
    "review_required_surface_count": 6,
    "reviewer_summary_synced": True,
    "surface_count": 6,
    "warning_evidence_items": 1,
    "warnings": 1,
}
EXPECTED_RUNBOOK_ARCHITECTURE = {
    "core_symbol_count": 14,
    "core_symbol_import_count": 14,
    "family_plugin_count": 6,
    "family_plugin_manifest_digests_match": True,
    "family_plugin_module_count": 55,
    "family_plugin_module_digest_count": 55,
    "family_plugin_module_import_count": 55,
    "family_registry_family_count_matches_plugin_manifest": True,
    "family_registry_plugin_count_matches_plugin_manifest": True,
    "family_registry_plugin_manifest_module_digest_count": 55,
    "family_registry_plugin_manifest_synced": True,
    "family_registry_runtime_adapter_entries_match_plugin_manifest": True,
    "lattice_is_first_implemented_plugin": True,
    "planned_family_plugin_count": 5,
    "public_runbook_audit_checks": 7,
    "public_runbook_audit_synced": True,
}
EXPECTED_CREDENTIAL_REVIEW_QUEUE = [
    {
        "artifact_count": 7,
        "credential_material_included": False,
        "first_publication_target": "private_or_draft_review_surface",
        "id": "huggingface-collection",
        "platform": "hugging_face",
        "publication_status": "local_manifest_ready_review_required",
        "review_required_before_publish": True,
        "smoke_gate": "hf-collection-manifest",
    },
    {
        "artifact_count": 6,
        "credential_material_included": False,
        "first_publication_target": "private_or_draft_review_surface",
        "id": "huggingface-dataset",
        "platform": "hugging_face",
        "publication_status": "local_artifact_ready",
        "review_required_before_publish": True,
        "smoke_gate": "hf-dataset-safety",
    },
    {
        "artifact_count": 4,
        "credential_material_included": False,
        "first_publication_target": "private_or_draft_review_surface",
        "id": "huggingface-space",
        "platform": "hugging_face",
        "publication_status": "local_artifact_ready",
        "review_required_before_publish": True,
        "smoke_gate": "hf-space-smoke",
    },
    {
        "artifact_count": 11,
        "credential_material_included": False,
        "first_publication_target": "private_or_draft_review_surface",
        "id": "prime-verifiers-environment",
        "platform": "prime_intellect",
        "publication_status": "local_package_ready",
        "review_required_before_publish": True,
        "smoke_gate": "prime-environment-smoke",
    },
]
EXPECTED_PLATFORM_REVIEW_MATRIX = {
    "github": {
        "artifact_count": 34,
        "credentialed_surface_count": 0,
        "publication_statuses": ["draft_pr_ready"],
        "review_required_surface_count": 1,
        "smoke_gates": ["github-actions-ci"],
        "surface_count": 1,
        "surface_ids": ["github-repository"],
    },
    "hugging_face": {
        "artifact_count": 17,
        "credentialed_surface_count": 3,
        "publication_statuses": [
            "local_artifact_ready",
            "local_manifest_ready_review_required",
        ],
        "review_required_surface_count": 3,
        "smoke_gates": [
            "hf-collection-manifest",
            "hf-dataset-safety",
            "hf-space-smoke",
        ],
        "surface_count": 3,
        "surface_ids": [
            "huggingface-collection",
            "huggingface-dataset",
            "huggingface-space",
        ],
    },
    "nvidia": {
        "artifact_count": 4,
        "credentialed_surface_count": 0,
        "publication_statuses": ["strategy_ready_review_required"],
        "review_required_surface_count": 1,
        "smoke_gates": ["nvidia-manifest-safety"],
        "surface_count": 1,
        "surface_ids": ["nvidia-accelerator-story"],
    },
    "prime_intellect": {
        "artifact_count": 11,
        "credentialed_surface_count": 1,
        "publication_statuses": ["local_package_ready"],
        "review_required_surface_count": 1,
        "smoke_gates": ["prime-environment-smoke"],
        "surface_count": 1,
        "surface_ids": ["prime-verifiers-environment"],
    },
}


def test_publication_preflight_blocks_external_publication_without_review() -> None:
    preflight = build_publication_preflight()

    assert preflight["schema_version"] == "agades.pqc.publication_preflight.v1"
    assert preflight["project"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "cli": "agades-pqc",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert preflight["inputs"] == {
        "family_support_matrix": "docs/family_support_matrix.json",
        "publication_manifest": "docs/publication_manifest.json",
        "release_audit": "public/release_audit.json",
        "release_status": "docs/release_status.json",
    }
    assert preflight["local_artifacts_ready"] is True
    assert preflight["ready_for_external_publication"] is False
    assert preflight["review_state"] == {
        "credentials_reviewed": False,
        "external_release_review_approved": False,
    }
    assert preflight["publication"] == {
        "surfaces": 6,
        "review_required_surfaces": 6,
        "credentialed_surfaces": [
            "huggingface-collection",
            "huggingface-dataset",
            "huggingface-space",
            "prime-verifiers-environment",
        ],
        "public_run_bundles": 18,
    }
    assert preflight["credential_review_queue"] == EXPECTED_CREDENTIAL_REVIEW_QUEUE
    assert preflight["family_support"] == EXPECTED_FAMILY_SUPPORT_PUBLICATION_GATE
    assert (
        preflight["source_catalog_scope"]
        == EXPECTED_SOURCE_CATALOG_PUBLICATION_SCOPE
    )
    assert preflight["public_private_boundary"] == EXPECTED_PUBLIC_PRIVATE_BOUNDARY
    assert preflight["runbook_architecture"] == EXPECTED_RUNBOOK_ARCHITECTURE
    assert preflight["platform_review_matrix"] == EXPECTED_PLATFORM_REVIEW_MATRIX
    family_readiness = preflight["family_readiness_matrix"]
    assert sorted(family_readiness) == [
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "LWE",
        "MLWE",
        "MULTIVARIATE",
        "NTRU",
        "SIS",
    ]
    assert family_readiness["LWE"] == {
        "benchmark_count": 5,
        "cross_family_review_source_count": 3,
        "default_estimator": "mock-lattice-estimator",
        "evaluator_status": "implemented",
        "future_reviewed_adapter_source_count": 2,
        "lattice_estimator_enabled": True,
        "operator_count": 12,
        "plugin": "lattice",
        "public_example_count": 10,
        "reproduction_status": (
            "downscaled_lwe_mlwe_fixture_solvers_and_estimator_replay_available_"
            "for_public_toy_targets"
        ),
        "review_required_before_claims": True,
        "support_level": "implemented",
    }
    assert family_readiness["CODE_BASED"] == {
        "benchmark_count": 21,
        "cross_family_review_source_count": 3,
        "default_estimator": "toy-code-based-isd-estimator",
        "evaluator_status": "implemented_toy",
        "future_reviewed_adapter_source_count": 3,
        "lattice_estimator_enabled": False,
        "operator_count": 2,
        "plugin": "code_based",
        "public_example_count": 21,
        "reproduction_status": (
            "toy_syndrome_hqc_mdpc_and_classic_mceliece_fixture_solvers_"
            "available_for_public_fixtures"
        ),
        "review_required_before_claims": True,
        "support_level": "toy_evaluator",
    }
    assert family_readiness["NTRU"]["support_level"] == "schema_only"
    assert family_readiness["NTRU"]["default_estimator"] is None
    assert family_readiness["NTRU"]["lattice_estimator_enabled"] is False
    assert [
        family
        for family, readiness in family_readiness.items()
        if readiness["lattice_estimator_enabled"]
    ] == ["LWE", "MLWE"]
    assert preflight["audit"] == {
        "accepted": True,
        "failed": 0,
        "passed": 60,
        "warning": 1,
        "warning_check_ids": ["prime-hub-publication"],
        "total": 61,
    }
    assert preflight["external_review"] == EXPECTED_EXTERNAL_REVIEW
    assert preflight["blockers"] == [
        {
            "id": "external_release_review_not_approved",
            "detail": (
                "External publication to Hugging Face, Prime Intellect, or "
                "public NVIDIA-facing channels requires explicit release review."
            ),
        },
        {
            "id": "credential_review_not_approved",
            "detail": (
                "Credentialed surfaces require token/account review before "
                "publication: huggingface-collection, huggingface-dataset, "
                "huggingface-space, prime-verifiers-environment."
            ),
        },
    ]
    assert preflight["warnings"] == [
        {
            "artifact": "prime_intellect/verifiers_environment",
            "id": "prime-hub-publication",
            "detail": (
                "Prime package is locally packaged but not published to the "
                "Prime Environments Hub without credentials and release review."
            ),
            "evidence": EXPECTED_PRIME_HUB_WARNING_EVIDENCE,
        }
    ]
    assert preflight["safety"] == {
        "arbitrary_code_execution": False,
        "contains_private_traces": False,
        "live_targeting": False,
        "publishes_private_candidates": False,
        "security_claim": False,
        "external_publication_requires_review": True,
    }
    assert preflight["release_gates"] == [
        (
            "uv run agades-pqc publication-preflight --out "
            "public/publication_preflight.json"
        ),
        (
            "uv run agades-pqc publication-preflight-verify --preflight "
            "public/publication_preflight.json"
        ),
        (
            "uv run agades-pqc ecosystem-smoke-verify --report "
            "reports/ecosystem_smoke.json"
        ),
    ]


def test_publication_preflight_models_reviewed_credentialed_release() -> None:
    preflight = build_publication_preflight(
        external_release_review_approved=True,
        credentials_reviewed=True,
    )

    assert preflight["local_artifacts_ready"] is True
    assert preflight["ready_for_external_publication"] is True
    assert preflight["review_state"] == {
        "credentials_reviewed": True,
        "external_release_review_approved": True,
    }
    assert preflight["blockers"] == []
    assert preflight["warnings"] == [
        {
            "artifact": "prime_intellect/verifiers_environment",
            "id": "prime-hub-publication",
            "detail": (
                "Prime package is locally packaged but not published to the "
                "Prime Environments Hub without credentials and release review."
            ),
            "evidence": EXPECTED_PRIME_HUB_WARNING_EVIDENCE,
        }
    ]


def test_committed_publication_preflight_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "publication_preflight.json"
    committed = Path("public/publication_preflight.json")

    write_publication_preflight(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_publication_preflight_cli_writes_preflight(tmp_path: Path) -> None:
    out = tmp_path / "publication_preflight.json"

    result = CliRunner().invoke(app, ["publication-preflight", "--out", str(out)])

    assert result.exit_code == 0
    assert f"publication_preflight={out}" in result.output
    assert json.loads(out.read_text())["ready_for_external_publication"] is False


def test_publication_preflight_verify_accepts_committed_artifact() -> None:
    result = verify_publication_preflight(Path("public/publication_preflight.json"))

    assert result == {
        "schema_version": PUBLICATION_PREFLIGHT_VERIFICATION_SCHEMA,
        "preflight_path": "public/publication_preflight.json",
        "accepted": True,
        "summary": {
            "blockers": 2,
            "credential_material_included": False,
            "credential_review_queue_complete": True,
            "credential_review_queue_items": 4,
            "failure_count": 0,
            "family_count": 9,
            "family_readiness_family_count": 9,
            "family_readiness_lattice_estimator_families": 2,
            "family_readiness_non_lattice_lattice_estimator_families": 0,
            "family_readiness_review_required_families": 9,
            "family_readiness_schema_only_default_estimators": 0,
            "local_artifacts_ready": True,
            "runbook_core_symbol_import_count": 14,
            "runbook_family_plugin_manifest_digests_match": True,
            "runbook_family_plugin_module_count": 55,
            "runbook_family_plugin_module_digest_count": 55,
            "runbook_family_plugin_module_import_count": 55,
            "runbook_family_registry_family_count_matches_plugin_manifest": True,
            "runbook_family_registry_plugin_count_matches_plugin_manifest": True,
            "runbook_family_registry_plugin_manifest_module_digest_count": 55,
            "runbook_family_registry_plugin_manifest_synced": True,
            "runbook_family_registry_runtime_adapter_entries_match_plugin_manifest": (
                True
            ),
            "platform_review_matrix_credentialed_surfaces": 4,
            "platform_review_matrix_review_required_surfaces": 6,
            "platform_review_matrix_surfaces": 6,
            "platform_family_support_family_counts_match": True,
            "platform_family_support_surfaces": 3,
            "platform_source_catalog_scope_counts_match": True,
            "platform_source_catalog_scope_security_claims": 0,
            "platform_source_catalog_scope_surfaces": 3,
            "platforms_with_family_claim_review_gate": 3,
            "non_lattice_toy_evaluator_count": 41,
            "non_lattice_toy_operator_security_claims": 0,
            "non_lattice_toy_operator_variant_count": 41,
            "raw_mapping_redaction_covered": True,
            "ready_for_external_publication": False,
            "report_redaction_records": 2,
            "reviewer_summary_synced": True,
            "review_required_before_claims": True,
            "typed_trace_redaction_covered": True,
            "warnings": 1,
            "warning_evidence_items": 1,
        },
        "failures": [],
    }


def test_publication_preflight_verify_rejects_overwritten_review_state(
    tmp_path: Path,
) -> None:
    path = tmp_path / "publication_preflight.json"
    preflight = build_publication_preflight()
    preflight["review_state"]["external_release_review_approved"] = True
    path.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n")

    result = verify_publication_preflight(path)

    assert result["accepted"] is False
    assert result["failures"] == [
        "Publication preflight is not in sync.",
        "Committed publication preflight must not mark release review approved.",
    ]


def test_publication_preflight_verify_rejects_platform_family_support_drift(
    tmp_path: Path,
) -> None:
    path = tmp_path / "publication_preflight.json"
    preflight = build_publication_preflight()
    preflight["family_support"]["platform_support"][
        "missing_claim_review_gate"
    ] = ["nvidia"]
    path.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n")

    result = verify_publication_preflight(path)

    assert result["accepted"] is False
    assert result["summary"]["platforms_with_family_claim_review_gate"] == 3
    assert result["failures"] == [
        "Publication preflight is not in sync.",
        "Publication preflight platform family-support gates are incomplete.",
    ]


def test_publication_preflight_verify_rejects_redaction_boundary_drift(
    tmp_path: Path,
) -> None:
    path = tmp_path / "publication_preflight.json"
    preflight = build_publication_preflight()
    preflight["public_private_boundary"]["report_generator_redaction"][
        "raw_mapping_redaction_covered"
    ] = False
    path.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n")

    result = verify_publication_preflight(path)

    assert result["accepted"] is False
    assert result["summary"]["raw_mapping_redaction_covered"] is False
    assert result["failures"] == [
        "Publication preflight is not in sync.",
        "Publication preflight raw trace mapping redaction gate is incomplete.",
    ]


def test_publication_preflight_verify_rejects_runbook_architecture_drift(
    tmp_path: Path,
) -> None:
    path = tmp_path / "publication_preflight.json"
    preflight = build_publication_preflight()
    preflight["runbook_architecture"]["core_symbol_import_count"] = 9
    preflight["runbook_architecture"][
        "family_plugin_manifest_digests_match"
    ] = False
    preflight["runbook_architecture"]["family_plugin_module_digest_count"] = 17
    preflight["runbook_architecture"]["family_plugin_module_import_count"] = 17
    preflight["runbook_architecture"]["family_registry_plugin_manifest_synced"] = False
    preflight["runbook_architecture"][
        "family_registry_plugin_manifest_module_digest_count"
    ] = 17
    preflight["runbook_architecture"][
        "family_registry_runtime_adapter_entries_match_plugin_manifest"
    ] = False
    path.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n")

    result = verify_publication_preflight(path)

    assert result["accepted"] is False
    assert result["summary"]["runbook_core_symbol_import_count"] == 9
    assert result["summary"]["runbook_family_plugin_manifest_digests_match"] is False
    assert result["summary"]["runbook_family_plugin_module_digest_count"] == 17
    assert result["summary"]["runbook_family_plugin_module_import_count"] == 17
    assert result["summary"]["runbook_family_registry_plugin_manifest_synced"] is False
    assert (
        result["summary"]["runbook_family_registry_plugin_manifest_module_digest_count"]
        == 17
    )
    assert (
        result["summary"][
            "runbook_family_registry_runtime_adapter_entries_match_plugin_manifest"
        ]
        is False
    )
    assert result["failures"] == [
        "Publication preflight is not in sync.",
        "Publication preflight runbook core import evidence is incomplete.",
        "Publication preflight runbook and family plugin manifest digests must match.",
        "Publication preflight runbook family plugin digest evidence is incomplete.",
        "Publication preflight runbook family plugin import evidence is incomplete.",
        "Publication preflight family registry and plugin manifest must be "
        "synchronized.",
        "Publication preflight family registry plugin manifest digest evidence "
        "is incomplete.",
        "Publication preflight family registry runtime adapters must match "
        "plugin manifest.",
    ]


def test_publication_preflight_verify_rejects_source_catalog_scope_drift(
    tmp_path: Path,
) -> None:
    path = tmp_path / "publication_preflight.json"
    preflight = build_publication_preflight()
    preflight["source_catalog_scope"][
        "non_lattice_toy_operator_security_claims"
    ] = 1
    preflight["source_catalog_scope"][
        "platform_source_catalog_scope_security_claims"
    ] = 1
    path.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n")

    result = verify_publication_preflight(path)

    assert result["accepted"] is False
    assert result["summary"]["non_lattice_toy_operator_security_claims"] == 1
    assert result["summary"]["platform_source_catalog_scope_security_claims"] == 1
    assert result["failures"] == [
        "Publication preflight is not in sync.",
        "Publication preflight source catalog scope must not contain "
        "non-lattice toy security claims.",
        "Publication preflight platform source catalog scope must not contain "
        "non-lattice toy security claims.",
    ]


def test_publication_preflight_verify_rejects_credential_queue_drift(
    tmp_path: Path,
) -> None:
    path = tmp_path / "publication_preflight.json"
    preflight = build_publication_preflight()
    preflight["credential_review_queue"][0]["credential_material_included"] = True
    path.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n")

    result = verify_publication_preflight(path)

    assert result["accepted"] is False
    assert result["summary"]["credential_material_included"] is True
    assert result["failures"] == [
        "Publication preflight is not in sync.",
        "Publication preflight credential review queue must not include "
        "credential material.",
    ]


def test_publication_preflight_verify_rejects_platform_review_matrix_drift(
    tmp_path: Path,
) -> None:
    path = tmp_path / "publication_preflight.json"
    preflight = build_publication_preflight()
    preflight["platform_review_matrix"]["hugging_face"]["surface_count"] = 2
    path.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n")

    result = verify_publication_preflight(path)

    assert result["accepted"] is False
    assert result["summary"]["platform_review_matrix_surfaces"] == 5
    assert result["failures"] == [
        "Publication preflight is not in sync.",
        "Publication preflight platform review matrix is inconsistent with "
        "surface notes.",
    ]


def test_publication_preflight_verify_rejects_family_readiness_drift(
    tmp_path: Path,
) -> None:
    path = tmp_path / "publication_preflight.json"
    preflight = build_publication_preflight()
    preflight["family_readiness_matrix"]["CODE_BASED"][
        "lattice_estimator_enabled"
    ] = True
    path.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n")

    result = verify_publication_preflight(path)

    assert result["accepted"] is False
    assert (
        result["summary"]["family_readiness_non_lattice_lattice_estimator_families"]
        == 1
    )
    assert result["failures"] == [
        "Publication preflight is not in sync.",
        "Publication preflight family readiness matrix is inconsistent with "
        "family support matrix.",
    ]


def test_publication_preflight_verify_rejects_warning_evidence_drift(
    tmp_path: Path,
) -> None:
    path = tmp_path / "publication_preflight.json"
    preflight = build_publication_preflight()
    preflight["warnings"][0]["evidence"] = {}
    path.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n")

    result = verify_publication_preflight(path)

    assert result["accepted"] is False
    assert result["summary"]["warning_evidence_items"] == 0
    assert result["summary"]["failure_count"] == 2
    assert result["failures"] == [
        "Publication preflight is not in sync.",
        "Publication preflight warning records must include evidence.",
    ]


def test_publication_preflight_verify_rejects_stale_warning_evidence(
    tmp_path: Path,
) -> None:
    path = tmp_path / "publication_preflight.json"
    preflight = build_publication_preflight()
    preflight["warnings"][0]["evidence"]["publication_task_count"] = 0
    path.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n")

    result = verify_publication_preflight(path)

    assert result["accepted"] is False
    assert result["summary"]["warning_evidence_items"] == 1
    assert result["summary"]["failure_count"] == 2
    assert result["failures"] == [
        "Publication preflight is not in sync.",
        "Publication preflight warning records are inconsistent with release "
        "audit.",
    ]


def test_publication_preflight_verify_rejects_reviewer_summary_drift(
    tmp_path: Path,
) -> None:
    path = tmp_path / "publication_preflight.json"
    preflight = build_publication_preflight()
    preflight["external_review"]["reviewer_summary_synced"] = False
    path.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n")

    result = verify_publication_preflight(path)

    assert result["accepted"] is False
    assert result["summary"]["reviewer_summary_synced"] is False
    assert result["summary"]["failure_count"] == 2
    assert result["failures"] == [
        "Publication preflight is not in sync.",
        "Publication preflight external review reviewer summary must be "
        "synchronized.",
    ]
