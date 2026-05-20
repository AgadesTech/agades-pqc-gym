from __future__ import annotations

import math
from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from agades_pqc_gym.families.implementation_security.kat_estimator import (
    TOY_CTGRIND_TAINT_MODEL,
    TOY_CTGRIND_TAINT_TOOL,
    TOY_DUDECT_SUMMARY_MODEL,
    TOY_DUDECT_SUMMARY_TOOL,
    TOY_TIMING_MODEL,
    TOY_TIMING_TOOL,
    required_ctgrind_checked_blocks,
    required_ctgrind_taint_count,
    required_cycle_list,
    welch_abs_t,
)

TOY_TIMING_SCHEMA_VERSION = "agades.pqc.implementation_security_toy_timing.v1"
TOY_DUDECT_SUMMARY_SCHEMA_VERSION = (
    "agades.pqc.implementation_security_toy_dudect_summary.v1"
)
TOY_CTGRIND_TAINT_SCHEMA_VERSION = (
    "agades.pqc.implementation_security_toy_ctgrind_secret_taint.v1"
)


class ToyTimingFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[
        "agades.pqc.implementation_security_toy_timing.v1",
        "agades.pqc.implementation_security_toy_dudect_summary.v1",
    ]
    family: Literal["IMPLEMENTATION_SECURITY"]
    target_name: str = Field(min_length=1)
    tool: Literal["toy_welch_timing_check", "toy_dudect_summary_check"]
    model: Literal[
        "toy_timing_welch_t_check",
        "toy_dudect_summary_threshold_check",
    ]
    dudect_version: str | None = None
    fixed_cycles: list[int]
    random_cycles: list[int]
    max_abs_t: float = Field(gt=0)
    artifact_execution: Literal[False]
    dudect_execution: Literal[False] | None = None
    public: Literal[True]
    constant_time_claim: Literal[False] | None = None
    security_claim: Literal[False]

    @field_validator("fixed_cycles", "random_cycles", mode="before")
    @classmethod
    def cycles_must_be_small_public_samples(
        cls,
        value: object,
        info: ValidationInfo,
    ) -> list[int]:
        return required_cycle_list({info.field_name: value}, info.field_name)

    @field_validator("max_abs_t")
    @classmethod
    def max_abs_t_must_be_finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("max_abs_t must be finite")
        return value

    @model_validator(mode="after")
    def validate_timing_summary(self) -> ToyTimingFixture:
        if self.schema_version == TOY_TIMING_SCHEMA_VERSION:
            if self.tool != TOY_TIMING_TOOL or self.model != TOY_TIMING_MODEL:
                raise ValueError(
                    "toy timing fixture must use the reviewed "
                    f"{TOY_TIMING_TOOL}/{TOY_TIMING_MODEL} pair"
                )
            if (
                self.dudect_version is not None
                or self.dudect_execution is not None
                or self.constant_time_claim is not None
            ):
                raise ValueError(
                    "toy timing fixture must not include dudect summary fields"
                )
        elif self.schema_version == TOY_DUDECT_SUMMARY_SCHEMA_VERSION:
            if (
                self.tool != TOY_DUDECT_SUMMARY_TOOL
                or self.model != TOY_DUDECT_SUMMARY_MODEL
            ):
                raise ValueError(
                    "toy dudect summary fixture must use the reviewed "
                    f"{TOY_DUDECT_SUMMARY_TOOL}/"
                    f"{TOY_DUDECT_SUMMARY_MODEL} pair"
                )
            if not self.dudect_version:
                raise ValueError(
                    "toy dudect summary fixture requires non-empty "
                    "dudect_version"
                )
            if self.dudect_execution is not False:
                raise ValueError(
                    "toy dudect summary fixture must declare dudect_execution=false"
                )
            if self.constant_time_claim is not False:
                raise ValueError(
                    "toy dudect summary fixture must declare "
                    "constant_time_claim=false"
                )
        if welch_abs_t(self.fixed_cycles, self.random_cycles) > self.max_abs_t:
            raise ValueError(
                "toy timing fixture observed abs t-statistic exceeds max_abs_t"
            )
        return self


class ToyTimingFixtureResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    target_name: str
    tool: str
    model: str
    dudect_version: str | None = None
    fixed_cycles: list[int]
    random_cycles: list[int]
    fixed_sample_count: int
    random_sample_count: int
    observed_abs_t: float
    max_abs_t: float
    artifact_execution: bool
    dudect_execution: bool | None = None
    public: bool
    constant_time_claim: bool | None = None
    security_claim: bool


class ToyCtgrindTaintFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[
        "agades.pqc.implementation_security_toy_ctgrind_secret_taint.v1"
    ]
    family: Literal["IMPLEMENTATION_SECURITY"]
    target_name: str = Field(min_length=1)
    tool: Literal["toy_ctgrind_secret_taint_summary_check"]
    model: Literal["toy_ctgrind_secret_taint_summary_check"]
    ctgrind_version: str = Field(min_length=1)
    checked_blocks: int
    secret_dependent_branch_count: int
    secret_dependent_memory_access_count: int
    max_secret_dependent_branch_count: int
    max_secret_dependent_memory_access_count: int
    artifact_execution: Literal[False]
    ctgrind_execution: Literal[False]
    public: Literal[True]
    constant_time_claim: Literal[False]
    security_claim: Literal[False]

    @field_validator("checked_blocks", mode="before")
    @classmethod
    def checked_blocks_must_be_small_public_summary(cls, value: object) -> int:
        return required_ctgrind_checked_blocks({"checked_blocks": value})

    @field_validator(
        "secret_dependent_branch_count",
        "secret_dependent_memory_access_count",
        "max_secret_dependent_branch_count",
        "max_secret_dependent_memory_access_count",
        mode="before",
    )
    @classmethod
    def counts_must_be_small_public_summary(
        cls,
        value: object,
        info: ValidationInfo,
    ) -> int:
        return required_ctgrind_taint_count({info.field_name: value}, info.field_name)

    @model_validator(mode="after")
    def validate_ctgrind_taint_summary(self) -> ToyCtgrindTaintFixture:
        if self.tool != TOY_CTGRIND_TAINT_TOOL or self.model != TOY_CTGRIND_TAINT_MODEL:
            raise ValueError(
                "toy ctgrind secret-taint fixture must use the reviewed "
                f"{TOY_CTGRIND_TAINT_TOOL}/{TOY_CTGRIND_TAINT_MODEL} pair"
            )
        if (
            self.secret_dependent_branch_count
            > self.max_secret_dependent_branch_count
        ):
            raise ValueError(
                "toy ctgrind secret-taint fixture "
                "secret_dependent_branch_count exceeds "
                "max_secret_dependent_branch_count"
            )
        if (
            self.secret_dependent_memory_access_count
            > self.max_secret_dependent_memory_access_count
        ):
            raise ValueError(
                "toy ctgrind secret-taint fixture "
                "secret_dependent_memory_access_count exceeds "
                "max_secret_dependent_memory_access_count"
            )
        return self


class ToyCtgrindTaintFixtureResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    target_name: str
    tool: str
    model: str
    ctgrind_version: str
    checked_blocks: int
    secret_dependent_branch_count: int
    secret_dependent_memory_access_count: int
    max_secret_dependent_branch_count: int
    max_secret_dependent_memory_access_count: int
    artifact_execution: bool
    ctgrind_execution: bool
    public: bool
    constant_time_claim: bool
    security_claim: bool


def verify_toy_timing_fixture(path: Path) -> ToyTimingFixtureResult:
    fixture = ToyTimingFixture.model_validate_json(path.read_text(encoding="utf-8"))
    observed_abs_t = welch_abs_t(fixture.fixed_cycles, fixture.random_cycles)
    return ToyTimingFixtureResult(
        verified=observed_abs_t <= fixture.max_abs_t,
        target_name=fixture.target_name,
        tool=fixture.tool,
        model=fixture.model,
        dudect_version=fixture.dudect_version,
        fixed_cycles=fixture.fixed_cycles,
        random_cycles=fixture.random_cycles,
        fixed_sample_count=len(fixture.fixed_cycles),
        random_sample_count=len(fixture.random_cycles),
        observed_abs_t=round(observed_abs_t, 4),
        max_abs_t=fixture.max_abs_t,
        artifact_execution=fixture.artifact_execution,
        dudect_execution=fixture.dudect_execution,
        public=fixture.public,
        constant_time_claim=fixture.constant_time_claim,
        security_claim=fixture.security_claim,
    )


def verify_toy_ctgrind_taint_fixture(path: Path) -> ToyCtgrindTaintFixtureResult:
    fixture = ToyCtgrindTaintFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )
    verified = (
        fixture.secret_dependent_branch_count
        <= fixture.max_secret_dependent_branch_count
        and fixture.secret_dependent_memory_access_count
        <= fixture.max_secret_dependent_memory_access_count
    )
    return ToyCtgrindTaintFixtureResult(
        verified=verified,
        target_name=fixture.target_name,
        tool=fixture.tool,
        model=fixture.model,
        ctgrind_version=fixture.ctgrind_version,
        checked_blocks=fixture.checked_blocks,
        secret_dependent_branch_count=fixture.secret_dependent_branch_count,
        secret_dependent_memory_access_count=(
            fixture.secret_dependent_memory_access_count
        ),
        max_secret_dependent_branch_count=(
            fixture.max_secret_dependent_branch_count
        ),
        max_secret_dependent_memory_access_count=(
            fixture.max_secret_dependent_memory_access_count
        ),
        artifact_execution=fixture.artifact_execution,
        ctgrind_execution=fixture.ctgrind_execution,
        public=fixture.public,
        constant_time_claim=fixture.constant_time_claim,
        security_claim=fixture.security_claim,
    )
