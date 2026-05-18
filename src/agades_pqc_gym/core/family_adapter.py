from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.target import TargetFamily, TargetSpec
from agades_pqc_gym.evaluators.base import EstimatorResult


class ValidationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: str
    message: str
    code: str


class ReproductionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempted: bool
    status: Literal[
        "not_requested",
        "not_applicable",
        "estimator_reproduced",
        "instance_solved",
        "failed",
    ]
    success: bool | None = None
    score: float = 0.0
    warnings: list[str] = Field(default_factory=list)


class FamilyAdapter(Protocol):
    family: TargetFamily
    support_level: str

    def validate_target(self, target: TargetSpec) -> list[ValidationFinding]:
        ...

    def validate_plan(self, plan: AttackPlan) -> list[ValidationFinding]:
        ...

    def supported_operators(self) -> set[str]:
        ...

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        ...

    def reproduce_downscaled(self, plan: AttackPlan) -> ReproductionResult | None:
        ...
