from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.huggingface_collection_manifest import (
    build_huggingface_collection_manifest,
    verify_huggingface_collection_manifest,
    write_huggingface_collection_manifest,
)

EXPECTED_FAMILY_SUPPORT = {
    "benchmark_count": 78,
    "cross_family_review_source_count": 3,
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
    "family_count": 9,
    "implemented": ["LWE", "MLWE"],
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
    "review_required_before_claims": True,
    "schema_only": ["NTRU", "SIS"],
    "toy_evaluators": [
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "MULTIVARIATE",
    ],
    "support_level_counts": {
        "implemented": 2,
        "schema_only": 2,
        "toy_evaluator": 5,
    },
    "unique_future_reviewed_adapter_source_count": 15,
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


def test_huggingface_collection_manifest_links_public_oss_surfaces(
    tmp_path: Path,
) -> None:
    out = tmp_path / "collection_manifest.json"

    manifest = write_huggingface_collection_manifest(out)

    dataset_info = json.loads(Path("hf/dataset/dataset_info.json").read_text())
    space_manifest = json.loads(Path("hf/space_manifest.json").read_text())
    public_benchmark = json.loads(
        Path("docs/public_benchmark_manifest.json").read_text()
    )
    public_run_export = json.loads(Path("public/run_export/manifest.json").read_text())
    source_catalog = json.loads(Path("docs/source_catalog.json").read_text())

    assert manifest == build_huggingface_collection_manifest()
    assert json.loads(out.read_text()) == manifest
    assert manifest["schema_version"] == "agades.pqc.hf_collection_manifest.v1"
    assert manifest["project"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert manifest["collection"] == {
        "suggested_title": "Agades PQC Gym",
        "suggested_slug": "agades/pqc-gym",
        "publication_status": "local_manifest_ready_review_required",
        "public_push_requires_review": True,
    }
    assert manifest["family_support"] == EXPECTED_FAMILY_SUPPORT
    assert manifest["source_catalog_scope"] == EXPECTED_SOURCE_CATALOG_SCOPE
    assert manifest["public_private_boundary"] == EXPECTED_PUBLIC_PRIVATE_BOUNDARY

    entries = {entry["id"]: entry for entry in manifest["entries"]}
    assert list(entries) == [
        "github-repository",
        "huggingface-dataset",
        "huggingface-space",
        "benchmark-card",
        "source-map",
        "public-benchmark-v0",
        "public-run-export",
    ]
    assert entries["github-repository"] == {
        "id": "github-repository",
        "kind": "repository",
        "platform": "github",
        "url": "https://github.com/AgadesTech/agades-pqc-gym",
        "local_path": ".",
        "description": "Canonical source for the Agades PQC Gym public verifier.",
        "requires_credentials": False,
        "review_required_before_publish": True,
    }
    assert entries["huggingface-dataset"]["repo_type"] == "dataset"
    assert entries["huggingface-dataset"]["suggested_repo_id"] == (
        dataset_info["dataset_name"]
    )
    assert entries["huggingface-dataset"]["local_path"] == "hf/dataset"
    assert entries["huggingface-dataset"]["attack_plan_count"] == (
        dataset_info["attack_plan_count"]
    )
    assert entries["huggingface-dataset"]["valid_attack_plan_count"] == (
        dataset_info["valid_attack_plan_count"]
    )
    assert entries["huggingface-dataset"]["public_run_bundles"] == (
        dataset_info["public_run_bundles"]
    )
    assert entries["huggingface-space"]["repo_type"] == "space"
    assert entries["huggingface-space"]["suggested_repo_id"] == (
        space_manifest["space"]["suggested_space_id"]
    )
    assert entries["huggingface-space"]["sdk"] == "gradio"
    assert entries["huggingface-space"]["example_count"] == (
        space_manifest["example_manifest"]["example_count"]
    )
    assert entries["benchmark-card"]["local_path"] == "hf/benchmark_card.md"
    assert entries["benchmark-card"]["public_benchmark_manifest"] == (
        "docs/public_benchmark_manifest.json"
    )
    assert entries["source-map"]["source_count"] == len(source_catalog["sources"])
    assert entries["source-map"]["platforms"] == sorted(
        {source["platform"] for source in source_catalog["sources"]}
    )
    assert entries["public-benchmark-v0"]["bundle_count"] == (
        public_benchmark["summary"]["bundle_count"]
    )
    assert entries["public-benchmark-v0"]["record_count"] == (
        public_benchmark["summary"]["record_count"]
    )
    assert entries["public-run-export"] == {
        "id": "public-run-export",
        "kind": "artifact",
        "platform": "github",
        "local_path": "public/run_export/manifest.json",
        "export_id": public_run_export["export"]["id"],
        "bundle_count": public_run_export["summary"]["bundle_count"],
        "run_count": public_run_export["summary"]["run_count"],
        "families": public_run_export["families"],
        "requires_credentials": False,
        "review_required_before_publish": True,
    }
    assert manifest["safety"] == {
        "contains_private_traces": False,
        "publishes_private_candidates": False,
        "arbitrary_code_execution": False,
        "live_targeting": False,
        "security_claim": False,
        "external_publication_requires_review": True,
    }
    assert manifest["release_gates"] == [
        "uv run agades-pqc hf-dataset --out hf/dataset",
        "uv run agades-pqc hf-dataset-verify --dataset hf/dataset",
        "uv run agades-pqc hf-space-manifest --out hf/space_manifest.json",
        "uv run agades-pqc hf-space-manifest-verify --manifest hf/space_manifest.json",
        "uv run agades-pqc hf-collection-manifest --out hf/collection_manifest.json",
        "uv run agades-pqc hf-collection-manifest-verify --manifest "
        "hf/collection_manifest.json",
        "uv run agades-pqc public-benchmark-manifest --out "
        "docs/public_benchmark_manifest.json",
        "uv run agades-pqc public-benchmark-verify --manifest "
        "docs/public_benchmark_manifest.json",
        "uv run agades-pqc public-run-export --out public/run_export",
        "uv run agades-pqc public-run-export-verify --export public/run_export",
        "uv run agades-pqc source-catalog --out docs/source_catalog.json",
        "uv run agades-pqc source-catalog-verify --catalog docs/source_catalog.json",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]


def test_committed_huggingface_collection_manifest_is_in_sync(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "collection_manifest.json"
    committed = Path("hf/collection_manifest.json")

    write_huggingface_collection_manifest(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_hf_collection_manifest_verify_accepts_committed_manifest() -> None:
    result = verify_huggingface_collection_manifest(
        Path("hf/collection_manifest.json")
    )

    assert result == {
        "schema_version": "agades.pqc.hf_collection_manifest_verification.v1",
        "manifest_path": "hf/collection_manifest.json",
        "accepted": True,
        "summary": {
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
            "families_with_future_reviewed_adapters": 8,
            "failure_count": 0,
            "family_count": 9,
            "non_lattice_toy_evaluator_count": 41,
            "non_lattice_toy_operator_security_claims": 0,
            "non_lattice_toy_operator_variant_count": 41,
            "public_push_requires_review": True,
            "raw_mapping_redaction_covered": True,
            "report_redaction_records": 2,
            "review_required_before_claims": True,
            "review_required_entries": 7,
            "security_claim": False,
            "suggested_slug": "agades/pqc-gym",
            "suggested_title": "Agades PQC Gym",
            "typed_trace_redaction_covered": True,
        },
        "failures": [],
    }


def test_hf_collection_manifest_verify_rejects_risky_publication_flags(
    tmp_path: Path,
) -> None:
    out = tmp_path / "collection_manifest.json"
    manifest = build_huggingface_collection_manifest()
    manifest["safety"]["publishes_private_candidates"] = True
    manifest["entries"][1]["review_required_before_publish"] = False
    manifest["family_support"]["review_required_before_claims"] = False
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_huggingface_collection_manifest(out)

    assert result["accepted"] is False
    assert "Hugging Face Collection manifest is not in sync." in result["failures"]
    assert (
        "Hugging Face Collection may publish private candidates."
        in result["failures"]
    )
    assert (
        "Hugging Face Collection entries must all require review."
        in result["failures"]
    )
    assert (
        "Hugging Face Collection family support must require review before claims."
        in result["failures"]
    )


def test_hf_collection_manifest_verify_rejects_source_scope_claim(
    tmp_path: Path,
) -> None:
    out = tmp_path / "collection_manifest.json"
    manifest = build_huggingface_collection_manifest()
    manifest["source_catalog_scope"]["non_lattice_toy_operator_security_claims"] = 1
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_huggingface_collection_manifest(out)

    assert result["accepted"] is False
    assert "Hugging Face Collection manifest is not in sync." in result["failures"]
    assert (
        "Hugging Face Collection source catalog scope must not contain "
        "non-lattice toy security claims."
    ) in result["failures"]


def test_hf_collection_manifest_verify_rejects_redaction_boundary_drift(
    tmp_path: Path,
) -> None:
    out = tmp_path / "collection_manifest.json"
    manifest = build_huggingface_collection_manifest()
    manifest["public_private_boundary"]["report_generator_redaction"][
        "raw_mapping_redaction_covered"
    ] = False
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_huggingface_collection_manifest(out)

    assert result["accepted"] is False
    assert result["summary"]["raw_mapping_redaction_covered"] is False
    assert "Hugging Face Collection manifest is not in sync." in result["failures"]
    assert (
        "Hugging Face Collection raw trace mapping redaction gate is incomplete."
        in result["failures"]
    )


def test_hf_collection_manifest_verify_rejects_empty_json_object(
    tmp_path: Path,
) -> None:
    out = tmp_path / "collection_manifest.json"
    out.write_text("{}\n", encoding="utf-8")

    result = verify_huggingface_collection_manifest(out)

    assert result["accepted"] is False
    assert "Hugging Face Collection manifest is not in sync." in result["failures"]
    assert (
        "Hugging Face Collection manifest project must be an object."
        in result["failures"]
    )


def test_hf_collection_manifest_cli_writes_manifest(tmp_path: Path) -> None:
    out = tmp_path / "collection_manifest.json"

    result = CliRunner().invoke(app, ["hf-collection-manifest", "--out", str(out)])

    assert result.exit_code == 0
    assert f"hf_collection_manifest={out}" in result.output
    assert json.loads(out.read_text())["schema_version"] == (
        "agades.pqc.hf_collection_manifest.v1"
    )


def test_hf_collection_manifest_verify_cli_accepts_current_manifest() -> None:
    result = CliRunner().invoke(
        app,
        [
            "hf-collection-manifest-verify",
            "--manifest",
            "hf/collection_manifest.json",
        ],
    )

    assert result.exit_code == 0
    assert "agades.pqc.hf_collection_manifest_verification.v1" in result.output
    assert '"accepted": true' in result.output
