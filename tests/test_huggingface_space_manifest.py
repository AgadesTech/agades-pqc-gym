from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.huggingface_space_manifest import (
    build_huggingface_space_manifest,
    verify_huggingface_space_manifest,
    write_huggingface_space_manifest,
)


def test_huggingface_space_manifest_describes_public_demo_contract(
    tmp_path: Path,
) -> None:
    out = tmp_path / "space_manifest.json"

    manifest = write_huggingface_space_manifest(out)

    assert manifest == build_huggingface_space_manifest()
    assert json.loads(out.read_text(encoding="utf-8")) == manifest
    assert manifest["schema_version"] == "agades.pqc.hf_space_manifest.v1"
    assert manifest["project"] == {
        "name": "Agades PQC Gym Space",
        "package": "agades-pqc-gym",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
        "app_path": "hf/app.py",
    }
    assert manifest["space"] == {
        "suggested_space_id": "AgadesTech/agades-pqc-gym-agent-env",
        "sdk": "gradio",
        "category": "agent-environment",
        "app_file": "hf/app.py",
        "requirements_file": "hf/requirements.txt",
        "dataset_bundle": "hf/dataset",
        "hub_create_command_template": (
            "hf repos create AgadesTech/agades-pqc-gym-agent-env --type=space "
            "--space-sdk gradio --private --exist-ok"
        ),
        "hub_upload_command_template": (
            'hf upload AgadesTech/agades-pqc-gym-agent-env hf . --repo-type=space '
            '--commit-message "Sync Agades PQC Gym Agent Environment"'
        ),
        "public_push_requires_review": True,
    }
    assert manifest["agent_environment_contract"] == {
        "environment_class": "agades_pqc_gym.rl.environment.AgadesPQCGymEnvironment",
        "observation_schema": "agades.pqc.rl.observation.v1",
        "reward_report_schema": "agades.pqc.rl.reward_report.v1",
        "rollout_trace_schema": "agades.pqc.rl.rollout_trace.v1",
        "task_dataset": "hf/dataset/task_metadata.jsonl",
        "rollout_examples": "hf/dataset/rl_rollouts.jsonl",
        "scoring_function": "agades_pqc_gym.rl.environment.score_attack_plan_candidate",
        "task_interface": "single_turn_attackplan_json",
        "public_track_only": True,
        "private_trace_publication_allowed": False,
        "claims_pqc_breaks": False,
    }
    assert manifest["example_manifest"]["default_label"] == (
        "LWE / lattice_primal_usvp_toy_v1"
    )
    assert manifest["example_manifest"]["dataset_attack_plan_count"] == 80
    assert manifest["example_manifest"]["dataset_valid_attack_plan_count"] == 79
    assert manifest["example_manifest"]["dataset_invalid_attack_plan_count"] == 1
    assert manifest["example_manifest"]["example_count"] == 79
    assert manifest["example_manifest"]["excluded_attack_plan_ids"] == [
        "invalid_module_hypothesis_on_lwe_v1"
    ]
    assert manifest["example_manifest"]["labels_match_valid_dataset_rows"] is True
    assert manifest["example_manifest"]["families"] == [
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
    assert "LWE / lattice_primal_usvp_toy_v1" in manifest["example_manifest"][
        "labels"
    ]
    assert "LWE / lattice_lwe_modulus_switching_primary_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert (
        "LWE / lattice_downscaled_lwe_instance_solve_n6_q23_ternary_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "MLWE / lattice_downscaled_mlwe_instance_solve_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert "CODE_BASED / code_based_qc_rotation_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "CODE_BASED / code_based_bike_placeholder_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "CODE_BASED / code_based_classic_mceliece_placeholder_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert (
        "CODE_BASED / code_based_classic_mceliece_support_syndrome_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_classic_mceliece_syndrome_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert "CODE_BASED / code_based_hqc_repetition_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "CODE_BASED / code_based_hqc_weighted_repetition_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "CODE_BASED / code_based_hqc_parity_check_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "CODE_BASED / code_based_hqc_circulant_syndrome_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "CODE_BASED / code_based_hqc_erasure_syndrome_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "CODE_BASED / code_based_mdpc_bit_flip_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "CODE_BASED / code_based_mdpc_black_gray_bit_flip_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert (
        "CODE_BASED / code_based_mdpc_syndrome_weight_bit_flip_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "ISOGENY_HISTORICAL / isogeny_historical_commutative_walk_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "ISOGENY_HISTORICAL / isogeny_historical_volcano_walk_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert "CODE_BASED / code_based_lee_brickell_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "CODE_BASED / code_based_dumer_toy_v1" in manifest["example_manifest"][
        "labels"
    ]
    assert "CODE_BASED / code_based_bjmm_toy_v1" in manifest["example_manifest"][
        "labels"
    ]
    assert "HASH_BASED / hash_based_collision_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "HASH_BASED / hash_based_merkle_auth_path_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "HASH_BASED / hash_based_fors_auth_path_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "HASH_BASED / hash_based_slh_dsa_hypertree_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "HASH_BASED / hash_based_misuse_reused_salt_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "IMPLEMENTATION_SECURITY / implementation_security_acvp_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert (
        "IMPLEMENTATION_SECURITY / implementation_security_mldsa_kat_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "IMPLEMENTATION_SECURITY / implementation_security_mldsa_acvp_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "IMPLEMENTATION_SECURITY / implementation_security_benchmark_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "IMPLEMENTATION_SECURITY / implementation_security_binary_size_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "IMPLEMENTATION_SECURITY / implementation_security_memory_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "IMPLEMENTATION_SECURITY / implementation_security_stack_usage_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "IMPLEMENTATION_SECURITY / implementation_security_nist_acvp_schema_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "IMPLEMENTATION_SECURITY / implementation_security_dudect_schema_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "IMPLEMENTATION_SECURITY / implementation_security_ctgrind_schema_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "IMPLEMENTATION_SECURITY / implementation_security_timecop_schema_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert "MULTIVARIATE / multivariate_mq_hybrid_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "MULTIVARIATE / multivariate_mq_hybrid_gf2_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "MULTIVARIATE / multivariate_mq_degree_bound_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "MULTIVARIATE / multivariate_mq_degree_bound_gf2_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "MULTIVARIATE / multivariate_minrank_rank_one_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert "MULTIVARIATE / multivariate_uov_public_map_toy_v1" in manifest[
        "example_manifest"
    ]["labels"]
    assert manifest["verifier_contract"] == {
        "verifier_schema": "agades.pqc.verifier.v1",
        "uses_shared_verifier": True,
        "accepts_arbitrary_code": False,
        "accepts_live_targets": False,
        "output_security_claim": False,
        "summary_must_include": "not a security claim",
    }
    assert manifest["safety"] == {
        "contains_private_traces": False,
        "arbitrary_code_execution": False,
        "live_targeting": False,
        "security_claim": False,
        "publishes_private_candidates": False,
    }
    assert manifest["release_gates"] == [
        "uv run pytest tests/test_huggingface_space_manifest.py -q",
        "uv run agades-pqc hf-dataset --out hf/dataset",
        "uv run agades-pqc hf-dataset-verify --dataset hf/dataset",
        "uv run agades-pqc hf-space-manifest --out hf/space_manifest.json",
        "uv run agades-pqc hf-space-manifest-verify --manifest hf/space_manifest.json",
        "uv run agades-pqc hf-space-smoke --out reports/hf_space_smoke.json",
        "uv run agades-pqc hf-space-smoke-verify --report reports/hf_space_smoke.json",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]


def test_huggingface_space_readme_matches_hub_workflow_contract() -> None:
    readme = Path("hf/space_README.md").read_text(encoding="utf-8")

    assert "hf repos create AgadesTech/agades-pqc-gym-agent-env --type=space" in readme
    assert (
        "hf upload AgadesTech/agades-pqc-gym-agent-env hf . --repo-type=space"
        in readme
    )
    assert "HF_TOKEN" in readme
    assert "Agent Environment" in readme
    assert "rl_rollouts.jsonl" in readme
    assert "Use a private Space first" in readme


def test_committed_huggingface_space_manifest_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "space_manifest.json"
    committed = Path("hf/space_manifest.json")

    write_huggingface_space_manifest(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_hf_space_manifest_verify_accepts_committed_manifest() -> None:
    result = verify_huggingface_space_manifest(Path("hf/space_manifest.json"))

    assert result == {
        "schema_version": "agades.pqc.hf_space_manifest_verification.v1",
        "manifest_path": "hf/space_manifest.json",
        "accepted": True,
        "summary": {
            "dataset_attack_plan_count": 80,
            "dataset_invalid_attack_plan_count": 1,
            "dataset_valid_attack_plan_count": 79,
            "default_label": "LWE / lattice_primal_usvp_toy_v1",
            "example_count": 79,
            "failure_count": 0,
            "is_agent_environment": True,
            "labels_match_valid_dataset_rows": True,
            "public_push_requires_review": True,
            "requires_gradio_to_import_for_audit": False,
            "uses_shared_verifier": True,
        },
        "failures": [],
    }


def test_hf_space_manifest_verify_rejects_arbitrary_code_flag(
    tmp_path: Path,
) -> None:
    out = tmp_path / "space_manifest.json"
    manifest = build_huggingface_space_manifest()
    manifest["verifier_contract"]["accepts_arbitrary_code"] = True
    manifest["safety"]["arbitrary_code_execution"] = True
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_huggingface_space_manifest(out)

    assert result["accepted"] is False
    assert "Hugging Face Space manifest is not in sync." in result["failures"]
    assert "Hugging Face Space manifest allows arbitrary code." in result["failures"]
    assert (
        "Hugging Face Space manifest advertises arbitrary execution."
        in result["failures"]
    )


def test_hf_space_manifest_verify_rejects_empty_json_object(tmp_path: Path) -> None:
    out = tmp_path / "space_manifest.json"
    out.write_text("{}\n", encoding="utf-8")

    result = verify_huggingface_space_manifest(out)

    assert result["accepted"] is False
    assert "Hugging Face Space manifest is not in sync." in result["failures"]
    assert (
        "Hugging Face Space manifest project must be an object."
        in result["failures"]
    )


def test_hf_space_manifest_cli_writes_manifest(tmp_path: Path) -> None:
    out = tmp_path / "space_manifest.json"

    result = CliRunner().invoke(app, ["hf-space-manifest", "--out", str(out)])

    assert result.exit_code == 0
    assert f"hf_space_manifest={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["schema_version"] == (
        "agades.pqc.hf_space_manifest.v1"
    )


def test_hf_space_manifest_verify_cli_accepts_current_manifest() -> None:
    result = CliRunner().invoke(
        app,
        ["hf-space-manifest-verify", "--manifest", "hf/space_manifest.json"],
    )

    assert result.exit_code == 0
    assert "agades.pqc.hf_space_manifest_verification.v1" in result.output
    assert '"accepted": true' in result.output
