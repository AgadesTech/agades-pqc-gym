from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.family_support import (
    build_family_support_matrix,
    summarize_family_support_matrix,
)
from agades_pqc_gym.integrations.prime_environment_manifest import (
    verify_prime_environment_manifest,
)
from agades_pqc_gym.integrations.prime_verifier_schemas import (
    verify_prime_verifier_schemas,
)
from agades_pqc_gym.integrations.source_catalog import (
    build_source_catalog,
    summarize_source_catalog_scope,
)

PRIME_PUBLICATION_HANDOFF_SCHEMA = "agades.pqc.prime_publication_handoff.v1"
PRIME_PUBLICATION_HANDOFF_VERIFICATION_SCHEMA = (
    "agades.pqc.prime_publication_handoff_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
PROJECT = {
    "name": "Agades PQC Gym",
    "package": "agades_pqc_gym",
    "cli": "agades-pqc",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
}
ENVIRONMENT_MANIFEST_PATH = Path(
    "prime_intellect/verifiers_environment/prime_manifest.json"
)
SCHEMA_MANIFEST_PATH = Path("prime_intellect/schemas/schema_manifest.json")
RELEASE_PLAN_PATH = Path("docs/PRIME_INTELLECT_RELEASE_PLAN.md")
SCHEMA_DIR = Path("prime_intellect/schemas")
LOCAL_PACKAGE_ARTIFACT_PATHS = [
    "prime_intellect/environment_card.md",
    "prime_intellect/verifier_spec.md",
    "prime_intellect/verifiers_environment/README.md",
    "prime_intellect/verifiers_environment/pyproject.toml",
    "prime_intellect/verifiers_environment/agades_pqc_verifier_env.py",
    ENVIRONMENT_MANIFEST_PATH.as_posix(),
    "prime_intellect/schemas/attack_plan.schema.json",
    "prime_intellect/schemas/verifier_result.schema.json",
    "prime_intellect/schemas/task_metadata.schema.json",
    SCHEMA_MANIFEST_PATH.as_posix(),
]
SOURCE_ANCHORS = [
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
PRIME_QUICKSTART_ALIGNMENT = {
    "source_anchor_id": "prime-quickstart",
    "source_url": "https://app.primeintellect.ai/dashboard/home/quickstart",
    "source_observed_date": "2026-05-18",
    "onboarding_commands": [
        {
            "id": "install_prime_cli",
            "command": "uv tool install -U prime",
            "purpose": "Install the Prime CLI from the public quickstart.",
        },
        {
            "id": "browser_login",
            "command": "prime login",
            "purpose": "Authenticate the local Prime CLI session.",
        },
        {
            "id": "workspace_setup",
            "command": "prime lab setup",
            "purpose": "Prepare local agent and Prime workspace configuration.",
        },
    ],
    "reference_eval_commands": [
        {
            "id": "quick_text_eval",
            "command": (
                "prime eval run primeintellect/reverse-text "
                "-m openai/gpt-oss-20b -p prime -n 1 -r 1 -t 512 -s -A"
            ),
            "purpose": "Prime quickstart one-example evaluation smoke.",
        },
        {
            "id": "reasoning_eval",
            "command": (
                "prime eval run primeintellect/aime2026 "
                "-m openai/gpt-oss-20b -p prime -n 1 -r 1 -t 2048 -s -A"
            ),
            "purpose": "Prime quickstart reasoning evaluation example.",
        },
    ],
    "agades_environment_command": "prime eval run <owner>/agades-pqc-verifier-env",
    "requires_credentials": True,
    "requires_billing_for_hosted_compute": True,
    "external_prime_execution_performed": False,
    "credentials_checked_at_generation": False,
}
EXPECTED_FALSE_SAFETY_FLAGS = (
    "contains_private_traces",
    "arbitrary_code_execution",
    "live_targeting",
    "security_claim",
    "publishes_private_candidates",
    "claims_external_publication",
)
REVIEW_REQUIRED_BEFORE_PUBLISH = [
    "Confirm Prime account, organization, and target namespace.",
    "Run the local Prime environment build and verifier smoke gates.",
    "Review all public cards for no private traces and no security claims.",
    "Publish first as private/unlisted if Prime Hub supports the target workflow.",
    "Record external Prime Hub URL only after credentialed review.",
]
REQUIRED_RELEASE_GATES = [
    "uv run pytest tests/test_prime_publication_handoff.py -q",
    "uv run agades-pqc prime-publication-handoff --out "
    "docs/prime_publication_handoff.json",
    "uv run agades-pqc prime-publication-handoff-verify --handoff "
    "docs/prime_publication_handoff.json",
    "uv run agades-pqc prime-manifest-verify --manifest "
    "prime_intellect/verifiers_environment/prime_manifest.json",
    "uv run agades-pqc prime-schemas-verify --schemas prime_intellect/schemas",
    "uv build prime_intellect/verifiers_environment",
    "uv run agades-pqc ecosystem-smoke-verify --report "
    "reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
]


def build_prime_publication_handoff(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    environment_verification = verify_prime_environment_manifest(
        ENVIRONMENT_MANIFEST_PATH,
        root=project_root,
    )
    schemas_verification = verify_prime_verifier_schemas(
        SCHEMA_DIR,
        root=project_root,
    )
    environment_manifest = _read_json(project_root / ENVIRONMENT_MANIFEST_PATH)
    task_manifest = environment_manifest.get("task_manifest", {})
    if not isinstance(task_manifest, dict):
        task_manifest = {}
    scoring_contract = environment_manifest.get("scoring_contract", {})
    if not isinstance(scoring_contract, dict):
        scoring_contract = {}
    source_mirror = environment_manifest.get("source_mirror", {})
    if not isinstance(source_mirror, dict):
        source_mirror = {}
    release = environment_manifest.get("release", {})
    if not isinstance(release, dict):
        release = {}
    families = task_manifest.get("families", [])
    if not isinstance(families, list):
        families = []

    return {
        "schema_version": PRIME_PUBLICATION_HANDOFF_SCHEMA,
        "project": dict(PROJECT),
        "platform": {
            "ecosystem": "prime_intellect",
            "environment_package": "agades-pqc-verifier-env",
            "environment_manifest": ENVIRONMENT_MANIFEST_PATH.as_posix(),
            "schema_manifest": SCHEMA_MANIFEST_PATH.as_posix(),
            "release_plan": RELEASE_PLAN_PATH.as_posix(),
            "handoff_status": "local_package_ready_external_publication_blocked",
        },
        "local_package": {
            "artifact_paths": list(LOCAL_PACKAGE_ARTIFACT_PATHS),
            "artifact_sha256": _artifact_sha256(
                project_root,
                LOCAL_PACKAGE_ARTIFACT_PATHS,
            ),
            "build_command": "uv build prime_intellect/verifiers_environment",
            "manifest_verify_command": (
                "uv run agades-pqc prime-manifest-verify --manifest "
                "prime_intellect/verifiers_environment/prime_manifest.json"
            ),
            "schemas_verify_command": (
                "uv run agades-pqc prime-schemas-verify --schemas "
                "prime_intellect/schemas"
            ),
        },
        "readiness": {
            "local_package_ready": release.get("publication_status")
            == "local_package_ready",
            "environment_manifest_accepted": environment_verification["accepted"],
            "schemas_accepted": schemas_verification["accepted"],
            "task_count": task_manifest.get("task_count"),
            "family_count": len(families),
            "json_only_scoring": (
                scoring_contract.get("requires_single_json_object") is True
                and scoring_contract.get("accepts_executable_code") is False
            ),
            "public_examples_mirrored": source_mirror.get(
                "mirrors_valid_public_examples"
            )
            is True,
            "prime_hub_publication_performed": False,
            "requires_credentials": True,
            "credentials_checked_at_generation": False,
            "credentials_present_in_artifact": False,
            "external_publication_requires_review": True,
        },
        "source_anchors": list(SOURCE_ANCHORS),
        "family_support": summarize_family_support_matrix(
            build_family_support_matrix(root=project_root)
        ),
        "source_catalog_scope": summarize_source_catalog_scope(
            build_source_catalog()
        ),
        "prime_quickstart_alignment": deepcopy(PRIME_QUICKSTART_ALIGNMENT),
        "safety": {
            "contains_private_traces": False,
            "arbitrary_code_execution": False,
            "live_targeting": False,
            "security_claim": False,
            "publishes_private_candidates": False,
            "claims_external_publication": False,
        },
        "review_required_before_publish": list(REVIEW_REQUIRED_BEFORE_PUBLISH),
        "release_gates": list(REQUIRED_RELEASE_GATES),
    }


def write_prime_publication_handoff(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    handoff = build_prime_publication_handoff(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(handoff, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return handoff


def verify_prime_publication_handoff(
    handoff_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    handoff = _read_handoff(handoff_path, project_root, failures)

    if handoff:
        expected = build_prime_publication_handoff(root=project_root)
        if handoff != expected:
            failures.append("Prime publication handoff is not in sync.")

        _verify_project(handoff, failures)
        _verify_platform(handoff, failures)
        _verify_local_package(project_root, handoff, failures)
        _verify_readiness(handoff, failures)
        _verify_source_anchors(handoff, failures)
        _verify_family_support(handoff, expected["family_support"], failures)
        _verify_source_catalog_scope(handoff, failures)
        _verify_quickstart_alignment(handoff, failures)
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
        failures.append(f"Prime publication handoff is missing: {handoff_path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Prime publication handoff is invalid JSON at line {exc.lineno}."
        )
        return {}

    if not isinstance(payload, dict):
        failures.append("Prime publication handoff must be a JSON object.")
        return {}
    return payload


def _verify_project(handoff: dict[str, Any], failures: list[str]) -> None:
    if handoff.get("schema_version") != PRIME_PUBLICATION_HANDOFF_SCHEMA:
        failures.append(
            "Prime publication handoff schema_version must be "
            f"{PRIME_PUBLICATION_HANDOFF_SCHEMA}."
        )
    if handoff.get("project") != PROJECT:
        failures.append("Prime publication handoff project metadata drifted.")


def _verify_platform(handoff: dict[str, Any], failures: list[str]) -> None:
    platform = handoff.get("platform")
    if not isinstance(platform, dict):
        failures.append("Prime publication handoff platform must be an object.")
        return
    expected = {
        "ecosystem": "prime_intellect",
        "environment_package": "agades-pqc-verifier-env",
        "environment_manifest": ENVIRONMENT_MANIFEST_PATH.as_posix(),
        "schema_manifest": SCHEMA_MANIFEST_PATH.as_posix(),
        "release_plan": RELEASE_PLAN_PATH.as_posix(),
        "handoff_status": "local_package_ready_external_publication_blocked",
    }
    for key, expected_value in expected.items():
        if platform.get(key) != expected_value:
            failures.append(f"Prime publication handoff platform.{key} drifted.")


def _verify_local_package(
    root: Path,
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    local_package = handoff.get("local_package")
    if not isinstance(local_package, dict):
        failures.append("Prime publication handoff local_package must be an object.")
        return
    artifact_paths = local_package.get("artifact_paths")
    if artifact_paths != LOCAL_PACKAGE_ARTIFACT_PATHS:
        failures.append("Prime handoff local package artifact paths drifted.")
        artifact_paths = artifact_paths if isinstance(artifact_paths, list) else []
    artifact_sha256 = local_package.get("artifact_sha256")
    if not isinstance(artifact_sha256, dict):
        failures.append("Prime handoff local package digest map must be an object.")
        artifact_sha256 = {}
    if set(artifact_sha256) != set(LOCAL_PACKAGE_ARTIFACT_PATHS):
        failures.append("Prime handoff local package digest keys drifted.")
    for artifact_path in artifact_paths:
        if not isinstance(artifact_path, str):
            failures.append("Prime handoff local package artifact path is invalid.")
            continue
        path = root / artifact_path
        if not path.is_file():
            failures.append(f"Prime handoff artifact is missing: {artifact_path}.")
            continue
        expected_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if artifact_sha256.get(artifact_path) != expected_digest:
            failures.append(f"Prime handoff artifact digest drifted: {artifact_path}.")
    if local_package.get("build_command") != (
        "uv build prime_intellect/verifiers_environment"
    ):
        failures.append("Prime handoff package build command drifted.")
    if local_package.get("manifest_verify_command") != (
        "uv run agades-pqc prime-manifest-verify --manifest "
        "prime_intellect/verifiers_environment/prime_manifest.json"
    ):
        failures.append("Prime handoff manifest verify command drifted.")
    if local_package.get("schemas_verify_command") != (
        "uv run agades-pqc prime-schemas-verify --schemas prime_intellect/schemas"
    ):
        failures.append("Prime handoff schemas verify command drifted.")


def _verify_readiness(handoff: dict[str, Any], failures: list[str]) -> None:
    readiness = handoff.get("readiness")
    if not isinstance(readiness, dict):
        failures.append("Prime publication handoff readiness must be an object.")
        return
    if readiness.get("local_package_ready") is not True:
        failures.append("Prime handoff local package is not marked ready.")
    if readiness.get("environment_manifest_accepted") is not True:
        failures.append("Prime handoff environment manifest is not accepted.")
    if readiness.get("schemas_accepted") is not True:
        failures.append("Prime handoff schemas are not accepted.")
    if not isinstance(readiness.get("task_count"), int) or (
        readiness.get("task_count", 0) <= 0
    ):
        failures.append("Prime handoff task_count must be a positive integer.")
    if not isinstance(readiness.get("family_count"), int) or (
        readiness.get("family_count", 0) <= 0
    ):
        failures.append("Prime handoff family_count must be a positive integer.")
    if readiness.get("json_only_scoring") is not True:
        failures.append("Prime handoff does not preserve JSON-only scoring.")
    if readiness.get("public_examples_mirrored") is not True:
        failures.append("Prime handoff public examples are not mirrored.")
    if readiness.get("prime_hub_publication_performed") is not False:
        failures.append("Prime handoff must not claim Prime Hub publication.")
    if readiness.get("requires_credentials") is not True:
        failures.append("Prime handoff lacks credential boundary.")
    if readiness.get("credentials_checked_at_generation") is not False:
        failures.append("Prime handoff must not inspect credentials at generation.")
    if readiness.get("credentials_present_in_artifact") is not False:
        failures.append("Prime handoff must not include credential evidence.")
    if readiness.get("external_publication_requires_review") is not True:
        failures.append("Prime handoff lacks external publication review boundary.")


def _verify_source_anchors(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    if handoff.get("source_anchors") != SOURCE_ANCHORS:
        failures.append("Prime handoff source anchors drifted.")
    source_catalog = build_source_catalog()
    source_by_id = {source["id"]: source for source in source_catalog["sources"]}
    for anchor in SOURCE_ANCHORS:
        source = source_by_id.get(anchor["id"])
        if source is None:
            failures.append(f"Prime source catalog anchor is missing: {anchor['id']}.")
        elif source.get("current_use") != anchor["current_use"]:
            failures.append(
                f"Prime source catalog anchor current_use drifted: {anchor['id']}."
            )


def _verify_family_support(
    handoff: dict[str, Any],
    expected: dict[str, Any],
    failures: list[str],
) -> None:
    family_support = handoff.get("family_support")
    if not isinstance(family_support, dict):
        failures.append("Prime handoff family_support must be an object.")
        return
    if family_support != expected:
        failures.append("Prime handoff family_support summary drifted.")
    if family_support.get("review_required_before_claims") is not True:
        failures.append(
            "Prime handoff family_support.review_required_before_claims must be true."
        )


def _verify_source_catalog_scope(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    scope = handoff.get("source_catalog_scope")
    if not isinstance(scope, dict):
        failures.append("Prime handoff source_catalog_scope must be an object.")
        return
    if scope.get("non_lattice_toy_operator_security_claims") != 0:
        failures.append(
            "Prime handoff source catalog scope must not contain "
            "non-lattice toy security claims."
        )
    if scope.get("non_lattice_toy_evaluator_count") != scope.get("source_count"):
        failures.append("Prime handoff source catalog scope must cover every source.")
    if scope.get("non_lattice_toy_operator_variant_count") != scope.get(
        "source_count"
    ):
        failures.append(
            "Prime handoff source catalog operator scope must cover every source."
        )


def _verify_quickstart_alignment(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    alignment = handoff.get("prime_quickstart_alignment")
    if alignment != PRIME_QUICKSTART_ALIGNMENT:
        failures.append("Prime handoff quickstart alignment drifted.")
        return
    if alignment["external_prime_execution_performed"] is not False:
        failures.append("Prime handoff must not claim Prime execution.")
    if alignment["credentials_checked_at_generation"] is not False:
        failures.append("Prime handoff must not inspect credentials at generation.")
    if alignment["requires_credentials"] is not True:
        failures.append("Prime handoff quickstart alignment lacks credential boundary.")
    source_catalog = build_source_catalog()
    source_by_id = {source["id"]: source for source in source_catalog["sources"]}
    source = source_by_id.get(alignment["source_anchor_id"])
    if source is None:
        failures.append("Prime quickstart source catalog anchor is missing.")
    elif source.get("url") != alignment["source_url"]:
        failures.append("Prime quickstart source URL drifted.")


def _verify_safety(handoff: dict[str, Any], failures: list[str]) -> None:
    safety = handoff.get("safety")
    if not isinstance(safety, dict):
        failures.append("Prime publication handoff safety must be an object.")
        return
    for flag in EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            if flag == "security_claim":
                failures.append("Prime handoff advertises a security claim.")
            elif flag == "publishes_private_candidates":
                failures.append("Prime handoff may publish private candidates.")
            elif flag == "claims_external_publication":
                failures.append("Prime handoff claims external publication.")
            elif flag == "arbitrary_code_execution":
                failures.append("Prime handoff advertises arbitrary execution.")
            else:
                failures.append(f"Prime handoff safety.{flag} must be false.")


def _verify_review_requirements(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    if handoff.get("review_required_before_publish") != REVIEW_REQUIRED_BEFORE_PUBLISH:
        failures.append("Prime handoff review checklist drifted.")


def _verify_release_gates(
    handoff: dict[str, Any],
    failures: list[str],
) -> None:
    release_gates = handoff.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append("Prime handoff release_gates must be a list.")
        return
    for required_gate in REQUIRED_RELEASE_GATES:
        if required_gate not in release_gates:
            failures.append(f"Prime handoff release gate missing: {required_gate}")


def _verification_result(
    handoff_path: Path,
    handoff: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    readiness = handoff.get("readiness", {})
    if not isinstance(readiness, dict):
        readiness = {}
    local_package = handoff.get("local_package", {})
    if not isinstance(local_package, dict):
        local_package = {}
    source_catalog_scope = handoff.get("source_catalog_scope", {})
    if not isinstance(source_catalog_scope, dict):
        source_catalog_scope = {}
    family_support = handoff.get("family_support", {})
    if not isinstance(family_support, dict):
        family_support = {}
    artifact_paths = local_package.get("artifact_paths", [])
    if not isinstance(artifact_paths, list):
        artifact_paths = []
    return {
        "schema_version": PRIME_PUBLICATION_HANDOFF_VERIFICATION_SCHEMA,
        "handoff_path": handoff_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "artifact_count": len(artifact_paths),
            "external_publication_requires_review": readiness.get(
                "external_publication_requires_review"
            ),
            "failure_count": len(failures),
            "family_count": readiness.get("family_count"),
            "family_support_review_required_before_claims": family_support.get(
                "review_required_before_claims"
            ),
            "implemented_families": family_support.get("implemented"),
            "local_package_ready": readiness.get("local_package_ready"),
            "non_lattice_toy_evaluator_count": source_catalog_scope.get(
                "non_lattice_toy_evaluator_count"
            ),
            "non_lattice_toy_operator_security_claims": (
                source_catalog_scope.get("non_lattice_toy_operator_security_claims")
            ),
            "non_lattice_toy_operator_variant_count": source_catalog_scope.get(
                "non_lattice_toy_operator_variant_count"
            ),
            "prime_hub_publication_performed": readiness.get(
                "prime_hub_publication_performed"
            ),
            "requires_credentials": readiness.get("requires_credentials"),
            "task_count": readiness.get("task_count"),
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
