from __future__ import annotations

from agades_pqc_gym.core.attack_plan import AttackPlan


def primary_attack_type(plan: AttackPlan) -> str:
    for operator in reversed(plan.operators):
        if operator.type in {
            "primal_usvp",
            "bounded_distance_decoding",
            "dual_attack",
            "dual_hybrid",
            "bkw",
        }:
            return operator.type
    return plan.operators[-1].type
