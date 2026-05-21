import json
from pathlib import Path

import yaml

from agades_pqc_gym.integrations.private_training_config import (
    PRIVATE_TRAINING_REQUIRED_ENV_VARS,
)
from agades_pqc_gym.openevolve_adapter import (
    DEFAULT_CONFIG_TEMPLATE,
    OPENEVOLVE_CONFIG_TEMPLATE_VERIFICATION_SCHEMA,
    OPENEVOLVE_SMOKE_SCHEMA,
    OPENEVOLVE_SMOKE_VERIFICATION_SCHEMA,
    build_openevolve_smoke_report,
    verify_default_config_template,
    verify_openevolve_smoke_report,
    write_default_config_template,
    write_openevolve_smoke_report,
)


def test_default_config_template_exposes_archive_driven_private_loop() -> None:
    template = DEFAULT_CONFIG_TEMPLATE

    assert template["program_type"] == "json_attack_plan"
    assert template["private_qwen_research_engine"] == {
        "model": "Qwen3.6-27B-private",
        "model_artifact_env": "AGADES_QWEN_BASE_MODEL",
        "lora_adapter_env": "AGADES_QWEN_LORA_ADAPTER_PATH",
        "gguf_otq_5bit_env": "AGADES_QWEN_GGUF_OTQ_5BIT_PATH",
        "required_env_vars": PRIVATE_TRAINING_REQUIRED_ENV_VARS,
        "training_manifest": "docs/private_training_config_manifest.json",
        "training_readiness": "docs/private_training_readiness.json",
        "pedagogical_rl_method": "docs/pedagogical_rl_method.json",
        "dataset_curation_manifest": "docs/private_dataset_curation.json",
        "public_model_id_allowed": False,
        "consumers": ["openevolve", "deepevolve"],
        "research_roles": [
            "generate_attackplan",
            "mutate_attackplan",
            "critique_attackplan",
            "repair_attackplan",
            "draft_proof_obligations",
            "draft_family_invariants",
            "propose_evaluation_strategy",
        ],
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
                "requires_private_training_readiness": True,
                "requires_human_review_before_claim": True,
            },
        },
    }
    assert template["candidate_roots"] == [
        "benchmarks/lattice_toy_lwe/lwe_n64_q257.json",
        "benchmarks/code_based_toy_isd",
        "benchmarks/multivariate_toy_mq",
        "benchmarks/hash_based_toy_bound",
        "benchmarks/implementation_security_toy_kat",
        "benchmarks/isogeny_historical_toy_path",
    ]
    assert template["mutation_batch_schema"] == (
        "agades.pqc.candidate_mutation_batch.v1"
    )
    assert template["paper_card_injection_schema"] == (
        "agades.pqc.paper_card_injection_batch.v1"
    )
    assert template["archive_schema"] == "agades.pqc.evolution_archive.v1"
    assert template["archive_snapshot_schema"] == (
        "agades.pqc.private_archive_snapshot.v1"
    )
    assert template["private_campaign_plan_schema"] == (
        "agades.pqc.private_evolution_campaign_plan.v1"
    )
    assert (
        "agades-pqc deepevolve-injections" in template["paper_card_injection_command"]
    )
    assert (
        "--out private/candidates/paper_card_injections.json"
        in template["paper_card_injection_command"]
    )
    assert template["heldout_review_log_schema"] == ("agades.pqc.heldout_review_log.v1")
    assert template["heldout_schedule_schema"] == "agades.pqc.heldout_schedule.v1"
    assert template["heldout_schedule_run_schema"] == (
        "agades.pqc.heldout_schedule_run.v1"
    )
    assert template["heldout_cron_plan_schema"] == "agades.pqc.heldout_cron_plan.v1"
    assert template["heldout_rescore_schema"] == "agades.pqc.heldout_rescore.v1"
    assert "agades-pqc mutate-candidates" in template["local_mutation_command"]
    assert (
        "agades-pqc evolve-batch runs/candidate_mutations/plans"
        in template["local_batch_command"]
    )
    assert (
        "agades-pqc mutate-archive runs/evolution_archive.json"
        in template["archive_mutation_command"]
    )
    assert (
        "agades-pqc archive-snapshot runs/evolution_archive.json"
        in template["archive_snapshot_command"]
    )
    assert (
        "agades-pqc private-evolution-campaign-plan"
        in template["private_campaign_plan_command"]
    )
    assert (
        "--out private/runs/private_evolution_campaign/campaign_plan.json"
        in (template["private_campaign_plan_command"])
    )
    assert (
        "--review-log private/runs/heldout_review_log.json"
        in template["archive_snapshot_command"]
    )
    assert "runs/evolution_trace.jsonl" in template["archive_mutation_command"]
    assert "--max-mutations-per-elite" in template["archive_mutation_command"]
    assert (
        "agades-pqc evolve-batch runs/archive_mutations/plans"
        in template["next_generation_batch_command"]
    )
    assert (
        "agades-pqc heldout-batch runs/evolution_archive.json"
        in template["heldout_batch_command"]
    )
    assert (
        "agades-pqc heldout-schedule runs/evolution_archive.json"
        in template["heldout_schedule_command"]
    )
    assert "agades-pqc heldout-review-log" in template["heldout_review_log_command"]
    assert (
        "--review-log private/runs/heldout_review_log.json"
        in template["heldout_schedule_command"]
    )
    assert (
        "--approval private-run-policy-review" in template["heldout_schedule_command"]
    )
    assert (
        "agades-pqc heldout-run-schedule private/runs/heldout_schedule.json"
        in (template["heldout_run_schedule_command"])
    )
    assert (
        "agades-pqc heldout-cron-plan private/runs/heldout_schedule.json"
        in (template["heldout_cron_plan_command"])
    )
    assert "--trigger local_cron_after_review" in template["heldout_schedule_command"]
    assert (
        "agades-pqc rescore-archive runs/evolution_archive.json"
        in template["heldout_rescore_command"]
    )
    assert template["safety"] == {
        "arbitrary_code_execution": False,
        "publishes_private_candidates": False,
        "security_claim": False,
    }
    assert any("historical-isogeny toy rules" in note for note in template["notes"])
    assert any("paper-card injection" in note for note in template["notes"])
    assert any("private archive snapshot" in note for note in template["notes"])
    assert any("Python candidates" in note for note in template["notes"])


def test_write_default_config_template_materializes_yaml(tmp_path: Path) -> None:
    out = tmp_path / "openevolve.yaml"

    config = write_default_config_template(out)

    assert config == DEFAULT_CONFIG_TEMPLATE
    assert yaml.safe_load(out.read_text()) == DEFAULT_CONFIG_TEMPLATE


def test_openevolve_config_template_verifier_accepts_synced_config(
    tmp_path: Path,
) -> None:
    out = tmp_path / "config.yaml"
    write_default_config_template(out)

    verification = verify_default_config_template(out)

    assert (
        OPENEVOLVE_CONFIG_TEMPLATE_VERIFICATION_SCHEMA
        == "agades.pqc.openevolve_config_template_verification.v1"
    )
    assert (
        verification["schema_version"] == OPENEVOLVE_CONFIG_TEMPLATE_VERIFICATION_SCHEMA
    )
    assert verification["accepted"] is True
    assert verification["config_path"] == out.as_posix()
    assert verification["summary"] == {
        "archive_loop_key_count": 13,
        "checked_config_synced": True,
        "failure_count": 0,
        "private_qwen_enabled": True,
        "program_type": "json_attack_plan",
        "publishes_private_candidates": False,
        "python_candidates_executed": False,
        "security_claim": False,
        "template_keys": 30,
    }
    assert verification["failures"] == []


def test_openevolve_config_template_verifier_rejects_security_claim(
    tmp_path: Path,
) -> None:
    out = tmp_path / "config.yaml"
    write_default_config_template(out)
    config = yaml.safe_load(out.read_text(encoding="utf-8"))
    config["safety"]["security_claim"] = True
    out.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    verification = verify_default_config_template(out)

    assert verification["accepted"] is False
    assert verification["summary"]["security_claim"] is True
    assert (
        "OpenEvolve checked config is not in sync with DEFAULT_CONFIG_TEMPLATE."
        in verification["failures"]
    )
    assert "OpenEvolve config security_claim must be false." in verification["failures"]


def test_openevolve_config_template_verifier_rejects_public_private_qwen(
    tmp_path: Path,
) -> None:
    out = tmp_path / "config.yaml"
    write_default_config_template(out)
    config = yaml.safe_load(out.read_text(encoding="utf-8"))
    config["private_qwen_research_engine"]["tracks"]["private_serious_research"][
        "publication_allowed"
    ] = True
    out.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    verification = verify_default_config_template(out)

    assert verification["accepted"] is False
    assert verification["summary"]["private_qwen_enabled"] is True
    assert (
        "OpenEvolve private Qwen research track must not be publishable."
        in verification["failures"]
    )


def test_openevolve_config_template_verifier_rejects_incomplete_qwen_runtime_contract(
    tmp_path: Path,
) -> None:
    out = tmp_path / "config.yaml"
    write_default_config_template(out)
    config = yaml.safe_load(out.read_text(encoding="utf-8"))
    config["private_qwen_research_engine"]["required_env_vars"] = ["HF_TOKEN"]
    out.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    verification = verify_default_config_template(out)

    assert verification["accepted"] is False
    assert (
        "OpenEvolve private Qwen runtime contract is incomplete."
        in verification["failures"]
    )


def test_openevolve_smoke_report_is_importable_from_adapter_package() -> None:
    report = build_openevolve_smoke_report(
        plan_path=Path("examples/attack_plans/lattice_primal_usvp_toy.json")
    )

    assert OPENEVOLVE_SMOKE_SCHEMA == "agades.pqc.openevolve_smoke.v1"
    assert report["schema_version"] == OPENEVOLVE_SMOKE_SCHEMA
    assert report["accepted"] is True
    assert report["summary"]["primary_metric"] == "combined_score"
    assert report["summary"]["python_candidates_executed"] is False


def test_openevolve_smoke_verifier_accepts_synced_checked_report(
    tmp_path: Path,
) -> None:
    out = tmp_path / "openevolve_smoke.json"
    write_openevolve_smoke_report(out)

    verification = verify_openevolve_smoke_report(out)

    assert (
        OPENEVOLVE_SMOKE_VERIFICATION_SCHEMA
        == "agades.pqc.openevolve_smoke_verification.v1"
    )
    assert verification["schema_version"] == OPENEVOLVE_SMOKE_VERIFICATION_SCHEMA
    assert verification["accepted"] is True
    assert verification["report_path"] == out.as_posix()
    assert verification["summary"] == {
        "arbitrary_code_execution": False,
        "checked_in_report_synced": True,
        "combined_score": -80.9096,
        "evaluation_status": "ok",
        "failure_count": 0,
        "feature_attack_type": "primal_usvp",
        "feature_family": "LWE",
        "primary_metric": "combined_score",
        "python_candidates_executed": False,
        "security_claim": False,
    }
    assert verification["failures"] == []


def test_openevolve_smoke_verifier_rejects_security_claim(
    tmp_path: Path,
) -> None:
    out = tmp_path / "openevolve_smoke.json"
    write_openevolve_smoke_report(out)
    report = json.loads(out.read_text(encoding="utf-8"))
    report["safety"]["security_claim"] = True
    out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verification = verify_openevolve_smoke_report(out)

    assert verification["accepted"] is False
    assert verification["summary"]["security_claim"] is True
    assert (
        "OpenEvolve smoke report security_claim must be false."
        in verification["failures"]
    )


def test_openevolve_smoke_report_rejects_bool_primary_metric(
    tmp_path: Path,
) -> None:
    evaluator = tmp_path / "bool_score_evaluator.py"
    evaluator.write_text(
        """
def evaluate(program_path):
    return {
        "combined_score": True,
        "fitness_schema_version": "agades.pqc.fitness_report.v1",
        "evaluation_status": "ok",
        "feature_family": "LWE",
        "feature_attack_type": "primal_usvp",
        "feature_operator_count": 1,
        "feature_memory_bucket": "low",
        "feature_assumption_bucket": "standard",
        "feature_estimator_model": "mock",
        "validity_score": 1.0,
        "reproducibility_score": 1.0,
        "assumption_penalty": 0.0,
        "instability_penalty": 0.0,
    }
""",
        encoding="utf-8",
    )

    report = build_openevolve_smoke_report(
        plan_path=Path("examples/attack_plans/lattice_primal_usvp_toy.json"),
        evaluator_path=evaluator,
    )

    assert report["accepted"] is False
    assert report["summary"]["combined_score"] is True
    assert report["summary"]["failure_count"] == 1
    assert report["failures"] == [
        "OpenEvolve evaluator combined_score must be numeric."
    ]
