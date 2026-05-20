from __future__ import annotations

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.family_adapter import ValidationFinding
from agades_pqc_gym.core.target import TargetSpec
from agades_pqc_gym.families.implementation_security.adapter import (
    ImplementationSecurityFamilyAdapter,
)


def validate_implementation_security_target(
    target: TargetSpec,
) -> list[ValidationFinding]:
    return ImplementationSecurityFamilyAdapter().validate_target(target)


def validate_implementation_security_plan(plan: AttackPlan) -> list[ValidationFinding]:
    return ImplementationSecurityFamilyAdapter().validate_plan(plan)
