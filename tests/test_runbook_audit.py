import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.runbook_audit import (
    build_runbook_audit,
    build_runbook_input_manifest,
    verify_runbook_input_manifest,
    write_runbook_audit,
    write_runbook_input_manifest,
)

EXPECTED_MILESTONE_IDS = [
    "milestone-0-repo-scaffold-and-runbook",
    "milestone-1-dsl-and-validators",
    "milestone-2-evaluator-suite",
    "milestone-3-trace-logging-and-redaction",
    "milestone-4-openevolve-adapter",
    "milestone-5-report-generator",
    "milestone-6-community-release-artifacts",
    "milestone-7-collaboration-briefs",
    "milestone-8-end-to-end-smoke-run",
]
EXPECTED_CORE_SYMBOLS = {
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
EXPECTED_CORE_SYMBOL_IMPORTS = {
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
EXPECTED_FAMILY_PLUGIN_MODULES = {
    "code_based": [
        "src/agades_pqc_gym/families/code_based/adapter.py",
        "src/agades_pqc_gym/families/code_based/bit_flip_estimator.py",
        "src/agades_pqc_gym/families/code_based/bit_flip_fixture.py",
        "src/agades_pqc_gym/families/code_based/classic_mceliece_fixture_decoder.py",
        "src/agades_pqc_gym/families/code_based/classic_mceliece_fixture_estimator.py",
        "src/agades_pqc_gym/families/code_based/hqc_fixture_decoder.py",
        "src/agades_pqc_gym/families/code_based/hqc_fixture_estimator.py",
        "src/agades_pqc_gym/families/code_based/isd_estimator.py",
        "src/agades_pqc_gym/families/code_based/operators.py",
        "src/agades_pqc_gym/families/code_based/plugin.py",
        "src/agades_pqc_gym/families/code_based/syndrome_solver.py",
        "src/agades_pqc_gym/families/code_based/targets.py",
        "src/agades_pqc_gym/families/code_based/validators.py",
    ],
    "hash_based": [
        "src/agades_pqc_gym/families/hash_based/adapter.py",
        "src/agades_pqc_gym/families/hash_based/bound_estimator.py",
        "src/agades_pqc_gym/families/hash_based/collision_fixture.py",
        "src/agades_pqc_gym/families/hash_based/misuse_fixture.py",
        "src/agades_pqc_gym/families/hash_based/operators.py",
        "src/agades_pqc_gym/families/hash_based/plugin.py",
        "src/agades_pqc_gym/families/hash_based/preimage_solver.py",
        "src/agades_pqc_gym/families/hash_based/signature_fixture.py",
        "src/agades_pqc_gym/families/hash_based/targets.py",
        "src/agades_pqc_gym/families/hash_based/validators.py",
    ],
    "implementation_security": [
        "src/agades_pqc_gym/families/implementation_security/adapter.py",
        "src/agades_pqc_gym/families/implementation_security/benchmark_fixture.py",
        "src/agades_pqc_gym/families/implementation_security/kat_estimator.py",
        "src/agades_pqc_gym/families/implementation_security/kat_fixture.py",
        "src/agades_pqc_gym/families/implementation_security/operators.py",
        "src/agades_pqc_gym/families/implementation_security/plugin.py",
        "src/agades_pqc_gym/families/implementation_security/targets.py",
        "src/agades_pqc_gym/families/implementation_security/timing_fixture.py",
        "src/agades_pqc_gym/families/implementation_security/validators.py",
    ],
    "isogeny_historical": [
        "src/agades_pqc_gym/families/isogeny_historical/adapter.py",
        "src/agades_pqc_gym/families/isogeny_historical/operators.py",
        "src/agades_pqc_gym/families/isogeny_historical/path_estimator.py",
        "src/agades_pqc_gym/families/isogeny_historical/path_fixture.py",
        "src/agades_pqc_gym/families/isogeny_historical/plugin.py",
        "src/agades_pqc_gym/families/isogeny_historical/targets.py",
        "src/agades_pqc_gym/families/isogeny_historical/validators.py",
    ],
    "lattice": [
        "src/agades_pqc_gym/families/lattice/adapter.py",
        "src/agades_pqc_gym/families/lattice/downscaled_solver.py",
        "src/agades_pqc_gym/families/lattice/lattice_estimator.py",
        "src/agades_pqc_gym/families/lattice/operators.py",
        "src/agades_pqc_gym/families/lattice/plugin.py",
        "src/agades_pqc_gym/families/lattice/targets.py",
        "src/agades_pqc_gym/families/lattice/validators.py",
    ],
    "multivariate": [
        "src/agades_pqc_gym/families/multivariate/adapter.py",
        "src/agades_pqc_gym/families/multivariate/minrank_solver.py",
        "src/agades_pqc_gym/families/multivariate/mq_estimator.py",
        "src/agades_pqc_gym/families/multivariate/mq_solver.py",
        "src/agades_pqc_gym/families/multivariate/operators.py",
        "src/agades_pqc_gym/families/multivariate/plugin.py",
        "src/agades_pqc_gym/families/multivariate/targets.py",
        "src/agades_pqc_gym/families/multivariate/uov_fixture.py",
        "src/agades_pqc_gym/families/multivariate/validators.py",
    ],
}
EXPECTED_FAMILY_PLUGIN_IMPORTS = {
    family: [
        path.removeprefix("src/").removesuffix(".py").replace("/", ".")
        for path in paths
    ]
    for family, paths in EXPECTED_FAMILY_PLUGIN_MODULES.items()
}
EXPECTED_FAMILY_PLUGIN_DIGESTS = {
    family: {
        path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        for path in paths
    }
    for family, paths in EXPECTED_FAMILY_PLUGIN_MODULES.items()
}
EXPECTED_RUNBOOK_INPUT_DIGESTS = {
    "project_context": (
        "bc5cdbb52c44a248564c2f75096706aaa740886b47a13dfd468bcf7acd870e9d"
    ),
    "source_brief": (
        "9d8b5652e4a9d7e554748175a6ea9d78830f2e4ca9bb2f0bfde9a82adcd3ffa3"
    ),
}


def test_runbook_audit_accepts_current_deliverables(tmp_path: Path) -> None:
    out = tmp_path / "runbook_audit.json"

    audit = write_runbook_audit(out)

    assert audit == build_runbook_audit()
    assert json.loads(out.read_text()) == audit
    assert audit["schema_version"] == "agades.pqc.runbook_audit.v1"
    assert audit["accepted"] is True
    assert audit["summary"] == {
        "artifact_count": 47,
        "failed": 0,
        "passed": 7,
        "total": 7,
    }

    checks = {check["id"]: check for check in audit["checks"]}
    assert checks["runbook-deliverable-artifacts"]["status"] == "passed"
    assert checks["runbook-deliverable-artifacts"]["evidence"] == {
        "artifact_count": 47,
        "groups": {
            "architecture_docs": 7,
            "collaboration_briefs": 3,
            "community_and_ecosystem": 9,
            "github_oss_onboarding": 4,
            "machine_readable_artifacts": 20,
            "mvp_reports": 1,
            "safety_and_moat": 3,
        },
    }
    assert checks["runbook-positioning-boundaries"]["status"] == "passed"
    assert checks["runbook-positioning-boundaries"]["evidence"] == {
        "current_name_paths": 6,
        "legacy_name_patterns": 7,
        "primary_package": "agades_pqc_gym",
        "repository_slug": "agades-pqc-gym",
    }
    assert checks["runbook-family-agnostic-core"]["status"] == "passed"
    assert all(
        import_path == f"agades_pqc_gym.core.{symbol}"
        for symbol, import_path in checks["runbook-family-agnostic-core"]["evidence"][
            "core_symbol_imports"
        ].items()
    )
    assert checks["runbook-family-agnostic-core"]["evidence"] == {
        "core_symbol_import_count": 14,
        "core_symbol_imports": EXPECTED_CORE_SYMBOL_IMPORTS,
        "core_symbol_count": 14,
        "core_symbols": EXPECTED_CORE_SYMBOLS,
        "family_plugin_count": 6,
        "family_plugin_module_digest_count": 55,
        "family_plugin_module_digests": EXPECTED_FAMILY_PLUGIN_DIGESTS,
        "family_plugin_module_import_count": 55,
        "family_plugin_module_imports": EXPECTED_FAMILY_PLUGIN_IMPORTS,
        "family_plugin_modules": EXPECTED_FAMILY_PLUGIN_MODULES,
        "family_registry_family_count_matches_plugin_manifest": True,
        "family_registry_plugin_count_matches_plugin_manifest": True,
        "family_registry_plugin_manifest_module_digest_count": 55,
        "family_registry_plugin_manifest_synced": True,
        "family_registry_runtime_adapter_entries_match_plugin_manifest": True,
        "lattice_is_first_implemented_plugin": True,
        "planned_family_plugin_count": 5,
    }
    assert checks["runbook-source-input-manifest"]["status"] == "passed"
    assert checks["runbook-source-input-manifest"]["evidence"] == {
        "input_count": 2,
        "manifest_path": "docs/runbook_input_manifest.json",
        "project_context_sha256": EXPECTED_RUNBOOK_INPUT_DIGESTS[
            "project_context"
        ],
        "project_name_override": {
            "name": "Agades PQC Gym",
            "package": "agades_pqc_gym",
            "repository_slug": "agades-pqc-gym",
        },
        "source_brief_sha256": EXPECTED_RUNBOOK_INPUT_DIGESTS["source_brief"],
        "source_input_ids": ["project_context", "source_brief"],
        "stores_absolute_paths": False,
        "stores_source_text": False,
    }
    assert checks["runbook-ecosystem-counts"]["status"] == "passed"
    assert checks["runbook-ecosystem-counts"]["evidence"] == {
            "hf_attack_plan_rows": 80,
            "hf_invalid_attack_plan_rows": 1,
            "hf_task_metadata_rows": 79,
            "hf_valid_attack_plan_rows": 79,
            "nvidia_workloads": 27,
            "prime_tasks": 79,
            "prime_tasks_match_hf_task_metadata_rows": True,
            "public_records": 59,
            "public_run_bundles": 18,
        }
    assert checks["runbook-public-moat-boundary"]["status"] == "passed"
    assert checks["runbook-public-moat-boundary"]["evidence"] == {
        "boundary_docs": 8,
        "contains_private_traces": False,
        "publishes_private_candidates": False,
        "security_claim": False,
    }
    assert checks["runbook-milestone-coverage"]["status"] == "passed"
    assert checks["runbook-milestone-coverage"]["evidence"] == {
        "failed_milestones": 0,
        "milestone_count": 9,
        "milestone_ids": EXPECTED_MILESTONE_IDS,
        "milestones": [
            {
                "artifact_count": 7,
                "artifacts": [
                    "pyproject.toml",
                    "README.md",
                    "docs/PLAN.md",
                    "docs/IMPLEMENT.md",
                    "docs/STATUS.md",
                    "docs/EVAL_LOG.md",
                    ".github/workflows/ci.yml",
                ],
                "id": "milestone-0-repo-scaffold-and-runbook",
                "status": "passed",
                "title": "Repo scaffold and Codex runbook",
            },
            {
                "artifact_count": 7,
                "artifacts": [
                    "src/agades_pqc_gym/core/target.py",
                    "src/agades_pqc_gym/core/attack_plan.py",
                    "src/agades_pqc_gym/core/operators.py",
                    "src/agades_pqc_gym/core/assumptions.py",
                    "src/agades_pqc_gym/validators/static.py",
                    "examples/attack_plans/lattice_primal_usvp_toy.json",
                    "examples/attack_plans/code_based_isd_placeholder.json",
                ],
                "id": "milestone-1-dsl-and-validators",
                "status": "passed",
                "title": "DSL and validators",
            },
            {
                "artifact_count": 7,
                "artifacts": [
                    "src/agades_pqc_gym/evaluators/router.py",
                    "src/agades_pqc_gym/evaluators/lattice_estimator.py",
                    "src/agades_pqc_gym/evaluators/mock_estimator.py",
                    "src/agades_pqc_gym/families/plugins.py",
                    "src/agades_pqc_gym/families/lattice/adapter.py",
                    "docs/family_plugin_manifest.json",
                    "docs/lattice_estimator_manifest.json",
                ],
                "id": "milestone-2-evaluator-suite",
                "status": "passed",
                "title": "Evaluator suite",
            },
            {
                "artifact_count": 6,
                "artifacts": [
                    "src/agades_pqc_gym/traces/schema.py",
                    "src/agades_pqc_gym/traces/writer.py",
                    "src/agades_pqc_gym/traces/redaction.py",
                    "src/agades_pqc_gym/traces/public_bundle.py",
                    "public/run_export/manifest.json",
                    "examples/public_runs/lattice_toy_lwe_v0/trace_public.jsonl",
                ],
                "id": "milestone-3-trace-logging-and-redaction",
                "status": "passed",
                "title": "Trace logging and redaction",
            },
            {
                "artifact_count": 8,
                "artifacts": [
                    "examples/openevolve/evaluator.py",
                    "src/agades_pqc_gym/openevolve_adapter/evaluator.py",
                    "src/agades_pqc_gym/openevolve_adapter/config_templates.py",
                    "src/agades_pqc_gym/evolution/campaign.py",
                    "src/agades_pqc_gym/evolution/archive.py",
                    "src/agades_pqc_gym/evolution/mutation.py",
                    "src/agades_pqc_gym/evolution/heldout.py",
                    "docs/deepevolve_research_hooks_manifest.json",
                ],
                "id": "milestone-4-openevolve-adapter",
                "status": "passed",
                "title": "OpenEvolve adapter",
            },
            {
                "artifact_count": 4,
                "artifacts": [
                    "src/agades_pqc_gym/reporting/generator.py",
                    "src/agades_pqc_gym/reporting/markdown.py",
                    "src/agades_pqc_gym/reporting/report.py",
                    "reports/AGADES_PQC_GYM_MVP_REPORT.md",
                ],
                "id": "milestone-5-report-generator",
                "status": "passed",
                "title": "Report generator",
            },
            {
                "artifact_count": 11,
                "artifacts": [
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
                ],
                "id": "milestone-6-community-release-artifacts",
                "status": "passed",
                "title": "Community release artifacts",
            },
            {
                "artifact_count": 3,
                "artifacts": [
                    "docs/ASI_LABS_COLLABORATION_BRIEF.md",
                    "docs/MARTIN_ALBRECHT_COLLABORATION_BRIEF.md",
                    "docs/LEO_DUCAS_COLLABORATION_BRIEF.md",
                ],
                "id": "milestone-7-collaboration-briefs",
                "status": "passed",
                "title": "Collaboration briefs",
            },
            {
                "artifact_count": 9,
                "artifacts": [
                    "docs/public_benchmark_manifest.json",
                    "public/run_export/runs.jsonl",
                    "hf/dataset/task_metadata.jsonl",
                    "hf/dataset/verifier_outputs.jsonl",
                    "prime_intellect/verifiers_environment/prime_manifest.json",
                    "reports/prime_environment_smoke.json",
                    "nvidia/accelerator_manifest.json",
                    "reports/nvidia_manifest_safety.json",
                    "reports/AGADES_PQC_GYM_MVP_REPORT.md",
                ],
                "id": "milestone-8-end-to-end-smoke-run",
                "status": "passed",
                "title": "End-to-end smoke run",
            },
        ],
        "passed_milestones": 9,
    }


def test_committed_public_runbook_audit_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "runbook_audit.json"
    committed = Path("public/runbook_audit.json")

    write_runbook_audit(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_public_runbook_audit_is_git_tracked() -> None:
    result = subprocess.run(
        ["git", "ls-files", "public/runbook_audit.json"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "public/runbook_audit.json"


def test_runbook_audit_rejects_missing_openevolve_milestone_artifact(
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
        / "src"
        / "agades_pqc_gym"
        / "openevolve_adapter"
        / "evaluator.py"
    ).unlink()

    audit = build_runbook_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["runbook-milestone-coverage"]["status"] == "failed"
    assert any(
        "milestone-4-openevolve-adapter" in failure
        and "src/agades_pqc_gym/openevolve_adapter/evaluator.py" in failure
        for failure in checks["runbook-milestone-coverage"]["failures"]
    )


def test_runbook_audit_rejects_missing_family_plugin_module(
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
        / "src"
        / "agades_pqc_gym"
        / "families"
        / "hash_based"
        / "plugin.py"
    ).unlink()

    audit = build_runbook_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["runbook-family-agnostic-core"]["status"] == "failed"
    assert any(
        "hash_based" in failure
        and "src/agades_pqc_gym/families/hash_based/plugin.py" in failure
        for failure in checks["runbook-family-agnostic-core"]["failures"]
    )


def test_runbook_audit_rejects_registry_plugin_alignment_drift(
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
    alignment = registry["plugin_manifest_alignment"]
    alignment["committed_manifest_synced"] = False
    alignment["implementation_module_digest_count"] = 17
    alignment["registry_runtime_adapter_entries_match_manifest"] = False
    registry_path.write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    audit = build_runbook_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    evidence = checks["runbook-family-agnostic-core"]["evidence"]
    failures = checks["runbook-family-agnostic-core"]["failures"]
    assert audit["accepted"] is False
    assert checks["runbook-family-agnostic-core"]["status"] == "failed"
    assert evidence["family_registry_plugin_manifest_synced"] is False
    assert evidence["family_registry_plugin_manifest_module_digest_count"] == 17
    assert (
        evidence["family_registry_runtime_adapter_entries_match_plugin_manifest"]
        is False
    )
    assert (
        "Family registry manifest is not synchronized with the family plugin "
        "manifest."
    ) in failures
    assert (
        "Family registry plugin manifest digest evidence is incomplete."
        in failures
    )
    assert (
        "Family registry runtime adapters do not match the plugin manifest."
        in failures
    )


def test_runbook_audit_rejects_non_importable_core_symbol_module(
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
    target_module = copied_root / "src" / "agades_pqc_gym" / "core" / "target.py"
    target_module.write_text(
        target_module.read_text(encoding="utf-8").replace(
            "from __future__ import annotations\n",
            (
                "from __future__ import annotations\n"
                "import missing_agades_core_dependency\n"
            ),
            1,
        ),
        encoding="utf-8",
    )

    audit = build_runbook_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["runbook-family-agnostic-core"]["status"] == "failed"
    assert any(
        "TargetSpec" in failure
        and "agades_pqc_gym.core.TargetSpec" in failure
        and "ModuleNotFoundError" in failure
        for failure in checks["runbook-family-agnostic-core"]["failures"]
    )


def test_runbook_audit_rejects_non_importable_family_plugin_module(
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
    validators_module = (
        copied_root
        / "src"
        / "agades_pqc_gym"
        / "families"
        / "hash_based"
        / "validators.py"
    )
    validators_module.write_text(
        validators_module.read_text(encoding="utf-8").replace(
            "from __future__ import annotations\n",
            (
                "from __future__ import annotations\n"
                "import missing_hash_validator_dependency\n"
            ),
            1,
        ),
        encoding="utf-8",
    )

    audit = build_runbook_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["runbook-family-agnostic-core"]["status"] == "failed"
    assert any(
        "hash_based" in failure
        and "agades_pqc_gym.families.hash_based.validators" in failure
        and "ModuleNotFoundError" in failure
        for failure in checks["runbook-family-agnostic-core"]["failures"]
    )


def test_runbook_audit_imports_all_family_implementation_modules() -> None:
    audit = build_runbook_audit()
    checks = {check["id"]: check for check in audit["checks"]}
    evidence = checks["runbook-family-agnostic-core"]["evidence"]

    assert evidence["family_plugin_module_digest_count"] == 55
    assert evidence["family_plugin_module_import_count"] == 55
    assert (
        evidence["family_registry_plugin_manifest_module_digest_count"]
        == evidence["family_plugin_module_digest_count"]
    )
    assert sorted(evidence["family_plugin_module_digests"]) == sorted(
        evidence["family_plugin_modules"]
    )
    assert all(
        sorted(evidence["family_plugin_module_digests"][family])
        == evidence["family_plugin_modules"][family]
        for family in evidence["family_plugin_modules"]
    )
    assert (
        "src/agades_pqc_gym/families/code_based/hqc_fixture_estimator.py"
        in evidence["family_plugin_modules"]["code_based"]
    )
    assert (
        "agades_pqc_gym.families.code_based.hqc_fixture_estimator"
        in evidence["family_plugin_module_imports"]["code_based"]
    )
    assert (
        "src/agades_pqc_gym/families/hash_based/bound_estimator.py"
        in evidence["family_plugin_modules"]["hash_based"]
    )
    assert (
        "agades_pqc_gym.families.hash_based.bound_estimator"
        in evidence["family_plugin_module_imports"]["hash_based"]
    )


def test_runbook_audit_rejects_non_importable_family_implementation_module(
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
    estimator_module = (
        copied_root
        / "src"
        / "agades_pqc_gym"
        / "families"
        / "hash_based"
        / "bound_estimator.py"
    )
    estimator_module.write_text(
        estimator_module.read_text(encoding="utf-8").replace(
            "from __future__ import annotations\n",
            (
                "from __future__ import annotations\n"
                "import missing_hash_bound_estimator_dependency\n"
            ),
            1,
        ),
        encoding="utf-8",
    )

    audit = build_runbook_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["runbook-family-agnostic-core"]["status"] == "failed"
    assert any(
        "hash_based" in failure
        and "agades_pqc_gym.families.hash_based.bound_estimator" in failure
        and "ModuleNotFoundError" in failure
        for failure in checks["runbook-family-agnostic-core"]["failures"]
    )


def test_runbook_audit_rejects_missing_source_input_manifest(
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
    (copied_root / "docs" / "runbook_input_manifest.json").unlink()

    audit = build_runbook_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["runbook-source-input-manifest"]["status"] == "failed"
    assert checks["runbook-source-input-manifest"]["failures"] == [
        "docs/runbook_input_manifest.json is not checked in."
    ]


def test_runbook_input_manifest_is_digest_only_and_verifiable(
    tmp_path: Path,
) -> None:
    out = tmp_path / "runbook_input_manifest.json"
    brief = tmp_path / "brief.md"
    brief.write_text(
        "\n".join(
            [
                "Agades PQC Gym v3 multi-family architecture",
                "TargetSpec AttackPlan AttackOperator AssumptionSet",
                "EvaluatorResult FitnessReport TraceRecord ReportGenerator",
                "Public/private redaction layer",
                "lattice/ code_based/ multivariate/ hash_based/",
                "isogeny_historical/ implementation_security/",
                "Lattice Estimator universal PQC oracle applicability validator",
                "Hugging Face Prime Intellect NVIDIA GitHub",
            ]
        ),
        encoding="utf-8",
    )
    context = tmp_path / "context.md"
    context.write_text(
        "\n".join(
            [
                "Hugging Face Prime Intellect NVIDIA community surfaces.",
                "post-quantum-crypto-fr post-quantum-crypto-en Q-GRID/pqc-ssl-scans",
                "facebook/TAPAS facebookresearch/LWE-benchmarking",
                "PQClean liboqs pqm4 PQ Code Package",
                "KAT ACVP dudect ctgrind TIMECOP",
                "OpenEvolve DeepEvolve evolutionary trace evaluator",
                "private traces moat security claim",
            ]
        ),
        encoding="utf-8",
    )

    manifest = write_runbook_input_manifest(
        out,
        brief_path=brief,
        context_path=context,
    )
    verification = verify_runbook_input_manifest(out)

    assert manifest == build_runbook_input_manifest(
        brief_path=brief,
        context_path=context,
    )
    assert verification == {
        "accepted": True,
        "failures": [],
        "summary": {
            "input_count": 2,
            "project_context_sha256": hashlib.sha256(
                context.read_bytes()
            ).hexdigest(),
            "source_brief_sha256": hashlib.sha256(brief.read_bytes()).hexdigest(),
            "source_input_ids": ["project_context", "source_brief"],
            "stores_absolute_paths": False,
            "stores_source_text": False,
        },
    }
    assert manifest["safety"] == {
        "stores_absolute_paths": False,
        "stores_source_text": False,
    }
    assert all(
        "/" not in source_input["source_label"]
        for source_input in manifest["source_inputs"]
    )
    legacy_product_name = " ".join(["Agades", "Cryptanalysis", "Gym"])
    legacy_package_name = "_".join(["agades", "crypto", "gym"])
    assert legacy_product_name not in json.dumps(manifest)
    assert legacy_package_name not in json.dumps(manifest)


def test_runbook_input_manifest_verify_rejects_source_text_leak(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runbook_input_manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "agades.pqc.runbook_input_manifest.v1",
                "source_inputs": [
                    {
                        "anchor_groups": {},
                        "id": "source_brief",
                        "kind": "source_brief",
                        "line_count": 1,
                        "sha256": "0" * 64,
                        "source_label": "brief.md",
                        "source_text": "private local prompt text",
                    },
                    {
                        "anchor_groups": {},
                        "id": "project_context",
                        "kind": "project_context",
                        "line_count": 1,
                        "sha256": "1" * 64,
                        "source_label": "/local/context.md",
                    },
                ],
                "safety": {
                    "stores_absolute_paths": False,
                    "stores_source_text": False,
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    verification = verify_runbook_input_manifest(path)

    assert verification["accepted"] is False
    assert "Runbook input manifest must not store source text." in verification[
        "failures"
    ]
    assert "Runbook input manifest must not store absolute paths." in verification[
        "failures"
    ]


def test_runbook_audit_rejects_missing_collaboration_brief(
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
    (copied_root / "docs" / "MARTIN_ALBRECHT_COLLABORATION_BRIEF.md").unlink()

    audit = build_runbook_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["runbook-deliverable-artifacts"]["status"] == "failed"
    assert any(
        "docs/MARTIN_ALBRECHT_COLLABORATION_BRIEF.md" in failure
        for failure in checks["runbook-deliverable-artifacts"]["failures"]
    )


def test_runbook_audit_rejects_missing_estimator_integration_template(
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
        copied_root / ".github" / "ISSUE_TEMPLATE" / "estimator_integration.yml"
    ).unlink(missing_ok=True)

    audit = build_runbook_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["runbook-deliverable-artifacts"]["status"] == "failed"
    assert any(
        ".github/ISSUE_TEMPLATE/estimator_integration.yml" in failure
        for failure in checks["runbook-deliverable-artifacts"]["failures"]
    )


def test_runbook_audit_reports_missing_machine_manifest(
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
    (copied_root / "hf" / "dataset" / "dataset_info.json").unlink()

    audit = build_runbook_audit(copied_root)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["runbook-ecosystem-counts"]["status"] == "failed"
    assert any(
        "hf/dataset/dataset_info.json" in failure
        for failure in checks["runbook-ecosystem-counts"]["failures"]
    )


def test_runbook_audit_accepts_source_brief_anchor(tmp_path: Path) -> None:
    brief = tmp_path / "brief.md"
    brief.write_text(
        "\n".join(
            [
                "Agades PQC Gym v3 multi-family architecture",
                "Family-agnostic core:",
                "TargetSpec AttackPlan AttackOperator AssumptionSet",
                "EvaluatorResult FitnessReport TraceRecord ReportGenerator",
                "Public/private redaction layer",
                "Family plugins:",
                "lattice/ code_based/ multivariate/ hash_based/",
                "isogeny_historical/ implementation_security/",
                "The Lattice Estimator is not a universal PQC oracle.",
                "Every family needs its own applicability validator.",
                "Hugging Face, Prime Intellect, NVIDIA, and GitHub surfaces.",
                "No real private evolution traces and not a security claim.",
            ]
        ),
        encoding="utf-8",
    )

    audit = build_runbook_audit(brief_path=brief)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is True
    assert audit["summary"] == {
        "artifact_count": 47,
        "failed": 0,
        "passed": 8,
        "total": 8,
    }
    assert checks["runbook-source-brief"]["status"] == "passed"
    assert checks["runbook-source-brief"]["evidence"]["brief_path"] == str(brief)
    assert len(checks["runbook-source-brief"]["evidence"]["sha256"]) == 64
    assert checks["runbook-source-brief"]["evidence"]["project_name_override"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "repository_slug": "agades-pqc-gym",
    }


def test_runbook_audit_rejects_source_brief_without_multifamily_core(
    tmp_path: Path,
) -> None:
    brief = tmp_path / "brief.md"
    brief.write_text(
        "Agades PQC Gym notes without the required architecture anchors.\n",
        encoding="utf-8",
    )

    audit = build_runbook_audit(brief_path=brief)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["runbook-source-brief"]["status"] == "failed"
    assert any(
        "TargetSpec" in failure
        for failure in checks["runbook-source-brief"]["failures"]
    )


def test_runbook_audit_accepts_project_context_anchor(tmp_path: Path) -> None:
    context = tmp_path / "context.md"
    context.write_text(
        "\n".join(
            [
                "Agades project context for PQC evaluator design.",
                "Hugging Face Prime Intellect NVIDIA community surfaces.",
                "post-quantum-crypto-fr post-quantum-crypto-en Q-GRID/pqc-ssl-scans",
                "facebook/TAPAS and facebookresearch/LWE-benchmarking for LWE.",
                "PQClean liboqs pqm4 PQ Code Package implementation seeds.",
                "KAT ACVP dudect ctgrind TIMECOP evaluator gates.",
                "OpenEvolve DeepEvolve evolutionary trace evaluator.",
                "Private traces, moat, and no public security claim.",
            ]
        ),
        encoding="utf-8",
    )

    audit = build_runbook_audit(context_path=context)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is True
    assert audit["summary"] == {
        "artifact_count": 47,
        "failed": 0,
        "passed": 8,
        "total": 8,
    }
    assert checks["runbook-project-context"]["status"] == "passed"
    assert checks["runbook-project-context"]["evidence"]["context_path"] == str(
        context
    )
    assert len(checks["runbook-project-context"]["evidence"]["sha256"]) == 64
    assert "facebook/TAPAS" in checks["runbook-project-context"]["evidence"][
        "dataset_terms"
    ]


def test_runbook_audit_rejects_project_context_without_evaluator_anchors(
    tmp_path: Path,
) -> None:
    context = tmp_path / "context.md"
    context.write_text(
        "Agades project context without the evaluator-first anchors.\n",
        encoding="utf-8",
    )

    audit = build_runbook_audit(context_path=context)

    checks = {check["id"]: check for check in audit["checks"]}
    assert audit["accepted"] is False
    assert checks["runbook-project-context"]["status"] == "failed"
    assert any(
        "OpenEvolve" in failure
        for failure in checks["runbook-project-context"]["failures"]
    )


def test_runbook_audit_cli_writes_audit(tmp_path: Path) -> None:
    out = tmp_path / "runbook_audit.json"

    result = CliRunner().invoke(app, ["runbook-audit", "--out", str(out)])

    assert result.exit_code == 0
    assert f"runbook_audit={out}" in result.output
    assert json.loads(out.read_text())["accepted"] is True


def test_runbook_audit_cli_accepts_brief_anchor(tmp_path: Path) -> None:
    out = tmp_path / "runbook_audit.json"
    brief = tmp_path / "brief.md"
    brief.write_text(
        "\n".join(
            [
                "Agades PQC Gym v3 multi-family architecture",
                "TargetSpec AttackPlan AttackOperator AssumptionSet",
                "EvaluatorResult FitnessReport TraceRecord ReportGenerator",
                "Public/private redaction layer",
                "lattice/ code_based/ multivariate/ hash_based/",
                "isogeny_historical/ implementation_security/",
                "Lattice Estimator",
                "universal PQC oracle",
                "applicability validator",
                "Hugging Face Prime Intellect NVIDIA GitHub",
            ]
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        ["runbook-audit", "--brief", str(brief), "--out", str(out)],
    )

    assert result.exit_code == 0
    payload = json.loads(out.read_text())
    assert payload["accepted"] is True
    assert payload["summary"]["total"] == 8


def test_runbook_audit_cli_accepts_brief_and_context_anchors(
    tmp_path: Path,
) -> None:
    out = tmp_path / "runbook_audit.json"
    brief = tmp_path / "brief.md"
    brief.write_text(
        "\n".join(
            [
                "Agades PQC Gym v3 multi-family architecture",
                "TargetSpec AttackPlan AttackOperator AssumptionSet",
                "EvaluatorResult FitnessReport TraceRecord ReportGenerator",
                "Public/private redaction layer",
                "lattice/ code_based/ multivariate/ hash_based/",
                "isogeny_historical/ implementation_security/",
                "Lattice Estimator",
                "universal PQC oracle",
                "applicability validator",
                "Hugging Face Prime Intellect GitHub",
            ]
        ),
        encoding="utf-8",
    )
    context = tmp_path / "context.md"
    context.write_text(
        "\n".join(
            [
                "Hugging Face Prime Intellect NVIDIA community surfaces.",
                "post-quantum-crypto-fr post-quantum-crypto-en Q-GRID/pqc-ssl-scans",
                "facebook/TAPAS facebookresearch/LWE-benchmarking",
                "PQClean liboqs pqm4 PQ Code Package",
                "KAT ACVP dudect ctgrind TIMECOP",
                "OpenEvolve DeepEvolve evolutionary trace evaluator",
                "private traces moat security claim",
            ]
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "runbook-audit",
            "--brief",
            str(brief),
            "--context",
            str(context),
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(out.read_text())
    assert payload["accepted"] is True
    assert payload["summary"]["total"] == 9


def test_runbook_input_manifest_cli_writes_and_verifies(tmp_path: Path) -> None:
    out = tmp_path / "runbook_input_manifest.json"
    brief = tmp_path / "brief.md"
    brief.write_text(
        "\n".join(
            [
                "Agades PQC Gym v3 multi-family architecture",
                "TargetSpec AttackPlan AttackOperator AssumptionSet",
                "EvaluatorResult FitnessReport TraceRecord ReportGenerator",
                "Public/private redaction layer",
                "lattice/ code_based/ multivariate/ hash_based/",
                "isogeny_historical/ implementation_security/",
                "Lattice Estimator universal PQC oracle applicability validator",
                "Hugging Face Prime Intellect NVIDIA GitHub",
            ]
        ),
        encoding="utf-8",
    )
    context = tmp_path / "context.md"
    context.write_text(
        "\n".join(
            [
                "Hugging Face Prime Intellect NVIDIA community surfaces.",
                "post-quantum-crypto-fr post-quantum-crypto-en Q-GRID/pqc-ssl-scans",
                "facebook/TAPAS facebookresearch/LWE-benchmarking",
                "PQClean liboqs pqm4 PQ Code Package",
                "KAT ACVP dudect ctgrind TIMECOP",
                "OpenEvolve DeepEvolve evolutionary trace evaluator",
                "private traces moat security claim",
            ]
        ),
        encoding="utf-8",
    )

    write_result = CliRunner().invoke(
        app,
        [
            "runbook-input-manifest",
            "--brief",
            str(brief),
            "--context",
            str(context),
            "--out",
            str(out),
        ],
    )
    verify_result = CliRunner().invoke(
        app,
        ["runbook-input-manifest-verify", "--manifest", str(out)],
    )

    assert write_result.exit_code == 0
    assert f"runbook_input_manifest={out}" in write_result.output
    assert verify_result.exit_code == 0
    assert json.loads(out.read_text())["schema_version"] == (
        "agades.pqc.runbook_input_manifest.v1"
    )
