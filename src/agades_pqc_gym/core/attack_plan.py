from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agades_pqc_gym.core.operators import (
    ALLOWED_OPERATORS,
    supported_operators_for_family,
    validate_operator_params,
)
from agades_pqc_gym.core.target import SupportLevel, TargetFamily, TargetSpec


class AttackOperator(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    params: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)

    @field_validator("type")
    @classmethod
    def operator_type_must_be_known(cls, value: str) -> str:
        if value not in ALLOWED_OPERATORS:
            raise ValueError(f"unsupported operator type: {value}")
        return value

    @model_validator(mode="after")
    def validate_params(self) -> AttackOperator:
        errors = validate_operator_params(self.type, self.params)
        if errors:
            raise ValueError("; ".join(errors))
        return self


class Constraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_memory_bits: float | None = Field(default=None, gt=0)
    max_time_bits: float | None = Field(default=None, gt=0)
    require_reproducibility_on_downscaled_instances: bool = False
    downscaled_reproduction_fixture: str | None = None


class Claims(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estimated_time_bits: float | None = Field(default=None, gt=0)
    estimated_memory_bits: float | None = Field(default=None, gt=0)
    success_probability: float | None = Field(default=None, ge=0, le=1)
    external_claim: bool = False
    source: str | None = None

    @model_validator(mode="after")
    def require_source_for_pre_evaluation_claims(self) -> Claims:
        has_claim = any(
            value is not None
            for value in (
                self.estimated_time_bits,
                self.estimated_memory_bits,
                self.success_probability,
            )
        )
        if has_claim and not self.external_claim:
            raise ValueError("pre-evaluation claims require external_claim=true")
        if self.external_claim and not self.source:
            raise ValueError("external_claim requires source")
        return self


class Metadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created_by: str = Field(min_length=1)
    public: bool = True
    notes: str = ""


class AttackPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attack_plan_id: str = Field(min_length=1)
    target: TargetSpec
    operators: list[AttackOperator] = Field(min_length=1)
    constraints: Constraints = Field(default_factory=Constraints)
    claims: Claims = Field(default_factory=Claims)
    metadata: Metadata

    @model_validator(mode="after")
    def validate_cross_field_rules(self) -> AttackPlan:
        operator_types = [operator.type for operator in self.operators]
        supported = supported_operators_for_family(self.target.family)
        unsupported = sorted(set(operator_types) - supported)
        if unsupported:
            raise ValueError(
                f"{self.target.family.value} target does not support operators: "
                f"{', '.join(unsupported)}"
            )
        if (
            "module_lattice_reduction_hypothesis" in operator_types
            and self.target.family is not TargetFamily.MLWE
        ):
            raise ValueError(
                "module_lattice_reduction_hypothesis requires an MLWE target"
            )
        if (
            self.target.family in {TargetFamily.LWE, TargetFamily.MLWE}
            and self.target.support_level is not SupportLevel.IMPLEMENTED
        ):
            raise ValueError("LWE/MLWE targets must use implemented support level")
        return self
