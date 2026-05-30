from __future__ import annotations

import hashlib
import json
from pathlib import Path

from expected_task_metadata_summary import EXPECTED_TASK_METADATA_SUMMARY
from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.huggingface_dataset import (
    verify_huggingface_dataset_bundle,
    write_huggingface_dataset_bundle,
)
from agades_pqc_gym.integrations.task_metadata import TASK_METADATA_SCHEMA


def test_huggingface_dataset_bundle_contains_public_examples_and_outputs(
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "hf_dataset"

    bundle = write_huggingface_dataset_bundle(out_dir)

    assert bundle["out_dir"] == out_dir
    assert (out_dir / "README.md").exists()
    assert (out_dir / "dataset_info.json").exists()
    assert (out_dir / "attack_plans.jsonl").exists()
    assert (out_dir / "task_metadata.jsonl").exists()
    assert (out_dir / "verifier_outputs.jsonl").exists()
    assert (out_dir / "rl_rollouts.jsonl").exists()
    info = json.loads((out_dir / "dataset_info.json").read_text())
    expected_public_runs = [
        "code_based_toy_classic_mceliece_v0",
        "code_based_toy_hqc_v0",
        "code_based_toy_isd_v0",
        "code_based_toy_mdpc_v0",
        "hash_based_toy_bound_v0",
        "hash_based_toy_misuse_v0",
        "hash_based_toy_signature_v0",
        "implementation_security_toy_benchmark_v0",
        "implementation_security_toy_kat_v0",
        "implementation_security_toy_timing_v0",
        "isogeny_historical_toy_path_v0",
        "lattice_downscaled_lwe_instance_solve_v0",
        "lattice_downscaled_mlwe_instance_solve_v0",
        "lattice_mlwe_downscaled_v0",
        "lattice_toy_lwe_v0",
        "multivariate_toy_minrank_v0",
        "multivariate_toy_mq_v0",
        "multivariate_toy_uov_v0",
    ]
    assert info["public_run_bundles"] == expected_public_runs
    for public_run in expected_public_runs:
        assert (out_dir / "public_runs" / public_run / "run_ledger.json").exists()
        assert (out_dir / "public_runs" / public_run / "MANIFEST.sha256").exists()
    assert (out_dir / "MANIFEST.sha256").exists()

    assert info["schema_version"] == "agades.pqc.hf_dataset.v1"
    assert info["dataset_name"] == "agades/pqc-gym-toy"
    assert info["task_metadata_schema"] == TASK_METADATA_SCHEMA
    assert info["attack_plan_count"] == 80
    assert info["valid_attack_plan_count"] == 79
    assert info["invalid_attack_plan_count"] == 1
    assert info["rl_rollout_count"] == 9
    assert info["task_metadata_count"] == 79
    assert info["prime_task_eligible_count"] == 79
    assert info["task_metadata_summary"] == EXPECTED_TASK_METADATA_SUMMARY
    assert info["invalid_attack_plan_ids"] == ["invalid_module_hypothesis_on_lwe_v1"]
    assert info["safety"]["contains_private_traces"] is False
    assert info["safety"]["arbitrary_code_execution"] is False
    assert info["release_gates"] == [
        "uv run pytest tests/test_huggingface_dataset_bundle.py -q",
        "uv run agades-pqc hf-dataset --out hf/dataset",
        "uv run agades-pqc hf-dataset-verify --dataset hf/dataset",
        "uv run agades-pqc hf-space-manifest-verify --manifest "
        "hf/space_manifest.json",
        "uv run agades-pqc hf-collection-manifest-verify --manifest "
        "hf/collection_manifest.json",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]

    attack_plan_rows = _read_jsonl(out_dir / "attack_plans.jsonl")
    assert len(attack_plan_rows) == 80
    assert attack_plan_rows[0]["source_path"] == (
        "examples/attack_plans/code_based_bike_placeholder.json"
    )
    assert attack_plan_rows[1]["source_path"] == (
        "examples/attack_plans/code_based_bjmm_toy.json"
    )
    assert attack_plan_rows[2]["source_path"] == (
        "examples/attack_plans/code_based_classic_mceliece_placeholder.json"
    )
    assert attack_plan_rows[3]["source_path"] == (
        "examples/attack_plans/"
        "code_based_classic_mceliece_support_syndrome_toy.json"
    )
    assert {row["target_family"] for row in attack_plan_rows} >= {
        "LWE",
        "MLWE",
        "NTRU",
        "SIS",
        "CODE_BASED",
        "MULTIVARIATE",
        "HASH_BASED",
        "ISOGENY_HISTORICAL",
        "IMPLEMENTATION_SECURITY",
    }
    assert all(row["public_example"] is True for row in attack_plan_rows)
    assert all("raw_json_sha256" in row for row in attack_plan_rows)
    public_valid_rows = [
        row
        for row in attack_plan_rows
        if row["attack_plan_id"] != "invalid_module_hypothesis_on_lwe_v1"
    ]
    assert all(row["task_metadata"] for row in public_valid_rows)
    task_metadata_rows = _read_jsonl(out_dir / "task_metadata.jsonl")
    assert task_metadata_rows == [row["task_metadata"] for row in public_valid_rows]
    assert len(task_metadata_rows) == info["task_metadata_count"]
    assert all(
        row["schema_version"] == TASK_METADATA_SCHEMA for row in task_metadata_rows
    )
    lattice_metadata = next(
        row["task_metadata"]
        for row in attack_plan_rows
        if row["attack_plan_id"] == "lattice_primal_usvp_toy_v1"
    )
    assert lattice_metadata["schema_version"] == TASK_METADATA_SCHEMA
    assert lattice_metadata["seed_attack_plan_sha256"] == next(
        row["raw_json_sha256"]
        for row in attack_plan_rows
        if row["attack_plan_id"] == "lattice_primal_usvp_toy_v1"
    )
    assert lattice_metadata["target_name"] == "toy_lwe_n64_q257"
    assert lattice_metadata["operator_types"] == ["primal_usvp"]
    assert lattice_metadata["seed_accepted"] is True
    assert lattice_metadata["seed_evaluation_status"] == "ok"
    assert lattice_metadata["seed_reward"] == 1.0
    unsupported_metadata = next(
        row["task_metadata"]
        for row in attack_plan_rows
        if row["attack_plan_id"] == "code_based_bike_placeholder_v1"
    )
    assert unsupported_metadata["seed_accepted"] is False
    assert unsupported_metadata["seed_evaluation_status"] == "unsupported"
    assert unsupported_metadata["seed_reward"] == 0.0
    implementation_security_source_contracts = {
        row["attack_plan_id"]: row["task_metadata"]
        for row in attack_plan_rows
        if row["attack_plan_id"]
        in {
            "implementation_security_dudect_schema_v1",
            "implementation_security_ctgrind_schema_v1",
            "implementation_security_timecop_schema_v1",
        }
    }
    assert set(implementation_security_source_contracts) == {
        "implementation_security_dudect_schema_v1",
        "implementation_security_ctgrind_schema_v1",
        "implementation_security_timecop_schema_v1",
    }
    for metadata in implementation_security_source_contracts.values():
        assert metadata["target_family"] == "IMPLEMENTATION_SECURITY"
        assert metadata["support_level"] == "schema_only"
        assert metadata["operator_types"] == ["constant_time_check"]
        assert metadata["requires_reproducibility"] is False
        assert metadata["seed_accepted"] is False
        assert metadata["seed_evaluation_status"] == "unsupported"
        assert metadata["seed_reward"] == 0.0
    dudect_summary_metadata = next(
        row["task_metadata"]
        for row in attack_plan_rows
        if row["attack_plan_id"] == "implementation_security_dudect_summary_toy_v1"
    )
    assert dudect_summary_metadata["target_name"] == "toy_dudect_mlkem_summary"
    assert dudect_summary_metadata["operator_types"] == ["constant_time_check"]
    assert dudect_summary_metadata["requires_reproducibility"] is True
    assert dudect_summary_metadata["seed_accepted"] is True
    assert dudect_summary_metadata["seed_evaluation_status"] == "ok"
    assert dudect_summary_metadata["seed_reward"] == 1.0
    nist_acvp_schema_metadata = next(
        row["task_metadata"]
        for row in attack_plan_rows
        if row["attack_plan_id"] == "implementation_security_nist_acvp_schema_v1"
    )
    assert nist_acvp_schema_metadata["target_name"] == "nist_acvp_pqc_vectors_schema"
    assert nist_acvp_schema_metadata["operator_types"] == ["kat_conformance"]
    assert nist_acvp_schema_metadata["support_level"] == "schema_only"
    assert nist_acvp_schema_metadata["seed_accepted"] is False
    assert nist_acvp_schema_metadata["seed_evaluation_status"] == "unsupported"
    assert nist_acvp_schema_metadata["seed_reward"] == 0.0
    lattice_runtime_boundary_metadata = next(
        row["task_metadata"]
        for row in attack_plan_rows
        if row["attack_plan_id"] == "lattice_lwe_modulus_switching_primary_v1"
    )
    assert lattice_runtime_boundary_metadata["target_name"] == (
        "toy_lwe_modulus_switching_primary_boundary"
    )
    assert lattice_runtime_boundary_metadata["operator_types"] == [
        "modulus_switching"
    ]
    assert lattice_runtime_boundary_metadata["seed_accepted"] is False
    assert lattice_runtime_boundary_metadata["seed_evaluation_status"] == (
        "unsupported"
    )
    assert lattice_runtime_boundary_metadata["seed_reward"] == 0.0
    weighted_hqc_metadata = next(
        row["task_metadata"]
        for row in attack_plan_rows
        if row["attack_plan_id"] == "code_based_hqc_weighted_repetition_toy_v1"
    )
    assert weighted_hqc_metadata["target_name"] == (
        "toy_hqc_weighted_repetition_25_5_w4"
    )
    assert weighted_hqc_metadata["seed_accepted"] is True
    uov_metadata = next(
        row["task_metadata"]
        for row in attack_plan_rows
        if row["attack_plan_id"] == "multivariate_uov_public_map_toy_v1"
    )
    assert uov_metadata["target_name"] == "toy_uov_public_map_gf2_v5_e3"
    assert uov_metadata["operator_types"] == ["signature_fixture_check"]
    assert uov_metadata["seed_accepted"] is True
    minrank_rank_two_metadata = next(
        row["task_metadata"]
        for row in attack_plan_rows
        if row["attack_plan_id"] == "multivariate_minrank_rank_two_toy_v1"
    )
    assert minrank_rank_two_metadata["target_name"] == "toy_minrank_gf2_m4_r2"
    assert minrank_rank_two_metadata["operator_types"] == ["minrank_attack"]
    assert minrank_rank_two_metadata["seed_accepted"] is True
    assert minrank_rank_two_metadata["seed_evaluation_status"] == "ok"
    assert minrank_rank_two_metadata["seed_reward"] == 1.0
    mayo_schema_metadata = next(
        row["task_metadata"]
        for row in attack_plan_rows
        if row["attack_plan_id"] == "multivariate_mayo_schema_placeholder_v1"
    )
    assert mayo_schema_metadata["target_name"] == "mayo_like_toy_schema"
    assert mayo_schema_metadata["operator_types"] == ["groebner_basis"]
    assert mayo_schema_metadata["seed_accepted"] is False
    assert mayo_schema_metadata["seed_evaluation_status"] == "unsupported"
    assert mayo_schema_metadata["seed_reward"] == 0.0
    rainbow_schema_metadata = next(
        row["task_metadata"]
        for row in attack_plan_rows
        if row["attack_plan_id"]
        == "multivariate_rainbow_historical_schema_placeholder_v1"
    )
    assert rainbow_schema_metadata["target_name"] == (
        "rainbow_historical_toy_schema"
    )
    assert rainbow_schema_metadata["operator_types"] == ["signature_fixture_check"]
    assert rainbow_schema_metadata["seed_accepted"] is False
    assert rainbow_schema_metadata["seed_evaluation_status"] == "unsupported"
    assert rainbow_schema_metadata["seed_reward"] == 0.0
    volcano_metadata = next(
        row["task_metadata"]
        for row in attack_plan_rows
        if row["attack_plan_id"] == "isogeny_historical_volcano_walk_toy_v1"
    )
    assert volcano_metadata["target_name"] == "toy_volcano_walk_reconstruction"
    assert volcano_metadata["operator_types"] == [
        "historical_isogeny_reconstruction"
    ]
    assert volcano_metadata["seed_accepted"] is True
    assert volcano_metadata["seed_evaluation_status"] == "ok"
    assert volcano_metadata["seed_reward"] == 1.0

    verifier_rows = _read_jsonl(out_dir / "verifier_outputs.jsonl")
    assert len(verifier_rows) == len(attack_plan_rows)
    by_id = {row["attack_plan_id"]: row for row in verifier_rows}
    assert by_id["lattice_bkw_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["lattice_bdd_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["lattice_ntru_schema_placeholder_v1"]["evaluation_status"] == (
        "unsupported"
    )
    assert by_id["lattice_ntru_schema_placeholder_v1"]["verifier_result"][
        "estimator"
    ]["name"] == "lattice-family-router"
    assert by_id["lattice_sis_schema_placeholder_v1"]["evaluation_status"] == (
        "unsupported"
    )
    assert by_id["lattice_sis_schema_placeholder_v1"]["verifier_result"][
        "estimator"
    ]["name"] == "lattice-family-router"
    assert by_id["lattice_lwe_modulus_switching_primary_v1"][
        "evaluation_status"
    ] == "unsupported"
    assert by_id["lattice_lwe_modulus_switching_primary_v1"]["verifier_result"][
        "estimated_time_bits"
    ] is None
    assert by_id["lattice_lwe_modulus_switching_primary_v1"]["verifier_result"][
        "estimated_memory_bits"
    ] is None
    assert by_id["lattice_lwe_modulus_switching_primary_v1"]["verifier_result"][
        "estimator"
    ]["name"] == "lattice-family-router"
    for attack_plan_id in [
        "code_based_bike_placeholder_v1",
        "code_based_classic_mceliece_placeholder_v1",
    ]:
        row = by_id[attack_plan_id]
        assert row["evaluation_status"] == "unsupported"
        assert row["verifier_result"]["estimated_time_bits"] is None
        assert row["verifier_result"]["estimated_memory_bits"] is None
        assert row["verifier_result"]["estimator"]["name"] == (
            "code-based-placeholder-estimator"
        )
    assert by_id["code_based_prange_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["code_based_prange_toy_v1"]["verifier_result"]["estimator"][
        "name"
    ] == "toy-code-based-isd-estimator"
    assert by_id["code_based_prange_toy_n15_v1"]["evaluation_status"] == "ok"
    assert by_id["code_based_prange_toy_n15_v1"]["verifier_result"][
        "reproduction"
    ]["status"] == "instance_solved"
    assert by_id["code_based_prange_toy_n15_v1"]["verifier_result"][
        "reproduction"
    ]["score"] == 0.4
    assert by_id["code_based_stern_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["code_based_stern_toy_v1"]["verifier_result"]["features"][
        "attack_type"
    ] == "information_set_decoding:stern_toy"
    assert by_id["code_based_stern_toy_v1"]["verifier_result"]["estimator"][
        "name"
    ] == "toy-code-based-isd-estimator"
    assert by_id["code_based_dumer_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["code_based_dumer_toy_v1"]["verifier_result"]["features"][
        "attack_type"
    ] == "information_set_decoding:dumer_toy"
    assert by_id["code_based_dumer_toy_v1"]["verifier_result"]["estimator"][
        "name"
    ] == "toy-code-based-isd-estimator"
    assert by_id["code_based_bjmm_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["code_based_bjmm_toy_v1"]["verifier_result"]["features"][
        "attack_type"
    ] == "information_set_decoding:bjmm_toy"
    assert by_id["code_based_bjmm_toy_v1"]["verifier_result"]["estimator"][
        "name"
    ] == "toy-code-based-isd-estimator"
    assert by_id["code_based_lee_brickell_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["code_based_lee_brickell_toy_v1"]["verifier_result"]["features"][
        "attack_type"
    ] == "information_set_decoding:lee_brickell_toy"
    assert by_id["code_based_lee_brickell_toy_v1"]["verifier_result"][
        "estimator"
    ]["name"] == "toy-code-based-isd-estimator"
    assert by_id["code_based_qc_rotation_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["code_based_qc_rotation_toy_v1"]["verifier_result"]["features"][
        "attack_type"
    ] == "information_set_decoding:qc_rotation_toy"
    qc_reproduction = by_id["code_based_qc_rotation_toy_v1"]["verifier_result"][
        "reproduction"
    ]
    assert qc_reproduction["status"] == "instance_solved"
    assert qc_reproduction["score"] == 0.4
    assert by_id["code_based_hqc_repetition_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["code_based_hqc_repetition_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "decoding_fixture_check:hqc_repetition_toy"
    assert by_id["code_based_hqc_repetition_toy_v1"]["verifier_result"][
        "estimator"
    ]["name"] == "toy-code-based-repetition-decoder-estimator"
    hqc_reproduction = by_id["code_based_hqc_repetition_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert hqc_reproduction["status"] == "instance_solved"
    assert hqc_reproduction["score"] == 0.4
    assert by_id["code_based_hqc_parity_check_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["code_based_hqc_parity_check_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "decoding_fixture_check:hqc_parity_check_toy"
    assert by_id["code_based_hqc_parity_check_toy_v1"]["verifier_result"][
        "estimator"
    ]["name"] == "toy-code-based-parity-check-decoder-estimator"
    hqc_parity_reproduction = by_id["code_based_hqc_parity_check_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert hqc_parity_reproduction["status"] == "instance_solved"
    assert hqc_parity_reproduction["score"] == 0.4
    assert by_id["code_based_hqc_circulant_syndrome_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["code_based_hqc_circulant_syndrome_toy_v1"][
        "verifier_result"
    ]["features"]["attack_type"] == (
        "decoding_fixture_check:hqc_circulant_syndrome_toy"
    )
    assert by_id["code_based_hqc_circulant_syndrome_toy_v1"][
        "verifier_result"
    ]["estimator"]["name"] == (
        "toy-code-based-circulant-syndrome-decoder-estimator"
    )
    hqc_circulant_reproduction = by_id[
        "code_based_hqc_circulant_syndrome_toy_v1"
    ]["verifier_result"]["reproduction"]
    assert hqc_circulant_reproduction["status"] == "instance_solved"
    assert hqc_circulant_reproduction["score"] == 0.4
    assert by_id["code_based_hqc_circulant_erasure_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["code_based_hqc_circulant_erasure_toy_v1"][
        "verifier_result"
    ]["features"]["attack_type"] == (
        "decoding_fixture_check:hqc_circulant_erasure_toy"
    )
    assert by_id["code_based_hqc_circulant_erasure_toy_v1"][
        "verifier_result"
    ]["estimator"]["name"] == (
        "toy-code-based-circulant-erasure-decoder-estimator"
    )
    hqc_circulant_erasure_reproduction = by_id[
        "code_based_hqc_circulant_erasure_toy_v1"
    ]["verifier_result"]["reproduction"]
    assert hqc_circulant_erasure_reproduction["status"] == "instance_solved"
    assert hqc_circulant_erasure_reproduction["score"] == 0.4
    assert by_id["code_based_hqc_erasure_syndrome_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["code_based_hqc_erasure_syndrome_toy_v1"][
        "verifier_result"
    ]["features"]["attack_type"] == (
        "decoding_fixture_check:hqc_erasure_syndrome_toy"
    )
    assert by_id["code_based_hqc_erasure_syndrome_toy_v1"][
        "verifier_result"
    ]["estimator"]["name"] == (
        "toy-code-based-erasure-syndrome-decoder-estimator"
    )
    hqc_erasure_reproduction = by_id["code_based_hqc_erasure_syndrome_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert hqc_erasure_reproduction["status"] == "instance_solved"
    assert hqc_erasure_reproduction["score"] == 0.4
    assert by_id["code_based_mdpc_bit_flip_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["code_based_mdpc_bit_flip_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "decoding_fixture_check:mdpc_bit_flip_toy"
    assert by_id["code_based_mdpc_bit_flip_toy_v1"]["verifier_result"][
        "estimator"
    ]["name"] == "toy-code-based-bit-flip-decoder-estimator"
    mdpc_reproduction = by_id["code_based_mdpc_bit_flip_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert mdpc_reproduction["status"] == "instance_solved"
    assert mdpc_reproduction["score"] == 0.4
    assert by_id["code_based_mdpc_black_gray_bit_flip_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["code_based_mdpc_black_gray_bit_flip_toy_v1"][
        "verifier_result"
    ]["features"]["attack_type"] == (
        "decoding_fixture_check:mdpc_black_gray_bit_flip_toy"
    )
    assert by_id["code_based_mdpc_black_gray_bit_flip_toy_v1"][
        "verifier_result"
    ]["estimator"]["name"] == "toy-code-based-bit-flip-decoder-estimator"
    mdpc_black_gray_reproduction = by_id[
        "code_based_mdpc_black_gray_bit_flip_toy_v1"
    ]["verifier_result"]["reproduction"]
    assert mdpc_black_gray_reproduction["status"] == "instance_solved"
    assert mdpc_black_gray_reproduction["score"] == 0.4
    assert by_id["code_based_mdpc_syndrome_weight_bit_flip_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["code_based_mdpc_syndrome_weight_bit_flip_toy_v1"][
        "verifier_result"
    ]["features"]["attack_type"] == (
        "decoding_fixture_check:mdpc_syndrome_weight_bit_flip_toy"
    )
    assert by_id["code_based_mdpc_syndrome_weight_bit_flip_toy_v1"][
        "verifier_result"
    ]["estimator"]["name"] == "toy-code-based-bit-flip-decoder-estimator"
    mdpc_syndrome_weight_reproduction = by_id[
        "code_based_mdpc_syndrome_weight_bit_flip_toy_v1"
    ]["verifier_result"]["reproduction"]
    assert mdpc_syndrome_weight_reproduction["status"] == "instance_solved"
    assert mdpc_syndrome_weight_reproduction["score"] == 0.4
    assert by_id["code_based_classic_mceliece_syndrome_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["code_based_classic_mceliece_syndrome_toy_v1"][
        "verifier_result"
    ]["features"]["attack_type"] == (
        "decoding_fixture_check:classic_mceliece_syndrome_toy"
    )
    assert by_id["code_based_classic_mceliece_syndrome_toy_v1"][
        "verifier_result"
    ]["estimator"]["name"] == (
        "toy-code-based-classic-mceliece-syndrome-estimator"
    )
    classic_reproduction = by_id["code_based_classic_mceliece_syndrome_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert classic_reproduction["status"] == "instance_solved"
    assert classic_reproduction["score"] == 0.4
    assert by_id["code_based_classic_mceliece_support_syndrome_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["code_based_classic_mceliece_support_syndrome_toy_v1"][
        "verifier_result"
    ]["features"]["attack_type"] == (
        "decoding_fixture_check:classic_mceliece_support_syndrome_toy"
    )
    assert by_id["code_based_classic_mceliece_support_syndrome_toy_v1"][
        "verifier_result"
    ]["estimator"]["name"] == (
        "toy-code-based-classic-mceliece-support-syndrome-estimator"
    )
    classic_support_reproduction = by_id[
        "code_based_classic_mceliece_support_syndrome_toy_v1"
    ]["verifier_result"]["reproduction"]
    assert classic_support_reproduction["status"] == "instance_solved"
    assert classic_support_reproduction["score"] == 0.4
    assert by_id["multivariate_uov_public_map_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["multivariate_uov_public_map_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "signature_fixture_check:toy_uov_public_map_verify"
    assert by_id["multivariate_uov_public_map_toy_v1"]["verifier_result"][
        "estimator"
    ]["name"] == "toy-multivariate-estimator"
    uov_reproduction = by_id["multivariate_uov_public_map_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert uov_reproduction["status"] == "instance_solved"
    assert uov_reproduction["score"] == 0.4
    assert by_id["hash_based_preimage_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["hash_based_preimage_toy_v1"]["verifier_result"]["estimator"][
        "name"
    ] == "toy-hash-bound-estimator"
    assert by_id["hash_based_collision_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["hash_based_collision_toy_v1"]["verifier_result"]["features"][
        "attack_type"
    ] == "security_bound_check:toy_collision_bound"
    assert by_id["hash_based_collision_toy_v1"]["verifier_result"][
        "estimated_time_bits"
    ] == 16.0
    collision_reproduction = by_id["hash_based_collision_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert collision_reproduction["status"] == "instance_solved"
    assert collision_reproduction["score"] == 0.4
    assert by_id["hash_based_signature_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["hash_based_signature_toy_v1"]["verifier_result"]["features"][
        "attack_type"
    ] == "hash_signature_verification:toy_wots_chain_verify"
    signature_reproduction = by_id["hash_based_signature_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert signature_reproduction["status"] == "instance_solved"
    assert signature_reproduction["score"] == 0.4
    assert by_id["hash_based_merkle_auth_path_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["hash_based_merkle_auth_path_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "hash_signature_verification:toy_merkle_auth_path_verify"
    merkle_reproduction = by_id["hash_based_merkle_auth_path_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert merkle_reproduction["status"] == "instance_solved"
    assert merkle_reproduction["score"] == 0.4
    assert by_id["hash_based_fors_auth_path_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["hash_based_fors_auth_path_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "hash_signature_verification:toy_fors_auth_path_verify"
    fors_reproduction = by_id["hash_based_fors_auth_path_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert fors_reproduction["status"] == "instance_solved"
    assert fors_reproduction["score"] == 0.4
    assert by_id["hash_based_slh_dsa_hypertree_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["hash_based_slh_dsa_hypertree_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "hash_signature_verification:toy_slh_dsa_hypertree_verify"
    slh_dsa_reproduction = by_id["hash_based_slh_dsa_hypertree_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert slh_dsa_reproduction["status"] == "instance_solved"
    assert slh_dsa_reproduction["score"] == 0.4
    assert by_id["hash_based_misuse_reused_salt_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["hash_based_misuse_reused_salt_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "misuse_check:toy_hash_reused_salt"
    misuse_reproduction = by_id["hash_based_misuse_reused_salt_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert misuse_reproduction["status"] == "instance_solved"
    assert misuse_reproduction["score"] == 0.4
    assert by_id["multivariate_mq_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["multivariate_mq_toy_v1"]["verifier_result"]["estimator"][
        "name"
    ] == "toy-multivariate-estimator"
    assert by_id["multivariate_mq_hybrid_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["multivariate_mq_hybrid_toy_v1"]["verifier_result"]["features"][
        "attack_type"
    ] == "groebner_basis:toy_mq_hybrid_search"
    assert by_id["multivariate_mq_hybrid_toy_v1"]["verifier_result"]["estimator"][
        "name"
    ] == "toy-multivariate-estimator"
    assert by_id["multivariate_mq_degree_bound_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["multivariate_mq_degree_bound_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "groebner_basis:toy_mq_degree_bound"
    assert by_id["multivariate_mq_degree_bound_toy_v1"]["verifier_result"][
        "estimator"
    ]["name"] == "toy-multivariate-estimator"
    assert by_id["multivariate_mq_degree_bound_gf2_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["multivariate_mq_degree_bound_gf2_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "groebner_basis:toy_mq_degree_bound"
    mq_degree_gf2_solution = by_id["multivariate_mq_degree_bound_gf2_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert mq_degree_gf2_solution["status"] == "instance_solved"
    assert mq_degree_gf2_solution["score"] == 0.4
    assert by_id["multivariate_mq_hybrid_gf2_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["multivariate_mq_hybrid_gf2_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "groebner_basis:toy_mq_hybrid_search"
    mq_hybrid_gf2_solution = by_id["multivariate_mq_hybrid_gf2_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert mq_hybrid_gf2_solution["status"] == "instance_solved"
    assert mq_hybrid_gf2_solution["score"] == 0.4
    assert by_id["multivariate_minrank_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["multivariate_minrank_toy_v1"]["verifier_result"]["features"][
        "attack_type"
    ] == "minrank_attack:toy_minrank_search"
    minrank_solution = by_id["multivariate_minrank_toy_v1"]["verifier_result"][
        "reproduction"
    ]
    assert minrank_solution["status"] == "instance_solved"
    assert minrank_solution["score"] == 0.4
    assert by_id["multivariate_minrank_rank_one_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["multivariate_minrank_rank_one_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "minrank_attack:toy_minrank_search"
    minrank_rank_one_solution = by_id["multivariate_minrank_rank_one_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert minrank_rank_one_solution["status"] == "instance_solved"
    assert minrank_rank_one_solution["score"] == 0.4
    assert by_id["implementation_security_kat_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["implementation_security_kat_toy_v1"]["verifier_result"][
        "estimator"
    ]["name"] == "toy-implementation-security-estimator"
    assert by_id["implementation_security_mldsa_kat_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["implementation_security_mldsa_kat_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "kat_conformance:toy_kat_digest_match"
    mldsa_kat_reproduction = by_id["implementation_security_mldsa_kat_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert mldsa_kat_reproduction["status"] == "instance_solved"
    assert mldsa_kat_reproduction["score"] == 0.4
    assert by_id["implementation_security_mldsa_acvp_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["implementation_security_mldsa_acvp_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "kat_conformance:toy_acvp_vector_set_match"
    mldsa_acvp_reproduction = by_id["implementation_security_mldsa_acvp_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert mldsa_acvp_reproduction["status"] == "instance_solved"
    assert mldsa_acvp_reproduction["score"] == 0.4
    assert by_id["implementation_security_acvp_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["implementation_security_acvp_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "kat_conformance:toy_acvp_vector_set_match"
    acvp_reproduction = by_id["implementation_security_acvp_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert acvp_reproduction["status"] == "instance_solved"
    assert acvp_reproduction["score"] == 0.4
    assert by_id["implementation_security_timing_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["implementation_security_timing_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "constant_time_check:toy_timing_welch_t_check"
    timing_reproduction = by_id["implementation_security_timing_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert timing_reproduction["status"] == "instance_solved"
    assert timing_reproduction["score"] == 0.4
    assert by_id["implementation_security_benchmark_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["implementation_security_benchmark_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "benchmark_harness:toy_benchmark_summary_check"
    benchmark_reproduction = by_id["implementation_security_benchmark_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert benchmark_reproduction["status"] == "instance_solved"
    assert benchmark_reproduction["score"] == 0.4
    assert by_id["implementation_security_binary_size_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["implementation_security_binary_size_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "benchmark_harness:toy_binary_size_check"
    binary_size_reproduction = by_id["implementation_security_binary_size_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert binary_size_reproduction["status"] == "instance_solved"
    assert binary_size_reproduction["score"] == 0.4
    assert by_id["implementation_security_memory_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["implementation_security_memory_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "benchmark_harness:toy_memory_footprint_check"
    memory_reproduction = by_id["implementation_security_memory_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert memory_reproduction["status"] == "instance_solved"
    assert memory_reproduction["score"] == 0.4
    assert by_id["implementation_security_stack_usage_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["implementation_security_stack_usage_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == "benchmark_harness:toy_stack_usage_check"
    stack_usage_reproduction = by_id["implementation_security_stack_usage_toy_v1"][
        "verifier_result"
    ]["reproduction"]
    assert stack_usage_reproduction["status"] == "instance_solved"
    assert stack_usage_reproduction["score"] == 0.4
    assert by_id["isogeny_historical_toy_path_v1"]["evaluation_status"] == "ok"
    assert by_id["isogeny_historical_toy_path_v1"]["verifier_result"]["estimator"][
        "name"
    ] == "toy-isogeny-historical-path-estimator"
    assert by_id["isogeny_historical_commutative_walk_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["isogeny_historical_commutative_walk_toy_v1"][
        "verifier_result"
    ]["features"]["attack_type"] == (
        "historical_isogeny_reconstruction:toy_commutative_walk_search"
    )
    isogeny_commutative_reproduction = by_id[
        "isogeny_historical_commutative_walk_toy_v1"
    ]["verifier_result"]["reproduction"]
    assert isogeny_commutative_reproduction["status"] == "instance_solved"
    assert isogeny_commutative_reproduction["score"] == 0.4
    assert by_id["isogeny_historical_volcano_walk_toy_v1"][
        "evaluation_status"
    ] == "ok"
    assert by_id["isogeny_historical_volcano_walk_toy_v1"]["verifier_result"][
        "features"
    ]["attack_type"] == (
        "historical_isogeny_reconstruction:toy_volcano_walk_search"
    )
    assert by_id["isogeny_historical_volcano_walk_toy_v1"]["verifier_result"][
        "estimator"
    ]["name"] == "toy-isogeny-historical-path-estimator"
    isogeny_volcano_reproduction = by_id[
        "isogeny_historical_volcano_walk_toy_v1"
    ]["verifier_result"]["reproduction"]
    assert isogeny_volcano_reproduction["status"] == "instance_solved"
    assert isogeny_volcano_reproduction["score"] == 0.4
    assert by_id["lattice_dual_attack_toy_v1"]["evaluation_status"] == "ok"
    assert by_id["lattice_primal_usvp_toy_v1"]["evaluation_status"] == "ok"
    reproduction_result = by_id["lattice_primal_usvp_toy_reproducible_v1"][
        "verifier_result"
    ]["reproduction"]
    assert reproduction_result["status"] == "estimator_reproduced"
    assert reproduction_result["score"] == 0.2
    instance_solution = by_id["lattice_downscaled_lwe_instance_solve_v1"][
        "verifier_result"
    ]["reproduction"]
    assert instance_solution["status"] == "instance_solved"
    assert instance_solution["score"] == 0.4
    second_instance_solution = by_id[
        "lattice_downscaled_lwe_instance_solve_n5_q19_v1"
    ]["verifier_result"]["reproduction"]
    assert second_instance_solution["status"] == "instance_solved"
    assert second_instance_solution["score"] == 0.4
    ternary_instance_solution = by_id[
        "lattice_downscaled_lwe_instance_solve_n6_q23_ternary_v1"
    ]["verifier_result"]["reproduction"]
    assert ternary_instance_solution["status"] == "instance_solved"
    assert ternary_instance_solution["score"] == 0.4
    mlwe_instance_solution = by_id[
        "lattice_downscaled_mlwe_instance_solve_v1"
    ]["verifier_result"]["reproduction"]
    assert mlwe_instance_solution["status"] == "instance_solved"
    assert mlwe_instance_solution["score"] == 0.4
    assert by_id["code_based_isd_placeholder_v1"]["evaluation_status"] == "unsupported"
    assert (
        by_id["invalid_module_hypothesis_on_lwe_v1"]["evaluation_status"] == "invalid"
    )
    assert by_id["invalid_module_hypothesis_on_lwe_v1"]["target_family"] == "LWE"
    assert all(row["safety"]["security_claim"] is False for row in verifier_rows)

    manifest = (out_dir / "MANIFEST.sha256").read_text().splitlines()
    assert any(line.endswith("  attack_plans.jsonl") for line in manifest)
    assert any(line.endswith("  task_metadata.jsonl") for line in manifest)
    assert any(line.endswith("  rl_rollouts.jsonl") for line in manifest)
    assert any(line.endswith("  verifier_outputs.jsonl") for line in manifest)
    assert any(
        line.endswith("  public_runs/code_based_toy_hqc_v0/run_ledger.json")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/code_based_toy_hqc_v0/MANIFEST.sha256")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/code_based_toy_isd_v0/run_ledger.json")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/code_based_toy_isd_v0/MANIFEST.sha256")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/hash_based_toy_bound_v0/run_ledger.json")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/hash_based_toy_bound_v0/MANIFEST.sha256")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/hash_based_toy_misuse_v0/run_ledger.json")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/hash_based_toy_misuse_v0/MANIFEST.sha256")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/hash_based_toy_signature_v0/run_ledger.json")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/hash_based_toy_signature_v0/MANIFEST.sha256")
        for line in manifest
    )
    assert any(
        line.endswith(
            "  public_runs/implementation_security_toy_benchmark_v0/run_ledger.json"
        )
        for line in manifest
    )
    assert any(
        line.endswith(
            "  public_runs/implementation_security_toy_benchmark_v0/MANIFEST.sha256"
        )
        for line in manifest
    )
    assert any(
        line.endswith(
            "  public_runs/implementation_security_toy_kat_v0/run_ledger.json"
        )
        for line in manifest
    )
    assert any(
        line.endswith(
            "  public_runs/implementation_security_toy_kat_v0/MANIFEST.sha256"
        )
        for line in manifest
    )
    assert any(
        line.endswith(
            "  public_runs/implementation_security_toy_timing_v0/run_ledger.json"
        )
        for line in manifest
    )
    assert any(
        line.endswith(
            "  public_runs/implementation_security_toy_timing_v0/MANIFEST.sha256"
        )
        for line in manifest
    )
    assert any(
        line.endswith(
            "  public_runs/isogeny_historical_toy_path_v0/run_ledger.json"
        )
        for line in manifest
    )
    assert any(
        line.endswith(
            "  public_runs/isogeny_historical_toy_path_v0/MANIFEST.sha256"
        )
        for line in manifest
    )
    assert any(
        line.endswith(
            "  public_runs/lattice_downscaled_lwe_instance_solve_v0/run_ledger.json"
        )
        for line in manifest
    )
    assert any(
        line.endswith(
            "  public_runs/lattice_downscaled_lwe_instance_solve_v0/MANIFEST.sha256"
        )
        for line in manifest
    )
    assert any(
        line.endswith(
            "  public_runs/lattice_downscaled_mlwe_instance_solve_v0/run_ledger.json"
        )
        for line in manifest
    )
    assert any(
        line.endswith(
            "  public_runs/lattice_downscaled_mlwe_instance_solve_v0/MANIFEST.sha256"
        )
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/lattice_toy_lwe_v0/run_ledger.json")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/lattice_toy_lwe_v0/MANIFEST.sha256")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/lattice_mlwe_downscaled_v0/run_ledger.json")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/lattice_mlwe_downscaled_v0/MANIFEST.sha256")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/multivariate_toy_mq_v0/run_ledger.json")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/multivariate_toy_mq_v0/MANIFEST.sha256")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/multivariate_toy_minrank_v0/run_ledger.json")
        for line in manifest
    )
    assert any(
        line.endswith("  public_runs/multivariate_toy_minrank_v0/MANIFEST.sha256")
        for line in manifest
    )
    assert _manifest_digest(out_dir, "attack_plans.jsonl") in manifest
    assert _manifest_digest(out_dir, "task_metadata.jsonl") in manifest


def test_huggingface_dataset_bundle_cli_writes_bundle(tmp_path: Path) -> None:
    out_dir = tmp_path / "hf_dataset"

    result = CliRunner().invoke(
        app,
        ["hf-dataset", "--out", str(out_dir)],
    )

    assert result.exit_code == 0
    assert f"hf_dataset={out_dir}" in result.output
    assert (out_dir / "dataset_info.json").exists()


def test_committed_huggingface_dataset_bundle_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "hf_dataset"
    committed = Path("hf/dataset")

    write_huggingface_dataset_bundle(generated)

    generated_files = sorted(
        path.relative_to(generated)
        for path in generated.rglob("*")
        if path.is_file()
    )
    committed_files = sorted(
        path.relative_to(committed)
        for path in committed.rglob("*")
        if path.is_file()
    )

    assert committed_files == generated_files
    for relative_path in generated_files:
        assert (committed / relative_path).read_bytes() == (
            generated / relative_path
        ).read_bytes()


def test_hf_dataset_verify_accepts_committed_bundle() -> None:
    result = verify_huggingface_dataset_bundle(Path("hf/dataset"))

    assert result == {
        "schema_version": "agades.pqc.hf_dataset_verification.v1",
        "dataset_dir": "hf/dataset",
        "accepted": True,
        "summary": {
            "attack_plan_count": 80,
            "contains_private_traces": False,
            "failure_count": 0,
            "invalid_attack_plan_count": 1,
            "invalid_attack_plan_ids": ["invalid_module_hypothesis_on_lwe_v1"],
            "manifest_entry_count": 78,
            "prime_task_eligible_count": 79,
            "public_run_bundle_count": 18,
            "release_gate_count": 7,
            "rl_rollout_rows": 9,
            "security_claim": False,
            "task_metadata_rows": 79,
            "task_metadata_rows_match_attack_plans": True,
            "valid_attack_plan_count": 79,
            "verifier_rows": 80,
        },
        "failures": [],
    }


def test_hf_dataset_verify_rejects_safety_and_row_drift(tmp_path: Path) -> None:
    out_dir = tmp_path / "hf_dataset"
    write_huggingface_dataset_bundle(out_dir)

    info_path = out_dir / "dataset_info.json"
    info = json.loads(info_path.read_text(encoding="utf-8"))
    info["safety"]["contains_private_traces"] = True
    info["release_gates"] = [
        gate for gate in info["release_gates"] if "hf-dataset-verify" not in gate
    ]
    info_path.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n")
    task_metadata_path = out_dir / "task_metadata.jsonl"
    task_metadata_path.write_text("", encoding="utf-8")

    result = verify_huggingface_dataset_bundle(out_dir)

    assert result["accepted"] is False
    assert "Hugging Face dataset info is not in sync." in result["failures"]
    assert "Hugging Face dataset task_metadata.jsonl is not in sync." in result[
        "failures"
    ]
    assert "Hugging Face dataset MANIFEST.sha256 is not in sync." in result[
        "failures"
    ]
    assert "Hugging Face dataset may contain private traces." in result["failures"]
    assert "Task metadata JSONL row count differs from metadata." in result[
        "failures"
    ]
    assert "Task metadata JSONL differs from embedded AttackPlan task metadata." in (
        result["failures"]
    )
    assert any("hf-dataset-verify" in failure for failure in result["failures"])


def test_hf_dataset_verify_rejects_seed_digest_drift(tmp_path: Path) -> None:
    out_dir = tmp_path / "hf_dataset"
    write_huggingface_dataset_bundle(out_dir)

    attack_plan_rows = _read_jsonl(out_dir / "attack_plans.jsonl")
    task_metadata_rows = _read_jsonl(out_dir / "task_metadata.jsonl")
    target_id = "lattice_primal_usvp_toy_v1"
    wrong_digest = "0" * 64
    for row in attack_plan_rows:
        if row["attack_plan_id"] == target_id:
            row["task_metadata"]["seed_attack_plan_sha256"] = wrong_digest
    for row in task_metadata_rows:
        if row["attack_plan_id"] == target_id:
            row["seed_attack_plan_sha256"] = wrong_digest
    (out_dir / "attack_plans.jsonl").write_text(
        _jsonl(attack_plan_rows),
        encoding="utf-8",
    )
    (out_dir / "task_metadata.jsonl").write_text(
        _jsonl(task_metadata_rows),
        encoding="utf-8",
    )

    result = verify_huggingface_dataset_bundle(out_dir)

    assert result["accepted"] is False
    assert (
        "Task metadata seed digest does not match AttackPlan row: "
        "lattice_primal_usvp_toy_v1"
    ) in result["failures"]


def test_hf_dataset_verify_rejects_missing_dataset_bundle(tmp_path: Path) -> None:
    result = verify_huggingface_dataset_bundle(tmp_path / "missing-dataset")

    assert result["accepted"] is False
    assert "Hugging Face dataset directory is missing." in result["failures"]
    assert "Hugging Face dataset info is missing." in result["failures"]


def test_hf_dataset_verify_cli_accepts_current_bundle() -> None:
    result = CliRunner().invoke(
        app,
        ["hf-dataset-verify", "--dataset", "hf/dataset"],
    )

    assert result.exit_code == 0
    assert "agades.pqc.hf_dataset_verification.v1" in result.output
    assert '"accepted": true' in result.output


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _jsonl(rows: list[dict[str, object]]) -> str:
    return "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"


def _manifest_digest(root: Path, relative_path: str) -> str:
    path = root / relative_path
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"{digest}  {relative_path}"
