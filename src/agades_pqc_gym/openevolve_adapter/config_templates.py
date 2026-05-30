from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agades_pqc_gym.deepevolve_hooks.injection import (
    PAPER_CARD_INJECTION_BATCH_SCHEMA,
)
from agades_pqc_gym.evolution.campaign import (
    PRIVATE_EVOLUTION_CAMPAIGN_PLAN_SCHEMA,
)
from agades_pqc_gym.evolution.cron import HELDOUT_CRON_PLAN_SCHEMA
from agades_pqc_gym.evolution.scheduler import HELDOUT_REVIEW_LOG_SCHEMA
from agades_pqc_gym.evolution.snapshot import PRIVATE_ARCHIVE_SNAPSHOT_SCHEMA
from agades_pqc_gym.integrations.private_qwen_artifacts import (
    PRIVATE_QWEN_ARTIFACT_PLAN_ENV,
    PRIVATE_QWEN_ARTIFACT_PLAN_SCHEMA,
    PRIVATE_QWEN_ARTIFACT_PLAN_TEMPLATE,
    PRIVATE_QWEN_ARTIFACT_VERIFICATION_COMMAND,
    PRIVATE_QWEN_ARTIFACT_VERIFICATION_SCHEMA,
)
from agades_pqc_gym.integrations.private_training_config import (
    PRIVATE_TRAINING_REQUIRED_ENV_VARS,
)

OPENEVOLVE_CONFIG_TEMPLATE_VERIFICATION_SCHEMA = (
    "agades.pqc.openevolve_config_template_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = Path("examples/openevolve/config.yaml")
OPENEVOLVE_CONFIG_ARCHIVE_LOOP_KEYS = (
    "archive_mutation_command",
    "archive_snapshot_command",
    "heldout_batch_command",
    "heldout_cron_plan_command",
    "heldout_rescore_command",
    "heldout_review_log_command",
    "heldout_run_schedule_command",
    "heldout_schedule_command",
    "local_batch_command",
    "local_mutation_command",
    "next_generation_batch_command",
    "paper_card_injection_command",
    "private_campaign_plan_command",
)
_COMMAND_SNIPPETS = {
    "archive_mutation_command": "agades-pqc mutate-archive",
    "archive_snapshot_command": "agades-pqc archive-snapshot",
    "heldout_batch_command": "agades-pqc heldout-batch",
    "heldout_cron_plan_command": "agades-pqc heldout-cron-plan",
    "heldout_rescore_command": "agades-pqc rescore-archive",
    "heldout_review_log_command": "agades-pqc heldout-review-log",
    "heldout_run_schedule_command": "agades-pqc heldout-run-schedule",
    "heldout_schedule_command": "agades-pqc heldout-schedule",
    "local_batch_command": "agades-pqc evolve-batch",
    "local_mutation_command": "agades-pqc mutate-candidates",
    "next_generation_batch_command": "agades-pqc evolve-batch",
    "paper_card_injection_command": "agades-pqc deepevolve-injections",
    "private_campaign_plan_command": "agades-pqc private-evolution-campaign-plan",
}
_SCHEMA_SYNC_KEYS = (
    "mutation_batch_schema",
    "paper_card_injection_schema",
    "archive_schema",
    "archive_snapshot_schema",
    "private_campaign_plan_schema",
    "heldout_review_log_schema",
    "heldout_schedule_schema",
    "heldout_schedule_run_schema",
    "heldout_cron_plan_schema",
    "heldout_rescore_schema",
)
PRIVATE_QWEN_RESEARCH_ROLES = [
    "generate_attackplan",
    "mutate_attackplan",
    "critique_attackplan",
    "repair_attackplan",
    "draft_proof_obligations",
    "draft_family_invariants",
    "propose_evaluation_strategy",
]
PRIVATE_QWEN_RESEARCH_ENGINE = {
    "model": "Qwen3.6-27B-private",
    "model_artifact_env": "AGADES_QWEN_BASE_MODEL",
    "lora_adapter_env": "AGADES_QWEN_LORA_ADAPTER_PATH",
    "gguf_otq_5bit_env": "AGADES_QWEN_GGUF_OTQ_5BIT_PATH",
    "artifact_plan_env": PRIVATE_QWEN_ARTIFACT_PLAN_ENV,
    "artifact_plan_template": PRIVATE_QWEN_ARTIFACT_PLAN_TEMPLATE,
    "artifact_plan_schema": PRIVATE_QWEN_ARTIFACT_PLAN_SCHEMA,
    "artifact_verification_schema": PRIVATE_QWEN_ARTIFACT_VERIFICATION_SCHEMA,
    "artifact_verification_command": PRIVATE_QWEN_ARTIFACT_VERIFICATION_COMMAND,
    "required_env_vars": list(PRIVATE_TRAINING_REQUIRED_ENV_VARS),
    "training_manifest": "docs/private_training_config_manifest.json",
    "training_readiness": "docs/private_training_readiness.json",
    "pedagogical_rl_method": "docs/pedagogical_rl_method.json",
    "dataset_curation_manifest": "docs/private_dataset_curation.json",
    "public_model_id_allowed": False,
    "consumers": ["openevolve", "deepevolve"],
    "research_roles": list(PRIVATE_QWEN_RESEARCH_ROLES),
    "tracks": {
        "public_toy_eval": {
            "private_qwen_allowed": False,
            "private_data_allowed": False,
            "security_claims_allowed": False,
        },
        "private_serious_research": {
            "private_qwen_allowed": True,
            "publication_allowed": False,
            "requires_formal_validation": True,
            "requires_estimator_compatibility": True,
            "requires_private_qwen_artifact_verification": True,
            "requires_private_training_readiness": True,
            "requires_human_review_before_claim": True,
        },
    },
}

DEFAULT_CONFIG_TEMPLATE = {
    "program_type": "json_attack_plan",
    "evaluator": "examples/openevolve/evaluator.py",
    "primary_metric": "combined_score",
    "private_qwen_research_engine": PRIVATE_QWEN_RESEARCH_ENGINE,
    "candidate_roots": [
        "benchmarks/lattice_toy_lwe/lwe_n64_q257.json",
        "benchmarks/code_based_toy_isd",
        "benchmarks/multivariate_toy_mq",
        "benchmarks/hash_based_toy_bound",
        "benchmarks/implementation_security_toy_kat",
        "benchmarks/isogeny_historical_toy_path",
    ],
    "mutation_batch_schema": "agades.pqc.candidate_mutation_batch.v1",
    "paper_card_injection_schema": PAPER_CARD_INJECTION_BATCH_SCHEMA,
    "paper_card_injection_command": (
        "agades-pqc deepevolve-injections "
        "--out private/candidates/paper_card_injections.json "
        "--policy docs/private_run_policy.json "
        "--paper-card-dir examples/paper_cards "
        "--run-id paper-card-injection"
    ),
    "local_mutation_command": (
        "agades-pqc mutate-candidates <seed-plan-or-benchmark> "
        "--out runs/candidate_mutations "
        "--generation 1 "
        "--max-mutations-per-plan 4"
    ),
    "local_batch_command": (
        "agades-pqc evolve-batch runs/candidate_mutations/plans "
        "--trace-out runs/evolution_trace.jsonl "
        "--archive-out runs/evolution_archive.json"
    ),
    "archive_schema": "agades.pqc.evolution_archive.v1",
    "archive_snapshot_schema": PRIVATE_ARCHIVE_SNAPSHOT_SCHEMA,
    "private_campaign_plan_schema": PRIVATE_EVOLUTION_CAMPAIGN_PLAN_SCHEMA,
    "private_campaign_plan_command": (
        "agades-pqc private-evolution-campaign-plan "
        "<seed-plan-or-benchmark> "
        "<heldout-target-or-benchmark> "
        "--out private/runs/private_evolution_campaign/campaign_plan.json "
        "--policy docs/private_run_policy.json "
        "--review-log private/runs/heldout_review_log.json "
        "--run-id private-evolution-campaign"
    ),
    "archive_snapshot_command": (
        "agades-pqc archive-snapshot runs/evolution_archive.json "
        "runs/evolution_trace.jsonl "
        "--out private/runs/archive_snapshot.json "
        "--review-log private/runs/heldout_review_log.json "
        "--policy docs/private_run_policy.json "
        "--run-id evolution-archive-snapshot"
    ),
    "archive_mutation_command": (
        "agades-pqc mutate-archive runs/evolution_archive.json "
        "runs/evolution_trace.jsonl "
        "--out runs/archive_mutations "
        "--max-mutations-per-elite 4"
    ),
    "next_generation_batch_command": (
        "agades-pqc evolve-batch runs/archive_mutations/plans "
        "--trace-out runs/archive_mutation_trace.jsonl "
        "--archive-out runs/archive_mutation_archive.json"
    ),
    "heldout_review_log_schema": HELDOUT_REVIEW_LOG_SCHEMA,
    "heldout_review_log_command": (
        "agades-pqc heldout-review-log "
        "--out private/runs/heldout_review_log.json "
        "--approval private-run-policy-review "
        "--approval heldout-target-review "
        "--approval retention-owner-review "
        "--approval publication-export-review "
        "--reviewed-by <reviewer> "
        "--review-id <review-id>"
    ),
    "heldout_schedule_schema": "agades.pqc.heldout_schedule.v1",
    "heldout_schedule_command": (
        "agades-pqc heldout-schedule runs/evolution_archive.json "
        "runs/evolution_trace.jsonl "
        "<heldout-target-or-benchmark> "
        "--out private/runs/heldout_schedule.json "
        "--trace-out private/traces/heldout_trace.jsonl "
        "--rescore-out private/reports/heldout_rescore.json "
        "--review-log private/runs/heldout_review_log.json "
        "--trigger local_cron_after_review "
        "--approval private-run-policy-review "
        "--approval heldout-target-review "
        "--approval retention-owner-review "
        "--approval publication-export-review"
    ),
    "heldout_schedule_run_schema": "agades.pqc.heldout_schedule_run.v1",
    "heldout_run_schedule_command": (
        "agades-pqc heldout-run-schedule private/runs/heldout_schedule.json "
        "--policy docs/private_run_policy.json"
    ),
    "heldout_cron_plan_schema": HELDOUT_CRON_PLAN_SCHEMA,
    "heldout_cron_plan_command": (
        "agades-pqc heldout-cron-plan private/runs/heldout_schedule.json "
        "--out private/runs/heldout_cron_plan.json "
        "--policy docs/private_run_policy.json "
        "--minute 17 "
        "--every-hours 6 "
        "--log-path private/runs/heldout_cron.log"
    ),
    "heldout_batch_command": (
        "agades-pqc heldout-batch runs/evolution_archive.json "
        "runs/evolution_trace.jsonl "
        "<heldout-target-or-benchmark> "
        "--trace-out runs/heldout_trace.jsonl "
        "--rescore-out runs/heldout_rescore.json"
    ),
    "heldout_rescore_schema": "agades.pqc.heldout_rescore.v1",
    "heldout_rescore_command": (
        "agades-pqc rescore-archive runs/evolution_archive.json "
        "runs/heldout_trace.jsonl "
        "--out runs/heldout_rescore.json"
    ),
    "safety": {
        "arbitrary_code_execution": False,
        "publishes_private_candidates": False,
        "security_claim": False,
    },
    "notes": [
        "JSON AttackPlans are supported in the MVP.",
        (
            "deepevolve-injections writes a private paper-card injection "
            "queue for review-gated literature hypotheses; it does not "
            "write AttackPlans, execute code, or change estimator scores."
        ),
        (
            "mutate-candidates generates private JSON-only candidate plans "
            "from reviewed lattice, code-based, multivariate, hash-based, "
            "implementation-security, and historical-isogeny toy rules."
        ),
        "evolve-batch keeps the best accepted candidate per MAP-Elites feature cell.",
        (
            "mutate-archive generates next-generation private candidates "
            "from archive elites and source trace links."
        ),
        (
            "archive-snapshot writes a private archive snapshot manifest "
            "with digests, retention metadata, and trace-link integrity only."
        ),
        (
            "private-evolution-campaign-plan records the reviewed long-running "
            "campaign argv sequence without executing commands or embedding "
            "private traces, scores, or candidate sources."
        ),
        (
            "heldout-batch creates private same-family re-evaluation traces "
            "from archive elites."
        ),
        (
            "heldout-schedule writes a reviewed private schedule manifest "
            "with a private review-log digest before any automated held-out run."
        ),
        (
            "heldout-run-schedule consumes that manifest through typed Python "
            "APIs without executing shell command strings."
        ),
        (
            "heldout-cron-plan writes a private crontab fragment for manual "
            "local installation and never edits the system crontab."
        ),
        "held-out rescore aggregates explicit TraceRecord parent links only.",
        "Python candidates are intentionally not executed without sandboxing.",
    ],
}


def write_default_config_template(out: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    resolved_out = _resolve(ROOT, out)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(
        yaml.safe_dump(
            DEFAULT_CONFIG_TEMPLATE,
            sort_keys=False,
            allow_unicode=False,
        ),
        encoding="utf-8",
    )
    return DEFAULT_CONFIG_TEMPLATE


def verify_default_config_template(
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    resolved_config = _resolve(project_root, config_path)
    config = _read_yaml_config(resolved_config, failures)
    checked_config_synced = config == DEFAULT_CONFIG_TEMPLATE

    if not checked_config_synced:
        failures.append(
            "OpenEvolve checked config is not in sync with DEFAULT_CONFIG_TEMPLATE."
        )

    _verify_config_contract(config, failures)

    return {
        "schema_version": OPENEVOLVE_CONFIG_TEMPLATE_VERIFICATION_SCHEMA,
        "config_path": _display_path(config_path),
        "accepted": not failures,
        "summary": _verification_summary(
            config,
            failures,
            checked_config_synced=checked_config_synced,
        ),
        "failures": failures,
    }


def _resolve(root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return root / path


def _display_path(path: Path) -> str:
    return path.as_posix()


def _read_yaml_config(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"OpenEvolve checked config is missing: {path}.")
        return {}
    except yaml.YAMLError as exc:
        failures.append(f"OpenEvolve checked config is invalid YAML: {exc}.")
        return {}
    if not isinstance(payload, dict):
        failures.append("OpenEvolve checked config must be a YAML mapping.")
        return {}
    return payload


def _verify_config_contract(config: dict[str, Any], failures: list[str]) -> None:
    missing_template_keys = [
        key
        for key in OPENEVOLVE_CONFIG_ARCHIVE_LOOP_KEYS
        if key not in DEFAULT_CONFIG_TEMPLATE
    ]
    missing_config_keys = [
        key for key in OPENEVOLVE_CONFIG_ARCHIVE_LOOP_KEYS if key not in config
    ]
    if missing_template_keys:
        failures.append(
            "OpenEvolve template is missing archive loop keys: "
            f"{', '.join(missing_template_keys)}."
        )
    if missing_config_keys:
        failures.append(
            "OpenEvolve checked config is missing archive loop keys: "
            f"{', '.join(missing_config_keys)}."
        )

    for key, snippet in _COMMAND_SNIPPETS.items():
        if snippet not in str(DEFAULT_CONFIG_TEMPLATE.get(key, "")):
            failures.append(f"OpenEvolve template {key} lacks {snippet}.")
        if snippet not in str(config.get(key, "")):
            failures.append(f"OpenEvolve checked config {key} lacks {snippet}.")

    for key in _SCHEMA_SYNC_KEYS:
        if DEFAULT_CONFIG_TEMPLATE.get(key) != config.get(key):
            failures.append(f"OpenEvolve config {key} is not synchronized.")

    _verify_private_qwen_research_engine(
        DEFAULT_CONFIG_TEMPLATE.get("private_qwen_research_engine"),
        label="OpenEvolve template private Qwen research engine",
        failures=failures,
    )
    _verify_private_qwen_research_engine(
        config.get("private_qwen_research_engine"),
        label="OpenEvolve private Qwen research engine",
        failures=failures,
    )

    safety = config.get("safety", {})
    if not isinstance(safety, dict):
        failures.append("OpenEvolve config safety block must be a mapping.")
    else:
        if safety.get("arbitrary_code_execution") is not False:
            failures.append("OpenEvolve config arbitrary_code_execution must be false.")
        if safety.get("publishes_private_candidates") is not False:
            failures.append(
                "OpenEvolve config publishes_private_candidates must be false."
            )
        if safety.get("security_claim") is not False:
            failures.append("OpenEvolve config security_claim must be false.")

    notes = config.get("notes", [])
    if not any(
        isinstance(note, str) and "Python candidates" in note and "sandboxing" in note
        for note in notes
    ):
        failures.append(
            "OpenEvolve config must document that Python candidates are not executed."
        )

    template_safety = DEFAULT_CONFIG_TEMPLATE.get("safety", {})
    if not isinstance(template_safety, dict):
        failures.append("OpenEvolve template safety block must be a mapping.")
    else:
        if template_safety.get("arbitrary_code_execution") is not False:
            failures.append("OpenEvolve template must not enable arbitrary code.")
        if template_safety.get("publishes_private_candidates") is not False:
            failures.append("OpenEvolve template must not publish private candidates.")
        if template_safety.get("security_claim") is not False:
            failures.append("OpenEvolve template must not make security claims.")


def _verify_private_qwen_research_engine(
    engine: object,
    *,
    label: str,
    failures: list[str],
) -> None:
    if not isinstance(engine, dict):
        failures.append(f"{label} must be a mapping.")
        return
    expected = PRIVATE_QWEN_RESEARCH_ENGINE
    runtime_contract_ok = True
    for key in (
        "model",
        "model_artifact_env",
        "lora_adapter_env",
        "gguf_otq_5bit_env",
        "artifact_plan_env",
        "artifact_plan_template",
        "artifact_plan_schema",
        "artifact_verification_schema",
        "artifact_verification_command",
        "required_env_vars",
        "training_manifest",
        "training_readiness",
        "pedagogical_rl_method",
        "dataset_curation_manifest",
        "public_model_id_allowed",
        "consumers",
        "research_roles",
    ):
        if engine.get(key) != expected[key]:
            runtime_contract_ok = False
            failures.append(f"{label} {key} is not synchronized.")
    if not runtime_contract_ok:
        failures.append("OpenEvolve private Qwen runtime contract is incomplete.")

    tracks = engine.get("tracks")
    if not isinstance(tracks, dict):
        failures.append(f"{label} tracks must be a mapping.")
        return
    public_track = tracks.get("public_toy_eval")
    if not isinstance(public_track, dict):
        failures.append(f"{label} public_toy_eval track must be a mapping.")
    else:
        if public_track.get("private_qwen_allowed") is not False:
            failures.append(
                "OpenEvolve public toy track must not use the private Qwen model."
            )
        if public_track.get("private_data_allowed") is not False:
            failures.append(
                "OpenEvolve public toy track must not use private data."
            )
        if public_track.get("security_claims_allowed") is not False:
            failures.append(
                "OpenEvolve public toy track must not allow security claims."
            )
    private_track = tracks.get("private_serious_research")
    if not isinstance(private_track, dict):
        failures.append(f"{label} private_serious_research track must be a mapping.")
        return
    if private_track.get("private_qwen_allowed") is not True:
        failures.append("OpenEvolve private research track must allow private Qwen.")
    if private_track.get("publication_allowed") is not False:
        failures.append(
            "OpenEvolve private Qwen research track must not be publishable."
        )
    if private_track.get("requires_formal_validation") is not True:
        failures.append("OpenEvolve private Qwen track must require formal validation.")
    if private_track.get("requires_estimator_compatibility") is not True:
        failures.append(
            "OpenEvolve private Qwen track must require estimator compatibility."
        )
    if private_track.get("requires_private_qwen_artifact_verification") is not True:
        failures.append(
            "OpenEvolve private Qwen track must require artifact verification."
        )
    if private_track.get("requires_private_training_readiness") is not True:
        failures.append(
            "OpenEvolve private Qwen track must require private training readiness."
        )
    if private_track.get("requires_human_review_before_claim") is not True:
        failures.append(
            "OpenEvolve private Qwen track must require human review before claims."
        )


def _private_qwen_enabled(config: dict[str, Any]) -> bool:
    engine = config.get("private_qwen_research_engine")
    if not isinstance(engine, dict):
        return False
    tracks = engine.get("tracks")
    if not isinstance(tracks, dict):
        return False
    private_track = tracks.get("private_serious_research")
    if not isinstance(private_track, dict):
        return False
    return private_track.get("private_qwen_allowed") is True


def _verification_summary(
    config: dict[str, Any],
    failures: list[str],
    *,
    checked_config_synced: bool,
) -> dict[str, Any]:
    safety = config.get("safety") if isinstance(config.get("safety"), dict) else {}
    return {
        "archive_loop_key_count": len(OPENEVOLVE_CONFIG_ARCHIVE_LOOP_KEYS),
        "checked_config_synced": checked_config_synced,
        "failure_count": len(failures),
        "private_qwen_enabled": _private_qwen_enabled(config),
        "program_type": config.get("program_type"),
        "publishes_private_candidates": safety.get("publishes_private_candidates"),
        "python_candidates_executed": safety.get("arbitrary_code_execution"),
        "security_claim": safety.get("security_claim"),
        "template_keys": len(DEFAULT_CONFIG_TEMPLATE),
    }
