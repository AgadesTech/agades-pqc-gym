from __future__ import annotations

from pathlib import Path

from agades_pqc_gym.families.hash_based import signature_fixture


def test_hash_based_toy_signature_fixture_verifies_public_chain() -> None:
    result = signature_fixture.verify_toy_signature_chain_fixture(
        Path(
            "benchmarks/hash_based_toy_signature/fixtures/"
            "toy_hash_signature_chain_24_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_hash_signature_chain_24"
    assert result.digest_bits == 24
    assert result.hash_function == "SHAKE256"
    assert result.chain_count == 4
    assert result.max_chain_steps == 8
    assert result.verified_chains == 4
    assert result.public is True
    assert result.security_claim is False


def test_hash_based_toy_signature_packaged_fixture_mirrors_benchmark_fixture() -> None:
    benchmark_fixture = Path(
        "benchmarks/hash_based_toy_signature/fixtures/"
        "toy_hash_signature_chain_24_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/hash_based/fixtures/"
        "toy_hash_signature_chain_24_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()


def test_hash_based_toy_merkle_auth_path_fixture_verifies_public_path() -> None:
    result = signature_fixture.verify_toy_merkle_auth_path_fixture(
        Path(
            "benchmarks/hash_based_toy_signature/fixtures/"
            "toy_hash_merkle_auth_path_24_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_hash_merkle_auth_path_24"
    assert result.digest_bits == 24
    assert result.hash_function == "SHAKE256"
    assert result.signature_model == "toy_merkle_auth_path_verify"
    assert result.tree_height == 3
    assert result.leaf_index == 5
    assert result.public is True
    assert result.security_claim is False


def test_hash_based_toy_merkle_packaged_fixture_mirrors_benchmark_fixture() -> None:
    benchmark_fixture = Path(
        "benchmarks/hash_based_toy_signature/fixtures/"
        "toy_hash_merkle_auth_path_24_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/hash_based/fixtures/"
        "toy_hash_merkle_auth_path_24_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()


def test_hash_based_toy_slh_dsa_hypertree_fixture_verifies_public_signature() -> None:
    result = signature_fixture.verify_toy_slh_dsa_hypertree_fixture(
        Path(
            "benchmarks/hash_based_toy_signature/fixtures/"
            "toy_hash_slh_dsa_hypertree_24_fixture.json"
        )
    )

    assert result.verified is True
    assert result.target_name == "toy_hash_slh_dsa_hypertree_24"
    assert result.digest_bits == 24
    assert result.hash_function == "SHAKE256"
    assert result.signature_model == "toy_slh_dsa_hypertree_verify"
    assert result.fors_tree_count == 2
    assert result.fors_tree_height == 2
    assert result.fors_selected_indices == [1, 2]
    assert result.wots_chain_count == 4
    assert result.wots_max_chain_steps == 8
    assert result.hypertree_height == 3
    assert result.hypertree_leaf_index == 5
    assert result.public is True
    assert result.security_claim is False


def test_hash_based_toy_slh_dsa_packaged_fixture_mirrors_benchmark_fixture() -> None:
    benchmark_fixture = Path(
        "benchmarks/hash_based_toy_signature/fixtures/"
        "toy_hash_slh_dsa_hypertree_24_fixture.json"
    )
    package_fixture = Path(
        "src/agades_pqc_gym/families/hash_based/fixtures/"
        "toy_hash_slh_dsa_hypertree_24_fixture.json"
    )

    assert package_fixture.read_bytes() == benchmark_fixture.read_bytes()
