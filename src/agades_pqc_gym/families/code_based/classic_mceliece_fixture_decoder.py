from __future__ import annotations

import math
from itertools import combinations
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_CLASSIC_MCELIECE_SUPPORT_CANDIDATES = 100_000


class ToyClassicMcElieceSupportSyndromeFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[
        "agades.pqc.code_based_toy_classic_mceliece_support_syndrome.v1"
    ]
    family: Literal["CODE_BASED"]
    target_name: str = Field(min_length=1)
    n: int = Field(gt=0)
    k: int = Field(gt=0)
    w: int = Field(gt=0)
    parity_check_matrix: list[list[int]] = Field(min_length=1)
    syndrome: list[int] = Field(min_length=1)
    support_positions: list[int] = Field(min_length=1)
    expected_error_positions: list[int] = Field(min_length=1)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_dimensions(self) -> ToyClassicMcElieceSupportSyndromeFixture:
        redundancy = self.n - self.k
        if redundancy <= 0:
            raise ValueError("toy Classic McEliece support fixture requires k < n")
        if len(self.parity_check_matrix) != redundancy:
            raise ValueError("parity_check_matrix row count must equal n-k")
        if len(self.syndrome) != redundancy:
            raise ValueError("syndrome length must equal n-k")
        _require_binary_vector(self.syndrome, name="syndrome")
        for row in self.parity_check_matrix:
            if len(row) != self.n:
                raise ValueError("parity_check_matrix rows must have length n")
            _require_binary_vector(row, name="parity_check_matrix rows")
        _require_positions(
            self.support_positions,
            limit=self.n,
            name="support_positions",
        )
        if len(self.support_positions) < self.w:
            raise ValueError("support_positions length must be at least w")
        _require_positions(
            self.expected_error_positions,
            limit=self.n,
            name="expected_error_positions",
        )
        if len(self.expected_error_positions) != self.w:
            raise ValueError("expected_error_positions length must equal w")
        if not set(self.expected_error_positions).issubset(self.support_positions):
            raise ValueError("expected_error_positions must be within support")
        if (
            _syndrome_for_positions(
                self.parity_check_matrix,
                self.expected_error_positions,
            )
            != self.syndrome
        ):
            raise ValueError("expected_error_positions do not match syndrome")
        return self


class ToyClassicMcElieceSupportSyndromeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solved: bool
    target_name: str
    n: int
    k: int
    w: int
    support_size: int
    candidate_count: int
    error_positions: list[int] | None
    error_vector_weight: int | None
    public: bool
    security_claim: bool


def decode_toy_classic_mceliece_support_syndrome_fixture(
    path: Path,
) -> ToyClassicMcElieceSupportSyndromeResult:
    fixture = ToyClassicMcElieceSupportSyndromeFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    candidate_count = math.comb(len(fixture.support_positions), fixture.w)
    if candidate_count > MAX_CLASSIC_MCELIECE_SUPPORT_CANDIDATES:
        raise ValueError(
            "toy Classic McEliece support fixture exceeds bounded candidate "
            f"limit: {candidate_count} > {MAX_CLASSIC_MCELIECE_SUPPORT_CANDIDATES}"
        )

    matches: list[list[int]] = []
    for positions in combinations(fixture.support_positions, fixture.w):
        candidate = list(positions)
        if (
            _syndrome_for_positions(fixture.parity_check_matrix, candidate)
            == fixture.syndrome
        ):
            matches.append(candidate)
            if len(matches) > 1:
                break

    error_positions: list[int] | None = None
    if len(matches) == 1 and matches[0] == fixture.expected_error_positions:
        error_positions = matches[0]

    return ToyClassicMcElieceSupportSyndromeResult(
        solved=error_positions is not None,
        target_name=fixture.target_name,
        n=fixture.n,
        k=fixture.k,
        w=fixture.w,
        support_size=len(fixture.support_positions),
        candidate_count=candidate_count,
        error_positions=error_positions,
        error_vector_weight=len(error_positions) if error_positions else None,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


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
