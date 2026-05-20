from __future__ import annotations

from agades_pqc_gym.core.assumptions import AssumptionSet
from agades_pqc_gym.core.attack_plan import AttackPlan


def assumption_penalty(plan: AttackPlan) -> float:
    return AssumptionSet.from_plan(plan).risk_score
