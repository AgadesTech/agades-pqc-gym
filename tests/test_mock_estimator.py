from pathlib import Path

from agades_lwe_gym.dsl.schema import AttackPlan
from agades_lwe_gym.evaluators.mock_estimator import MockEstimatorAdapter


def test_mock_estimator_is_deterministic() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/dual_hybrid_toy.json").read_text()
    )
    adapter = MockEstimatorAdapter()

    first = adapter.estimate(plan)
    second = adapter.estimate(plan)

    assert first == second
    assert first.estimator_name == "mock-lattice-estimator"
    assert first.attack_type == "dual_hybrid"
    assert first.time_bits > 0
    assert first.memory_bits > 0
    assert "mock" in first.warnings[0].lower()

