from __future__ import annotations

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.family_adapter import ValidationFinding
from agades_pqc_gym.core.target import TargetSpec
from agades_pqc_gym.families.multivariate.adapter import MultivariateFamilyAdapter


def validate_multivariate_target(target: TargetSpec) -> list[ValidationFinding]:
    return MultivariateFamilyAdapter().validate_target(target)


def validate_multivariate_plan(plan: AttackPlan) -> list[ValidationFinding]:
    return MultivariateFamilyAdapter().validate_plan(plan)
