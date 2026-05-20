from __future__ import annotations

import json
from pathlib import Path

from expected_family_support_summary import EXPECTED_FAMILY_SUPPORT_SUMMARY
from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.nvidia_publication_handoff import (
    build_nvidia_publication_handoff,
    verify_nvidia_publication_handoff,
    write_nvidia_publication_handoff,
)

EXPECTED_NVIDIA_ARTIFACT_PATHS = [
    "docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md",
    "nvidia/README.md",
    "nvidia/accelerator_manifest.json",
    "docs/source_catalog.json",
    "docs/benchmark_source_contracts.json",
    "docs/family_support_matrix.json",
    "docs/public_benchmark_manifest.json",
    "public/run_export/manifest.json",
    "docs/lattice_estimator_manifest.json",
    "docs/lattice_estimator_baseline_contracts.json",
    "hf/collection_manifest.json",
    "docs/huggingface_publication_handoff.json",
    "prime_intellect/verifiers_environment/prime_manifest.json",
    "prime_intellect/schemas/schema_manifest.json",
    "docs/prime_publication_handoff.json",
    "docs/prime_speedrun_handoff.json",
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


def test_nvidia_publication_handoff_records_review_boundaries(
    tmp_path: Path,
) -> None:
    out = tmp_path / "nvidia_publication_handoff.json"

    handoff = write_nvidia_publication_handoff(out)

    assert handoff == build_nvidia_publication_handoff()
    assert json.loads(out.read_text(encoding="utf-8")) == handoff
    assert handoff["schema_version"] == "agades.pqc.nvidia_publication_handoff.v1"
    assert handoff["project"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "cli": "agades-pqc",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert handoff["platform"] == {
        "ecosystem": "nvidia",
        "handoff_status": "strategy_ready_external_submission_blocked",
        "accelerator_manifest": "nvidia/accelerator_manifest.json",
        "accelerator_strategy": "docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md",
        "suggested_programs": [
            "nvidia_inception",
            "nvidia_accelerated_research_review",
        ],
        "review_channel": "manual_program_review_required",
    }
    assert handoff["readiness"] == {
        "accelerator_manifest_accepted": True,
        "all_current_workloads_cpu": True,
        "current_gpu_required_workload_count": 0,
        "current_workload_count": 26,
        "gpu_future_workload_count": 1,
        "public_run_bundles": 18,
        "total_workload_count": 27,
        "requires_credentials": False,
        "credentials_checked_at_generation": False,
        "credentials_present_in_artifact": False,
        "external_submission_requires_review": True,
        "nvidia_submission_performed": False,
        "gpu_execution_performed": False,
    }
    assert handoff["submission_plan"] == {
        "artifact_review_required": True,
        "program_application_manual_review_required": True,
        "command_templates": [],
        "contains_credentials": False,
        "external_submission_performed": False,
        "external_url_recorded": False,
        "first_publication_target": "manual_review_packet",
    }
    assert handoff["source_anchors"] == [
        {
            "id": "agades-nvidia-accelerator",
            "source_catalog_required": True,
            "current_use": "current_public_accelerator_contract",
        },
        {
            "id": "nvidia-inception",
            "source_catalog_required": True,
            "current_use": "accelerator_strategy_anchor",
        },
    ]
    assert handoff["family_support"] == EXPECTED_FAMILY_SUPPORT_SUMMARY
    assert handoff["source_catalog_scope"] == EXPECTED_SOURCE_CATALOG_SCOPE
    assert handoff["local_artifacts"]["artifact_paths"] == (
        EXPECTED_NVIDIA_ARTIFACT_PATHS
    )
    assert sorted(handoff["local_artifacts"]["artifact_sha256"]) == sorted(
        EXPECTED_NVIDIA_ARTIFACT_PATHS
    )
    assert handoff["safety"] == {
        "contains_private_traces": False,
        "publishes_private_candidates": False,
        "arbitrary_code_execution": False,
        "live_targeting": False,
        "security_claim": False,
        "claims_external_submission": False,
        "claims_gpu_results": False,
        "credentials_present_in_artifact": False,
    }
    assert handoff["review_required_before_submission"] == [
        "Confirm NVIDIA program, account, and target review channel.",
        "Run accelerator manifest, handoff, publication, and release gates.",
        "Review strategy text for CPU-only current workload boundaries.",
        "Confirm no GPU result or security claim is made before external use.",
        "Record external NVIDIA URLs only after reviewer approval.",
    ]
    assert handoff["release_gates"] == [
        "uv run pytest tests/test_nvidia_publication_handoff.py -q",
        "uv run agades-pqc nvidia-publication-handoff --out "
        "docs/nvidia_publication_handoff.json",
        "uv run agades-pqc nvidia-publication-handoff-verify --handoff "
        "docs/nvidia_publication_handoff.json",
        "uv run agades-pqc nvidia-manifest-verify --manifest "
        "nvidia/accelerator_manifest.json",
        "uv run agades-pqc publication-manifest-verify --manifest "
        "docs/publication_manifest.json",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]


def test_committed_nvidia_publication_handoff_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "nvidia_publication_handoff.json"
    committed = Path("docs/nvidia_publication_handoff.json")

    write_nvidia_publication_handoff(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_nvidia_publication_handoff_verify_accepts_committed_handoff() -> None:
    result = verify_nvidia_publication_handoff(
        Path("docs/nvidia_publication_handoff.json")
    )

    assert result == {
        "schema_version": "agades.pqc.nvidia_publication_handoff_verification.v1",
        "handoff_path": "docs/nvidia_publication_handoff.json",
        "accepted": True,
        "summary": {
            "artifact_count": 16,
            "current_gpu_required_workload_count": 0,
            "current_workload_count": 26,
            "external_submission_requires_review": True,
            "failure_count": 0,
            "gpu_execution_performed": False,
            "gpu_future_workload_count": 1,
            "nvidia_submission_performed": False,
            "family_count": 9,
            "family_support_review_required_before_claims": True,
            "implemented_families": ["LWE", "MLWE"],
            "non_lattice_toy_evaluator_count": 41,
            "non_lattice_toy_operator_security_claims": 0,
            "non_lattice_toy_operator_variant_count": 41,
            "public_run_bundles": 18,
            "requires_credentials": False,
            "total_workload_count": 27,
        },
        "failures": [],
    }


def test_nvidia_publication_handoff_verify_rejects_external_submission_claim(
    tmp_path: Path,
) -> None:
    handoff = build_nvidia_publication_handoff()
    handoff["readiness"]["nvidia_submission_performed"] = True
    handoff["submission_plan"]["external_submission_performed"] = True
    handoff["safety"]["claims_external_submission"] = True
    out = tmp_path / "nvidia_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_nvidia_publication_handoff(out)

    assert result["accepted"] is False
    assert "NVIDIA publication handoff is not in sync." in result["failures"]
    assert "NVIDIA handoff must not claim external submission." in result[
        "failures"
    ]
    assert "NVIDIA handoff claims external submission." in result["failures"]


def test_nvidia_publication_handoff_verify_rejects_gpu_result_claim(
    tmp_path: Path,
) -> None:
    handoff = build_nvidia_publication_handoff()
    handoff["readiness"]["gpu_execution_performed"] = True
    handoff["safety"]["claims_gpu_results"] = True
    out = tmp_path / "nvidia_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_nvidia_publication_handoff(out)

    assert result["accepted"] is False
    assert "NVIDIA handoff must not claim GPU execution." in result["failures"]
    assert "NVIDIA handoff claims GPU results." in result["failures"]


def test_nvidia_publication_handoff_verify_rejects_source_scope_claim(
    tmp_path: Path,
) -> None:
    handoff = build_nvidia_publication_handoff()
    handoff["source_catalog_scope"]["non_lattice_toy_operator_security_claims"] = 1
    out = tmp_path / "nvidia_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_nvidia_publication_handoff(out)

    assert result["accepted"] is False
    assert "NVIDIA publication handoff is not in sync." in result["failures"]
    assert (
        "NVIDIA handoff source catalog scope must not contain "
        "non-lattice toy security claims."
    ) in result["failures"]


def test_nvidia_publication_handoff_verify_rejects_family_support_claim_gate(
    tmp_path: Path,
) -> None:
    handoff = build_nvidia_publication_handoff()
    handoff["family_support"]["review_required_before_claims"] = False
    out = tmp_path / "nvidia_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_nvidia_publication_handoff(out)

    assert result["accepted"] is False
    assert "NVIDIA publication handoff is not in sync." in result["failures"]
    assert (
        "NVIDIA handoff family_support.review_required_before_claims must be true."
    ) in result["failures"]


def test_nvidia_publication_handoff_cli_writes_handoff(tmp_path: Path) -> None:
    out = tmp_path / "nvidia_publication_handoff.json"

    result = CliRunner().invoke(
        app,
        ["nvidia-publication-handoff", "--out", str(out)],
    )

    assert result.exit_code == 0
    assert f"nvidia_publication_handoff={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["schema_version"] == (
        "agades.pqc.nvidia_publication_handoff.v1"
    )


def test_nvidia_publication_handoff_verify_cli_accepts_committed_handoff() -> None:
    result = CliRunner().invoke(
        app,
        [
            "nvidia-publication-handoff-verify",
            "--handoff",
            "docs/nvidia_publication_handoff.json",
        ],
    )

    assert result.exit_code == 0
    assert "agades.pqc.nvidia_publication_handoff_verification.v1" in result.output
    assert '"accepted": true' in result.output
