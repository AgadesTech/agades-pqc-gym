from pathlib import Path

from agades_pqc_gym.core.assumptions import AssumptionSet
from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.validators.assumptions import assumption_penalty


def test_assumption_set_summarizes_plan_assumptions_deterministically() -> None:
    base_plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    plan = base_plan.model_copy(
        update={
            "operators": [
                AttackOperator(
                    type="sample_selection",
                    params={"sample_count": 32},
                    assumptions=[
                        "requires_expert_review",
                        "public_toy_target",
                    ],
                ),
                AttackOperator(
                    type="primal_usvp",
                    params={"beta": 40, "svp_cost_model": "ADPS16"},
                    assumptions=[
                        "public_toy_target",
                        "noise_model_preserved_approximately",
                        "requires_expert_review",
                    ],
                ),
            ]
        }
    )

    assumptions = AssumptionSet.from_plan(plan)

    assert assumptions.items == (
        "noise_model_preserved_approximately",
        "public_toy_target",
        "requires_expert_review",
    )
    assert assumptions.occurrence_counts == {
        "noise_model_preserved_approximately": 1,
        "public_toy_target": 2,
        "requires_expert_review": 2,
    }
    assert assumptions.total_count == 5
    assert assumptions.risky_items == (
        "noise_model_preserved_approximately",
        "requires_expert_review",
    )
    assert assumptions.risky_occurrence_count == 3
    assert assumptions.risk_score == 0.75
    assert len(assumptions.fingerprint) == 64


def test_assumption_penalty_uses_assumption_set_risk_score() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    ).model_copy(
        update={
            "operators": [
                AttackOperator(
                    type="primal_usvp",
                    params={"beta": 40, "svp_cost_model": "ADPS16"},
                    assumptions=[
                        "requires_expert_review",
                        "noise_model_preserved_approximately",
                    ],
                )
            ]
        }
    )

    assert assumption_penalty(plan) == AssumptionSet.from_plan(plan).risk_score
