from __future__ import annotations

from pydantic import BaseModel, Field

from agades_lwe_gym.dsl.schema import AttackPlan


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def validate_attack_plan(plan: AttackPlan) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    memory_floor = _plausible_memory_floor_bits(plan)
    if (
        plan.constraints.max_memory_bits is not None
        and plan.constraints.max_memory_bits < memory_floor
    ):
        errors.append(
            "max_memory_bits is below the conservative memory floor "
            f"for the selected operators ({memory_floor:.1f})"
        )

    time_floor = _plausible_time_floor_bits(plan)
    if (
        plan.constraints.max_time_bits is not None
        and plan.constraints.max_time_bits < time_floor
    ):
        errors.append(
            "max_time_bits is below the conservative time floor "
            f"for the selected target/operators ({time_floor:.1f})"
        )

    if not plan.metadata.public:
        warnings.append("plan is marked private and must not be exported publicly")

    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)


def _plausible_memory_floor_bits(plan: AttackPlan) -> float:
    floor = 8.0
    for operator in plan.operators:
        beta = operator.params.get("beta")
        if isinstance(beta, int):
            floor = max(floor, beta * 0.5)
        zeta = operator.params.get("zeta")
        if isinstance(zeta, int):
            floor = max(floor, zeta * 1.5)
    return floor


def _plausible_time_floor_bits(plan: AttackPlan) -> float:
    operator_count_cost = 2.0 * len(plan.operators)
    dimension_cost = max(8.0, plan.target.n / 8.0)
    return dimension_cost + operator_count_cost
