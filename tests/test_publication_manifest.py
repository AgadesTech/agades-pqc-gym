from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations import publication_manifest
from agades_pqc_gym.integrations.publication_manifest import (
    build_publication_manifest,
    write_publication_manifest,
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


def _write_placeholder_surface_artifacts(root: Path) -> None:
    for surface in build_publication_manifest()["surfaces"]:
        for artifact_path in surface["artifact_paths"]:
            path = root / artifact_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{artifact_path}\n", encoding="utf-8")
    for artifact_path in (
        "docs/family_support_matrix.json",
        "hf/collection_manifest.json",
        "nvidia/accelerator_manifest.json",
        "prime_intellect/verifiers_environment/prime_manifest.json",
    ):
        (root / artifact_path).write_text(
            Path(artifact_path).read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def test_publication_manifest_maps_public_oss_surfaces(tmp_path: Path) -> None:
    out = tmp_path / "publication_manifest.json"

    manifest = write_publication_manifest(out)

    assert manifest == build_publication_manifest()
    assert json.loads(out.read_text()) == manifest
    assert manifest["schema_version"] == "agades.pqc.publication_manifest.v1"
    assert manifest["project"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "cli": "agades-pqc",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert manifest["safety"] == {
        "contains_private_traces": False,
        "arbitrary_code_execution": False,
        "live_targeting": False,
        "security_claim": False,
        "publishes_private_candidates": False,
        "external_publication_requires_review": True,
    }
    assert manifest["family_support"] == EXPECTED_FAMILY_SUPPORT_PUBLICATION_GATE

    surfaces = {surface["id"]: surface for surface in manifest["surfaces"]}
    assert set(surfaces) == {
        "github-repository",
        "huggingface-dataset",
        "huggingface-collection",
        "huggingface-space",
        "prime-verifiers-environment",
        "nvidia-accelerator-story",
    }
    assert surfaces["github-repository"]["platform"] == "github"
    assert "docs/lattice_estimator_manifest.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "docs/lattice_estimator_baseline_contracts.json" in surfaces[
        "github-repository"
    ]["artifact_paths"]
    assert "docs/public_benchmark_manifest.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "docs/runbook_input_manifest.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "public/run_export/manifest.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "public/run_export/runs.jsonl" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "public/run_export/runs.csv" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "public/run_export/MANIFEST.sha256" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "docs/benchmark_source_contracts.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "docs/source_catalog.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "docs/family_support_matrix.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "docs/private_run_policy.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "docs/family_registry_manifest.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "docs/family_plugin_manifest.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "docs/family_operator_catalog.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "docs/huggingface_publication_handoff.json" in surfaces[
        "github-repository"
    ]["artifact_paths"]
    assert "docs/prime_publication_handoff.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "docs/prime_speedrun_handoff.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "docs/nvidia_publication_handoff.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    assert "docs/release_status.json" in surfaces["github-repository"][
        "artifact_paths"
    ]
    expected_paper_cards = {
        path.as_posix()
        for path in sorted(Path("examples/paper_cards").glob("*.yaml"))
    }
    assert expected_paper_cards <= set(
        surfaces["github-repository"]["artifact_paths"]
    )
    assert surfaces["huggingface-dataset"]["platform"] == "hugging_face"
    assert surfaces["huggingface-dataset"]["requires_credentials"] is True
    assert surfaces["huggingface-dataset"]["publication_status"] == (
        "local_artifact_ready"
    )
    assert "hf/dataset/MANIFEST.sha256" in surfaces["huggingface-dataset"][
        "artifact_paths"
    ]
    assert "hf/dataset/task_metadata.jsonl" in surfaces["huggingface-dataset"][
        "artifact_paths"
    ]
    assert surfaces["huggingface-space"]["smoke_gate"] == "hf-space-smoke"
    assert "hf/space_manifest.json" in surfaces["huggingface-space"][
        "artifact_paths"
    ]
    assert surfaces["huggingface-collection"]["platform"] == "hugging_face"
    assert surfaces["huggingface-collection"]["requires_credentials"] is True
    assert surfaces["huggingface-collection"]["smoke_gate"] == (
        "hf-collection-manifest"
    )
    assert "hf/collection_manifest.json" in surfaces["huggingface-collection"][
        "artifact_paths"
    ]
    assert "hf/benchmark_card.md" in surfaces["huggingface-collection"][
        "artifact_paths"
    ]
    assert "docs/source_catalog.json" in surfaces["huggingface-collection"][
        "artifact_paths"
    ]
    assert "docs/huggingface_publication_handoff.json" in surfaces[
        "huggingface-collection"
    ]["artifact_paths"]
    assert surfaces["prime-verifiers-environment"]["smoke_gate"] == (
        "prime-environment-smoke"
    )
    assert "prime_intellect/verifiers_environment/prime_manifest.json" in surfaces[
        "prime-verifiers-environment"
    ]["artifact_paths"]
    assert "prime_intellect/schemas/attack_plan.schema.json" in surfaces[
        "prime-verifiers-environment"
    ]["artifact_paths"]
    assert "prime_intellect/schemas/verifier_result.schema.json" in surfaces[
        "prime-verifiers-environment"
    ]["artifact_paths"]
    assert "prime_intellect/schemas/task_metadata.schema.json" in surfaces[
        "prime-verifiers-environment"
    ]["artifact_paths"]
    assert "prime_intellect/schemas/schema_manifest.json" in surfaces[
        "prime-verifiers-environment"
    ]["artifact_paths"]
    assert "docs/prime_speedrun_handoff.json" in surfaces[
        "prime-verifiers-environment"
    ]["artifact_paths"]
    assert surfaces["nvidia-accelerator-story"]["review_required_before_publish"] is (
        True
    )
    assert "docs/nvidia_publication_handoff.json" in surfaces[
        "nvidia-accelerator-story"
    ]["artifact_paths"]
    for surface in surfaces.values():
        digest_exclusions = surface.get("artifact_digest_exclusions", {})
        assert surface["artifact_sha256"] == {
            artifact_path: hashlib.sha256(Path(artifact_path).read_bytes()).hexdigest()
            for artifact_path in surface["artifact_paths"]
            if artifact_path not in digest_exclusions
        }
        assert set(surface["artifact_sha256"]) | set(digest_exclusions) == set(
            surface["artifact_paths"]
        )
    assert surfaces["github-repository"]["artifact_digest_exclusions"] == {
        "docs/external_publication_review_packet.json": (
            "derived_from_preflight_status_and_platform_manifests"
        ),
        "docs/release_status.json": (
            "derived_from_release_audit_and_publication_manifest"
        ),
        "public/release_audit.json": "recursive_release_audit_artifact",
    }

    public_run_bundles = {
        bundle["id"]: bundle for bundle in manifest["public_run_bundles"]
    }
    assert public_run_bundles == {
        "code_based_toy_classic_mceliece_v0": {
            "id": "code_based_toy_classic_mceliece_v0",
            "family": "CODE_BASED",
            "benchmark_path": "benchmarks/code_based_toy_classic_mceliece",
            "artifact_paths": [
                "examples/public_runs/code_based_toy_classic_mceliece_v0/README.md",
                (
                    "examples/public_runs/code_based_toy_classic_mceliece_v0/"
                    "run_ledger.json"
                ),
                (
                    "examples/public_runs/code_based_toy_classic_mceliece_v0/"
                    "trace_public.jsonl"
                ),
                (
                    "examples/public_runs/code_based_toy_classic_mceliece_v0/"
                    "MANIFEST.sha256"
                ),
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/code_based_toy_classic_mceliece_v0/README.md",
                    (
                        "examples/public_runs/code_based_toy_classic_mceliece_v0/"
                        "run_ledger.json"
                    ),
                    (
                        "examples/public_runs/code_based_toy_classic_mceliece_v0/"
                        "trace_public.jsonl"
                    ),
                    (
                        "examples/public_runs/code_based_toy_classic_mceliece_v0/"
                        "MANIFEST.sha256"
                    ),
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "code_based_toy_hqc_v0": {
            "id": "code_based_toy_hqc_v0",
            "family": "CODE_BASED",
            "benchmark_path": "benchmarks/code_based_toy_hqc",
            "artifact_paths": [
                "examples/public_runs/code_based_toy_hqc_v0/README.md",
                "examples/public_runs/code_based_toy_hqc_v0/run_ledger.json",
                "examples/public_runs/code_based_toy_hqc_v0/trace_public.jsonl",
                "examples/public_runs/code_based_toy_hqc_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/code_based_toy_hqc_v0/README.md",
                    "examples/public_runs/code_based_toy_hqc_v0/run_ledger.json",
                    "examples/public_runs/code_based_toy_hqc_v0/trace_public.jsonl",
                    "examples/public_runs/code_based_toy_hqc_v0/MANIFEST.sha256",
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "code_based_toy_isd_v0": {
            "id": "code_based_toy_isd_v0",
            "family": "CODE_BASED",
            "benchmark_path": "benchmarks/code_based_toy_isd",
            "artifact_paths": [
                "examples/public_runs/code_based_toy_isd_v0/README.md",
                "examples/public_runs/code_based_toy_isd_v0/run_ledger.json",
                "examples/public_runs/code_based_toy_isd_v0/trace_public.jsonl",
                "examples/public_runs/code_based_toy_isd_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/code_based_toy_isd_v0/README.md",
                    "examples/public_runs/code_based_toy_isd_v0/run_ledger.json",
                    "examples/public_runs/code_based_toy_isd_v0/trace_public.jsonl",
                    "examples/public_runs/code_based_toy_isd_v0/MANIFEST.sha256",
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "code_based_toy_mdpc_v0": {
            "id": "code_based_toy_mdpc_v0",
            "family": "CODE_BASED",
            "benchmark_path": "benchmarks/code_based_toy_mdpc",
            "artifact_paths": [
                "examples/public_runs/code_based_toy_mdpc_v0/README.md",
                "examples/public_runs/code_based_toy_mdpc_v0/run_ledger.json",
                "examples/public_runs/code_based_toy_mdpc_v0/trace_public.jsonl",
                "examples/public_runs/code_based_toy_mdpc_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/code_based_toy_mdpc_v0/README.md",
                    "examples/public_runs/code_based_toy_mdpc_v0/run_ledger.json",
                    "examples/public_runs/code_based_toy_mdpc_v0/trace_public.jsonl",
                    "examples/public_runs/code_based_toy_mdpc_v0/MANIFEST.sha256",
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "hash_based_toy_bound_v0": {
            "id": "hash_based_toy_bound_v0",
            "family": "HASH_BASED",
            "benchmark_path": "benchmarks/hash_based_toy_bound",
            "artifact_paths": [
                "examples/public_runs/hash_based_toy_bound_v0/README.md",
                "examples/public_runs/hash_based_toy_bound_v0/run_ledger.json",
                "examples/public_runs/hash_based_toy_bound_v0/trace_public.jsonl",
                "examples/public_runs/hash_based_toy_bound_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/hash_based_toy_bound_v0/README.md",
                    "examples/public_runs/hash_based_toy_bound_v0/run_ledger.json",
                    "examples/public_runs/hash_based_toy_bound_v0/trace_public.jsonl",
                    "examples/public_runs/hash_based_toy_bound_v0/MANIFEST.sha256",
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "hash_based_toy_misuse_v0": {
            "id": "hash_based_toy_misuse_v0",
            "family": "HASH_BASED",
            "benchmark_path": "benchmarks/hash_based_toy_misuse",
            "artifact_paths": [
                "examples/public_runs/hash_based_toy_misuse_v0/README.md",
                "examples/public_runs/hash_based_toy_misuse_v0/run_ledger.json",
                "examples/public_runs/hash_based_toy_misuse_v0/trace_public.jsonl",
                "examples/public_runs/hash_based_toy_misuse_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/hash_based_toy_misuse_v0/README.md",
                    "examples/public_runs/hash_based_toy_misuse_v0/run_ledger.json",
                    "examples/public_runs/hash_based_toy_misuse_v0/trace_public.jsonl",
                    "examples/public_runs/hash_based_toy_misuse_v0/MANIFEST.sha256",
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "hash_based_toy_signature_v0": {
            "id": "hash_based_toy_signature_v0",
            "family": "HASH_BASED",
            "benchmark_path": "benchmarks/hash_based_toy_signature",
            "artifact_paths": [
                "examples/public_runs/hash_based_toy_signature_v0/README.md",
                "examples/public_runs/hash_based_toy_signature_v0/run_ledger.json",
                "examples/public_runs/hash_based_toy_signature_v0/trace_public.jsonl",
                "examples/public_runs/hash_based_toy_signature_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/hash_based_toy_signature_v0/README.md",
                    (
                        "examples/public_runs/hash_based_toy_signature_v0/"
                        "run_ledger.json"
                    ),
                    (
                        "examples/public_runs/hash_based_toy_signature_v0/"
                        "trace_public.jsonl"
                    ),
                    (
                        "examples/public_runs/hash_based_toy_signature_v0/"
                        "MANIFEST.sha256"
                    ),
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "implementation_security_toy_benchmark_v0": {
            "id": "implementation_security_toy_benchmark_v0",
            "family": "IMPLEMENTATION_SECURITY",
            "benchmark_path": "benchmarks/implementation_security_toy_benchmark",
            "artifact_paths": [
                (
                    "examples/public_runs/implementation_security_toy_benchmark_v0/"
                    "README.md"
                ),
                (
                    "examples/public_runs/implementation_security_toy_benchmark_v0/"
                    "run_ledger.json"
                ),
                (
                    "examples/public_runs/implementation_security_toy_benchmark_v0/"
                    "trace_public.jsonl"
                ),
                (
                    "examples/public_runs/implementation_security_toy_benchmark_v0/"
                    "MANIFEST.sha256"
                ),
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    (
                        "examples/public_runs/"
                        "implementation_security_toy_benchmark_v0/README.md"
                    ),
                    (
                        "examples/public_runs/"
                        "implementation_security_toy_benchmark_v0/run_ledger.json"
                    ),
                    (
                        "examples/public_runs/"
                        "implementation_security_toy_benchmark_v0/"
                        "trace_public.jsonl"
                    ),
                    (
                        "examples/public_runs/"
                        "implementation_security_toy_benchmark_v0/MANIFEST.sha256"
                    ),
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "implementation_security_toy_kat_v0": {
            "id": "implementation_security_toy_kat_v0",
            "family": "IMPLEMENTATION_SECURITY",
            "benchmark_path": "benchmarks/implementation_security_toy_kat",
            "artifact_paths": [
                "examples/public_runs/implementation_security_toy_kat_v0/README.md",
                "examples/public_runs/implementation_security_toy_kat_v0/run_ledger.json",
                "examples/public_runs/implementation_security_toy_kat_v0/trace_public.jsonl",
                "examples/public_runs/implementation_security_toy_kat_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/implementation_security_toy_kat_v0/README.md",
                    (
                        "examples/public_runs/implementation_security_toy_kat_v0/"
                        "run_ledger.json"
                    ),
                    (
                        "examples/public_runs/implementation_security_toy_kat_v0/"
                        "trace_public.jsonl"
                    ),
                    (
                        "examples/public_runs/implementation_security_toy_kat_v0/"
                        "MANIFEST.sha256"
                    ),
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "implementation_security_toy_timing_v0": {
            "id": "implementation_security_toy_timing_v0",
            "family": "IMPLEMENTATION_SECURITY",
            "benchmark_path": "benchmarks/implementation_security_toy_timing",
            "artifact_paths": [
                "examples/public_runs/implementation_security_toy_timing_v0/README.md",
                (
                    "examples/public_runs/implementation_security_toy_timing_v0/"
                    "run_ledger.json"
                ),
                (
                    "examples/public_runs/implementation_security_toy_timing_v0/"
                    "trace_public.jsonl"
                ),
                (
                    "examples/public_runs/implementation_security_toy_timing_v0/"
                    "MANIFEST.sha256"
                ),
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    (
                        "examples/public_runs/implementation_security_toy_timing_v0/"
                        "README.md"
                    ),
                    (
                        "examples/public_runs/implementation_security_toy_timing_v0/"
                        "run_ledger.json"
                    ),
                    (
                        "examples/public_runs/implementation_security_toy_timing_v0/"
                        "trace_public.jsonl"
                    ),
                    (
                        "examples/public_runs/implementation_security_toy_timing_v0/"
                        "MANIFEST.sha256"
                    ),
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "isogeny_historical_toy_path_v0": {
            "id": "isogeny_historical_toy_path_v0",
            "family": "ISOGENY_HISTORICAL",
            "benchmark_path": "benchmarks/isogeny_historical_toy_path",
            "artifact_paths": [
                "examples/public_runs/isogeny_historical_toy_path_v0/README.md",
                "examples/public_runs/isogeny_historical_toy_path_v0/run_ledger.json",
                "examples/public_runs/isogeny_historical_toy_path_v0/trace_public.jsonl",
                "examples/public_runs/isogeny_historical_toy_path_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/isogeny_historical_toy_path_v0/README.md",
                    (
                        "examples/public_runs/isogeny_historical_toy_path_v0/"
                        "run_ledger.json"
                    ),
                    (
                        "examples/public_runs/isogeny_historical_toy_path_v0/"
                        "trace_public.jsonl"
                    ),
                    (
                        "examples/public_runs/isogeny_historical_toy_path_v0/"
                        "MANIFEST.sha256"
                    ),
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "lattice_downscaled_lwe_instance_solve_v0": {
            "id": "lattice_downscaled_lwe_instance_solve_v0",
            "family": "LWE",
            "benchmark_path": "benchmarks/lattice_downscaled_lwe_instance_solve",
            "artifact_paths": [
                "examples/public_runs/lattice_downscaled_lwe_instance_solve_v0/README.md",
                "examples/public_runs/lattice_downscaled_lwe_instance_solve_v0/run_ledger.json",
                "examples/public_runs/lattice_downscaled_lwe_instance_solve_v0/trace_public.jsonl",
                "examples/public_runs/lattice_downscaled_lwe_instance_solve_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    (
                        "examples/public_runs/lattice_downscaled_lwe_instance_solve_v0/"
                        "README.md"
                    ),
                    (
                        "examples/public_runs/lattice_downscaled_lwe_instance_solve_v0/"
                        "run_ledger.json"
                    ),
                    (
                        "examples/public_runs/lattice_downscaled_lwe_instance_solve_v0/"
                        "trace_public.jsonl"
                    ),
                    (
                        "examples/public_runs/lattice_downscaled_lwe_instance_solve_v0/"
                        "MANIFEST.sha256"
                    ),
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "lattice_downscaled_mlwe_instance_solve_v0": {
            "id": "lattice_downscaled_mlwe_instance_solve_v0",
            "family": "MLWE",
            "benchmark_path": "benchmarks/lattice_downscaled_mlwe_instance_solve",
            "artifact_paths": [
                "examples/public_runs/lattice_downscaled_mlwe_instance_solve_v0/README.md",
                "examples/public_runs/lattice_downscaled_mlwe_instance_solve_v0/run_ledger.json",
                "examples/public_runs/lattice_downscaled_mlwe_instance_solve_v0/trace_public.jsonl",
                "examples/public_runs/lattice_downscaled_mlwe_instance_solve_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    (
                        "examples/public_runs/"
                        "lattice_downscaled_mlwe_instance_solve_v0/README.md"
                    ),
                    (
                        "examples/public_runs/"
                        "lattice_downscaled_mlwe_instance_solve_v0/run_ledger.json"
                    ),
                    (
                        "examples/public_runs/"
                        "lattice_downscaled_mlwe_instance_solve_v0/trace_public.jsonl"
                    ),
                    (
                        "examples/public_runs/"
                        "lattice_downscaled_mlwe_instance_solve_v0/MANIFEST.sha256"
                    ),
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "lattice_mlwe_downscaled_v0": {
            "id": "lattice_mlwe_downscaled_v0",
            "family": "MLWE",
            "benchmark_path": "benchmarks/lattice_mlkem_like",
            "artifact_paths": [
                "examples/public_runs/lattice_mlwe_downscaled_v0/README.md",
                "examples/public_runs/lattice_mlwe_downscaled_v0/run_ledger.json",
                "examples/public_runs/lattice_mlwe_downscaled_v0/trace_public.jsonl",
                "examples/public_runs/lattice_mlwe_downscaled_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/lattice_mlwe_downscaled_v0/README.md",
                    "examples/public_runs/lattice_mlwe_downscaled_v0/run_ledger.json",
                    (
                        "examples/public_runs/lattice_mlwe_downscaled_v0/"
                        "trace_public.jsonl"
                    ),
                    "examples/public_runs/lattice_mlwe_downscaled_v0/MANIFEST.sha256",
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "lattice_toy_lwe_v0": {
            "id": "lattice_toy_lwe_v0",
            "family": "LWE",
            "benchmark_path": "benchmarks/lattice_toy_lwe",
            "artifact_paths": [
                "examples/public_runs/lattice_toy_lwe_v0/README.md",
                "examples/public_runs/lattice_toy_lwe_v0/run_ledger.json",
                "examples/public_runs/lattice_toy_lwe_v0/trace_public.jsonl",
                "examples/public_runs/lattice_toy_lwe_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/lattice_toy_lwe_v0/README.md",
                    "examples/public_runs/lattice_toy_lwe_v0/run_ledger.json",
                    "examples/public_runs/lattice_toy_lwe_v0/trace_public.jsonl",
                    "examples/public_runs/lattice_toy_lwe_v0/MANIFEST.sha256",
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "multivariate_toy_minrank_v0": {
            "id": "multivariate_toy_minrank_v0",
            "family": "MULTIVARIATE",
            "benchmark_path": "benchmarks/multivariate_toy_minrank",
            "artifact_paths": [
                "examples/public_runs/multivariate_toy_minrank_v0/README.md",
                "examples/public_runs/multivariate_toy_minrank_v0/run_ledger.json",
                "examples/public_runs/multivariate_toy_minrank_v0/trace_public.jsonl",
                "examples/public_runs/multivariate_toy_minrank_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/multivariate_toy_minrank_v0/README.md",
                    (
                        "examples/public_runs/multivariate_toy_minrank_v0/"
                        "run_ledger.json"
                    ),
                    (
                        "examples/public_runs/multivariate_toy_minrank_v0/"
                        "trace_public.jsonl"
                    ),
                    (
                        "examples/public_runs/multivariate_toy_minrank_v0/"
                        "MANIFEST.sha256"
                    ),
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "multivariate_toy_mq_v0": {
            "id": "multivariate_toy_mq_v0",
            "family": "MULTIVARIATE",
            "benchmark_path": "benchmarks/multivariate_toy_mq",
            "artifact_paths": [
                "examples/public_runs/multivariate_toy_mq_v0/README.md",
                "examples/public_runs/multivariate_toy_mq_v0/run_ledger.json",
                "examples/public_runs/multivariate_toy_mq_v0/trace_public.jsonl",
                "examples/public_runs/multivariate_toy_mq_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/multivariate_toy_mq_v0/README.md",
                    "examples/public_runs/multivariate_toy_mq_v0/run_ledger.json",
                    "examples/public_runs/multivariate_toy_mq_v0/trace_public.jsonl",
                    "examples/public_runs/multivariate_toy_mq_v0/MANIFEST.sha256",
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "multivariate_toy_uov_v0": {
            "id": "multivariate_toy_uov_v0",
            "family": "MULTIVARIATE",
            "benchmark_path": "benchmarks/multivariate_toy_uov",
            "artifact_paths": [
                "examples/public_runs/multivariate_toy_uov_v0/README.md",
                "examples/public_runs/multivariate_toy_uov_v0/run_ledger.json",
                "examples/public_runs/multivariate_toy_uov_v0/trace_public.jsonl",
                "examples/public_runs/multivariate_toy_uov_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                artifact_path: hashlib.sha256(
                    Path(artifact_path).read_bytes()
                ).hexdigest()
                for artifact_path in [
                    "examples/public_runs/multivariate_toy_uov_v0/README.md",
                    "examples/public_runs/multivariate_toy_uov_v0/run_ledger.json",
                    "examples/public_runs/multivariate_toy_uov_v0/trace_public.jsonl",
                    "examples/public_runs/multivariate_toy_uov_v0/MANIFEST.sha256",
                ]
            },
            "security_claim": False,
            "publishes_private_candidates": False,
        },
    }

    for surface in surfaces.values():
        assert surface["public"] is True
        assert surface["publishes_private_candidates"] is False
        assert surface["review_required_before_publish"] is True
        assert surface["security_claim"] is False

    assert (
        "uv run agades-pqc publication-manifest --out "
        "docs/publication_manifest.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc publication-manifest-verify --manifest "
        "docs/publication_manifest.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc public-benchmark-manifest --out "
        "docs/public_benchmark_manifest.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc public-benchmark-verify --manifest "
        "docs/public_benchmark_manifest.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc public-run-export --out public/run_export"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc public-run-export-verify --export public/run_export"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc source-catalog-verify --catalog "
        "docs/source_catalog.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc benchmark-source-verify --contracts "
        "docs/benchmark_source_contracts.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc family-registry-manifest-verify --manifest "
        "docs/family_registry_manifest.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc family-plugin-manifest-verify --manifest "
        "docs/family_plugin_manifest.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc hf-publication-handoff-verify --handoff "
        "docs/huggingface_publication_handoff.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc prime-publication-handoff-verify --handoff "
        "docs/prime_publication_handoff.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc prime-speedrun-handoff-verify --handoff "
        "docs/prime_speedrun_handoff.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc nvidia-publication-handoff-verify --handoff "
        "docs/nvidia_publication_handoff.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc family-support-verify --matrix "
        "docs/family_support_matrix.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc lattice-estimator-baseline-contracts-verify "
        "--contracts docs/lattice_estimator_baseline_contracts.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc private-run-policy --out docs/private_run_policy.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc private-run-policy-verify --policy "
        "docs/private_run_policy.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json"
    ) in manifest["release_gates"]


def test_committed_publication_manifest_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "publication_manifest.json"
    committed = Path("docs/publication_manifest.json")

    write_publication_manifest(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_publication_manifest_verify_accepts_committed_manifest() -> None:
    verifier = getattr(publication_manifest, "verify_publication_manifest", None)
    assert verifier is not None

    result = verifier(Path("docs/publication_manifest.json"))

    assert result == {
        "schema_version": "agades.pqc.publication_manifest_verification.v1",
        "manifest_path": "docs/publication_manifest.json",
        "accepted": True,
        "summary": {
            "credentialed_surfaces": [
                "huggingface-collection",
                "huggingface-dataset",
                "huggingface-space",
                "prime-verifiers-environment",
            ],
            "failure_count": 0,
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
                "surface_artifact_digests": 64,
            "surfaces": 6,
        },
        "failures": [],
    }


def test_publication_manifest_verify_rejects_security_claim(
    tmp_path: Path,
) -> None:
    verifier = getattr(publication_manifest, "verify_publication_manifest", None)
    assert verifier is not None

    out = tmp_path / "publication_manifest.json"
    manifest = build_publication_manifest()
    manifest["safety"]["security_claim"] = True
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verifier(out)

    assert result["accepted"] is False
    assert "Publication manifest is not in sync." in result["failures"]
    assert "Publication manifest advertises a security claim." in result["failures"]


def test_publication_manifest_verify_rejects_platform_family_support_drift(
    tmp_path: Path,
) -> None:
    verifier = getattr(publication_manifest, "verify_publication_manifest", None)
    assert verifier is not None

    out = tmp_path / "publication_manifest.json"
    manifest = build_publication_manifest()
    manifest["family_support"]["platform_support"][
        "missing_claim_review_gate"
    ] = ["nvidia"]
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verifier(out)

    assert result["accepted"] is False
    assert result["summary"]["platforms_with_family_claim_review_gate"] == 3
    assert result["failures"] == [
        "Publication manifest is not in sync.",
        "Publication manifest platform family-support gates are incomplete.",
    ]


def test_publication_manifest_discovers_public_run_bundles(tmp_path: Path) -> None:
    _write_placeholder_surface_artifacts(tmp_path)
    bundle_dir = tmp_path / "examples" / "public_runs" / "custom_public_run_v0"
    benchmark_dir = tmp_path / "benchmarks" / "custom_public_run"
    bundle_dir.mkdir(parents=True)
    benchmark_dir.mkdir(parents=True)
    (bundle_dir / "README.md").write_text("public bundle\n", encoding="utf-8")
    (bundle_dir / "trace_public.jsonl").write_text("{}\n", encoding="utf-8")
    (bundle_dir / "MANIFEST.sha256").write_text(
        "0" * 64 + "  README.md\n",
        encoding="utf-8",
    )
    (bundle_dir / "run_ledger.json").write_text(
        json.dumps(
            {
                "schema_version": "agades.pqc.public_run_ledger.v1",
                "entries": [
                    {
                        "run_id": "custom_public_run",
                        "target_family": "HASH_BASED",
                        "redacted": False,
                    }
                ],
                "summary": {"by_family": {"HASH_BASED": 1}},
                "safety": {"security_claim": False},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = build_publication_manifest(root=tmp_path)

    assert manifest["public_run_bundles"] == [
        {
            "id": "custom_public_run_v0",
            "family": "HASH_BASED",
            "benchmark_path": "benchmarks/custom_public_run",
            "artifact_paths": [
                "examples/public_runs/custom_public_run_v0/README.md",
                "examples/public_runs/custom_public_run_v0/run_ledger.json",
                "examples/public_runs/custom_public_run_v0/trace_public.jsonl",
                "examples/public_runs/custom_public_run_v0/MANIFEST.sha256",
            ],
            "artifact_sha256": {
                "examples/public_runs/custom_public_run_v0/README.md": (
                    hashlib.sha256((bundle_dir / "README.md").read_bytes()).hexdigest()
                ),
                "examples/public_runs/custom_public_run_v0/run_ledger.json": (
                    hashlib.sha256(
                        (bundle_dir / "run_ledger.json").read_bytes()
                    ).hexdigest()
                ),
                "examples/public_runs/custom_public_run_v0/trace_public.jsonl": (
                    hashlib.sha256(
                        (bundle_dir / "trace_public.jsonl").read_bytes()
                    ).hexdigest()
                ),
                "examples/public_runs/custom_public_run_v0/MANIFEST.sha256": (
                    hashlib.sha256(
                        (bundle_dir / "MANIFEST.sha256").read_bytes()
                    ).hexdigest()
                ),
            },
            "publishes_private_candidates": False,
            "security_claim": False,
        }
    ]


def test_publication_manifest_requires_surface_artifacts(tmp_path: Path) -> None:
    with pytest.raises(
        FileNotFoundError,
        match="Publication manifest references missing artifact",
    ):
        build_publication_manifest(root=tmp_path)


def test_publication_manifest_cli_writes_manifest(tmp_path: Path) -> None:
    out = tmp_path / "publication_manifest.json"

    result = CliRunner().invoke(app, ["publication-manifest", "--out", str(out)])

    assert result.exit_code == 0
    assert f"publication_manifest={out}" in result.output
    assert json.loads(out.read_text())["schema_version"] == (
        "agades.pqc.publication_manifest.v1"
    )


def test_publication_manifest_verify_cli_accepts_current_manifest() -> None:
    result = CliRunner().invoke(
        app,
        [
            "publication-manifest-verify",
            "--manifest",
            "docs/publication_manifest.json",
        ],
    )

    assert result.exit_code == 0
    assert "agades.pqc.publication_manifest_verification.v1" in result.output
    assert '"accepted": true' in result.output
