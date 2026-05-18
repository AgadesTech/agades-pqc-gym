from pathlib import Path

from agades_pqc_gym.families.code_based.syndrome_solver import (
    solve_toy_qc_rotation_fixture,
    solve_toy_syndrome_fixture,
)


def test_toy_syndrome_solver_recovers_unique_public_error_vector() -> None:
    result = solve_toy_syndrome_fixture(
        Path("benchmarks/code_based_toy_isd/fixtures/toy_syndrome_31_16_w3_fixture.json")
    )

    assert result.solved is True
    assert result.error_positions == [0, 3, 9]
    assert result.error_vector_weight == 3
    assert result.candidate_count == 4495
    assert result.target_name == "toy_syndrome_31_16_w3"
    assert result.public is True
    assert result.security_claim is False


def test_toy_syndrome_solver_recovers_second_public_error_vector() -> None:
    result = solve_toy_syndrome_fixture(
        Path(
            "benchmarks/code_based_toy_isd/fixtures/"
            "toy_syndrome_15_7_w2_fixture.json"
        )
    )

    assert result.solved is True
    assert result.error_positions == [2, 11]
    assert result.error_vector_weight == 2
    assert result.candidate_count == 105
    assert result.target_name == "toy_syndrome_15_7_w2"
    assert result.public is True
    assert result.security_claim is False


def test_toy_qc_rotation_solver_recovers_unique_public_rotation() -> None:
    result = solve_toy_qc_rotation_fixture(
        Path(
            "benchmarks/code_based_toy_isd/fixtures/"
            "toy_qc_syndrome_21_12_w2_fixture.json"
        )
    )

    assert result.solved is True
    assert result.rotation == 3
    assert result.error_positions == [4, 11]
    assert result.error_vector_weight == 2
    assert result.candidate_count == 7
    assert result.target_name == "toy_qc_syndrome_21_12_w2"
    assert result.public is True
    assert result.security_claim is False
