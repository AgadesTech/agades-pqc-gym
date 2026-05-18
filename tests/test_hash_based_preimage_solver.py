from __future__ import annotations

from pathlib import Path

from agades_pqc_gym.families.hash_based.preimage_solver import (
    solve_toy_preimage_fixture,
)


def test_hash_based_toy_preimage_solver_recovers_unique_public_candidate() -> None:
    solution = solve_toy_preimage_fixture(
        Path(
            "benchmarks/hash_based_toy_bound/fixtures/"
            "toy_hash_preimage_24_fixture.json"
        )
    )

    assert solution.solved is True
    assert solution.target_name == "toy_hash_preimage_24"
    assert solution.digest_bits == 24
    assert solution.hash_function == "SHAKE256"
    assert solution.digest_hex == "59c55a"
    assert solution.candidate_count == 65536
    assert solution.candidate == 4242
    assert solution.public is True
    assert solution.security_claim is False


def test_hash_based_toy_preimage_packaged_fixture_mirrors_benchmark_fixture() -> None:
    benchmark_fixture = Path(
        "benchmarks/hash_based_toy_bound/fixtures/"
        "toy_hash_preimage_24_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/hash_based/fixtures/"
        "toy_hash_preimage_24_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()
