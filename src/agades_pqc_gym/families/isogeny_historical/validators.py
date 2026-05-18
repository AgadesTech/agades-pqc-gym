from __future__ import annotations

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.family_adapter import ValidationFinding
from agades_pqc_gym.core.target import TargetSpec
from agades_pqc_gym.families.isogeny_historical.adapter import (
    IsogenyHistoricalFamilyAdapter,
)


def validate_isogeny_historical_target(
    target: TargetSpec,
) -> list[ValidationFinding]:
    return IsogenyHistoricalFamilyAdapter().validate_target(target)


def validate_isogeny_historical_plan(plan: AttackPlan) -> list[ValidationFinding]:
    return IsogenyHistoricalFamilyAdapter().validate_plan(plan)
