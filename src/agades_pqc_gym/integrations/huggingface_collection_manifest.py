from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.family_support import (
    summarize_family_support_matrix,
)
from agades_pqc_gym.integrations.public_private_boundary import (
    build_public_private_boundary,
    redaction_summary_fields,
    verify_public_private_boundary,
)
from agades_pqc_gym.integrations.source_catalog import summarize_source_catalog_scope

HF_COLLECTION_MANIFEST_SCHEMA = "agades.pqc.hf_collection_manifest.v1"
HF_COLLECTION_MANIFEST_VERIFICATION_SCHEMA = (
    "agades.pqc.hf_collection_manifest_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
_EXPECTED_ENTRY_IDS = [
    "github-repository",
    "huggingface-dataset",
    "huggingface-space",
    "benchmark-card",
    "source-map",
    "public-benchmark-v0",
    "public-run-export",
]
_EXPECTED_FALSE_SAFETY_FLAGS = (
    "contains_private_traces",
    "publishes_private_candidates",
    "arbitrary_code_execution",
    "live_targeting",
    "security_claim",
)
_REQUIRED_RELEASE_GATES = (
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
)


def build_huggingface_collection_manifest(
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    dataset_info = _read_json(project_root / "hf" / "dataset" / "dataset_info.json")
    space_manifest = _read_json(project_root / "hf" / "space_manifest.json")
    public_benchmark = _read_json(
        project_root / "docs" / "public_benchmark_manifest.json"
    )
    public_run_export = _read_json(
        project_root / "public" / "run_export" / "manifest.json"
    )
    source_catalog = _read_json(project_root / "docs" / "source_catalog.json")
    family_support_matrix = _read_json(
        project_root / "docs" / "family_support_matrix.json"
    )

    return {
        "schema_version": HF_COLLECTION_MANIFEST_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "package": "agades_pqc_gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
        },
        "collection": {
            "suggested_title": "Agades PQC Gym",
            "suggested_slug": "agades/pqc-gym",
            "publication_status": "local_manifest_ready_review_required",
            "public_push_requires_review": True,
        },
        "entries": [
            _github_repository_entry(),
            _dataset_entry(dataset_info),
            _space_entry(space_manifest),
            _benchmark_card_entry(),
            _source_map_entry(source_catalog),
            _public_benchmark_entry(public_benchmark),
            _public_run_export_entry(public_run_export),
        ],
        "family_support": summarize_family_support_matrix(family_support_matrix),
        "source_catalog_scope": summarize_source_catalog_scope(source_catalog),
        "public_private_boundary": build_public_private_boundary(project_root),
        "safety": {
            "contains_private_traces": False,
            "publishes_private_candidates": False,
            "arbitrary_code_execution": False,
            "live_targeting": False,
            "security_claim": False,
            "external_publication_requires_review": True,
        },
        "release_gates": [
            *_REQUIRED_RELEASE_GATES,
        ],
    }


def write_huggingface_collection_manifest(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    manifest = build_huggingface_collection_manifest(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_huggingface_collection_manifest(
    manifest_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    manifest = _read_huggingface_collection_manifest(
        manifest_path,
        project_root,
        failures,
    )
    expected = build_huggingface_collection_manifest(root=project_root)

    if manifest != expected:
        failures.append("Hugging Face Collection manifest is not in sync.")

    _verify_project_metadata(manifest, failures)
    _verify_collection_metadata(manifest, failures)
    _verify_entries(project_root, manifest, failures)
    _verify_family_support(manifest, failures)
    _verify_source_catalog_scope(manifest, failures)
    _verify_public_private_boundary(manifest, failures)
    _verify_safety(manifest, failures)
    _verify_release_gates(manifest, failures)

    return _verification_result(manifest_path, manifest, failures)


def _read_huggingface_collection_manifest(
    manifest_path: Path,
    root: Path,
    failures: list[str],
) -> dict[str, Any]:
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(
            f"Hugging Face Collection manifest is missing: {manifest_path}."
        )
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Hugging Face Collection manifest is invalid JSON at line {exc.lineno}."
        )
        return {}

    if not isinstance(payload, dict):
        failures.append("Hugging Face Collection manifest must be a JSON object.")
        return {}
    return payload


def _verify_project_metadata(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    if manifest.get("schema_version") != HF_COLLECTION_MANIFEST_SCHEMA:
        failures.append(
            "Hugging Face Collection manifest schema_version must be "
            f"{HF_COLLECTION_MANIFEST_SCHEMA}."
        )
    project = manifest.get("project")
    if not isinstance(project, dict):
        failures.append("Hugging Face Collection manifest project must be an object.")
        return
    expected_project = {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    for key, expected in expected_project.items():
        if project.get(key) != expected:
            failures.append(
                f"Hugging Face Collection manifest project.{key} is incorrect."
            )


def _verify_collection_metadata(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    collection = manifest.get("collection")
    if not isinstance(collection, dict):
        failures.append(
            "Hugging Face Collection manifest collection must be an object."
        )
        return
    if collection.get("suggested_title") != "Agades PQC Gym":
        failures.append("Hugging Face Collection title drifted.")
    if collection.get("suggested_slug") != "agades/pqc-gym":
        failures.append("Hugging Face Collection slug drifted.")
    if (
        collection.get("publication_status")
        != "local_manifest_ready_review_required"
    ):
        failures.append("Hugging Face Collection publication status drifted.")
    if collection.get("public_push_requires_review") is not True:
        failures.append("Hugging Face Collection lacks public push review gate.")


def _verify_entries(
    root: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        failures.append("Hugging Face Collection entries must be a list.")
        return
    entry_ids = [
        entry.get("id")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    ]
    if entry_ids != _EXPECTED_ENTRY_IDS:
        failures.append("Hugging Face Collection entries drifted.")
    review_required_entries = 0
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            failures.append("Hugging Face Collection entries must be objects.")
            continue
        if entry.get("review_required_before_publish") is True:
            review_required_entries += 1
        _verify_entry_shape(index, entry, failures)
        _verify_entry_paths(root, entry, failures)
    if review_required_entries != len(_EXPECTED_ENTRY_IDS):
        failures.append("Hugging Face Collection entries must all require review.")


def _verify_entry_shape(
    index: int,
    entry: dict[str, Any],
    failures: list[str],
) -> None:
    entry_id = entry.get("id")
    if entry_id not in _EXPECTED_ENTRY_IDS:
        failures.append(f"Hugging Face Collection entry[{index}] id is unsupported.")
    for field in ("kind", "platform", "requires_credentials"):
        if field not in entry:
            failures.append(
                f"Hugging Face Collection entry {entry_id} is missing {field}."
            )


def _verify_entry_paths(
    root: Path,
    entry: dict[str, Any],
    failures: list[str],
) -> None:
    for path_field in ("local_path", "card_path", "public_benchmark_manifest"):
        candidate = entry.get(path_field)
        if isinstance(candidate, str) and not (root / candidate).exists():
            failures.append(
                "Hugging Face Collection entry points to missing "
                f"{path_field}: {candidate}."
            )


def _verify_family_support(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    family_support = manifest.get("family_support")
    if not isinstance(family_support, dict):
        failures.append(
            "Hugging Face Collection manifest family_support must be an object."
        )
        return
    if family_support.get("review_required_before_claims") is not True:
        failures.append(
            "Hugging Face Collection family support must require review before claims."
        )


def _verify_source_catalog_scope(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    scope = manifest.get("source_catalog_scope")
    if not isinstance(scope, dict):
        failures.append(
            "Hugging Face Collection source_catalog_scope must be an object."
        )
        return
    if scope.get("non_lattice_toy_operator_security_claims") != 0:
        failures.append(
            "Hugging Face Collection source catalog scope must not contain "
            "non-lattice toy security claims."
        )
    if scope.get("non_lattice_toy_evaluator_count") != scope.get("source_count"):
        failures.append(
            "Hugging Face Collection source catalog scope must cover every source."
        )
    if scope.get("non_lattice_toy_operator_variant_count") != scope.get(
        "source_count"
    ):
        failures.append(
            "Hugging Face Collection source catalog operator scope must cover every "
            "source."
        )


def _verify_public_private_boundary(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    public_private_boundary = manifest.get("public_private_boundary")
    if not isinstance(public_private_boundary, dict):
        failures.append(
            "Hugging Face Collection public_private_boundary must be an object."
        )
        return
    verify_public_private_boundary(
        public_private_boundary,
        failures,
        label="Hugging Face Collection",
    )


def _verify_safety(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        failures.append("Hugging Face Collection manifest safety must be an object.")
        return
    for flag in _EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            if flag == "contains_private_traces":
                failures.append("Hugging Face Collection may expose private traces.")
            elif flag == "publishes_private_candidates":
                failures.append(
                    "Hugging Face Collection may publish private candidates."
                )
            elif flag == "security_claim":
                failures.append("Hugging Face Collection advertises a security claim.")
            elif flag == "arbitrary_code_execution":
                failures.append(
                    "Hugging Face Collection advertises arbitrary execution."
                )
            else:
                failures.append(
                    f"Hugging Face Collection safety.{flag} must be false."
                )
    if safety.get("external_publication_requires_review") is not True:
        failures.append("Hugging Face Collection lacks external review gate.")


def _verify_release_gates(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    release_gates = manifest.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append("Hugging Face Collection release_gates must be a list.")
        return
    for required_gate in _REQUIRED_RELEASE_GATES:
        if required_gate not in release_gates:
            failures.append(
                f"Hugging Face Collection release gate missing: {required_gate}"
            )


def _verification_result(
    manifest_path: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    collection = manifest.get("collection", {})
    if not isinstance(collection, dict):
        collection = {}
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        entries = []
    safety = manifest.get("safety", {})
    if not isinstance(safety, dict):
        safety = {}
    family_support = manifest.get("family_support", {})
    if not isinstance(family_support, dict):
        family_support = {}
    source_catalog_scope = manifest.get("source_catalog_scope", {})
    if not isinstance(source_catalog_scope, dict):
        source_catalog_scope = {}
    public_private_boundary = manifest.get("public_private_boundary", {})
    if not isinstance(public_private_boundary, dict):
        public_private_boundary = {}
    entry_ids = [
        entry.get("id")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    ]
    credentialed_entries = sorted(
        entry["id"]
        for entry in entries
        if isinstance(entry, dict)
        and isinstance(entry.get("id"), str)
        and entry.get("requires_credentials") is True
    )
    review_required_entries = sum(
        1
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("review_required_before_publish") is True
    )
    redaction_summary = redaction_summary_fields(public_private_boundary)
    return {
        "schema_version": HF_COLLECTION_MANIFEST_VERIFICATION_SCHEMA,
        "manifest_path": manifest_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "contains_private_traces": safety.get("contains_private_traces"),
            "credentialed_entries": credentialed_entries,
            "entries": entry_ids,
            "entry_count": len(entries),
            "external_publication_requires_review": safety.get(
                "external_publication_requires_review"
            ),
            "families_with_future_reviewed_adapters": _list_count(
                family_support.get("families_with_future_reviewed_adapters")
            ),
            "failure_count": len(failures),
            "family_count": family_support.get("family_count"),
            "non_lattice_toy_evaluator_count": source_catalog_scope.get(
                "non_lattice_toy_evaluator_count"
            ),
            "non_lattice_toy_operator_security_claims": (
                source_catalog_scope.get("non_lattice_toy_operator_security_claims")
            ),
            "non_lattice_toy_operator_variant_count": source_catalog_scope.get(
                "non_lattice_toy_operator_variant_count"
            ),
            "public_push_requires_review": collection.get(
                "public_push_requires_review"
            ),
            **redaction_summary,
            "review_required_before_claims": family_support.get(
                "review_required_before_claims"
            ),
            "review_required_entries": review_required_entries,
            "security_claim": safety.get("security_claim"),
            "suggested_slug": collection.get("suggested_slug"),
            "suggested_title": collection.get("suggested_title"),
        },
        "failures": failures,
    }


def _list_count(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _github_repository_entry() -> dict[str, Any]:
    return {
        "id": "github-repository",
        "kind": "repository",
        "platform": "github",
        "url": "https://github.com/AgadesTech/agades-pqc-gym",
        "local_path": ".",
        "description": "Canonical source for the Agades PQC Gym public verifier.",
        "requires_credentials": False,
        "review_required_before_publish": True,
    }


def _dataset_entry(dataset_info: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "huggingface-dataset",
        "kind": "hub_repo",
        "platform": "hugging_face",
        "repo_type": "dataset",
        "suggested_repo_id": dataset_info["dataset_name"],
        "local_path": "hf/dataset",
        "card_path": "hf/dataset_card.md",
        "attack_plan_count": dataset_info["attack_plan_count"],
        "valid_attack_plan_count": dataset_info["valid_attack_plan_count"],
        "invalid_attack_plan_count": dataset_info["invalid_attack_plan_count"],
        "task_metadata_count": dataset_info["task_metadata_count"],
        "public_run_bundles": dataset_info["public_run_bundles"],
        "requires_credentials": True,
        "review_required_before_publish": True,
    }


def _space_entry(space_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "huggingface-space",
        "kind": "hub_repo",
        "platform": "hugging_face",
        "repo_type": "space",
        "suggested_repo_id": space_manifest["space"]["suggested_space_id"],
        "local_path": "hf",
        "app_file": space_manifest["space"]["app_file"],
        "sdk": space_manifest["space"]["sdk"],
        "example_count": space_manifest["example_manifest"]["example_count"],
        "default_label": space_manifest["example_manifest"]["default_label"],
        "requires_credentials": True,
        "review_required_before_publish": True,
    }


def _benchmark_card_entry() -> dict[str, Any]:
    return {
        "id": "benchmark-card",
        "kind": "card",
        "platform": "hugging_face",
        "local_path": "hf/benchmark_card.md",
        "public_benchmark_manifest": "docs/public_benchmark_manifest.json",
        "requires_credentials": True,
        "review_required_before_publish": True,
    }


def _source_map_entry(source_catalog: dict[str, Any]) -> dict[str, Any]:
    sources = source_catalog["sources"]
    return {
        "id": "source-map",
        "kind": "artifact",
        "platform": "github",
        "local_path": "docs/source_catalog.json",
        "source_count": len(sources),
        "platforms": sorted({source["platform"] for source in sources}),
        "requires_credentials": False,
        "review_required_before_publish": True,
    }


def _public_benchmark_entry(public_benchmark: dict[str, Any]) -> dict[str, Any]:
    summary = public_benchmark["summary"]
    return {
        "id": "public-benchmark-v0",
        "kind": "artifact",
        "platform": "github",
        "local_path": "docs/public_benchmark_manifest.json",
        "bundle_count": summary["bundle_count"],
        "record_count": summary["record_count"],
        "families": summary["families"],
        "requires_credentials": False,
        "review_required_before_publish": True,
    }


def _public_run_export_entry(public_run_export: dict[str, Any]) -> dict[str, Any]:
    summary = public_run_export["summary"]
    return {
        "id": "public-run-export",
        "kind": "artifact",
        "platform": "github",
        "local_path": "public/run_export/manifest.json",
        "export_id": public_run_export["export"]["id"],
        "bundle_count": summary["bundle_count"],
        "run_count": summary["run_count"],
        "families": public_run_export["families"],
        "requires_credentials": False,
        "review_required_before_publish": True,
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Hugging Face collection input missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
