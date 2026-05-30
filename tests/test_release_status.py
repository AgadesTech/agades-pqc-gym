from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.release_status import (
    RELEASE_STATUS_VERIFICATION_SCHEMA,
    build_release_status,
    summarize_release_status_family_support,
    summarize_release_status_public_private_boundary,
    summarize_release_status_source_catalog_scope,
    verify_release_status,
    write_release_status,
)

EXPECTED_FAMILY_SUPPORT = {
    "benchmark_count": 78,
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
    "per_family_future_reviewed_adapter_source_counts": {
        "CODE_BASED": 3,
        "HASH_BASED": 1,
        "IMPLEMENTATION_SECURITY": 8,
        "ISOGENY_HISTORICAL": 0,
        "LWE": 2,
        "MLWE": 2,
        "MULTIVARIATE": 1,
        "NTRU": 2,
        "SIS": 2,
    },
    "plugin_count": 6,
    "plugins": [
        "code_based",
        "hash_based",
        "implementation_security",
        "isogeny_historical",
        "lattice",
        "multivariate",
    ],
    "public_example_count": 79,
    "unique_future_reviewed_adapter_source_count": 15,
    "cross_family_review_source_count": 3,
    "review_required_before_claims": True,
    "support_level_counts": {
        "implemented": 2,
        "schema_only": 2,
        "toy_evaluator": 5,
    },
}
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
EXPECTED_PRIME_HUB_WARNING_RECORD = {
    "artifact": "prime_intellect/verifiers_environment",
    "detail": (
        "Prime package is locally packaged but not published to the Prime "
        "Environments Hub without credentials and release review."
    ),
    "evidence": EXPECTED_PRIME_HUB_WARNING_EVIDENCE,
    "id": "prime-hub-publication",
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


def test_release_status_family_support_publication_summary_tracks_gates() -> None:
    status = build_release_status()

    assert (
        summarize_release_status_family_support(status)
        == EXPECTED_FAMILY_SUPPORT_PUBLICATION_GATE
    )


def test_release_status_family_support_publication_summary_is_detached() -> None:
    status = build_release_status()
    summary = summarize_release_status_family_support(status)

    summary["implemented"].append("BOGUS")
    summary["families_with_future_reviewed_adapters"].append("BOGUS")
    summary["platform_support"]["platforms"].append("bogus")

    assert status["family_support"]["implemented"] == ["LWE", "MLWE"]
    assert "BOGUS" not in status["family_support"][
        "families_with_future_reviewed_adapters"
    ]


def test_release_status_public_private_boundary_summary_tracks_redaction() -> None:
    status = build_release_status()

    assert (
        summarize_release_status_public_private_boundary(status)
        == EXPECTED_PUBLIC_PRIVATE_BOUNDARY
    )


def test_release_status_source_catalog_scope_summary_tracks_platforms() -> None:
    status = build_release_status()

    assert summarize_release_status_source_catalog_scope(status) == {
        **EXPECTED_SOURCE_CATALOG_SCOPE,
        "platform_source_catalog_scope_counts_match": True,
        "platform_source_catalog_scope_surfaces": 3,
        "platform_source_catalog_scope_security_claims": 0,
    }
    assert (
        status["ecosystem"]["huggingface_collection"]["source_catalog_scope"]
        == EXPECTED_SOURCE_CATALOG_SCOPE
    )
    assert (
        status["ecosystem"]["prime_intellect"]["source_catalog_scope"]
        == EXPECTED_SOURCE_CATALOG_SCOPE
    )
    assert (
        status["ecosystem"]["nvidia"]["source_catalog_scope"]
        == EXPECTED_SOURCE_CATALOG_SCOPE
    )


def test_release_status_summarizes_current_public_evidence(tmp_path: Path) -> None:
    out = tmp_path / "release_status.json"

    status = write_release_status(out)

    assert status == build_release_status()
    assert json.loads(out.read_text()) == status
    assert status["schema_version"] == "agades.pqc.release_status.v1"
    assert status["project"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "cli": "agades-pqc",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert status["audit"] == {
        "accepted": True,
        "passed": 61,
        "failed": 0,
        "warning": 1,
        "warning_check_ids": ["prime-hub-publication"],
        "warning_records": [EXPECTED_PRIME_HUB_WARNING_RECORD],
        "total": 62,
    }
    assert status["runbook"] == {
        "artifact_count": 47,
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
        "hf_attack_plan_rows": 80,
        "hf_invalid_attack_plan_rows": 1,
        "hf_task_metadata_rows": 79,
        "hf_valid_attack_plan_rows": 79,
        "lattice_is_first_implemented_plugin": True,
        "nvidia_workloads": 27,
        "planned_family_plugin_count": 5,
        "prime_tasks": 79,
        "prime_tasks_match_hf_task_metadata_rows": True,
        "project_context_sha256": (
            "bc5cdbb52c44a248564c2f75096706aaa740886b47a13dfd468bcf7acd870e9d"
        ),
        "public_records": 59,
        "public_run_bundles": 18,
        "public_runbook_audit_checks": 7,
        "public_runbook_audit_synced": True,
        "source_brief_sha256": (
            "9d8b5652e4a9d7e554748175a6ea9d78830f2e4ca9bb2f0bfde9a82adcd3ffa3"
        ),
        "source_input_count": 2,
        "source_input_ids": ["project_context", "source_brief"],
    }
    assert status["public_benchmark"] == {
        "bundle_count": 18,
        "record_count": 59,
        "families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
        ],
    }
    assert status["publication"] == {
        "surfaces": 6,
        "review_required_surfaces": 6,
        "credentialed_surfaces": [
            "huggingface-collection",
            "huggingface-dataset",
            "huggingface-space",
            "prime-verifiers-environment",
        ],
            "surface_artifact_digests": 64,
        "surface_artifact_digest_exclusions": 3,
        "public_run_bundles": 18,
        "public_run_bundle_artifacts": 72,
        "public_run_bundle_artifact_digests": 72,
    }
    assert status["external_review"] == EXPECTED_EXTERNAL_REVIEW
    assert status["family_support"] == EXPECTED_FAMILY_SUPPORT
    assert status["public_private_boundary"] == EXPECTED_PUBLIC_PRIVATE_BOUNDARY
    assert status["ecosystem"] == {
        "huggingface_dataset": {
            "attack_plan_count": 80,
            "valid_attack_plan_count": 79,
            "invalid_attack_plan_count": 1,
            "task_metadata_count": 79,
            "prime_task_eligible_count": 79,
            "invalid_attack_plan_ids": ["invalid_module_hypothesis_on_lwe_v1"],
            "verifier_output_count": 80,
            "public_run_bundles": 18,
        },
        "huggingface_space": {
            "dataset_attack_plan_count": 80,
            "dataset_valid_attack_plan_count": 79,
            "dataset_invalid_attack_plan_count": 1,
            "example_count": 79,
            "excluded_attack_plan_ids": ["invalid_module_hypothesis_on_lwe_v1"],
            "family_count": 9,
            "labels_match_valid_dataset_rows": True,
        },
        "huggingface_collection": {
            "contains_private_traces": False,
            "credentialed_entries": [
                "benchmark-card",
                "huggingface-dataset",
                "huggingface-space",
            ],
            "entry_count": 7,
            "external_publication_requires_review": True,
            "public_push_requires_review": True,
            "review_required_entries": 7,
            "security_claim": False,
            "suggested_slug": "agades/pqc-gym",
            "suggested_title": "Agades PQC Gym",
            "family_support": EXPECTED_FAMILY_SUPPORT,
            "source_catalog_scope": EXPECTED_SOURCE_CATALOG_SCOPE,
        },
        "prime_intellect": {
            "task_count": 79,
            "family_count": 9,
            "handoff_local_package_ready": True,
            "handoff_artifact_count": 12,
            "prime_hub_publication_performed": False,
            "requires_credentials": True,
            "review_required_before_publish": True,
            "family_support": EXPECTED_FAMILY_SUPPORT,
            "source_catalog_scope": EXPECTED_SOURCE_CATALOG_SCOPE,
        },
        "nvidia": {
            "all_current_workloads_cpu": True,
            "cpu_workload_count": 26,
            "current_gpu_required_workload_count": 0,
            "current_workload_count": 26,
            "gpu_future_workload_count": 1,
            "gpu_status": "future_acceleration_surface",
            "no_current_workload_requires_gpu": True,
            "public_run_bundle_count": 18,
            "reserved_future_gpu_required_workload_count": 1,
            "reserved_future_workload_count": 1,
            "workload_count": 27,
            "handoff_artifact_count": 16,
            "handoff_external_submission_requires_review": True,
            "nvidia_submission_performed": False,
            "gpu_execution_performed": False,
            "family_support": EXPECTED_FAMILY_SUPPORT,
            "source_catalog_scope": EXPECTED_SOURCE_CATALOG_SCOPE,
        },
        "source_catalog": {
            "current_public_surfaces": [
                "agades-benchmark-source-contracts",
                "agades-family-plugin-manifest",
                "agades-family-registry-manifest",
                "agades-family-support-matrix",
                "agades-hf-collection",
                "agades-hf-dataset",
                "agades-hf-space",
                "agades-lattice-estimator-baseline-contracts",
                "agades-nvidia-accelerator",
                "agades-nvidia-publication-handoff",
                "agades-prime-environment",
                "agades-prime-publication-handoff",
                "agades-public-run-export",
                "agades-publication-manifest",
                "prime-verifiers",
            ],
            "future_reviewed_adapters": [
                "ctgrind",
                "dudect",
                "facebook-lwe-benchmarking",
                "facebook-tapas",
                "hf-post-quantum-crypto-en",
                "hf-post-quantum-crypto-fr",
                "hf-pqc-ssl-scans",
                "hf-sc2026-side-channel",
                "liboqs",
                "nist-acvp",
                "nist-additional-signatures-round3",
                "nist-bike-round4-status",
                "nist-classic-mceliece-round4-status",
                "nist-hqc-selection",
                "pq-code-package",
                "pqclean",
                "pqm4",
                "prime-rl",
                "timecop-supercop",
            ],
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
            "platforms": [
                "ebacs",
                "github",
                "hugging_face",
                "nist",
                "nvidia",
                "prime_intellect",
            ],
            "source_count": 41,
            "source_map_only": [
                "nvidia-inception",
                "prime-autonanogpt-speedrun",
                "prime-autonomous-speedrunning-experiments",
                "prime-quickstart",
            ],
        },
        "release_plans": {
            "plans": [
                "docs/HUGGINGFACE_RELEASE_PLAN.md",
                "docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md",
                "docs/PRIME_INTELLECT_RELEASE_PLAN.md",
            ],
            "prime_ecosystem_anchors": [
                "prime-autonanogpt-speedrun",
                "prime-autonomous-speedrunning-experiments",
                "prime-quickstart",
            ],
            "prime_ecosystem_anchor_plan_coverage": {
                "docs/HUGGINGFACE_RELEASE_PLAN.md": [
                    "prime-autonanogpt-speedrun",
                    "prime-autonomous-speedrunning-experiments",
                    "prime-quickstart",
                ],
                "docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md": [
                    "prime-autonanogpt-speedrun",
                    "prime-autonomous-speedrunning-experiments",
                    "prime-quickstart",
                ],
                "docs/PRIME_INTELLECT_RELEASE_PLAN.md": [
                    "prime-autonanogpt-speedrun",
                    "prime-autonomous-speedrunning-experiments",
                    "prime-quickstart",
                ],
            },
        },
    }
    assert status["safety"] == {
        "arbitrary_code_execution": False,
        "contains_private_traces": False,
        "live_targeting": False,
        "publishes_private_candidates": False,
        "security_claim": False,
        "external_publication_requires_review": True,
    }
    assert (
        "uv run agades-pqc release-status --out docs/release_status.json"
        in status["release_gates"]
    )
    assert (
        "uv run agades-pqc release-status-verify --status docs/release_status.json"
        in status["release_gates"]
    )
    assert (
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json"
    ) in status["release_gates"]


def test_committed_release_status_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "release_status.json"
    committed = Path("docs/release_status.json")

    write_release_status(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_release_status_cli_writes_status(tmp_path: Path) -> None:
    out = tmp_path / "release_status.json"

    result = CliRunner().invoke(app, ["release-status", "--out", str(out)])

    assert result.exit_code == 0
    assert f"release_status={out}" in result.output
    assert json.loads(out.read_text())["schema_version"] == (
        "agades.pqc.release_status.v1"
    )


def test_release_status_verify_accepts_committed_status() -> None:
    result = verify_release_status(Path("docs/release_status.json"))

    assert result == {
        "schema_version": RELEASE_STATUS_VERIFICATION_SCHEMA,
        "status_path": "docs/release_status.json",
        "accepted": True,
        "summary": {
            "audit_accepted": True,
            "audit_failed": 0,
            "audit_passed": 61,
            "audit_total": 62,
            "audit_warning": 1,
            "audit_warning_evidence_items": 1,
            "audit_warning_records": 1,
            "current_public_surfaces": 15,
            "family_count": 9,
            "families_with_future_reviewed_adapters": 8,
            "future_reviewed_adapters": 19,
            "future_reviewed_adapter_sources_by_family": 21,
            "reviewer_summary_synced": True,
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
            "hf_valid_attack_plan_rows": 79,
            "platform_family_support_family_counts_match": True,
            "platform_family_support_surfaces": 3,
            "platform_source_catalog_scope_counts_match": True,
            "platform_source_catalog_scope_security_claims": 0,
            "platform_source_catalog_scope_surfaces": 3,
            "platforms_with_family_claim_review_gate": 3,
            "prime_tasks": 79,
            "public_run_bundles": 18,
            "raw_mapping_redaction_covered": True,
            "report_redaction_records": 2,
            "non_lattice_toy_evaluator_count": 41,
            "non_lattice_toy_operator_security_claims": 0,
            "non_lattice_toy_operator_variant_count": 41,
            "source_count": 41,
            "source_map_only": 4,
            "typed_trace_redaction_covered": True,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_release_status_verify_rejects_stale_source_count(tmp_path: Path) -> None:
    status_path = tmp_path / "release_status.json"
    status = build_release_status()
    status["ecosystem"]["source_catalog"]["source_count"] = 28
    status_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")

    result = verify_release_status(status_path)

    assert result["accepted"] is False
    assert result["summary"]["source_count"] == 28
    assert result["summary"]["failure_count"] == 4
    assert result["failures"] == [
        (
            "release status: ecosystem.huggingface_collection."
            "source_catalog_scope.source_count must match "
            "ecosystem.source_catalog.source_count."
        ),
        (
            "release status: ecosystem.prime_intellect."
            "source_catalog_scope.source_count must match "
            "ecosystem.source_catalog.source_count."
        ),
        (
            "release status: ecosystem.nvidia.source_catalog_scope.source_count "
            "must match ecosystem.source_catalog.source_count."
        ),
        "release status is not synchronized with the generated status.",
    ]


def test_release_status_verify_rejects_family_support_claim_gate_drift(
    tmp_path: Path,
) -> None:
    status_path = tmp_path / "release_status.json"
    status = build_release_status()
    status["family_support"]["review_required_before_claims"] = False
    status_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")

    result = verify_release_status(status_path)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 2
    assert result["failures"] == [
        "release status: family_support.review_required_before_claims must be true.",
        "release status is not synchronized with the generated status.",
    ]


def test_release_status_verify_rejects_platform_family_support_claim_gate_drift(
    tmp_path: Path,
) -> None:
    status_path = tmp_path / "release_status.json"
    status = build_release_status()
    status["ecosystem"]["nvidia"]["family_support"][
        "review_required_before_claims"
    ] = False
    status_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")

    result = verify_release_status(status_path)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 2
    assert result["summary"]["platforms_with_family_claim_review_gate"] == 2
    assert result["failures"] == [
        (
            "release status: ecosystem.nvidia.family_support."
            "review_required_before_claims must be true."
        ),
        "release status is not synchronized with the generated status.",
    ]


def test_release_status_verify_rejects_platform_source_scope_claim_drift(
    tmp_path: Path,
) -> None:
    status_path = tmp_path / "release_status.json"
    status = build_release_status()
    status["ecosystem"]["nvidia"]["source_catalog_scope"][
        "non_lattice_toy_operator_security_claims"
    ] = 1
    status_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")

    result = verify_release_status(status_path)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 2
    assert result["summary"]["platform_source_catalog_scope_security_claims"] == 1
    assert result["failures"] == [
        (
            "release status: ecosystem.nvidia.source_catalog_scope."
            "non_lattice_toy_operator_security_claims must be zero."
        ),
        "release status is not synchronized with the generated status.",
    ]


def test_release_status_verify_rejects_redaction_boundary_drift(
    tmp_path: Path,
) -> None:
    status_path = tmp_path / "release_status.json"
    status = build_release_status()
    status["public_private_boundary"]["report_generator_redaction"][
        "raw_mapping_redaction_covered"
    ] = False
    status_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")

    result = verify_release_status(status_path)

    assert result["accepted"] is False
    assert result["summary"]["raw_mapping_redaction_covered"] is False
    assert result["summary"]["failure_count"] == 2
    assert result["failures"] == [
        "release status: raw trace mapping redaction boundary must be covered.",
        "release status is not synchronized with the generated status.",
    ]


def test_release_status_verify_rejects_warning_evidence_drift(
    tmp_path: Path,
) -> None:
    status_path = tmp_path / "release_status.json"
    status = build_release_status()
    status["audit"]["warning_records"][0]["evidence"] = {}
    status_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")

    result = verify_release_status(status_path)

    assert result["accepted"] is False
    assert result["summary"]["audit_warning_evidence_items"] == 0
    assert result["summary"]["failure_count"] == 2
    assert result["failures"] == [
        "release status: audit warning records must include evidence.",
        "release status is not synchronized with the generated status.",
    ]


def test_release_status_verify_rejects_reviewer_summary_drift(
    tmp_path: Path,
) -> None:
    status_path = tmp_path / "release_status.json"
    status = build_release_status()
    status["external_review"]["reviewer_summary_synced"] = False
    status_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")

    result = verify_release_status(status_path)

    assert result["accepted"] is False
    assert result["summary"]["reviewer_summary_synced"] is False
    assert result["summary"]["failure_count"] == 2
    assert result["failures"] == [
        "release status: external review reviewer summary must be synchronized.",
        "release status is not synchronized with the generated status.",
    ]


def test_release_status_verify_rejects_runbook_import_evidence_drift(
    tmp_path: Path,
) -> None:
    status_path = tmp_path / "release_status.json"
    status = build_release_status()
    status["runbook"]["core_symbol_import_count"] = 9
    status["runbook"]["family_plugin_manifest_digests_match"] = False
    status["runbook"]["family_plugin_module_digest_count"] = 17
    status["runbook"]["family_plugin_module_import_count"] = 17
    status["runbook"]["family_registry_plugin_manifest_synced"] = False
    status["runbook"]["family_registry_plugin_manifest_module_digest_count"] = 17
    status["runbook"][
        "family_registry_runtime_adapter_entries_match_plugin_manifest"
    ] = False
    status_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")

    result = verify_release_status(status_path)

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
        "release status: runbook core import evidence is incomplete.",
        "release status: runbook and family plugin manifest digests must match.",
        "release status: runbook family plugin digest evidence is incomplete.",
        "release status: runbook family plugin import evidence is incomplete.",
        "release status: family registry and plugin manifest must be synchronized.",
        "release status: family registry plugin manifest digest evidence "
        "is incomplete.",
        "release status: family registry runtime adapters must match plugin manifest.",
        "release status is not synchronized with the generated status.",
    ]


def test_release_status_verify_cli_accepts_committed_status() -> None:
    result = CliRunner().invoke(
        app,
        ["release-status-verify", "--status", "docs/release_status.json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == RELEASE_STATUS_VERIFICATION_SCHEMA
    assert payload["accepted"] is True
