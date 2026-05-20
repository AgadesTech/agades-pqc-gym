from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.release_audit import (
    build_release_audit,
    write_release_audit,
)

EXPECTED_RUNBOOK_INPUT_DIGESTS = {
    "project_context": (
        "bc5cdbb52c44a248564c2f75096706aaa740886b47a13dfd468bcf7acd870e9d"
    ),
    "source_brief": (
        "9d8b5652e4a9d7e554748175a6ea9d78830f2e4ca9bb2f0bfde9a82adcd3ffa3"
    ),
}
EXPECTED_ECOSYSTEM_RUNBOOK_ARCHITECTURE = {
    "runbook_core_symbol_import_count": 14,
    "runbook_family_plugin_manifest_digests_match": True,
    "runbook_family_plugin_module_count": 55,
    "runbook_family_plugin_module_digest_count": 55,
    "runbook_family_plugin_module_import_count": 55,
    "runbook_family_registry_family_count_matches_plugin_manifest": True,
    "runbook_family_registry_plugin_count_matches_plugin_manifest": True,
    "runbook_family_registry_plugin_manifest_module_digest_count": 55,
    "runbook_family_registry_plugin_manifest_synced": True,
    "runbook_family_registry_runtime_adapter_entries_match_plugin_manifest": True,
}


def test_release_audit_accepts_current_public_artifacts(tmp_path: Path) -> None:
    out = tmp_path / "release_audit.json"

    audit = write_release_audit(out)

    assert audit == build_release_audit()
    assert json.loads(out.read_text()) == audit
    assert audit["schema_version"] == "agades.pqc.release_audit.v1"
    assert audit["accepted"] is True
    assert audit["summary"] == {
        "passed": 60,
        "failed": 0,
        "warning": 1,
        "total": 61,
    }

    checks = {check["id"]: check for check in audit["checks"]}
    assert checks["release-gate-closure"]["status"] == "passed"
    assert checks["release-gate-closure"]["blocking"] is True
    assert checks["release-gate-closure"]["evidence"] == {
        "checked_release_gate_artifacts": 39,
        "release_audit_gate_artifacts": 25,
        "ecosystem_smoke_gate_artifacts": 27,
        "missing_ecosystem_smoke_gate": [],
        "late_ecosystem_smoke_gate": [],
    }
    assert checks["runbook-deliverables"]["status"] == "passed"
    assert checks["runbook-deliverables"]["blocking"] is True
    assert checks["runbook-deliverables"]["evidence"] == {
        "artifact_count": 47,
        "hf_attack_plan_rows": 80,
        "hf_invalid_attack_plan_rows": 1,
        "hf_task_metadata_rows": 79,
        "hf_valid_attack_plan_rows": 79,
        "nvidia_workloads": 27,
        "prime_tasks": 79,
        "prime_tasks_match_hf_task_metadata_rows": True,
        "public_records": 59,
        "public_runbook_audit_checks": 7,
        "public_runbook_audit_synced": True,
        "public_run_bundles": 18,
        "runbook_core_symbol_import_count": 14,
        "runbook_core_symbol_count": 14,
        "runbook_family_plugin_module_count": 55,
        "runbook_family_plugin_module_digest_count": 55,
        "runbook_family_plugin_module_import_count": 55,
        "runbook_family_plugin_count": 6,
        "runbook_family_registry_family_count_matches_plugin_manifest": True,
        "runbook_family_registry_plugin_count_matches_plugin_manifest": True,
        "runbook_family_registry_plugin_manifest_module_digest_count": 55,
        "runbook_family_registry_plugin_manifest_synced": True,
        "runbook_family_registry_runtime_adapter_entries_match_plugin_manifest": True,
        "runbook_failed_milestones": 0,
        "runbook_milestone_ids": [
            "milestone-0-repo-scaffold-and-runbook",
            "milestone-1-dsl-and-validators",
            "milestone-2-evaluator-suite",
            "milestone-3-trace-logging-and-redaction",
            "milestone-4-openevolve-adapter",
            "milestone-5-report-generator",
            "milestone-6-community-release-artifacts",
            "milestone-7-collaboration-briefs",
            "milestone-8-end-to-end-smoke-run",
        ],
        "runbook_milestone_count": 9,
        "runbook_passed_milestones": 9,
        "runbook_project_context_sha256": EXPECTED_RUNBOOK_INPUT_DIGESTS[
            "project_context"
        ],
        "runbook_source_brief_sha256": EXPECTED_RUNBOOK_INPUT_DIGESTS["source_brief"],
        "runbook_source_input_count": 2,
        "runbook_source_input_ids": ["project_context", "source_brief"],
    }
    assert checks["prime-verifier-schemas"]["status"] == "passed"
    assert checks["prime-verifier-schemas"]["blocking"] is True
    assert checks["prime-verifier-schemas"]["evidence"] == {
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
        "submission_required_fields": [
            "attack_plan_id",
            "metadata",
            "operators",
            "target",
        ],
    }
    assert checks["community-release-cards"]["status"] == "passed"
    assert checks["community-release-cards"]["blocking"] is True
    assert checks["community-release-cards"]["evidence"] == {
        "cards": [
            "hf/benchmark_card.md",
            "hf/dataset/README.md",
            "hf/dataset_card.md",
            "prime_intellect/environment_card.md",
            "reports/AGADES_PQC_GYM_MVP_REPORT.md",
        ],
        "public_run_bundles": 18,
        "toy_families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
    }
    assert checks["ecosystem-release-plans"]["status"] == "passed"
    assert checks["ecosystem-release-plans"]["blocking"] is True
    assert checks["ecosystem-release-plans"]["evidence"] == {
        "plans": [
            "docs/HUGGINGFACE_RELEASE_PLAN.md",
            "docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md",
            "docs/PRIME_INTELLECT_RELEASE_PLAN.md",
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
        "prime_ecosystem_anchors": [
            "prime-autonanogpt-speedrun",
            "prime-autonomous-speedrunning-experiments",
            "prime-quickstart",
        ],
        "public_run_bundles": 18,
        "schema_artifacts": [
            "prime_intellect/schemas/attack_plan.schema.json",
            "prime_intellect/schemas/schema_manifest.json",
            "prime_intellect/schemas/task_metadata.schema.json",
            "prime_intellect/schemas/verifier_result.schema.json",
        ],
        "schema_artifact_plan_coverage": {
            "docs/HUGGINGFACE_RELEASE_PLAN.md": [
                "prime_intellect/schemas/attack_plan.schema.json",
                "prime_intellect/schemas/schema_manifest.json",
                "prime_intellect/schemas/task_metadata.schema.json",
                "prime_intellect/schemas/verifier_result.schema.json",
            ],
            "docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md": [
                "prime_intellect/schemas/attack_plan.schema.json",
                "prime_intellect/schemas/schema_manifest.json",
                "prime_intellect/schemas/task_metadata.schema.json",
                "prime_intellect/schemas/verifier_result.schema.json",
            ],
            "docs/PRIME_INTELLECT_RELEASE_PLAN.md": [
                "prime_intellect/schemas/attack_plan.schema.json",
                "prime_intellect/schemas/schema_manifest.json",
                "prime_intellect/schemas/task_metadata.schema.json",
                "prime_intellect/schemas/verifier_result.schema.json",
            ],
        },
    }
    assert checks["schema-only-applicability-validators"]["status"] == "passed"
    assert checks["schema-only-applicability-validators"]["blocking"] is True
    assert checks["schema-only-applicability-validators"]["evidence"] == {
        "families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
        "invalid_cases": 9,
    }
    assert checks["publication-manifest-safety"]["status"] == "passed"
    assert checks["publication-manifest-safety"]["blocking"] is True
    assert checks["publication-manifest-safety"]["evidence"] == {
        "credentialed_surfaces": [
            "huggingface-collection",
            "huggingface-dataset",
            "huggingface-space",
            "prime-verifiers-environment",
        ],
        "family_count": 9,
        "platform_family_support_family_counts_match": True,
        "platform_family_support_surfaces": 3,
        "platforms_with_family_claim_review_gate": 3,
        "public_run_bundle_artifact_digests": 72,
        "public_run_bundle_artifacts": 72,
        "public_run_bundles": 18,
        "review_required_before_claims": True,
        "review_required_surfaces": 6,
        "surface_artifact_digest_exclusions": 3,
        "surface_artifact_digests": 63,
        "surfaces": 6,
    }
    assert checks["external-publication-review-packet"]["status"] == "passed"
    assert checks["external-publication-review-packet"]["blocking"] is True
    assert checks["external-publication-review-packet"]["evidence"] == {
        "blockers": 2,
        "credential_material_included": False,
        "credential_review_queue_complete": True,
        "credential_review_queue_items": 4,
        "credentialed_surface_count": 4,
        "families_with_future_reviewed_adapters": 8,
        "family_count": 9,
        "family_readiness_family_count": 9,
        "family_readiness_lattice_estimator_families": 2,
        "family_readiness_non_lattice_lattice_estimator_families": 0,
        "family_readiness_review_required_families": 9,
        "family_readiness_schema_only_default_estimators": 0,
        "reviewer_summary_synced": True,
        "future_reviewed_adapter_sources_by_family": 21,
        "platform_review_matrix_credentialed_surfaces": 4,
        "platform_review_matrix_review_required_surfaces": 6,
        "platform_review_matrix_surfaces": 6,
        "platform_family_support_family_counts_match": True,
        "platform_family_support_surfaces": 3,
        "platforms_with_family_claim_review_gate": 3,
        "publication_dry_run_commands": 5,
        "publication_dry_run_contains_credentials": False,
        "publication_dry_run_entries": 4,
        "publication_dry_run_external_publication_performed": False,
        "publication_dry_run_manual_entries": 1,
        "publication_dry_run_private_first": True,
        "ready_for_external_publication": False,
        "review_required_before_claims": True,
        "review_required_surface_count": 6,
        "surface_count": 6,
        "warnings": 1,
        "warning_evidence_items": 1,
    }
    assert checks["ecosystem-smoke-report"]["status"] == "passed"
    assert checks["ecosystem-smoke-report"]["blocking"] is True
    assert checks["ecosystem-smoke-report"]["evidence"] == {
        "checked_in_report_synced": True,
        "external_publication_ready": False,
        "families_with_future_reviewed_adapters": 8,
        "family_count": 9,
        "future_reviewed_adapter_sources_by_family": 21,
        "hf_valid_attack_plan_rows": 79,
        "local_artifacts_ready": True,
        "nvidia_current_gpu_required_workloads": 0,
        "platform_family_support_family_counts_match": True,
        "platform_family_support_surfaces": 3,
        "platform_public_private_boundary_surfaces": 3,
        "platform_report_redaction_records_match": True,
        "platforms_with_family_claim_review_gate": 3,
        "platforms_with_raw_mapping_redaction_gate": 3,
        "platforms_with_typed_trace_redaction_gate": 3,
        "prime_tasks": 79,
        "public_run_bundles": 18,
        "reviewer_summary_synced": True,
        **EXPECTED_ECOSYSTEM_RUNBOOK_ARCHITECTURE,
    }
    assert checks["public-benchmark-manifest"]["status"] == "passed"
    assert checks["public-benchmark-manifest"]["blocking"] is True
    assert checks["public-benchmark-manifest"]["evidence"] == {
        "bundle_count": 18,
        "families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
        ],
        "record_count": 59,
    }
    assert checks["public-run-export"]["status"] == "passed"
    assert checks["public-run-export"]["blocking"] is True
    assert checks["public-run-export"]["evidence"] == {
        "bundle_count": 18,
        "contains_private_traces": False,
        "run_count": 59,
        "security_claim": False,
    }
    assert checks["evolution-heldout-rescore"]["status"] == "passed"
    assert checks["evolution-heldout-rescore"]["blocking"] is True
    assert checks["evolution-heldout-rescore"]["evidence"] == {
        "archive_schema": "agades.pqc.evolution_archive.v1",
        "arbitrary_code_execution": False,
        "heldout_rescore_schema": "agades.pqc.heldout_rescore.v1",
        "requires_parent_link": True,
        "rescored_elites": 1,
    }
    assert checks["evolution-heldout-batch"]["status"] == "passed"
    assert checks["evolution-heldout-batch"]["blocking"] is True
    assert checks["evolution-heldout-batch"]["evidence"] == {
        "arbitrary_code_execution": False,
        "heldout_candidates": 1,
        "private_rebased_plan": True,
        "requires_same_family": True,
        "source_parent_link": "release-audit-candidate",
    }
    assert checks["evolution-heldout-schedule"]["status"] == "passed"
    assert checks["evolution-heldout-schedule"]["blocking"] is True
    assert checks["evolution-heldout-schedule"]["evidence"] == {
        "approval_gates": 4,
        "ready_to_run": True,
        "review_log_attached": True,
        "scheduled_candidates": 1,
        "trace_output_private": True,
    }
    assert checks["evolution-heldout-schedule-run"]["status"] == "passed"
    assert checks["evolution-heldout-schedule-run"]["blocking"] is True
    assert checks["evolution-heldout-schedule-run"]["evidence"] == {
        "arbitrary_code_execution": False,
        "external_network_access": False,
        "heldout_records": 1,
        "rescored_elites": 1,
        "review_packet_accepted": True,
        "review_packet_contains_private_scores": False,
        "review_packet_public_release_ok": False,
        "review_packet_trace_digest_present": True,
        "shell_commands_executed": False,
        "trace_output_private": True,
    }
    assert checks["evolution-heldout-cron-plan"]["status"] == "passed"
    assert checks["evolution-heldout-cron-plan"]["blocking"] is True
    assert checks["evolution-heldout-cron-plan"]["evidence"] == {
        "cron_expression": "17 */6 * * *",
        "manual_install_required": True,
        "review_log_revalidated": True,
        "schedule_trigger": "local_cron_after_review",
        "system_crontab_written": False,
        "trace_output_private": True,
    }
    assert checks["private-evolution-campaign-plan"]["status"] == "passed"
    assert checks["private-evolution-campaign-plan"]["blocking"] is True
    assert checks["private-evolution-campaign-plan"]["evidence"] == {
        "campaign_schema": "agades.pqc.private_evolution_campaign_plan.v1",
        "compatible_target_family_count": 1,
        "heldout_target_count": 1,
        "outputs_private": True,
        "private_plan": True,
        "public_release_ok": False,
        "review_log_attached": True,
        "seed_family_coverage_complete": True,
        "seed_mutation_candidate_count": 2,
        "seed_plan_count": 1,
        "shell_commands_executed": False,
        "step_count": 7,
        "verification_accepted": True,
    }
    assert checks["evolution-archive-snapshot"]["status"] == "passed"
    assert checks["evolution-archive-snapshot"]["blocking"] is True
    assert checks["evolution-archive-snapshot"]["evidence"] == {
        "archive_schema": "agades.pqc.evolution_archive.v1",
        "contains_attack_plans": False,
        "contains_trace_payloads": False,
        "digest_only_artifacts": 3,
        "private_snapshot": True,
        "public_release_ok": False,
        "retention_days": 90,
        "review_log_attached": True,
        "snapshot_schema": "agades.pqc.private_archive_snapshot.v1",
        "trace_links_complete": True,
        "writes_only_allowed_private_roots": True,
    }
    assert checks["evolution-mutation-batch"]["status"] == "passed"
    assert checks["evolution-mutation-batch"]["blocking"] is True
    assert checks["evolution-mutation-batch"]["evidence"] == {
        "arbitrary_code_execution": False,
        "candidate_count": 35,
        "generation": 1,
        "fixture_bound_skipped": 5,
        "mutated_parameters": [
            "beta",
            "block_size",
            "branching_factor",
            "degree_bound",
            "ell",
            "equations",
            "guessed_variables",
            "n",
            "p",
            "q_prime",
            "representation_count",
            "variables",
            "vector_count",
            "w",
            "walk_length",
            "zeta",
        ],
        "private_candidates": True,
        "schema_only_skipped": 1,
        "skipped_count": 6,
        "source_count": 19,
    }
    assert checks["evolution-archive-mutation-batch"]["status"] == "passed"
    assert checks["evolution-archive-mutation-batch"]["blocking"] is True
    assert checks["evolution-archive-mutation-batch"]["evidence"] == {
        "arbitrary_code_execution": False,
        "candidate_count": 6,
        "generation": 1,
        "parent_candidate_id": "release-audit-elite",
        "parent_trace_linked": True,
        "private_candidates": True,
        "source_count": 1,
    }
    assert checks["lattice-estimator-mapping-coverage"]["status"] == "passed"
    assert checks["lattice-estimator-mapping-coverage"]["blocking"] is True
    assert checks["lattice-estimator-mapping-coverage"]["evidence"] == {
        "covered_algorithm_keys": ["bdd", "bkw", "dual", "dual_hybrid", "usvp"],
        "covered_attack_types": [
            "bounded_distance_decoding",
            "bkw",
            "dual_attack",
            "dual_hybrid",
            "primal_usvp",
        ],
        "hf_rows": 5,
        "prime_tasks": 5,
        "public_examples": 5,
    }
    assert checks["lattice-estimator-pin"]["status"] == "passed"
    assert checks["lattice-estimator-pin"]["blocking"] is True
    assert checks["lattice-estimator-pin"]["evidence"] == {
        "mapping_count": 5,
        "pin_enforcement": {
            "mismatched_commit": "error",
            "missing_commit_metadata": "error",
            "runtime_required_commit": "6019056011d10d7e9c30a0d5da2d2f729fbc2eec",
        },
        "pinned_commit": "6019056011d10d7e9c30a0d5da2d2f729fbc2eec",
        "runtime_environment": {
            "ci_dependency": False,
            "missing_runtime_behavior": (
                "private_error_report_without_public_numeric_outputs"
            ),
            "private_preflight_command": (
                "uv run agades-pqc lattice-estimator-runtime-preflight "
                "--out private/reports/lattice_estimator_runtime_preflight.json "
                "--policy docs/private_run_policy.json"
            ),
            "private_preflight_verify_command": (
                "uv run agades-pqc lattice-estimator-runtime-preflight-verify "
                "--preflight private/reports/lattice_estimator_runtime_preflight.json"
            ),
            "private_baseline_sage_worker_command": (
                "uv run agades-pqc lattice-estimator-baseline-run "
                "--contracts docs/lattice_estimator_baseline_contracts.json "
                "--contracts-root . "
                "--out private/reports/lattice_estimator_baseline_run.json "
                "--policy docs/private_run_policy.json "
                "--estimator-source /path/to/lattice-estimator "
                "--sage-command sage"
            ),
            "private_baseline_sage_python_worker_command": (
                "uv run agades-pqc lattice-estimator-baseline-run "
                "--contracts docs/lattice_estimator_baseline_contracts.json "
                "--contracts-root . "
                "--out private/reports/lattice_estimator_baseline_run.json "
                "--policy docs/private_run_policy.json "
                "--estimator-source /path/to/lattice-estimator "
                "--sage-python-command '/path/to/python-with-sage-all'"
            ),
            "private_baseline_verify_command": (
                "uv run agades-pqc lattice-estimator-baseline-run-verify "
                "--report private/reports/lattice_estimator_baseline_run.json "
                "--contracts-root ."
            ),
            "private_baseline_review_packet_command": (
                "uv run agades-pqc lattice-estimator-baseline-review-packet "
                "--baseline-report private/reports/lattice_estimator_baseline_run.json "
                "--out private/reports/lattice_estimator_baseline_review_packet.json "
                "--policy docs/private_run_policy.json "
                "--contracts-root ."
            ),
            "private_baseline_review_packet_verify_command": (
                "uv run agades-pqc lattice-estimator-baseline-review-packet-verify "
                "--packet "
                "private/reports/lattice_estimator_baseline_review_packet.json "
                "--baseline-report private/reports/lattice_estimator_baseline_run.json "
                "--contracts-root ."
            ),
            "required_for_numeric_baseline": True,
            "sage_command": "sage",
            "sage_python_command_default": "sage -python",
            "sage_python_command_option": "--sage-python-command",
            "sage_python_probe": "<sage-python-command> -c 'import sage.all'",
            "sage_worker": "private_subprocess_after_checkout_preflight",
        },
        "schema_only_lattice_families": ["NTRU", "SIS"],
        "source_checkout_backend": {
            "cli_option": "--estimator-source",
            "clean_tree_probe": "git status --porcelain",
            "clean_tree_verified_before_import": True,
            "commit_probe": "git rev-parse HEAD",
            "commit_verified_before_import": True,
            "dirty_checkout": "error_before_import",
            "entrypoint_verified_before_import": True,
            "mismatched_checkout_commit": "error_before_import",
            "mismatched_origin": "error_before_import",
            "origin_probe": "git remote get-url origin",
            "origin_verified_before_import": True,
            "scope": "private_lattice_estimator_baseline_runs",
        },
        "source_checkout_import_guard": {
            "dirty_checkout_imported_estimator": False,
            "dirty_checkout_status": "error",
            "wrong_origin_imported_estimator": False,
            "wrong_origin_status": "error",
        },
    }
    assert checks["lattice-estimator-baseline-contracts"]["status"] == "passed"
    assert checks["lattice-estimator-baseline-contracts"]["blocking"] is True
    assert checks["lattice-estimator-baseline-contracts"]["evidence"] == {
        "contract_count": 5,
        "covered_algorithm_keys": ["bdd", "bkw", "dual", "dual_hybrid", "usvp"],
        "numeric_reference_outputs_committed": False,
        "pinned_commit": "6019056011d10d7e9c30a0d5da2d2f729fbc2eec",
        "security_claim": False,
    }
    assert checks["lattice-estimator-baseline-run-boundary"]["status"] == "passed"
    assert checks["lattice-estimator-baseline-run-boundary"]["blocking"] is True
    assert checks["lattice-estimator-baseline-run-boundary"]["evidence"] == {
        "all_successful_results_from_pinned_commit": True,
        "contract_count": 5,
        "lwe_only": True,
        "numeric_reference_outputs_committed": False,
        "numeric_result_count": 5,
        "ok_results": 5,
        "private_numeric_outputs": True,
        "private_report": True,
        "public_release_ok": False,
        "publishes_numeric_references": False,
        "raw_estimator_output_committed": False,
        "raw_output_digest_count": 5,
        "review_packet_accepted": True,
        "review_packet_contains_numeric_values": False,
        "review_packet_public_release_ok": False,
        "review_packet_raw_output_digest_count": 5,
        "security_claim": False,
        "standalone_verifier_accepted": True,
    }
    assert checks["lattice-estimator-checkout-preflight-boundary"]["status"] == (
        "passed"
    )
    assert checks["lattice-estimator-checkout-preflight-boundary"]["blocking"] is True
    assert checks["lattice-estimator-checkout-preflight-boundary"]["evidence"] == {
        "executes_estimator": False,
        "failure_count": 0,
        "head_matches_required_pin": True,
        "imports_upstream_python": False,
        "private_report": True,
        "publication_allowed": False,
        "ready_for_private_baseline_run": True,
        "remote_matches_upstream": True,
        "security_claim": False,
        "writes_only_allowed_private_roots": True,
    }
    assert checks["lattice-estimator-runtime-preflight-verifier"]["status"] == (
        "passed"
    )
    assert checks["lattice-estimator-runtime-preflight-verifier"]["blocking"] is True
    assert checks["lattice-estimator-runtime-preflight-verifier"]["evidence"] == {
        "accepted_closed_failure_report": True,
        "executes_estimator": False,
        "external_network_access": False,
        "failure_count": 1,
        "imports_upstream_python": False,
        "numeric_reference_outputs_committed": False,
        "private_report": True,
        "publication_allowed": False,
        "ready_for_private_lattice_estimator_import": False,
        "sage_found": False,
        "sage_python_imports_sage": False,
        "security_claim": False,
        "writes_only_allowed_private_roots": True,
    }
    assert checks["lattice-runtime-primary-boundary"]["status"] == "passed"
    assert checks["lattice-runtime-primary-boundary"]["blocking"] is True
    assert checks["lattice-runtime-primary-boundary"]["evidence"] == {
        "attack_plan_id": "lattice_lwe_modulus_switching_primary_v1",
        "estimator": "lattice-family-router",
        "hf_seed_evaluation_status": "unsupported",
        "hf_seed_reward": 0.0,
        "operator_types": ["modulus_switching"],
        "prime_seed_evaluation_status": "unsupported",
        "prime_seed_reward": 0.0,
        "source_path": (
            "examples/attack_plans/lattice_lwe_modulus_switching_primary.json"
        ),
        "space_label_present": True,
        "verifier_accepted": False,
        "verifier_evaluation_status": "unsupported",
        "verifier_time_bits": None,
        "warning_contains_catalog_boundary": True,
    }
    assert checks["prime-environment-smoke"]["status"] == "passed"
    assert checks["prime-environment-smoke"]["blocking"] is True
    assert checks["prime-environment-smoke"]["evidence"] == {
        "accepted_score": 1.0,
        "dataset_rows": 79,
        "imports_without_verifiers": True,
        "optional_dependency_boundary": True,
        "prefixed_json_score": 0.0,
        "unsupported_score": 0.0,
    }
    assert checks["prime-environment-manifest"]["status"] == "passed"
    assert checks["prime-environment-manifest"]["blocking"] is True
    assert checks["prime-environment-manifest"]["evidence"] == {
        "families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
            "NTRU",
            "SIS",
        ],
        "hub_install_command_template": (
            "prime env install <owner>/agades-pqc-verifier-env"
        ),
        "eval_config_path": "prime_intellect/evals/agades_pqc_eval.template.toml",
        "local_eval_command": (
            "cd prime_intellect/verifiers_environment && "
            "uv run vf-eval agades-pqc-verifier-env"
        ),
        "mirrored_public_examples": 79,
        "mirrors_public_examples": True,
        "task_count": 79,
    }
    assert checks["prime-eval-config"]["status"] == "passed"
    assert checks["prime-eval-config"]["blocking"] is True
    assert checks["prime-eval-config"]["evidence"] == {
        "family_count": 9,
        "num_examples": 32,
        "rollouts_per_example": 2,
        "task_count": 79,
    }
    assert checks["pedagogical-rl-method"]["status"] == "passed"
    assert checks["pedagogical-rl-method"]["blocking"] is True
    assert checks["pedagogical-rl-method"]["evidence"] == {
        "stages": 4,
        "reward_terms": 8,
        "linked_artifacts": 9,
        "teacher_student_pattern": "privileged_self_teacher_student",
        "pedagogy_reward": "R_agades(x,c,tau) * G_spike_student(tau|x)",
        "privacy_preserving": True,
    }
    assert checks["private-dataset-curation"]["status"] == "passed"
    assert checks["private-dataset-curation"]["blocking"] is True
    assert checks["private-dataset-curation"]["evidence"] == {
        "sources": 3,
        "pipeline_stages": 7,
        "required_controls": 5,
        "linked_artifacts": 3,
        "public_rows_allowed": False,
        "license_review_required": True,
    }
    assert checks["hf-space-smoke"]["status"] == "passed"
    assert checks["hf-space-smoke"]["blocking"] is True
    assert checks["hf-space-smoke"]["evidence"] == {
        "default_label": "LWE / lattice_primal_usvp_toy_v1",
        "example_count": 79,
        "imports_without_gradio": True,
        "summary_contains_not_security_claim": True,
        "uses_shared_verifier": True,
    }
    assert checks["hf-space-manifest"]["status"] == "passed"
    assert checks["hf-space-manifest"]["blocking"] is True
    assert checks["hf-space-manifest"]["evidence"] == {
        "dataset_attack_plan_count": 80,
        "dataset_invalid_attack_plan_count": 1,
        "dataset_valid_attack_plan_count": 79,
        "default_label": "LWE / lattice_primal_usvp_toy_v1",
        "example_count": 79,
        "excluded_attack_plan_ids": ["invalid_module_hypothesis_on_lwe_v1"],
        "families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
            "NTRU",
            "SIS",
        ],
        "hub_create_command_template": (
            "hf repos create AgadesTech/agades-pqc-gym-agent-env --type=space "
            "--space-sdk gradio --private --exist-ok"
        ),
        "hub_upload_command_template": (
            "hf upload AgadesTech/agades-pqc-gym-agent-env hf . --repo-type=space "
            '--commit-message "Sync Agades PQC Gym Agent Environment"'
        ),
        "labels_match_valid_dataset_rows": True,
    }
    assert checks["hf-collection-manifest"]["status"] == "passed"
    assert checks["hf-collection-manifest"]["blocking"] is True
    assert checks["hf-collection-manifest"]["evidence"] == {
        "contains_private_traces": False,
        "credentialed_entries": [
            "benchmark-card",
            "huggingface-dataset",
            "huggingface-space",
        ],
        "entries": [
            "github-repository",
            "huggingface-dataset",
            "huggingface-space",
            "benchmark-card",
            "source-map",
            "public-benchmark-v0",
            "public-run-export",
        ],
        "entry_count": 7,
        "external_publication_requires_review": True,
        "public_push_requires_review": True,
        "review_required_entries": 7,
        "security_claim": False,
        "suggested_slug": "agades/pqc-gym",
        "suggested_title": "Agades PQC Gym",
    }
    assert checks["hf-publication-handoff"]["status"] == "passed"
    assert checks["hf-publication-handoff"]["blocking"] is True
    assert checks["hf-publication-handoff"]["evidence"] == {
        "artifact_count": 17,
        "attack_plan_count": 80,
        "collection_entry_count": 7,
        "external_publication_requires_review": True,
        "public_run_bundles": 18,
        "space_example_count": 79,
        "task_metadata_rows": 79,
        "valid_attack_plan_count": 79,
    }
    assert checks["checksum-manifests"]["status"] == "passed"
    assert checks["checksum-manifests"]["blocking"] is True
    assert checks["checksum-manifests"]["evidence"] == {
        "manifests": [
            "examples/public_runs/code_based_toy_classic_mceliece_v0/MANIFEST.sha256",
            "examples/public_runs/code_based_toy_hqc_v0/MANIFEST.sha256",
            "examples/public_runs/code_based_toy_isd_v0/MANIFEST.sha256",
            "examples/public_runs/code_based_toy_mdpc_v0/MANIFEST.sha256",
            "examples/public_runs/hash_based_toy_bound_v0/MANIFEST.sha256",
            "examples/public_runs/hash_based_toy_misuse_v0/MANIFEST.sha256",
            "examples/public_runs/hash_based_toy_signature_v0/MANIFEST.sha256",
            "examples/public_runs/implementation_security_toy_benchmark_v0/MANIFEST.sha256",
            "examples/public_runs/implementation_security_toy_kat_v0/MANIFEST.sha256",
            "examples/public_runs/implementation_security_toy_timing_v0/MANIFEST.sha256",
            "examples/public_runs/isogeny_historical_toy_path_v0/MANIFEST.sha256",
            "examples/public_runs/lattice_downscaled_lwe_instance_solve_v0/MANIFEST.sha256",
            "examples/public_runs/lattice_downscaled_mlwe_instance_solve_v0/MANIFEST.sha256",
            "examples/public_runs/lattice_mlwe_downscaled_v0/MANIFEST.sha256",
            "examples/public_runs/lattice_toy_lwe_v0/MANIFEST.sha256",
            "examples/public_runs/multivariate_toy_minrank_v0/MANIFEST.sha256",
            "examples/public_runs/multivariate_toy_mq_v0/MANIFEST.sha256",
            "examples/public_runs/multivariate_toy_uov_v0/MANIFEST.sha256",
            "hf/dataset/MANIFEST.sha256",
            "hf/dataset/public_runs/code_based_toy_classic_mceliece_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/code_based_toy_hqc_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/code_based_toy_isd_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/code_based_toy_mdpc_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/hash_based_toy_bound_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/hash_based_toy_misuse_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/hash_based_toy_signature_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/implementation_security_toy_benchmark_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/implementation_security_toy_kat_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/implementation_security_toy_timing_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/isogeny_historical_toy_path_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/lattice_downscaled_lwe_instance_solve_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/lattice_downscaled_mlwe_instance_solve_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/lattice_mlwe_downscaled_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/lattice_toy_lwe_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/multivariate_toy_minrank_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/multivariate_toy_mq_v0/MANIFEST.sha256",
            "hf/dataset/public_runs/multivariate_toy_uov_v0/MANIFEST.sha256",
            "public/run_export/MANIFEST.sha256",
            ],
            "verified_entries": 189,
        }
    assert checks["github-actions-ci"]["status"] == "passed"
    assert checks["github-actions-ci"]["blocking"] is True
    assert checks["github-actions-ci"]["evidence"]["required_actions"] == [
        "actions/checkout@",
        "leanprover/lean-action@",
        "astral-sh/setup-uv@",
    ]
    assert checks["github-actions-ci"]["evidence"]["lean_gate_required_inputs"] == {
        "lake-package-directory": "formal/lean",
        "build": True,
        "test": False,
        "lint": False,
        "auto-config": False,
        "use-mathlib-cache": True,
    }
    assert checks["github-actions-ci"]["evidence"]["lean_gate_inputs"] == {
        "lake-package-directory": "formal/lean",
        "build": True,
        "test": False,
        "lint": False,
        "auto-config": False,
        "use-mathlib-cache": True,
    }
    assert checks["github-actions-ci"]["evidence"]["required_commands"] == [
        "build-package",
        "build-prime-environment",
        "check-artifact-diff",
        "check-whitespace",
        "generate-private-run-policy",
        "verify-private-run-policy",
        "generate-private-dataset-curation",
        "verify-private-dataset-curation",
        "verify-runbook-input-manifest",
        "generate-deepevolve-manifest",
        "verify-deepevolve-manifest",
        "generate-benchmark-source-contracts",
        "verify-benchmark-source-contracts",
        "generate-family-registry-manifest",
        "verify-family-registry-manifest",
        "generate-family-plugin-manifest",
        "verify-family-plugin-manifest",
        "generate-family-support",
        "verify-family-support",
        "generate-ecosystem-source-graph",
        "verify-ecosystem-source-graph",
        "generate-family-operator-catalog",
        "verify-family-operator-catalog",
        "generate-formal-lean-backend",
        "verify-formal-lean-backend",
        "generate-hf-dataset",
        "verify-hf-dataset",
        "generate-hf-space-manifest",
        "verify-hf-space-manifest",
        "generate-hf-space-smoke",
        "verify-hf-space-smoke",
        "generate-hf-collection-manifest",
        "verify-hf-collection-manifest",
        "generate-hf-publication-handoff",
        "verify-hf-publication-handoff",
        "generate-lattice-estimator-manifest",
        "verify-lattice-estimator-manifest",
        "generate-lattice-estimator-baseline-contracts",
        "verify-lattice-estimator-baseline-contracts",
        "generate-nvidia-manifest",
        "verify-nvidia-manifest",
        "generate-nvidia-manifest-safety",
        "verify-nvidia-manifest-safety",
        "generate-nvidia-publication-handoff",
        "verify-nvidia-publication-handoff",
        "generate-openevolve-config-template",
        "verify-openevolve-config-template",
        "generate-openevolve-smoke-report",
        "verify-openevolve-smoke-report",
        "generate-prime-manifest",
        "verify-prime-manifest",
        "generate-prime-environment-smoke",
        "verify-prime-environment-smoke",
        "generate-prime-eval-config",
        "verify-prime-eval-config",
        "generate-pedagogical-rl-method",
        "verify-pedagogical-rl-method",
        "generate-prime-schemas",
        "verify-prime-schemas",
        "generate-prime-publication-handoff",
        "verify-prime-publication-handoff",
        "generate-prime-speedrun-handoff",
        "verify-prime-speedrun-handoff",
        "generate-public-benchmark-manifest",
        "verify-public-benchmark",
        "generate-public-run-export",
        "verify-public-run-export",
        "generate-publication-manifest",
        "verify-publication-manifest",
        "converge-release-artifacts",
        "generate-source-catalog",
        "verify-source-catalog",
        "lint",
        "tests",
    ]
    required_commands = checks["github-actions-ci"]["evidence"]["required_commands"]
    assert "converge-release-artifacts" in required_commands
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "uv run agades-pqc release-artifacts --max-passes 6" in workflow
    assert (
        "uv run agades-pqc openevolve-config --out "
        "examples/openevolve/config.yaml" in workflow
    )
    assert (
        "uv run agades-pqc openevolve-config-verify --config "
        "examples/openevolve/config.yaml" in workflow
    )
    assert "/tmp/agades_openevolve_config.yaml" not in workflow
    assert (
        "uv run agades-pqc openevolve-smoke --out reports/openevolve_smoke.json"
        in workflow
    )
    assert (
        "uv run agades-pqc openevolve-smoke-verify --report "
        "reports/openevolve_smoke.json" in workflow
    )
    assert (
        "uv run agades-pqc formal-lean-backend --out "
        "docs/formal_lean_backend.json" in workflow
    )
    assert (
        "uv run agades-pqc formal-lean-backend-verify --backend "
        "docs/formal_lean_backend.json" in workflow
    )
    artifact_diff_line = next(
        line for line in workflow.splitlines() if "git diff --exit-code --" in line
    )
    assert "docs/external_publication_review_packet.json" in artifact_diff_line
    assert "docs/formal_lean_backend.json" in artifact_diff_line
    assert "reports/openevolve_smoke.json" in artifact_diff_line
    assert checks["openevolve-config-template"]["status"] == "passed"
    assert checks["openevolve-config-template"]["blocking"] is True
    assert checks["openevolve-config-template"]["evidence"] == {
        "archive_loop_keys": [
            "archive_mutation_command",
            "archive_snapshot_command",
            "heldout_batch_command",
            "heldout_cron_plan_command",
            "heldout_rescore_command",
            "heldout_review_log_command",
            "heldout_run_schedule_command",
            "heldout_schedule_command",
            "local_batch_command",
            "local_mutation_command",
            "next_generation_batch_command",
            "paper_card_injection_command",
            "private_campaign_plan_command",
        ],
        "checked_config_synced": True,
        "config_path": "examples/openevolve/config.yaml",
        "example_config_synced": True,
        "private_qwen_enabled": True,
        "python_candidates_executed": False,
        "security_claim": False,
        "template_keys": 30,
    }
    assert checks["openevolve-evaluator-smoke"]["status"] == "passed"
    assert checks["openevolve-evaluator-smoke"]["blocking"] is True
    assert checks["openevolve-evaluator-smoke"]["evidence"] == {
        "attack_plan_path": "examples/attack_plans/lattice_primal_usvp_toy.json",
        "checked_in_report_synced": True,
        "combined_score": -80.9096,
        "evaluation_status": "ok",
        "feature_attack_type": "primal_usvp",
        "feature_family": "LWE",
        "feature_memory_bucket": "low",
        "metric_count": 23,
        "primary_metric": "combined_score",
        "python_candidates_executed": False,
        "report_path": "reports/openevolve_smoke.json",
        "security_claim": False,
    }
    assert checks["deepevolve-paper-card-injections"]["status"] == "passed"
    assert checks["deepevolve-paper-card-injections"]["blocking"] is True
    assert checks["deepevolve-paper-card-injections"]["evidence"] == {
        "all_injections_review_required": True,
        "arbitrary_code_execution": False,
        "contains_private_traces": False,
        "injection_count": 13,
        "modifies_estimator_scores": False,
        "public_release_ok": False,
        "research_claim": False,
        "writes_attack_plans": False,
    }
    assert checks["deepevolve-research-hooks"]["status"] == "passed"
    assert checks["deepevolve-research-hooks"]["blocking"] is True
    assert checks["deepevolve-research-hooks"]["evidence"] == {
        "all_cards_note_only": True,
        "all_proposals_review_required": True,
        "arbitrary_code_execution": False,
        "card_count": 8,
        "modifies_estimator_scores": False,
        "private_qwen_bound": True,
        "proposal_count": 13,
        "research_claim": False,
        "review_required_before_implementation": True,
    }
    assert checks["multi-family-readiness"]["status"] == "passed"
    assert checks["family-registry-manifest"]["status"] == "passed"
    assert checks["family-registry-manifest"]["blocking"] is True
    assert checks["family-registry-manifest"]["evidence"] == {
        "applicability_validator_entries": 9,
        "distinct_applicability_validators": 6,
        "families": 9,
        "implemented": ["LWE", "MLWE"],
        "lattice_estimator_external_enabled": ["LWE"],
        "lattice_validator_families": ["LWE", "MLWE", "NTRU", "SIS"],
        "non_lattice_applicability_validators": 5,
        "operator_review_boundaries": {
            "CODE_BASED": {
                "catalog_operator_types": 2,
                "catalog_variant_entries": 17,
                "external_estimator_operator_types": 0,
                "runtime_operator_types": 2,
                "runtime_without_catalog_operator_types": 0,
            },
            "HASH_BASED": {
                "catalog_operator_types": 3,
                "catalog_variant_entries": 7,
                "external_estimator_operator_types": 0,
                "runtime_operator_types": 3,
                "runtime_without_catalog_operator_types": 0,
            },
            "IMPLEMENTATION_SECURITY": {
                "catalog_operator_types": 3,
                "catalog_variant_entries": 9,
                "external_estimator_operator_types": 0,
                "runtime_operator_types": 3,
                "runtime_without_catalog_operator_types": 0,
            },
            "ISOGENY_HISTORICAL": {
                "catalog_operator_types": 1,
                "catalog_variant_entries": 3,
                "external_estimator_operator_types": 0,
                "runtime_operator_types": 1,
                "runtime_without_catalog_operator_types": 0,
            },
            "LWE": {
                "catalog_operator_types": 5,
                "catalog_variant_entries": 5,
                "external_estimator_operator_types": 5,
                "runtime_operator_types": 12,
                "runtime_without_catalog_operator_types": 7,
            },
            "MLWE": {
                "catalog_operator_types": 2,
                "catalog_variant_entries": 2,
                "external_estimator_operator_types": 0,
                "runtime_operator_types": 12,
                "runtime_without_catalog_operator_types": 10,
            },
            "MULTIVARIATE": {
                "catalog_operator_types": 3,
                "catalog_variant_entries": 5,
                "external_estimator_operator_types": 0,
                "runtime_operator_types": 3,
                "runtime_without_catalog_operator_types": 0,
            },
            "NTRU": {
                "catalog_operator_types": 0,
                "catalog_variant_entries": 0,
                "external_estimator_operator_types": 0,
                "runtime_operator_types": 0,
                "runtime_without_catalog_operator_types": 0,
            },
            "SIS": {
                "catalog_operator_types": 0,
                "catalog_variant_entries": 0,
                "external_estimator_operator_types": 0,
                "runtime_operator_types": 0,
                "runtime_without_catalog_operator_types": 0,
            },
        },
        "plugin_manifest_family_count": 9,
        "plugin_manifest_implementation_module_count": 55,
        "plugin_manifest_implementation_module_digest_count": 55,
        "plugin_manifest_implementation_module_import_count": 55,
        "plugin_manifest_plugin_count": 6,
        "plugin_manifest_runtime_adapter_entries": 9,
        "plugin_manifest_synced": True,
        "plugins": 6,
        "registry_family_count_matches_plugin_manifest": True,
        "registry_plugin_count_matches_plugin_manifest": True,
        "registry_runtime_adapter_entries_match_plugin_manifest": True,
        "runtime_adapter_entries": 9,
        "schema_only": [
            "NTRU",
            "SIS",
        ],
        "toy_evaluators": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
    }
    assert checks["family-plugin-manifest"]["status"] == "passed"
    assert checks["family-plugin-manifest"]["blocking"] is True
    assert checks["family-plugin-manifest"]["evidence"] == {
        "families": 9,
        "implemented": ["LWE", "MLWE"],
        "implementation_module_digest_count": 55,
        "implementation_module_count": 55,
        "implementation_module_import_count": 55,
        "lattice_plugin_families": ["LWE", "MLWE", "NTRU", "SIS"],
        "non_lattice_plugin_count": 5,
        "plugins": 6,
        "runtime_adapter_entries": 9,
        "runbook_module_digest_count": 55,
        "runbook_module_digests_match": True,
        "schema_only": [
            "NTRU",
            "SIS",
        ],
        "toy_evaluators": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
    }
    assert checks["family-support-matrix"]["status"] == "passed"
    assert checks["family-support-matrix"]["evidence"] == {
        "benchmarks": 78,
        "cross_family_review_source_count": 3,
        "families": 9,
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
        "implemented": ["LWE", "MLWE"],
        "plugins": [
            "code_based",
            "hash_based",
            "implementation_security",
            "isogeny_historical",
            "lattice",
            "multivariate",
        ],
        "plugin_count": 6,
        "public_examples": 79,
        "review_required_before_claims": True,
        "schema_only": [
            "NTRU",
            "SIS",
        ],
        "support_level_counts": {
            "implemented": 2,
            "schema_only": 2,
            "toy_evaluator": 5,
        },
        "toy_evaluators": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
        "unique_future_reviewed_adapter_source_count": 15,
    }
    assert checks["ecosystem-source-graph"]["status"] == "passed"
    assert checks["ecosystem-source-graph"]["blocking"] is True
    assert checks["ecosystem-source-graph"]["evidence"] == {
        "benchmark_source_catalog_links": 18,
        "benchmark_source_contracts": 18,
        "family_count": 9,
        "family_cross_family_source_links": 27,
        "family_future_source_links": 21,
        "prime_source_ids": 8,
        "prime_visibility_anchor_ids": 3,
        "source_catalog_sources": 41,
        "unique_family_cross_family_source_ids": 3,
        "unique_family_future_source_ids": 15,
        "unresolved_benchmark_source_catalog_links": 0,
        "unresolved_family_source_links": 0,
    }
    assert checks["family-operator-catalog"]["status"] == "passed"
    assert checks["family-operator-catalog"]["blocking"] is True
    assert checks["family-operator-catalog"]["evidence"] == {
        "applicability_validator_count": 6,
        "families": 9,
        "families_with_operator_entries": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
        ],
        "lattice_estimator_operator_entries": 5,
        "non_lattice_lattice_estimator_operator_entries": 0,
        "operator_entries": 48,
        "schema_only_families": [
            "NTRU",
            "SIS",
        ],
        "schema_only_operator_entries": 0,
        "support_level_counts": {
            "implemented": 2,
            "schema_only": 2,
            "toy_evaluator": 5,
        },
        "toy_evaluator_families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
    }
    assert checks["multi-family-readiness"]["blocking"] is True
    assert checks["multi-family-readiness"]["evidence"]["plugins"] == [
        "code_based",
        "hash_based",
        "implementation_security",
        "isogeny_historical",
        "lattice",
        "multivariate",
    ]
    assert checks["multi-family-readiness"]["evidence"]["example_families"] == [
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
    assert checks["multi-family-readiness"]["evidence"]["benchmark_families"] == [
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
    assert checks["hf-dataset-safety"]["status"] == "passed"
    assert checks["hf-dataset-safety"]["evidence"] == {
        "attack_plan_count": 80,
        "task_metadata_rows": 79,
        "task_metadata_rows_match_attack_plans": True,
        "verifier_output_count": 80,
        "verifier_rows": 80,
    }
    assert checks["source-catalog-safety"]["status"] == "passed"
    assert checks["source-catalog-safety"]["evidence"] == {
        "current_public_surface_count": 15,
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
        "future_reviewed_adapter_count": 19,
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
        "local_artifact_source_count": 14,
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
        "platform_counts": {
            "ebacs": 1,
            "github": 14,
            "hugging_face": 8,
            "nist": 7,
            "nvidia": 3,
            "prime_intellect": 8,
        },
        "requires_gpu_source_count": 3,
        "source_count": 41,
        "source_map_only": [
            "nvidia-inception",
            "prime-autonanogpt-speedrun",
            "prime-autonomous-speedrunning-experiments",
            "prime-quickstart",
        ],
        "source_map_only_count": 4,
    }
    assert checks["benchmark-source-contracts"]["status"] == "passed"
    assert checks["benchmark-source-contracts"]["blocking"] is True
    assert checks["benchmark-source-contracts"]["evidence"] == {
        "blocked_public_benchmark_claim_surface_contracts": 18,
        "blocked_public_verifier_contracts": 18,
        "blocked_prime_reward_contracts": 18,
        "contract_count": 18,
        "current_runtime_enabled_contracts": 0,
        "expert_review_gate_contracts": 18,
        "future_reviewed_adapters": 18,
        "heavy_storage_contracts": 2,
        "public_verifier_allowed_contracts": 0,
        "requires_gpu_contracts": 2,
        "source_catalog_id_count": 18,
        "target_family_counts": {
            "all": 3,
            "code_based": 3,
            "hash_based": 1,
            "implementation_security": 8,
            "lattice": 2,
            "multivariate": 1,
        },
    }
    assert checks["nvidia-manifest-safety"]["status"] == "passed"
    assert checks["nvidia-manifest-safety"]["evidence"] == {
        "all_current_workloads_cpu": True,
        "artifact_count": 18,
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
    }
    assert checks["nvidia-publication-handoff"]["status"] == "passed"
    assert checks["nvidia-publication-handoff"]["blocking"] is True
    assert checks["nvidia-publication-handoff"]["evidence"] == {
        "artifact_count": 16,
        "current_gpu_required_workload_count": 0,
        "current_workload_count": 26,
        "external_submission_requires_review": True,
        "gpu_execution_performed": False,
        "gpu_future_workload_count": 1,
        "nvidia_submission_performed": False,
        "public_run_bundles": 18,
        "requires_credentials": False,
        "total_workload_count": 27,
    }
    assert checks["prime-environment-json-only"]["status"] == "passed"
    assert checks["prime-environment-json-only"]["evidence"] == {
        "packaged_tasks": 79,
    }
    assert checks["public-run-ledger-safety"]["status"] == "passed"
    assert checks["public-run-ledger-safety"]["evidence"] == {
        "bundles": 18,
        "families": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "LWE",
            "MLWE",
            "MULTIVARIATE",
        ],
        "redacted_records": 0,
        "total_records": 59,
    }
    assert checks["report-generator-redaction"]["status"] == "passed"
    assert checks["report-generator-redaction"]["blocking"] is True
    assert checks["report-generator-redaction"]["evidence"] == {
        "private_mapping_evaluator_output_absent": True,
        "private_mapping_score_absent": True,
        "private_mapping_target_absent": True,
        "private_evaluator_output_absent": True,
        "private_mutation_absent": True,
        "private_score_absent": True,
        "redacted_records": 2,
        "sensitive_target_absent": True,
    }
    assert checks["private-run-policy"]["status"] == "passed"
    assert checks["private-run-policy"]["blocking"] is True
    assert checks["private-run-policy"]["evidence"] == {
        "allowed_private_commands": 16,
        "allowed_private_roots": 6,
        "forbidden_public_roots": 5,
        "private_dataset_sources": 3,
        "private_rl_reward_terms": 6,
        "required_publication_controls": 5,
        "scheduler_allowed_triggers": 2,
        "scheduler_approval_gates": 4,
        "scheduler_retention_rules": 4,
    }
    assert checks["legacy-name-guard"]["status"] == "passed"
    assert checks["prime-publication-handoff"]["status"] == "passed"
    assert checks["prime-publication-handoff"]["blocking"] is True
    assert checks["prime-publication-handoff"]["evidence"] == {
        "artifact_count": 12,
        "external_publication_requires_review": True,
        "family_count": 9,
        "local_package_ready": True,
        "prime_hub_publication_performed": False,
        "requires_credentials": True,
        "task_count": 79,
    }
    assert checks["prime-speedrun-handoff"]["status"] == "passed"
    assert checks["prime-speedrun-handoff"]["blocking"] is True
    assert checks["prime-speedrun-handoff"]["evidence"] == {
        "artifact_count": 11,
        "bundle_count": 18,
        "external_execution_requires_review": True,
        "family_count": 9,
        "run_count": 59,
        "task_count": 79,
    }
    assert checks["prime-hub-publication"]["status"] == "warning"
    assert checks["prime-hub-publication"]["blocking"] is False
    assert checks["prime-hub-publication"]["evidence"] == {
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


def test_committed_release_audit_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "release_audit.json"
    committed = Path("public/release_audit.json")

    write_release_audit(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_release_audit_rejects_stale_public_checksum_manifest(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    dataset_rows = copied_root / "hf" / "dataset" / "attack_plans.jsonl"
    dataset_rows.write_text(
        dataset_rows.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    audit = build_release_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["checksum-manifests"]["status"] == "failed"
    assert any(
        "checksum mismatch for attack_plans.jsonl" in failure
        for failure in checks["checksum-manifests"]["failures"]
    )


def test_release_audit_rejects_runbook_manifest_digest_mismatch(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    runbook_path = copied_root / "public" / "runbook_audit.json"
    runbook = json.loads(runbook_path.read_text(encoding="utf-8"))
    architecture = next(
        check
        for check in runbook["checks"]
        if check["id"] == "runbook-family-agnostic-core"
    )
    architecture["evidence"]["family_plugin_module_digests"]["code_based"][
        "src/agades_pqc_gym/families/code_based/adapter.py"
    ] = "0" * 64
    runbook_path.write_text(json.dumps(runbook, indent=2, sort_keys=True) + "\n")

    audit = build_release_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["family-plugin-manifest"]["status"] == "failed"
    assert (
        checks["family-plugin-manifest"]["evidence"]["runbook_module_digests_match"]
        is False
    )
    assert (
        "Family plugin manifest digests do not match public runbook audit digests."
        in checks["family-plugin-manifest"]["failures"]
    )


def test_release_audit_rejects_registry_plugin_alignment_drift(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    registry_path = copied_root / "docs" / "family_registry_manifest.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["plugin_manifest_alignment"]["committed_manifest_synced"] = False
    registry["plugin_manifest_alignment"][
        "registry_runtime_adapter_entries_match_manifest"
    ] = False
    registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")

    audit = build_release_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    evidence = checks["family-registry-manifest"]["evidence"]
    assert audit["accepted"] is False
    assert checks["family-registry-manifest"]["status"] == "failed"
    assert evidence["plugin_manifest_synced"] is False
    assert evidence["registry_runtime_adapter_entries_match_plugin_manifest"] is False
    assert (
        "manifest: plugin_manifest_alignment.committed_manifest_synced is inconsistent."
    ) in checks["family-registry-manifest"]["failures"]
    assert (
        "manifest: plugin_manifest_alignment."
        "registry_runtime_adapter_entries_match_manifest is inconsistent."
    ) in checks["family-registry-manifest"]["failures"]


def test_release_audit_rejects_stale_ecosystem_smoke_report(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    report_path = copied_root / "reports" / "ecosystem_smoke.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["summary"]["prime_tasks"] = 1
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    audit = build_release_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["ecosystem-smoke-report"]["status"] == "failed"
    assert (
        checks["ecosystem-smoke-report"]["evidence"]["checked_in_report_synced"]
        is False
    )
    assert (
        "Ecosystem smoke report is not in sync."
        in checks["ecosystem-smoke-report"]["failures"]
    )


def test_release_audit_rejects_lattice_manifest_without_pin_enforcement(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    manifest_path = copied_root / "docs" / "lattice_estimator_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["agades_boundary"]["pin_enforcement"]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    audit = build_release_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["lattice-estimator-pin"]["status"] == "failed"
    assert any(
        "runtime pin enforcement" in failure
        for failure in checks["lattice-estimator-pin"]["failures"]
    )


def test_release_audit_rejects_missing_lattice_runtime_primary_boundary(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    (
        copied_root
        / "examples"
        / "attack_plans"
        / "lattice_lwe_modulus_switching_primary.json"
    ).unlink()

    audit = build_release_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["lattice-runtime-primary-boundary"]["status"] == "failed"
    assert (
        "Lattice runtime primary boundary AttackPlan is missing."
        in checks["lattice-runtime-primary-boundary"]["failures"]
    )


def test_release_audit_rejects_missing_openevolve_evaluator(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    (copied_root / "examples" / "openevolve" / "evaluator.py").unlink()

    audit = build_release_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["openevolve-evaluator-smoke"]["status"] == "failed"
    assert any(
        "OpenEvolve evaluator smoke failed" in failure
        for failure in checks["openevolve-evaluator-smoke"]["failures"]
    )


def test_release_audit_rejects_stale_openevolve_config(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    config_path = copied_root / "examples" / "openevolve" / "config.yaml"
    config = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        config.replace("security_claim: false", "security_claim: true"),
        encoding="utf-8",
    )

    audit = build_release_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["openevolve-config-template"]["status"] == "failed"
    assert (
        "OpenEvolve checked config is not in sync with DEFAULT_CONFIG_TEMPLATE."
        in checks["openevolve-config-template"]["failures"]
    )
    assert (
        "OpenEvolve config security_claim must be false."
        in checks["openevolve-config-template"]["failures"]
    )


def test_release_audit_rejects_stale_openevolve_smoke_report(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    report_path = copied_root / "reports" / "openevolve_smoke.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["summary"]["feature_family"] = "CODE_BASED"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    audit = build_release_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["openevolve-evaluator-smoke"]["status"] == "failed"
    assert (
        "Checked OpenEvolve smoke report is not in sync."
        in checks["openevolve-evaluator-smoke"]["failures"]
    )
    assert (
        "OpenEvolve smoke report seed plan family drifted."
        in checks["openevolve-evaluator-smoke"]["failures"]
    )


def test_release_audit_rejects_stale_nvidia_workload_summary(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    manifest_path = copied_root / "nvidia" / "accelerator_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["workload_summary"]["cpu_workload_count"] = 21
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    audit = build_release_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["nvidia-manifest-safety"]["status"] == "failed"
    assert any(
        "not in sync" in failure
        for failure in checks["nvidia-manifest-safety"]["failures"]
    )


def test_release_audit_rejects_ci_release_artifacts_without_explicit_max_passes(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    workflow_path = copied_root / ".github" / "workflows" / "ci.yml"
    workflow_path.write_text(
        workflow_path.read_text(encoding="utf-8").replace(
            "uv run agades-pqc release-artifacts --max-passes 6",
            "uv run agades-pqc release-artifacts",
        ),
        encoding="utf-8",
    )

    audit = build_release_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["github-actions-ci"]["status"] == "failed"
    assert any(
        "converge-release-artifacts" in failure
        and "release-artifacts --max-passes 6" in failure
        for failure in checks["github-actions-ci"]["failures"]
    )


def test_release_audit_rejects_ci_lean_gate_with_wrong_project_dir(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    workflow_path = copied_root / ".github" / "workflows" / "ci.yml"
    workflow_path.write_text(
        workflow_path.read_text(encoding="utf-8").replace(
            "lake-package-directory: formal/lean",
            "lake-package-directory: formal",
        ),
        encoding="utf-8",
    )

    audit = build_release_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["github-actions-ci"]["status"] == "failed"
    assert any(
        "Lean build gate has invalid input lake-package-directory" in failure
        and "'formal/lean'" in failure
        for failure in checks["github-actions-ci"]["failures"]
    )


def test_release_audit_rejects_ci_diff_without_task_metadata_schema(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    workflow_path = copied_root / ".github" / "workflows" / "ci.yml"
    workflow_path.write_text(
        workflow_path.read_text(encoding="utf-8").replace(
            " prime_intellect/schemas/task_metadata.schema.json",
            "",
        ),
        encoding="utf-8",
    )

    audit = build_release_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["github-actions-ci"]["status"] == "failed"
    assert any(
        "check-artifact-diff" in failure
        and "prime_intellect/schemas/task_metadata.schema.json" in failure
        for failure in checks["github-actions-ci"]["failures"]
    )


def test_release_audit_cli_writes_audit(tmp_path: Path) -> None:
    out = tmp_path / "release_audit.json"

    result = CliRunner().invoke(app, ["release-audit", "--out", str(out)])

    assert result.exit_code == 0
    assert f"release_audit={out}" in result.output
    assert json.loads(out.read_text())["accepted"] is True
