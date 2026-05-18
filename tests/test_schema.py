from pathlib import Path

import pytest
from pydantic import ValidationError

from agades_pqc_gym.core.attack_plan import AttackPlan, TargetFamily


def test_valid_primal_plan_loads() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )

    assert plan.attack_plan_id == "lattice_primal_usvp_toy_v1"
    assert plan.target.family is TargetFamily.LWE
    assert plan.operators[0].type == "primal_usvp"


def test_module_hypothesis_requires_module_family() -> None:
    with pytest.raises(ValidationError, match="module_lattice_reduction_hypothesis"):
        AttackPlan.model_validate_json(
            Path("examples/attack_plans/invalid_plan_should_fail.json").read_text()
        )


def test_claims_require_external_source_before_evaluation() -> None:
    data = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    ).model_dump()
    data["claims"]["estimated_time_bits"] = 64.0

    with pytest.raises(ValidationError, match="external_claim"):
        AttackPlan.model_validate(data)

