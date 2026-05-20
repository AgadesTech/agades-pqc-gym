from __future__ import annotations

import math
from itertools import combinations
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_HQC_PARITY_CHECK_CANDIDATES = 100_000
MAX_HQC_CIRCULANT_CANDIDATES = 100_000
MAX_HQC_CIRCULANT_ERASURE_CANDIDATES = 100_000
MAX_HQC_ERASURE_SYNDROME_CANDIDATES = 100_000
MAX_HQC_WEIGHTED_REPETITION_RELIABILITY = 16


class ToyHQCRepetitionFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.code_based_toy_hqc_repetition.v1"]
    family: Literal["CODE_BASED"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    k: int = Field(gt=0)
    w: int = Field(gt=0)
    repetition_factor: int = Field(gt=0)
    received_bits: list[int] = Field(min_length=1)
    expected_message_bits: list[int] = Field(min_length=1)
    expected_error_positions: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> ToyHQCRepetitionFixture:
        if self.repetition_factor < 3 or self.repetition_factor % 2 == 0:
            raise ValueError(
                "toy HQC repetition fixture requires an odd "
                "repetition_factor >= 3"
            )
        if self.n != self.k * self.repetition_factor:
            raise ValueError(
                "toy HQC repetition fixture requires "
                "n == k * repetition_factor"
            )
        if len(self.received_bits) != self.n:
            raise ValueError("received_bits length must equal n")
        if len(self.expected_message_bits) != self.k:
            raise ValueError("expected_message_bits length must equal k")
        if len(self.expected_error_positions) != self.w:
            raise ValueError("expected_error_positions length must equal w")
        if sorted(set(self.expected_error_positions)) != self.expected_error_positions:
            raise ValueError("expected_error_positions must be sorted and unique")
        for position in self.expected_error_positions:
            if position < 0 or position >= self.n:
                raise ValueError("expected_error_positions must be in range [0, n)")
        if any(bit not in {0, 1} for bit in self.received_bits):
            raise ValueError("received_bits must be binary")
        if any(bit not in {0, 1} for bit in self.expected_message_bits):
            raise ValueError("expected_message_bits must be binary")
        return self


class ToyHQCRepetitionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decoded: bool
    target_name: str
    n: int
    k: int
    w: int
    repetition_factor: int
    checked_blocks: int
    decoded_message_bits: list[int]
    error_positions: list[int] | None
    error_vector_weight: int | None
    public: bool
    security_claim: bool


class ToyHQCWeightedRepetitionFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.code_based_toy_hqc_weighted_repetition.v1"]
    family: Literal["CODE_BASED"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    k: int = Field(gt=0)
    w: int = Field(gt=0)
    repetition_factor: int = Field(gt=0)
    received_bits: list[int] = Field(min_length=1)
    reliability_weights: list[int] = Field(min_length=1)
    expected_message_bits: list[int] = Field(min_length=1)
    expected_error_positions: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> ToyHQCWeightedRepetitionFixture:
        if self.repetition_factor < 3 or self.repetition_factor % 2 == 0:
            raise ValueError(
                "toy HQC weighted repetition fixture requires an odd "
                "repetition_factor >= 3"
            )
        if self.n != self.k * self.repetition_factor:
            raise ValueError(
                "toy HQC weighted repetition fixture requires "
                "n == k * repetition_factor"
            )
        if len(self.received_bits) != self.n:
            raise ValueError("received_bits length must equal n")
        if len(self.reliability_weights) != self.n:
            raise ValueError("reliability_weights length must equal n")
        if len(self.expected_message_bits) != self.k:
            raise ValueError("expected_message_bits length must equal k")
        if len(self.expected_error_positions) != self.w:
            raise ValueError("expected_error_positions length must equal w")
        if sorted(set(self.expected_error_positions)) != self.expected_error_positions:
            raise ValueError("expected_error_positions must be sorted and unique")
        for position in self.expected_error_positions:
            if position < 0 or position >= self.n:
                raise ValueError("expected_error_positions must be in range [0, n)")
        if any(bit not in {0, 1} for bit in self.received_bits):
            raise ValueError("received_bits must be binary")
        if any(bit not in {0, 1} for bit in self.expected_message_bits):
            raise ValueError("expected_message_bits must be binary")
        if any(
            weight < 1 or weight > MAX_HQC_WEIGHTED_REPETITION_RELIABILITY
            for weight in self.reliability_weights
        ):
            raise ValueError(
                "reliability_weights must be in range [1, "
                f"{MAX_HQC_WEIGHTED_REPETITION_RELIABILITY}]"
            )
        reconstructed = _repeat_message(
            self.expected_message_bits,
            repetition_factor=self.repetition_factor,
        )
        actual_error_positions = [
            index
            for index, (received_bit, expected_bit) in enumerate(
                zip(self.received_bits, reconstructed, strict=True)
            )
            if received_bit != expected_bit
        ]
        if actual_error_positions != self.expected_error_positions:
            raise ValueError("expected_error_positions must match received_bits")
        _, margins = _weighted_majority_decode(
            self.received_bits,
            self.reliability_weights,
            repetition_factor=self.repetition_factor,
        )
        if any(margin == 0 for margin in margins):
            raise ValueError("weighted repetition fixture must not contain ties")
        return self


class ToyHQCWeightedRepetitionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decoded: bool
    target_name: str
    n: int
    k: int
    w: int
    repetition_factor: int
    checked_blocks: int
    decoded_message_bits: list[int]
    error_positions: list[int] | None
    error_vector_weight: int | None
    block_weight_margins: list[int]
    total_reliability_weight: int
    public: bool
    security_claim: bool


class ToyHQCParityCheckFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.code_based_toy_hqc_parity_check.v1"]
    family: Literal["CODE_BASED"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    k: int = Field(gt=0)
    w: int = Field(gt=0)
    parity_check_matrix: list[list[int]] = Field(min_length=1)
    syndrome: list[int] = Field(min_length=1)
    received_bits: list[int] = Field(min_length=1)
    expected_codeword_bits: list[int] = Field(min_length=1)
    expected_error_positions: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> ToyHQCParityCheckFixture:
        if self.k >= self.n:
            raise ValueError("toy HQC parity-check fixture requires k < n")
        redundancy = self.n - self.k
        if self.w > redundancy:
            raise ValueError("toy HQC parity-check fixture requires w <= n-k")
        if len(self.parity_check_matrix) != redundancy:
            raise ValueError("parity_check_matrix row count must equal n-k")
        if len(self.syndrome) != redundancy:
            raise ValueError("syndrome length must equal n-k")
        if len(self.received_bits) != self.n:
            raise ValueError("received_bits length must equal n")
        if len(self.expected_codeword_bits) != self.n:
            raise ValueError("expected_codeword_bits length must equal n")
        _require_binary_vector(self.syndrome, name="syndrome")
        _require_binary_vector(self.received_bits, name="received_bits")
        _require_binary_vector(
            self.expected_codeword_bits,
            name="expected_codeword_bits",
        )
        for row in self.parity_check_matrix:
            if len(row) != self.n:
                raise ValueError("parity_check_matrix rows must have length n")
            _require_binary_vector(row, name="parity_check_matrix rows")
        if len(self.expected_error_positions) != self.w:
            raise ValueError("expected_error_positions length must equal w")
        if sorted(set(self.expected_error_positions)) != self.expected_error_positions:
            raise ValueError("expected_error_positions must be sorted and unique")
        for position in self.expected_error_positions:
            if position < 0 or position >= self.n:
                raise ValueError("expected_error_positions must be in range [0, n)")
        if (
            _syndrome_for_positions(
                self.parity_check_matrix,
                self.expected_error_positions,
            )
            != self.syndrome
        ):
            raise ValueError("expected_error_positions do not match syndrome")
        if _matrix_vector_product(
            self.parity_check_matrix,
            self.expected_codeword_bits,
        ) != [0] * redundancy:
            raise ValueError("expected_codeword_bits must have zero syndrome")
        if _matrix_vector_product(self.parity_check_matrix, self.received_bits) != (
            self.syndrome
        ):
            raise ValueError("received_bits syndrome must match syndrome")
        return self


class ToyHQCParityCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decoded: bool
    target_name: str
    n: int
    k: int
    w: int
    candidate_count: int
    checked_syndrome_rows: int
    error_positions: list[int] | None
    error_vector_weight: int | None
    corrected_codeword_bits: list[int] | None
    public: bool
    security_claim: bool


class ToyHQCCirculantSyndromeFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[
        "agades.pqc.code_based_toy_hqc_circulant_syndrome.v1"
    ]
    family: Literal["CODE_BASED"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    k: int = Field(gt=0)
    w: int = Field(gt=0)
    block_size: int = Field(gt=0)
    multiplier_bits: list[int] = Field(min_length=1)
    syndrome_bits: list[int] = Field(min_length=1)
    first_block_error_positions: list[int] = Field(default_factory=list)
    second_block_error_positions: list[int] = Field(default_factory=list)
    expected_error_positions: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> ToyHQCCirculantSyndromeFixture:
        if self.n != 2 * self.block_size:
            raise ValueError("toy HQC circulant fixture requires n == 2 * block_size")
        if self.k != self.block_size:
            raise ValueError("toy HQC circulant fixture requires k == block_size")
        if self.w > self.block_size:
            raise ValueError("toy HQC circulant fixture requires w <= block_size")
        if len(self.multiplier_bits) != self.block_size:
            raise ValueError("multiplier_bits length must equal block_size")
        if len(self.syndrome_bits) != self.block_size:
            raise ValueError("syndrome_bits length must equal block_size")
        _require_binary_vector(self.multiplier_bits, name="multiplier_bits")
        _require_binary_vector(self.syndrome_bits, name="syndrome_bits")
        if (
            len(self.first_block_error_positions)
            + len(self.second_block_error_positions)
            != self.w
        ):
            raise ValueError(
                "first and second block error positions must have total weight w"
            )
        expected_flattened = [
            *self.first_block_error_positions,
            *[
                self.block_size + position
                for position in self.second_block_error_positions
            ],
        ]
        if sorted(expected_flattened) != self.expected_error_positions:
            raise ValueError(
                "expected_error_positions must match flattened block positions"
            )
        _require_positions(
            self.first_block_error_positions,
            limit=self.block_size,
            name="first_block_error_positions",
        )
        _require_positions(
            self.second_block_error_positions,
            limit=self.block_size,
            name="second_block_error_positions",
        )
        _require_positions(
            self.expected_error_positions,
            limit=self.n,
            name="expected_error_positions",
        )
        if _circulant_syndrome(
            block_size=self.block_size,
            multiplier_bits=self.multiplier_bits,
            first_block_positions=self.first_block_error_positions,
            second_block_positions=self.second_block_error_positions,
        ) != self.syndrome_bits:
            raise ValueError("declared block error positions do not match syndrome")
        return self


class ToyHQCCirculantSyndromeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decoded: bool
    target_name: str
    n: int
    k: int
    w: int
    block_size: int
    candidate_count: int
    first_block_error_positions: list[int] | None
    second_block_error_positions: list[int] | None
    error_positions: list[int] | None
    error_vector_weight: int | None
    public: bool
    security_claim: bool


class ToyHQCCirculantErasureFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[
        "agades.pqc.code_based_toy_hqc_circulant_erasure.v1"
    ]
    family: Literal["CODE_BASED"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    k: int = Field(gt=0)
    w: int = Field(gt=0)
    block_size: int = Field(gt=0)
    multiplier_bits: list[int] = Field(min_length=1)
    syndrome_bits: list[int] = Field(min_length=1)
    first_block_erasure_positions: list[int] = Field(min_length=1)
    second_block_erasure_positions: list[int] = Field(min_length=1)
    first_block_error_positions: list[int] = Field(default_factory=list)
    second_block_error_positions: list[int] = Field(default_factory=list)
    expected_error_positions: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> ToyHQCCirculantErasureFixture:
        if self.n != 2 * self.block_size:
            raise ValueError(
                "toy HQC circulant-erasure fixture requires n == 2 * block_size"
            )
        if self.k != self.block_size:
            raise ValueError(
                "toy HQC circulant-erasure fixture requires k == block_size"
            )
        if len(self.multiplier_bits) != self.block_size:
            raise ValueError("multiplier_bits length must equal block_size")
        if len(self.syndrome_bits) != self.block_size:
            raise ValueError("syndrome_bits length must equal block_size")
        _require_binary_vector(self.multiplier_bits, name="multiplier_bits")
        _require_binary_vector(self.syndrome_bits, name="syndrome_bits")
        _require_positions(
            self.first_block_erasure_positions,
            limit=self.block_size,
            name="first_block_erasure_positions",
        )
        _require_positions(
            self.second_block_erasure_positions,
            limit=self.block_size,
            name="second_block_erasure_positions",
        )
        _require_positions(
            self.first_block_error_positions,
            limit=self.block_size,
            name="first_block_error_positions",
        )
        _require_positions(
            self.second_block_error_positions,
            limit=self.block_size,
            name="second_block_error_positions",
        )
        if not set(self.first_block_error_positions).issubset(
            self.first_block_erasure_positions
        ):
            raise ValueError(
                "first_block_error_positions must be within first block erasures"
            )
        if not set(self.second_block_error_positions).issubset(
            self.second_block_erasure_positions
        ):
            raise ValueError(
                "second_block_error_positions must be within second block erasures"
            )
        if (
            len(self.first_block_error_positions)
            + len(self.second_block_error_positions)
            != self.w
        ):
            raise ValueError(
                "first and second block error positions must have total weight w"
            )
        expected_flattened = [
            *self.first_block_error_positions,
            *[
                self.block_size + position
                for position in self.second_block_error_positions
            ],
        ]
        if sorted(expected_flattened) != self.expected_error_positions:
            raise ValueError(
                "expected_error_positions must match flattened block positions"
            )
        _require_positions(
            self.expected_error_positions,
            limit=self.n,
            name="expected_error_positions",
        )
        if (
            len(self.first_block_erasure_positions)
            + len(self.second_block_erasure_positions)
            < self.w
        ):
            raise ValueError(
                "circulant-erasure fixture requires total erasure count >= w"
            )
        if _circulant_syndrome(
            block_size=self.block_size,
            multiplier_bits=self.multiplier_bits,
            first_block_positions=self.first_block_error_positions,
            second_block_positions=self.second_block_error_positions,
        ) != self.syndrome_bits:
            raise ValueError("declared block error positions do not match syndrome")
        return self


class ToyHQCCirculantErasureResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decoded: bool
    target_name: str
    n: int
    k: int
    w: int
    block_size: int
    erasure_count: int
    candidate_count: int
    first_block_error_positions: list[int] | None
    second_block_error_positions: list[int] | None
    error_positions: list[int] | None
    error_vector_weight: int | None
    public: bool
    security_claim: bool


class ToyHQCErasureSyndromeFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[
        "agades.pqc.code_based_toy_hqc_erasure_syndrome.v1"
    ]
    family: Literal["CODE_BASED"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    k: int = Field(gt=0)
    w: int = Field(gt=0)
    parity_check_matrix: list[list[int]] = Field(min_length=1)
    syndrome: list[int] = Field(min_length=1)
    received_bits: list[int] = Field(min_length=1)
    expected_codeword_bits: list[int] = Field(min_length=1)
    erasure_positions: list[int] = Field(min_length=1)
    expected_error_positions: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> ToyHQCErasureSyndromeFixture:
        if self.k >= self.n:
            raise ValueError("toy HQC erasure fixture requires k < n")
        redundancy = self.n - self.k
        if self.w > redundancy:
            raise ValueError("toy HQC erasure fixture requires w <= n-k")
        if len(self.parity_check_matrix) != redundancy:
            raise ValueError("parity_check_matrix row count must equal n-k")
        if len(self.syndrome) != redundancy:
            raise ValueError("syndrome length must equal n-k")
        if len(self.received_bits) != self.n:
            raise ValueError("received_bits length must equal n")
        if len(self.expected_codeword_bits) != self.n:
            raise ValueError("expected_codeword_bits length must equal n")
        _require_binary_vector(self.syndrome, name="syndrome")
        _require_binary_vector(self.received_bits, name="received_bits")
        _require_binary_vector(
            self.expected_codeword_bits,
            name="expected_codeword_bits",
        )
        for row in self.parity_check_matrix:
            if len(row) != self.n:
                raise ValueError("parity_check_matrix rows must have length n")
            _require_binary_vector(row, name="parity_check_matrix rows")
        _require_positions(
            self.erasure_positions,
            limit=self.n,
            name="erasure_positions",
        )
        if len(self.erasure_positions) < self.w:
            raise ValueError("erasure_positions length must be at least w")
        _require_positions(
            self.expected_error_positions,
            limit=self.n,
            name="expected_error_positions",
        )
        if len(self.expected_error_positions) != self.w:
            raise ValueError("expected_error_positions length must equal w")
        if not set(self.expected_error_positions).issubset(self.erasure_positions):
            raise ValueError("expected_error_positions must be within erasures")
        if (
            _syndrome_for_positions(
                self.parity_check_matrix,
                self.expected_error_positions,
            )
            != self.syndrome
        ):
            raise ValueError("expected_error_positions do not match syndrome")
        if _matrix_vector_product(
            self.parity_check_matrix,
            self.expected_codeword_bits,
        ) != [0] * redundancy:
            raise ValueError("expected_codeword_bits must have zero syndrome")
        if _apply_error_positions(
            self.expected_codeword_bits,
            self.expected_error_positions,
        ) != self.received_bits:
            raise ValueError("received_bits must equal codeword plus error")
        if _matrix_vector_product(self.parity_check_matrix, self.received_bits) != (
            self.syndrome
        ):
            raise ValueError("received_bits syndrome must match syndrome")
        return self


class ToyHQCErasureSyndromeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decoded: bool
    target_name: str
    n: int
    k: int
    w: int
    erasure_count: int
    candidate_count: int
    checked_syndrome_rows: int
    error_positions: list[int] | None
    error_vector_weight: int | None
    corrected_codeword_bits: list[int] | None
    public: bool
    security_claim: bool


def decode_toy_hqc_repetition_fixture(path: Path) -> ToyHQCRepetitionResult:
    fixture = ToyHQCRepetitionFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    decoded_message_bits = _majority_decode(
        fixture.received_bits,
        repetition_factor=fixture.repetition_factor,
    )
    reconstructed = _repeat_message(
        decoded_message_bits,
        repetition_factor=fixture.repetition_factor,
    )
    error_positions = [
        index
        for index, (received_bit, decoded_bit) in enumerate(
            zip(fixture.received_bits, reconstructed, strict=True)
        )
        if received_bit != decoded_bit
    ]
    decoded = (
        decoded_message_bits == fixture.expected_message_bits
        and error_positions == fixture.expected_error_positions
    )

    return ToyHQCRepetitionResult(
        decoded=decoded,
        target_name=fixture.target_name,
        n=fixture.n,
        k=fixture.k,
        w=fixture.w,
        repetition_factor=fixture.repetition_factor,
        checked_blocks=fixture.k,
        decoded_message_bits=decoded_message_bits,
        error_positions=error_positions if decoded else None,
        error_vector_weight=len(error_positions) if decoded else None,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def decode_toy_hqc_weighted_repetition_fixture(
    path: Path,
) -> ToyHQCWeightedRepetitionResult:
    fixture = ToyHQCWeightedRepetitionFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    decoded_message_bits, block_weight_margins = _weighted_majority_decode(
        fixture.received_bits,
        fixture.reliability_weights,
        repetition_factor=fixture.repetition_factor,
    )
    reconstructed = _repeat_message(
        decoded_message_bits,
        repetition_factor=fixture.repetition_factor,
    )
    error_positions = [
        index
        for index, (received_bit, decoded_bit) in enumerate(
            zip(fixture.received_bits, reconstructed, strict=True)
        )
        if received_bit != decoded_bit
    ]
    decoded = (
        decoded_message_bits == fixture.expected_message_bits
        and error_positions == fixture.expected_error_positions
        and all(margin > 0 for margin in block_weight_margins)
    )

    return ToyHQCWeightedRepetitionResult(
        decoded=decoded,
        target_name=fixture.target_name,
        n=fixture.n,
        k=fixture.k,
        w=fixture.w,
        repetition_factor=fixture.repetition_factor,
        checked_blocks=fixture.k,
        decoded_message_bits=decoded_message_bits,
        error_positions=error_positions if decoded else None,
        error_vector_weight=len(error_positions) if decoded else None,
        block_weight_margins=block_weight_margins,
        total_reliability_weight=sum(fixture.reliability_weights),
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def decode_toy_hqc_parity_check_fixture(path: Path) -> ToyHQCParityCheckResult:
    fixture = ToyHQCParityCheckFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    candidate_count = math.comb(fixture.n, fixture.w)
    if candidate_count > MAX_HQC_PARITY_CHECK_CANDIDATES:
        raise ValueError(
            "toy HQC parity-check fixture exceeds bounded candidate limit: "
            f"{candidate_count} > {MAX_HQC_PARITY_CHECK_CANDIDATES}"
        )

    matching_positions: list[list[int]] = []
    for positions in combinations(range(fixture.n), fixture.w):
        candidate = list(positions)
        if (
            _syndrome_for_positions(fixture.parity_check_matrix, candidate)
            == fixture.syndrome
        ):
            matching_positions.append(candidate)
            if len(matching_positions) > 1:
                break

    decoded = False
    error_positions: list[int] | None = None
    corrected_codeword_bits: list[int] | None = None
    if len(matching_positions) == 1:
        candidate_error_positions = matching_positions[0]
        candidate_codeword = _apply_error_positions(
            fixture.received_bits,
            candidate_error_positions,
        )
        decoded = (
            candidate_error_positions == fixture.expected_error_positions
            and candidate_codeword == fixture.expected_codeword_bits
            and _matrix_vector_product(
                fixture.parity_check_matrix,
                candidate_codeword,
            )
            == [0] * (fixture.n - fixture.k)
        )
        if decoded:
            error_positions = candidate_error_positions
            corrected_codeword_bits = candidate_codeword

    return ToyHQCParityCheckResult(
        decoded=decoded,
        target_name=fixture.target_name,
        n=fixture.n,
        k=fixture.k,
        w=fixture.w,
        candidate_count=candidate_count,
        checked_syndrome_rows=fixture.n - fixture.k,
        error_positions=error_positions,
        error_vector_weight=len(error_positions) if error_positions else None,
        corrected_codeword_bits=corrected_codeword_bits,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def decode_toy_hqc_circulant_syndrome_fixture(
    path: Path,
) -> ToyHQCCirculantSyndromeResult:
    fixture = ToyHQCCirculantSyndromeFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    candidate_count = _hqc_circulant_candidate_count(
        block_size=fixture.block_size,
        weight=fixture.w,
    )
    if candidate_count > MAX_HQC_CIRCULANT_CANDIDATES:
        raise ValueError(
            "toy HQC circulant fixture exceeds bounded candidate limit: "
            f"{candidate_count} > {MAX_HQC_CIRCULANT_CANDIDATES}"
        )

    matching_positions: list[tuple[list[int], list[int]]] = []
    for first_weight in range(fixture.w + 1):
        second_weight = fixture.w - first_weight
        for first_positions_tuple in combinations(
            range(fixture.block_size),
            first_weight,
        ):
            first_positions = list(first_positions_tuple)
            for second_positions_tuple in combinations(
                range(fixture.block_size),
                second_weight,
            ):
                second_positions = list(second_positions_tuple)
                if (
                    _circulant_syndrome(
                        block_size=fixture.block_size,
                        multiplier_bits=fixture.multiplier_bits,
                        first_block_positions=first_positions,
                        second_block_positions=second_positions,
                    )
                    == fixture.syndrome_bits
                ):
                    matching_positions.append((first_positions, second_positions))
                    if len(matching_positions) > 1:
                        break
            if len(matching_positions) > 1:
                break
        if len(matching_positions) > 1:
            break

    first_block_error_positions: list[int] | None = None
    second_block_error_positions: list[int] | None = None
    error_positions: list[int] | None = None
    decoded = False
    if len(matching_positions) == 1:
        first_block_error_positions, second_block_error_positions = (
            matching_positions[0]
        )
        error_positions = [
            *first_block_error_positions,
            *[
                fixture.block_size + position
                for position in second_block_error_positions
            ],
        ]
        decoded = (
            first_block_error_positions == fixture.first_block_error_positions
            and second_block_error_positions == fixture.second_block_error_positions
            and error_positions == fixture.expected_error_positions
        )

    return ToyHQCCirculantSyndromeResult(
        decoded=decoded,
        target_name=fixture.target_name,
        n=fixture.n,
        k=fixture.k,
        w=fixture.w,
        block_size=fixture.block_size,
        candidate_count=candidate_count,
        first_block_error_positions=(
            first_block_error_positions if decoded else None
        ),
        second_block_error_positions=(
            second_block_error_positions if decoded else None
        ),
        error_positions=error_positions if decoded else None,
        error_vector_weight=(
            len(error_positions) if decoded and error_positions else None
        ),
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def decode_toy_hqc_circulant_erasure_fixture(
    path: Path,
) -> ToyHQCCirculantErasureResult:
    fixture = ToyHQCCirculantErasureFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    candidate_count = _hqc_circulant_erasure_candidate_count(
        first_block_erasure_count=len(fixture.first_block_erasure_positions),
        second_block_erasure_count=len(fixture.second_block_erasure_positions),
        weight=fixture.w,
    )
    if candidate_count > MAX_HQC_CIRCULANT_ERASURE_CANDIDATES:
        raise ValueError(
            "toy HQC circulant-erasure fixture exceeds bounded candidate limit: "
            f"{candidate_count} > {MAX_HQC_CIRCULANT_ERASURE_CANDIDATES}"
        )

    matching_positions: list[tuple[list[int], list[int]]] = []
    for first_weight in range(
        max(0, fixture.w - len(fixture.second_block_erasure_positions)),
        min(fixture.w, len(fixture.first_block_erasure_positions)) + 1,
    ):
        second_weight = fixture.w - first_weight
        for first_positions_tuple in combinations(
            fixture.first_block_erasure_positions,
            first_weight,
        ):
            first_positions = list(first_positions_tuple)
            for second_positions_tuple in combinations(
                fixture.second_block_erasure_positions,
                second_weight,
            ):
                second_positions = list(second_positions_tuple)
                if (
                    _circulant_syndrome(
                        block_size=fixture.block_size,
                        multiplier_bits=fixture.multiplier_bits,
                        first_block_positions=first_positions,
                        second_block_positions=second_positions,
                    )
                    == fixture.syndrome_bits
                ):
                    matching_positions.append((first_positions, second_positions))
                    if len(matching_positions) > 1:
                        break
            if len(matching_positions) > 1:
                break
        if len(matching_positions) > 1:
            break

    first_block_error_positions: list[int] | None = None
    second_block_error_positions: list[int] | None = None
    error_positions: list[int] | None = None
    decoded = False
    if len(matching_positions) == 1:
        first_block_error_positions, second_block_error_positions = (
            matching_positions[0]
        )
        error_positions = [
            *first_block_error_positions,
            *[
                fixture.block_size + position
                for position in second_block_error_positions
            ],
        ]
        decoded = (
            first_block_error_positions == fixture.first_block_error_positions
            and second_block_error_positions == fixture.second_block_error_positions
            and error_positions == fixture.expected_error_positions
        )

    return ToyHQCCirculantErasureResult(
        decoded=decoded,
        target_name=fixture.target_name,
        n=fixture.n,
        k=fixture.k,
        w=fixture.w,
        block_size=fixture.block_size,
        erasure_count=(
            len(fixture.first_block_erasure_positions)
            + len(fixture.second_block_erasure_positions)
        ),
        candidate_count=candidate_count,
        first_block_error_positions=(
            first_block_error_positions if decoded else None
        ),
        second_block_error_positions=(
            second_block_error_positions if decoded else None
        ),
        error_positions=error_positions if decoded else None,
        error_vector_weight=(
            len(error_positions) if decoded and error_positions else None
        ),
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def decode_toy_hqc_erasure_syndrome_fixture(
    path: Path,
) -> ToyHQCErasureSyndromeResult:
    fixture = ToyHQCErasureSyndromeFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    candidate_count = math.comb(len(fixture.erasure_positions), fixture.w)
    if candidate_count > MAX_HQC_ERASURE_SYNDROME_CANDIDATES:
        raise ValueError(
            "toy HQC erasure fixture exceeds bounded candidate limit: "
            f"{candidate_count} > {MAX_HQC_ERASURE_SYNDROME_CANDIDATES}"
        )

    matching_positions: list[list[int]] = []
    for positions in combinations(fixture.erasure_positions, fixture.w):
        candidate = list(positions)
        if (
            _syndrome_for_positions(fixture.parity_check_matrix, candidate)
            == fixture.syndrome
        ):
            matching_positions.append(candidate)
            if len(matching_positions) > 1:
                break

    decoded = False
    error_positions: list[int] | None = None
    corrected_codeword_bits: list[int] | None = None
    if len(matching_positions) == 1:
        candidate_error_positions = matching_positions[0]
        candidate_codeword = _apply_error_positions(
            fixture.received_bits,
            candidate_error_positions,
        )
        decoded = (
            candidate_error_positions == fixture.expected_error_positions
            and candidate_codeword == fixture.expected_codeword_bits
            and _matrix_vector_product(
                fixture.parity_check_matrix,
                candidate_codeword,
            )
            == [0] * (fixture.n - fixture.k)
        )
        if decoded:
            error_positions = candidate_error_positions
            corrected_codeword_bits = candidate_codeword

    return ToyHQCErasureSyndromeResult(
        decoded=decoded,
        target_name=fixture.target_name,
        n=fixture.n,
        k=fixture.k,
        w=fixture.w,
        erasure_count=len(fixture.erasure_positions),
        candidate_count=candidate_count,
        checked_syndrome_rows=fixture.n - fixture.k,
        error_positions=error_positions,
        error_vector_weight=len(error_positions) if error_positions else None,
        corrected_codeword_bits=corrected_codeword_bits,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def _majority_decode(bits: list[int], *, repetition_factor: int) -> list[int]:
    decoded = []
    threshold = repetition_factor // 2
    for offset in range(0, len(bits), repetition_factor):
        block = bits[offset : offset + repetition_factor]
        decoded.append(1 if sum(block) > threshold else 0)
    return decoded


def _weighted_majority_decode(
    bits: list[int],
    weights: list[int],
    *,
    repetition_factor: int,
) -> tuple[list[int], list[int]]:
    decoded: list[int] = []
    margins: list[int] = []
    for offset in range(0, len(bits), repetition_factor):
        block = bits[offset : offset + repetition_factor]
        block_weights = weights[offset : offset + repetition_factor]
        one_weight = sum(
            weight for bit, weight in zip(block, block_weights, strict=True) if bit
        )
        zero_weight = sum(block_weights) - one_weight
        decoded.append(1 if one_weight > zero_weight else 0)
        margins.append(abs(one_weight - zero_weight))
    return decoded, margins


def _repeat_message(bits: list[int], *, repetition_factor: int) -> list[int]:
    repeated = []
    for bit in bits:
        repeated.extend([bit] * repetition_factor)
    return repeated


def _require_binary_vector(bits: list[int], *, name: str) -> None:
    if any(bit not in {0, 1} for bit in bits):
        raise ValueError(f"{name} must be binary")


def _require_positions(positions: list[int], *, limit: int, name: str) -> None:
    if sorted(set(positions)) != positions:
        raise ValueError(f"{name} must be sorted and unique")
    for position in positions:
        if position < 0 or position >= limit:
            raise ValueError(f"{name} must be in range [0, {limit})")


def _syndrome_for_positions(
    parity_check_matrix: list[list[int]],
    positions: list[int],
) -> list[int]:
    syndrome = []
    for row in parity_check_matrix:
        value = 0
        for position in positions:
            value ^= row[position]
        syndrome.append(value)
    return syndrome


def _matrix_vector_product(
    parity_check_matrix: list[list[int]],
    vector: list[int],
) -> list[int]:
    product = []
    for row in parity_check_matrix:
        value = 0
        for row_bit, vector_bit in zip(row, vector, strict=True):
            value ^= row_bit & vector_bit
        product.append(value)
    return product


def _apply_error_positions(bits: list[int], positions: list[int]) -> list[int]:
    corrected = list(bits)
    for position in positions:
        corrected[position] ^= 1
    return corrected


def _hqc_circulant_candidate_count(*, block_size: int, weight: int) -> int:
    return sum(
        math.comb(block_size, first_weight)
        * math.comb(block_size, weight - first_weight)
        for first_weight in range(weight + 1)
    )


def _hqc_circulant_erasure_candidate_count(
    *,
    first_block_erasure_count: int,
    second_block_erasure_count: int,
    weight: int,
) -> int:
    return sum(
        math.comb(first_block_erasure_count, first_weight)
        * math.comb(second_block_erasure_count, weight - first_weight)
        for first_weight in range(
            max(0, weight - second_block_erasure_count),
            min(weight, first_block_erasure_count) + 1,
        )
    )


def _circulant_syndrome(
    *,
    block_size: int,
    multiplier_bits: list[int],
    first_block_positions: list[int],
    second_block_positions: list[int],
) -> list[int]:
    syndrome = [0] * block_size
    for position in first_block_positions:
        syndrome[position] ^= 1
    for position in second_block_positions:
        for offset, multiplier_bit in enumerate(multiplier_bits):
            if multiplier_bit:
                syndrome[(position + offset) % block_size] ^= 1
    return syndrome
