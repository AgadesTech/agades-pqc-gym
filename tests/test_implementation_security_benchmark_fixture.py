from __future__ import annotations

from pathlib import Path

from agades_pqc_gym.families.implementation_security.benchmark_fixture import (
    verify_toy_benchmark_fixture,
)


def test_toy_benchmark_fixture_verifies_public_summary() -> None:
    result = verify_toy_benchmark_fixture(
        Path(
            "benchmarks/implementation_security_toy_benchmark/fixtures/"
            "toy_mlkem_benchmark_summary_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_mlkem_benchmark_summary"
    assert result.suite == "toy_mlkem_benchmark"
    assert result.metric == "toy_cycles_per_operation"
    assert result.model == "toy_benchmark_summary_check"
    assert result.samples == [1200, 1210, 1190, 1205, 1195]
    assert result.sample_count == 5
    assert result.median_cycles == 1200.0
    assert result.max_median_cycles == 1250.0
    assert result.artifact_execution is False
    assert result.public is True
    assert result.security_claim is False


def test_toy_memory_fixture_verifies_public_summary() -> None:
    result = verify_toy_benchmark_fixture(
        Path(
            "benchmarks/implementation_security_toy_benchmark/fixtures/"
            "toy_mlkem_memory_footprint_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_mlkem_memory_footprint"
    assert result.suite == "toy_mlkem_memory"
    assert result.metric == "toy_memory_footprint_bytes"
    assert result.model == "toy_memory_footprint_check"
    assert result.stack_bytes == 2048
    assert result.heap_bytes == 1024
    assert result.code_bytes == 8192
    assert result.total_bytes == 11264
    assert result.max_stack_bytes == 4096
    assert result.max_heap_bytes == 2048
    assert result.max_code_bytes == 16384
    assert result.artifact_execution is False
    assert result.public is True
    assert result.security_claim is False


def test_toy_stack_usage_fixture_verifies_public_summary() -> None:
    result = verify_toy_benchmark_fixture(
        Path(
            "benchmarks/implementation_security_toy_benchmark/fixtures/"
            "toy_pqm4_stack_usage_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_pqm4_stack_usage"
    assert result.suite == "toy_pqm4_stack_usage"
    assert result.metric == "toy_stack_usage_bytes"
    assert result.model == "toy_stack_usage_check"
    assert result.stack_samples == [1536, 1600, 1584, 1616, 1568]
    assert result.sample_count == 5
    assert result.max_observed_stack_bytes == 1616
    assert result.mean_stack_bytes == 1580.8
    assert result.max_stack_bytes == 2048
    assert result.artifact_execution is False
    assert result.public is True
    assert result.security_claim is False


def test_toy_binary_size_fixture_verifies_public_summary() -> None:
    result = verify_toy_benchmark_fixture(
        Path(
            "benchmarks/implementation_security_toy_benchmark/fixtures/"
            "toy_mlkem_binary_size_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_mlkem_binary_size"
    assert result.suite == "toy_mlkem_binary_size"
    assert result.metric == "toy_binary_size_bytes"
    assert result.model == "toy_binary_size_check"
    assert result.text_bytes == 16384
    assert result.rodata_bytes == 4096
    assert result.data_bytes == 1024
    assert result.bss_bytes == 2048
    assert result.total_bytes == 23552
    assert result.max_total_bytes == 24576
    assert result.artifact_execution is False
    assert result.public is True
    assert result.security_claim is False


def test_implementation_security_toy_benchmark_packaged_fixture_mirror() -> None:
    benchmark_fixture = Path(
        "benchmarks/implementation_security_toy_benchmark/fixtures/"
        "toy_mlkem_benchmark_summary_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/implementation_security/fixtures/"
        "toy_mlkem_benchmark_summary_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()


def test_implementation_security_toy_binary_size_packaged_fixture_mirror() -> None:
    benchmark_fixture = Path(
        "benchmarks/implementation_security_toy_benchmark/fixtures/"
        "toy_mlkem_binary_size_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/implementation_security/fixtures/"
        "toy_mlkem_binary_size_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()


def test_implementation_security_toy_memory_packaged_fixture_mirror() -> None:
    benchmark_fixture = Path(
        "benchmarks/implementation_security_toy_benchmark/fixtures/"
        "toy_mlkem_memory_footprint_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/implementation_security/fixtures/"
        "toy_mlkem_memory_footprint_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()


def test_implementation_security_toy_stack_usage_packaged_fixture_mirror() -> None:
    benchmark_fixture = Path(
        "benchmarks/implementation_security_toy_benchmark/fixtures/"
        "toy_pqm4_stack_usage_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/implementation_security/fixtures/"
        "toy_pqm4_stack_usage_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()
