from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.validators.static import validate_attack_plan


def test_static_validator_accepts_valid_plan() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_dual_hybrid_toy.json").read_text()
    )

    result = validate_attack_plan(plan)

    assert result.valid is True
    assert result.errors == []


def test_static_validator_reports_budget_violation() -> None:
    data = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_dual_hybrid_toy.json").read_text()
    ).model_dump()
    data["constraints"]["max_memory_bits"] = 1.0
    plan = AttackPlan.model_validate(data)

    result = validate_attack_plan(plan)

    assert result.valid is False
    assert any("max_memory_bits" in error for error in result.errors)

