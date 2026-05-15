from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from agades_lwe_gym.dsl.operators import ALLOWED_OPERATORS, validate_operator_params


class TargetFamily(StrEnum):
    LWE = "LWE"
    MLWE = "MLWE"
    NTRU = "NTRU"
    SIS = "SIS"


class Distribution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1)
    hamming_weight: int | None = Field(default=None, ge=0)
    sigma: float | None = Field(default=None, gt=0)
    eta: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_distribution_parameters(self) -> Distribution:
        if self.type == "discrete_gaussian" and self.sigma is None:
            raise ValueError("discrete_gaussian distributions require sigma")
        if self.type == "centered_binomial" and self.eta is None:
            raise ValueError("centered_binomial distributions require eta")
        return self


class Target(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: TargetFamily
    name: str = Field(min_length=1)
    n: int = Field(gt=0)
    q: int = Field(gt=1)
    m: int | None = Field(default=None, gt=0)
    k: int | None = Field(default=None, gt=0)
    secret_distribution: Distribution
    error_distribution: Distribution
    claimed_security_bits: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_family_shape(self) -> Target:
        if self.family is TargetFamily.MLWE and self.k is None:
            raise ValueError("MLWE targets require module rank k")
        return self


class Operator(BaseModel):
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
    def validate_params(self) -> Operator:
        errors = validate_operator_params(self.type, self.params)
        if errors:
            raise ValueError("; ".join(errors))
        return self


class Constraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_memory_bits: float | None = Field(default=None, gt=0)
    max_time_bits: float | None = Field(default=None, gt=0)
    require_reproducibility_on_downscaled_instances: bool = False


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
    target: Target
    operators: list[Operator] = Field(min_length=1)
    constraints: Constraints = Field(default_factory=Constraints)
    claims: Claims = Field(default_factory=Claims)
    metadata: Metadata

    @model_validator(mode="after")
    def validate_cross_field_rules(self, info: ValidationInfo) -> AttackPlan:
        del info
        operator_types = [operator.type for operator in self.operators]
        if (
            "module_lattice_reduction_hypothesis" in operator_types
            and self.target.family is not TargetFamily.MLWE
        ):
            raise ValueError(
                "module_lattice_reduction_hypothesis requires an MLWE target"
            )
        if self.target.family not in {TargetFamily.LWE, TargetFamily.MLWE}:
            raise ValueError(
                f"{self.target.family.value} targets are not supported in MVP"
            )
        return self
