from __future__ import annotations

from pathlib import Path

from agades_pqc_gym.families.multivariate.minrank_solver import (
    solve_toy_minrank_fixture,
)


def test_multivariate_toy_minrank_solver_recovers_unique_public_solution() -> None:
    solution = solve_toy_minrank_fixture(
        Path(
            "benchmarks/multivariate_toy_minrank/fixtures/"
            "toy_minrank_gf2_m3_r0_fixture.json"
        )
    )

    assert solution.solved is True
    assert solution.target_name == "toy_minrank_gf2_m3_r0"
    assert solution.variables == 4
    assert solution.field_order == 2
    assert solution.matrix_rows == 3
    assert solution.matrix_cols == 3
    assert solution.target_rank == 0
    assert solution.assignment_count == 16
    assert solution.solution == [1, 0, 1, 1]
    assert solution.public is True
    assert solution.security_claim is False


def test_multivariate_toy_minrank_solver_recovers_unique_rank_one_solution() -> None:
    solution = solve_toy_minrank_fixture(
        Path(
            "benchmarks/multivariate_toy_minrank/fixtures/"
            "toy_minrank_gf2_m3_r1_fixture.json"
        )
    )

    assert solution.solved is True
    assert solution.target_name == "toy_minrank_gf2_m3_r1"
    assert solution.variables == 4
    assert solution.field_order == 2
    assert solution.matrix_rows == 3
    assert solution.matrix_cols == 3
    assert solution.target_rank == 1
    assert solution.assignment_count == 16
    assert solution.solution == [0, 1, 1, 0]
    assert solution.public is True
    assert solution.security_claim is False


def test_multivariate_toy_minrank_solver_recovers_unique_rank_two_solution() -> None:
    solution = solve_toy_minrank_fixture(
        Path(
            "benchmarks/multivariate_toy_minrank/fixtures/"
            "toy_minrank_gf2_m4_r2_fixture.json"
        )
    )

    assert solution.solved is True
    assert solution.target_name == "toy_minrank_gf2_m4_r2"
    assert solution.variables == 4
    assert solution.field_order == 2
    assert solution.matrix_rows == 4
    assert solution.matrix_cols == 4
    assert solution.target_rank == 2
    assert solution.assignment_count == 16
    assert solution.solution == [1, 1, 0, 1]
    assert solution.public is True
    assert solution.security_claim is False


def test_multivariate_toy_minrank_packaged_fixture_mirrors_benchmark_fixture() -> None:
    for fixture_name in (
        "toy_minrank_gf2_m3_r0_fixture.json",
        "toy_minrank_gf2_m3_r1_fixture.json",
        "toy_minrank_gf2_m4_r2_fixture.json",
    ):
        benchmark_fixture = Path(
            f"benchmarks/multivariate_toy_minrank/fixtures/{fixture_name}"
        )
        package_fixture = Path(
            f"src/agades_pqc_gym/families/multivariate/fixtures/{fixture_name}"
        )

        assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()
