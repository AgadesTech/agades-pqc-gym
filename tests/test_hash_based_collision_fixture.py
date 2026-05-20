from __future__ import annotations

import json
from pathlib import Path

import pytest

from agades_pqc_gym.families.hash_based.collision_fixture import (
    verify_toy_collision_fixture,
)


def test_hash_based_toy_collision_fixture_verifies_public_pair() -> None:
    result = verify_toy_collision_fixture(
        Path(
            "benchmarks/hash_based_toy_bound/fixtures/"
            "toy_hash_collision_32_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_hash_collision_32"
    assert result.digest_bits == 32
    assert result.hash_function == "SHAKE256"
    assert result.digest_hex == "f4fb02c8"
    assert result.left_message == "agades-hash-collision-v0:22252"
    assert result.right_message == "agades-hash-collision-v0:26349"
    assert result.public is True
    assert result.security_claim is False


def test_hash_based_toy_collision_packaged_fixture_mirrors_benchmark_fixture() -> None:
    benchmark_fixture = Path(
        "benchmarks/hash_based_toy_bound/fixtures/"
        "toy_hash_collision_32_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/hash_based/fixtures/"
        "toy_hash_collision_32_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()


def test_hash_based_toy_collision_fixture_rejects_non_collision(
    tmp_path: Path,
) -> None:
    fixture = json.loads(
        Path(
            "benchmarks/hash_based_toy_bound/fixtures/"
            "toy_hash_collision_32_fixture.json"
        ).read_text(encoding="utf-8")
    )
    fixture["right_message"] = "agades-hash-collision-v0:not-a-collision"
    out = tmp_path / "toy_hash_collision_32_fixture.json"
    out.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n")

    result = verify_toy_collision_fixture(out)

    assert result.verified is False


def test_hash_based_toy_collision_fixture_rejects_identical_messages(
    tmp_path: Path,
) -> None:
    fixture = json.loads(
        Path(
            "benchmarks/hash_based_toy_bound/fixtures/"
            "toy_hash_collision_32_fixture.json"
        ).read_text(encoding="utf-8")
    )
    fixture["right_message"] = fixture["left_message"]
    out = tmp_path / "toy_hash_collision_32_fixture.json"
    out.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n")

    with pytest.raises(ValueError, match="messages must be distinct"):
        verify_toy_collision_fixture(out)
