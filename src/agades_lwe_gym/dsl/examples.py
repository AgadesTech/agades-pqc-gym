from __future__ import annotations

from agades_lwe_gym.dsl.schema import (
    AttackPlan,
    Claims,
    Constraints,
    Metadata,
    Operator,
    Target,
)


def seed_primal_plan(target: Target, attack_plan_id: str) -> AttackPlan:
    beta = max(32, min(80, target.n // 2))
    return AttackPlan(
        attack_plan_id=attack_plan_id,
        target=target,
        operators=[
            Operator(
                type="primal_usvp",
                params={"beta": beta, "svp_cost_model": "ADPS16"},
                assumptions=["lattice_estimator_default_cost_model"],
            )
        ],
        constraints=Constraints(
            max_memory_bits=max(64.0, beta * 1.5),
            max_time_bits=max(96.0, target.n * 2.0),
            require_reproducibility_on_downscaled_instances=False,
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="benchmark_seed",
            public=True,
            notes="Generated seed plan for benchmark smoke evaluation.",
        ),
    )
