from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from agades_lwe_gym.dsl.schema import AttackPlan


class EstimatorResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estimator_name: str
    estimator_version: str | None
    estimator_commit: str | None
    attack_type: str
    time_bits: float
    memory_bits: float
    success_probability: float | None = None
    raw_output: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class EstimatorAdapter(Protocol):
    def is_available(self) -> bool:
        ...

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        ...


class EstimatorUnavailable(RuntimeError):
    pass

