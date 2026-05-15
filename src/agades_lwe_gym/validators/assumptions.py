from __future__ import annotations

from agades_lwe_gym.dsl.schema import AttackPlan


def assumption_penalty(plan: AttackPlan) -> float:
    risky_assumptions = {
        "requires_expert_review",
        "noise_model_preserved_approximately",
    }
    count = sum(
        1
        for operator in plan.operators
        for assumption in operator.assumptions
        if assumption in risky_assumptions
    )
    return min(1.0, count * 0.25)

