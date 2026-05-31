from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.huggingface_space_manifest import (
    SPACE_RUNTIME_DOC_FILES,
    _requirements_allow_injected_gradio,
    _sync_space_runtime_assets,
    build_huggingface_space_manifest,
    verify_huggingface_space_manifest,
    write_huggingface_space_manifest,
)


def test_huggingface_space_manifest_describes_public_demo_contract(
    tmp_path: Path,
) -> None:
    out = tmp_path / "space_manifest.json"

    manifest = write_huggingface_space_manifest(out)
    space_readme = Path("hf/README.md")

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
        "suggested_space_id": "agades/agades-pqc-gym-agent-env",
        "sdk": "gradio",
        "category": "agent-environment",
        "app_file": "hf/app.py",
        "space_readme_file": "hf/README.md",
        "space_readme_sha256": manifest["space"]["space_readme_sha256"],
        "space_readme_metadata": {
            "title": "Agades PQC Gym Agent Environment",
            "sdk": "gradio",
            "app_file": "app.py",
            "python_version": "3.11",
            "license": "apache-2.0",
            "colorFrom": "gray",
            "colorTo": "blue",
            "pinned": False,
            "tags": [
                "agent-environment",
                "reinforcement-learning",
                "post-quantum-cryptography",
                "cryptanalysis",
            ],
            "short_description": (
                "Public-safe AttackPlan Agent Environment for Agades PQC Gym."
            ),
        },
        "requirements_file": "hf/requirements.txt",
        "dataset_bundle": "hf/dataset",
        "hub_create_command_template": (
            "hf repo create agades/agades-pqc-gym-agent-env --repo-type=space "
            "--space_sdk gradio --private --exist-ok"
        ),
        "hub_upload_command_template": (
            "hf upload agades/agades-pqc-gym-agent-env hf . --repo-type=space "
            '--commit-message "Sync Agades PQC Gym Agent Environment"'
        ),
        "public_push_requires_review": True,
    }
    assert manifest["runtime"]["hf_spaces_injected_gradio"] == (
        "gradio[oauth,mcp]==6.14.0"
    )
    assert manifest["runtime"]["requirements_compatible_with_injected_gradio"] is True
    formal_bundle = manifest["runtime"]["formal_runtime_bundle"]
    assert formal_bundle["docs_path"] == "hf/docs"
    assert formal_bundle["docs_json_count"] >= 10
    assert formal_bundle["lean_path"] == "hf/formal/lean"
    assert formal_bundle["lean_file_count"] >= 10
    assert formal_bundle["ci_workflow_path"] == "hf/.github/workflows/ci.yml"
    assert formal_bundle["required_files_present"] is True
    assert len(formal_bundle["bundle_sha256"]) == 64
    assert len(manifest["space"]["space_readme_sha256"]) == 64
    assert space_readme.is_file()
    space_readme_text = space_readme.read_text(encoding="utf-8")
    assert "sdk: gradio" in space_readme_text
    assert "app_file: app.py" in space_readme_text
    assert "agent-environment" in space_readme_text
    assert manifest["agent_environment_contract"] == {
        "environment_class": "agades_pqc_gym.rl.environment.AgadesPQCGymEnvironment",
        "observation_schema": "agades.pqc.rl.observation.v1",
        "reward_report_schema": "agades.pqc.rl.reward_report.v1",
        "rollout_trace_schema": "agades.pqc.rl.rollout_trace.v1",
        "formal_artifact_binding_schema": ("agades.pqc.rl.formal_artifact_binding.v1"),
        "review_governance_binding_schema": (
            "agades.pqc.formal.proof_artifact.reviewer_governance_binding.v1"
        ),
        "task_dataset": "hf/dataset/task_metadata.jsonl",
        "rollout_examples": "hf/dataset/rl_rollouts.jsonl",
        "scoring_function": "agades_pqc_gym.rl.environment.score_attack_plan_candidate",
        "task_interface": "single_turn_attackplan_json",
        "reviewer_quality_requires_governance": True,
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
    assert "LWE / lattice_primal_usvp_toy_v1" in manifest["example_manifest"]["labels"]
    assert (
        "LWE / lattice_lwe_modulus_switching_primary_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "LWE / lattice_downscaled_lwe_instance_solve_n6_q23_ternary_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "MLWE / lattice_downscaled_mlwe_instance_solve_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_qc_rotation_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_bike_placeholder_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_classic_mceliece_placeholder_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_classic_mceliece_support_syndrome_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_classic_mceliece_syndrome_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_hqc_repetition_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_hqc_weighted_repetition_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_hqc_parity_check_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_hqc_circulant_syndrome_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_hqc_erasure_syndrome_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_mdpc_bit_flip_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_mdpc_black_gray_bit_flip_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
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
    assert (
        "CODE_BASED / code_based_lee_brickell_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_dumer_toy_v1" in manifest["example_manifest"]["labels"]
    )
    assert (
        "CODE_BASED / code_based_bjmm_toy_v1" in manifest["example_manifest"]["labels"]
    )
    assert (
        "HASH_BASED / hash_based_collision_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "HASH_BASED / hash_based_merkle_auth_path_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "HASH_BASED / hash_based_fors_auth_path_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "HASH_BASED / hash_based_slh_dsa_hypertree_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "HASH_BASED / hash_based_misuse_reused_salt_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "IMPLEMENTATION_SECURITY / implementation_security_acvp_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
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
    assert (
        "MULTIVARIATE / multivariate_mq_hybrid_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "MULTIVARIATE / multivariate_mq_hybrid_gf2_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "MULTIVARIATE / multivariate_mq_degree_bound_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "MULTIVARIATE / multivariate_mq_degree_bound_gf2_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "MULTIVARIATE / multivariate_minrank_rank_one_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
    assert (
        "MULTIVARIATE / multivariate_uov_public_map_toy_v1"
        in manifest["example_manifest"]["labels"]
    )
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

    assert "hf repo create agades/agades-pqc-gym-agent-env --repo-type=space" in readme
    assert "hf upload agades/agades-pqc-gym-agent-env hf . --repo-type=space" in readme
    assert "HF_TOKEN" in readme
    assert "Agent Environment" in readme
    assert "rl_rollouts.jsonl" in readme
    assert "Use a private Space first" in readme


def test_huggingface_space_requirements_allow_hf_injected_gradio(
    tmp_path: Path,
) -> None:
    compatible = tmp_path / "compatible.txt"
    incompatible = tmp_path / "incompatible.txt"
    compatible.write_text("gradio>=4,<7\n", encoding="utf-8")
    incompatible.write_text("gradio>=4,<6\n", encoding="utf-8")

    assert _requirements_allow_injected_gradio(compatible) is True
    assert _requirements_allow_injected_gradio(incompatible) is False


def test_committed_huggingface_space_manifest_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "space_manifest.json"
    committed = Path("hf/space_manifest.json")

    write_huggingface_space_manifest(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_hf_space_manifest_syncs_runtime_docs_and_lean_sources(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    for file_name in SPACE_RUNTIME_DOC_FILES:
        (tmp_path / "docs" / file_name).write_text("{}\n")
    (tmp_path / "docs" / "formal_attackplan_semantics.json").write_text(
        '{"ok": true}\n'
    )
    (tmp_path / "docs" / "reviewer_governance.json").write_text(
        json.dumps(
            {
                "schema_version": "agades.pqc.reviewer_governance.v1",
                "role_groups": {},
                "linked_artifacts": {"volatile": {"sha256": "0" * 64}},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (tmp_path / "hf" / "docs").mkdir(parents=True)
    (tmp_path / "hf" / "docs" / "stale.json").write_text("{}\n")
    (tmp_path / "formal" / "lean" / "AgadesPQC").mkdir(parents=True)
    (tmp_path / "formal" / "lean" / "AgadesPQC" / "AttackPlan.lean").write_text(
        "def synced := True\n"
    )
    (tmp_path / "formal" / "lean" / ".lake").mkdir(parents=True)
    (tmp_path / "formal" / "lean" / ".lake" / "ignored.olean").write_text("cached\n")
    (tmp_path / "hf" / "formal" / "lean").mkdir(parents=True)
    (tmp_path / "hf" / "formal" / "lean" / "stale.lean").write_text(
        "def stale := True\n"
    )

    _sync_space_runtime_assets(tmp_path)

    assert (tmp_path / "hf" / "docs" / "family_operator_catalog.json").is_file()
    assert (tmp_path / "hf" / "docs" / "family_plugin_manifest.json").is_file()
    assert (
        tmp_path / "hf" / "docs" / "formal_attackplan_semantics.json"
    ).read_text() == '{"ok": true}\n'
    synced_governance = json.loads(
        (tmp_path / "hf" / "docs" / "reviewer_governance.json").read_text()
    )
    assert "linked_artifacts" not in synced_governance
    assert not (tmp_path / "hf" / "docs" / "stale.json").exists()
    assert (
        tmp_path / "hf" / "formal" / "lean" / "AgadesPQC" / "AttackPlan.lean"
    ).read_text() == "def synced := True\n"
    assert not (tmp_path / "hf" / "formal" / "lean" / "stale.lean").exists()
    assert not (tmp_path / "hf" / "formal" / "lean" / ".lake").exists()


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
            "has_space_readme_metadata": True,
            "is_agent_environment": True,
            "labels_match_valid_dataset_rows": True,
            "public_push_requires_review": True,
            "requires_gradio_to_import_for_audit": False,
            "formal_runtime_bundle_ready": True,
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


def test_hf_space_manifest_verify_rejects_space_readme_metadata_drift(
    tmp_path: Path,
) -> None:
    out = tmp_path / "space_manifest.json"
    manifest = build_huggingface_space_manifest()
    manifest["space"]["space_readme_metadata"]["tags"] = ["post-quantum-cryptography"]
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_huggingface_space_manifest(out)

    assert result["accepted"] is False
    assert "Hugging Face Space manifest is not in sync." in result["failures"]
    assert (
        "Hugging Face Space manifest has incorrect space_readme_metadata."
        in result["failures"]
    )
    assert "Hugging Face Space root README metadata drifted." in result["failures"]
    assert (
        "Hugging Face Space root README is missing required tags: "
        "agent-environment, reinforcement-learning, cryptanalysis."
        in result["failures"]
    )


def test_hf_space_manifest_verify_rejects_empty_json_object(tmp_path: Path) -> None:
    out = tmp_path / "space_manifest.json"
    out.write_text("{}\n", encoding="utf-8")

    result = verify_huggingface_space_manifest(out)

    assert result["accepted"] is False
    assert "Hugging Face Space manifest is not in sync." in result["failures"]
    assert (
        "Hugging Face Space manifest project must be an object." in result["failures"]
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
