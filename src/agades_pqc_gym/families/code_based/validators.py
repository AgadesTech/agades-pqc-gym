from __future__ import annotations

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.family_adapter import ValidationFinding
from agades_pqc_gym.core.target import TargetSpec
from agades_pqc_gym.families.code_based.adapter import CodeBasedFamilyAdapter


def validate_code_based_target(target: TargetSpec) -> list[ValidationFinding]:
    return CodeBasedFamilyAdapter().validate_target(target)


def validate_code_based_plan(plan: AttackPlan) -> list[ValidationFinding]:
    return CodeBasedFamilyAdapter().validate_plan(plan)
