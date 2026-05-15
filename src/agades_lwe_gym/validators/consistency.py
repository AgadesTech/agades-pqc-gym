from __future__ import annotations

from agades_lwe_gym.dsl.schema import AttackPlan


def primary_attack_type(plan: AttackPlan) -> str:
    for operator in reversed(plan.operators):
        if operator.type in {"primal_usvp", "dual_attack", "dual_hybrid", "bkw"}:
            return operator.type
    return plan.operators[-1].type

