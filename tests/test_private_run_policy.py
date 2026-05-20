from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.private_run_policy import (
    PRIVATE_RUN_POLICY_VERIFICATION_SCHEMA,
    build_private_run_policy,
    verify_private_run_policy,
    write_private_run_policy,
)


def test_private_run_policy_defines_private_moat_boundaries() -> None:
    policy = build_private_run_policy()

    assert policy["schema_version"] == "agades.pqc.private_run_policy.v1"
    assert policy["project"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "cli": "agades-pqc",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert policy["private_run_defaults"] == {
        "candidate_public_release_ok_default": False,
        "trace_public_release_ok_default": False,
        "external_network_access": False,
        "arbitrary_python_candidates": False,
        "live_targeting": False,
        "security_claims": False,
    }
    assert policy["allowed_private_roots"] == [
        "private/candidates",
        "private/datasets",
        "private/models",
        "private/reports",
        "private/runs",
        "private/traces",
    ]
    assert policy["forbidden_public_roots"] == [
        "docs",
        "examples/public_runs",
        "hf/dataset",
        "prime_intellect/verifiers_environment/data",
        "public",
    ]
    assert policy["required_publication_controls"] == [
        "redact_trace_record",
        "public-bundle",
        "public-ledger",
        "publication-preflight",
        "release-audit",
    ]
    assert policy["private_holdback"] == [
        "serious evolution traces",
        "private prompts and prompt-ranking policies",
        "evaluator weighting and anti-gaming heuristics",
        "unreleased candidate strategies",
        "responsible-disclosure material",
        "pedagogical RL traces and reviewer annotations",
        "private Qwen fine-tuning corpora and adapters",
        (
            "license-reviewed derived datasets from LWE-benchmarking TAPAS "
            "and pq-code-package"
        ),
    ]
    assert policy["private_rl_policy"] == {
        "method": "pedagogical_rl",
        "teacher_student_pattern": "privileged_self_teacher_student",
        "reward_terms": [
            "formal_validity",
            "cryptographic_applicability",
            "no_security_overclaim",
            "student_readability",
            "reproducibility",
            "reviewer_quality",
        ],
        "student_model": "private_qwen3_6_27b",
        "preferred_private_quantization": "gguf_otq_5bit",
        "training_path": "lora_or_qlora_then_private_gguf_otq_quantization",
        "publish_finetuned_model_publicly": False,
        "publish_training_traces_publicly": False,
        "public_metadata_only": True,
    }
    assert policy["private_dataset_policy"] == {
        "sources": [
            "facebookresearch/LWE-benchmarking",
            "facebook/TAPAS",
            "pq-code-package",
        ],
        "required_controls": [
            "license_review",
            "provenance_tracking",
            "deduplication",
            "redaction",
            "contamination_audit",
        ],
        "publish_train_datasets_publicly": False,
        "publish_rollouts_publicly": False,
        "publish_reviewer_annotations_publicly": False,
    }
    assert policy["scheduler_policy"] == {
        "scheduler_enabled_by_default": False,
        "allowed_triggers": [
            "manual_reviewed",
            "local_cron_after_review",
        ],
        "retention": {
            "private_trace_max_age_days": 30,
            "archive_snapshot_max_age_days": 90,
            "review_log_required": True,
            "delete_expired_private_runs": True,
        },
        "approval_gates": [
            "private-run-policy-review",
            "heldout-target-review",
            "retention-owner-review",
            "publication-export-review",
        ],
        "execution_safety": {
            "external_network_access": False,
            "arbitrary_code_execution": False,
            "writes_only_allowed_private_roots": True,
            "publishes_private_trace_outputs": False,
        },
    }
    assert "agades-pqc mutate-candidates" in policy["allowed_private_commands"]
    assert "agades-pqc mutate-archive" in policy["allowed_private_commands"]
    assert "agades-pqc deepevolve-injections" in policy["allowed_private_commands"]
    assert "agades-pqc evolve-batch" in policy["allowed_private_commands"]
    assert "agades-pqc private-evolution-campaign-plan" in policy[
        "allowed_private_commands"
    ]
    assert "agades-pqc heldout-review-log" in policy["allowed_private_commands"]
    assert "agades-pqc heldout-schedule" in policy["allowed_private_commands"]
    assert "agades-pqc heldout-run-schedule" in policy["allowed_private_commands"]
    assert "agades-pqc heldout-review-packet" in policy[
        "allowed_private_commands"
    ]
    assert "agades-pqc heldout-cron-plan" in policy["allowed_private_commands"]
    assert "agades-pqc heldout-batch" in policy["allowed_private_commands"]
    assert "agades-pqc rescore-archive" in policy["allowed_private_commands"]
    assert "agades-pqc archive-snapshot" in policy["allowed_private_commands"]
    assert "agades-pqc lattice-estimator-baseline-run" in policy[
        "allowed_private_commands"
    ]
    assert "agades-pqc lattice-estimator-baseline-review-packet" in policy[
        "allowed_private_commands"
    ]
    assert "agades-pqc lattice-estimator-checkout-preflight" in policy[
        "allowed_private_commands"
    ]
    assert policy["release_gates"] == [
        "uv run agades-pqc private-run-policy --out docs/private_run_policy.json",
        (
            "uv run agades-pqc private-run-policy-verify --policy "
            "docs/private_run_policy.json"
        ),
    ]


def test_committed_private_run_policy_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "private_run_policy.json"
    committed = Path("docs/private_run_policy.json")

    write_private_run_policy(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_private_run_policy_cli_writes_policy(tmp_path: Path) -> None:
    out = tmp_path / "private_run_policy.json"

    result = CliRunner().invoke(app, ["private-run-policy", "--out", str(out)])

    assert result.exit_code == 0
    assert f"private_run_policy={out}" in result.output
    assert json.loads(out.read_text())["schema_version"] == (
        "agades.pqc.private_run_policy.v1"
    )


def test_private_run_policy_verify_accepts_committed_policy() -> None:
    result = verify_private_run_policy(Path("docs/private_run_policy.json"))

    assert result == {
        "schema_version": PRIVATE_RUN_POLICY_VERIFICATION_SCHEMA,
        "policy_path": "docs/private_run_policy.json",
            "accepted": True,
            "summary": {
                "allowed_private_commands": 16,
                "allowed_private_roots": 6,
                "failure_count": 0,
                "forbidden_public_roots": 5,
                "required_publication_controls": 5,
                "scheduler_allowed_triggers": 2,
                "scheduler_approval_gates": 4,
                "scheduler_retention_rules": 4,
                "private_rl_reward_terms": 6,
                "private_dataset_sources": 3,
            },
            "failures": [],
        }


def test_private_run_policy_verify_rejects_public_qwen_publication(
    tmp_path: Path,
) -> None:
    path = tmp_path / "private_run_policy.json"
    policy = build_private_run_policy()
    policy["private_rl_policy"]["publish_finetuned_model_publicly"] = True
    path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n")

    result = verify_private_run_policy(path)

    assert result["accepted"] is False
    assert "Private RL policy must not publish the fine-tuned Qwen model." in result[
        "failures"
    ]


def test_private_run_policy_verify_rejects_public_release_defaults(
    tmp_path: Path,
) -> None:
    path = tmp_path / "private_run_policy.json"
    policy = build_private_run_policy()
    policy["private_run_defaults"]["trace_public_release_ok_default"] = True
    path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n")

    result = verify_private_run_policy(path)

    assert result["accepted"] is False
    assert "Private trace public release default must be false." in result[
        "failures"
    ]


def test_private_run_policy_verify_rejects_public_private_dataset_release(
    tmp_path: Path,
) -> None:
    path = tmp_path / "private_run_policy.json"
    policy = build_private_run_policy()
    policy["private_dataset_policy"]["publish_train_datasets_publicly"] = True
    path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n")

    result = verify_private_run_policy(path)

    assert result["accepted"] is False
    assert "Private dataset policy publish_train_datasets_publicly must be false." in (
        result["failures"]
    )


def test_private_run_policy_verify_rejects_missing_forbidden_public_root(
    tmp_path: Path,
) -> None:
    path = tmp_path / "private_run_policy.json"
    policy = build_private_run_policy()
    policy["forbidden_public_roots"].remove("hf/dataset")
    path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n")

    result = verify_private_run_policy(path)

    assert result["accepted"] is False
    assert "Private run policy must forbid writing private traces to hf/dataset." in (
        result["failures"]
    )


def test_private_run_policy_verify_rejects_enabled_default_scheduler(
    tmp_path: Path,
) -> None:
    path = tmp_path / "private_run_policy.json"
    policy = build_private_run_policy()
    policy["scheduler_policy"]["scheduler_enabled_by_default"] = True
    path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n")

    result = verify_private_run_policy(path)

    assert result["accepted"] is False
    assert "Private run scheduler must be disabled by default." in result[
        "failures"
    ]


def test_private_run_policy_verify_rejects_excessive_trace_retention(
    tmp_path: Path,
) -> None:
    path = tmp_path / "private_run_policy.json"
    policy = build_private_run_policy()
    policy["scheduler_policy"]["retention"]["private_trace_max_age_days"] = 365
    path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n")

    result = verify_private_run_policy(path)

    assert result["accepted"] is False
    assert "Private trace retention may not exceed 30 days." in result[
        "failures"
    ]


def test_private_run_policy_verify_rejects_non_object_scheduler_policy(
    tmp_path: Path,
) -> None:
    path = tmp_path / "private_run_policy.json"
    policy = build_private_run_policy()
    policy["scheduler_policy"] = []
    path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n")

    result = verify_private_run_policy(path)

    assert result["accepted"] is False
    assert "Private run scheduler policy must be a JSON object." in result[
        "failures"
    ]
