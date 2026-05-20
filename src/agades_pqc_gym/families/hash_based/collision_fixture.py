from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ToyHashCollisionFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.hash_based_toy_collision.v1"]
    family: Literal["HASH_BASED"]
    target_name: str = Field(min_length=1)
    digest_bits: int = Field(gt=0, le=64)
    hash_function: Literal["SHAKE256"]
    message_encoding: Literal["utf8"]
    left_message: str = Field(min_length=1, max_length=256)
    right_message: str = Field(min_length=1, max_length=256)
    digest_hex: str = Field(min_length=1)
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
    def validate_collision_fixture(self) -> ToyHashCollisionFixture:
        if self.digest_bits % 8 != 0:
            raise ValueError("digest_bits must be byte-aligned")
        if len(self.digest_hex) != (self.digest_bits // 4):
            raise ValueError("digest_hex length must match digest_bits")
        if self.left_message == self.right_message:
            raise ValueError("toy collision fixture messages must be distinct")
        return self


class ToyHashCollisionVerification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    target_name: str
    digest_bits: int
    hash_function: str
    digest_hex: str
    left_message: str
    right_message: str
    public: bool
    security_claim: bool


def verify_toy_collision_fixture(path: Path) -> ToyHashCollisionVerification:
    fixture = ToyHashCollisionFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )
    left_digest = _digest_hex(fixture, fixture.left_message)
    right_digest = _digest_hex(fixture, fixture.right_message)
    verified = left_digest == right_digest == fixture.digest_hex

    return ToyHashCollisionVerification(
        verified=verified,
        target_name=fixture.target_name,
        digest_bits=fixture.digest_bits,
        hash_function=fixture.hash_function,
        digest_hex=fixture.digest_hex,
        left_message=fixture.left_message,
        right_message=fixture.right_message,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def _digest_hex(fixture: ToyHashCollisionFixture, message: str) -> str:
    if fixture.hash_function == "SHAKE256":
        return hashlib.shake_256(message.encode("utf-8")).digest(
            fixture.digest_bits // 8
        ).hex()
    raise ValueError(f"unsupported toy hash function: {fixture.hash_function}")
