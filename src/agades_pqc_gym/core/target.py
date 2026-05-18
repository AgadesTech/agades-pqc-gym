from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TargetFamily(StrEnum):
    LWE = "LWE"
    MLWE = "MLWE"
    NTRU = "NTRU"
    SIS = "SIS"
    CODE_BASED = "CODE_BASED"
    MULTIVARIATE = "MULTIVARIATE"
    HASH_BASED = "HASH_BASED"
    ISOGENY_HISTORICAL = "ISOGENY_HISTORICAL"
    IMPLEMENTATION_SECURITY = "IMPLEMENTATION_SECURITY"


class SupportLevel(StrEnum):
    IMPLEMENTED = "implemented"
    SCHEMA_ONLY = "schema_only"
    PLACEHOLDER = "placeholder"


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


class TargetSpec(BaseModel):
    """Family-agnostic target schema with reviewed family-specific fields."""

    model_config = ConfigDict(extra="forbid")

    family: TargetFamily
    name: str = Field(min_length=1)
    support_level: SupportLevel = SupportLevel.IMPLEMENTED
    claimed_security_bits: float | None = Field(default=None, gt=0)

    # Lattice and code-based shared numeric fields.
    n: int | None = Field(default=None, gt=0)
    q: int | None = Field(default=None, gt=1)
    m: int | None = Field(default=None, gt=0)
    k: int | None = Field(default=None, gt=0)
    w: int | None = Field(default=None, gt=0)
    secret_distribution: Distribution | None = None
    error_distribution: Distribution | None = None

    # Multivariate fields.
    variables: int | None = Field(default=None, gt=0)
    equations: int | None = Field(default=None, gt=0)
    field: str | None = None

    # Hash-based fields.
    hash_function: str | None = None

    @model_validator(mode="after")
    def validate_family_shape(self) -> TargetSpec:
        lattice_families = {
            TargetFamily.LWE,
            TargetFamily.MLWE,
            TargetFamily.NTRU,
            TargetFamily.SIS,
        }
        if self.family in lattice_families:
            self._require_fields("n", "q")
            if self.secret_distribution is None:
                raise ValueError(
                    f"{self.family.value} targets require secret_distribution"
                )
            if self.error_distribution is None and self.family in {
                TargetFamily.LWE,
                TargetFamily.MLWE,
            }:
                raise ValueError(
                    f"{self.family.value} targets require error_distribution"
                )
            if self.family is TargetFamily.MLWE and self.k is None:
                raise ValueError("MLWE targets require module rank k")
            if self.family in {TargetFamily.NTRU, TargetFamily.SIS}:
                self._require_schema_only()
        elif self.family is TargetFamily.CODE_BASED:
            self._require_fields("n", "k", "w")
        elif self.family is TargetFamily.MULTIVARIATE:
            self._require_fields("variables", "equations")
            if self.field is None:
                raise ValueError("MULTIVARIATE targets require field")
        elif self.family is TargetFamily.HASH_BASED:
            if self.hash_function is None:
                raise ValueError("HASH_BASED targets require hash_function")
        elif self.family is TargetFamily.ISOGENY_HISTORICAL:
            self._require_fields("n")
        elif self.family is TargetFamily.IMPLEMENTATION_SECURITY:
            pass
        return self

    def _require_fields(self, *field_names: str) -> None:
        for field_name in field_names:
            if getattr(self, field_name) is None:
                raise ValueError(f"{self.family.value} targets require {field_name}")

    def _require_schema_only(self) -> None:
        if self.support_level is not SupportLevel.SCHEMA_ONLY:
            raise ValueError(
                f"{self.family.value} targets are schema_only until a reviewed "
                "family evaluator is implemented"
            )
