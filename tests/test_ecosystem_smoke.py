from __future__ import annotations

import json
from pathlib import Path

from agades_pqc_gym.integrations import ecosystem_smoke
from agades_pqc_gym.integrations.ecosystem_smoke import (
    ECOSYSTEM_SMOKE_SCHEMA,
    build_ecosystem_smoke_report,
    verify_ecosystem_smoke_report,
    write_ecosystem_smoke_report,
)

EXPECTED_PLATFORM_FAMILY_SUPPORT = {
    "families_with_future_reviewed_adapters": 8,
    "family_count": 9,
    "review_required_before_claims": True,
}
EXPECTED_PLATFORM_PUBLIC_PRIVATE_BOUNDARY = {
    "raw_mapping_redaction_covered": True,
    "report_redaction_records": 2,
    "typed_trace_redaction_covered": True,
}
EXPECTED_RUNBOOK_ARCHITECTURE = {
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


def test_ecosystem_smoke_report_summarizes_local_oss_surfaces(
    tmp_path: Path,
) -> None:
    out = tmp_path / "ecosystem_smoke.json"

    report = write_ecosystem_smoke_report(out)

    assert json.loads(out.read_text(encoding="utf-8")) == report
    assert report == build_ecosystem_smoke_report()
    assert report["schema_version"] == ECOSYSTEM_SMOKE_SCHEMA
    assert report["accepted"] is True
    assert report["summary"] == {
        "credentialed_surface_count": 4,
        "external_publication_ready": False,
        "families_with_future_reviewed_adapters": 8,
        "failure_count": 0,
        "family_count": 9,
        "future_reviewed_adapter_sources_by_family": 21,
        "hf_space_examples": 79,
        "hf_valid_attack_plan_rows": 79,
        "local_artifacts_ready": True,
        "nvidia_current_gpu_required_workloads": 0,
        "nvidia_current_workloads": 26,
        "platform_family_support_family_counts_match": True,
        "platform_family_support_surfaces": 3,
        "platform_public_private_boundary_surfaces": 3,
        "platform_report_redaction_records_match": True,
        "platforms_with_family_claim_review_gate": 3,
        "platforms_with_raw_mapping_redaction_gate": 3,
        "platforms_with_typed_trace_redaction_gate": 3,
        "prime_tasks": 79,
        "public_run_bundles": 18,
        "review_required_surface_count": 6,
        "reviewer_summary_synced": True,
        **EXPECTED_RUNBOOK_ARCHITECTURE,
    }
    assert report["surfaces"]["hugging_face"]["accepted"] is True
    assert report["surfaces"]["hugging_face"]["dataset"] == {
        "accepted": True,
        "attack_plan_count": 80,
        "public_run_bundle_count": 18,
        "task_metadata_rows": 79,
        "valid_attack_plan_count": 79,
    }
    assert report["surfaces"]["hugging_face"]["collection"] == {
        "accepted": True,
        "entry_count": 7,
        "external_publication_requires_review": True,
        "family_support": EXPECTED_PLATFORM_FAMILY_SUPPORT,
        "public_private_boundary": EXPECTED_PLATFORM_PUBLIC_PRIVATE_BOUNDARY,
        "public_push_requires_review": True,
    }
    assert report["surfaces"]["prime_intellect"]["environment"] == {
        "accepted": True,
        "family_support": EXPECTED_PLATFORM_FAMILY_SUPPORT,
        "family_count": 9,
        "mirrors_public_examples": True,
        "public_private_boundary": EXPECTED_PLATFORM_PUBLIC_PRIVATE_BOUNDARY,
        "public_push_requires_review": True,
        "task_count": 79,
    }
    assert report["surfaces"]["nvidia"] == {
        "accepted": True,
        "all_current_workloads_cpu": True,
        "current_gpu_required_workload_count": 0,
        "current_workload_count": 26,
        "family_support": EXPECTED_PLATFORM_FAMILY_SUPPORT,
        "public_private_boundary": EXPECTED_PLATFORM_PUBLIC_PRIVATE_BOUNDARY,
        "public_run_bundle_count": 18,
        "reserved_future_gpu_required_workload_count": 1,
        "total_workload_count": 27,
    }
    assert report["surfaces"]["publication"]["preflight"] == {
        "accepted": True,
        "blockers": 2,
        "local_artifacts_ready": True,
        "ready_for_external_publication": False,
        "warnings": 1,
    }
    assert report["surfaces"]["publication"]["external_review_packet"] == {
        "accepted": True,
        "blockers": 2,
        "credentialed_surface_count": 4,
        "families_with_future_reviewed_adapters": 8,
        "family_count": 9,
        "future_reviewed_adapter_sources_by_family": 21,
        "ready_for_external_publication": False,
        "review_required_before_claims": True,
        "review_required_surface_count": 6,
        "reviewer_summary_synced": True,
        "surface_count": 6,
        "warnings": 1,
        **EXPECTED_RUNBOOK_ARCHITECTURE,
    }
    assert report["safety"] == {
        "arbitrary_code_execution": False,
        "external_publication_performed": False,
        "external_publication_requires_review": True,
        "live_targeting": False,
        "publishes_private_candidates": False,
        "security_claim": False,
    }
    assert report["failures"] == []


def test_ecosystem_smoke_reports_downstream_preflight_readiness_without_failing(
    monkeypatch,
) -> None:
    def fake_publication_preflight(*args, **kwargs) -> dict[str, object]:
        return {
            "accepted": True,
            "summary": {
                "blockers": 2,
                "failure_count": 0,
                "local_artifacts_ready": False,
                "ready_for_external_publication": False,
                "warnings": 1,
            },
            "failures": [],
        }

    monkeypatch.setattr(
        ecosystem_smoke,
        "verify_publication_preflight",
        fake_publication_preflight,
    )

    report = build_ecosystem_smoke_report()

    assert report["accepted"] is True
    assert report["summary"]["local_artifacts_ready"] is False
    assert report["surfaces"]["publication"]["preflight"]["accepted"] is True
    assert report["failures"] == []


def test_ecosystem_smoke_verify_accepts_checked_in_report() -> None:
    result = verify_ecosystem_smoke_report(Path("reports/ecosystem_smoke.json"))

    assert result["schema_version"] == "agades.pqc.ecosystem_smoke_verification.v1"
    assert result["accepted"] is True
    assert result["summary"] == {
        "checked_in_report_accepted": True,
        "checked_in_report_synced": True,
        "expected_report_accepted": True,
        "failure_count": 0,
        "reviewer_summary_synced": True,
        **EXPECTED_RUNBOOK_ARCHITECTURE,
    }
    assert result["failures"] == []


def test_ecosystem_smoke_verify_rejects_unsynced_report(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "ecosystem_smoke.json"
    report = build_ecosystem_smoke_report()
    report["summary"]["prime_tasks"] = 1
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = verify_ecosystem_smoke_report(report_path)

    assert result["accepted"] is False
    assert result["summary"]["checked_in_report_synced"] is False
    assert "Ecosystem smoke report is not in sync." in result["failures"]


def test_ecosystem_smoke_treats_preflight_sync_as_downstream_advisory(
    monkeypatch,
) -> None:
    def fake_publication_preflight(*args, **kwargs) -> dict[str, object]:
        return {
            "accepted": False,
            "summary": {
                "blockers": 2,
                "failure_count": 1,
                "local_artifacts_ready": False,
                "ready_for_external_publication": False,
                "warnings": 1,
            },
            "failures": ["Publication preflight is not in sync."],
        }

    monkeypatch.setattr(
        ecosystem_smoke,
        "verify_publication_preflight",
        fake_publication_preflight,
    )

    report = build_ecosystem_smoke_report()

    assert report["accepted"] is True
    assert report["summary"]["local_artifacts_ready"] is False
    assert report["surfaces"]["publication"]["preflight"]["accepted"] is False
    assert report["failures"] == []


def test_ecosystem_smoke_rejects_runbook_architecture_drift(
    monkeypatch,
) -> None:
    original_verifier = (
        ecosystem_smoke.verify_external_publication_review_packet
    )

    def fake_external_packet_verifier(*args, **kwargs) -> dict[str, object]:
        result = original_verifier(*args, **kwargs)
        result["summary"]["runbook_family_plugin_manifest_digests_match"] = False
        result["summary"]["runbook_family_registry_plugin_manifest_synced"] = False
        result["summary"][
            "runbook_family_registry_runtime_adapter_entries_match_plugin_manifest"
        ] = False
        return result

    monkeypatch.setattr(
        ecosystem_smoke,
        "verify_external_publication_review_packet",
        fake_external_packet_verifier,
    )

    report = build_ecosystem_smoke_report()

    assert report["accepted"] is False
    assert report["summary"]["runbook_family_plugin_manifest_digests_match"] is False
    assert report["summary"]["runbook_family_registry_plugin_manifest_synced"] is False
    assert (
        "Ecosystem smoke runbook architecture evidence must keep plugin "
        "digests synchronized."
    ) in report["failures"]
    assert (
        "Ecosystem smoke runbook architecture evidence must keep the family "
        "registry synchronized with the plugin manifest."
    ) in report["failures"]
    assert (
        "Ecosystem smoke runbook architecture evidence must keep registry "
        "runtime adapters synchronized."
    ) in report["failures"]


def test_ecosystem_smoke_rejects_external_reviewer_summary_drift(
    monkeypatch,
) -> None:
    original_verifier = (
        ecosystem_smoke.verify_external_publication_review_packet
    )

    def fake_external_packet_verifier(*args, **kwargs) -> dict[str, object]:
        result = original_verifier(*args, **kwargs)
        result["summary"]["reviewer_summary_synced"] = False
        return result

    monkeypatch.setattr(
        ecosystem_smoke,
        "verify_external_publication_review_packet",
        fake_external_packet_verifier,
    )

    report = build_ecosystem_smoke_report()

    assert report["accepted"] is False
    assert report["summary"]["reviewer_summary_synced"] is False
    assert (
        "Ecosystem smoke external review packet summary must remain synchronized."
    ) in report["failures"]


def test_ecosystem_smoke_rejects_platform_family_claim_gate_drift(
    monkeypatch,
) -> None:
    original_verifier = ecosystem_smoke.verify_nvidia_accelerator_manifest

    def fake_nvidia_verifier(*args, **kwargs) -> dict[str, object]:
        result = original_verifier(*args, **kwargs)
        result["summary"]["review_required_before_claims"] = False
        return result

    monkeypatch.setattr(
        ecosystem_smoke,
        "verify_nvidia_accelerator_manifest",
        fake_nvidia_verifier,
    )

    report = build_ecosystem_smoke_report()

    assert report["accepted"] is False
    assert report["summary"]["platforms_with_family_claim_review_gate"] == 2
    assert (
        "Ecosystem smoke platform family-support gates must require review "
        "before claims."
    ) in report["failures"]


def test_ecosystem_smoke_rejects_platform_redaction_gate_drift(
    monkeypatch,
) -> None:
    original_verifier = ecosystem_smoke.verify_nvidia_accelerator_manifest

    def fake_nvidia_verifier(*args, **kwargs) -> dict[str, object]:
        result = original_verifier(*args, **kwargs)
        result["summary"]["raw_mapping_redaction_covered"] = False
        return result

    monkeypatch.setattr(
        ecosystem_smoke,
        "verify_nvidia_accelerator_manifest",
        fake_nvidia_verifier,
    )

    report = build_ecosystem_smoke_report()

    assert report["accepted"] is False
    assert report["summary"]["platforms_with_raw_mapping_redaction_gate"] == 2
    assert (
        "Ecosystem smoke platform raw trace mapping redaction gates must be "
        "covered."
    ) in report["failures"]
