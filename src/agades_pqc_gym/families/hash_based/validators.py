from __future__ import annotations

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.family_adapter import ValidationFinding
from agades_pqc_gym.core.target import TargetSpec
from agades_pqc_gym.families.hash_based.adapter import HashBasedFamilyAdapter


def validate_hash_based_target(target: TargetSpec) -> list[ValidationFinding]:
    return HashBasedFamilyAdapter().validate_target(target)


def validate_hash_based_plan(plan: AttackPlan) -> list[ValidationFinding]:
    return HashBasedFamilyAdapter().validate_plan(plan)
