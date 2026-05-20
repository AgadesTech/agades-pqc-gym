from __future__ import annotations

from pathlib import Path

from agades_pqc_gym.families.implementation_security.kat_fixture import (
    verify_toy_acvp_fixture,
    verify_toy_kat_fixture,
)


def test_implementation_security_toy_kat_fixture_verifies_public_digest() -> None:
    result = verify_toy_kat_fixture(
        Path(
            "benchmarks/implementation_security_toy_kat/fixtures/"
            "toy_mlkem_kat_digest_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_mlkem_kat_digest"
    assert result.suite == "toy_mlkem_kat"
    assert result.model == "toy_kat_digest_match"
    assert result.payload_sha256 == (
        "42b4b222b2c3dee6b453babe2ea401606b24032174d9ed734d2de31c0097cba8"
    )
    assert result.expected_sha256 == result.payload_sha256
    assert result.vector_count == 2
    assert result.artifact_execution is False
    assert result.public is True
    assert result.security_claim is False


def test_implementation_security_kat_packaged_fixture_mirror() -> None:
    benchmark_fixture = Path(
        "benchmarks/implementation_security_toy_kat/fixtures/"
        "toy_mlkem_kat_digest_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/implementation_security/fixtures/"
        "toy_mlkem_kat_digest_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()


def test_implementation_security_toy_acvp_fixture_verifies_public_vector_set() -> None:
    result = verify_toy_acvp_fixture(
        Path(
            "benchmarks/implementation_security_toy_kat/fixtures/"
            "toy_acvp_mlkem_vector_set_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_acvp_mlkem_vector_set"
    assert result.suite == "toy_acvp_mlkem_encap"
    assert result.model == "toy_acvp_vector_set_match"
    assert result.algorithm == "ML-KEM"
    assert result.mode == "encapsulation"
    assert result.test_group_count == 1
    assert result.test_count == 2
    assert result.vector_set_sha256 == result.expected_vector_set_sha256
    assert result.artifact_execution is False
    assert result.public is True
    assert result.security_claim is False
