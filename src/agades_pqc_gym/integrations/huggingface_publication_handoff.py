from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.family_support import (
    build_family_support_matrix,
    summarize_family_support_matrix,
)
from agades_pqc_gym.integrations.huggingface_collection_manifest import (
    verify_huggingface_collection_manifest,
)
from agades_pqc_gym.integrations.huggingface_dataset import (
    verify_huggingface_dataset_bundle,
)
from agades_pqc_gym.integrations.huggingface_space_manifest import (
    verify_huggingface_space_manifest,
)
from agades_pqc_gym.integrations.source_catalog import (
    build_source_catalog,
    summarize_source_catalog_scope,
)

HF_PUBLICATION_HANDOFF_SCHEMA = "agades.pqc.hf_publication_handoff.v1"
HF_PUBLICATION_HANDOFF_VERIFICATION_SCHEMA = (
    "agades.pqc.hf_publication_handoff_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
PROJECT = {
    "name": "Agades PQC Gym",
    "package": "agades_pqc_gym",
    "cli": "agades-pqc",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
}
RELEASE_PLAN_PATH = Path("docs/HUGGINGFACE_RELEASE_PLAN.md")
LOCAL_ARTIFACT_PATHS = [
    "hf/dataset/README.md",
    "hf/dataset/dataset_info.json",
    "hf/dataset/attack_plans.jsonl",
    "hf/dataset/task_metadata.jsonl",
    "hf/dataset/verifier_outputs.jsonl",
    "hf/dataset/MANIFEST.sha256",
    "hf/app.py",
    "hf/requirements.txt",
    "hf/space_README.md",
    "hf/space_manifest.json",
    "hf/dataset_card.md",
    "hf/benchmark_card.md",
    "hf/collection_manifest.json",
    "docs/source_catalog.json",
    "docs/public_benchmark_manifest.json",
    "public/run_export/manifest.json",
    RELEASE_PLAN_PATH.as_posix(),
]
PUBLICATION_COMMANDS = {
    "dataset_private_create": (
        "hf repos create <owner>/pqc-gym-toy --type=dataset --private --exist-ok"
    ),
    "dataset_upload": (
        "hf upload <owner>/pqc-gym-toy hf/dataset . --repo-type=dataset "
        '--commit-message "Sync Agades PQC Gym dataset"'
    ),
    "space_private_create": (
        "hf repos create <owner>/pqc-gym --type=space --space-sdk gradio "
        "--private --exist-ok"
    ),
    "space_upload": (
        "hf upload <owner>/pqc-gym hf . --repo-type=space "
        '--commit-message "Sync Agades PQC Gym Space"'
    ),
    "collection_manual_review_required": True,
}
SOURCE_ANCHORS = [
    {
        "id": "agades-hf-dataset",
        "source_catalog_required": True,
        "current_use": "current_public_artifact",
    },
    {
        "id": "agades-hf-space",
        "source_catalog_required": True,
        "current_use": "current_public_gradio_space_contract",
    },
    {
        "id": "agades-hf-collection",
        "source_catalog_required": True,
        "current_use": "current_public_collection_contract",
    },
    {
        "id": "hf-post-quantum-crypto-en",
        "source_catalog_required": True,
        "current_use": "future_pqc_instruction_eval_seed",
    },
    {
        "id": "hf-post-quantum-crypto-fr",
        "source_catalog_required": True,
        "current_use": "future_pqc_instruction_eval_seed",
    },
    {
        "id": "hf-pqc-ssl-scans",
        "source_catalog_required": True,
        "current_use": "future_pqc_migration_scoring_anchor",
    },
    {
        "id": "hf-sc2026-side-channel",
        "source_catalog_required": True,
        "current_use": "future_side_channel_research_anchor",
    },
]
SAFETY = {
    "contains_private_traces": False,
    "publishes_private_candidates": False,
    "arbitrary_code_execution": False,
    "live_targeting": False,
    "security_claim": False,
    "claims_external_publication": False,
    "credentials_present_in_artifact": False,
}
REVIEW_REQUIRED_BEFORE_PUBLISH = [
    "Confirm Hugging Face account, organization, and target namespaces.",
    "Create or update dataset and Space as private first.",
    "Run dataset, Space, Collection, release audit, and publication preflight gates.",
    (
        "Review cards for no private traces, no executable submissions, "
        "and no security claims."
    ),
    "Record external Hugging Face URLs only after credentialed review.",
]
REQUIRED_RELEASE_GATES = [
    "uv run pytest tests/test_huggingface_publication_handoff.py -q",
    "uv run agades-pqc hf-publication-handoff --out "
    "docs/huggingface_publication_handoff.json",
    "uv run agades-pqc hf-publication-handoff-verify --handoff "
    "docs/huggingface_publication_handoff.json",
    "uv run agades-pqc hf-dataset-verify --dataset hf/dataset",
    "uv run agades-pqc hf-space-manifest-verify --manifest hf/space_manifest.json",
    "uv run agades-pqc hf-collection-manifest-verify --manifest "
    "hf/collection_manifest.json",
    "uv run agades-pqc publication-preflight-verify --preflight "
    "public/publication_preflight.json",
    "uv run agades-pqc ecosystem-smoke-verify --report "
    "reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
]


def build_huggingface_publication_handoff(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    dataset_verification = verify_huggingface_dataset_bundle(
        Path("hf/dataset"),
        root=project_root,
    )
    space_verification = verify_huggingface_space_manifest(
        Path("hf/space_manifest.json"),
        root=project_root,
    )
    collection_verification = verify_huggingface_collection_manifest(
        Path("hf/collection_manifest.json"),
        root=project_root,
    )
    dataset_summary = dataset_verification["summary"]
    space_summary = space_verification["summary"]
    collection_summary = collection_verification["summary"]

    return {
        "schema_version": HF_PUBLICATION_HANDOFF_SCHEMA,
        "project": dict(PROJECT),
        "platform": {
            "ecosystem": "hugging_face",
            "handoff_status": "local_artifacts_ready_external_publication_blocked",
            "dataset_repo_type": "dataset",
            "dataset_suggested_repo_id": "agades/pqc-gym-toy",
            "space_repo_type": "space",
            "space_suggested_repo_id": "agades/pqc-gym",
            "collection_suggested_slug": "agades/pqc-gym",
            "release_plan": RELEASE_PLAN_PATH.as_posix(),
        },
        "readiness": {
            "dataset_bundle_accepted": dataset_verification["accepted"],
            "space_manifest_accepted": space_verification["accepted"],
            "collection_manifest_accepted": collection_verification["accepted"],
            "attack_plan_count": dataset_summary["attack_plan_count"],
            "valid_attack_plan_count": dataset_summary["valid_attack_plan_count"],
            "invalid_attack_plan_count": dataset_summary["invalid_attack_plan_count"],
            "task_metadata_rows": dataset_summary["task_metadata_rows"],
            "space_example_count": space_summary["example_count"],
            "collection_entry_count": collection_summary["entry_count"],
            "public_run_bundles": dataset_summary["public_run_bundle_count"],
            "requires_credentials": True,
            "credentials_checked_at_generation": False,
            "credentials_present_in_artifact": False,
            "external_publication_requires_review": True,
            "hf_hub_publication_performed": False,
        },
        "publication_commands": dict(PUBLICATION_COMMANDS),
        "source_anchors": list(SOURCE_ANCHORS),
        "family_support": summarize_family_support_matrix(
            build_family_support_matrix(root=project_root)
        ),
        "source_catalog_scope": summarize_source_catalog_scope(
            build_source_catalog()
        ),
        "local_artifacts": {
            "artifact_paths": list(LOCAL_ARTIFACT_PATHS),
            "artifact_sha256": _artifact_sha256(project_root, LOCAL_ARTIFACT_PATHS),
        },
        "safety": dict(SAFETY),
        "review_required_before_publish": list(REVIEW_REQUIRED_BEFORE_PUBLISH),
        "release_gates": list(REQUIRED_RELEASE_GATES),
    }


def write_huggingface_publication_handoff(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    handoff = build_huggingface_publication_handoff(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(handoff, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return handoff


def verify_huggingface_publication_handoff(
    handoff_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    handoff = _read_handoff(handoff_path, project_root, failures)

    if handoff:
        expected = build_huggingface_publication_handoff(root=project_root)
        if handoff != expected:
            failures.append("Hugging Face publication handoff is not in sync.")

        _verify_project(handoff, failures)
        _verify_platform(handoff, failures)
        _verify_readiness(handoff, expected["readiness"], failures)
        _verify_publication_commands(handoff, failures)
        _verify_source_anchors(handoff, failures)
        _verify_family_support(handoff, expected["family_support"], failures)
        _verify_source_catalog_scope(handoff, failures)
        _verify_local_artifacts(project_root, handoff, failures)
        _verify_safety(handoff, failures)
        _verify_review_requirements(handoff, failures)
        _verify_release_gates(handoff, failures)

    return _verification_result(handoff_path, handoff, failures)


def _read_handoff(
    handoff_path: Path,
    root: Path,
    failures: list[str],
) -> dict[str, Any]:
    path = handoff_path if handoff_path.is_absolute() else root / handoff_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Hugging Face publication handoff is missing: {handoff_path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Hugging Face publication handoff is invalid JSON at line {exc.lineno}."
        )
        return {}

    if not isinstance(payload, dict):
        failures.append("Hugging Face publication handoff must be a JSON object.")
        return {}
    return payload


def _verify_project(handoff: dict[str, Any], failures: list[str]) -> None:
    if handoff.get("schema_version") != HF_PUBLICATION_HANDOFF_SCHEMA:
        failures.append(
            "Hugging Face publication handoff schema_version must be "
            f"{HF_PUBLICATION_HANDOFF_SCHEMA}."
        )
    if handoff.get("project") != PROJECT:
        failures.append("Hugging Face publication handoff project metadata drifted.")


def _verify_platform(handoff: dict[str, Any], failures: list[str]) -> None:
    platform = handoff.get("platform")
    if not isinstance(platform, dict):
        failures.append("Hugging Face publication handoff platform must be an object.")
        return
    expected = {
        "ecosystem": "hugging_face",
        "handoff_status": "local_artifacts_ready_external_publication_blocked",
        "dataset_repo_type": "dataset",
        "dataset_suggested_repo_id": "agades/pqc-gym-toy",
        "space_repo_type": "space",
        "space_suggested_repo_id": "agades/pqc-gym",
        "collection_suggested_slug": "agades/pqc-gym",
        "release_plan": RELEASE_PLAN_PATH.as_posix(),
    }
    for key, expected_value in expected.items():
        if platform.get(key) != expected_value:
            failures.append(
                f"Hugging Face publication handoff platform.{key} drifted."
            )


def _verify_readiness(
    handoff: dict[str, Any],
    expected: dict[str, Any],
    failures: list[str],
) -> None:
    readiness = handoff.get("readiness")
    if not isinstance(readiness, dict):
        failures.append("Hugging Face publication handoff readiness must be an object.")
        return
    for key, expected_value in expected.items():
        if readiness.get(key) != expected_value:
            failures.append(f"Hugging Face handoff readiness.{key} drifted.")
    if readiness.get("dataset_bundle_accepted") is not True:
        failures.append("Hugging Face handoff dataset bundle is not accepted.")
    if readiness.get("space_manifest_accepted") is not True:
        failures.append("Hugging Face handoff Space manifest is not accepted.")
    if readiness.get("collection_manifest_accepted") is not True:
        failures.append("Hugging Face handoff Collection manifest is not accepted.")
    if readiness.get("hf_hub_publication_performed") is not False:
        failures.append("Hugging Face handoff must not claim Hub publication.")
    if readiness.get("requires_credentials") is not True:
        failures.append("Hugging Face handoff lacks credential boundary.")
    if readiness.get("credentials_checked_at_generation") is not False:
        failures.append(
            "Hugging Face handoff must not inspect credentials at generation."
        )
    if readiness.get("credentials_present_in_artifact") is not False:
        failures.append("Hugging Face handoff must not include credential evidence.")
    if readiness.get("external_publication_requires_review") is not True:
        failures.append(
            "Hugging Face handoff lacks external publication review boundary."
        )


def _verify_publication_commands(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    if handoff.get("publication_commands") != PUBLICATION_COMMANDS:
        failures.append("Hugging Face handoff publication commands drifted.")


def _verify_source_anchors(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    if handoff.get("source_anchors") != SOURCE_ANCHORS:
        failures.append("Hugging Face handoff source anchors drifted.")
    source_catalog = build_source_catalog()
    source_by_id = {source["id"]: source for source in source_catalog["sources"]}
    for anchor in SOURCE_ANCHORS:
        source = source_by_id.get(anchor["id"])
        if source is None:
            failures.append(
                f"Hugging Face source catalog anchor is missing: {anchor['id']}."
            )
        elif source.get("current_use") != anchor["current_use"]:
            failures.append(
                "Hugging Face source catalog anchor current_use drifted: "
                f"{anchor['id']}."
            )


def _verify_family_support(
    handoff: dict[str, Any],
    expected: dict[str, Any],
    failures: list[str],
) -> None:
    family_support = handoff.get("family_support")
    if not isinstance(family_support, dict):
        failures.append("Hugging Face handoff family_support must be an object.")
        return
    if family_support != expected:
        failures.append("Hugging Face handoff family_support summary drifted.")
    if family_support.get("review_required_before_claims") is not True:
        failures.append(
            "Hugging Face handoff family_support.review_required_before_claims "
            "must be true."
        )


def _verify_source_catalog_scope(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    scope = handoff.get("source_catalog_scope")
    if not isinstance(scope, dict):
        failures.append("Hugging Face handoff source_catalog_scope must be an object.")
        return
    if scope.get("non_lattice_toy_operator_security_claims") != 0:
        failures.append(
            "Hugging Face handoff source catalog scope must not contain "
            "non-lattice toy security claims."
        )
    if scope.get("non_lattice_toy_evaluator_count") != scope.get("source_count"):
        failures.append(
            "Hugging Face handoff source catalog scope must cover every source."
        )
    if scope.get("non_lattice_toy_operator_variant_count") != scope.get(
        "source_count"
    ):
        failures.append(
            "Hugging Face handoff source catalog operator scope must cover "
            "every source."
        )


def _verify_local_artifacts(
    root: Path,
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    local_artifacts = handoff.get("local_artifacts")
    if not isinstance(local_artifacts, dict):
        failures.append(
            "Hugging Face publication handoff local_artifacts must be an object."
        )
        return
    artifact_paths = local_artifacts.get("artifact_paths")
    if artifact_paths != LOCAL_ARTIFACT_PATHS:
        failures.append("Hugging Face handoff local artifact paths drifted.")
        artifact_paths = artifact_paths if isinstance(artifact_paths, list) else []
    artifact_sha256 = local_artifacts.get("artifact_sha256")
    if not isinstance(artifact_sha256, dict):
        failures.append("Hugging Face handoff artifact digest map must be an object.")
        artifact_sha256 = {}
    if set(artifact_sha256) != set(LOCAL_ARTIFACT_PATHS):
        failures.append("Hugging Face handoff artifact digest keys drifted.")
    for artifact_path in artifact_paths:
        if not isinstance(artifact_path, str):
            failures.append("Hugging Face handoff artifact path is invalid.")
            continue
        path = root / artifact_path
        if not path.is_file():
            failures.append(
                f"Hugging Face handoff artifact is missing: {artifact_path}."
            )
            continue
        expected_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if artifact_sha256.get(artifact_path) != expected_digest:
            failures.append(
                f"Hugging Face handoff artifact digest drifted: {artifact_path}."
            )


def _verify_safety(handoff: dict[str, Any], failures: list[str]) -> None:
    safety = handoff.get("safety")
    if not isinstance(safety, dict):
        failures.append("Hugging Face publication handoff safety must be an object.")
        return
    for key, expected_value in SAFETY.items():
        if safety.get(key) != expected_value:
            if key == "claims_external_publication":
                failures.append("Hugging Face handoff claims external publication.")
            elif key == "publishes_private_candidates":
                failures.append(
                    "Hugging Face handoff may publish private candidates."
                )
            elif key == "arbitrary_code_execution":
                failures.append("Hugging Face handoff advertises arbitrary execution.")
            elif key == "credentials_present_in_artifact":
                failures.append(
                    "Hugging Face handoff must not include credential evidence."
                )
            elif key == "security_claim":
                failures.append("Hugging Face handoff advertises a security claim.")
            else:
                failures.append(f"Hugging Face handoff safety.{key} drifted.")


def _verify_review_requirements(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    if (
        handoff.get("review_required_before_publish")
        != REVIEW_REQUIRED_BEFORE_PUBLISH
    ):
        failures.append("Hugging Face handoff review checklist drifted.")


def _verify_release_gates(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    release_gates = handoff.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append("Hugging Face handoff release_gates must be a list.")
        return
    for required_gate in REQUIRED_RELEASE_GATES:
        if required_gate not in release_gates:
            failures.append(
                f"Hugging Face handoff release gate missing: {required_gate}"
            )


def _verification_result(
    handoff_path: Path,
    handoff: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    readiness = handoff.get("readiness", {})
    if not isinstance(readiness, dict):
        readiness = {}
    local_artifacts = handoff.get("local_artifacts", {})
    if not isinstance(local_artifacts, dict):
        local_artifacts = {}
    source_catalog_scope = handoff.get("source_catalog_scope", {})
    if not isinstance(source_catalog_scope, dict):
        source_catalog_scope = {}
    family_support = handoff.get("family_support", {})
    if not isinstance(family_support, dict):
        family_support = {}
    artifact_paths = local_artifacts.get("artifact_paths", [])
    if not isinstance(artifact_paths, list):
        artifact_paths = []
    return {
        "schema_version": HF_PUBLICATION_HANDOFF_VERIFICATION_SCHEMA,
        "handoff_path": handoff_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "artifact_count": len(artifact_paths),
            "attack_plan_count": readiness.get("attack_plan_count"),
            "collection_entry_count": readiness.get("collection_entry_count"),
            "external_publication_requires_review": readiness.get(
                "external_publication_requires_review"
            ),
            "failure_count": len(failures),
            "family_count": family_support.get("family_count"),
            "family_support_review_required_before_claims": family_support.get(
                "review_required_before_claims"
            ),
            "implemented_families": family_support.get("implemented"),
            "non_lattice_toy_evaluator_count": source_catalog_scope.get(
                "non_lattice_toy_evaluator_count"
            ),
            "non_lattice_toy_operator_security_claims": (
                source_catalog_scope.get("non_lattice_toy_operator_security_claims")
            ),
            "non_lattice_toy_operator_variant_count": source_catalog_scope.get(
                "non_lattice_toy_operator_variant_count"
            ),
            "public_run_bundles": readiness.get("public_run_bundles"),
            "space_example_count": readiness.get("space_example_count"),
            "task_metadata_rows": readiness.get("task_metadata_rows"),
            "valid_attack_plan_count": readiness.get("valid_attack_plan_count"),
        },
        "failures": failures,
    }


def _artifact_sha256(root: Path, artifact_paths: list[str]) -> dict[str, str]:
    return {
        artifact_path: hashlib.sha256((root / artifact_path).read_bytes()).hexdigest()
        for artifact_path in artifact_paths
    }
