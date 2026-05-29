from __future__ import annotations

import json
import shutil
import tomllib
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.formal.artifacts import REVIEWER_GOVERNANCE_BINDING_SCHEMA
from agades_pqc_gym.integrations.family_support import (
    summarize_family_support_matrix,
)
from agades_pqc_gym.integrations.prime_eval_config import (
    DEFAULT_CONFIG_PATH as PRIME_EVAL_CONFIG_PATH,
)
from agades_pqc_gym.integrations.prime_eval_config import (
    DEFAULT_MANIFEST_PATH as PRIME_EVAL_MANIFEST_PATH,
)
from agades_pqc_gym.integrations.public_private_boundary import (
    build_public_private_boundary,
    redaction_summary_fields,
    verify_public_private_boundary,
)
from agades_pqc_gym.integrations.source_catalog import (
    build_source_catalog,
    summarize_source_catalog_scope,
)
from agades_pqc_gym.integrations.task_metadata import (
    TASK_METADATA_SCHEMA,
    summarize_task_metadata_rows,
    task_metadata_for_plan,
)
from agades_pqc_gym.rl.environment import FORMAL_ARTIFACT_BINDING_SCHEMA

PRIME_ENVIRONMENT_MANIFEST_SCHEMA = "agades.pqc.prime_environment_manifest.v1"
PRIME_ENVIRONMENT_MANIFEST_VERIFICATION_SCHEMA = (
    "agades.pqc.prime_environment_manifest_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
ENVIRONMENT_DIR = Path("prime_intellect/verifiers_environment")
ENVIRONMENT_MODULE = "agades_pqc_verifier_env:load_environment"
_EXPECTED_FALSE_SAFETY_FLAGS = (
    "contains_private_traces",
    "arbitrary_code_execution",
    "live_targeting",
    "security_claim",
    "publishes_private_candidates",
)
_REQUIRED_RELEASE_GATES = (
    "uv run pytest tests/test_prime_environment_manifest.py -q",
    "uv run agades-pqc prime-manifest --out "
    "prime_intellect/verifiers_environment/prime_manifest.json",
    "uv run agades-pqc prime-manifest-verify --manifest "
    "prime_intellect/verifiers_environment/prime_manifest.json",
    "uv run agades-pqc prime-environment-smoke --out "
    "reports/prime_environment_smoke.json",
    "uv run agades-pqc prime-environment-smoke-verify --report "
    "reports/prime_environment_smoke.json",
    "uv run agades-pqc prime-eval-config --config "
    "prime_intellect/evals/agades_pqc_eval.template.toml --manifest "
    "docs/prime_eval_config_manifest.json",
    "uv run agades-pqc prime-eval-config-verify --config "
    "prime_intellect/evals/agades_pqc_eval.template.toml --manifest "
    "docs/prime_eval_config_manifest.json",
    "uv run agades-pqc prime-schemas --out prime_intellect/schemas",
    "uv build prime_intellect/verifiers_environment",
    "uv run agades-pqc ecosystem-smoke-verify --report "
    "reports/ecosystem_smoke.json",
    "uv run agades-pqc release-audit --out public/release_audit.json",
)


def build_prime_environment_manifest(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    environment_dir = project_root / ENVIRONMENT_DIR
    pyproject = tomllib.loads(
        (environment_dir / "pyproject.toml").read_text(encoding="utf-8")
    )
    project = pyproject["project"]
    evaluation_defaults = pyproject.get("tool", {}).get("verifiers", {}).get("eval", {})
    task_rows = _packaged_task_rows(environment_dir)
    families = sorted({row["target_family"] for row in task_rows})
    source_mirror = _source_mirror_contract(project_root, environment_dir)
    family_support_matrix = json.loads(
        (project_root / "docs" / "family_support_matrix.json").read_text(
            encoding="utf-8"
        )
    )

    return {
        "schema_version": PRIME_ENVIRONMENT_MANIFEST_SCHEMA,
        "project": {
            "name": "Agades PQC Verifier Environment",
            "environment_package": project["name"],
            "source_package": "agades-pqc-gym",
            "entrypoint": ENVIRONMENT_MODULE,
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
        },
        "prime": {
            "environment_dir": ENVIRONMENT_DIR.as_posix(),
            "eval_config_path": PRIME_EVAL_CONFIG_PATH.as_posix(),
            "eval_manifest_path": PRIME_EVAL_MANIFEST_PATH.as_posix(),
            "eval_config_verify_command": (
                "uv run agades-pqc prime-eval-config-verify --config "
                f"{PRIME_EVAL_CONFIG_PATH.as_posix()} --manifest "
                f"{PRIME_EVAL_MANIFEST_PATH.as_posix()}"
            ),
            "local_editable_install_command": (
                f"cd {ENVIRONMENT_DIR.as_posix()} && uv pip install -e ."
            ),
            "local_eval_command": (
                f"cd {ENVIRONMENT_DIR.as_posix()} && uv run vf-eval "
                f"{project['name']}"
            ),
            "hub_private_push_command": (
                f"prime env push --path {ENVIRONMENT_DIR.as_posix()} "
                "--visibility PRIVATE"
            ),
            "hub_install_command_template": (
                f"prime env install <owner>/{project['name']}"
            ),
            "public_push_requires_review": True,
        },
        "evaluation_defaults": {
            "num_examples": evaluation_defaults.get("num_examples"),
            "rollouts_per_example": evaluation_defaults.get("rollouts_per_example"),
        },
        "task_manifest": {
            "task_metadata_schema": TASK_METADATA_SCHEMA,
            "task_count": len(task_rows),
            "task_summary": summarize_task_metadata_rows(task_rows),
            "families": families,
            "source_paths": [row["source_path"] for row in task_rows],
            "attack_plan_ids": [row["attack_plan_id"] for row in task_rows],
            "support_levels": sorted({row["support_level"] for row in task_rows}),
        },
        "family_support": summarize_family_support_matrix(family_support_matrix),
        "source_catalog_scope": summarize_source_catalog_scope(build_source_catalog()),
        "public_private_boundary": build_public_private_boundary(project_root),
        "source_mirror": source_mirror,
        "scoring_contract": {
            "reward_range": [0.0, 1.0],
            "accepted_reward": 1.0,
            "unsupported_reward": 0.0,
            "invalid_reward": 0.0,
            "requires_single_json_object": True,
            "accepts_executable_code": False,
            "formal_artifact_binding_schema": FORMAL_ARTIFACT_BINDING_SCHEMA,
            "review_governance_binding_schema": REVIEWER_GOVERNANCE_BINDING_SCHEMA,
            "reviewer_quality_requires_governance": True,
            "acceptance_rule": (
                "schema_valid == true and accepted == true from "
                "agades_pqc_gym.verifier.verify_attack_plan_json"
            ),
            "formal_binding_rule": (
                "accepted Prime rewards must attach an "
                "agades.pqc.rl.formal_artifact_binding.v1 proof binding with "
                "review_governance_ok == true"
            ),
            "task_match_rule": (
                "accepted candidates must match the current task info for "
                "target_family, target_name, support_level, and ordered "
                "operator_types; attack_plan_id may change"
            ),
            "prompt_profiles": {
                "attackplan_json": {
                    "intended_use": "private_training_or_eval",
                    "contract": (
                        "submit one AttackPlan JSON object for the seed task; "
                        "do not invent pre-evaluation claims"
                    ),
                },
                "format_first_copy_seed": {
                    "intended_use": "format_smoke_and_supported_strict_eval",
                    "contract": "copy the seed AttackPlan unchanged as one JSON object",
                },
                "format_repair_extract_seed": {
                    "intended_use": "private_format_curriculum",
                    "contract": (
                        "extract the public seed AttackPlan from wrapped prose "
                        "and markdown"
                    ),
                },
                "claims_guard_repair": {
                    "intended_use": "private_claims_repair_curriculum",
                    "contract": (
                        "repair invalid pre-evaluation claim estimates by "
                        "restoring unknown null claims without adding external "
                        "claim evidence"
                    ),
                },
                "claims_guard_format_repair": {
                    "intended_use": "private_format_and_claims_repair_curriculum",
                    "contract": (
                        "extract a fenced public toy AttackPlan, repair invalid "
                        "pre-evaluation claim estimates back to unknown nulls, "
                        "and return one JSON object without wrapper text"
                    ),
                },
                "claims_guard_decoy_format_repair": {
                    "intended_use": "private_format_and_claims_repair_curriculum",
                    "contract": (
                        "ignore an AttackPlan-like decoy from a different task, "
                        "extract the fenced public toy AttackPlan, repair invalid "
                        "pre-evaluation claim estimates back to unknown nulls, "
                        "and return one JSON object without wrapper text"
                    ),
                },
            },
            "reward_profiles": {
                "strict": {
                    "intended_use": "public_eval",
                    "aggregate_rule": "accepted_attack_plan only",
                    "rubric_weights": {
                        "accepted_attack_plan": 1.0,
                        "single_json_object": 0.0,
                        "formal_validity": 0.0,
                        "cryptographic_applicability": 0.0,
                        "no_security_overclaim": 0.0,
                        "student_readability": 0.0,
                        "reproducibility": 0.0,
                        "reviewer_quality": 0.0,
                        "task_match": 0.0,
                        "proof_obligation_coverage": 0.0,
                    },
                },
                "pedagogical_dense": {
                    "intended_use": "private_prime_rl_training",
                    "aggregate_rule": (
                        "weighted training signal over JSON-format compliance "
                        "and existing verifier sub-scores"
                    ),
                    "accepted_candidates_still_require_strict_acceptance": True,
                    "rubric_weights": {
                        "accepted_attack_plan": 0.30,
                        "single_json_object": 0.10,
                        "formal_validity": 0.15,
                        "cryptographic_applicability": 0.10,
                        "no_security_overclaim": 0.10,
                        "student_readability": 0.07,
                        "reproducibility": 0.05,
                        "reviewer_quality": 0.05,
                        "task_match": 0.04,
                        "proof_obligation_coverage": 0.04,
                    },
                },
                "format_repair_dense": {
                    "intended_use": "private_prime_rl_training",
                    "aggregate_rule": (
                        "weighted format-repair signal; exact valid JSON can "
                        "receive full reward, wrapped JSON can receive partial "
                        "non-accepted reward"
                    ),
                    "accepted_candidates_still_require_strict_acceptance": True,
                    "rubric_weights": {
                        "accepted_attack_plan": 0.20,
                        "single_json_object": 0.20,
                        "formal_validity": 0.20,
                        "cryptographic_applicability": 0.05,
                        "no_security_overclaim": 0.15,
                        "student_readability": 0.08,
                        "reproducibility": 0.03,
                        "reviewer_quality": 0.03,
                        "task_match": 0.04,
                        "proof_obligation_coverage": 0.02,
                    },
                },
            },
            "task_info_fields": [
                "schema_version",
                "source_path",
                "attack_plan_id",
                "target_family",
                "target_name",
                "support_level",
                "operator_types",
                "requires_reproducibility",
                "public",
                "seed_accepted",
                "seed_evaluation_status",
                "seed_estimator_name",
                "seed_reproduction_attempted",
                "seed_reproduction_status",
                "seed_reproduction_success",
                "seed_reward",
            ],
        },
        "schemas": {
            "schema_dir": "prime_intellect/schemas",
            "schema_manifest": "prime_intellect/schemas/schema_manifest.json",
            "submission_schema": "prime_intellect/schemas/attack_plan.schema.json",
            "task_metadata_schema": "prime_intellect/schemas/task_metadata.schema.json",
            "result_schema": "prime_intellect/schemas/verifier_result.schema.json",
            "generator_command": (
                "uv run agades-pqc prime-schemas --out prime_intellect/schemas"
            ),
        },
        "safety": {
            "contains_private_traces": False,
            "arbitrary_code_execution": False,
            "live_targeting": False,
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "release": {
            "publication_status": "local_package_ready",
            "requires_credentials": True,
            "review_required_before_publish": True,
            "package_build_command": "uv build prime_intellect/verifiers_environment",
            "smoke_gate": "prime-environment-smoke",
            "audit_gate": "prime-environment-manifest",
        },
        "release_gates": list(_REQUIRED_RELEASE_GATES),
    }


def write_prime_environment_manifest(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    _sync_packaged_environment_assets(
        project_root,
        project_root / ENVIRONMENT_DIR,
    )
    manifest = build_prime_environment_manifest(root=project_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_prime_environment_manifest(
    manifest_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    manifest = _read_prime_environment_manifest(manifest_path, project_root, failures)
    expected = build_prime_environment_manifest(root=project_root)

    if manifest != expected:
        failures.append("Prime environment manifest is not in sync.")

    _verify_project_metadata(manifest, failures)
    _verify_prime_commands(manifest, expected, failures)
    _verify_scoring_contract(manifest, failures)
    _verify_schema_references(project_root, manifest, failures)
    _verify_safety(manifest, failures)
    _verify_release_contract(manifest, failures)
    _verify_source_mirror(project_root, manifest, failures)
    _verify_task_manifest(project_root, manifest, failures)
    _verify_family_support(manifest, failures)
    _verify_source_catalog_scope(manifest, failures)
    _verify_public_private_boundary(manifest, failures)
    _verify_release_gates(manifest, failures)

    return _verification_result(manifest_path, manifest, failures)


def _read_prime_environment_manifest(
    manifest_path: Path,
    root: Path,
    failures: list[str],
) -> dict[str, Any]:
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Prime environment manifest is missing: {manifest_path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(
            f"Prime environment manifest is invalid JSON at line {exc.lineno}."
        )
        return {}

    if not isinstance(payload, dict):
        failures.append("Prime environment manifest must be a JSON object.")
        return {}
    return payload


def _verify_project_metadata(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    if manifest.get("schema_version") != PRIME_ENVIRONMENT_MANIFEST_SCHEMA:
        failures.append(
            "Prime environment manifest schema_version must be "
            f"{PRIME_ENVIRONMENT_MANIFEST_SCHEMA}."
        )
    project = manifest.get("project")
    if not isinstance(project, dict):
        failures.append("Prime environment manifest project must be an object.")
        return
    expected_project = {
        "name": "Agades PQC Verifier Environment",
        "environment_package": "agades-pqc-verifier-env",
        "source_package": "agades-pqc-gym",
        "entrypoint": ENVIRONMENT_MODULE,
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    for key, expected in expected_project.items():
        if project.get(key) != expected:
            failures.append(f"Prime environment manifest project.{key} is incorrect.")


def _verify_prime_commands(
    manifest: dict[str, Any],
    expected: dict[str, Any],
    failures: list[str],
) -> None:
    prime = manifest.get("prime")
    if not isinstance(prime, dict):
        failures.append("Prime environment manifest prime must be an object.")
        return
    expected_prime = expected.get("prime", {})
    for field in (
        "environment_dir",
        "eval_config_path",
        "eval_manifest_path",
        "eval_config_verify_command",
        "local_editable_install_command",
        "local_eval_command",
        "hub_private_push_command",
        "hub_install_command_template",
    ):
        if prime.get(field) != expected_prime.get(field):
            failures.append(f"Prime manifest has incorrect {field}.")
    if prime.get("public_push_requires_review") is not True:
        failures.append("Prime manifest lacks public push review boundary.")


def _verify_scoring_contract(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    scoring_contract = manifest.get("scoring_contract")
    if not isinstance(scoring_contract, dict):
        failures.append(
            "Prime environment manifest scoring_contract must be an object."
        )
        return
    expected_rewards = {
        "reward_range": [0.0, 1.0],
        "accepted_reward": 1.0,
        "unsupported_reward": 0.0,
        "invalid_reward": 0.0,
    }
    for field, expected in expected_rewards.items():
        if scoring_contract.get(field) != expected:
            failures.append(f"Prime manifest scoring_contract.{field} is incorrect.")
    if scoring_contract.get("accepts_executable_code") is not False:
        failures.append("Prime manifest allows executable model submissions.")
    if scoring_contract.get("requires_single_json_object") is not True:
        failures.append("Prime manifest does not require a single JSON object.")
    if (
        scoring_contract.get("formal_artifact_binding_schema")
        != FORMAL_ARTIFACT_BINDING_SCHEMA
    ):
        failures.append("Prime manifest formal artifact binding schema drifted.")
    if (
        scoring_contract.get("review_governance_binding_schema")
        != REVIEWER_GOVERNANCE_BINDING_SCHEMA
    ):
        failures.append("Prime manifest reviewer governance schema drifted.")
    if scoring_contract.get("reviewer_quality_requires_governance") is not True:
        failures.append("Prime manifest reviewer quality is not governance-bound.")
    reward_profiles = scoring_contract.get("reward_profiles")
    if not isinstance(reward_profiles, dict):
        failures.append("Prime manifest reward_profiles must be an object.")
    else:
        strict_profile = reward_profiles.get("strict")
        dense_profile = reward_profiles.get("pedagogical_dense")
        format_repair_profile = reward_profiles.get("format_repair_dense")
        if not isinstance(strict_profile, dict):
            failures.append("Prime manifest lacks strict reward profile.")
        elif strict_profile.get("rubric_weights", {}).get(
            "accepted_attack_plan"
        ) != 1.0:
            failures.append("Prime strict profile must weight accepted plans only.")
        if not isinstance(dense_profile, dict):
            failures.append("Prime manifest lacks pedagogical_dense reward profile.")
        elif dense_profile.get(
            "accepted_candidates_still_require_strict_acceptance"
        ) is not True:
            failures.append("Prime dense profile weakens accepted-candidate rule.")
        if not isinstance(format_repair_profile, dict):
            failures.append("Prime manifest lacks format_repair_dense reward profile.")
        elif format_repair_profile.get(
            "accepted_candidates_still_require_strict_acceptance"
        ) is not True:
            failures.append(
                "Prime format-repair profile weakens accepted-candidate rule."
            )
        for name, profile in reward_profiles.items():
            if not isinstance(profile, dict):
                continue
            weights = profile.get("rubric_weights")
            if not isinstance(weights, dict):
                failures.append(f"Prime reward profile {name} lacks weights.")
                continue
            if abs(sum(float(value) for value in weights.values()) - 1.0) > 1e-12:
                failures.append(f"Prime reward profile {name} weights do not sum to 1.")
    prompt_profiles = scoring_contract.get("prompt_profiles")
    if not isinstance(prompt_profiles, dict):
        failures.append("Prime manifest prompt_profiles must be an object.")
    else:
        expected_prompt_profiles = {
            "attackplan_json",
            "format_first_copy_seed",
            "format_repair_extract_seed",
            "claims_guard_repair",
            "claims_guard_format_repair",
            "claims_guard_decoy_format_repair",
        }
        if set(prompt_profiles) != expected_prompt_profiles:
            failures.append("Prime manifest prompt_profiles drifted.")
    if scoring_contract.get("formal_binding_rule") != (
        "accepted Prime rewards must attach an "
        "agades.pqc.rl.formal_artifact_binding.v1 proof binding with "
        "review_governance_ok == true"
    ):
        failures.append("Prime manifest formal binding rule drifted.")
    task_info_fields = scoring_contract.get("task_info_fields")
    if not isinstance(task_info_fields, list) or not task_info_fields:
        failures.append("Prime manifest task_info_fields must be a non-empty list.")


def _verify_schema_references(
    root: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    schemas = manifest.get("schemas")
    if not isinstance(schemas, dict):
        failures.append("Prime environment manifest schemas must be an object.")
        return
    expected_paths = {
        "schema_manifest": "prime_intellect/schemas/schema_manifest.json",
        "submission_schema": "prime_intellect/schemas/attack_plan.schema.json",
        "task_metadata_schema": "prime_intellect/schemas/task_metadata.schema.json",
        "result_schema": "prime_intellect/schemas/verifier_result.schema.json",
    }
    if schemas.get("schema_dir") != "prime_intellect/schemas":
        failures.append("Prime manifest has incorrect schema_dir.")
    if schemas.get("generator_command") != (
        "uv run agades-pqc prime-schemas --out prime_intellect/schemas"
    ):
        failures.append("Prime manifest has incorrect schema generator command.")
    for field, expected_path in expected_paths.items():
        if schemas.get(field) != expected_path:
            failures.append(f"Prime manifest does not reference {field}.")
            continue
        if not (root / expected_path).is_file():
            failures.append(f"Prime manifest schema file is missing: {expected_path}.")


def _verify_safety(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        failures.append("Prime environment manifest safety must be an object.")
        return
    for flag in _EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            if flag == "arbitrary_code_execution":
                failures.append("Prime manifest advertises arbitrary execution.")
            elif flag == "security_claim":
                failures.append("Prime manifest advertises a security claim.")
            elif flag == "publishes_private_candidates":
                failures.append("Prime manifest may publish private candidates.")
            else:
                failures.append(f"Prime manifest safety.{flag} must be false.")


def _verify_release_contract(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    release = manifest.get("release")
    if not isinstance(release, dict):
        failures.append("Prime environment manifest release must be an object.")
        return
    if release.get("publication_status") != "local_package_ready":
        failures.append("Prime manifest has incorrect publication status.")
    if release.get("requires_credentials") is not True:
        failures.append("Prime manifest lacks credential boundary.")
    if release.get("review_required_before_publish") is not True:
        failures.append("Prime manifest lacks publication review boundary.")
    if release.get("package_build_command") != (
        "uv build prime_intellect/verifiers_environment"
    ):
        failures.append("Prime manifest has incorrect package build command.")
    if release.get("smoke_gate") != "prime-environment-smoke":
        failures.append("Prime manifest does not point to the Prime smoke gate.")
    if release.get("audit_gate") != "prime-environment-manifest":
        failures.append("Prime manifest does not point to the Prime audit gate.")


def _verify_source_mirror(
    root: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    task_manifest = manifest.get("task_manifest")
    if not isinstance(task_manifest, dict):
        task_manifest = {}
    source_mirror = manifest.get("source_mirror")
    if not isinstance(source_mirror, dict):
        failures.append("Prime manifest source_mirror must be an object.")
        return
    if source_mirror.get("source_dir") != "examples/attack_plans":
        failures.append("Prime manifest source mirror has incorrect source_dir.")
    if source_mirror.get("data_dir") != "prime_intellect/verifiers_environment/data":
        failures.append("Prime manifest source mirror has incorrect data_dir.")
    if source_mirror.get("mirrors_valid_public_examples") is not True:
        failures.append("Prime manifest data files do not mirror public examples.")
    task_count = task_manifest.get("task_count")
    if source_mirror.get("valid_public_example_count") != task_count:
        failures.append("Prime manifest source mirror count does not match task_count.")
    if source_mirror.get("packaged_data_file_count") != task_count:
        failures.append("Prime manifest packaged data count does not match task_count.")

    source_example_paths = _string_list(
        source_mirror.get("source_example_paths"),
        "Prime manifest source_example_paths",
        failures,
    )
    packaged_data_paths = _string_list(
        source_mirror.get("packaged_data_paths"),
        "Prime manifest packaged_data_paths",
        failures,
    )
    packaged_by_name = {Path(path).name: path for path in packaged_data_paths}
    for source_example_path in source_example_paths:
        source = root / source_example_path
        if not source.is_file():
            failures.append(
                f"Prime manifest source example is missing: {source_example_path}"
            )
            continue
        packaged_data_path = packaged_by_name.get(source.name)
        if packaged_data_path is None:
            failures.append(
                "Prime manifest packaged data mirror is missing for "
                f"{source_example_path}"
            )
            continue
        packaged = root / packaged_data_path
        if not packaged.is_file():
            failures.append(
                f"Prime manifest packaged data file is missing: {packaged_data_path}"
            )
            continue
        if packaged.read_bytes() != source.read_bytes():
            failures.append(
                "Prime manifest packaged data differs from source example: "
                f"{source_example_path}"
            )


def _verify_task_manifest(
    root: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    task_manifest = manifest.get("task_manifest")
    if not isinstance(task_manifest, dict):
        failures.append("Prime environment manifest task_manifest must be an object.")
        return
    source_paths = _string_list(
        task_manifest.get("source_paths"),
        "Prime manifest source_paths",
        failures,
    )
    attack_plan_ids = _string_list(
        task_manifest.get("attack_plan_ids"),
        "Prime manifest attack_plan_ids",
        failures,
    )
    families = _string_list(
        task_manifest.get("families"),
        "Prime manifest families",
        failures,
    )
    if task_manifest.get("task_metadata_schema") != TASK_METADATA_SCHEMA:
        failures.append("Prime manifest task metadata schema is incorrect.")
    if task_manifest.get("task_count") != len(source_paths):
        failures.append("Prime manifest task_count does not match source_paths.")
    if len(attack_plan_ids) != len(source_paths):
        failures.append("Prime manifest attack_plan_ids count does not match tasks.")
    if not families:
        failures.append("Prime manifest families must be non-empty.")
    environment_dir = root / ENVIRONMENT_DIR
    try:
        expected_task_summary = summarize_task_metadata_rows(
            _packaged_task_rows(environment_dir)
        )
    except ValueError:
        failures.append("Prime packaged task metadata contains invalid rows.")
    else:
        if task_manifest.get("task_summary") != expected_task_summary:
            failures.append("Prime manifest task_summary is not in sync.")
    for source_path in source_paths:
        candidate = environment_dir / source_path
        if not candidate.is_file():
            failures.append(f"Prime manifest task path is missing: {source_path}")


def _verify_family_support(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    family_support = manifest.get("family_support")
    if not isinstance(family_support, dict):
        failures.append("Prime manifest family_support must be an object.")
        return
    if family_support.get("review_required_before_claims") is not True:
        failures.append(
            "Prime manifest family support must require review before claims."
        )


def _verify_source_catalog_scope(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    scope = manifest.get("source_catalog_scope")
    if not isinstance(scope, dict):
        failures.append("Prime manifest source_catalog_scope must be an object.")
        return
    if scope.get("non_lattice_toy_operator_security_claims") != 0:
        failures.append(
            "Prime manifest source catalog scope must not contain "
            "non-lattice toy security claims."
        )
    if scope.get("non_lattice_toy_evaluator_count") != scope.get("source_count"):
        failures.append("Prime manifest source catalog scope must cover every source.")
    if scope.get("non_lattice_toy_operator_variant_count") != scope.get(
        "source_count"
    ):
        failures.append(
            "Prime manifest source catalog operator scope must cover every source."
        )


def _verify_public_private_boundary(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    public_private_boundary = manifest.get("public_private_boundary")
    if not isinstance(public_private_boundary, dict):
        failures.append("Prime manifest public_private_boundary must be an object.")
        return
    verify_public_private_boundary(
        public_private_boundary,
        failures,
        label="Prime manifest",
    )


def _verify_release_gates(
    manifest: dict[str, Any],
    failures: list[str],
) -> None:
    release_gates = manifest.get("release_gates")
    if not isinstance(release_gates, list):
        failures.append("Prime manifest release_gates must be a list.")
        return
    for required_gate in _REQUIRED_RELEASE_GATES:
        if required_gate not in release_gates:
            failures.append(f"Prime manifest release gate missing: {required_gate}")


def _string_list(
    value: object,
    label: str,
    failures: list[str],
) -> list[str]:
    if not isinstance(value, list):
        failures.append(f"{label} must be a list.")
        return []
    strings: list[str] = []
    for item in value:
        if not isinstance(item, str):
            failures.append(f"{label} contains a non-string value.")
            continue
        strings.append(item)
    return strings


def _list_count(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _verification_result(
    manifest_path: Path,
    manifest: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    prime = manifest.get("prime", {})
    if not isinstance(prime, dict):
        prime = {}
    task_manifest = manifest.get("task_manifest", {})
    if not isinstance(task_manifest, dict):
        task_manifest = {}
    source_mirror = manifest.get("source_mirror", {})
    if not isinstance(source_mirror, dict):
        source_mirror = {}
    scoring_contract = manifest.get("scoring_contract", {})
    if not isinstance(scoring_contract, dict):
        scoring_contract = {}
    family_support = manifest.get("family_support", {})
    if not isinstance(family_support, dict):
        family_support = {}
    source_catalog_scope = manifest.get("source_catalog_scope", {})
    if not isinstance(source_catalog_scope, dict):
        source_catalog_scope = {}
    public_private_boundary = manifest.get("public_private_boundary", {})
    if not isinstance(public_private_boundary, dict):
        public_private_boundary = {}
    families = task_manifest.get("families", [])
    if not isinstance(families, list):
        families = []
    redaction_summary = redaction_summary_fields(public_private_boundary)
    return {
        "schema_version": PRIME_ENVIRONMENT_MANIFEST_VERIFICATION_SCHEMA,
        "manifest_path": manifest_path.as_posix(),
        "accepted": not failures,
        "summary": {
            "families": families,
            "families_with_future_reviewed_adapters": _list_count(
                family_support.get("families_with_future_reviewed_adapters")
            ),
            "family_count": family_support.get("family_count"),
            "failure_count": len(failures),
            "mirrored_public_examples": source_mirror.get(
                "valid_public_example_count"
            ),
            "mirrors_public_examples": source_mirror.get(
                "mirrors_valid_public_examples"
            ),
            "non_lattice_toy_evaluator_count": source_catalog_scope.get(
                "non_lattice_toy_evaluator_count"
            ),
            "non_lattice_toy_operator_security_claims": (
                source_catalog_scope.get("non_lattice_toy_operator_security_claims")
            ),
            "non_lattice_toy_operator_variant_count": source_catalog_scope.get(
                "non_lattice_toy_operator_variant_count"
            ),
            "packaged_data_file_count": source_mirror.get(
                "packaged_data_file_count"
            ),
            "public_push_requires_review": prime.get("public_push_requires_review"),
            **redaction_summary,
            "review_required_before_claims": family_support.get(
                "review_required_before_claims"
            ),
            "requires_single_json_object": scoring_contract.get(
                "requires_single_json_object"
            ),
            "formal_artifact_binding_schema": scoring_contract.get(
                "formal_artifact_binding_schema"
            ),
            "review_governance_binding_schema": scoring_contract.get(
                "review_governance_binding_schema"
            ),
            "reviewer_quality_requires_governance": scoring_contract.get(
                "reviewer_quality_requires_governance"
            ),
            "task_count": task_manifest.get("task_count"),
        },
        "failures": failures,
    }


def _packaged_task_rows(environment_dir: Path) -> list[dict[str, Any]]:
    data_dir = environment_dir / "data"
    rows: list[dict[str, Any]] = []
    for path in sorted(data_dir.glob("*.json")):
        raw_json = path.read_text(encoding="utf-8")
        plan = AttackPlan.model_validate_json(raw_json)
        rows.append(
            task_metadata_for_plan(
                plan,
                source_path=path.relative_to(environment_dir).as_posix(),
                seed_attack_plan_json=raw_json,
            )
        )
    return rows


def _sync_packaged_environment_assets(
    project_root: Path,
    environment_dir: Path,
) -> None:
    _sync_packaged_task_data(project_root, environment_dir)
    _sync_directory(
        source_dir=project_root / "docs",
        target_dir=environment_dir / "docs",
        suffix=".json",
    )
    _sync_directory(
        source_dir=project_root / "formal" / "lean",
        target_dir=environment_dir / "formal" / "lean",
        ignored_parts=frozenset({".lake"}),
    )


def _sync_packaged_task_data(project_root: Path, environment_dir: Path) -> None:
    data_dir = environment_dir / "data"
    source_paths = _valid_public_attack_plan_paths(project_root)
    source_names = {path.name for path in source_paths}
    data_dir.mkdir(parents=True, exist_ok=True)

    for stale_path in sorted(data_dir.glob("*.json")):
        if stale_path.name not in source_names:
            stale_path.unlink()

    for source_path in source_paths:
        packaged_path = data_dir / source_path.name
        if (
            not packaged_path.is_file()
            or packaged_path.read_bytes() != source_path.read_bytes()
        ):
            shutil.copyfile(source_path, packaged_path)


def _sync_directory(
    *,
    source_dir: Path,
    target_dir: Path,
    suffix: str | None = None,
    ignored_parts: frozenset[str] = frozenset(),
) -> None:
    source_files = {
        path.relative_to(source_dir): path
        for path in sorted(source_dir.rglob("*"))
        if path.is_file()
        and not ignored_parts.intersection(path.relative_to(source_dir).parts)
        and (suffix is None or path.suffix == suffix)
    }
    target_files = {
        path.relative_to(target_dir): path
        for path in sorted(target_dir.rglob("*"))
        if path.is_file()
        and not ignored_parts.intersection(path.relative_to(target_dir).parts)
        and (suffix is None or path.suffix == suffix)
    }
    target_dir.mkdir(parents=True, exist_ok=True)

    for relative_path, target_path in target_files.items():
        if relative_path not in source_files:
            target_path.unlink()

    for relative_path, source_path in source_files.items():
        target_path = target_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if (
            not target_path.is_file()
            or target_path.read_bytes() != source_path.read_bytes()
        ):
            shutil.copyfile(source_path, target_path)


def _source_mirror_contract(
    project_root: Path,
    environment_dir: Path,
) -> dict[str, Any]:
    source_paths = _valid_public_attack_plan_paths(project_root)
    packaged_paths = sorted((environment_dir / "data").glob("*.json"))
    source_names = [path.name for path in source_paths]
    packaged_names = [path.name for path in packaged_paths]
    content_matches = all(
        (environment_dir / "data" / source_path.name).is_file()
        and (environment_dir / "data" / source_path.name).read_bytes()
        == source_path.read_bytes()
        for source_path in source_paths
    )

    return {
        "source_dir": "examples/attack_plans",
        "data_dir": (ENVIRONMENT_DIR / "data").as_posix(),
        "valid_public_example_count": len(source_paths),
        "packaged_data_file_count": len(packaged_paths),
        "mirrors_valid_public_examples": packaged_names == source_names
        and content_matches,
        "source_example_paths": [
            path.relative_to(project_root).as_posix() for path in source_paths
        ],
        "packaged_data_paths": [
            path.relative_to(project_root).as_posix() for path in packaged_paths
        ],
    }


def _valid_public_attack_plan_paths(project_root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in sorted((project_root / "examples" / "attack_plans").glob("*.json")):
        try:
            plan = AttackPlan.model_validate_json(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if plan.metadata.public:
            paths.append(path)
    return paths
