from __future__ import annotations

import json
from pathlib import Path

from expected_task_metadata_summary import EXPECTED_TASK_METADATA_SUMMARY
from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.integrations.prime_environment_manifest import (
    build_prime_environment_manifest,
    verify_prime_environment_manifest,
    write_prime_environment_manifest,
)
from agades_pqc_gym.integrations.task_metadata import TASK_METADATA_SCHEMA

EXPECTED_FAMILY_SUPPORT = {
    "benchmark_count": 78,
    "cross_family_review_source_count": 3,
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
    "family_count": 9,
    "implemented": ["LWE", "MLWE"],
    "per_family_future_reviewed_adapter_source_counts": {
        "CODE_BASED": 3,
        "HASH_BASED": 1,
        "IMPLEMENTATION_SECURITY": 8,
        "ISOGENY_HISTORICAL": 0,
        "LWE": 2,
        "MLWE": 2,
        "MULTIVARIATE": 1,
        "NTRU": 2,
        "SIS": 2,
    },
    "plugin_count": 6,
    "plugins": [
        "code_based",
        "hash_based",
        "implementation_security",
        "isogeny_historical",
        "lattice",
        "multivariate",
    ],
    "public_example_count": 79,
    "review_required_before_claims": True,
    "schema_only": ["NTRU", "SIS"],
    "toy_evaluators": [
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "MULTIVARIATE",
    ],
    "support_level_counts": {
        "implemented": 2,
        "schema_only": 2,
        "toy_evaluator": 5,
    },
    "unique_future_reviewed_adapter_source_count": 15,
}
EXPECTED_SOURCE_CATALOG_SCOPE = {
    "non_lattice_toy_evaluator_count": 41,
    "non_lattice_toy_operator_families": [
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "MULTIVARIATE",
    ],
    "non_lattice_toy_operator_security_claims": 0,
    "non_lattice_toy_operator_variant_count": 41,
    "source_count": 41,
}
EXPECTED_PUBLIC_PRIVATE_BOUNDARY = {
    "report_generator_redaction": {
        "blocking": True,
        "check_id": "report-generator-redaction",
        "private_evaluator_output_absent": True,
        "private_mapping_evaluator_output_absent": True,
        "private_mapping_score_absent": True,
        "private_mapping_target_absent": True,
        "private_mutation_absent": True,
        "private_score_absent": True,
        "raw_mapping_redaction_covered": True,
        "redacted_records": 2,
        "sensitive_target_absent": True,
        "status": "passed",
        "typed_trace_redaction_covered": True,
    }
}


def _valid_public_attack_plan_paths() -> list[Path]:
    paths = []
    for path in sorted(Path("examples/attack_plans").glob("*.json")):
        try:
            plan = AttackPlan.model_validate_json(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if plan.metadata.public:
            paths.append(path)
    return paths


def test_prime_environment_manifest_describes_packaged_verifier_tasks(
    tmp_path: Path,
) -> None:
    out = tmp_path / "prime_manifest.json"

    manifest = write_prime_environment_manifest(out)

    assert manifest == build_prime_environment_manifest()
    assert json.loads(out.read_text(encoding="utf-8")) == manifest
    assert manifest["schema_version"] == (
        "agades.pqc.prime_environment_manifest.v1"
    )
    assert manifest["project"] == {
        "name": "Agades PQC Verifier Environment",
        "environment_package": "agades-pqc-verifier-env",
        "source_package": "agades-pqc-gym",
        "entrypoint": "agades_pqc_verifier_env:load_environment",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert manifest["prime"] == {
        "environment_dir": "prime_intellect/verifiers_environment",
        "eval_config_path": "prime_intellect/evals/agades_pqc_eval.template.toml",
        "eval_manifest_path": "docs/prime_eval_config_manifest.json",
        "eval_config_verify_command": (
            "uv run agades-pqc prime-eval-config-verify --config "
            "prime_intellect/evals/agades_pqc_eval.template.toml --manifest "
            "docs/prime_eval_config_manifest.json"
        ),
        "local_editable_install_command": (
            "cd prime_intellect/verifiers_environment && uv pip install -e ."
        ),
        "local_eval_command": (
            "cd prime_intellect/verifiers_environment && "
            "uv run vf-eval agades-pqc-verifier-env"
        ),
        "hub_private_push_command": (
            "prime env push --path prime_intellect/verifiers_environment "
            "--visibility PRIVATE"
        ),
        "hub_install_command_template": (
            "prime env install <owner>/agades-pqc-verifier-env"
        ),
        "public_push_requires_review": True,
    }
    assert manifest["evaluation_defaults"] == {
        "num_examples": 2,
        "rollouts_per_example": 1,
    }
    assert manifest["family_support"] == EXPECTED_FAMILY_SUPPORT
    assert manifest["source_catalog_scope"] == EXPECTED_SOURCE_CATALOG_SCOPE
    assert manifest["public_private_boundary"] == EXPECTED_PUBLIC_PRIVATE_BOUNDARY
    assert manifest["task_manifest"]["task_count"] == len(
        _valid_public_attack_plan_paths()
    )
    assert manifest["task_manifest"]["families"] == [
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "LWE",
        "MLWE",
        "MULTIVARIATE",
        "NTRU",
        "SIS",
    ]
    assert "data/lattice_primal_usvp_toy.json" in manifest["task_manifest"][
        "source_paths"
    ]
    assert "data/lattice_lwe_modulus_switching_primary.json" in manifest[
        "task_manifest"
    ]["source_paths"]
    assert "data/code_based_qc_rotation_toy.json" in manifest["task_manifest"][
        "source_paths"
    ]
    assert "data/code_based_classic_mceliece_syndrome_toy.json" in manifest[
        "task_manifest"
    ]["source_paths"]
    assert manifest["task_manifest"]["task_metadata_schema"] == TASK_METADATA_SCHEMA
    assert manifest["task_manifest"]["task_summary"] == EXPECTED_TASK_METADATA_SUMMARY
    assert manifest["source_mirror"]["source_dir"] == "examples/attack_plans"
    assert manifest["source_mirror"]["data_dir"] == (
        "prime_intellect/verifiers_environment/data"
    )
    assert manifest["source_mirror"]["mirrors_valid_public_examples"] is True
    assert manifest["source_mirror"]["valid_public_example_count"] == len(
        _valid_public_attack_plan_paths()
    )
    assert manifest["source_mirror"]["packaged_data_file_count"] == len(
        _valid_public_attack_plan_paths()
    )
    source_mirror = manifest["source_mirror"]
    assert (
        "examples/attack_plans/lattice_primal_usvp_toy.json"
        in source_mirror["source_example_paths"]
    )
    assert (
        "prime_intellect/verifiers_environment/data/lattice_primal_usvp_toy.json"
        in source_mirror["packaged_data_paths"]
    )
    assert manifest["scoring_contract"] == {
        "reward_range": [0.0, 1.0],
        "accepted_reward": 1.0,
        "unsupported_reward": 0.0,
        "invalid_reward": 0.0,
        "requires_single_json_object": True,
        "accepts_executable_code": False,
        "formal_artifact_binding_schema": (
            "agades.pqc.rl.formal_artifact_binding.v1"
        ),
        "review_governance_binding_schema": (
            "agades.pqc.formal.proof_artifact.reviewer_governance_binding.v1"
        ),
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
            "operator_types/operator_params/operator_assumptions; "
            "attack_plan_id may change; semantic-mutation tasks may change "
            "operator_params only when explicitly required"
        ),
        "challenge_suite_contract": {
            "challenge_types": [
                "claims_guard_repair",
                "contextual_claims_guard_decoy_repair",
                "semantic_mutation_repair",
                "wrong_family_decoy_repair",
                "multi_trap_repair",
                "contextual_multi_trap_repair",
                "implicit_operator_semantics_repair",
                "reviewer_decision",
                "reviewer_decision_hard",
                "operator_mismatch_repair",
                "operator_param_mismatch_repair",
                "missing_hypothesis_repair",
                "invented_complexity_repair",
                "unsupported_refusal",
            ],
            "balanced_heldout_parameter": "min_challenge_examples_per_type",
            "balanced_heldout_policy": "balanced_min_per_type_v1",
            "recommended_min_examples_per_type": 8,
            "claim_boundary": (
                "adapter-improvement claims require a held-out broad "
                "challenge suite with sufficient examples for every "
                "required challenge type"
            ),
        },
        "prompt_profiles": {
            "attackplan_json": {
                "intended_use": "private_training_or_eval",
                "contract": (
                    "submit one AttackPlan JSON object for the seed task; "
                    "return an already valid seed unchanged; do not invent "
                    "pre-evaluation claims; do not include markdown, "
                    "prose, analysis, comments, code fences, or wrapper text"
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
            "semantic_mutation_repair": {
                "intended_use": "private_semantic_mutation_curriculum",
                "contract": (
                    "mutate a valid seed AttackPlan semantically while "
                    "preserving target metadata, operator family, unknown "
                    "claim fields, and no-claim boundaries"
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
                        "weighted format-repair signal; exact valid readable "
                        "JSON can receive full reward, wrapped JSON can "
                        "receive partial non-accepted reward, and provider "
                        "hidden reasoning is tracked outside the visible "
                        "student_readability reward"
                    ),
                    "accepted_candidates_still_require_strict_acceptance": True,
                "rubric_weights": {
                    "accepted_attack_plan": 0.22,
                    "single_json_object": 0.16,
                    "formal_validity": 0.20,
                    "cryptographic_applicability": 0.04,
                    "no_security_overclaim": 0.15,
                    "student_readability": 0.15,
                    "reproducibility": 0.02,
                    "reviewer_quality": 0.02,
                    "task_match": 0.03,
                    "proof_obligation_coverage": 0.01,
                },
            },
        },
        "task_info_fields": [
            "schema_version",
            "source_path",
            "seed_attack_plan_sha256",
            "attack_plan_id",
            "target_family",
            "target_name",
            "support_level",
            "operator_types",
            "operator_params",
            "operator_assumptions",
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
    }
    assert manifest["schemas"] == {
        "schema_dir": "prime_intellect/schemas",
        "schema_manifest": "prime_intellect/schemas/schema_manifest.json",
        "submission_schema": "prime_intellect/schemas/attack_plan.schema.json",
        "task_metadata_schema": "prime_intellect/schemas/task_metadata.schema.json",
        "result_schema": "prime_intellect/schemas/verifier_result.schema.json",
        "generator_command": (
            "uv run agades-pqc prime-schemas --out prime_intellect/schemas"
        ),
    }
    assert manifest["safety"] == {
        "contains_private_traces": False,
        "arbitrary_code_execution": False,
        "live_targeting": False,
        "security_claim": False,
        "publishes_private_candidates": False,
    }
    assert manifest["release_gates"] == [
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
    ]


def test_prime_environment_readme_matches_hub_workflow_contract() -> None:
    readme = Path("prime_intellect/verifiers_environment/README.md").read_text(
        encoding="utf-8"
    )

    assert "uv pip install -e ." in readme
    assert "uv run vf-eval agades-pqc-verifier-env" in readme
    assert "prime-eval-config-verify" in readme
    assert "AGADES_PRIME_ENV_REF" in readme
    assert "prime env push --visibility PRIVATE" in readme
    assert "prime env install <owner>/agades-pqc-verifier-env" in readme
    assert "Required Environment Variables" in readme
    assert "No environment variables are required" in readme


def test_committed_prime_environment_manifest_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "prime_manifest.json"
    committed = Path("prime_intellect/verifiers_environment/prime_manifest.json")

    write_prime_environment_manifest(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_prime_manifest_verify_accepts_committed_manifest() -> None:
    result = verify_prime_environment_manifest(
        Path("prime_intellect/verifiers_environment/prime_manifest.json")
    )

    assert result == {
        "schema_version": "agades.pqc.prime_environment_manifest_verification.v1",
        "manifest_path": "prime_intellect/verifiers_environment/prime_manifest.json",
        "accepted": True,
        "summary": {
            "families": [
                "CODE_BASED",
                "HASH_BASED",
                "IMPLEMENTATION_SECURITY",
                "ISOGENY_HISTORICAL",
                "LWE",
                "MLWE",
                "MULTIVARIATE",
                "NTRU",
                "SIS",
            ],
            "families_with_future_reviewed_adapters": 8,
            "family_count": 9,
            "failure_count": 0,
            "mirrored_public_examples": 79,
            "mirrors_public_examples": True,
            "non_lattice_toy_evaluator_count": 41,
            "non_lattice_toy_operator_security_claims": 0,
            "non_lattice_toy_operator_variant_count": 41,
            "packaged_data_file_count": 79,
            "public_push_requires_review": True,
            "raw_mapping_redaction_covered": True,
            "report_redaction_records": 2,
            "review_required_before_claims": True,
            "requires_single_json_object": True,
            "formal_artifact_binding_schema": (
                "agades.pqc.rl.formal_artifact_binding.v1"
            ),
            "review_governance_binding_schema": (
                "agades.pqc.formal.proof_artifact.reviewer_governance_binding.v1"
            ),
            "reviewer_quality_requires_governance": True,
            "task_count": 79,
            "typed_trace_redaction_covered": True,
        },
        "failures": [],
    }


def test_prime_manifest_verify_rejects_executable_submission(
    tmp_path: Path,
) -> None:
    out = tmp_path / "prime_manifest.json"
    manifest = build_prime_environment_manifest()
    manifest["scoring_contract"]["accepts_executable_code"] = True
    manifest["safety"]["arbitrary_code_execution"] = True
    manifest["family_support"]["review_required_before_claims"] = False
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_prime_environment_manifest(out)

    assert result["accepted"] is False
    assert "Prime environment manifest is not in sync." in result["failures"]
    assert "Prime manifest allows executable model submissions." in result["failures"]
    assert "Prime manifest advertises arbitrary execution." in result["failures"]
    assert (
        "Prime manifest family support must require review before claims."
        in result["failures"]
    )


def test_prime_manifest_verify_rejects_source_scope_claim(
    tmp_path: Path,
) -> None:
    out = tmp_path / "prime_manifest.json"
    manifest = build_prime_environment_manifest()
    manifest["source_catalog_scope"]["non_lattice_toy_operator_security_claims"] = 1
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_prime_environment_manifest(out)

    assert result["accepted"] is False
    assert "Prime environment manifest is not in sync." in result["failures"]
    assert (
        "Prime manifest source catalog scope must not contain "
        "non-lattice toy security claims."
    ) in result["failures"]


def test_prime_manifest_verify_rejects_redaction_boundary_drift(
    tmp_path: Path,
) -> None:
    out = tmp_path / "prime_manifest.json"
    manifest = build_prime_environment_manifest()
    manifest["public_private_boundary"]["report_generator_redaction"][
        "raw_mapping_redaction_covered"
    ] = False
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_prime_environment_manifest(out)

    assert result["accepted"] is False
    assert result["summary"]["raw_mapping_redaction_covered"] is False
    assert "Prime environment manifest is not in sync." in result["failures"]
    assert (
        "Prime manifest raw trace mapping redaction gate is incomplete."
        in result["failures"]
    )


def test_prime_manifest_verify_rejects_empty_json_object(tmp_path: Path) -> None:
    out = tmp_path / "prime_manifest.json"
    out.write_text("{}\n", encoding="utf-8")

    result = verify_prime_environment_manifest(out)

    assert result["accepted"] is False
    assert "Prime environment manifest is not in sync." in result["failures"]
    assert "Prime environment manifest project must be an object." in result["failures"]


def test_prime_manifest_cli_writes_manifest(tmp_path: Path) -> None:
    out = tmp_path / "prime_manifest.json"

    result = CliRunner().invoke(app, ["prime-manifest", "--out", str(out)])

    assert result.exit_code == 0
    assert f"prime_manifest={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["schema_version"] == (
        "agades.pqc.prime_environment_manifest.v1"
    )


def test_prime_manifest_verify_cli_accepts_current_manifest() -> None:
    result = CliRunner().invoke(
        app,
        [
            "prime-manifest-verify",
            "--manifest",
            "prime_intellect/verifiers_environment/prime_manifest.json",
        ],
    )

    assert result.exit_code == 0
    assert "agades.pqc.prime_environment_manifest_verification.v1" in result.output
    assert '"accepted": true' in result.output
