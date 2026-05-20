from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.family_support import (
    build_family_support_matrix,
    summarize_family_support_matrix,
)
from agades_pqc_gym.integrations.prime_environment_manifest import (
    verify_prime_environment_manifest,
)
from agades_pqc_gym.integrations.prime_publication_handoff import (
    verify_prime_publication_handoff,
)
from agades_pqc_gym.integrations.public_run_export import verify_public_run_export
from agades_pqc_gym.integrations.source_catalog import (
    build_source_catalog,
    summarize_source_catalog_scope,
)

PRIME_SPEEDRUN_HANDOFF_SCHEMA = "agades.pqc.prime_speedrun_handoff.v1"
PRIME_SPEEDRUN_HANDOFF_VERIFICATION_SCHEMA = (
    "agades.pqc.prime_speedrun_handoff_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
PROJECT = {
    "name": "Agades PQC Gym",
    "package": "agades_pqc_gym",
    "cli": "agades-pqc",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
}
PLATFORM = {
    "ecosystem": "prime_intellect",
    "handoff_status": "local_public_speedrun_packet_ready_external_execution_blocked",
    "environment_docs_url": "https://docs.primeintellect.ai/verifiers/environments",
    "autonomous_speedrunning_archive_url": (
        "https://github.com/PrimeIntellect-ai/experiments-autonomous-speedrunning"
    ),
    "auto_nanogpt_story_url": "https://www.primeintellect.ai/auto-nanogpt",
}
ENVIRONMENT_MANIFEST_PATH = Path(
    "prime_intellect/verifiers_environment/prime_manifest.json"
)
PRIME_PUBLICATION_HANDOFF_PATH = Path("docs/prime_publication_handoff.json")
PUBLIC_RUN_EXPORT_PATH = Path("public/run_export")
SPEEDRUN_ARTIFACT_PATHS = [
    "docs/prime_publication_handoff.json",
    "prime_intellect/verifiers_environment/prime_manifest.json",
    "prime_intellect/verifiers_environment/agades_pqc_verifier_env.py",
    "prime_intellect/verifiers_environment/README.md",
    "prime_intellect/schemas/task_metadata.schema.json",
    "prime_intellect/schemas/verifier_result.schema.json",
    "docs/source_catalog.json",
    "public/run_export/manifest.json",
    "public/run_export/runs.jsonl",
    "public/run_export/runs.csv",
    "public/run_export/MANIFEST.sha256",
]
AUTONOMY_HARNESS_PATHS = [
    "AGENTS.md",
    "docs/PLAN.md",
    "docs/IMPLEMENT.md",
    "docs/STATUS.md",
    "public/run_export/manifest.json",
    "docs/private_run_policy.json",
]
AUTONOMY_HARNESS_ROLES = {
    "AGENTS.md": "repository-level safety and code-quality rules",
    "docs/PLAN.md": "stable milestone plan",
    "docs/IMPLEMENT.md": "reproducible command runbook",
    "docs/STATUS.md": "durable long-running implementation log",
    "public/run_export/manifest.json": "public run observability export",
    "docs/private_run_policy.json": "private moat and release boundary",
}
AUTONOMY_SOURCE_PATTERN = {
    "agent_rules_file": "AGENTS.md",
    "mission_context_file": "goal.md",
    "mutable_plan_file": "plan.md",
    "durable_thread_log": "scratchpad/THREAD.md",
    "released_observability_artifacts": [
        "scratchpads",
        "run logs",
        "scripts",
        "configs",
    ],
}
SOURCE_ANCHORS = [
    {
        "id": "prime-verifiers",
        "source_catalog_required": True,
        "current_use": "current_verifier_packaging",
    },
    {
        "id": "prime-quickstart",
        "source_catalog_required": True,
        "current_use": "current_operator_onboarding_reference",
    },
    {
        "id": "prime-autonomous-speedrunning-experiments",
        "source_catalog_required": True,
        "current_use": "public_evaluator_observability_pattern",
    },
    {
        "id": "prime-autonanogpt-speedrun",
        "source_catalog_required": True,
        "current_use": "public_benchmark_story_anchor",
    },
]
EXPECTED_FALSE_SAFETY_FLAGS = (
    "contains_private_traces",
    "publishes_private_candidates",
    "publishes_private_scratchpads",
    "arbitrary_code_execution",
    "live_targeting",
    "security_claim",
    "claims_external_execution",
    "claims_external_publication",
)
REVIEW_REQUIRED_BEFORE_EXTERNAL_EXECUTION = [
    "Confirm Prime credentials, organization, and target namespace.",
    "Run Prime environment smoke and local package build.",
    "Run release audit and publication preflight.",
    "Start with a private or unlisted Prime environment execution.",
    "Record external run URLs only after reviewer approval.",
]
REQUIRED_RELEASE_GATES = [
    "uv run pytest tests/test_prime_speedrun_handoff.py -q",
    "uv run agades-pqc prime-speedrun-handoff --out "
    "docs/prime_speedrun_handoff.json",
    "uv run agades-pqc prime-speedrun-handoff-verify --handoff "
    "docs/prime_speedrun_handoff.json",
    "uv run agades-pqc prime-manifest-verify --manifest "
    "prime_intellect/verifiers_environment/prime_manifest.json",
    "uv run agades-pqc prime-publication-handoff-verify --handoff "
    "docs/prime_publication_handoff.json",
    "uv run agades-pqc public-run-export-verify --export public/run_export",
    "uv build prime_intellect/verifiers_environment",
    "uv run agades-pqc ecosystem-smoke-verify --report "
    "reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
]


def build_prime_speedrun_handoff(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    environment_manifest = _read_json(project_root / ENVIRONMENT_MANIFEST_PATH)
    environment_verification = verify_prime_environment_manifest(
        ENVIRONMENT_MANIFEST_PATH,
        root=project_root,
    )
    publication_handoff_verification = verify_prime_publication_handoff(
        PRIME_PUBLICATION_HANDOFF_PATH,
        root=project_root,
    )
    public_run_export_verification = verify_public_run_export(
        PUBLIC_RUN_EXPORT_PATH,
        root=project_root,
    )
    public_run_manifest = _read_json(
        project_root / PUBLIC_RUN_EXPORT_PATH / "manifest.json"
    )
    task_manifest = _dict_or_empty(environment_manifest.get("task_manifest"))
    evaluation_defaults = _dict_or_empty(
        environment_manifest.get("evaluation_defaults")
    )
    project = _dict_or_empty(environment_manifest.get("project"))
    scoring_contract = _dict_or_empty(environment_manifest.get("scoring_contract"))
    public_run_summary = _dict_or_empty(public_run_manifest.get("summary"))

    return {
        "schema_version": PRIME_SPEEDRUN_HANDOFF_SCHEMA,
        "project": dict(PROJECT),
        "platform": dict(PLATFORM),
        "prime_verifiers_alignment": {
            "environment_manifest": ENVIRONMENT_MANIFEST_PATH.as_posix(),
            "environment_package": project.get("environment_package"),
            "entrypoint": project.get("entrypoint"),
            "environment_type": "SingleTurnEnv",
            "dataset_row_fields": ["answer", "info", "prompt"],
            "task_count": task_manifest.get("task_count"),
            "family_count": len(task_manifest.get("families", [])),
            "num_examples_default": evaluation_defaults.get("num_examples"),
            "rollouts_per_example_default": evaluation_defaults.get(
                "rollouts_per_example"
            ),
            "json_only_reward": (
                scoring_contract.get("requires_single_json_object") is True
                and scoring_contract.get("accepts_executable_code") is False
            ),
        },
        "public_speedrun_alignment": {
            "public_run_export": PUBLIC_RUN_EXPORT_PATH.as_posix(),
            "public_run_export_accepted": public_run_export_verification["accepted"],
            "bundle_count": public_run_summary.get("bundle_count"),
            "run_count": public_run_summary.get("run_count"),
            "artifact_formats": ["manifest.json", "runs.jsonl", "runs.csv"],
            "observable_loop": [
                "select_public_prime_task",
                "submit_single_json_attack_plan",
                "score_with_deterministic_verifier",
                "review_before_public_run_export_update",
            ],
            "publishes_private_scratchpads": False,
            "publishes_private_candidates": False,
        },
        "autonomy_harness_alignment": _autonomy_harness_alignment(project_root),
        "local_readiness": {
            "prime_environment_manifest_accepted": environment_verification[
                "accepted"
            ],
            "prime_publication_handoff_accepted": publication_handoff_verification[
                "accepted"
            ],
            "public_run_export_accepted": public_run_export_verification["accepted"],
            "external_execution_requires_review": True,
            "credentials_present_in_artifact": False,
            "external_execution_performed": False,
        },
        "source_anchors": list(SOURCE_ANCHORS),
        "family_support": summarize_family_support_matrix(
            build_family_support_matrix(root=project_root)
        ),
        "source_catalog_scope": summarize_source_catalog_scope(
            build_source_catalog()
        ),
        "local_artifacts": {
            "artifact_paths": list(SPEEDRUN_ARTIFACT_PATHS),
            "artifact_sha256": _artifact_sha256(
                project_root,
                SPEEDRUN_ARTIFACT_PATHS,
            ),
        },
        "safety": {
            "contains_private_traces": False,
            "publishes_private_candidates": False,
            "publishes_private_scratchpads": False,
            "arbitrary_code_execution": False,
            "live_targeting": False,
            "security_claim": False,
            "claims_external_execution": False,
            "claims_external_publication": False,
        },
        "review_required_before_external_execution": list(
            REVIEW_REQUIRED_BEFORE_EXTERNAL_EXECUTION
        ),
        "release_gates": list(REQUIRED_RELEASE_GATES),
    }


def write_prime_speedrun_handoff(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    handoff = build_prime_speedrun_handoff(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(handoff, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return handoff


def verify_prime_speedrun_handoff(
    handoff_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    handoff = _read_handoff(handoff_path, project_root, failures)

    if handoff:
        expected = build_prime_speedrun_handoff(root=project_root)
        if handoff != expected:
            failures.append("Prime speedrun handoff is not in sync.")
        _verify_project(handoff, failures)
        _verify_platform(handoff, failures)
        _verify_prime_verifiers_alignment(handoff, failures)
        _verify_public_speedrun_alignment(handoff, failures)
        _verify_autonomy_harness_alignment(project_root, handoff, failures)
        _verify_local_readiness(handoff, failures)
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
        failures.append(f"Prime speedrun handoff is missing: {handoff_path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Prime speedrun handoff is invalid JSON at line {exc.lineno}."
        )
        return {}

    if not isinstance(payload, dict):
        failures.append("Prime speedrun handoff must be a JSON object.")
        return {}
    return payload


def _verify_project(handoff: dict[str, Any], failures: list[str]) -> None:
    if handoff.get("schema_version") != PRIME_SPEEDRUN_HANDOFF_SCHEMA:
        failures.append(
            "Prime speedrun handoff schema_version must be "
            f"{PRIME_SPEEDRUN_HANDOFF_SCHEMA}."
        )
    if handoff.get("project") != PROJECT:
        failures.append("Prime speedrun handoff project metadata drifted.")


def _verify_platform(handoff: dict[str, Any], failures: list[str]) -> None:
    platform = handoff.get("platform")
    if not isinstance(platform, dict):
        failures.append("Prime speedrun handoff platform must be an object.")
        return
    if platform != PLATFORM:
        failures.append("Prime speedrun handoff platform metadata drifted.")


def _verify_prime_verifiers_alignment(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    alignment = handoff.get("prime_verifiers_alignment")
    if not isinstance(alignment, dict):
        failures.append("Prime speedrun handoff verifier alignment must be an object.")
        return
    if alignment.get("environment_manifest") != ENVIRONMENT_MANIFEST_PATH.as_posix():
        failures.append("Prime speedrun handoff environment manifest drifted.")
    if alignment.get("environment_package") != "agades-pqc-verifier-env":
        failures.append("Prime speedrun handoff package name drifted.")
    if alignment.get("entrypoint") != "agades_pqc_verifier_env:load_environment":
        failures.append("Prime speedrun handoff entrypoint drifted.")
    if alignment.get("environment_type") != "SingleTurnEnv":
        failures.append("Prime speedrun handoff environment type drifted.")
    if alignment.get("dataset_row_fields") != ["answer", "info", "prompt"]:
        failures.append("Prime speedrun handoff dataset row fields drifted.")
    if not isinstance(alignment.get("task_count"), int) or (
        alignment.get("task_count", 0) <= 0
    ):
        failures.append("Prime speedrun handoff task_count must be positive.")
    if not isinstance(alignment.get("family_count"), int) or (
        alignment.get("family_count", 0) <= 0
    ):
        failures.append("Prime speedrun handoff family_count must be positive.")
    if alignment.get("json_only_reward") is not True:
        failures.append("Prime speedrun handoff does not preserve JSON-only reward.")


def _verify_public_speedrun_alignment(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    alignment = handoff.get("public_speedrun_alignment")
    if not isinstance(alignment, dict):
        failures.append("Prime speedrun handoff public alignment must be an object.")
        return
    if alignment.get("public_run_export") != PUBLIC_RUN_EXPORT_PATH.as_posix():
        failures.append("Prime speedrun handoff public run export path drifted.")
    if alignment.get("public_run_export_accepted") is not True:
        failures.append("Prime speedrun handoff public run export is not accepted.")
    if not isinstance(alignment.get("bundle_count"), int) or (
        alignment.get("bundle_count", 0) <= 0
    ):
        failures.append("Prime speedrun handoff bundle_count must be positive.")
    if not isinstance(alignment.get("run_count"), int) or (
        alignment.get("run_count", 0) <= 0
    ):
        failures.append("Prime speedrun handoff run_count must be positive.")
    if alignment.get("artifact_formats") != ["manifest.json", "runs.jsonl", "runs.csv"]:
        failures.append("Prime speedrun handoff artifact formats drifted.")
    if alignment.get("publishes_private_scratchpads") is not False:
        failures.append("Prime speedrun handoff may publish private scratchpads.")
    if alignment.get("publishes_private_candidates") is not False:
        failures.append("Prime speedrun handoff may publish private candidates.")


def _verify_autonomy_harness_alignment(
    root: Path,
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    alignment = handoff.get("autonomy_harness_alignment")
    if not isinstance(alignment, dict):
        failures.append(
            "Prime speedrun handoff autonomy harness alignment must be an object."
        )
        return
    expected = _autonomy_harness_alignment(root)
    if alignment.get("source_anchor_id") != "prime-autonanogpt-speedrun":
        failures.append("Prime speedrun handoff autonomy source anchor drifted.")
    if alignment.get("source_pattern") != AUTONOMY_SOURCE_PATTERN:
        failures.append("Prime speedrun handoff autonomy source pattern drifted.")
    if alignment.get("agades_public_harness_paths") != AUTONOMY_HARNESS_PATHS:
        failures.append("Prime speedrun handoff autonomy harness paths drifted.")
    if alignment.get("agades_public_harness_roles") != AUTONOMY_HARNESS_ROLES:
        failures.append("Prime speedrun handoff autonomy harness roles drifted.")
    if alignment.get("public_harness_paths_exist") is not True:
        failures.append("Prime speedrun handoff public harness paths are missing.")
    for path in AUTONOMY_HARNESS_PATHS:
        if not (root / path).is_file():
            failures.append(
                f"Prime speedrun handoff autonomy harness path is missing: {path}."
            )
    if alignment.get("external_prime_autonomous_run_performed") is not False:
        failures.append("Prime speedrun handoff claims Prime autonomous execution.")
    if alignment.get("publishes_private_scratchpads") is not False:
        failures.append("Prime speedrun handoff may publish private scratchpads.")
    if alignment.get("publishes_private_evolution_traces") is not False:
        failures.append("Prime speedrun handoff may publish private evolution traces.")
    if alignment.get("publishes_private_candidate_payloads") is not False:
        failures.append(
            "Prime speedrun handoff may publish private candidate payloads."
        )
    if alignment.get("review_required_before_prime_autonomy") is not True:
        failures.append("Prime speedrun handoff lacks Prime autonomy review.")
    if alignment != expected:
        failures.append("Prime speedrun handoff autonomy harness alignment drifted.")


def _verify_local_readiness(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    readiness = handoff.get("local_readiness")
    if not isinstance(readiness, dict):
        failures.append("Prime speedrun handoff local_readiness must be an object.")
        return
    if readiness.get("prime_environment_manifest_accepted") is not True:
        failures.append("Prime speedrun handoff environment manifest is not accepted.")
    if readiness.get("prime_publication_handoff_accepted") is not True:
        failures.append("Prime speedrun handoff publication handoff is not accepted.")
    if readiness.get("public_run_export_accepted") is not True:
        failures.append("Prime speedrun handoff public run export is not accepted.")
    if readiness.get("external_execution_requires_review") is not True:
        failures.append("Prime speedrun handoff lacks external execution review.")
    if readiness.get("credentials_present_in_artifact") is not False:
        failures.append("Prime speedrun handoff must not include credential evidence.")
    if readiness.get("external_execution_performed") is not False:
        failures.append("Prime speedrun handoff must not claim external execution.")


def _verify_source_anchors(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    if handoff.get("source_anchors") != SOURCE_ANCHORS:
        failures.append("Prime speedrun handoff source anchors drifted.")
    source_catalog = build_source_catalog()
    source_by_id = {source["id"]: source for source in source_catalog["sources"]}
    for anchor in SOURCE_ANCHORS:
        source = source_by_id.get(anchor["id"])
        if source is None:
            failures.append(
                f"Prime speedrun source catalog anchor is missing: {anchor['id']}."
            )
        elif source.get("current_use") != anchor["current_use"]:
            failures.append(
                "Prime speedrun source catalog anchor current_use drifted: "
                f"{anchor['id']}."
            )


def _verify_family_support(
    handoff: dict[str, Any],
    expected: dict[str, Any],
    failures: list[str],
) -> None:
    family_support = handoff.get("family_support")
    if not isinstance(family_support, dict):
        failures.append("Prime speedrun handoff family_support must be an object.")
        return
    if family_support != expected:
        failures.append("Prime speedrun handoff family_support summary drifted.")
    if family_support.get("review_required_before_claims") is not True:
        failures.append(
            "Prime speedrun handoff family_support.review_required_before_claims "
            "must be true."
        )


def _verify_source_catalog_scope(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    scope = handoff.get("source_catalog_scope")
    if not isinstance(scope, dict):
        failures.append(
            "Prime speedrun handoff source_catalog_scope must be an object."
        )
        return
    if scope.get("non_lattice_toy_operator_security_claims") != 0:
        failures.append(
            "Prime speedrun handoff source catalog scope must not contain "
            "non-lattice toy security claims."
        )
    if scope.get("non_lattice_toy_evaluator_count") != scope.get("source_count"):
        failures.append(
            "Prime speedrun handoff source catalog scope must cover every source."
        )
    if scope.get("non_lattice_toy_operator_variant_count") != scope.get(
        "source_count"
    ):
        failures.append(
            "Prime speedrun handoff source catalog operator scope must cover "
            "every source."
        )


def _verify_local_artifacts(
    root: Path,
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    local_artifacts = handoff.get("local_artifacts")
    if not isinstance(local_artifacts, dict):
        failures.append("Prime speedrun handoff local_artifacts must be an object.")
        return
    artifact_paths = local_artifacts.get("artifact_paths")
    if artifact_paths != SPEEDRUN_ARTIFACT_PATHS:
        failures.append("Prime speedrun handoff artifact paths drifted.")
        artifact_paths = artifact_paths if isinstance(artifact_paths, list) else []
    artifact_sha256 = local_artifacts.get("artifact_sha256")
    if not isinstance(artifact_sha256, dict):
        failures.append("Prime speedrun handoff digest map must be an object.")
        artifact_sha256 = {}
    if set(artifact_sha256) != set(SPEEDRUN_ARTIFACT_PATHS):
        failures.append("Prime speedrun handoff digest keys drifted.")
    for artifact_path in artifact_paths:
        if not isinstance(artifact_path, str):
            failures.append("Prime speedrun handoff artifact path is invalid.")
            continue
        path = root / artifact_path
        if not path.is_file():
            failures.append(
                f"Prime speedrun handoff artifact is missing: {artifact_path}."
            )
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if artifact_sha256.get(artifact_path) != digest:
            failures.append(
                f"Prime speedrun handoff artifact digest drifted: {artifact_path}."
            )


def _verify_safety(handoff: dict[str, Any], failures: list[str]) -> None:
    safety = handoff.get("safety")
    if not isinstance(safety, dict):
        failures.append("Prime speedrun handoff safety must be an object.")
        return
    for flag in EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is False:
            continue
        if flag == "publishes_private_scratchpads":
            failures.append("Prime speedrun handoff may publish private scratchpads.")
        elif flag == "publishes_private_candidates":
            failures.append("Prime speedrun handoff may publish private candidates.")
        elif flag == "claims_external_execution":
            failures.append("Prime speedrun handoff claims external execution.")
        elif flag == "claims_external_publication":
            failures.append("Prime speedrun handoff claims external publication.")
        elif flag == "security_claim":
            failures.append("Prime speedrun handoff advertises a security claim.")
        else:
            failures.append(f"Prime speedrun handoff safety.{flag} must be false.")


def _verify_review_requirements(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    if (
        handoff.get("review_required_before_external_execution")
        != REVIEW_REQUIRED_BEFORE_EXTERNAL_EXECUTION
    ):
        failures.append("Prime speedrun handoff external execution review drifted.")


def _verify_release_gates(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    release_gates = handoff.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append("Prime speedrun handoff release_gates must be a list.")
        return
    for required_gate in REQUIRED_RELEASE_GATES:
        if required_gate not in release_gates:
            failures.append(
                f"Prime speedrun handoff release gate missing: {required_gate}"
            )


def _verification_result(
    handoff_path: Path,
    handoff: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    local_artifacts = _dict_or_empty(handoff.get("local_artifacts"))
    artifact_paths = local_artifacts.get("artifact_paths", [])
    if not isinstance(artifact_paths, list):
        artifact_paths = []
    alignment = _dict_or_empty(handoff.get("prime_verifiers_alignment"))
    public_alignment = _dict_or_empty(handoff.get("public_speedrun_alignment"))
    local_readiness = _dict_or_empty(handoff.get("local_readiness"))
    family_support = _dict_or_empty(handoff.get("family_support"))
    source_catalog_scope = _dict_or_empty(handoff.get("source_catalog_scope"))
    return {
        "schema_version": PRIME_SPEEDRUN_HANDOFF_VERIFICATION_SCHEMA,
        "handoff_path": handoff_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "artifact_count": len(artifact_paths),
            "bundle_count": public_alignment.get("bundle_count"),
            "external_execution_requires_review": local_readiness.get(
                "external_execution_requires_review"
            ),
            "failure_count": len(failures),
            "family_count": alignment.get("family_count"),
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
            "run_count": public_alignment.get("run_count"),
            "task_count": alignment.get("task_count"),
        },
        "failures": failures,
    }


def _artifact_sha256(root: Path, artifact_paths: list[str]) -> dict[str, str]:
    return {
        artifact_path: hashlib.sha256((root / artifact_path).read_bytes()).hexdigest()
        for artifact_path in artifact_paths
    }


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        msg = f"{path.as_posix()} must contain a JSON object."
        raise ValueError(msg)
    return payload


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _autonomy_harness_alignment(root: Path) -> dict[str, Any]:
    return {
        "source_anchor_id": "prime-autonanogpt-speedrun",
        "source_publication_date": "2026-05-14",
        "source_observed_date": "2026-05-18",
        "source_pattern": dict(AUTONOMY_SOURCE_PATTERN),
        "agades_public_harness_paths": list(AUTONOMY_HARNESS_PATHS),
        "agades_public_harness_roles": dict(AUTONOMY_HARNESS_ROLES),
        "public_harness_paths_exist": all(
            (root / path).is_file() for path in AUTONOMY_HARNESS_PATHS
        ),
        "external_prime_autonomous_run_performed": False,
        "publishes_private_scratchpads": False,
        "publishes_private_evolution_traces": False,
        "publishes_private_candidate_payloads": False,
        "review_required_before_prime_autonomy": True,
    }
