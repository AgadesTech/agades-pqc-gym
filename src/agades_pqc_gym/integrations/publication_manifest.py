from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.family_support import (
    summarize_family_support_matrix,
    summarize_family_support_publication_gate,
)

PUBLICATION_MANIFEST_SCHEMA = "agades.pqc.publication_manifest.v1"
PUBLICATION_MANIFEST_VERIFICATION_SCHEMA = (
    "agades.pqc.publication_manifest_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
PUBLIC_RUN_ARTIFACT_FILENAMES = (
    "README.md",
    "run_ledger.json",
    "trace_public.jsonl",
    "MANIFEST.sha256",
)
PAPER_CARD_ARTIFACT_DIR = Path("examples/paper_cards")
REVIEWED_PUBLICATION_DIGEST_EXCLUSIONS = {
    "docs/external_publication_review_packet.json": (
        "derived_from_preflight_status_and_platform_manifests"
    ),
    "docs/release_status.json": (
        "derived_from_release_audit_and_publication_manifest"
    ),
    "public/release_audit.json": "recursive_release_audit_artifact",
}
_EXPECTED_FALSE_SAFETY_FLAGS = (
    "contains_private_traces",
    "arbitrary_code_execution",
    "live_targeting",
    "security_claim",
    "publishes_private_candidates",
)
_REQUIRED_PLATFORM_FAMILY_SUPPORTS = (
    "huggingface_collection",
    "nvidia",
    "prime_intellect",
)
_REQUIRED_RELEASE_GATES = (
    "uv run pytest tests/test_publication_manifest.py -q",
    "uv run agades-pqc publication-manifest --out docs/publication_manifest.json",
    "uv run agades-pqc publication-manifest-verify --manifest "
    "docs/publication_manifest.json",
    "uv run agades-pqc public-benchmark-manifest --out "
    "docs/public_benchmark_manifest.json",
    "uv run agades-pqc public-benchmark-verify --manifest "
    "docs/public_benchmark_manifest.json",
    "uv run agades-pqc public-run-export --out public/run_export",
    "uv run agades-pqc public-run-export-verify --export public/run_export",
    "uv run agades-pqc source-catalog-verify --catalog docs/source_catalog.json",
    "uv run agades-pqc benchmark-source-verify --contracts "
    "docs/benchmark_source_contracts.json",
    "uv run agades-pqc family-registry-manifest-verify --manifest "
    "docs/family_registry_manifest.json",
    "uv run agades-pqc family-plugin-manifest-verify --manifest "
    "docs/family_plugin_manifest.json",
    "uv run agades-pqc hf-publication-handoff-verify --handoff "
    "docs/huggingface_publication_handoff.json",
    "uv run agades-pqc prime-publication-handoff-verify --handoff "
    "docs/prime_publication_handoff.json",
    "uv run agades-pqc prime-speedrun-handoff-verify --handoff "
    "docs/prime_speedrun_handoff.json",
    "uv run agades-pqc nvidia-publication-handoff-verify --handoff "
    "docs/nvidia_publication_handoff.json",
    "uv run agades-pqc family-support-verify --matrix "
    "docs/family_support_matrix.json",
    "uv run agades-pqc lattice-estimator-baseline-contracts-verify --contracts "
    "docs/lattice_estimator_baseline_contracts.json",
    "uv run agades-pqc private-run-policy --out docs/private_run_policy.json",
    "uv run agades-pqc private-run-policy-verify --policy "
    "docs/private_run_policy.json",
    "uv run agades-pqc runbook-input-manifest-verify --manifest "
    "docs/runbook_input_manifest.json",
    "uv run agades-pqc external-publication-review-packet --out "
    "docs/external_publication_review_packet.json",
    "uv run agades-pqc external-publication-review-packet-verify --packet "
    "docs/external_publication_review_packet.json",
    "uv run agades-pqc ecosystem-smoke-verify --report "
    "reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
    "uv run agades-pqc release-status --out docs/release_status.json",
)


def build_publication_manifest(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    surfaces = _surfaces(project_root)
    return {
        "schema_version": PUBLICATION_MANIFEST_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "package": "agades_pqc_gym",
            "cli": "agades-pqc",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
        },
        "family_support": _family_support_publication_gate(project_root),
        "surfaces": surfaces,
        "public_run_bundles": _public_run_bundles(project_root),
        "private_holdback": [
            "serious evolution traces",
            "private prompts and prompt-ranking policies",
            "evaluator weighting and anti-gaming heuristics",
            "unreleased candidate strategies",
            "responsible-disclosure material",
        ],
        "safety": {
            "contains_private_traces": False,
            "arbitrary_code_execution": False,
            "live_targeting": False,
            "security_claim": False,
            "publishes_private_candidates": False,
            "external_publication_requires_review": True,
        },
        "release_gates": list(_REQUIRED_RELEASE_GATES),
    }


def _surfaces(root: Path) -> list[dict[str, Any]]:
    surfaces = [
        {
            "id": "github-repository",
            "platform": "github",
            "publication_status": "draft_pr_ready",
            "requires_credentials": False,
            "public": True,
            "review_required_before_publish": True,
            "publishes_private_candidates": False,
            "security_claim": False,
            "artifact_paths": [
                "README.md",
                "docs/ARCHITECTURE.md",
                "docs/FAMILY_ADAPTERS.md",
                "docs/benchmark_source_contracts.json",
                "docs/source_catalog.json",
                "docs/family_support_matrix.json",
                "docs/family_registry_manifest.json",
                "docs/family_plugin_manifest.json",
                "docs/family_operator_catalog.json",
                "docs/runbook_input_manifest.json",
                "docs/huggingface_publication_handoff.json",
                "docs/prime_publication_handoff.json",
                "docs/prime_speedrun_handoff.json",
                "docs/nvidia_publication_handoff.json",
                "docs/lattice_estimator_manifest.json",
                "docs/lattice_estimator_baseline_contracts.json",
                "docs/public_benchmark_manifest.json",
                "public/run_export/manifest.json",
                "public/run_export/runs.jsonl",
                "public/run_export/runs.csv",
                "public/run_export/MANIFEST.sha256",
                "docs/MOAT_AND_OPEN_SOURCE_STRATEGY.md",
                *_paper_card_artifact_paths(root),
                "docs/private_run_policy.json",
                "docs/external_publication_review_packet.json",
                "docs/release_status.json",
                "public/release_audit.json",
            ],
            "artifact_digest_exclusions": {
                "docs/external_publication_review_packet.json": (
                    "derived_from_preflight_status_and_platform_manifests"
                ),
                "docs/release_status.json": (
                    "derived_from_release_audit_and_publication_manifest"
                ),
                "public/release_audit.json": "recursive_release_audit_artifact",
            },
            "smoke_gate": "github-actions-ci",
            "publish_notes": [
                "Repository is the canonical public OSS surface.",
                "Merge only after release-audit and CI pass.",
            ],
        },
        {
            "id": "huggingface-dataset",
            "platform": "hugging_face",
            "publication_status": "local_artifact_ready",
            "requires_credentials": True,
            "public": True,
            "review_required_before_publish": True,
            "publishes_private_candidates": False,
            "security_claim": False,
            "artifact_paths": [
                "hf/dataset/README.md",
                "hf/dataset/dataset_info.json",
                "hf/dataset/attack_plans.jsonl",
                "hf/dataset/task_metadata.jsonl",
                "hf/dataset/verifier_outputs.jsonl",
                "hf/dataset/MANIFEST.sha256",
            ],
            "smoke_gate": "hf-dataset-safety",
            "publish_notes": [
                "Publish only toy/schema-only AttackPlans and verifier rows.",
                "Do not publish private evolution traces or candidate strategies.",
            ],
        },
        {
            "id": "huggingface-space",
            "platform": "hugging_face",
            "publication_status": "local_artifact_ready",
            "requires_credentials": True,
            "public": True,
            "review_required_before_publish": True,
            "publishes_private_candidates": False,
            "security_claim": False,
            "artifact_paths": [
                "hf/app.py",
                "hf/requirements.txt",
                "hf/space_README.md",
                "hf/space_manifest.json",
            ],
            "smoke_gate": "hf-space-smoke",
            "publish_notes": [
                "Space demo must run on public examples only.",
                "Summary text must keep the not-a-security-claim boundary.",
            ],
        },
        {
            "id": "huggingface-collection",
            "platform": "hugging_face",
            "publication_status": "local_manifest_ready_review_required",
            "requires_credentials": True,
            "public": True,
            "review_required_before_publish": True,
            "publishes_private_candidates": False,
            "security_claim": False,
            "artifact_paths": [
                "hf/collection_manifest.json",
                "hf/dataset_card.md",
                "hf/benchmark_card.md",
                "hf/space_manifest.json",
                "docs/source_catalog.json",
                "docs/public_benchmark_manifest.json",
                "docs/huggingface_publication_handoff.json",
            ],
            "smoke_gate": "hf-collection-manifest",
            "publish_notes": [
                "Collection links the GitHub repo, toy dataset, Space, "
                "benchmark card, source map, and public benchmark manifest.",
                "Publish only after dataset and Space review are complete.",
            ],
        },
        {
            "id": "prime-verifiers-environment",
            "platform": "prime_intellect",
            "publication_status": "local_package_ready",
            "requires_credentials": True,
            "public": True,
            "review_required_before_publish": True,
            "publishes_private_candidates": False,
            "security_claim": False,
            "artifact_paths": [
                "prime_intellect/environment_card.md",
                "prime_intellect/verifier_spec.md",
                "prime_intellect/verifiers_environment/README.md",
                "prime_intellect/verifiers_environment/pyproject.toml",
                "prime_intellect/verifiers_environment/agades_pqc_verifier_env.py",
                "prime_intellect/verifiers_environment/prime_manifest.json",
                "prime_intellect/schemas/attack_plan.schema.json",
                "prime_intellect/schemas/verifier_result.schema.json",
                "prime_intellect/schemas/task_metadata.schema.json",
                "prime_intellect/schemas/schema_manifest.json",
                "docs/prime_speedrun_handoff.json",
            ],
            "smoke_gate": "prime-environment-smoke",
            "publish_notes": [
                "Environment accepts JSON AttackPlan submissions only.",
                "Prime Hub publication requires credentials and release review.",
            ],
        },
        {
            "id": "nvidia-accelerator-story",
            "platform": "nvidia",
            "publication_status": "strategy_ready_review_required",
            "requires_credentials": False,
            "public": True,
            "review_required_before_publish": True,
            "publishes_private_candidates": False,
            "security_claim": False,
            "artifact_paths": [
                "docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md",
                "nvidia/README.md",
                "nvidia/accelerator_manifest.json",
                "docs/nvidia_publication_handoff.json",
            ],
            "smoke_gate": "nvidia-manifest-safety",
            "publish_notes": [
                "Current MVP is CPU/verifier-only.",
                "GPU work remains future reviewed reproduction infrastructure.",
            ],
        },
    ]
    for surface in surfaces:
        _require_artifact_files(root, surface["artifact_paths"])
        surface["artifact_sha256"] = _artifact_sha256(
            root,
            [
                artifact_path
                for artifact_path in surface["artifact_paths"]
                if artifact_path not in surface.get("artifact_digest_exclusions", {})
            ],
        )
    return surfaces


def _paper_card_artifact_paths(root: Path) -> list[str]:
    paper_cards_root = root / PAPER_CARD_ARTIFACT_DIR
    if not paper_cards_root.is_dir():
        return []
    return sorted(
        path.relative_to(root).as_posix()
        for path in paper_cards_root.glob("*.yaml")
    )


def write_publication_manifest(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    manifest = build_publication_manifest(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_publication_manifest(
    manifest_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    manifest = _read_publication_manifest(manifest_path, failures)

    if manifest:
        expected = build_publication_manifest(root=project_root)
        if manifest != expected:
            failures.append("Publication manifest is not in sync.")

        _verify_project_metadata(manifest, failures)
        _verify_safety(manifest, failures)
        _verify_family_support(manifest, failures)
        _verify_release_gates(manifest, failures)
        summary = _verify_surfaces_and_bundles(project_root, manifest, failures)
    else:
        summary = _empty_verification_summary()

    family_support = _dict_or_empty(manifest.get("family_support"))
    platform_support = _dict_or_empty(family_support.get("platform_support"))
    summary.update(
        {
            "family_count": family_support.get("family_count"),
            "platform_family_support_family_counts_match": platform_support.get(
                "family_counts_match"
            ),
            "platform_family_support_surfaces": platform_support.get(
                "surface_count"
            ),
            "platforms_with_family_claim_review_gate": len(
                _list_or_empty(
                    platform_support.get("platforms_with_claim_review_gate")
                )
            ),
            "review_required_before_claims": family_support.get(
                "review_required_before_claims"
            ),
        }
    )
    summary["failure_count"] = len(failures)
    return {
        "schema_version": PUBLICATION_MANIFEST_VERIFICATION_SCHEMA,
        "manifest_path": manifest_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _family_support_publication_gate(root: Path) -> dict[str, Any]:
    matrix = _read_json(root / "docs" / "family_support_matrix.json")
    family_support = summarize_family_support_matrix(matrix)
    platform_family_supports = {
        "huggingface_collection": _read_json(
            root / "hf" / "collection_manifest.json"
        )["family_support"],
        "nvidia": _read_json(root / "nvidia" / "accelerator_manifest.json")[
            "family_support"
        ],
        "prime_intellect": _read_json(
            root
            / "prime_intellect"
            / "verifiers_environment"
            / "prime_manifest.json"
        )["family_support"],
    }
    return summarize_family_support_publication_gate(
        family_support,
        platform_family_supports,
        required_platforms=_REQUIRED_PLATFORM_FAMILY_SUPPORTS,
    )


def _public_run_bundles(root: Path) -> list[dict[str, Any]]:
    public_runs_root = root / "examples" / "public_runs"
    if not public_runs_root.is_dir():
        return []
    bundle_dirs = sorted(path for path in public_runs_root.iterdir() if path.is_dir())
    return [
        _public_run_bundle_entry(root, bundle_dir)
        for bundle_dir in bundle_dirs
    ]


def _public_run_bundle_entry(root: Path, bundle_dir: Path) -> dict[str, Any]:
    missing_artifacts = [
        filename
        for filename in PUBLIC_RUN_ARTIFACT_FILENAMES
        if not (bundle_dir / filename).is_file()
    ]
    if missing_artifacts:
        missing = ", ".join(missing_artifacts)
        raise FileNotFoundError(
            f"Public run bundle {bundle_dir.name} is missing: {missing}"
        )

    ledger = json.loads((bundle_dir / "run_ledger.json").read_text(encoding="utf-8"))
    entries = ledger.get("entries", [])
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"Public run bundle {bundle_dir.name} has no ledger entries.")

    run_ids = {
        entry.get("run_id")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("run_id"), str)
    }
    if len(run_ids) != 1:
        raise ValueError(
            f"Public run bundle {bundle_dir.name} must contain exactly one run_id."
        )
    run_id = next(iter(run_ids))
    benchmark_path = Path("benchmarks") / run_id
    if not (root / benchmark_path).is_dir():
        raise FileNotFoundError(
            f"Public run bundle {bundle_dir.name} benchmark is missing: "
            f"{benchmark_path.as_posix()}"
        )

    return {
        "id": bundle_dir.name,
        "family": _public_run_bundle_family(bundle_dir.name, ledger, entries),
        "benchmark_path": benchmark_path.as_posix(),
        "artifact_paths": [
            (bundle_dir / filename).relative_to(root).as_posix()
            for filename in PUBLIC_RUN_ARTIFACT_FILENAMES
        ],
        "artifact_sha256": _artifact_sha256(
            root,
            [
                (bundle_dir / filename).relative_to(root).as_posix()
                for filename in PUBLIC_RUN_ARTIFACT_FILENAMES
            ],
        ),
        "publishes_private_candidates": False,
        "security_claim": bool(ledger.get("safety", {}).get("security_claim")),
    }


def _artifact_sha256(root: Path, artifact_paths: list[str]) -> dict[str, str]:
    return {
        artifact_path: hashlib.sha256((root / artifact_path).read_bytes()).hexdigest()
        for artifact_path in artifact_paths
    }


def _read_publication_manifest(
    path: Path,
    failures: list[str],
) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Publication manifest is missing: {path.as_posix()}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"Publication manifest is invalid JSON at line {exc.lineno}.")
        return {}

    if not isinstance(payload, dict):
        failures.append("Publication manifest must be a JSON object.")
        return {}
    return payload


def _verify_project_metadata(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    if manifest.get("schema_version") != PUBLICATION_MANIFEST_SCHEMA:
        failures.append(
            "Publication manifest schema_version must be "
            f"{PUBLICATION_MANIFEST_SCHEMA}."
        )
    project = manifest.get("project")
    if not isinstance(project, dict):
        failures.append("Publication manifest project must be an object.")
        return
    expected_project = {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "cli": "agades-pqc",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    for key, expected in expected_project.items():
        if project.get(key) != expected:
            failures.append(f"Publication manifest project.{key} is incorrect.")


def _verify_safety(manifest: dict[str, Any], failures: list[str]) -> None:
    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        failures.append("Publication manifest safety must be an object.")
        return
    for flag in _EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            if flag == "contains_private_traces":
                failures.append("Publication manifest may expose private traces.")
            elif flag == "publishes_private_candidates":
                failures.append("Publication manifest may publish private candidates.")
            elif flag == "security_claim":
                failures.append("Publication manifest advertises a security claim.")
            else:
                failures.append(f"Publication manifest safety.{flag} must be false.")
    if safety.get("external_publication_requires_review") is not True:
        failures.append("Publication manifest lacks external review boundary.")


def _verify_family_support(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    family_support = _dict_or_empty(manifest.get("family_support"))
    if not family_support:
        failures.append("Publication manifest family_support must be an object.")
        return
    if family_support.get("review_required_before_claims") is not True:
        failures.append(
            "Publication manifest must keep family-support review gate."
        )
    platform_support = _dict_or_empty(family_support.get("platform_support"))
    if (
        platform_support.get("family_counts_match") is not True
        or platform_support.get("missing_claim_review_gate") != []
    ):
        failures.append(
            "Publication manifest platform family-support gates are incomplete."
        )


def _verify_release_gates(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    release_gates = manifest.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append("Publication manifest release_gates must be a list.")
        return
    for required_gate in _REQUIRED_RELEASE_GATES:
        if required_gate not in release_gates:
            failures.append(
                f"Publication manifest release gate missing: {required_gate}"
            )


def _verify_surfaces_and_bundles(
    root: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    credentialed_surfaces: list[str] = []
    review_required_surfaces = 0
    surface_artifact_digests = 0
    surface_artifact_digest_exclusions = 0
    public_run_bundle_artifacts = 0
    public_run_bundle_artifact_digests = 0

    surfaces = manifest.get("surfaces", [])
    if not isinstance(surfaces, list):
        surfaces = []
        failures.append("Publication manifest surfaces must be a list.")

    for surface in surfaces:
        if not isinstance(surface, dict):
            failures.append("Publication manifest contains a non-object surface.")
            continue
        surface_id = surface.get("id")
        if surface.get("public") is not True:
            failures.append(f"Publication surface is not public: {surface_id}")
        if surface.get("publishes_private_candidates") is not False:
            failures.append(
                f"Publication surface may publish private candidates: {surface_id}"
            )
        if surface.get("security_claim") is not False:
            failures.append(f"Publication surface makes a security claim: {surface_id}")
        if surface.get("review_required_before_publish") is True:
            review_required_surfaces += 1
        else:
            failures.append(
                f"Publication surface lacks review gate before publish: {surface_id}"
            )
        if surface.get("requires_credentials") is True:
            credentialed_surfaces.append(str(surface_id))

        artifact_paths = surface.get("artifact_paths", [])
        if not isinstance(artifact_paths, list) or not artifact_paths:
            failures.append(f"Publication surface lacks artifacts: {surface_id}")
            continue
        artifact_sha256 = surface.get("artifact_sha256", {})
        artifact_digest_exclusions = surface.get("artifact_digest_exclusions", {})
        if not isinstance(artifact_sha256, dict):
            failures.append(f"Publication surface lacks digest map: {surface_id}")
            artifact_sha256 = {}
        if not isinstance(artifact_digest_exclusions, dict):
            failures.append(
                f"Publication surface has invalid digest exclusions: {surface_id}"
            )
            artifact_digest_exclusions = {}
        digest_or_excluded_paths = set(artifact_sha256) | set(
            artifact_digest_exclusions
        )
        if digest_or_excluded_paths != set(artifact_paths):
            failures.append(
                f"Publication surface digest keys differ from artifacts: {surface_id}"
            )
        surface_artifact_digests += len(artifact_sha256)
        surface_artifact_digest_exclusions += len(artifact_digest_exclusions)
        _verify_artifact_digests(
            root=root,
            owner=f"Publication surface {surface_id}",
            artifact_paths=artifact_paths,
            artifact_sha256=artifact_sha256,
            artifact_digest_exclusions=artifact_digest_exclusions,
            failures=failures,
        )

    public_run_bundles = manifest.get("public_run_bundles", [])
    if not isinstance(public_run_bundles, list):
        public_run_bundles = []
        failures.append("Publication manifest public_run_bundles must be a list.")

    for bundle in public_run_bundles:
        if not isinstance(bundle, dict):
            failures.append("Publication manifest contains a non-object public bundle.")
            continue
        bundle_id = bundle.get("id")
        if bundle.get("publishes_private_candidates") is not False:
            failures.append(
                f"Publication public run bundle may publish private candidates: "
                f"{bundle_id}"
            )
        if bundle.get("security_claim") is not False:
            failures.append(
                f"Publication public run bundle makes a security claim: {bundle_id}"
            )
        benchmark_path = bundle.get("benchmark_path")
        if not isinstance(benchmark_path, str) or not (root / benchmark_path).is_dir():
            failures.append(
                f"Publication public run bundle benchmark is missing: {bundle_id}"
            )
        artifact_paths = bundle.get("artifact_paths", [])
        if not isinstance(artifact_paths, list) or not artifact_paths:
            failures.append(
                f"Publication public run bundle lacks artifacts: {bundle_id}"
            )
            continue
        public_run_bundle_artifacts += len(artifact_paths)
        artifact_sha256 = bundle.get("artifact_sha256", {})
        if not isinstance(artifact_sha256, dict):
            failures.append(
                f"Publication public run bundle lacks digest map: {bundle_id}"
            )
            artifact_sha256 = {}
        elif set(artifact_sha256) != set(artifact_paths):
            failures.append(
                f"Publication public run bundle digest keys differ from artifacts: "
                f"{bundle_id}"
            )
        public_run_bundle_artifact_digests += len(artifact_sha256)
        _verify_artifact_digests(
            root=root,
            owner=f"Publication public run bundle {bundle_id}",
            artifact_paths=artifact_paths,
            artifact_sha256=artifact_sha256,
            artifact_digest_exclusions={},
            failures=failures,
        )

    return {
        "credentialed_surfaces": sorted(credentialed_surfaces),
        "public_run_bundle_artifact_digests": public_run_bundle_artifact_digests,
        "public_run_bundle_artifacts": public_run_bundle_artifacts,
        "public_run_bundles": len(public_run_bundles),
        "review_required_surfaces": review_required_surfaces,
        "surface_artifact_digest_exclusions": surface_artifact_digest_exclusions,
        "surface_artifact_digests": surface_artifact_digests,
        "surfaces": len(surfaces),
    }


def _verify_artifact_digests(
    *,
    root: Path,
    owner: str,
    artifact_paths: list[Any],
    artifact_sha256: dict[str, Any],
    artifact_digest_exclusions: dict[str, Any],
    failures: list[str],
) -> None:
    for artifact_path in artifact_paths:
        if not isinstance(artifact_path, str):
            failures.append(f"{owner} has non-string artifact.")
            continue
        candidate = root / artifact_path
        if not candidate.exists():
            failures.append(f"{owner} artifact is missing: {artifact_path}")
            continue
        if artifact_path in artifact_digest_exclusions:
            if artifact_digest_exclusions[artifact_path] != (
                REVIEWED_PUBLICATION_DIGEST_EXCLUSIONS.get(artifact_path)
            ):
                failures.append(
                    f"{owner} has unreviewed digest exclusion: {artifact_path}"
                )
            continue
        expected_digest = artifact_sha256.get(artifact_path)
        actual_digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if expected_digest != actual_digest:
            failures.append(f"{owner} artifact digest mismatch: {artifact_path}")


def _empty_verification_summary() -> dict[str, Any]:
    return {
        "credentialed_surfaces": [],
        "family_count": None,
        "platform_family_support_family_counts_match": None,
        "platform_family_support_surfaces": None,
        "platforms_with_family_claim_review_gate": 0,
        "public_run_bundle_artifact_digests": 0,
        "public_run_bundle_artifacts": 0,
        "public_run_bundles": 0,
        "review_required_before_claims": None,
        "review_required_surfaces": 0,
        "surface_artifact_digest_exclusions": 0,
        "surface_artifact_digests": 0,
        "surfaces": 0,
    }


def _require_artifact_files(root: Path, artifact_paths: list[str]) -> None:
    missing_paths = [
        artifact_path
        for artifact_path in artifact_paths
        if not (root / artifact_path).is_file()
    ]
    if missing_paths:
        joined_paths = ", ".join(missing_paths)
        raise FileNotFoundError(
            f"Publication manifest references missing artifact(s): {joined_paths}"
        )


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return payload


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _public_run_bundle_family(
    bundle_id: str,
    ledger: dict[str, Any],
    entries: list[Any],
) -> str:
    summary = ledger.get("summary", {})
    by_family = summary.get("by_family") if isinstance(summary, dict) else None
    families = set(by_family) if isinstance(by_family, dict) else set()
    if not families:
        families = {
            entry.get("target_family")
            for entry in entries
            if isinstance(entry, dict) and isinstance(entry.get("target_family"), str)
        }
    if len(families) != 1:
        raise ValueError(
            f"Public run bundle {bundle_id} must contain exactly one target family."
        )
    return next(iter(families))
