from __future__ import annotations

from pathlib import Path

from agades_pqc_gym.families.multivariate.mq_solver import (
    solve_toy_mq_fixture,
    solve_toy_mq_hybrid_fixture,
)


def test_multivariate_toy_mq_solver_recovers_unique_public_binary_solution() -> None:
    solution = solve_toy_mq_fixture(
        Path(
            "benchmarks/multivariate_toy_mq/fixtures/"
            "toy_mq_gf2_v6_e4_fixture.json"
        )
    )

    assert solution.solved is True
    assert solution.target_name == "toy_mq_gf2_v6_e4"
    assert solution.assignment_count == 64
    assert solution.solution == [1, 0, 1, 1, 0, 1]
    assert solution.public is True
    assert solution.security_claim is False


def test_multivariate_toy_mq_hybrid_solver_uses_declared_guess_prefix() -> None:
    solution = solve_toy_mq_hybrid_fixture(
        Path(
            "benchmarks/multivariate_toy_mq/fixtures/"
            "toy_mq_gf2_v6_e4_fixture.json"
        ),
        guessed_variables=2,
    )

    assert solution.solved is True
    assert solution.target_name == "toy_mq_gf2_v6_e4"
    assert solution.assignment_count == 64
    assert solution.guessed_variables == 2
    assert solution.guess_count == 4
    assert solution.residual_variables == 4
    assert solution.max_residual_assignments_per_guess == 16
    assert solution.solution == [1, 0, 1, 1, 0, 1]
    assert solution.public is True
    assert solution.security_claim is False


def test_multivariate_toy_mq_packaged_fixture_mirrors_benchmark_fixture() -> None:
    benchmark_fixture = Path(
        "benchmarks/multivariate_toy_mq/fixtures/"
        "toy_mq_gf2_v6_e4_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/multivariate/fixtures/"
        "toy_mq_gf2_v6_e4_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()
