from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agades_pqc_gym.core.attack_plan import AttackPlan, Constraints
from agades_pqc_gym.verifier import verify_attack_plan_json, verify_attack_plan_path


def test_public_verifier_returns_prime_compatible_lattice_result() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json")
    )

    assert result["schema_version"] == "agades.pqc.verifier.v1"
    assert result["attack_plan_id"] == "lattice_primal_usvp_toy_v1"
    assert result["target_family"] == "LWE"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["combined_score"] < 0
    assert result["estimator"]["schema_version"] == (
        "agades.pqc.evaluator_result.v1"
    )
    assert result["estimator"]["name"] == "mock-lattice-estimator"
    assert result["safety"]["arbitrary_code_execution"] is False
    assert result["reproduction"]["status"] == "not_requested"
    assert "attack_plan" not in result


def test_public_verifier_exposes_downscaled_reproduction_status() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    ).model_copy(
        update={
            "constraints": Constraints(
                max_memory_bits=80.0,
                max_time_bits=128.0,
                require_reproducibility_on_downscaled_instances=True,
            )
        }
    )

    result = verify_attack_plan_json(plan.model_dump_json())

    assert result["accepted"] is True
    assert result["reproducibility_score"] == 0.2
    assert result["reproduction"]["attempted"] is True
    assert result["reproduction"]["status"] == "estimator_reproduced"
    assert result["reproduction"]["success"] is True
    assert "not cryptanalytic evidence" in " ".join(result["reproduction"]["warnings"])


def test_public_verifier_exposes_assumption_set_features() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy_reproducible.json")
        .read_text()
    )
    plan = plan.model_copy(
        update={
            "operators": [
                plan.operators[0].model_copy(
                    update={
                        "assumptions": [
                            "requires_expert_review",
                            "lattice_estimator_default_cost_model",
                        ]
                    }
                )
            ]
        }
    )

    result = verify_attack_plan_json(plan.model_dump_json())

    assert result["features"]["assumption_count"] == 2
    assert result["features"]["unique_assumption_count"] == 2
    assert result["features"]["risky_assumption_count"] == 1
    assert len(result["features"]["assumption_fingerprint"]) == 64


def test_public_verifier_preserves_unsupported_family_semantics() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/code_based_isd_placeholder.json")
    )

    assert result["target_family"] == "CODE_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is False
    assert result["evaluation_status"] == "unsupported"
    assert result["estimated_time_bits"] is None
    assert result["estimated_memory_bits"] is None
    assert result["estimator"]["name"] == "code-based-placeholder-estimator"


def test_public_verifier_validation_errors_are_dependency_version_stable() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/invalid_plan_should_fail.json")
    )

    assert result["schema_valid"] is False
    assert result["accepted"] is False
    assert result["evaluation_status"] == "invalid"
    assert result["validation_errors"]
    assert "module_lattice_reduction_hypothesis requires an MLWE target" in (
        " ".join(result["validation_errors"])
    )
    assert not any(
        "errors.pydantic.dev" in error for error in result["validation_errors"]
    )


@pytest.mark.parametrize(
    ("path", "attack_plan_id", "attack_type", "placeholder_param"),
    [
        (
            Path("examples/attack_plans/implementation_security_pqclean_schema.json"),
            "implementation_security_pqclean_schema_v1",
            "kat_conformance",
            "suite",
        ),
        (
            Path("examples/attack_plans/implementation_security_liboqs_schema.json"),
            "implementation_security_liboqs_schema_v1",
            "benchmark_harness",
            "metric",
        ),
        (
            Path("examples/attack_plans/implementation_security_pqm4_schema.json"),
            "implementation_security_pqm4_schema_v1",
            "benchmark_harness",
            "metric",
        ),
        (
            Path(
                "examples/attack_plans/"
                "implementation_security_pq_code_package_schema.json"
            ),
            "implementation_security_pq_code_package_schema_v1",
            "kat_conformance",
            "suite",
        ),
        (
            Path("examples/attack_plans/implementation_security_dudect_schema.json"),
            "implementation_security_dudect_schema_v1",
            "constant_time_check",
            "tool",
        ),
        (
            Path(
                "examples/attack_plans/implementation_security_nist_acvp_schema.json"
            ),
            "implementation_security_nist_acvp_schema_v1",
            "kat_conformance",
            "suite",
        ),
        (
            Path("examples/attack_plans/implementation_security_ctgrind_schema.json"),
            "implementation_security_ctgrind_schema_v1",
            "constant_time_check",
            "tool",
        ),
        (
            Path("examples/attack_plans/implementation_security_timecop_schema.json"),
            "implementation_security_timecop_schema_v1",
            "constant_time_check",
            "tool",
        ),
    ],
)
def test_public_verifier_keeps_implementation_security_source_placeholders_unsupported(
    path: Path,
    attack_plan_id: str,
    attack_type: str,
    placeholder_param: str,
) -> None:
    plan = AttackPlan.model_validate_json(path.read_text(encoding="utf-8"))
    operator = plan.operators[0]

    assert plan.metadata.public is True
    assert operator.type == attack_type
    assert operator.params[placeholder_param].endswith("_schema_placeholder")
    assert not (
        {
            "binary_path",
            "device_id",
            "host",
            "ip",
            "ssh_target",
            "target_url",
            "trace_path",
        }
        & set(operator.params)
    )

    result = verify_attack_plan_path(path)

    assert result["attack_plan_id"] == attack_plan_id
    assert result["target_family"] == "IMPLEMENTATION_SECURITY"
    assert result["schema_valid"] is True
    assert result["accepted"] is False
    assert result["evaluation_status"] == "unsupported"
    assert result["estimated_time_bits"] is None
    assert result["estimated_memory_bits"] is None
    assert (
        result["estimator"]["name"]
        == "implementation-security-placeholder-evaluator"
    )
    assert result["safety"] == {
        "arbitrary_code_execution": False,
        "live_targeting": False,
        "security_claim": False,
    }
    assert any("schema-only target" in warning for warning in result["warnings"])


@pytest.mark.parametrize(
    ("path", "attack_plan_id"),
    [
        (
            Path("examples/attack_plans/code_based_classic_mceliece_placeholder.json"),
            "code_based_classic_mceliece_placeholder_v1",
        ),
        (
            Path("examples/attack_plans/code_based_bike_placeholder.json"),
            "code_based_bike_placeholder_v1",
        ),
    ],
)
def test_public_verifier_keeps_code_based_roadmap_placeholders_unsupported(
    path: Path,
    attack_plan_id: str,
) -> None:
    result = verify_attack_plan_path(path)

    assert result["attack_plan_id"] == attack_plan_id
    assert result["target_family"] == "CODE_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is False
    assert result["evaluation_status"] == "unsupported"
    assert result["estimated_time_bits"] is None
    assert result["estimated_memory_bits"] is None
    assert result["estimator"]["name"] == "code-based-placeholder-estimator"
    assert any("schema-only target" in warning for warning in result["warnings"])


def test_public_verifier_preserves_ntru_sis_schema_only_lattice_boundary() -> None:
    ntru = verify_attack_plan_path(
        Path("examples/attack_plans/lattice_ntru_schema_placeholder.json")
    )
    sis = verify_attack_plan_path(
        Path("examples/attack_plans/lattice_sis_schema_placeholder.json")
    )

    for result, family in [(ntru, "NTRU"), (sis, "SIS")]:
        assert result["target_family"] == family
        assert result["schema_valid"] is True
        assert result["accepted"] is False
        assert result["evaluation_status"] == "unsupported"
        assert result["estimated_time_bits"] is None
        assert result["estimated_memory_bits"] is None
        assert result["estimator"]["name"] == "lattice-family-router"
        assert result["safety"]["security_claim"] is False
        assert any(
            "unsupported until mappings are reviewed" in warning
            for warning in result["warnings"]
        )


def test_public_verifier_rejects_runtime_lattice_operator_as_primary_route() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/lattice_lwe_modulus_switching_primary.json")
    )

    assert result["attack_plan_id"] == "lattice_lwe_modulus_switching_primary_v1"
    assert result["target_family"] == "LWE"
    assert result["schema_valid"] is True
    assert result["accepted"] is False
    assert result["evaluation_status"] == "unsupported"
    assert result["estimated_time_bits"] is None
    assert result["estimated_memory_bits"] is None
    assert result["estimator"]["name"] == "lattice-family-router"
    assert result["features"]["attack_type"] == "modulus_switching"
    assert any(
        "not a cataloged primary LWE/MLWE estimator route" in warning
        for warning in result["warnings"]
    )


def test_public_verifier_accepts_code_based_toy_isd_without_lattice_estimator() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/code_based_prange_toy.json")
    )

    assert result["target_family"] == "CODE_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] is not None
    assert result["estimator"]["name"] == "toy-code-based-isd-estimator"
    assert result["features"]["attack_type"] == "information_set_decoding:prange_toy"
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_second_code_based_toy_isd_fixture() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/code_based_prange_toy_n15.json")
    )

    assert result["target_family"] == "CODE_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 7.3987
    assert result["estimator"]["name"] == "toy-code-based-isd-estimator"
    assert result["features"]["attack_type"] == "information_set_decoding:prange_toy"
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_code_based_stern_toy_isd() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/code_based_stern_toy.json")
    )

    assert result["target_family"] == "CODE_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] is not None
    assert result["estimator"]["name"] == "toy-code-based-isd-estimator"
    assert result["features"]["attack_type"] == "information_set_decoding:stern_toy"
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_code_based_dumer_toy_isd() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/code_based_dumer_toy.json")
    )

    assert result["target_family"] == "CODE_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] is not None
    assert result["estimator"]["name"] == "toy-code-based-isd-estimator"
    assert result["features"]["attack_type"] == "information_set_decoding:dumer_toy"
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_code_based_lee_brickell_toy_isd() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/code_based_lee_brickell_toy.json")
    )

    assert result["target_family"] == "CODE_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 14.3741
    assert result["estimated_memory_bits"] == 5.5546
    assert result["estimator"]["name"] == "toy-code-based-isd-estimator"
    assert result["features"]["attack_type"] == (
        "information_set_decoding:lee_brickell_toy"
    )
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_code_based_hqc_repetition_toy_fixture() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/code_based_hqc_repetition_toy.json")
    )

    assert result["target_family"] == "CODE_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 4.3923
    assert result["estimated_memory_bits"] == 4.8074
    assert result["estimator"]["name"] == (
        "toy-code-based-repetition-decoder-estimator"
    )
    assert result["features"]["attack_type"] == (
        "decoding_fixture_check:hqc_repetition_toy"
    )
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("not an HQC result" in warning for warning in result["warnings"])
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_code_based_hqc_parity_check_toy_fixture() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/code_based_hqc_parity_check_toy.json")
    )

    assert result["target_family"] == "CODE_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 10.7142
    assert result["estimated_memory_bits"] == 4.6439
    assert result["estimator"]["name"] == (
        "toy-code-based-parity-check-decoder-estimator"
    )
    assert result["features"]["attack_type"] == (
        "decoding_fixture_check:hqc_parity_check_toy"
    )
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("not an HQC result" in warning for warning in result["warnings"])
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_hash_based_toy_bound() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/hash_based_preimage_toy.json")
    )

    assert result["target_family"] == "HASH_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 32.0
    assert result["estimator"]["name"] == "toy-hash-bound-estimator"
    assert result["features"]["attack_type"] == (
        "security_bound_check:toy_preimage_bound"
    )
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_hash_based_toy_collision_bound() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/hash_based_collision_toy.json")
    )

    assert result["target_family"] == "HASH_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 16.0
    assert result["estimated_memory_bits"] == 16.0
    assert result["estimator"]["name"] == "toy-hash-bound-estimator"
    assert result["features"]["attack_type"] == (
        "security_bound_check:toy_collision_bound"
    )
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_hash_based_toy_signature_chain() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/hash_based_signature_toy.json")
    )

    assert result["target_family"] == "HASH_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 5.0
    assert result["estimator"]["name"] == "toy-hash-bound-estimator"
    assert result["features"]["attack_type"] == (
        "hash_signature_verification:toy_wots_chain_verify"
    )
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_hash_based_toy_merkle_auth_path() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/hash_based_merkle_auth_path_toy.json")
    )

    assert result["target_family"] == "HASH_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 2.0
    assert result["estimator"]["name"] == "toy-hash-bound-estimator"
    assert result["features"]["attack_type"] == (
        "hash_signature_verification:toy_merkle_auth_path_verify"
    )
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_hash_based_toy_misuse_check() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/hash_based_misuse_reused_salt_toy.json")
    )

    assert result["target_family"] == "HASH_BASED"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 2.585
    assert result["estimated_memory_bits"] == 3.585
    assert result["estimator"]["name"] == "toy-hash-bound-estimator"
    assert result["features"]["attack_type"] == "misuse_check:toy_hash_reused_salt"
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_multivariate_toy_mq() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/multivariate_mq_toy.json")
    )

    assert result["target_family"] == "MULTIVARIATE"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 34.585
    assert result["estimator"]["name"] == "toy-multivariate-estimator"
    assert result["features"]["attack_type"] == "groebner_basis:toy_mq_search"
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_multivariate_toy_mq_hybrid() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/multivariate_mq_hybrid_toy.json")
    )

    assert result["target_family"] == "MULTIVARIATE"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 27.7619
    assert result["estimated_memory_bits"] == 8.8041
    assert result["estimator"]["name"] == "toy-multivariate-estimator"
    assert result["features"]["attack_type"] == (
        "groebner_basis:toy_mq_hybrid_search"
    )
    assert result["reproduction"]["status"] == "not_applicable"
    assert result["reproduction"]["score"] == 0.0
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_multivariate_toy_mq_degree_bound() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/multivariate_mq_degree_bound_toy.json")
    )

    assert result["target_family"] == "MULTIVARIATE"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 27.2107
    assert result["estimated_memory_bits"] == 13.1212
    assert result["estimator"]["name"] == "toy-multivariate-estimator"
    assert result["features"]["attack_type"] == (
        "groebner_basis:toy_mq_degree_bound"
    )
    assert result["reproduction"]["status"] == "not_applicable"
    assert any("not a Groebner proof" in warning for warning in result["warnings"])
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_multivariate_toy_minrank() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/multivariate_minrank_toy.json")
    )

    assert result["target_family"] == "MULTIVARIATE"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 8.7549
    assert result["estimator"]["name"] == "toy-multivariate-estimator"
    assert result["features"]["attack_type"] == "minrank_attack:toy_minrank_search"
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_implementation_security_toy_kat() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/implementation_security_kat_toy.json")
    )

    assert result["target_family"] == "IMPLEMENTATION_SECURITY"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimator"]["name"] == (
        "toy-implementation-security-estimator"
    )
    assert result["features"]["attack_type"] == (
        "kat_conformance:toy_kat_digest_match"
    )
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_implementation_security_toy_timing() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/implementation_security_timing_toy.json")
    )

    assert result["target_family"] == "IMPLEMENTATION_SECURITY"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 3.585
    assert result["estimator"]["name"] == "toy-implementation-security-estimator"
    assert result["features"]["attack_type"] == (
        "constant_time_check:toy_timing_welch_t_check"
    )
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("not a constant-time" in warning for warning in result["warnings"])
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_implementation_security_toy_ctgrind_taint() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/implementation_security_ctgrind_taint_toy.json")
    )

    assert result["target_family"] == "IMPLEMENTATION_SECURITY"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 3.7004
    assert result["estimated_memory_bits"] == 0.0
    assert result["estimator"]["name"] == "toy-implementation-security-estimator"
    assert result["features"]["attack_type"] == (
        "constant_time_check:toy_ctgrind_secret_taint_summary_check"
    )
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("did not execute ctgrind" in warning for warning in result["warnings"])
    assert any("not a constant-time" in warning for warning in result["warnings"])
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_implementation_security_toy_acvp() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/implementation_security_acvp_toy.json")
    )

    assert result["target_family"] == "IMPLEMENTATION_SECURITY"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 8.1649
    assert result["estimator"]["name"] == "toy-implementation-security-estimator"
    assert result["features"]["attack_type"] == (
        "kat_conformance:toy_acvp_vector_set_match"
    )
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("not an ACVP certificate" in warning for warning in result["warnings"])
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_implementation_security_toy_benchmark() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/implementation_security_benchmark_toy.json")
    )

    assert result["target_family"] == "IMPLEMENTATION_SECURITY"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 12.5507
    assert result["estimated_memory_bits"] == 2.3219
    assert result["estimator"]["name"] == "toy-implementation-security-estimator"
    assert result["features"]["attack_type"] == (
        "benchmark_harness:toy_benchmark_summary_check"
    )
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("not a performance claim" in warning for warning in result["warnings"])
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_implementation_security_toy_binary_size() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/implementation_security_binary_size_toy.json")
    )

    assert result["target_family"] == "IMPLEMENTATION_SECURITY"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimated_time_bits"] == 14.5236
    assert result["estimated_memory_bits"] == 14.0
    assert result["estimator"]["name"] == "toy-implementation-security-estimator"
    assert result["features"]["attack_type"] == (
        "benchmark_harness:toy_binary_size_check"
    )
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("not a binary-size claim" in warning for warning in result["warnings"])
    assert any("not a performance claim" in warning for warning in result["warnings"])
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_isogeny_historical_toy_path() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/isogeny_historical_toy.json")
    )

    assert result["target_family"] == "ISOGENY_HISTORICAL"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimator"]["name"] == "toy-isogeny-historical-path-estimator"
    assert result["features"]["attack_type"] == (
        "historical_isogeny_reconstruction:toy_sidh_path_search"
    )
    assert any("historical toy" in warning for warning in result["warnings"])
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_public_verifier_accepts_isogeny_historical_commutative_walk_toy() -> None:
    result = verify_attack_plan_path(
        Path("examples/attack_plans/isogeny_historical_commutative_walk_toy.json")
    )

    assert result["target_family"] == "ISOGENY_HISTORICAL"
    assert result["schema_valid"] is True
    assert result["accepted"] is True
    assert result["evaluation_status"] == "ok"
    assert result["estimator"]["name"] == "toy-isogeny-historical-path-estimator"
    assert result["features"]["attack_type"] == (
        "historical_isogeny_reconstruction:toy_commutative_walk_search"
    )
    assert result["reproduction"]["status"] == "instance_solved"
    assert result["reproduction"]["score"] == 0.4
    assert any("historical toy" in warning for warning in result["warnings"])
    assert any("not a security claim" in warning for warning in result["warnings"])


def test_prime_verifier_script_outputs_public_json() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path("src").resolve())
    completed = subprocess.run(
        [
            sys.executable,
            "prime_intellect/verifier.py",
            "examples/attack_plans/lattice_primal_usvp_toy.json",
        ],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    result = json.loads(completed.stdout)
    assert result["schema_version"] == "agades.pqc.verifier.v1"
    assert result["evaluation_status"] == "ok"


def test_hf_space_adapter_evaluates_json_without_gradio_dependency() -> None:
    spec = importlib.util.spec_from_file_location("hf_space_app", "hf/app.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    raw_plan = Path("examples/attack_plans/code_based_isd_placeholder.json").read_text()
    summary, payload = module.evaluate_attack_plan_json(raw_plan)

    result = json.loads(payload)
    assert "unsupported" in summary
    assert result["evaluation_status"] == "unsupported"


def test_hf_space_exposes_curated_public_examples_without_path_input() -> None:
    spec = importlib.util.spec_from_file_location("hf_space_app", "hf/app.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    choices = module.example_plan_choices()
    valid_public_plans = _valid_public_attack_plans()

    assert len(choices) == len(valid_public_plans)
    assert set(choices) == {
        f"{plan.target.family.value} / {plan.attack_plan_id}"
        for plan in valid_public_plans
    }
    assert "MLWE / lattice_mlwe_module_hypothesis_toy_v1" in choices
    assert "LWE / invalid_module_hypothesis_on_lwe_v1" not in choices
    assert json.loads(module.load_example_plan(choices[0]))["attack_plan_id"]
    _, unsupported_payload = module.evaluate_attack_plan_json(
        module.load_example_plan("CODE_BASED / code_based_isd_placeholder_v1")
    )
    assert json.loads(unsupported_payload)["evaluation_status"] == "unsupported"

    with pytest.raises(ValueError, match="unknown example plan"):
        module.load_example_plan("../private.json")


def test_hf_space_requirements_install_public_package_from_github() -> None:
    requirements = Path("hf/requirements.txt").read_text().splitlines()

    assert (
        "agades-pqc-gym @ "
        "git+https://github.com/AgadesTech/agades-pqc-gym.git@main"
    ) in requirements


def _valid_public_attack_plans() -> list[AttackPlan]:
    plans = []
    for path in sorted(Path("examples/attack_plans").glob("*.json")):
        try:
            plan = AttackPlan.model_validate_json(path.read_text())
        except ValueError:
            continue
        if plan.metadata.public:
            plans.append(plan)
    return plans
