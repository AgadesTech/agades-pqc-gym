from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PRIVATE_RUN_POLICY_SCHEMA = "agades.pqc.private_run_policy.v1"
PRIVATE_RUN_POLICY_VERIFICATION_SCHEMA = (
    "agades.pqc.private_run_policy_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
PROJECT = {
    "name": "Agades PQC Gym",
    "package": "agades_pqc_gym",
    "cli": "agades-pqc",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
}
ALLOWED_PRIVATE_ROOTS = [
    "private/candidates",
    "private/datasets",
    "private/models",
    "private/reports",
    "private/runs",
    "private/traces",
]
FORBIDDEN_PUBLIC_ROOTS = [
    "docs",
    "examples/public_runs",
    "hf/dataset",
    "prime_intellect/verifiers_environment/data",
    "public",
]
REQUIRED_PUBLICATION_CONTROLS = [
    "redact_trace_record",
    "public-bundle",
    "public-ledger",
    "publication-preflight",
    "release-audit",
]
ALLOWED_PRIVATE_COMMANDS = [
    "agades-pqc mutate-candidates",
    "agades-pqc mutate-archive",
    "agades-pqc deepevolve-injections",
    "agades-pqc evolve-batch",
    "agades-pqc private-evolution-campaign-plan",
    "agades-pqc heldout-review-log",
    "agades-pqc heldout-schedule",
    "agades-pqc heldout-run-schedule",
    "agades-pqc heldout-review-packet",
    "agades-pqc heldout-cron-plan",
    "agades-pqc heldout-batch",
    "agades-pqc rescore-archive",
    "agades-pqc archive-snapshot",
    "agades-pqc lattice-estimator-baseline-run",
    "agades-pqc lattice-estimator-baseline-review-packet",
    "agades-pqc lattice-estimator-checkout-preflight",
]
PRIVATE_HOLDBACK = [
    "serious evolution traces",
    "private prompts and prompt-ranking policies",
    "evaluator weighting and anti-gaming heuristics",
    "unreleased candidate strategies",
    "responsible-disclosure material",
    "pedagogical RL traces and reviewer annotations",
    "private Qwen fine-tuning corpora and adapters",
    "license-reviewed derived datasets from LWE-benchmarking TAPAS and pq-code-package",
]
PRIVATE_RL_POLICY = {
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
PRIVATE_DATASET_POLICY = {
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
SCHEDULER_ALLOWED_TRIGGERS = [
    "manual_reviewed",
    "local_cron_after_review",
]
SCHEDULER_APPROVAL_GATES = [
    "private-run-policy-review",
    "heldout-target-review",
    "retention-owner-review",
    "publication-export-review",
]
SCHEDULER_RETENTION = {
    "private_trace_max_age_days": 30,
    "archive_snapshot_max_age_days": 90,
    "review_log_required": True,
    "delete_expired_private_runs": True,
}
SCHEDULER_EXECUTION_SAFETY = {
    "external_network_access": False,
    "arbitrary_code_execution": False,
    "writes_only_allowed_private_roots": True,
    "publishes_private_trace_outputs": False,
}


def build_private_run_policy() -> dict[str, Any]:
    return {
        "schema_version": PRIVATE_RUN_POLICY_SCHEMA,
        "project": PROJECT,
        "private_run_defaults": {
            "candidate_public_release_ok_default": False,
            "trace_public_release_ok_default": False,
            "external_network_access": False,
            "arbitrary_python_candidates": False,
            "live_targeting": False,
            "security_claims": False,
        },
        "allowed_private_roots": list(ALLOWED_PRIVATE_ROOTS),
        "forbidden_public_roots": list(FORBIDDEN_PUBLIC_ROOTS),
        "allowed_private_commands": list(ALLOWED_PRIVATE_COMMANDS),
        "required_publication_controls": list(REQUIRED_PUBLICATION_CONTROLS),
        "private_holdback": list(PRIVATE_HOLDBACK),
        "private_rl_policy": dict(PRIVATE_RL_POLICY),
        "private_dataset_policy": dict(PRIVATE_DATASET_POLICY),
        "scheduler_policy": {
            "scheduler_enabled_by_default": False,
            "allowed_triggers": list(SCHEDULER_ALLOWED_TRIGGERS),
            "retention": dict(SCHEDULER_RETENTION),
            "approval_gates": list(SCHEDULER_APPROVAL_GATES),
            "execution_safety": dict(SCHEDULER_EXECUTION_SAFETY),
        },
        "export_policy": {
            "public_trace_exports_require_redaction": True,
            "public_bundle_exports_require_release_audit": True,
            "external_publication_requires_preflight": True,
            "publish_private_candidates": False,
            "publish_private_trace_scores": False,
        },
        "release_gates": [
            "uv run agades-pqc private-run-policy --out docs/private_run_policy.json",
            (
                "uv run agades-pqc private-run-policy-verify --policy "
                "docs/private_run_policy.json"
            ),
        ],
    }


def write_private_run_policy(out: Path) -> dict[str, Any]:
    policy = build_private_run_policy()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(policy, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return policy


def verify_private_run_policy(
    policy_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    resolved_path = (
        policy_path if policy_path.is_absolute() else project_root / policy_path
    )
    failures: list[str] = []
    policy = _read_policy(resolved_path, failures)

    if policy:
        expected = build_private_run_policy()
        if policy != expected:
            failures.append("Private run policy is not in sync.")
        _verify_policy(policy, failures)

    scheduler_policy = _scheduler_policy_for_summary(policy)
    summary = {
        "allowed_private_commands": len(policy.get("allowed_private_commands", [])),
        "allowed_private_roots": len(policy.get("allowed_private_roots", [])),
        "failure_count": len(failures),
        "forbidden_public_roots": len(policy.get("forbidden_public_roots", [])),
        "required_publication_controls": len(
            policy.get("required_publication_controls", [])
        ),
        "scheduler_allowed_triggers": len(
            scheduler_policy.get("allowed_triggers", [])
        ),
        "scheduler_approval_gates": len(
            scheduler_policy.get("approval_gates", [])
        ),
        "scheduler_retention_rules": len(
            scheduler_policy.get("retention", {})
        ),
        "private_rl_reward_terms": len(
            policy.get("private_rl_policy", {}).get("reward_terms", [])
        ),
        "private_dataset_sources": len(
            policy.get("private_dataset_policy", {}).get("sources", [])
        ),
    }
    return {
        "schema_version": PRIVATE_RUN_POLICY_VERIFICATION_SCHEMA,
        "policy_path": policy_path.as_posix(),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _verify_policy(policy: dict[str, Any], failures: list[str]) -> None:
    if policy.get("schema_version") != PRIVATE_RUN_POLICY_SCHEMA:
        failures.append(
            f"Private run policy schema_version must be {PRIVATE_RUN_POLICY_SCHEMA}."
        )
    if policy.get("project") != PROJECT:
        failures.append("Private run policy project metadata is incorrect.")

    defaults = policy.get("private_run_defaults", {})
    if defaults.get("candidate_public_release_ok_default") is not False:
        failures.append("Private candidate public release default must be false.")
    if defaults.get("trace_public_release_ok_default") is not False:
        failures.append("Private trace public release default must be false.")
    for key in (
        "external_network_access",
        "arbitrary_python_candidates",
        "live_targeting",
        "security_claims",
    ):
        if defaults.get(key) is not False:
            failures.append(f"Private run default {key} must be false.")

    allowed_private_roots = policy.get("allowed_private_roots", [])
    if allowed_private_roots != ALLOWED_PRIVATE_ROOTS:
        failures.append("Private run policy allowed private roots are incorrect.")
    forbidden_public_roots = policy.get("forbidden_public_roots", [])
    for root in FORBIDDEN_PUBLIC_ROOTS:
        if root not in forbidden_public_roots:
            failures.append(
                f"Private run policy must forbid writing private traces to {root}."
            )
    if forbidden_public_roots != FORBIDDEN_PUBLIC_ROOTS:
        failures.append("Private run policy forbidden public roots are incorrect.")

    controls = policy.get("required_publication_controls", [])
    for control in REQUIRED_PUBLICATION_CONTROLS:
        if control not in controls:
            failures.append(
                f"Private run policy must require publication control {control}."
            )
    if controls != REQUIRED_PUBLICATION_CONTROLS:
        failures.append("Private run policy publication controls are incorrect.")

    if policy.get("allowed_private_commands") != ALLOWED_PRIVATE_COMMANDS:
        failures.append("Private run policy commands are incorrect.")
    if policy.get("private_holdback") != PRIVATE_HOLDBACK:
        failures.append("Private run holdback list is incorrect.")
    _verify_private_rl_policy(policy.get("private_rl_policy", {}), failures)
    _verify_private_dataset_policy(
        policy.get("private_dataset_policy", {}),
        failures,
    )
    _verify_scheduler_policy(policy.get("scheduler_policy", {}), failures)

    export_policy = policy.get("export_policy", {})
    expected_true = (
        "public_trace_exports_require_redaction",
        "public_bundle_exports_require_release_audit",
        "external_publication_requires_preflight",
    )
    expected_false = (
        "publish_private_candidates",
        "publish_private_trace_scores",
    )
    for key in expected_true:
        if export_policy.get(key) is not True:
            failures.append(f"Private run export policy {key} must be true.")
    for key in expected_false:
        if export_policy.get(key) is not False:
            failures.append(f"Private run export policy {key} must be false.")


def _verify_private_rl_policy(
    private_rl_policy: Any,
    failures: list[str],
) -> None:
    if private_rl_policy != PRIVATE_RL_POLICY:
        failures.append("Private RL policy is incorrect.")
    if private_rl_policy.get("method") != "pedagogical_rl":
        failures.append("Private RL policy must use pedagogical_rl.")
    if private_rl_policy.get("publish_finetuned_model_publicly") is not False:
        failures.append("Private RL policy must not publish the fine-tuned Qwen model.")
    if private_rl_policy.get("publish_training_traces_publicly") is not False:
        failures.append("Private RL policy must not publish training traces.")


def _verify_private_dataset_policy(
    private_dataset_policy: Any,
    failures: list[str],
) -> None:
    if private_dataset_policy != PRIVATE_DATASET_POLICY:
        failures.append("Private dataset policy is incorrect.")
    for key in (
        "publish_train_datasets_publicly",
        "publish_rollouts_publicly",
        "publish_reviewer_annotations_publicly",
    ):
        if private_dataset_policy.get(key) is not False:
            failures.append(f"Private dataset policy {key} must be false.")


def _verify_scheduler_policy(
    scheduler_policy: Any,
    failures: list[str],
) -> None:
    if not isinstance(scheduler_policy, dict):
        failures.append("Private run scheduler policy must be a JSON object.")
        return

    if scheduler_policy.get("scheduler_enabled_by_default") is not False:
        failures.append("Private run scheduler must be disabled by default.")
    if scheduler_policy.get("allowed_triggers") != SCHEDULER_ALLOWED_TRIGGERS:
        failures.append("Private run scheduler triggers are incorrect.")
    if scheduler_policy.get("approval_gates") != SCHEDULER_APPROVAL_GATES:
        failures.append("Private run scheduler approval gates are incorrect.")

    retention = scheduler_policy.get("retention", {})
    if retention != SCHEDULER_RETENTION:
        failures.append("Private run scheduler retention policy is incorrect.")
    if retention.get("private_trace_max_age_days", 0) > 30:
        failures.append("Private trace retention may not exceed 30 days.")
    if retention.get("archive_snapshot_max_age_days", 0) > 90:
        failures.append("Archive snapshot retention may not exceed 90 days.")
    if retention.get("review_log_required") is not True:
        failures.append("Private run scheduler must require a review log.")
    if retention.get("delete_expired_private_runs") is not True:
        failures.append("Private run scheduler must delete expired private runs.")

    execution_safety = scheduler_policy.get("execution_safety", {})
    if execution_safety != SCHEDULER_EXECUTION_SAFETY:
        failures.append("Private run scheduler execution safety is incorrect.")
    if execution_safety.get("external_network_access") is not False:
        failures.append("Private run scheduler must not use external networking.")
    if execution_safety.get("arbitrary_code_execution") is not False:
        failures.append("Private run scheduler must not execute arbitrary code.")
    if execution_safety.get("writes_only_allowed_private_roots") is not True:
        failures.append("Private run scheduler must write only allowed private roots.")
    if execution_safety.get("publishes_private_trace_outputs") is not False:
        failures.append("Private run scheduler must not publish private trace outputs.")


def _scheduler_policy_for_summary(policy: dict[str, Any]) -> dict[str, Any]:
    scheduler_policy = policy.get("scheduler_policy", {})
    if isinstance(scheduler_policy, dict):
        return scheduler_policy
    return {}


def _read_policy(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"Private run policy is missing: {path.as_posix()}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"Private run policy is invalid JSON at line {exc.lineno}.")
        return {}
    if not isinstance(payload, dict):
        failures.append("Private run policy must be a JSON object.")
        return {}
    return payload
