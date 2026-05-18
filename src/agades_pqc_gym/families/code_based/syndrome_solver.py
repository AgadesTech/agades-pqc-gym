from __future__ import annotations

import math
from itertools import combinations
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_SYNDROME_CANDIDATES = 100_000


class ToySyndromeFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.code_based_toy_syndrome.v1"]
    family: Literal["CODE_BASED"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    k: int = Field(gt=0)
    w: int = Field(gt=0)
    parity_check_matrix: list[list[int]] = Field(min_length=1)
    syndrome: list[int] = Field(min_length=1)
    expected_error_positions: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> ToySyndromeFixture:
        redundancy = self.n - self.k
        if redundancy <= 0:
            raise ValueError("toy syndrome fixture requires k < n")
        if len(self.parity_check_matrix) != redundancy:
            raise ValueError("parity_check_matrix row count must equal n-k")
        if len(self.syndrome) != redundancy:
            raise ValueError("syndrome length must equal n-k")
        if len(self.expected_error_positions) != self.w:
            raise ValueError("expected_error_positions length must equal w")
        if sorted(set(self.expected_error_positions)) != self.expected_error_positions:
            raise ValueError("expected_error_positions must be sorted and unique")
        for position in self.expected_error_positions:
            if position < 0 or position >= self.n:
                raise ValueError("expected_error_positions must be in range [0, n)")
        for row in self.parity_check_matrix:
            if len(row) != self.n:
                raise ValueError("each parity_check_matrix row length must equal n")
            if any(bit not in {0, 1} for bit in row):
                raise ValueError("parity_check_matrix must be binary")
        if any(bit not in {0, 1} for bit in self.syndrome):
            raise ValueError("syndrome must be binary")
        return self


class ToySyndromeSolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solved: bool
    target_name: str
    n: int
    k: int
    w: int
    candidate_count: int
    error_positions: list[int] | None
    error_vector_weight: int | None
    public: bool
    security_claim: bool


class ToyQCRotationFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.code_based_toy_qc_rotation.v1"]
    family: Literal["CODE_BASED"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    k: int = Field(gt=0)
    w: int = Field(gt=0)
    block_size: int = Field(gt=0)
    block_count: int = Field(gt=0)
    parity_check_matrix: list[list[int]] = Field(min_length=1)
    syndrome: list[int] = Field(min_length=1)
    base_error_positions: list[int] = Field(min_length=1)
    expected_rotation: int = Field(ge=0)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> ToyQCRotationFixture:
        redundancy = self.n - self.k
        if redundancy <= 0:
            raise ValueError("toy QC rotation fixture requires k < n")
        if self.n != self.block_size * self.block_count:
            raise ValueError(
                "toy QC rotation fixture requires n == block_size * block_count"
            )
        if self.expected_rotation >= self.block_size:
            raise ValueError("expected_rotation must be smaller than block_size")
        if len(self.parity_check_matrix) != redundancy:
            raise ValueError("parity_check_matrix row count must equal n-k")
        if len(self.syndrome) != redundancy:
            raise ValueError("syndrome length must equal n-k")
        if len(self.base_error_positions) != self.w:
            raise ValueError("base_error_positions length must equal w")
        if sorted(set(self.base_error_positions)) != self.base_error_positions:
            raise ValueError("base_error_positions must be sorted and unique")
        for position in self.base_error_positions:
            if position < 0 or position >= self.n:
                raise ValueError("base_error_positions must be in range [0, n)")
        for row in self.parity_check_matrix:
            if len(row) != self.n:
                raise ValueError("each parity_check_matrix row length must equal n")
            if any(bit not in {0, 1} for bit in row):
                raise ValueError("parity_check_matrix must be binary")
        if any(bit not in {0, 1} for bit in self.syndrome):
            raise ValueError("syndrome must be binary")
        return self


class ToyQCRotationSolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solved: bool
    target_name: str
    n: int
    k: int
    w: int
    block_size: int
    block_count: int
    candidate_count: int
    rotation: int | None
    error_positions: list[int] | None
    error_vector_weight: int | None
    public: bool
    security_claim: bool


def solve_toy_syndrome_fixture(path: Path) -> ToySyndromeSolution:
    fixture = ToySyndromeFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )
    candidate_count = math.comb(fixture.n, fixture.w)
    if candidate_count > MAX_SYNDROME_CANDIDATES:
        raise ValueError(
            "toy syndrome fixture exceeds exhaustive candidate limit: "
            f"{candidate_count}"
        )

    matches: list[list[int]] = []
    for positions in combinations(range(fixture.n), fixture.w):
        candidate = list(positions)
        if _syndrome_for_positions(fixture.parity_check_matrix, candidate) == (
            fixture.syndrome
        ):
            matches.append(candidate)

    if len(matches) != 1:
        return _solution(
            fixture,
            candidate_count=candidate_count,
            error_positions=None,
            solved=False,
        )

    error_positions = matches[0]
    return _solution(
        fixture,
        candidate_count=candidate_count,
        error_positions=error_positions,
        solved=error_positions == fixture.expected_error_positions,
    )


def solve_toy_qc_rotation_fixture(path: Path) -> ToyQCRotationSolution:
    fixture = ToyQCRotationFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    matches: list[tuple[int, list[int]]] = []
    for rotation in range(fixture.block_size):
        candidate = _rotate_positions_within_blocks(
            fixture.base_error_positions,
            block_size=fixture.block_size,
            rotation=rotation,
        )
        if _syndrome_for_positions(fixture.parity_check_matrix, candidate) == (
            fixture.syndrome
        ):
            matches.append((rotation, candidate))

    if len(matches) != 1:
        return _qc_solution(
            fixture,
            candidate_count=fixture.block_size,
            rotation=None,
            error_positions=None,
            solved=False,
        )

    rotation, error_positions = matches[0]
    return _qc_solution(
        fixture,
        candidate_count=fixture.block_size,
        rotation=rotation,
        error_positions=error_positions,
        solved=rotation == fixture.expected_rotation,
    )


def _syndrome_for_positions(
    parity_check_matrix: list[list[int]],
    positions: list[int],
) -> list[int]:
    return [
        sum(row[position] for position in positions) % 2
        for row in parity_check_matrix
    ]


def _rotate_positions_within_blocks(
    positions: list[int],
    *,
    block_size: int,
    rotation: int,
) -> list[int]:
    rotated_positions = []
    for position in positions:
        block = position // block_size
        offset = position % block_size
        rotated_positions.append(
            block * block_size + ((offset + rotation) % block_size)
        )
    return sorted(rotated_positions)


def _solution(
    fixture: ToySyndromeFixture,
    *,
    candidate_count: int,
    error_positions: list[int] | None,
    solved: bool,
) -> ToySyndromeSolution:
    return ToySyndromeSolution(
        solved=solved,
        target_name=fixture.target_name,
        n=fixture.n,
        k=fixture.k,
        w=fixture.w,
        candidate_count=candidate_count,
        error_positions=error_positions,
        error_vector_weight=len(error_positions) if error_positions else None,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def _qc_solution(
    fixture: ToyQCRotationFixture,
    *,
    candidate_count: int,
    rotation: int | None,
    error_positions: list[int] | None,
    solved: bool,
) -> ToyQCRotationSolution:
    return ToyQCRotationSolution(
        solved=solved,
        target_name=fixture.target_name,
        n=fixture.n,
        k=fixture.k,
        w=fixture.w,
        block_size=fixture.block_size,
        block_count=fixture.block_count,
        candidate_count=candidate_count,
        rotation=rotation,
        error_positions=error_positions,
        error_vector_weight=len(error_positions) if error_positions else None,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )
