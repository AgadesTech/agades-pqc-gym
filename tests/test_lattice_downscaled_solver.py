from pathlib import Path

from agades_pqc_gym.families.lattice.downscaled_solver import (
    solve_downscaled_lwe_fixture,
    solve_downscaled_mlwe_fixture,
)


def test_downscaled_lwe_solver_recovers_unique_public_fixture_secret() -> None:
    result = solve_downscaled_lwe_fixture(
        Path("benchmarks/lattice_downscaled_lwe_instances/toy_lwe_n4_q17_instance.json")
    )

    assert result.solved is True
    assert result.secret == [1, 0, 1, 1]
    assert result.residuals == [0, 1, -1, 0, 1, -1, 0, 1]
    assert result.sample_count == 8
    assert result.candidate_count == 16
    assert result.security_claim is False


def test_downscaled_lwe_solver_recovers_second_public_fixture_secret() -> None:
    result = solve_downscaled_lwe_fixture(
        Path("benchmarks/lattice_downscaled_lwe_instances/toy_lwe_n5_q19_instance.json")
    )

    assert result.solved is True
    assert result.secret == [1, 0, 1, 0, 1]
    assert result.residuals == [1, -1, 1, -1, -1, 1, -1, 0, -1, -1]
    assert result.sample_count == 10
    assert result.candidate_count == 32
    assert result.security_claim is False


def test_downscaled_lwe_solver_recovers_ternary_public_fixture_secret() -> None:
    result = solve_downscaled_lwe_fixture(
        Path("benchmarks/lattice_downscaled_lwe_instances/toy_lwe_n6_q23_ternary_instance.json")
    )

    assert result.solved is True
    assert result.secret == [-1, 0, 1, 1, 0, -1]
    assert result.residuals == [0, 1, -1, 0, 1, -1, 1, 0, -1, 1, 0, -1]
    assert result.sample_count == 12
    assert result.candidate_count == 729
    assert result.security_claim is False


def test_downscaled_mlwe_solver_recovers_unique_public_fixture_secret() -> None:
    result = solve_downscaled_mlwe_fixture(
        Path(
            "benchmarks/lattice_downscaled_mlwe_instances/"
            "toy_mlwe_k2_n3_q17_instance.json"
        )
    )

    assert result.solved is True
    assert result.secret == [[1, 0, -1], [0, 1, 1]]
    assert result.residuals == [0, 1, -1, 0, 1, -1, 0, 1]
    assert result.sample_count == 8
    assert result.candidate_count == 729
    assert result.k == 2
    assert result.n == 3
    assert result.security_claim is False
