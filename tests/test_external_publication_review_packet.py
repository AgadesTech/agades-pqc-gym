from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.external_publication_review_packet import (
    EXTERNAL_PUBLICATION_REVIEW_PACKET_VERIFICATION_SCHEMA,
    build_external_publication_review_packet,
    verify_external_publication_review_packet,
    write_external_publication_review_packet,
)

EXPECTED_INPUTS = {
    "huggingface_collection_manifest": "hf/collection_manifest.json",
    "huggingface_publication_handoff": (
        "docs/huggingface_publication_handoff.json"
    ),
    "huggingface_space_manifest": "hf/space_manifest.json",
    "nvidia_accelerator_manifest": "nvidia/accelerator_manifest.json",
    "nvidia_publication_handoff": "docs/nvidia_publication_handoff.json",
    "prime_environment_manifest": (
        "prime_intellect/verifiers_environment/prime_manifest.json"
    ),
    "prime_publication_handoff": "docs/prime_publication_handoff.json",
    "publication_manifest": "docs/publication_manifest.json",
    "publication_preflight": "public/publication_preflight.json",
    "release_status": "docs/release_status.json",
}
EXPECTED_PLATFORM_SUPPORT = {
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
EXPECTED_PUBLICATION_DRY_RUN_PLAN = [
    {
        "artifact_count": 7,
        "command_templates": [],
        "contains_credentials": False,
        "external_publication_performed": False,
        "external_url_recorded": False,
        "first_publication_target": "private_or_draft_review_surface",
        "id": "huggingface-collection",
        "manual_review_action": (
            "Create or update the Hugging Face Collection from "
            "hf/collection_manifest.json only after dataset and Space private "
            "review pass."
        ),
        "platform": "hugging_face",
        "review_required_before_publish": True,
        "source_manifest": "hf/collection_manifest.json",
    },
    {
        "artifact_count": 6,
        "command_templates": [
            (
                "hf repos create <owner>/pqc-gym-toy --type=dataset --private "
                "--exist-ok"
            ),
            (
                "hf upload <owner>/pqc-gym-toy hf/dataset . --repo-type=dataset "
                '--commit-message "Sync Agades PQC Gym Dataset"'
            ),
        ],
        "contains_credentials": False,
        "external_publication_performed": False,
        "external_url_recorded": False,
        "first_publication_target": "private_or_draft_review_surface",
        "id": "huggingface-dataset",
        "manual_review_action": None,
        "platform": "hugging_face",
        "review_required_before_publish": True,
        "source_manifest": "hf/dataset/dataset_info.json",
    },
    {
        "artifact_count": 4,
        "command_templates": [
            (
                "hf repos create AgadesTech/agades-pqc-gym-agent-env "
                "--type=space --space-sdk gradio --private --exist-ok"
            ),
            (
                "hf upload AgadesTech/agades-pqc-gym-agent-env hf "
                ". --repo-type=space --commit-message "
                '"Sync Agades PQC Gym Agent Environment"'
            ),
        ],
        "contains_credentials": False,
        "external_publication_performed": False,
        "external_url_recorded": False,
        "first_publication_target": "private_or_draft_review_surface",
        "id": "huggingface-space",
        "manual_review_action": None,
        "platform": "hugging_face",
        "review_required_before_publish": True,
        "source_manifest": "hf/space_manifest.json",
    },
    {
        "artifact_count": 11,
        "command_templates": [
            (
                "prime env push --path prime_intellect/verifiers_environment "
                "--visibility PRIVATE"
            )
        ],
        "contains_credentials": False,
        "external_publication_performed": False,
        "external_url_recorded": False,
        "first_publication_target": "private_or_draft_review_surface",
        "id": "prime-verifiers-environment",
        "manual_review_action": None,
        "platform": "prime_intellect",
        "review_required_before_publish": True,
        "source_manifest": (
            "prime_intellect/verifiers_environment/prime_manifest.json"
        ),
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
EXPECTED_REVIEWER_SUMMARY = {
    "blockers": 2,
    "claims_external_publication": False,
    "contains_credentials": False,
    "contains_private_traces": False,
    "credential_review_queue_items": 4,
    "credentialed_surface_count": 4,
    "family_count": 9,
    "family_readiness_lattice_estimator_families": 2,
    "family_readiness_non_lattice_lattice_estimator_families": 0,
    "implemented_family_count": 2,
    "non_lattice_toy_operator_security_claims": 0,
    "platform_count": 4,
    "platform_review_matrix_credentialed_surfaces": 4,
    "platform_review_matrix_review_required_surfaces": 6,
    "platform_review_matrix_surfaces": 6,
    "platforms_with_family_claim_review_gate": 3,
    "publication_dry_run_commands": 5,
    "publication_dry_run_entries": 4,
    "publication_dry_run_private_first": True,
    "ready_for_external_publication": False,
    "review_required_surface_count": 6,
    "schema_only_family_count": 2,
    "security_claim": False,
    "surface_count": 6,
    "toy_evaluator_family_count": 5,
    "warning_evidence_items": 1,
    "warnings": 1,
}


def test_external_publication_review_packet_records_cross_surface_boundaries(
    tmp_path: Path,
) -> None:
    out = tmp_path / "external_publication_review_packet.json"

    packet = write_external_publication_review_packet(out)

    assert packet == build_external_publication_review_packet()
    assert json.loads(out.read_text(encoding="utf-8")) == packet
    assert packet["schema_version"] == (
        "agades.pqc.external_publication_review_packet.v1"
    )
    assert packet["project"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "cli": "agades-pqc",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert packet["inputs"] == EXPECTED_INPUTS
    assert sorted(packet["input_sha256"]) == sorted(EXPECTED_INPUTS.values())
    assert all(len(value) == 64 for value in packet["input_sha256"].values())
    assert packet["readiness"] == {
        "local_artifacts_ready": True,
        "ready_for_external_publication": False,
        "external_release_review_approved": False,
        "credentials_reviewed": False,
        "blocker_ids": [
            "credential_review_not_approved",
            "external_release_review_not_approved",
        ],
        "warning_ids": ["prime-hub-publication"],
        "warning_evidence": {
            "prime-hub-publication": EXPECTED_PRIME_HUB_WARNING_EVIDENCE
        },
        "credentialed_surface_count": 4,
        "review_required_surface_count": 6,
    }
    assert [entry["id"] for entry in packet["surface_review_queue"]] == [
        "github-repository",
        "huggingface-collection",
        "huggingface-dataset",
        "huggingface-space",
        "nvidia-accelerator-story",
        "prime-verifiers-environment",
    ]
    assert packet["credential_review_queue"] == EXPECTED_CREDENTIAL_REVIEW_QUEUE
    assert packet["publication_dry_run_plan"] == EXPECTED_PUBLICATION_DRY_RUN_PLAN
    assert packet["platform_review_matrix"] == EXPECTED_PLATFORM_REVIEW_MATRIX
    assert packet["reviewer_summary"] == EXPECTED_REVIEWER_SUMMARY
    family_readiness = packet["family_readiness_matrix"]
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
    assert family_readiness["MLWE"]["support_level"] == "implemented"
    assert family_readiness["MLWE"]["lattice_estimator_enabled"] is True
    assert family_readiness["SIS"]["support_level"] == "schema_only"
    assert family_readiness["SIS"]["default_estimator"] is None
    assert family_readiness["SIS"]["lattice_estimator_enabled"] is False
    assert family_readiness["IMPLEMENTATION_SECURITY"] == {
        "benchmark_count": 21,
        "cross_family_review_source_count": 3,
        "default_estimator": "toy-implementation-security-estimator",
        "evaluator_status": "implemented_toy",
        "future_reviewed_adapter_source_count": 8,
        "lattice_estimator_enabled": False,
        "operator_count": 3,
        "plugin": "implementation_security",
        "public_example_count": 20,
        "reproduction_status": (
            "toy_kat_acvp_timing_and_benchmark_verifiers_available_for_public_"
            "json_only_fixtures"
        ),
        "review_required_before_claims": True,
        "support_level": "toy_evaluator",
    }
    assert packet["ecosystem_focus"] == {
        "hugging_face": {
            "collection_entries": 7,
            "dataset_valid_attack_plan_rows": 79,
            "space_examples": 79,
        },
        "prime_intellect": {
            "environment_task_count": 79,
            "family_count": 9,
            "prime_hub_publication_performed": False,
            "source_anchors": [
                "prime-autonanogpt-speedrun",
                "prime-autonomous-speedrunning-experiments",
                "prime-quickstart",
            ],
        },
        "nvidia": {
            "current_gpu_required_workload_count": 0,
            "gpu_future_workload_count": 1,
            "workload_count": 27,
        },
        "family_support": {
            "family_count": 9,
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
            "implemented": ["LWE", "MLWE"],
            "review_required_before_claims": True,
            "schema_only": ["NTRU", "SIS"],
            "toy_evaluators": [
                "CODE_BASED",
                "HASH_BASED",
                "IMPLEMENTATION_SECURITY",
                "ISOGENY_HISTORICAL",
                "MULTIVARIATE",
            ],
            "unique_future_reviewed_adapter_source_count": 15,
            "platform_support": EXPECTED_PLATFORM_SUPPORT,
        },
        "source_catalog_scope": EXPECTED_SOURCE_CATALOG_PUBLICATION_SCOPE,
        "public_private_boundary": EXPECTED_PUBLIC_PRIVATE_BOUNDARY,
        "runbook_architecture": EXPECTED_RUNBOOK_ARCHITECTURE,
    }
    assert packet["safety"] == {
        "arbitrary_code_execution": False,
        "claims_external_publication": False,
        "contains_credentials": False,
        "contains_private_traces": False,
        "live_targeting": False,
        "publishes_private_candidates": False,
        "security_claim": False,
    }
    assert packet["release_gates"] == [
        (
            "uv run agades-pqc external-publication-review-packet --out "
            "docs/external_publication_review_packet.json"
        ),
        (
            "uv run agades-pqc external-publication-review-packet-verify "
            "--packet docs/external_publication_review_packet.json"
        ),
        (
            "uv run agades-pqc publication-preflight-verify --preflight "
            "public/publication_preflight.json"
        ),
        (
            "uv run agades-pqc ecosystem-smoke-verify --report "
            "reports/ecosystem_smoke.json"
        ),
        (
            "uv run agades-pqc hf-publication-handoff-verify --handoff "
            "docs/huggingface_publication_handoff.json"
        ),
        (
            "uv run agades-pqc prime-publication-handoff-verify --handoff "
            "docs/prime_publication_handoff.json"
        ),
        (
            "uv run agades-pqc nvidia-publication-handoff-verify --handoff "
            "docs/nvidia_publication_handoff.json"
        ),
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]
    encoded = json.dumps(packet, sort_keys=True)
    assert "private/traces" not in encoded
    assert "HF_TOKEN" not in encoded
    assert "PRIME_API_KEY" not in encoded
    assert "NVIDIA_API_KEY" not in encoded

    verification = verify_external_publication_review_packet(out)
    assert verification == {
        "schema_version": EXTERNAL_PUBLICATION_REVIEW_PACKET_VERIFICATION_SCHEMA,
        "packet_path": out.as_posix(),
        "accepted": True,
        "summary": {
            "blockers": 2,
            "credential_material_included": False,
            "credential_review_queue_complete": True,
            "credential_review_queue_items": 4,
            "credentialed_surface_count": 4,
            "families_with_future_reviewed_adapters": 8,
            "failure_count": 0,
            "family_count": 9,
            "family_readiness_family_count": 9,
            "family_readiness_lattice_estimator_families": 2,
            "family_readiness_non_lattice_lattice_estimator_families": 0,
            "family_readiness_review_required_families": 9,
            "family_readiness_schema_only_default_estimators": 0,
            "reviewer_summary_synced": True,
            "future_reviewed_adapter_sources_by_family": 21,
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
            "publication_dry_run_commands": 5,
            "publication_dry_run_contains_credentials": False,
            "publication_dry_run_entries": 4,
            "publication_dry_run_external_publication_performed": False,
            "publication_dry_run_manual_entries": 1,
            "publication_dry_run_private_first": True,
            "raw_mapping_redaction_covered": True,
            "ready_for_external_publication": False,
            "report_redaction_records": 2,
            "review_required_before_claims": True,
            "review_required_surface_count": 6,
            "surface_count": 6,
            "typed_trace_redaction_covered": True,
            "warnings": 1,
            "warning_evidence_items": 1,
        },
        "failures": [],
    }


def test_committed_external_publication_review_packet_is_in_sync(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "external_publication_review_packet.json"
    committed = Path("docs/external_publication_review_packet.json")

    write_external_publication_review_packet(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_external_publication_review_packet_verify_accepts_committed_packet() -> None:
    result = verify_external_publication_review_packet(
        Path("docs/external_publication_review_packet.json")
    )

    assert result["accepted"] is True
    assert result["summary"]["ready_for_external_publication"] is False
    assert result["summary"]["blockers"] == 2
    assert result["failures"] == []


def test_external_publication_review_packet_rejects_publication_claim(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    packet["readiness"]["ready_for_external_publication"] = True
    packet["safety"]["claims_external_publication"] = True
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert "External publication review packet is not in sync." in result[
        "failures"
    ]
    assert "External publication review packet must not claim publication." in result[
        "failures"
    ]
    assert (
        "External publication review packet must remain blocked by default."
        in result["failures"]
    )


def test_external_publication_review_packet_rejects_family_support_claim_gate_drift(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    packet["ecosystem_focus"]["family_support"][
        "review_required_before_claims"
    ] = False
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert "External publication review packet is not in sync." in result[
        "failures"
    ]
    assert (
        "External publication review packet must keep family-support review gate."
        in result["failures"]
    )


def test_external_publication_review_packet_rejects_platform_family_support_drift(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    packet["ecosystem_focus"]["family_support"]["platform_support"][
        "missing_claim_review_gate"
    ] = ["prime_intellect"]
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert result["summary"]["platforms_with_family_claim_review_gate"] == 3
    assert "External publication review packet is not in sync." in result[
        "failures"
    ]
    assert (
        "External publication review packet platform family-support gates "
        "are incomplete."
    ) in result["failures"]


def test_external_publication_review_packet_rejects_runbook_architecture_drift(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    packet["ecosystem_focus"]["runbook_architecture"][
        "core_symbol_import_count"
    ] = 9
    packet["ecosystem_focus"]["runbook_architecture"][
        "family_plugin_manifest_digests_match"
    ] = False
    packet["ecosystem_focus"]["runbook_architecture"][
        "family_plugin_module_digest_count"
    ] = 17
    packet["ecosystem_focus"]["runbook_architecture"][
        "family_plugin_module_import_count"
    ] = 17
    packet["ecosystem_focus"]["runbook_architecture"][
        "family_registry_plugin_manifest_synced"
    ] = False
    packet["ecosystem_focus"]["runbook_architecture"][
        "family_registry_plugin_manifest_module_digest_count"
    ] = 17
    packet["ecosystem_focus"]["runbook_architecture"][
        "family_registry_runtime_adapter_entries_match_plugin_manifest"
    ] = False
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

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
    assert "External publication review packet is not in sync." in result[
        "failures"
    ]
    assert (
        "External publication review packet runbook core import evidence is "
        "incomplete."
    ) in result["failures"]
    assert (
        "External publication review packet runbook and family plugin manifest "
        "digests must match."
    ) in result["failures"]
    assert (
        "External publication review packet runbook family plugin digest evidence "
        "is incomplete."
    ) in result["failures"]
    assert (
        "External publication review packet runbook family plugin import evidence "
        "is incomplete."
    ) in result["failures"]
    assert (
        "External publication review packet family registry and plugin manifest "
        "must be synchronized."
    ) in result["failures"]
    assert (
        "External publication review packet family registry plugin manifest digest "
        "evidence is incomplete."
    ) in result["failures"]
    assert (
        "External publication review packet family registry runtime adapters must "
        "match plugin manifest."
    ) in result["failures"]


def test_external_publication_review_packet_rejects_redaction_boundary_drift(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    packet["ecosystem_focus"]["public_private_boundary"][
        "report_generator_redaction"
    ]["raw_mapping_redaction_covered"] = False
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert result["summary"]["raw_mapping_redaction_covered"] is False
    assert "External publication review packet is not in sync." in result[
        "failures"
    ]
    assert (
        "External publication review packet raw trace mapping redaction gate "
        "is incomplete."
    ) in result["failures"]


def test_external_publication_review_packet_rejects_source_catalog_scope_drift(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    packet["ecosystem_focus"]["source_catalog_scope"][
        "non_lattice_toy_operator_security_claims"
    ] = 1
    packet["ecosystem_focus"]["source_catalog_scope"][
        "platform_source_catalog_scope_security_claims"
    ] = 1
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert result["summary"]["non_lattice_toy_operator_security_claims"] == 1
    assert result["summary"]["platform_source_catalog_scope_security_claims"] == 1
    assert "External publication review packet is not in sync." in result[
        "failures"
    ]
    assert (
        "External publication review packet source catalog scope must not "
        "contain non-lattice toy security claims."
    ) in result["failures"]
    assert (
        "External publication review packet platform source catalog scope must "
        "not contain non-lattice toy security claims."
    ) in result["failures"]


def test_external_publication_review_packet_rejects_credential_queue_drift(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    packet["credential_review_queue"] = packet["credential_review_queue"][:-1]
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert result["summary"]["credential_review_queue_complete"] is False
    assert "External publication review packet is not in sync." in result[
        "failures"
    ]
    assert (
        "External publication review packet credential queue must cover every "
        "credentialed surface."
    ) in result["failures"]


def test_external_publication_review_packet_rejects_public_dry_run_command(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    packet["publication_dry_run_plan"][-1]["command_templates"] = [
        "prime env push --path prime_intellect/verifiers_environment "
        "--visibility PUBLIC"
    ]
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert result["summary"]["publication_dry_run_private_first"] is False
    assert "External publication review packet is not in sync." in result[
        "failures"
    ]
    assert (
        "External publication review packet dry-run plan must keep private or "
        "draft first-publication commands."
    ) in result["failures"]


def test_external_publication_review_packet_rejects_wrong_dry_run_source_manifest(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    for entry in packet["publication_dry_run_plan"]:
        if entry["id"] == "huggingface-dataset":
            entry["source_manifest"] = "hf/collection_manifest.json"
            break
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert "External publication review packet is not in sync." in result[
        "failures"
    ]
    assert (
        "External publication review packet dry-run source_manifest is not one "
        "of the surface artifacts: huggingface-dataset."
    ) in result["failures"]


def test_external_publication_review_packet_rejects_platform_review_matrix_drift(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    packet["platform_review_matrix"]["prime_intellect"]["surface_count"] = 2
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert result["summary"]["platform_review_matrix_surfaces"] == 7
    assert "External publication review packet is not in sync." in result[
        "failures"
    ]
    assert (
        "External publication review packet platform review matrix is "
        "inconsistent with surface queue."
    ) in result["failures"]


def test_external_publication_review_packet_rejects_family_readiness_drift(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    packet["family_readiness_matrix"]["CODE_BASED"][
        "lattice_estimator_enabled"
    ] = True
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert (
        result["summary"]["family_readiness_non_lattice_lattice_estimator_families"]
        == 1
    )
    assert "External publication review packet is not in sync." in result[
        "failures"
    ]
    assert (
        "External publication review packet family readiness matrix is "
        "inconsistent with publication preflight."
    ) in result["failures"]


def test_external_publication_review_packet_rejects_reviewer_summary_drift(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    packet["reviewer_summary"]["publication_dry_run_private_first"] = False
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert result["summary"]["reviewer_summary_synced"] is False
    assert "External publication review packet is not in sync." in result[
        "failures"
    ]
    assert (
        "External publication review packet reviewer summary is inconsistent "
        "with packet evidence."
    ) in result["failures"]


def test_external_publication_review_packet_rejects_warning_evidence_drift(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    packet["readiness"]["warning_evidence"]["prime-hub-publication"] = {}
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert result["summary"]["warning_evidence_items"] == 0
    assert result["summary"]["failure_count"] == 3
    assert result["failures"] == [
        "External publication review packet is not in sync.",
        "External publication review packet warning evidence must cover every "
        "warning id.",
        "External publication review packet reviewer summary is inconsistent "
        "with packet evidence.",
    ]


def test_external_publication_review_packet_rejects_stale_warning_evidence(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    packet["readiness"]["warning_evidence"]["prime-hub-publication"][
        "publication_task_count"
    ] = 0
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert result["summary"]["warning_evidence_items"] == 1
    assert result["summary"]["failure_count"] == 2
    assert result["failures"] == [
        "External publication review packet is not in sync.",
        "External publication review packet warning evidence is inconsistent "
        "with publication preflight.",
    ]


def test_external_publication_review_packet_rejects_unscoped_dry_run_create(
    tmp_path: Path,
) -> None:
    packet = build_external_publication_review_packet()
    dataset_plan = next(
        entry
        for entry in packet["publication_dry_run_plan"]
        if entry["id"] == "huggingface-dataset"
    )
    dataset_plan["command_templates"][0] = (
        "hf repos create <owner>/pqc-gym-toy --type=dataset --exist-ok"
    )
    out = tmp_path / "external_publication_review_packet.json"
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    result = verify_external_publication_review_packet(out)

    assert result["accepted"] is False
    assert result["summary"]["publication_dry_run_private_first"] is False
    assert "External publication review packet is not in sync." in result[
        "failures"
    ]
    assert (
        "External publication review packet dry-run plan must keep private or "
        "draft first-publication commands."
    ) in result["failures"]


def test_external_publication_review_packet_cli_writes_and_verifies(
    tmp_path: Path,
) -> None:
    out = tmp_path / "external_publication_review_packet.json"

    write_result = CliRunner().invoke(
        app,
        ["external-publication-review-packet", "--out", str(out)],
    )
    verify_result = CliRunner().invoke(
        app,
        ["external-publication-review-packet-verify", "--packet", str(out)],
    )

    assert write_result.exit_code == 0, write_result.output
    assert f"external_publication_review_packet={out}" in write_result.output
    assert verify_result.exit_code == 0, verify_result.output
    assert '"accepted": true' in verify_result.output
