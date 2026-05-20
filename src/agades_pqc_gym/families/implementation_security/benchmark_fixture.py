from __future__ import annotations

import math
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agades_pqc_gym.families.implementation_security.kat_estimator import (
    TOY_BENCHMARK_METRIC,
    TOY_BENCHMARK_MODEL,
    TOY_BINARY_SIZE_METRIC,
    TOY_BINARY_SIZE_MODEL,
    TOY_MEMORY_METRIC,
    TOY_MEMORY_MODEL,
    TOY_STACK_USAGE_METRIC,
    TOY_STACK_USAGE_MODEL,
    median,
    required_benchmark_samples,
    required_binary_size_bytes,
    required_binary_size_threshold,
    required_memory_bytes,
    required_memory_threshold,
    required_stack_samples,
)


class ToyBenchmarkFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.implementation_security_toy_benchmark.v1"]
    family: Literal["IMPLEMENTATION_SECURITY"]
    target_name: str = Field(min_length=1)
    suite: str = Field(min_length=1)
    metric: Literal[
        "toy_binary_size_bytes",
        "toy_cycles_per_operation",
        "toy_memory_footprint_bytes",
        "toy_stack_usage_bytes",
    ]
    model: Literal[
        "toy_benchmark_summary_check",
        "toy_binary_size_check",
        "toy_memory_footprint_check",
        "toy_stack_usage_check",
    ]
    samples: list[int] | None = None
    stack_samples: list[int] | None = None
    max_median_cycles: float | None = Field(default=None, gt=0)
    text_bytes: int | None = None
    rodata_bytes: int | None = None
    data_bytes: int | None = None
    bss_bytes: int | None = None
    max_total_bytes: int | None = None
    stack_bytes: int | None = None
    heap_bytes: int | None = None
    code_bytes: int | None = None
    max_stack_bytes: int | None = None
    max_heap_bytes: int | None = None
    max_code_bytes: int | None = None
    artifact_execution: Literal[False]
    public: Literal[True]
    security_claim: Literal[False]

    @field_validator("samples", mode="before")
    @classmethod
    def samples_must_be_small_public_cycles(cls, value: object) -> list[int] | None:
        if value is None:
            return value
        return required_benchmark_samples({"samples": value}, "samples")

    @field_validator("stack_samples", mode="before")
    @classmethod
    def stack_samples_must_be_bounded(cls, value: object) -> list[int] | None:
        if value is None:
            return value
        return required_stack_samples(
            {"stack_samples": value},
            "stack_samples",
        )

    @field_validator("max_median_cycles")
    @classmethod
    def max_median_cycles_must_be_finite(cls, value: float | None) -> float | None:
        if value is None:
            return None
        if not math.isfinite(value):
            raise ValueError("max_median_cycles must be finite")
        return value

    @field_validator(
        "text_bytes", "rodata_bytes", "data_bytes", "bss_bytes", mode="before"
    )
    @classmethod
    def binary_size_bytes_must_be_bounded(cls, value: object) -> int | None:
        if value is None:
            return None
        return required_binary_size_bytes(
            {"binary_size_bytes": value},
            "binary_size_bytes",
        )

    @field_validator("max_total_bytes", mode="before")
    @classmethod
    def binary_size_threshold_must_be_bounded(cls, value: object) -> int | None:
        if value is None:
            return None
        return required_binary_size_threshold(
            {"binary_size_threshold": value},
            "binary_size_threshold",
        )

    @field_validator("stack_bytes", "heap_bytes", "code_bytes", mode="before")
    @classmethod
    def memory_bytes_must_be_bounded(cls, value: object) -> int | None:
        if value is None:
            return None
        return required_memory_bytes({"memory_bytes": value}, "memory_bytes")

    @field_validator(
        "max_stack_bytes",
        "max_heap_bytes",
        "max_code_bytes",
        mode="before",
    )
    @classmethod
    def memory_thresholds_must_be_bounded(cls, value: object) -> int | None:
        if value is None:
            return None
        return required_memory_threshold(
            {"memory_threshold": value},
            "memory_threshold",
        )

    @model_validator(mode="after")
    def validate_benchmark_summary(self) -> ToyBenchmarkFixture:
        if self.model == TOY_BENCHMARK_MODEL:
            self._validate_cycle_summary()
            return self
        if self.model == TOY_BINARY_SIZE_MODEL:
            self._validate_binary_size_summary()
            return self
        if self.model == TOY_MEMORY_MODEL:
            self._validate_memory_summary()
            return self
        if self.model == TOY_STACK_USAGE_MODEL:
            self._validate_stack_usage_summary()
            return self
        raise ValueError("toy benchmark fixture uses an unsupported model")

    def _validate_cycle_summary(self) -> None:
        if self.metric != TOY_BENCHMARK_METRIC:
            raise ValueError(
                f"toy benchmark fixture metric must be {TOY_BENCHMARK_METRIC}"
            )
        if self.samples is None:
            raise ValueError(
                "toy benchmark fixture requires samples for cycle summaries"
            )
        if self.max_median_cycles is None:
            raise ValueError(
                "toy benchmark fixture requires max_median_cycles for "
                "cycle summaries"
            )
        if median(self.samples) > self.max_median_cycles:
            raise ValueError(
                "toy benchmark fixture median cycles exceeds max_median_cycles"
            )

    def _validate_binary_size_summary(self) -> None:
        if self.metric != TOY_BINARY_SIZE_METRIC:
            raise ValueError(
                f"toy binary-size fixture metric must be {TOY_BINARY_SIZE_METRIC}"
            )
        required_fields = {
            "bss_bytes": self.bss_bytes,
            "data_bytes": self.data_bytes,
            "max_total_bytes": self.max_total_bytes,
            "rodata_bytes": self.rodata_bytes,
            "text_bytes": self.text_bytes,
        }
        missing_fields = [
            name for name, value in required_fields.items() if value is None
        ]
        if missing_fields:
            raise ValueError(
                "toy binary-size fixture requires "
                + ", ".join(sorted(missing_fields))
            )
        assert self.text_bytes is not None
        assert self.rodata_bytes is not None
        assert self.data_bytes is not None
        assert self.bss_bytes is not None
        assert self.max_total_bytes is not None
        total_bytes = (
            self.text_bytes + self.rodata_bytes + self.data_bytes + self.bss_bytes
        )
        if total_bytes <= 0:
            raise ValueError(
                "toy binary-size fixture requires positive total bytes"
            )
        if total_bytes > self.max_total_bytes:
            raise ValueError(
                "toy binary-size fixture total binary size exceeds max_total_bytes"
            )

    def _validate_memory_summary(self) -> None:
        if self.metric != TOY_MEMORY_METRIC:
            raise ValueError(
                f"toy memory fixture metric must be {TOY_MEMORY_METRIC}"
            )
        required_fields = {
            "stack_bytes": self.stack_bytes,
            "heap_bytes": self.heap_bytes,
            "code_bytes": self.code_bytes,
            "max_stack_bytes": self.max_stack_bytes,
            "max_heap_bytes": self.max_heap_bytes,
            "max_code_bytes": self.max_code_bytes,
        }
        missing_fields = [
            name for name, value in required_fields.items() if value is None
        ]
        if missing_fields:
            raise ValueError(
                "toy memory fixture requires "
                + ", ".join(sorted(missing_fields))
            )
        assert self.stack_bytes is not None
        assert self.heap_bytes is not None
        assert self.code_bytes is not None
        assert self.max_stack_bytes is not None
        assert self.max_heap_bytes is not None
        assert self.max_code_bytes is not None
        if self.stack_bytes + self.heap_bytes + self.code_bytes <= 0:
            raise ValueError("toy memory fixture requires positive total bytes")
        for observed_name, observed, threshold_name, threshold in (
            ("stack_bytes", self.stack_bytes, "max_stack_bytes", self.max_stack_bytes),
            ("heap_bytes", self.heap_bytes, "max_heap_bytes", self.max_heap_bytes),
            ("code_bytes", self.code_bytes, "max_code_bytes", self.max_code_bytes),
        ):
            if observed > threshold:
                raise ValueError(
                    f"toy memory fixture {observed_name} exceeds {threshold_name}"
                )

    def _validate_stack_usage_summary(self) -> None:
        if self.metric != TOY_STACK_USAGE_METRIC:
            raise ValueError(
                f"toy stack-usage fixture metric must be {TOY_STACK_USAGE_METRIC}"
            )
        if self.stack_samples is None:
            raise ValueError(
                "toy stack-usage fixture requires stack_samples"
            )
        if self.max_stack_bytes is None:
            raise ValueError(
                "toy stack-usage fixture requires max_stack_bytes"
            )
        if max(self.stack_samples) > self.max_stack_bytes:
            raise ValueError(
                "toy stack-usage fixture observed stack usage exceeds "
                "max_stack_bytes"
            )


class ToyBenchmarkFixtureResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    target_name: str
    suite: str
    metric: str
    model: str
    samples: list[int] | None = None
    stack_samples: list[int] | None = None
    sample_count: int | None = None
    median_cycles: float | None = None
    max_median_cycles: float | None = None
    max_observed_stack_bytes: int | None = None
    mean_stack_bytes: float | None = None
    total_stack_bytes: int | None = None
    text_bytes: int | None = None
    rodata_bytes: int | None = None
    data_bytes: int | None = None
    bss_bytes: int | None = None
    max_total_bytes: int | None = None
    stack_bytes: int | None = None
    heap_bytes: int | None = None
    code_bytes: int | None = None
    total_bytes: int | None = None
    max_stack_bytes: int | None = None
    max_heap_bytes: int | None = None
    max_code_bytes: int | None = None
    artifact_execution: bool
    public: bool
    security_claim: bool


def verify_toy_benchmark_fixture(path: Path) -> ToyBenchmarkFixtureResult:
    fixture = ToyBenchmarkFixture.model_validate_json(
        path.read_text(encoding="utf-8")
    )
    if fixture.model == TOY_BINARY_SIZE_MODEL:
        assert fixture.text_bytes is not None
        assert fixture.rodata_bytes is not None
        assert fixture.data_bytes is not None
        assert fixture.bss_bytes is not None
        assert fixture.max_total_bytes is not None
        total_bytes = (
            fixture.text_bytes
            + fixture.rodata_bytes
            + fixture.data_bytes
            + fixture.bss_bytes
        )
        return ToyBenchmarkFixtureResult(
            verified=total_bytes > 0 and total_bytes <= fixture.max_total_bytes,
            target_name=fixture.target_name,
            suite=fixture.suite,
            metric=fixture.metric,
            model=fixture.model,
            text_bytes=fixture.text_bytes,
            rodata_bytes=fixture.rodata_bytes,
            data_bytes=fixture.data_bytes,
            bss_bytes=fixture.bss_bytes,
            total_bytes=total_bytes,
            max_total_bytes=fixture.max_total_bytes,
            artifact_execution=fixture.artifact_execution,
            public=fixture.public,
            security_claim=fixture.security_claim,
        )

    if fixture.model == TOY_MEMORY_MODEL:
        assert fixture.stack_bytes is not None
        assert fixture.heap_bytes is not None
        assert fixture.code_bytes is not None
        assert fixture.max_stack_bytes is not None
        assert fixture.max_heap_bytes is not None
        assert fixture.max_code_bytes is not None
        total_bytes = fixture.stack_bytes + fixture.heap_bytes + fixture.code_bytes
        return ToyBenchmarkFixtureResult(
            verified=(
                fixture.stack_bytes <= fixture.max_stack_bytes
                and fixture.heap_bytes <= fixture.max_heap_bytes
                and fixture.code_bytes <= fixture.max_code_bytes
                and total_bytes > 0
            ),
            target_name=fixture.target_name,
            suite=fixture.suite,
            metric=fixture.metric,
            model=fixture.model,
            stack_bytes=fixture.stack_bytes,
            heap_bytes=fixture.heap_bytes,
            code_bytes=fixture.code_bytes,
            total_bytes=total_bytes,
            max_stack_bytes=fixture.max_stack_bytes,
            max_heap_bytes=fixture.max_heap_bytes,
            max_code_bytes=fixture.max_code_bytes,
            artifact_execution=fixture.artifact_execution,
            public=fixture.public,
            security_claim=fixture.security_claim,
        )

    if fixture.model == TOY_STACK_USAGE_MODEL:
        assert fixture.stack_samples is not None
        assert fixture.max_stack_bytes is not None
        total_stack_bytes = sum(fixture.stack_samples)
        max_observed_stack_bytes = max(fixture.stack_samples)
        return ToyBenchmarkFixtureResult(
            verified=max_observed_stack_bytes <= fixture.max_stack_bytes,
            target_name=fixture.target_name,
            suite=fixture.suite,
            metric=fixture.metric,
            model=fixture.model,
            stack_samples=fixture.stack_samples,
            sample_count=len(fixture.stack_samples),
            max_observed_stack_bytes=max_observed_stack_bytes,
            mean_stack_bytes=round(
                total_stack_bytes / len(fixture.stack_samples),
                4,
            ),
            total_stack_bytes=total_stack_bytes,
            max_stack_bytes=fixture.max_stack_bytes,
            artifact_execution=fixture.artifact_execution,
            public=fixture.public,
            security_claim=fixture.security_claim,
        )

    assert fixture.samples is not None
    assert fixture.max_median_cycles is not None
    median_cycles = median(fixture.samples)
    return ToyBenchmarkFixtureResult(
        verified=median_cycles <= fixture.max_median_cycles,
        target_name=fixture.target_name,
        suite=fixture.suite,
        metric=fixture.metric,
        model=fixture.model,
        samples=fixture.samples,
        sample_count=len(fixture.samples),
        median_cycles=round(median_cycles, 4),
        max_median_cycles=fixture.max_median_cycles,
        artifact_execution=fixture.artifact_execution,
        public=fixture.public,
        security_claim=fixture.security_claim,
    )
