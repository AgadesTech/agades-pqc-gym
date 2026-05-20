from __future__ import annotations

from pathlib import Path

from agades_pqc_gym.families.implementation_security.timing_fixture import (
    verify_toy_ctgrind_taint_fixture,
    verify_toy_timing_fixture,
)


def test_implementation_security_toy_timing_fixture_verifies_public_summary() -> None:
    result = verify_toy_timing_fixture(
        Path(
            "benchmarks/implementation_security_toy_timing/fixtures/"
            "toy_timing_welch_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_timing_welch_mlkem"
    assert result.tool == "toy_welch_timing_check"
    assert result.model == "toy_timing_welch_t_check"
    assert result.fixed_cycles == [100, 101, 99, 100, 102, 98]
    assert result.random_cycles == [101, 100, 100, 102, 99, 101]
    assert result.fixed_sample_count == 6
    assert result.random_sample_count == 6
    assert result.observed_abs_t == 0.6956
    assert result.max_abs_t == 1.0
    assert result.artifact_execution is False
    assert result.public is True
    assert result.security_claim is False


def test_implementation_security_toy_dudect_summary_fixture_verifies_public_summary(
) -> None:
    result = verify_toy_timing_fixture(
        Path(
            "benchmarks/implementation_security_toy_timing/fixtures/"
            "toy_dudect_mlkem_summary_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_dudect_mlkem_summary"
    assert result.tool == "toy_dudect_summary_check"
    assert result.model == "toy_dudect_summary_threshold_check"
    assert result.dudect_version == "dudect-toy-summary-v0"
    assert result.fixed_cycles == [210, 211, 209, 210, 212, 208, 211, 209]
    assert result.random_cycles == [211, 210, 210, 212, 209, 211, 210, 212]
    assert result.fixed_sample_count == 8
    assert result.random_sample_count == 8
    assert result.observed_abs_t == 1.0491
    assert result.max_abs_t == 1.2
    assert result.artifact_execution is False
    assert result.dudect_execution is False
    assert result.public is True
    assert result.constant_time_claim is False
    assert result.security_claim is False


def test_implementation_security_toy_ctgrind_taint_fixture_verifies_public_summary(
) -> None:
    result = verify_toy_ctgrind_taint_fixture(
        Path(
            "benchmarks/implementation_security_toy_timing/fixtures/"
            "toy_ctgrind_mlkem_secret_taint_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_ctgrind_mlkem_secret_taint"
    assert result.tool == "toy_ctgrind_secret_taint_summary_check"
    assert result.model == "toy_ctgrind_secret_taint_summary_check"
    assert result.ctgrind_version == "ctgrind-toy-summary-v0"
    assert result.checked_blocks == 12
    assert result.secret_dependent_branch_count == 0
    assert result.secret_dependent_memory_access_count == 0
    assert result.max_secret_dependent_branch_count == 0
    assert result.max_secret_dependent_memory_access_count == 0
    assert result.artifact_execution is False
    assert result.ctgrind_execution is False
    assert result.public is True
    assert result.constant_time_claim is False
    assert result.security_claim is False


def test_implementation_security_toy_timing_packaged_fixture_mirror() -> None:
    benchmark_fixture = Path(
        "benchmarks/implementation_security_toy_timing/fixtures/"
        "toy_timing_welch_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/implementation_security/fixtures/"
        "toy_timing_welch_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()


def test_implementation_security_toy_dudect_summary_packaged_fixture_mirror() -> None:
    benchmark_fixture = Path(
        "benchmarks/implementation_security_toy_timing/fixtures/"
        "toy_dudect_mlkem_summary_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/implementation_security/fixtures/"
        "toy_dudect_mlkem_summary_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()


def test_implementation_security_toy_ctgrind_taint_packaged_fixture_mirror() -> None:
    benchmark_fixture = Path(
        "benchmarks/implementation_security_toy_timing/fixtures/"
        "toy_ctgrind_mlkem_secret_taint_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/implementation_security/fixtures/"
        "toy_ctgrind_mlkem_secret_taint_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()
