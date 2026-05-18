from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

RUNBOOK_AUDIT_SCHEMA = "agades.pqc.runbook_audit.v1"
RUNBOOK_INPUT_MANIFEST_SCHEMA = "agades.pqc.runbook_input_manifest.v1"
ROOT = Path(__file__).resolve().parents[3]
PROJECT_NAME = "Agades PQC Gym"
REPOSITORY_SLUG = "agades-pqc-gym"
PACKAGE_NAME = "agades_pqc_gym"
RUNBOOK_INPUT_MANIFEST_PATH = Path("docs/runbook_input_manifest.json")
LEGACY_NAME_PATTERNS = tuple(
    "".join(parts)
    for parts in (
        ("agades", "-", "cryptanalysis", "-", "gym"),
        ("agades", "_", "crypto", "_", "gym"),
        ("agades", "_", "crypto"),
        ("crypto", "_", "gym"),
        ("crypto", "-", "gym"),
        ("Agades", " ", "Cryptanalysis", " ", "Gym"),
        ("Cryptanalysis", " ", "Gym"),
    )
)
LEGACY_SCAN_PATHS = (
    "README.md",
    "docs",
    "examples",
    "hf",
    "nvidia",
    "prime_intellect",
    "pyproject.toml",
    "src",
    "tests",
)
RUNBOOK_ARTIFACT_GROUPS = {
    "architecture_docs": (
        "README.md",
        "docs/ARCHITECTURE.md",
        "docs/FAMILY_ADAPTERS.md",
        "docs/PLAN.md",
        "docs/IMPLEMENT.md",
        "docs/STATUS.md",
        "docs/EVAL_LOG.md",
    ),
    "safety_and_moat": (
        "docs/MOAT_AND_OPEN_SOURCE_STRATEGY.md",
        "docs/RESPONSIBLE_RESEARCH.md",
        "SECURITY.md",
    ),
    "community_and_ecosystem": (
        "hf/dataset_card.md",
        "hf/space_README.md",
        "hf/benchmark_card.md",
        "prime_intellect/environment_card.md",
        "prime_intellect/verifier_spec.md",
        "nvidia/README.md",
        "docs/HUGGINGFACE_RELEASE_PLAN.md",
        "docs/PRIME_INTELLECT_RELEASE_PLAN.md",
        "docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md",
    ),
    "github_oss_onboarding": (
        "CONTRIBUTING.md",
        ".github/ISSUE_TEMPLATE/evaluator_bug.yml",
        ".github/ISSUE_TEMPLATE/estimator_integration.yml",
        ".github/ISSUE_TEMPLATE/family_adapter.yml",
    ),
    "collaboration_briefs": (
        "docs/ASI_LABS_COLLABORATION_BRIEF.md",
        "docs/MARTIN_ALBRECHT_COLLABORATION_BRIEF.md",
        "docs/LEO_DUCAS_COLLABORATION_BRIEF.md",
    ),
    "machine_readable_artifacts": (
        "docs/source_catalog.json",
        "docs/benchmark_source_contracts.json",
        "docs/deepevolve_research_hooks_manifest.json",
        "docs/family_registry_manifest.json",
        "docs/family_operator_catalog.json",
        "docs/family_support_matrix.json",
        "docs/lattice_estimator_manifest.json",
        "docs/runbook_input_manifest.json",
        "docs/public_benchmark_manifest.json",
        "docs/publication_manifest.json",
        "docs/release_status.json",
        "public/run_export/manifest.json",
        "hf/dataset/dataset_info.json",
        "hf/space_manifest.json",
        "reports/hf_space_smoke.json",
        "prime_intellect/schemas/schema_manifest.json",
        "prime_intellect/verifiers_environment/prime_manifest.json",
        "reports/prime_environment_smoke.json",
        "nvidia/accelerator_manifest.json",
        "reports/nvidia_manifest_safety.json",
    ),
    "mvp_reports": (
        "reports/AGADES_PQC_GYM_MVP_REPORT.md",
    ),
}
CURRENT_NAME_PATHS = (
    "README.md",
    "docs/ARCHITECTURE.md",
    "hf/dataset_card.md",
    "hf/space_README.md",
    "prime_intellect/environment_card.md",
    "nvidia/README.md",
)
PUBLIC_BOUNDARY_DOCS = (
    "README.md",
    "docs/MOAT_AND_OPEN_SOURCE_STRATEGY.md",
    "docs/RESPONSIBLE_RESEARCH.md",
    "hf/dataset_card.md",
    "hf/space_README.md",
    "prime_intellect/environment_card.md",
    "docs/HUGGINGFACE_RELEASE_PLAN.md",
    "docs/PRIME_INTELLECT_RELEASE_PLAN.md",
)
PUBLIC_BOUNDARY_PHRASES = (
    "No real private evolution traces",
    "Do not publish real traces",
    "not a security claim",
    "does not execute arbitrary Python",
    "Do not target live third-party systems",
)
CORE_SYMBOL_PATHS = {
    "AssumptionSet": "src/agades_pqc_gym/core/assumptions.py",
    "AttackOperator": "src/agades_pqc_gym/core/attack_plan.py",
    "AttackPlan": "src/agades_pqc_gym/core/attack_plan.py",
    "EvaluatorResult": "src/agades_pqc_gym/core/evaluator_result.py",
    "FamilyAdapter": "src/agades_pqc_gym/core/family_adapter.py",
    "FamilyPluginDescriptor": "src/agades_pqc_gym/core/family_plugin.py",
    "FamilyPluginEntry": "src/agades_pqc_gym/core/family_plugin.py",
    "FamilyRegistry": "src/agades_pqc_gym/core/registry.py",
    "FitnessReport": "src/agades_pqc_gym/core/fitness.py",
    "ReportGenerator": "src/agades_pqc_gym/reporting/generator.py",
    "TargetSpec": "src/agades_pqc_gym/core/target.py",
    "TraceRecord": "src/agades_pqc_gym/core/trace_record.py",
    "default_family_registry": "src/agades_pqc_gym/core/registry.py",
    "redact_trace_record": "src/agades_pqc_gym/traces/redaction.py",
}
CORE_SYMBOL_IMPORTS = {
    "AssumptionSet": "agades_pqc_gym.core.AssumptionSet",
    "AttackOperator": "agades_pqc_gym.core.AttackOperator",
    "AttackPlan": "agades_pqc_gym.core.AttackPlan",
    "EvaluatorResult": "agades_pqc_gym.core.EvaluatorResult",
    "FamilyAdapter": "agades_pqc_gym.core.FamilyAdapter",
    "FamilyPluginDescriptor": "agades_pqc_gym.core.FamilyPluginDescriptor",
    "FamilyPluginEntry": "agades_pqc_gym.core.FamilyPluginEntry",
    "FamilyRegistry": "agades_pqc_gym.core.FamilyRegistry",
    "FitnessReport": "agades_pqc_gym.core.FitnessReport",
    "ReportGenerator": "agades_pqc_gym.core.ReportGenerator",
    "TargetSpec": "agades_pqc_gym.core.TargetSpec",
    "TraceRecord": "agades_pqc_gym.core.TraceRecord",
    "default_family_registry": "agades_pqc_gym.core.default_family_registry",
    "redact_trace_record": "agades_pqc_gym.core.redact_trace_record",
}
FAMILY_PLUGIN_NAMES = (
    "code_based",
    "hash_based",
    "implementation_security",
    "isogeny_historical",
    "lattice",
    "multivariate",
)
REQUIRED_FAMILY_PLUGIN_MODULES = {
    "code_based": [
        "src/agades_pqc_gym/families/code_based/plugin.py",
        "src/agades_pqc_gym/families/code_based/adapter.py",
        "src/agades_pqc_gym/families/code_based/validators.py",
    ],
    "hash_based": [
        "src/agades_pqc_gym/families/hash_based/plugin.py",
        "src/agades_pqc_gym/families/hash_based/adapter.py",
        "src/agades_pqc_gym/families/hash_based/validators.py",
    ],
    "implementation_security": [
        "src/agades_pqc_gym/families/implementation_security/plugin.py",
        "src/agades_pqc_gym/families/implementation_security/adapter.py",
        "src/agades_pqc_gym/families/implementation_security/validators.py",
    ],
    "isogeny_historical": [
        "src/agades_pqc_gym/families/isogeny_historical/plugin.py",
        "src/agades_pqc_gym/families/isogeny_historical/adapter.py",
        "src/agades_pqc_gym/families/isogeny_historical/validators.py",
    ],
    "lattice": [
        "src/agades_pqc_gym/families/lattice/plugin.py",
        "src/agades_pqc_gym/families/lattice/adapter.py",
        "src/agades_pqc_gym/families/lattice/validators.py",
    ],
    "multivariate": [
        "src/agades_pqc_gym/families/multivariate/plugin.py",
        "src/agades_pqc_gym/families/multivariate/adapter.py",
        "src/agades_pqc_gym/families/multivariate/validators.py",
    ],
}
IMPORT_PROBE_SCRIPT = r"""
import importlib
import json
import sys

payload = json.loads(sys.argv[1])
failures = []

for label, object_path in payload.get("objects", {}).items():
    module_name, separator, qualname = object_path.rpartition(".")
    if not separator or not module_name or not qualname:
        failures.append(
            f"{label}: {object_path} is not importable: ValueError: "
            "dotted object path must include a module and object"
        )
        continue
    try:
        obj = importlib.import_module(module_name)
        for part in qualname.split("."):
            obj = getattr(obj, part)
    except Exception as exc:
        failures.append(
            f"{label}: {object_path} is not importable: "
            f"{type(exc).__name__}: {exc}"
        )

for label, module_name in payload.get("modules", {}).items():
    try:
        importlib.import_module(module_name)
    except Exception as exc:
        failures.append(
            f"{label}: {module_name} is not importable: "
            f"{type(exc).__name__}: {exc}"
        )

print(json.dumps(failures, sort_keys=True))
raise SystemExit(1 if failures else 0)
"""
RUNBOOK_MILESTONES = (
    {
        "id": "milestone-0-repo-scaffold-and-runbook",
        "title": "Repo scaffold and Codex runbook",
        "artifacts": (
            "pyproject.toml",
            "README.md",
            "docs/PLAN.md",
            "docs/IMPLEMENT.md",
            "docs/STATUS.md",
            "docs/EVAL_LOG.md",
            ".github/workflows/ci.yml",
        ),
    },
    {
        "id": "milestone-1-dsl-and-validators",
        "title": "DSL and validators",
        "artifacts": (
            "src/agades_pqc_gym/core/target.py",
            "src/agades_pqc_gym/core/attack_plan.py",
            "src/agades_pqc_gym/core/operators.py",
            "src/agades_pqc_gym/core/assumptions.py",
            "src/agades_pqc_gym/validators/static.py",
            "examples/attack_plans/lattice_primal_usvp_toy.json",
            "examples/attack_plans/code_based_isd_placeholder.json",
        ),
    },
    {
        "id": "milestone-2-evaluator-suite",
        "title": "Evaluator suite",
        "artifacts": (
            "src/agades_pqc_gym/evaluators/router.py",
            "src/agades_pqc_gym/evaluators/lattice_estimator.py",
            "src/agades_pqc_gym/evaluators/mock_estimator.py",
            "src/agades_pqc_gym/families/plugins.py",
            "src/agades_pqc_gym/families/lattice/adapter.py",
            "docs/family_plugin_manifest.json",
            "docs/lattice_estimator_manifest.json",
        ),
    },
    {
        "id": "milestone-3-trace-logging-and-redaction",
        "title": "Trace logging and redaction",
        "artifacts": (
            "src/agades_pqc_gym/traces/schema.py",
            "src/agades_pqc_gym/traces/writer.py",
            "src/agades_pqc_gym/traces/redaction.py",
            "src/agades_pqc_gym/traces/public_bundle.py",
            "public/run_export/manifest.json",
            "examples/public_runs/lattice_toy_lwe_v0/trace_public.jsonl",
        ),
    },
    {
        "id": "milestone-4-openevolve-adapter",
        "title": "OpenEvolve adapter",
        "artifacts": (
            "examples/openevolve/evaluator.py",
            "src/agades_pqc_gym/openevolve_adapter/evaluator.py",
            "src/agades_pqc_gym/openevolve_adapter/config_templates.py",
            "src/agades_pqc_gym/evolution/campaign.py",
            "src/agades_pqc_gym/evolution/archive.py",
            "src/agades_pqc_gym/evolution/mutation.py",
            "src/agades_pqc_gym/evolution/heldout.py",
            "docs/deepevolve_research_hooks_manifest.json",
        ),
    },
    {
        "id": "milestone-5-report-generator",
        "title": "Report generator",
        "artifacts": (
            "src/agades_pqc_gym/reporting/generator.py",
            "src/agades_pqc_gym/reporting/markdown.py",
            "src/agades_pqc_gym/reporting/report.py",
            "reports/AGADES_PQC_GYM_MVP_REPORT.md",
        ),
    },
    {
        "id": "milestone-6-community-release-artifacts",
        "title": "Community release artifacts",
        "artifacts": (
            "hf/dataset/README.md",
            "hf/dataset/dataset_info.json",
            "hf/app.py",
            "hf/collection_manifest.json",
            "hf/space_manifest.json",
            "prime_intellect/verifiers_environment/agades_pqc_verifier_env.py",
            "prime_intellect/verifiers_environment/prime_manifest.json",
            "reports/prime_environment_smoke.json",
            "nvidia/accelerator_manifest.json",
            "reports/nvidia_manifest_safety.json",
            "docs/publication_manifest.json",
        ),
    },
    {
        "id": "milestone-7-collaboration-briefs",
        "title": "Collaboration briefs",
        "artifacts": (
            "docs/ASI_LABS_COLLABORATION_BRIEF.md",
            "docs/MARTIN_ALBRECHT_COLLABORATION_BRIEF.md",
            "docs/LEO_DUCAS_COLLABORATION_BRIEF.md",
        ),
    },
    {
        "id": "milestone-8-end-to-end-smoke-run",
        "title": "End-to-end smoke run",
        "artifacts": (
            "docs/public_benchmark_manifest.json",
            "public/run_export/runs.jsonl",
            "hf/dataset/task_metadata.jsonl",
            "hf/dataset/verifier_outputs.jsonl",
            "prime_intellect/verifiers_environment/prime_manifest.json",
            "reports/prime_environment_smoke.json",
            "nvidia/accelerator_manifest.json",
            "reports/nvidia_manifest_safety.json",
            "reports/AGADES_PQC_GYM_MVP_REPORT.md",
        ),
    },
)
SOURCE_BRIEF_CORE_TERMS = (
    "TargetSpec",
    "AttackPlan",
    "AttackOperator",
    "AssumptionSet",
    "EvaluatorResult",
    "FitnessReport",
    "TraceRecord",
    "ReportGenerator",
    "Public/private redaction layer",
)
SOURCE_BRIEF_PLUGIN_TERMS = (
    "lattice/",
    "code_based/",
    "multivariate/",
    "hash_based/",
    "isogeny_historical/",
    "implementation_security/",
)
SOURCE_BRIEF_ECOSYSTEM_TERMS = (
    "GitHub",
    "Hugging Face",
    "Prime Intellect",
)
SOURCE_BRIEF_BOUNDARY_TERMS = (
    "multi-family",
    "Lattice Estimator",
    "universal PQC oracle",
    "applicability validator",
)
PROJECT_CONTEXT_DATASET_TERMS = (
    "post-quantum-crypto-fr",
    "post-quantum-crypto-en",
    "Q-GRID/pqc-ssl-scans",
    "facebook/TAPAS",
    "facebookresearch/LWE-benchmarking",
)
PROJECT_CONTEXT_IMPLEMENTATION_TERMS = (
    "PQClean",
    "liboqs",
    "pqm4",
    "PQ Code Package",
)
PROJECT_CONTEXT_EVALUATOR_TERMS = (
    "KAT",
    "ACVP",
    "dudect",
    "ctgrind",
    "TIMECOP",
)
PROJECT_CONTEXT_EVOLUTION_TERMS = (
    "OpenEvolve",
    "DeepEvolve",
    "evolutionary trace",
    "evaluator",
)
PROJECT_CONTEXT_ECOSYSTEM_TERMS = (
    "Hugging Face",
    "Prime Intellect",
)
PROJECT_CONTEXT_MOAT_TERMS = (
    "trace",
    "moat",
    "claim",
)


def build_runbook_audit(
    root: Path | None = None,
    *,
    brief_path: Path | None = None,
    context_path: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    checks = [
        _deliverable_artifacts(project_root),
        _positioning_boundaries(project_root),
        _family_agnostic_core(project_root),
        _runbook_input_manifest(project_root),
        _ecosystem_counts(project_root),
        _public_moat_boundary(project_root),
        _milestone_coverage(project_root),
    ]
    if brief_path is not None:
        checks.append(_source_brief_anchor(brief_path))
    if context_path is not None:
        checks.append(_project_context_anchor(context_path))
    return {
        "schema_version": RUNBOOK_AUDIT_SCHEMA,
        "project": {
            "name": PROJECT_NAME,
            "package": PACKAGE_NAME,
            "repository": f"https://github.com/AgadesTech/{REPOSITORY_SLUG}",
        },
        "accepted": all(check["status"] == "passed" for check in checks),
        "summary": {
            "artifact_count": _artifact_count(),
            "failed": sum(1 for check in checks if check["status"] == "failed"),
            "passed": sum(1 for check in checks if check["status"] == "passed"),
            "total": len(checks),
        },
        "checks": checks,
        "safety": {
            "contains_private_traces": False,
            "publishes_private_candidates": False,
            "security_claim": False,
        },
    }


def write_runbook_audit(
    out: Path,
    *,
    root: Path | None = None,
    brief_path: Path | None = None,
    context_path: Path | None = None,
) -> dict[str, Any]:
    audit = build_runbook_audit(
        root=root,
        brief_path=brief_path,
        context_path=context_path,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return audit


def build_runbook_input_manifest(
    *,
    brief_path: Path,
    context_path: Path,
) -> dict[str, Any]:
    brief_text = brief_path.read_text(encoding="utf-8")
    context_text = context_path.read_text(encoding="utf-8")
    failures = _missing_required_terms(
        brief_text,
        _source_brief_required_groups(),
    ) + _missing_required_terms(
        context_text,
        _project_context_required_groups(),
        casefold=True,
    )
    if failures:
        raise ValueError("; ".join(failures))

    return {
        "schema_version": RUNBOOK_INPUT_MANIFEST_SCHEMA,
        "source_inputs": [
            {
                "anchor_groups": {
                    name: list(terms)
                    for name, terms in _project_context_required_groups().items()
                },
                "id": "project_context",
                "kind": "project_context",
                "line_count": _line_count(context_text),
                "sha256": _sha256_text(context_text),
                "source_label": context_path.name,
            },
            {
                "anchor_groups": {
                    name: list(terms)
                    for name, terms in _source_brief_required_groups().items()
                },
                "id": "source_brief",
                "kind": "source_brief",
                "line_count": _line_count(brief_text),
                "project_name_override": _project_name_override(),
                "sha256": _sha256_text(brief_text),
                "source_label": brief_path.name,
            },
        ],
        "safety": {
            "stores_absolute_paths": False,
            "stores_source_text": False,
        },
    }


def write_runbook_input_manifest(
    out: Path,
    *,
    brief_path: Path,
    context_path: Path,
) -> dict[str, Any]:
    manifest = build_runbook_input_manifest(
        brief_path=brief_path,
        context_path=context_path,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_runbook_input_manifest(manifest_path: Path) -> dict[str, Any]:
    failures: list[str] = []
    payload = _read_json_or_empty(manifest_path, failures=failures)
    summary = _summarize_runbook_input_manifest(payload)

    if payload.get("schema_version") != RUNBOOK_INPUT_MANIFEST_SCHEMA:
        failures.append("Runbook input manifest schema version is invalid.")
    if _stores_source_text(payload):
        failures.append("Runbook input manifest must not store source text.")
    if _stores_absolute_paths(payload):
        failures.append("Runbook input manifest must not store absolute paths.")

    safety = payload.get("safety")
    if not isinstance(safety, dict):
        failures.append("Runbook input manifest safety block must be an object.")
    else:
        if safety.get("stores_source_text") is not False:
            failures.append(
                "Runbook input manifest safety.stores_source_text must be false."
            )
        if safety.get("stores_absolute_paths") is not False:
            failures.append(
                "Runbook input manifest safety.stores_absolute_paths must be false."
            )

    source_inputs = payload.get("source_inputs")
    if not isinstance(source_inputs, list):
        failures.append("Runbook input manifest source_inputs must be a list.")
        source_inputs = []
    by_id = {
        source_input.get("id"): source_input
        for source_input in source_inputs
        if isinstance(source_input, dict)
    }
    expected_ids = {"project_context", "source_brief"}
    if set(by_id) != expected_ids:
        failures.append(
            "Runbook input manifest must include project_context and source_brief."
        )

    for input_id, source_input in by_id.items():
        if not isinstance(source_input.get("source_label"), str):
            failures.append(f"Runbook input {input_id} source_label must be a string.")
        elif "/" in source_input["source_label"] or "\\" in source_input[
            "source_label"
        ]:
            failures.append(
                f"Runbook input {input_id} source_label must be a filename only."
            )
        sha256 = source_input.get("sha256")
        if not isinstance(sha256, str) or not _is_sha256_hex(sha256):
            failures.append(f"Runbook input {input_id} sha256 must be a SHA-256 hex.")
        line_count = source_input.get("line_count")
        if not isinstance(line_count, int) or line_count <= 0:
            failures.append(f"Runbook input {input_id} line_count must be positive.")
        anchor_groups = source_input.get("anchor_groups")
        if not isinstance(anchor_groups, dict):
            failures.append(
                f"Runbook input {input_id} anchor_groups must be an object."
            )
        elif input_id == "source_brief":
            _verify_anchor_group_manifest(
                anchor_groups,
                _source_brief_required_groups(),
                "source_brief",
                failures,
            )
            if source_input.get("project_name_override") != _project_name_override():
                failures.append(
                    "Runbook source brief project_name_override must match current "
                    "Agades PQC Gym naming."
                )
        elif input_id == "project_context":
            _verify_anchor_group_manifest(
                anchor_groups,
                _project_context_required_groups(),
                "project_context",
                failures,
            )

    return {
        "accepted": not failures,
        "failures": failures,
        "summary": summary,
    }


def _deliverable_artifacts(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    for artifact in _required_artifacts():
        if not (root / artifact).is_file():
            failures.append(f"Required runbook deliverable is missing: {artifact}")
    return _check(
        check_id="runbook-deliverable-artifacts",
        status="failed" if failures else "passed",
        artifact="runbook deliverables",
        detail=(
            "Runbook-required docs, collaboration briefs, ecosystem cards, "
            "machine-readable manifests, and MVP reports are checked in."
        ),
        evidence={
            "artifact_count": _artifact_count(),
            "groups": _artifact_group_counts(),
        },
        failures=failures,
    )


def _positioning_boundaries(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8")
    if f'name = "{REPOSITORY_SLUG}"' not in pyproject_text:
        failures.append("pyproject.toml does not use the Agades PQC package slug.")
    if not (root / "src" / PACKAGE_NAME).is_dir():
        failures.append(f"Package directory is missing: src/{PACKAGE_NAME}")

    for relative_path in CURRENT_NAME_PATHS:
        text = (root / relative_path).read_text(encoding="utf-8")
        if PROJECT_NAME not in text:
            failures.append(f"{relative_path} does not mention {PROJECT_NAME}.")

    for relative_path in LEGACY_SCAN_PATHS:
        candidate = root / relative_path
        files = [candidate] if candidate.is_file() else _iter_text_files(candidate)
        for path in files:
            text = path.read_text(encoding="utf-8")
            for pattern in LEGACY_NAME_PATTERNS:
                if pattern in text:
                    failures.append(
                        f"{path.relative_to(root)} contains legacy name {pattern!r}."
                    )

    return _check(
        check_id="runbook-positioning-boundaries",
        status="failed" if failures else "passed",
        artifact="README.md + docs + package metadata",
        detail=(
            "Public positioning uses Agades PQC Gym naming and rejects legacy "
            "cryptanalysis and generic package names that could confuse the "
            "project with unrelated digital-asset tooling."
        ),
        evidence={
            "current_name_paths": len(CURRENT_NAME_PATHS),
            "legacy_name_patterns": len(LEGACY_NAME_PATTERNS),
            "primary_package": PACKAGE_NAME,
            "repository_slug": REPOSITORY_SLUG,
        },
        failures=failures,
    )


def _source_brief_anchor(brief_path: Path) -> dict[str, Any]:
    failures: list[str] = []
    text = ""
    try:
        text = brief_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        failures.append(f"Source runbook brief is missing: {brief_path}")
    except OSError as exc:
        failures.append(f"Source runbook brief cannot be read: {brief_path}: {exc}")

    required_groups = {
        "core_terms": SOURCE_BRIEF_CORE_TERMS,
        "family_plugins": SOURCE_BRIEF_PLUGIN_TERMS,
        "ecosystem_terms": SOURCE_BRIEF_ECOSYSTEM_TERMS,
        "boundary_terms": SOURCE_BRIEF_BOUNDARY_TERMS,
    }
    for group_name, terms in required_groups.items():
        for term in terms:
            if term not in text:
                failures.append(
                    f"Source runbook brief is missing {group_name} anchor: {term}"
                )

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None
    return _check(
        check_id="runbook-source-brief",
        status="failed" if failures else "passed",
        artifact=str(brief_path),
        detail=(
            "Optional user-provided long-running brief is anchored by digest and "
            "checked for the v3 multi-family core, plugin, ecosystem, and "
            "family-specific-validator requirements while preserving the current "
            "Agades PQC Gym public naming."
        ),
        evidence={
            "brief_path": str(brief_path),
            "sha256": digest,
            "core_terms": list(SOURCE_BRIEF_CORE_TERMS),
            "family_plugins": list(SOURCE_BRIEF_PLUGIN_TERMS),
            "ecosystem_terms": list(SOURCE_BRIEF_ECOSYSTEM_TERMS),
            "boundary_terms": list(SOURCE_BRIEF_BOUNDARY_TERMS),
            "project_name_override": {
                "name": PROJECT_NAME,
                "package": PACKAGE_NAME,
                "repository_slug": REPOSITORY_SLUG,
            },
        },
        failures=failures,
    )


def _family_agnostic_core(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    for symbol, relative_path in CORE_SYMBOL_PATHS.items():
        path = root / relative_path
        if not path.is_file():
            failures.append(
                f"Family-agnostic core symbol {symbol} file is missing: "
                f"{relative_path}"
            )
            continue
        text = path.read_text(encoding="utf-8")
        if symbol not in text:
            failures.append(
                f"Family-agnostic core symbol {symbol} is missing from "
                f"{relative_path}"
            )

    core_import_failures = _run_python_import_probe(
        root,
        objects=CORE_SYMBOL_IMPORTS,
        modules={},
    )
    failures.extend(core_import_failures)

    family_plugin_modules = _family_plugin_modules(root)
    family_plugin_module_digests = _family_plugin_module_digests(
        family_plugin_modules,
        root=root,
    )
    family_plugin_module_digest_count = sum(
        len(digests) for digests in family_plugin_module_digests.values()
    )
    plugin_module_imports = _family_plugin_module_imports(family_plugin_modules)
    registry_plugin_alignment = _family_registry_plugin_alignment(
        root,
        expected_module_digest_count=family_plugin_module_digest_count,
        failures=failures,
    )
    for family, module_paths in family_plugin_modules.items():
        for relative_path in module_paths:
            if not (root / relative_path).is_file():
                failures.append(
                    f"Family plugin {family} evidence module is missing: "
                    f"{relative_path}"
                )

    plugin_module_labels = {
        f"{family}: {module_name}": module_name
        for family, module_names in plugin_module_imports.items()
        for module_name in module_names
    }
    failures.extend(
        _run_python_import_probe(
            root,
            objects={},
            modules=plugin_module_labels,
        )
    )

    planned_families = [
        family
        for family in family_plugin_modules
        if family != "lattice"
    ]
    return _check(
        check_id="runbook-family-agnostic-core",
        status="failed" if failures else "passed",
        artifact="family-agnostic core and family plugin modules",
        detail=(
            "Family-agnostic runtime symbols and every planned family plugin "
            "module are present, with lattice kept as the first implemented "
            "vertical instead of the product boundary."
        ),
        evidence={
            "core_symbol_import_count": len(CORE_SYMBOL_IMPORTS),
            "core_symbol_imports": dict(CORE_SYMBOL_IMPORTS),
            "core_symbol_count": len(CORE_SYMBOL_PATHS),
            "core_symbols": dict(CORE_SYMBOL_PATHS),
            "family_plugin_count": len(family_plugin_modules),
            "family_plugin_module_digest_count": family_plugin_module_digest_count,
            "family_plugin_module_digests": family_plugin_module_digests,
            "family_plugin_module_import_count": sum(
                len(modules) for modules in plugin_module_imports.values()
            ),
            "family_plugin_module_imports": plugin_module_imports,
            "family_plugin_modules": {
                family: list(paths)
                for family, paths in family_plugin_modules.items()
            },
            **registry_plugin_alignment,
            "lattice_is_first_implemented_plugin": "lattice"
            in family_plugin_modules,
            "planned_family_plugin_count": len(planned_families),
        },
        failures=failures,
    )


def _family_plugin_modules(root: Path) -> dict[str, list[str]]:
    modules: dict[str, list[str]] = {}
    for family in FAMILY_PLUGIN_NAMES:
        family_root = root / "src" / "agades_pqc_gym" / "families" / family
        discovered = {
            _relative_to_root(path, root)
            for path in family_root.glob("*.py")
            if path.name != "__init__.py"
        }
        discovered.update(REQUIRED_FAMILY_PLUGIN_MODULES[family])
        modules[family] = sorted(discovered)
    return modules


def _family_plugin_module_imports(
    family_plugin_modules: dict[str, list[str]],
) -> dict[str, list[str]]:
    return {
        family: [_source_path_to_module(relative_path) for relative_path in paths]
        for family, paths in family_plugin_modules.items()
    }


def _family_plugin_module_digests(
    family_plugin_modules: dict[str, list[str]],
    *,
    root: Path,
) -> dict[str, dict[str, str]]:
    digests: dict[str, dict[str, str]] = {}
    for family, paths in family_plugin_modules.items():
        family_digests: dict[str, str] = {}
        for relative_path in paths:
            path = root / relative_path
            if path.is_file():
                family_digests[relative_path] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
        digests[family] = family_digests
    return digests


def _family_registry_plugin_alignment(
    root: Path,
    *,
    expected_module_digest_count: int,
    failures: list[str],
) -> dict[str, bool | int]:
    registry_manifest = _read_json_or_empty(
        root / "docs" / "family_registry_manifest.json",
        root=root,
        failures=failures,
    )
    alignment = registry_manifest.get("plugin_manifest_alignment")
    if not isinstance(alignment, dict):
        failures.append(
            "Family registry manifest is missing plugin manifest alignment "
            "evidence."
        )
        return {
            "family_registry_family_count_matches_plugin_manifest": False,
            "family_registry_plugin_count_matches_plugin_manifest": False,
            "family_registry_plugin_manifest_module_digest_count": 0,
            "family_registry_plugin_manifest_synced": False,
            "family_registry_runtime_adapter_entries_match_plugin_manifest": False,
        }

    module_digest_count = _non_negative_int(
        alignment.get("implementation_module_digest_count")
    )
    evidence = {
        "family_registry_family_count_matches_plugin_manifest": alignment.get(
            "registry_family_count_matches_manifest"
        )
        is True,
        "family_registry_plugin_count_matches_plugin_manifest": alignment.get(
            "registry_plugin_count_matches_manifest"
        )
        is True,
        "family_registry_plugin_manifest_module_digest_count": module_digest_count,
        "family_registry_plugin_manifest_synced": alignment.get(
            "committed_manifest_synced"
        )
        is True,
        "family_registry_runtime_adapter_entries_match_plugin_manifest": alignment.get(
            "registry_runtime_adapter_entries_match_manifest"
        )
        is True,
    }

    if not evidence["family_registry_plugin_manifest_synced"]:
        failures.append(
            "Family registry manifest is not synchronized with the family plugin "
            "manifest."
        )
    if not evidence["family_registry_family_count_matches_plugin_manifest"]:
        failures.append(
            "Family registry family count does not match the plugin manifest."
        )
    if not evidence["family_registry_plugin_count_matches_plugin_manifest"]:
        failures.append(
            "Family registry plugin count does not match the plugin manifest."
        )
    if module_digest_count != expected_module_digest_count:
        failures.append(
            "Family registry plugin manifest digest evidence is incomplete."
        )
    if not evidence[
        "family_registry_runtime_adapter_entries_match_plugin_manifest"
    ]:
        failures.append(
            "Family registry runtime adapters do not match the plugin manifest."
        )
    return evidence


def _non_negative_int(value: Any) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return 0


def _source_path_to_module(relative_path: str) -> str:
    return relative_path.removeprefix("src/").removesuffix(".py").replace("/", ".")


def _relative_to_root(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _run_python_import_probe(
    root: Path,
    *,
    objects: dict[str, str],
    modules: dict[str, str],
) -> list[str]:
    env = os.environ.copy()
    source_root = str((root / "src").resolve())
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        source_root
        if not existing_pythonpath
        else source_root + os.pathsep + existing_pythonpath
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            IMPORT_PROBE_SCRIPT,
            json.dumps(
                {"objects": objects, "modules": modules},
                sort_keys=True,
            ),
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        failures = json.loads(completed.stdout)
    except json.JSONDecodeError:
        if completed.returncode == 0:
            return []
        output = completed.stderr.strip() or completed.stdout.strip()
        return [f"Import probe failed without JSON output: {output}"]
    if not isinstance(failures, list):
        return ["Import probe returned an invalid JSON payload."]
    return [str(failure) for failure in failures]


def _runbook_input_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / RUNBOOK_INPUT_MANIFEST_PATH
    failures: list[str] = []
    if not manifest_path.is_file():
        failures.append(f"{RUNBOOK_INPUT_MANIFEST_PATH.as_posix()} is not checked in.")
        verification = {
            "summary": {
                "input_count": 0,
                "project_context_sha256": None,
                "source_brief_sha256": None,
                "source_input_ids": [],
                "stores_absolute_paths": None,
                "stores_source_text": None,
            }
        }
    else:
        verification = verify_runbook_input_manifest(manifest_path)
        failures.extend(verification["failures"])
    summary = verification["summary"]
    return _check(
        check_id="runbook-source-input-manifest",
        status="failed" if failures else "passed",
        artifact=RUNBOOK_INPUT_MANIFEST_PATH.as_posix(),
        detail=(
            "The user-provided v3 runbook brief and project-context transcript "
            "are anchored by digest in a public manifest without storing local "
            "absolute paths or source text."
        ),
        evidence={
            "input_count": summary["input_count"],
            "manifest_path": RUNBOOK_INPUT_MANIFEST_PATH.as_posix(),
            "project_context_sha256": summary["project_context_sha256"],
            "project_name_override": _project_name_override(),
            "source_brief_sha256": summary["source_brief_sha256"],
            "source_input_ids": summary["source_input_ids"],
            "stores_absolute_paths": summary["stores_absolute_paths"],
            "stores_source_text": summary["stores_source_text"],
        },
        failures=failures,
    )


def _project_context_anchor(context_path: Path) -> dict[str, Any]:
    failures: list[str] = []
    text = ""
    try:
        text = context_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        failures.append(f"Project context file is missing: {context_path}")
    except OSError as exc:
        failures.append(f"Project context file cannot be read: {context_path}: {exc}")

    required_groups = {
        "dataset_terms": PROJECT_CONTEXT_DATASET_TERMS,
        "implementation_terms": PROJECT_CONTEXT_IMPLEMENTATION_TERMS,
        "evaluator_terms": PROJECT_CONTEXT_EVALUATOR_TERMS,
        "evolution_terms": PROJECT_CONTEXT_EVOLUTION_TERMS,
        "ecosystem_terms": PROJECT_CONTEXT_ECOSYSTEM_TERMS,
        "moat_terms": PROJECT_CONTEXT_MOAT_TERMS,
    }
    casefolded = text.casefold()
    for group_name, terms in required_groups.items():
        for term in terms:
            if term.casefold() not in casefolded:
                failures.append(
                    f"Project context file is missing {group_name} anchor: {term}"
                )

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None
    return _check(
        check_id="runbook-project-context",
        status="failed" if failures else "passed",
        artifact=str(context_path),
        detail=(
            "Optional project-context transcript is anchored by digest and checked "
            "for the dataset, implementation-lab, evaluator-gate, evolution-loop, "
            "ecosystem, and private-moat themes that motivated the long-running "
            "Agades PQC Gym build."
        ),
        evidence={
            "context_path": str(context_path),
            "sha256": digest,
            "dataset_terms": list(PROJECT_CONTEXT_DATASET_TERMS),
            "implementation_terms": list(PROJECT_CONTEXT_IMPLEMENTATION_TERMS),
            "evaluator_terms": list(PROJECT_CONTEXT_EVALUATOR_TERMS),
            "evolution_terms": list(PROJECT_CONTEXT_EVOLUTION_TERMS),
            "ecosystem_terms": list(PROJECT_CONTEXT_ECOSYSTEM_TERMS),
            "moat_terms": list(PROJECT_CONTEXT_MOAT_TERMS),
        },
        failures=failures,
    )


def _ecosystem_counts(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    public_benchmark = _read_json_or_empty(
        root / "docs" / "public_benchmark_manifest.json",
        root=root,
        failures=failures,
    )
    hf_info = _read_json_or_empty(
        root / "hf" / "dataset" / "dataset_info.json",
        root=root,
        failures=failures,
    )
    prime_manifest = _read_json_or_empty(
        root / "prime_intellect" / "verifiers_environment" / "prime_manifest.json",
        root=root,
        failures=failures,
    )
    nvidia_manifest = _read_json_or_empty(
        root / "nvidia" / "accelerator_manifest.json",
        root=root,
        failures=failures,
    )

    evidence = {
        "hf_attack_plan_rows": hf_info.get("attack_plan_count"),
        "hf_valid_attack_plan_rows": hf_info.get("valid_attack_plan_count"),
        "hf_invalid_attack_plan_rows": hf_info.get("invalid_attack_plan_count"),
        "hf_task_metadata_rows": hf_info.get("task_metadata_count"),
        "nvidia_workloads": len(nvidia_manifest.get("workloads", [])),
        "prime_tasks": prime_manifest.get("task_manifest", {}).get("task_count"),
        "public_records": public_benchmark.get("summary", {}).get("record_count"),
        "public_run_bundles": public_benchmark.get("summary", {}).get(
            "bundle_count"
        ),
    }
    prime_eligible_count = hf_info.get("prime_task_eligible_count")
    evidence["prime_tasks_match_hf_task_metadata_rows"] = (
        isinstance(evidence["prime_tasks"], int)
        and isinstance(evidence["hf_task_metadata_rows"], int)
        and evidence["prime_tasks"] == evidence["hf_task_metadata_rows"]
    )
    if evidence["hf_attack_plan_rows"] != hf_info.get("verifier_output_count"):
        failures.append("Hugging Face AttackPlan and verifier row counts differ.")
    if not isinstance(evidence["hf_valid_attack_plan_rows"], int) or not isinstance(
        evidence["hf_invalid_attack_plan_rows"], int
    ):
        failures.append("Hugging Face dataset lacks valid/invalid AttackPlan counts.")
    elif evidence["hf_attack_plan_rows"] != (
        evidence["hf_valid_attack_plan_rows"] + evidence["hf_invalid_attack_plan_rows"]
    ):
        failures.append(
            "Hugging Face valid and invalid AttackPlan counts do not add up."
        )
    if not isinstance(evidence["hf_task_metadata_rows"], int) or not isinstance(
        prime_eligible_count, int
    ):
        failures.append(
            "Hugging Face dataset lacks task metadata or Prime-eligible counts."
        )
    elif evidence["hf_task_metadata_rows"] != prime_eligible_count:
        failures.append(
            "Hugging Face task metadata count differs from Prime-eligible count."
        )
    if not evidence["prime_tasks_match_hf_task_metadata_rows"]:
        failures.append(
            "Prime task count differs from Hugging Face task metadata rows."
        )
    if evidence["prime_tasks"] != len(
        prime_manifest.get("task_manifest", {}).get("attack_plan_ids", [])
    ):
        failures.append("Prime task count differs from packaged AttackPlan ids.")
    if evidence["public_run_bundles"] != len(
        nvidia_manifest.get("public_artifacts", {}).get("public_run_bundles", [])
    ):
        failures.append(
            "NVIDIA public bundle count differs from public benchmark manifest."
        )
    if public_benchmark.get("summary", {}).get("security_claim") is not False:
        failures.append("Public benchmark manifest advertises a security claim.")

    return _check(
        check_id="runbook-ecosystem-counts",
        status="failed" if failures else "passed",
        artifact="HF/Prime/NVIDIA/public benchmark manifests",
        detail=(
            "Community-facing Hugging Face, Prime Intellect, NVIDIA, and public "
            "benchmark counts are cross-checked from committed manifests."
        ),
        evidence=evidence,
        failures=failures,
    )


def _public_moat_boundary(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    combined_text = "\n".join(
        _read_text_or_empty(root / relative_path, root=root, failures=failures)
        for relative_path in PUBLIC_BOUNDARY_DOCS
    )
    for phrase in PUBLIC_BOUNDARY_PHRASES:
        if phrase not in combined_text:
            failures.append(f"Public boundary docs lack phrase: {phrase!r}.")

    hf_info = _read_json_or_empty(
        root / "hf" / "dataset" / "dataset_info.json",
        root=root,
        failures=failures,
    )
    prime_manifest = _read_json_or_empty(
        root / "prime_intellect" / "verifiers_environment" / "prime_manifest.json",
        root=root,
        failures=failures,
    )
    nvidia_manifest = _read_json_or_empty(
        root / "nvidia" / "accelerator_manifest.json",
        root=root,
        failures=failures,
    )
    safety_blocks = (
        hf_info.get("safety", {}),
        prime_manifest.get("safety", {}),
        nvidia_manifest.get("safety", {}),
    )
    if any(
        block.get("contains_private_traces") is not False
        for block in safety_blocks
    ):
        failures.append("At least one public manifest may expose private traces.")
    if any(block.get("security_claim") is not False for block in safety_blocks):
        failures.append("At least one public manifest advertises a security claim.")
    if any(
        block.get("publishes_private_candidates") is True for block in safety_blocks
    ):
        failures.append("At least one public manifest publishes private candidates.")

    return _check(
        check_id="runbook-public-moat-boundary",
        status="failed" if failures else "passed",
        artifact="public/private boundary docs and manifests",
        detail=(
            "Public docs and machine-readable manifests preserve the open-core "
            "boundary: no private traces, no private candidate publication, and "
            "no security claims from toy evidence."
        ),
        evidence={
            "boundary_docs": len(PUBLIC_BOUNDARY_DOCS),
            "contains_private_traces": False,
            "publishes_private_candidates": False,
            "security_claim": False,
        },
        failures=failures,
    )


def _milestone_coverage(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    milestones = []
    for milestone in RUNBOOK_MILESTONES:
        missing = [
            artifact
            for artifact in milestone["artifacts"]
            if not (root / artifact).is_file()
        ]
        if missing:
            for artifact in missing:
                failures.append(
                    f"{milestone['id']} missing evidence artifact: {artifact}"
                )
        milestones.append(
            {
                "id": milestone["id"],
                "title": milestone["title"],
                "artifact_count": len(milestone["artifacts"]),
                "artifacts": list(milestone["artifacts"]),
                "status": "failed" if missing else "passed",
            }
        )

    passed = sum(1 for milestone in milestones if milestone["status"] == "passed")
    failed = len(milestones) - passed
    return _check(
        check_id="runbook-milestone-coverage",
        status="failed" if failures else "passed",
        artifact="runbook milestone acceptance matrix",
        detail=(
            "Runbook milestones 0-8 are mapped to committed implementation, "
            "evaluation, trace, reporting, ecosystem, collaboration, and smoke "
            "evidence so completion is auditable milestone by milestone."
        ),
        evidence={
            "failed_milestones": failed,
            "milestone_count": len(milestones),
            "milestone_ids": [milestone["id"] for milestone in milestones],
            "milestones": milestones,
            "passed_milestones": passed,
        },
        failures=failures,
    )


def _check(
    *,
    check_id: str,
    status: str,
    artifact: str,
    detail: str,
    evidence: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "artifact": artifact,
        "detail": detail,
        "evidence": evidence,
        "failures": failures,
    }


def _artifact_count() -> int:
    return len(_required_artifacts())


def _artifact_group_counts() -> dict[str, int]:
    return {
        group: len(artifacts)
        for group, artifacts in sorted(RUNBOOK_ARTIFACT_GROUPS.items())
    }


def _required_artifacts() -> tuple[str, ...]:
    return tuple(
        artifact
        for artifacts in RUNBOOK_ARTIFACT_GROUPS.values()
        for artifact in artifacts
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_or_empty(
    path: Path,
    *,
    root: Path | None = None,
    failures: list[str],
) -> dict[str, Any]:
    display_path = str(path if root is None else path.relative_to(root))
    if not path.is_file():
        failures.append(f"Required JSON artifact is missing: {display_path}")
        return {}
    try:
        return _read_json(path)
    except json.JSONDecodeError as exc:
        failures.append(f"JSON artifact is invalid: {display_path}: {exc}")
        return {}


def _summarize_runbook_input_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    source_inputs = payload.get("source_inputs")
    if not isinstance(source_inputs, list):
        source_inputs = []
    by_id = {
        source_input.get("id"): source_input
        for source_input in source_inputs
        if isinstance(source_input, dict)
    }
    safety = payload.get("safety") if isinstance(payload.get("safety"), dict) else {}
    return {
        "input_count": len(by_id),
        "project_context_sha256": _source_input_digest(by_id, "project_context"),
        "source_brief_sha256": _source_input_digest(by_id, "source_brief"),
        "source_input_ids": sorted(str(input_id) for input_id in by_id),
        "stores_absolute_paths": safety.get("stores_absolute_paths"),
        "stores_source_text": safety.get("stores_source_text"),
    }


def _source_input_digest(
    by_id: dict[Any, dict[str, Any]],
    input_id: str,
) -> str | None:
    digest = by_id.get(input_id, {}).get("sha256")
    return digest if isinstance(digest, str) else None


def _source_brief_required_groups() -> dict[str, tuple[str, ...]]:
    return {
        "boundary_terms": SOURCE_BRIEF_BOUNDARY_TERMS,
        "core_terms": SOURCE_BRIEF_CORE_TERMS,
        "ecosystem_terms": SOURCE_BRIEF_ECOSYSTEM_TERMS,
        "family_plugins": SOURCE_BRIEF_PLUGIN_TERMS,
    }


def _project_context_required_groups() -> dict[str, tuple[str, ...]]:
    return {
        "dataset_terms": PROJECT_CONTEXT_DATASET_TERMS,
        "ecosystem_terms": PROJECT_CONTEXT_ECOSYSTEM_TERMS,
        "evaluator_terms": PROJECT_CONTEXT_EVALUATOR_TERMS,
        "evolution_terms": PROJECT_CONTEXT_EVOLUTION_TERMS,
        "implementation_terms": PROJECT_CONTEXT_IMPLEMENTATION_TERMS,
        "moat_terms": PROJECT_CONTEXT_MOAT_TERMS,
    }


def _project_name_override() -> dict[str, str]:
    return {
        "name": PROJECT_NAME,
        "package": PACKAGE_NAME,
        "repository_slug": REPOSITORY_SLUG,
    }


def _missing_required_terms(
    text: str,
    required_groups: dict[str, tuple[str, ...]],
    *,
    casefold: bool = False,
) -> list[str]:
    haystack = text.casefold() if casefold else text
    failures: list[str] = []
    for group_name, terms in required_groups.items():
        for term in terms:
            needle = term.casefold() if casefold else term
            if needle not in haystack:
                failures.append(f"Missing {group_name} anchor: {term}")
    return failures


def _verify_anchor_group_manifest(
    anchor_groups: dict[str, Any],
    expected_groups: dict[str, tuple[str, ...]],
    input_id: str,
    failures: list[str],
) -> None:
    for group_name, expected_terms in expected_groups.items():
        terms = anchor_groups.get(group_name)
        if terms != list(expected_terms):
            failures.append(
                f"Runbook input {input_id} anchor group {group_name} is out of sync."
            )


def _line_count(text: str) -> int:
    if text == "":
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _stores_source_text(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            key == "source_text" or _stores_source_text(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_stores_source_text(child) for child in value)
    return False


def _stores_absolute_paths(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_stores_absolute_paths(child) for child in value.values())
    if isinstance(value, list):
        return any(_stores_absolute_paths(child) for child in value)
    if isinstance(value, str):
        return value.startswith("/") or (
            len(value) >= 3 and value[1:3] in {":\\", ":/"}
        )
    return False


def _read_text_or_empty(
    path: Path,
    *,
    root: Path,
    failures: list[str],
) -> str:
    if not path.is_file():
        failures.append(f"Required text artifact is missing: {path.relative_to(root)}")
        return ""
    return path.read_text(encoding="utf-8")


def _iter_text_files(root: Path) -> list[Path]:
    ignored_dirs = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
    }
    if not root.exists():
        return []
    return [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and not any(part in ignored_dirs for part in path.parts)
        and path.suffix
        in {
            ".cfg",
            ".json",
            ".md",
            ".py",
            ".toml",
            ".txt",
            ".yaml",
            ".yml",
        }
    ]
