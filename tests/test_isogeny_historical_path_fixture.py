from __future__ import annotations

from pathlib import Path

from agades_pqc_gym.families.isogeny_historical.path_fixture import (
    verify_toy_isogeny_path_fixture,
)


def test_isogeny_historical_toy_path_fixture_verifies_public_path() -> None:
    result = verify_toy_isogeny_path_fixture(
        Path(
            "benchmarks/isogeny_historical_toy_path/fixtures/"
            "toy_sidh_path_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_sidh_path_reconstruction"
    assert result.n == 64
    assert result.case == "toy_sidh_path_search"
    assert result.walk_length == 8
    assert result.branching_factor == 4
    assert result.start_node == "toy_curve_start"
    assert result.end_node == "toy_curve_end"
    assert result.path == [
        "toy_curve_start",
        "toy_kernel_a",
        "toy_kernel_b",
        "toy_kernel_c",
        "toy_kernel_d",
        "toy_kernel_e",
        "toy_kernel_f",
        "toy_kernel_g",
        "toy_curve_end",
    ]
    assert result.historical_not_current is True
    assert result.current_standard_claim is False
    assert result.public is True
    assert result.security_claim is False


def test_isogeny_historical_toy_commutative_walk_fixture_verifies_public_path() -> None:
    result = verify_toy_isogeny_path_fixture(
        Path(
            "benchmarks/isogeny_historical_toy_path/fixtures/"
            "toy_commutative_walk_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_commutative_walk_reconstruction"
    assert result.n == 97
    assert result.case == "toy_commutative_walk_search"
    assert result.walk_length == 6
    assert result.branching_factor == 5
    assert result.start_node == "toy_class_group_start"
    assert result.end_node == "toy_class_group_end"
    assert result.path == [
        "toy_class_group_start",
        "toy_prime_3_step",
        "toy_prime_5_step",
        "toy_prime_7_step",
        "toy_prime_11_step",
        "toy_prime_13_step",
        "toy_class_group_end",
    ]
    assert result.historical_not_current is True
    assert result.current_standard_claim is False
    assert result.public is True
    assert result.security_claim is False


def test_isogeny_historical_path_packaged_fixture_mirror() -> None:
    for fixture_name in (
        "toy_sidh_path_fixture.json",
        "toy_commutative_walk_fixture.json",
    ):
        benchmark_fixture = Path(
            f"benchmarks/isogeny_historical_toy_path/fixtures/{fixture_name}"
        )
        package_fixture = Path(
            f"src/agades_pqc_gym/families/isogeny_historical/fixtures/{fixture_name}"
        )

        assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()
