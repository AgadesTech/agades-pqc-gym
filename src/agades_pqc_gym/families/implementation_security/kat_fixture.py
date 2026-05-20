from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agades_pqc_gym.families.implementation_security.kat_estimator import (
    TOY_ACVP_MAX_TESTS,
    TOY_ACVP_MODEL,
    TOY_KAT_MAX_PAYLOAD_BYTES,
    TOY_KAT_MAX_VECTOR_COUNT,
    TOY_KAT_MODEL,
    analyze_toy_acvp_vector_set,
    payload_sha256,
)


class ToyKATFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.implementation_security_toy_kat.v1"]
    family: Literal["IMPLEMENTATION_SECURITY"]
    target_name: str = Field(min_length=1)
    suite: str = Field(min_length=1)
    model: Literal["toy_kat_digest_match"]
    payload: str = Field(min_length=1)
    expected_sha256: str
    vector_count: int = Field(ge=1, le=TOY_KAT_MAX_VECTOR_COUNT)
    artifact_execution: Literal[False]
    public: Literal[True]
    security_claim: Literal[False]

    @field_validator("expected_sha256")
    @classmethod
    def expected_sha256_must_be_lowercase_hex(cls, value: str) -> str:
        if len(value) != 64:
            raise ValueError("expected_sha256 must be 64 hex characters")
        if value != value.lower():
            raise ValueError("expected_sha256 must be lowercase")
        try:
            bytes.fromhex(value)
        except ValueError as exc:
            raise ValueError("expected_sha256 must be valid hexadecimal") from exc
        return value

    @model_validator(mode="after")
    def validate_payload_digest(self) -> ToyKATFixture:
        if self.model != TOY_KAT_MODEL:
            raise ValueError(f"toy KAT fixture model must be {TOY_KAT_MODEL}")
        payload_bytes = len(self.payload.encode("utf-8"))
        if payload_bytes > TOY_KAT_MAX_PAYLOAD_BYTES:
            raise ValueError(
                "toy KAT fixture payload exceeds public verifier byte limit"
            )
        if payload_sha256(self.payload) != self.expected_sha256:
            raise ValueError("expected_sha256 must match SHA-256(payload)")
        return self


class ToyKATFixtureResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    target_name: str
    suite: str
    model: str
    payload_bytes: int
    payload_sha256: str
    expected_sha256: str
    vector_count: int
    artifact_execution: bool
    public: bool
    security_claim: bool


class ToyACVPFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.implementation_security_toy_acvp.v1"]
    family: Literal["IMPLEMENTATION_SECURITY"]
    target_name: str = Field(min_length=1)
    suite: str = Field(min_length=1)
    model: Literal["toy_acvp_vector_set_match"]
    algorithm: str = Field(min_length=1)
    mode: str = Field(min_length=1)
    vector_set: dict[str, Any]
    expected_vector_set_sha256: str
    test_count: int = Field(ge=1, le=TOY_ACVP_MAX_TESTS)
    artifact_execution: Literal[False]
    public: Literal[True]
    security_claim: Literal[False]

    @field_validator("expected_vector_set_sha256")
    @classmethod
    def expected_digest_must_be_lowercase_hex(cls, value: str) -> str:
        if len(value) != 64:
            raise ValueError("expected_vector_set_sha256 must be 64 hex characters")
        if value != value.lower():
            raise ValueError("expected_vector_set_sha256 must be lowercase")
        try:
            bytes.fromhex(value)
        except ValueError as exc:
            raise ValueError(
                "expected_vector_set_sha256 must be valid hexadecimal"
            ) from exc
        return value

    @model_validator(mode="after")
    def validate_vector_set_digest(self) -> ToyACVPFixture:
        if self.model != TOY_ACVP_MODEL:
            raise ValueError(f"toy ACVP fixture model must be {TOY_ACVP_MODEL}")
        summary = analyze_toy_acvp_vector_set(
            self.vector_set,
            self.algorithm,
            self.mode,
        )
        if summary.test_count != self.test_count:
            raise ValueError("test_count must match vector_set tests")
        if summary.vector_set_sha256 != self.expected_vector_set_sha256:
            raise ValueError(
                "expected_vector_set_sha256 must match canonical "
                "SHA-256(vector_set)"
            )
        return self


class ToyACVPFixtureResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    target_name: str
    suite: str
    model: str
    algorithm: str
    mode: str
    vector_set_bytes: int
    vector_set_sha256: str
    expected_vector_set_sha256: str
    test_group_count: int
    test_count: int
    artifact_execution: bool
    public: bool
    security_claim: bool


def verify_toy_kat_fixture(path: Path) -> ToyKATFixtureResult:
    fixture = ToyKATFixture.model_validate_json(path.read_text(encoding="utf-8"))
    digest = payload_sha256(fixture.payload)
    return ToyKATFixtureResult(
        verified=digest == fixture.expected_sha256,
        target_name=fixture.target_name,
        suite=fixture.suite,
        model=fixture.model,
        payload_bytes=len(fixture.payload.encode("utf-8")),
        payload_sha256=digest,
        expected_sha256=fixture.expected_sha256,
        vector_count=fixture.vector_count,
        artifact_execution=fixture.artifact_execution,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )


def verify_toy_acvp_fixture(path: Path) -> ToyACVPFixtureResult:
    fixture = ToyACVPFixture.model_validate_json(path.read_text(encoding="utf-8"))
    summary = analyze_toy_acvp_vector_set(
        fixture.vector_set,
        fixture.algorithm,
        fixture.mode,
    )
    return ToyACVPFixtureResult(
        verified=summary.vector_set_sha256 == fixture.expected_vector_set_sha256,
        target_name=fixture.target_name,
        suite=fixture.suite,
        model=fixture.model,
        algorithm=fixture.algorithm,
        mode=fixture.mode,
        vector_set_bytes=summary.vector_set_bytes,
        vector_set_sha256=summary.vector_set_sha256,
        expected_vector_set_sha256=fixture.expected_vector_set_sha256,
        test_group_count=summary.test_group_count,
        test_count=summary.test_count,
        artifact_execution=fixture.artifact_execution,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )
