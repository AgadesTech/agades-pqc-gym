from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ToyMDPCBitFlipFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.code_based_toy_mdpc_bit_flip.v1"]
    family: Literal["CODE_BASED"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    k: int = Field(gt=0)
    w: int = Field(gt=0)
    threshold: int = Field(gt=0)
    max_iterations: int = Field(gt=0, le=32)
    parity_check_matrix: list[list[int]] = Field(min_length=1)
    received_bits: list[int] = Field(min_length=1)
    expected_codeword_bits: list[int] = Field(min_length=1)
    expected_error_positions: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> ToyMDPCBitFlipFixture:
        if self.k >= self.n:
            raise ValueError("toy MDPC bit-flip fixture requires k < n")
        redundancy = self.n - self.k
        if len(self.parity_check_matrix) != redundancy:
            raise ValueError("parity_check_matrix row count must equal n-k")
        if self.threshold > redundancy:
            raise ValueError("threshold must be at most n-k")
        if len(self.received_bits) != self.n:
            raise ValueError("received_bits length must equal n")
        if len(self.expected_codeword_bits) != self.n:
            raise ValueError("expected_codeword_bits length must equal n")
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
        if _matrix_vector_product(
            self.parity_check_matrix,
            self.expected_codeword_bits,
        ) != [0] * redundancy:
            raise ValueError("expected_codeword_bits must have zero syndrome")
        expected_received = _apply_error_positions(
            self.expected_codeword_bits,
            self.expected_error_positions,
        )
        if expected_received != self.received_bits:
            raise ValueError(
                "received_bits must equal expected_codeword_bits plus expected "
                "error positions"
            )
        return self


class ToyMDPCBlackGrayBitFlipFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.code_based_toy_mdpc_black_gray_bit_flip.v1"]
    family: Literal["CODE_BASED"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    k: int = Field(gt=0)
    w: int = Field(gt=0)
    black_threshold: int = Field(gt=0)
    gray_threshold: int = Field(gt=0)
    max_iterations: int = Field(gt=0, le=32)
    parity_check_matrix: list[list[int]] = Field(min_length=1)
    received_bits: list[int] = Field(min_length=1)
    expected_codeword_bits: list[int] = Field(min_length=1)
    expected_error_positions: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> ToyMDPCBlackGrayBitFlipFixture:
        if self.k >= self.n:
            raise ValueError("toy MDPC black-gray fixture requires k < n")
        redundancy = self.n - self.k
        if len(self.parity_check_matrix) != redundancy:
            raise ValueError("parity_check_matrix row count must equal n-k")
        if self.gray_threshold > self.black_threshold:
            raise ValueError("gray_threshold must be at most black_threshold")
        if self.black_threshold > redundancy:
            raise ValueError("black_threshold must be at most n-k")
        if len(self.received_bits) != self.n:
            raise ValueError("received_bits length must equal n")
        if len(self.expected_codeword_bits) != self.n:
            raise ValueError("expected_codeword_bits length must equal n")
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
        if _matrix_vector_product(
            self.parity_check_matrix,
            self.expected_codeword_bits,
        ) != [0] * redundancy:
            raise ValueError("expected_codeword_bits must have zero syndrome")
        expected_received = _apply_error_positions(
            self.expected_codeword_bits,
            self.expected_error_positions,
        )
        if expected_received != self.received_bits:
            raise ValueError(
                "received_bits must equal expected_codeword_bits plus expected "
                "error positions"
            )
        return self


class ToyMDPCSyndromeWeightBitFlipFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[
        "agades.pqc.code_based_toy_mdpc_syndrome_weight_bit_flip.v1"
    ]
    family: Literal["CODE_BASED"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    k: int = Field(gt=0)
    w: int = Field(gt=0)
    min_syndrome_weight_drop: int = Field(gt=0)
    max_iterations: int = Field(gt=0, le=32)
    parity_check_matrix: list[list[int]] = Field(min_length=1)
    received_bits: list[int] = Field(min_length=1)
    expected_codeword_bits: list[int] = Field(min_length=1)
    expected_error_positions: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> ToyMDPCSyndromeWeightBitFlipFixture:
        if self.k >= self.n:
            raise ValueError("toy MDPC syndrome-weight fixture requires k < n")
        redundancy = self.n - self.k
        if len(self.parity_check_matrix) != redundancy:
            raise ValueError("parity_check_matrix row count must equal n-k")
        if len(self.received_bits) != self.n:
            raise ValueError("received_bits length must equal n")
        if len(self.expected_codeword_bits) != self.n:
            raise ValueError("expected_codeword_bits length must equal n")
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
        if _matrix_vector_product(
            self.parity_check_matrix,
            self.expected_codeword_bits,
        ) != [0] * redundancy:
            raise ValueError("expected_codeword_bits must have zero syndrome")
        expected_received = _apply_error_positions(
            self.expected_codeword_bits,
            self.expected_error_positions,
        )
        if expected_received != self.received_bits:
            raise ValueError(
                "received_bits must equal expected_codeword_bits plus expected "
                "error positions"
            )
        return self


class ToyMDPCBitFlipResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decoded: bool
    target_name: str
    n: int
    k: int
    w: int
    threshold: int
    max_iterations: int
    iterations: int
    recovered_error_positions: list[int] | None
    corrected_codeword_bits: list[int] | None
    public: bool
    security_claim: bool


class ToyMDPCBlackGrayBitFlipResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decoded: bool
    target_name: str
    n: int
    k: int
    w: int
    black_threshold: int
    gray_threshold: int
    max_iterations: int
    iterations: int
    black_flips: int
    gray_flips: int
    recovered_error_positions: list[int] | None
    corrected_codeword_bits: list[int] | None
    public: bool
    security_claim: bool


class ToyMDPCSyndromeWeightBitFlipResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decoded: bool
    target_name: str
    n: int
    k: int
    w: int
    min_syndrome_weight_drop: int
    max_iterations: int
    iterations: int
    syndrome_weights: list[int]
    recovered_error_positions: list[int] | None
    corrected_codeword_bits: list[int] | None
    public: bool
    security_claim: bool


def decode_toy_mdpc_bit_flip_fixture(path: Path) -> ToyMDPCBitFlipResult:
    fixture = ToyMDPCBitFlipFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    current = list(fixture.received_bits)
    iterations = 0
    for iteration in range(1, fixture.max_iterations + 1):
        syndrome = _matrix_vector_product(fixture.parity_check_matrix, current)
        if syndrome == [0] * (fixture.n - fixture.k):
            iterations = iteration - 1
            break
        unsatisfied_counts = _unsatisfied_counts(
            fixture.parity_check_matrix,
            syndrome,
        )
        flip_positions = [
            position
            for position, count in enumerate(unsatisfied_counts)
            if count >= fixture.threshold
        ]
        iterations = iteration
        if not flip_positions:
            break
        current = _apply_error_positions(current, flip_positions)
    else:
        syndrome = _matrix_vector_product(fixture.parity_check_matrix, current)

    corrected_codeword = current
    recovered_error_positions = [
        position
        for position, (received_bit, corrected_bit) in enumerate(
            zip(fixture.received_bits, corrected_codeword, strict=True)
        )
        if received_bit != corrected_bit
    ]
    decoded = (
        _matrix_vector_product(fixture.parity_check_matrix, corrected_codeword)
        == [0] * (fixture.n - fixture.k)
        and corrected_codeword == fixture.expected_codeword_bits
        and recovered_error_positions == fixture.expected_error_positions
    )

    return ToyMDPCBitFlipResult(
        decoded=decoded,
        target_name=fixture.target_name,
        n=fixture.n,
        k=fixture.k,
        w=fixture.w,
        threshold=fixture.threshold,
        max_iterations=fixture.max_iterations,
        iterations=iterations,
        recovered_error_positions=recovered_error_positions if decoded else None,
        corrected_codeword_bits=corrected_codeword if decoded else None,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def decode_toy_mdpc_syndrome_weight_fixture(
    path: Path,
) -> ToyMDPCSyndromeWeightBitFlipResult:
    fixture = ToyMDPCSyndromeWeightBitFlipFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    current = list(fixture.received_bits)
    syndrome_weights: list[int] = []
    iterations = 0
    for iteration in range(1, fixture.max_iterations + 1):
        syndrome = _matrix_vector_product(fixture.parity_check_matrix, current)
        syndrome_weight = sum(syndrome)
        syndrome_weights.append(syndrome_weight)
        if syndrome_weight == 0:
            iterations = iteration - 1
            break
        best_position: int | None = None
        best_drop = 0
        for position in range(fixture.n):
            candidate = _apply_error_positions(current, [position])
            candidate_weight = sum(
                _matrix_vector_product(fixture.parity_check_matrix, candidate)
            )
            drop = syndrome_weight - candidate_weight
            if drop > best_drop:
                best_drop = drop
                best_position = position
        iterations = iteration
        if (
            best_position is None
            or best_drop < fixture.min_syndrome_weight_drop
        ):
            break
        current = _apply_error_positions(current, [best_position])
    else:
        syndrome_weights.append(
            sum(_matrix_vector_product(fixture.parity_check_matrix, current))
        )

    corrected_codeword = current
    recovered_error_positions = [
        position
        for position, (received_bit, corrected_bit) in enumerate(
            zip(fixture.received_bits, corrected_codeword, strict=True)
        )
        if received_bit != corrected_bit
    ]
    decoded = (
        _matrix_vector_product(fixture.parity_check_matrix, corrected_codeword)
        == [0] * (fixture.n - fixture.k)
        and corrected_codeword == fixture.expected_codeword_bits
        and recovered_error_positions == fixture.expected_error_positions
    )

    return ToyMDPCSyndromeWeightBitFlipResult(
        decoded=decoded,
        target_name=fixture.target_name,
        n=fixture.n,
        k=fixture.k,
        w=fixture.w,
        min_syndrome_weight_drop=fixture.min_syndrome_weight_drop,
        max_iterations=fixture.max_iterations,
        iterations=iterations,
        syndrome_weights=syndrome_weights,
        recovered_error_positions=recovered_error_positions if decoded else None,
        corrected_codeword_bits=corrected_codeword if decoded else None,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def decode_toy_mdpc_black_gray_fixture(
    path: Path,
) -> ToyMDPCBlackGrayBitFlipResult:
    fixture = ToyMDPCBlackGrayBitFlipFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    current = list(fixture.received_bits)
    iterations = 0
    black_flips = 0
    gray_flips = 0
    for iteration in range(1, fixture.max_iterations + 1):
        syndrome = _matrix_vector_product(fixture.parity_check_matrix, current)
        if syndrome == [0] * (fixture.n - fixture.k):
            iterations = iteration - 1
            break
        unsatisfied_counts = _unsatisfied_counts(
            fixture.parity_check_matrix,
            syndrome,
        )
        flips = {
            position
            for position, count in enumerate(unsatisfied_counts)
            if count >= fixture.black_threshold
        }
        base_syndrome_weight = sum(syndrome)
        for position, count in enumerate(unsatisfied_counts):
            if position in flips:
                continue
            if not fixture.gray_threshold <= count < fixture.black_threshold:
                continue
            candidate = _apply_error_positions(current, [position])
            candidate_syndrome_weight = sum(
                _matrix_vector_product(fixture.parity_check_matrix, candidate)
            )
            if candidate_syndrome_weight < base_syndrome_weight:
                flips.add(position)
                gray_flips += 1
        iterations = iteration
        if not flips:
            break
        black_flips += sum(
            1
            for position in flips
            if unsatisfied_counts[position] >= fixture.black_threshold
        )
        current = _apply_error_positions(current, sorted(flips))

    corrected_codeword = current
    recovered_error_positions = [
        position
        for position, (received_bit, corrected_bit) in enumerate(
            zip(fixture.received_bits, corrected_codeword, strict=True)
        )
        if received_bit != corrected_bit
    ]
    decoded = (
        _matrix_vector_product(fixture.parity_check_matrix, corrected_codeword)
        == [0] * (fixture.n - fixture.k)
        and corrected_codeword == fixture.expected_codeword_bits
        and recovered_error_positions == fixture.expected_error_positions
    )

    return ToyMDPCBlackGrayBitFlipResult(
        decoded=decoded,
        target_name=fixture.target_name,
        n=fixture.n,
        k=fixture.k,
        w=fixture.w,
        black_threshold=fixture.black_threshold,
        gray_threshold=fixture.gray_threshold,
        max_iterations=fixture.max_iterations,
        iterations=iterations,
        black_flips=black_flips,
        gray_flips=gray_flips,
        recovered_error_positions=recovered_error_positions if decoded else None,
        corrected_codeword_bits=corrected_codeword if decoded else None,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def _unsatisfied_counts(
    parity_check_matrix: list[list[int]],
    syndrome: list[int],
) -> list[int]:
    counts = [0] * len(parity_check_matrix[0])
    for row, syndrome_bit in zip(parity_check_matrix, syndrome, strict=True):
        if syndrome_bit == 0:
            continue
        for position, row_bit in enumerate(row):
            if row_bit:
                counts[position] += 1
    return counts


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


def _require_binary_vector(bits: list[int], *, name: str) -> None:
    if any(bit not in {0, 1} for bit in bits):
        raise ValueError(f"{name} must be binary")
