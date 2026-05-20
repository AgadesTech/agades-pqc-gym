from pathlib import Path

from agades_pqc_gym.families.code_based.hqc_fixture_decoder import (
    decode_toy_hqc_circulant_erasure_fixture,
    decode_toy_hqc_parity_check_fixture,
    decode_toy_hqc_repetition_fixture,
    decode_toy_hqc_weighted_repetition_fixture,
)


def test_toy_hqc_repetition_decoder_recovers_public_message_and_errors() -> None:
    result = decode_toy_hqc_repetition_fixture(
        Path(
            "benchmarks/code_based_toy_hqc/fixtures/"
            "toy_hqc_repetition_21_7_w3_fixture.json"
        )
    )

    assert result.decoded is True
    assert result.target_name == "toy_hqc_repetition_21_7_w3"
    assert result.decoded_message_bits == [1, 0, 1, 1, 0, 0, 1]
    assert result.error_positions == [2, 7, 16]
    assert result.checked_blocks == 7
    assert result.public is True
    assert result.security_claim is False


def test_toy_hqc_weighted_repetition_decoder_recovers_public_fixture() -> None:
    result = decode_toy_hqc_weighted_repetition_fixture(
        Path(
            "benchmarks/code_based_toy_hqc/fixtures/"
            "toy_hqc_weighted_repetition_25_5_w4_fixture.json"
        )
    )

    assert result.decoded is True
    assert result.target_name == "toy_hqc_weighted_repetition_25_5_w4"
    assert result.decoded_message_bits == [1, 0, 1, 1, 0]
    assert result.error_positions == [1, 6, 12, 17]
    assert result.checked_blocks == 5
    assert result.block_weight_margins == [10, 9, 9, 8, 11]
    assert result.public is True
    assert result.security_claim is False


def test_toy_hqc_parity_check_decoder_recovers_public_error_vector() -> None:
    result = decode_toy_hqc_parity_check_fixture(
        Path(
            "benchmarks/code_based_toy_hqc/fixtures/"
            "toy_hqc_parity_check_15_7_w2_fixture.json"
        )
    )

    assert result.decoded is True
    assert result.target_name == "toy_hqc_parity_check_15_7_w2"
    assert result.error_positions == [0, 1]
    assert result.corrected_codeword_bits == [0] * 15
    assert result.candidate_count == 105
    assert result.checked_syndrome_rows == 8
    assert result.public is True
    assert result.security_claim is False


def test_toy_hqc_circulant_erasure_decoder_recovers_public_fixture() -> None:
    result = decode_toy_hqc_circulant_erasure_fixture(
        Path(
            "benchmarks/code_based_toy_hqc/fixtures/"
            "toy_hqc_circulant_erasure_16_8_w3_fixture.json"
        )
    )

    assert result.decoded is True
    assert result.target_name == "toy_hqc_circulant_erasure_16_8_w3"
    assert result.block_size == 8
    assert result.first_block_error_positions == [1, 6]
    assert result.second_block_error_positions == [2]
    assert result.error_positions == [1, 6, 10]
    assert result.candidate_count == 20
    assert result.erasure_count == 6
    assert result.public is True
    assert result.security_claim is False
