from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

PRIVATE_DATASET_CURATION_SCHEMA = "agades.pqc.private_dataset_curation.v1"
PRIVATE_DATASET_CURATION_VERIFICATION_SCHEMA = (
    "agades.pqc.private_dataset_curation_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CURATION_PATH = Path("docs/private_dataset_curation.json")
REQUIRED_CONTROLS = [
    "license_review",
    "provenance_tracking",
    "deduplication",
    "redaction",
    "contamination_audit",
]
PIPELINE_STAGE_IDS = [
    "source_license_review",
    "source_provenance_capture",
    "raw_ingest_to_private_storage",
    "deduplicate_and_normalize",
    "redact_sensitive_material",
    "contamination_audit",
    "curated_trace_export_gate",
]
SOURCES = {
    "facebookresearch_lwe_benchmarking": {
        "source": "facebookresearch/LWE-benchmarking",
        "upstream_url": "https://github.com/facebookresearch/LWE-benchmarking",
        "kind": "lwe_benchmark_source",
        "intended_private_use": "lwe_mlwe_task_generation_and_teacher_context",
        "license_review_status": "required_unverified",
        "ingestion_allowed_before_license_review": False,
    },
    "facebook_tapas": {
        "source": "facebook/TAPAS",
        "upstream_url": "https://huggingface.co/datasets/facebook/TAPAS",
        "kind": "lwe_learning_dataset",
        "intended_private_use": "lwe_trace_pedagogy_and_student_curriculum",
        "license_review_status": "required_unverified",
        "ingestion_allowed_before_license_review": False,
    },
    "pq_code_package": {
        "source": "pq-code-package",
        "upstream_url": "https://github.com/pq-code-package",
        "kind": "implementation_security_source_corpus",
        "intended_private_use": (
            "implementation_security_attackplan_context_after_review"
        ),
        "license_review_status": "required_unverified",
        "ingestion_allowed_before_license_review": False,
    },
}
PRIVATE_ROOTS = [
    "private/datasets/agades_pedagogical_rl",
    "private/reports/dataset_curation",
    "private/traces/pedagogical_rl",
]
LINKED_ARTIFACT_PATHS = {
    "source_catalog": "docs/source_catalog.json",
    "benchmark_source_contracts": "docs/benchmark_source_contracts.json",
    "private_run_policy": "docs/private_run_policy.json",
}
FORBIDDEN_PUBLIC_ARTIFACTS = [
    "private_dataset_rows",
    "raw_source_rows",
    "derived_training_rows",
    "pedagogical_rl_rollouts",
    "reviewer_annotations",
    "teacher_prompts",
    "student_prompts",
    "fine_tuning_corpora",
]


def build_private_dataset_curation(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    return {
        "schema_version": PRIVATE_DATASET_CURATION_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
        },
        "purpose": {
            "method": "pedagogical_rl",
            "target": "private_qwen3_6_27b_attackplan_trace_quality",
            "claim_boundary": (
                "curates private training traces for AttackPlan generation, "
                "validation, proof-obligation review, and critique; it does "
                "not publish data rows or assert cryptographic breaks"
            ),
        },
        "sources": copy.deepcopy(SOURCES),
        "required_controls": list(REQUIRED_CONTROLS),
        "pipeline": _pipeline(),
        "outputs": {
            "public_manifest_only": True,
            "public_rows_allowed": False,
            "public_prompts_allowed": False,
            "public_reviewer_annotations_allowed": False,
            "public_finetuning_corpus_allowed": False,
            "private_roots": list(PRIVATE_ROOTS),
            "curated_dataset_path": (
                "private/datasets/agades_pedagogical_rl/"
                "curated_attackplan_traces.jsonl"
            ),
            "provenance_manifest_path": (
                "private/reports/dataset_curation/provenance_manifest.json"
            ),
            "contamination_report_path": (
                "private/reports/dataset_curation/contamination_audit.json"
            ),
        },
        "provenance_tracking": {
            "required_fields": [
                "source",
                "upstream_url",
                "revision_or_commit",
                "retrieved_at_utc",
                "raw_content_sha256",
                "normalized_content_sha256",
                "private_storage_path",
                "license_review_id",
            ],
            "requires_per_row_source_map": True,
            "requires_hash_manifest": True,
            "requires_reproducible_transform_config": True,
        },
        "deduplication": {
            "exact_hash_deduplication": True,
            "normalized_text_deduplication": True,
            "near_duplicate_review_required": True,
            "cross_source_deduplication": True,
        },
        "redaction": {
            "remove_credentials": True,
            "remove_personal_data": True,
            "remove_unlicensed_text_spans": True,
            "strip_private_paths_from_public_metadata": True,
            "requires_redaction_report": True,
        },
        "contamination_audit": {
            "public_reference_roots": [
                "examples/attack_plans",
                "hf/dataset",
                "prime_intellect/verifiers_environment/data",
            ],
            "reject_exact_public_overlap": True,
            "reject_prompt_or_reviewer_annotation_leakage": True,
            "requires_hash_and_similarity_report": True,
            "requires_manual_review": True,
        },
        "review": {
            "launch_readiness": (
                "blocked_until_license_provenance_redaction_and_contamination_review"
            ),
            "required_reviewers": [
                "dataset_license_reviewer",
                "cryptography_domain_reviewer",
                "privacy_release_reviewer",
            ],
            "review_status": "required_unassigned",
        },
        "publication_boundary": {
            "public_artifact": DEFAULT_CURATION_PATH.as_posix(),
            "public_artifact_contains_private_rows": False,
            "forbidden_public_artifacts": list(FORBIDDEN_PUBLIC_ARTIFACTS),
            "allowed_public_artifacts": [
                "sanitized_curation_manifest",
                "aggregate_counts_after_review",
                "metadata_cards_without_rows_or_prompts",
            ],
        },
        "linked_artifacts": _linked_artifacts(project_root),
        "release_gates": [
            "uv run pytest tests/test_private_dataset_curation.py -q",
            "uv run agades-pqc private-dataset-curation --out "
            "docs/private_dataset_curation.json",
            "uv run agades-pqc private-dataset-curation-verify --curation "
            "docs/private_dataset_curation.json",
            "uv run agades-pqc source-catalog-verify --catalog "
            "docs/source_catalog.json",
            "uv run agades-pqc benchmark-source-verify --contracts "
            "docs/benchmark_source_contracts.json",
            "uv run agades-pqc private-run-policy-verify --policy "
            "docs/private_run_policy.json",
            "uv run agades-pqc ecosystem-smoke-verify --report "
            "reports/ecosystem_smoke.json",
            "uv run agades-pqc release-audit --out public/release_audit.json",
        ],
    }


def write_private_dataset_curation(
    out: Path = DEFAULT_CURATION_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    payload = build_private_dataset_curation(root=project_root)
    resolved_out = _resolve_path(out, project_root)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def verify_private_dataset_curation(
    curation_path: Path = DEFAULT_CURATION_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    curation = _read_curation(_resolve_path(curation_path, project_root), failures)
    expected = build_private_dataset_curation(root=project_root)

    if curation:
        if curation != expected:
            failures.append("Private dataset curation artifact is not in sync.")
        _verify_sources(curation, failures)
        _verify_pipeline(curation, failures)
        _verify_outputs(curation, failures)
        _verify_controls(curation, failures)
        _verify_contamination_audit(curation, failures)
        _verify_review(curation, failures)
        _verify_publication_boundary(curation, failures)
        _verify_linked_artifacts(curation, expected, project_root, failures)

    return {
        "schema_version": PRIVATE_DATASET_CURATION_VERIFICATION_SCHEMA,
        "curation_path": curation_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "sources": len(curation.get("sources", {})),
            "pipeline_stages": len(curation.get("pipeline", [])),
            "required_controls": len(curation.get("required_controls", [])),
            "linked_artifacts": len(curation.get("linked_artifacts", {})),
            "failure_count": len(failures),
        },
        "failures": failures,
    }


def _pipeline() -> list[dict[str, Any]]:
    return [
        {
            "id": "source_license_review",
            "required_control": "license_review",
            "blocks_ingestion": True,
            "private_output": (
                "private/reports/dataset_curation/license_review.json"
            ),
        },
        {
            "id": "source_provenance_capture",
            "required_control": "provenance_tracking",
            "blocks_training": True,
            "private_output": (
                "private/reports/dataset_curation/provenance_manifest.json"
            ),
        },
        {
            "id": "raw_ingest_to_private_storage",
            "required_control": "provenance_tracking",
            "public_output_allowed": False,
            "private_output": "private/datasets/agades_pedagogical_rl/raw",
        },
        {
            "id": "deduplicate_and_normalize",
            "required_control": "deduplication",
            "blocks_training": True,
            "private_output": (
                "private/reports/dataset_curation/deduplication_report.json"
            ),
        },
        {
            "id": "redact_sensitive_material",
            "required_control": "redaction",
            "blocks_training": True,
            "private_output": (
                "private/reports/dataset_curation/redaction_report.json"
            ),
        },
        {
            "id": "contamination_audit",
            "required_control": "contamination_audit",
            "blocks_training": True,
            "private_output": (
                "private/reports/dataset_curation/contamination_audit.json"
            ),
        },
        {
            "id": "curated_trace_export_gate",
            "required_control": "license_review",
            "blocks_training": True,
            "private_output": (
                "private/datasets/agades_pedagogical_rl/"
                "curated_attackplan_traces.jsonl"
            ),
        },
    ]


def _verify_sources(curation: dict[str, Any], failures: list[str]) -> None:
    sources = curation.get("sources")
    if sources != SOURCES:
        failures.append("Private dataset sources are incorrect.")
    if not isinstance(sources, dict):
        return
    for source in sources.values():
        if not isinstance(source, dict):
            failures.append("Private dataset source entries must be objects.")
            continue
        if source.get("license_review_status") != "required_unverified":
            failures.append("Dataset source license review status is incorrect.")
        if source.get("ingestion_allowed_before_license_review") is not False:
            failures.append("Dataset ingestion must wait for license review.")


def _verify_pipeline(curation: dict[str, Any], failures: list[str]) -> None:
    pipeline = curation.get("pipeline")
    if not isinstance(pipeline, list):
        failures.append("Private dataset pipeline must be a list.")
        return
    if [stage.get("id") for stage in pipeline if isinstance(stage, dict)] != (
        PIPELINE_STAGE_IDS
    ):
        failures.append("Private dataset pipeline stage sequence is incorrect.")
    for stage in pipeline:
        if not isinstance(stage, dict):
            failures.append("Private dataset pipeline stages must be objects.")
            continue
        private_output = stage.get("private_output")
        if not isinstance(private_output, str) or not private_output.startswith(
            "private/"
        ):
            failures.append("Private dataset pipeline outputs must stay private.")
        if stage.get("required_control") not in REQUIRED_CONTROLS:
            failures.append("Private dataset pipeline control is unknown.")


def _verify_outputs(curation: dict[str, Any], failures: list[str]) -> None:
    outputs = _dict_or_empty(curation.get("outputs"))
    for key in (
        "public_rows_allowed",
        "public_prompts_allowed",
        "public_reviewer_annotations_allowed",
        "public_finetuning_corpus_allowed",
    ):
        if outputs.get(key) is not False:
            if key == "public_rows_allowed":
                failures.append("Private dataset rows must never be public.")
            else:
                failures.append(f"Private dataset output {key} must be false.")
    if outputs.get("public_manifest_only") is not True:
        failures.append("Private dataset curation must expose only public metadata.")
    private_roots = outputs.get("private_roots")
    if private_roots != PRIVATE_ROOTS:
        failures.append("Private dataset roots are incorrect.")
    for key in (
        "curated_dataset_path",
        "provenance_manifest_path",
        "contamination_report_path",
    ):
        value = outputs.get(key)
        if not isinstance(value, str) or not value.startswith("private/"):
            failures.append(f"Private dataset output path {key} must stay private.")


def _verify_controls(curation: dict[str, Any], failures: list[str]) -> None:
    if curation.get("required_controls") != REQUIRED_CONTROLS:
        failures.append("Private dataset required controls are incorrect.")
    provenance = _dict_or_empty(curation.get("provenance_tracking"))
    if provenance.get("requires_per_row_source_map") is not True:
        failures.append("Private dataset provenance must track per-row source maps.")
    if provenance.get("requires_hash_manifest") is not True:
        failures.append("Private dataset provenance must require hash manifests.")
    deduplication = _dict_or_empty(curation.get("deduplication"))
    if deduplication.get("cross_source_deduplication") is not True:
        failures.append("Private dataset deduplication must be cross-source.")
    redaction = _dict_or_empty(curation.get("redaction"))
    if redaction.get("requires_redaction_report") is not True:
        failures.append("Private dataset redaction report is required.")


def _verify_contamination_audit(
    curation: dict[str, Any],
    failures: list[str],
) -> None:
    audit = _dict_or_empty(curation.get("contamination_audit"))
    if audit.get("public_reference_roots") != [
        "examples/attack_plans",
        "hf/dataset",
        "prime_intellect/verifiers_environment/data",
    ]:
        failures.append("Private dataset contamination reference roots are incorrect.")
    for key in (
        "reject_exact_public_overlap",
        "reject_prompt_or_reviewer_annotation_leakage",
        "requires_hash_and_similarity_report",
        "requires_manual_review",
    ):
        if audit.get(key) is not True:
            failures.append(f"Private dataset contamination audit {key} must be true.")


def _verify_review(curation: dict[str, Any], failures: list[str]) -> None:
    review = _dict_or_empty(curation.get("review"))
    if review.get("launch_readiness") != (
        "blocked_until_license_provenance_redaction_and_contamination_review"
    ):
        failures.append("Private dataset curation launch readiness is incorrect.")
    if review.get("review_status") != "required_unassigned":
        failures.append("Private dataset curation review status is incorrect.")
    if review.get("required_reviewers") != [
        "dataset_license_reviewer",
        "cryptography_domain_reviewer",
        "privacy_release_reviewer",
    ]:
        failures.append("Private dataset curation reviewers are incorrect.")


def _verify_publication_boundary(
    curation: dict[str, Any],
    failures: list[str],
) -> None:
    boundary = _dict_or_empty(curation.get("publication_boundary"))
    if boundary.get("public_artifact_contains_private_rows") is not False:
        failures.append("Private dataset public artifact must not contain rows.")
    if boundary.get("forbidden_public_artifacts") != FORBIDDEN_PUBLIC_ARTIFACTS:
        failures.append("Private dataset forbidden public artifacts are incorrect.")


def _verify_linked_artifacts(
    curation: dict[str, Any],
    expected: dict[str, Any],
    root: Path,
    failures: list[str],
) -> None:
    linked_artifacts = curation.get("linked_artifacts")
    if not isinstance(linked_artifacts, dict):
        failures.append("Private dataset linked_artifacts must be an object.")
        return
    if linked_artifacts != expected.get("linked_artifacts"):
        failures.append("Private dataset linked artifact hashes are not in sync.")
    for name, artifact in linked_artifacts.items():
        if not isinstance(artifact, dict):
            failures.append(f"Private dataset linked artifact {name} must be object.")
            continue
        path = artifact.get("path")
        if not isinstance(path, str) or not path:
            failures.append(f"Private dataset linked artifact {name} is missing path.")
            continue
        if not (root / path).is_file():
            failures.append(f"Private dataset linked artifact is missing: {path}.")
        if artifact.get("sha256") is None:
            failures.append(
                f"Private dataset linked artifact {name} is missing SHA-256."
            )


def _linked_artifacts(root: Path) -> dict[str, dict[str, str | None]]:
    return {
        name: {
            "path": path,
            "sha256": _file_sha256(root / path),
        }
        for name, path in LINKED_ARTIFACT_PATHS.items()
    }


def _read_curation(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Private dataset curation artifact is missing: {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Private dataset curation artifact is invalid JSON at line {exc.lineno}."
        )
        return {}
    if not isinstance(payload, dict):
        failures.append("Private dataset curation artifact must be a JSON object.")
        return {}
    return payload


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
