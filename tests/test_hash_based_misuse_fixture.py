from pathlib import Path

from agades_pqc_gym.families.hash_based.misuse_fixture import (
    verify_toy_hash_misuse_fixture,
)


def test_toy_hash_misuse_fixture_detects_reused_public_salt() -> None:
    result = verify_toy_hash_misuse_fixture(
        Path(
            "benchmarks/hash_based_toy_misuse/fixtures/"
            "toy_hash_reused_salt_24_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_hash_reused_salt_24"
    assert result.hash_function == "SHAKE256"
    assert result.digest_bits == 24
    assert result.misuse_model == "toy_hash_reused_salt"
    assert result.record_count == 4
    assert result.salt_bytes == 3
    assert result.issue_count == 1
    assert result.reused_salts == ["001122"]
    assert result.public is True
    assert result.security_claim is False
