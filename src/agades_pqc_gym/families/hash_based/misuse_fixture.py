from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TOY_HASH_MISUSE_FIXTURE_SCHEMA = "agades.pqc.hash_based_toy_misuse.v1"
TOY_HASH_REUSED_SALT_MODEL = "toy_hash_reused_salt"


class ToyHashMisuseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(min_length=1)
    salt_hex: str = Field(min_length=2)
    message: str = Field(min_length=1)
    digest_hex: str = Field(min_length=2)

    @model_validator(mode="after")
    def validate_hex_fields(self) -> ToyHashMisuseRecord:
        _decode_hex(self.salt_hex, name="salt_hex")
        _decode_hex(self.digest_hex, name="digest_hex")
        return self


class ToyHashMisuseFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.hash_based_toy_misuse.v1"]
    family: Literal["HASH_BASED"]
    target_name: str = Field(min_length=1)
    hash_function: Literal["SHAKE256"]
    digest_bits: int = Field(gt=0)
    misuse_model: Literal["toy_hash_reused_salt"]
    records: list[ToyHashMisuseRecord] = Field(min_length=2)
    expected_reused_salts: list[str] = Field(min_length=1)
    expected_issue_count: int = Field(gt=0)
    public: Literal[True]
    security_claim: Literal[False]

    @model_validator(mode="after")
    def validate_fixture(self) -> ToyHashMisuseFixture:
        if self.digest_bits % 8 != 0:
            raise ValueError("digest_bits must be byte-aligned")
        digest_bytes = self.digest_bits // 8
        seen_ids: set[str] = set()
        for record in self.records:
            if record.message_id in seen_ids:
                raise ValueError("record message_id values must be unique")
            seen_ids.add(record.message_id)
            if len(_decode_hex(record.digest_hex, name="digest_hex")) != digest_bytes:
                raise ValueError("record digest length must equal digest_bits")
            expected_digest = _toy_digest_hex(
                self.hash_function,
                salt_hex=record.salt_hex,
                message=record.message,
                digest_bytes=digest_bytes,
            )
            if record.digest_hex.lower() != expected_digest:
                raise ValueError("record digest_hex does not match toy hash input")

        expected_salts = sorted(salt.lower() for salt in self.expected_reused_salts)
        for salt in expected_salts:
            _decode_hex(salt, name="expected_reused_salts")
        observed_salts = _reused_salts(self.records)
        if observed_salts != expected_salts:
            raise ValueError("expected_reused_salts do not match records")
        if len(observed_salts) != self.expected_issue_count:
            raise ValueError("expected_issue_count does not match reused salts")
        return self


class ToyHashMisuseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    target_name: str
    hash_function: str
    digest_bits: int
    misuse_model: str
    record_count: int
    salt_bytes: int
    issue_count: int
    reused_salts: list[str]
    public: bool
    security_claim: bool


def verify_toy_hash_misuse_fixture(path: Path) -> ToyHashMisuseResult:
    fixture = ToyHashMisuseFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )
    reused_salts = _reused_salts(fixture.records)
    verified = (
        reused_salts == sorted(salt.lower() for salt in fixture.expected_reused_salts)
        and len(reused_salts) == fixture.expected_issue_count
    )
    salt_bytes = _salt_byte_count(fixture.records)
    return ToyHashMisuseResult(
        verified=verified,
        target_name=fixture.target_name,
        hash_function=fixture.hash_function,
        digest_bits=fixture.digest_bits,
        misuse_model=fixture.misuse_model,
        record_count=len(fixture.records),
        salt_bytes=salt_bytes,
        issue_count=len(reused_salts),
        reused_salts=reused_salts,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def _toy_digest_hex(
    hash_function: str,
    *,
    salt_hex: str,
    message: str,
    digest_bytes: int,
) -> str:
    payload = _decode_hex(salt_hex, name="salt_hex") + message.encode("utf-8")
    if hash_function == "SHAKE256":
        return hashlib.shake_256(payload).digest(digest_bytes).hex()
    raise ValueError(f"unsupported toy hash function: {hash_function}")


def _reused_salts(records: list[ToyHashMisuseRecord]) -> list[str]:
    records_by_salt: dict[str, list[ToyHashMisuseRecord]] = defaultdict(list)
    for record in records:
        records_by_salt[record.salt_hex.lower()].append(record)
    reused = []
    for salt, salt_records in records_by_salt.items():
        distinct_messages = {record.message for record in salt_records}
        if len(salt_records) > 1 and len(distinct_messages) > 1:
            reused.append(salt)
    return sorted(reused)


def _salt_byte_count(records: list[ToyHashMisuseRecord]) -> int:
    salt_lengths = {
        len(_decode_hex(record.salt_hex, name="salt_hex")) for record in records
    }
    if len(salt_lengths) != 1:
        raise ValueError("all record salts must have the same byte length")
    return salt_lengths.pop()


def _decode_hex(value: str, *, name: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be hex") from exc
