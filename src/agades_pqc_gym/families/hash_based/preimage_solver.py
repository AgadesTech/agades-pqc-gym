from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_HASH_PREIMAGE_CANDIDATES = 100_000


class ToyHashPreimageFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.hash_based_toy_preimage.v1"]
    family: Literal["HASH_BASED"]
    target_name: str = Field(min_length=1)
    digest_bits: int = Field(gt=0, le=64)
    hash_function: Literal["SHAKE256"]
    message_prefix: str = Field(min_length=1)
    candidate_encoding: Literal["uint_be_fixed_width"]
    candidate_byte_length: int = Field(ge=1, le=4)
    max_candidate_exclusive: int = Field(gt=0)
    digest_hex: str = Field(min_length=1)
    expected_candidate: int = Field(ge=0)
    public: Literal[True]
    security_claim: Literal[False]

    @field_validator("digest_hex")
    @classmethod
    def digest_hex_must_be_lowercase_hex(cls, value: str) -> str:
        if value != value.lower():
            raise ValueError("digest_hex must be lowercase")
        try:
            bytes.fromhex(value)
        except ValueError as exc:
            raise ValueError("digest_hex must be valid hexadecimal") from exc
        return value

    @model_validator(mode="after")
    def validate_bounds(self) -> ToyHashPreimageFixture:
        if self.digest_bits % 8 != 0:
            raise ValueError("digest_bits must be byte-aligned")
        if len(self.digest_hex) != (self.digest_bits // 4):
            raise ValueError("digest_hex length must match digest_bits")
        if self.max_candidate_exclusive > MAX_HASH_PREIMAGE_CANDIDATES:
            raise ValueError(
                "toy hash preimage fixture exceeds exhaustive candidate limit"
            )
        candidate_limit = 1 << (8 * self.candidate_byte_length)
        if self.max_candidate_exclusive > candidate_limit:
            raise ValueError("candidate range exceeds fixed-width encoding")
        if self.expected_candidate >= self.max_candidate_exclusive:
            raise ValueError("expected_candidate must be inside candidate range")
        return self


class ToyHashPreimageSolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solved: bool
    target_name: str
    digest_bits: int
    hash_function: str
    digest_hex: str
    candidate_count: int
    candidate: int | None
    candidate_bytes_hex: str | None
    public: bool
    security_claim: bool


def solve_toy_preimage_fixture(path: Path) -> ToyHashPreimageSolution:
    fixture = ToyHashPreimageFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    matches: list[int] = []
    for candidate in range(fixture.max_candidate_exclusive):
        digest_hex = _digest_for_candidate(fixture, candidate)
        if digest_hex == fixture.digest_hex:
            matches.append(candidate)

    if len(matches) != 1:
        return _solution(
            fixture,
            candidate=None,
            solved=False,
        )

    candidate = matches[0]
    return _solution(
        fixture,
        candidate=candidate,
        solved=candidate == fixture.expected_candidate,
    )


def _digest_for_candidate(fixture: ToyHashPreimageFixture, candidate: int) -> str:
    payload = fixture.message_prefix.encode("utf-8") + _candidate_bytes(
        fixture,
        candidate,
    )
    if fixture.hash_function == "SHAKE256":
        return hashlib.shake_256(payload).digest(fixture.digest_bits // 8).hex()
    raise ValueError(f"unsupported toy hash function: {fixture.hash_function}")


def _candidate_bytes(fixture: ToyHashPreimageFixture, candidate: int) -> bytes:
    return candidate.to_bytes(fixture.candidate_byte_length, "big")


def _solution(
    fixture: ToyHashPreimageFixture,
    *,
    candidate: int | None,
    solved: bool,
) -> ToyHashPreimageSolution:
    candidate_bytes_hex = (
        _candidate_bytes(fixture, candidate).hex() if candidate is not None else None
    )
    return ToyHashPreimageSolution(
        solved=solved,
        target_name=fixture.target_name,
        digest_bits=fixture.digest_bits,
        hash_function=fixture.hash_function,
        digest_hex=fixture.digest_hex,
        candidate_count=fixture.max_candidate_exclusive,
        candidate=candidate,
        candidate_bytes_hex=candidate_bytes_hex,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )
