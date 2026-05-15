from pathlib import Path

from agades_lwe_gym.evaluators.cascade import CascadeEvaluator
from agades_lwe_gym.evaluators.mock_estimator import MockEstimatorAdapter


def test_cascade_returns_openevolve_metrics_for_valid_plan() -> None:
    evaluator = CascadeEvaluator(estimator=MockEstimatorAdapter())

    result = evaluator.evaluate_path(Path("examples/attack_plans/primal_usvp_toy.json"))

    assert result.valid is True
    assert result.metrics["combined_score"] < 0
    assert result.metrics["feature_family"] == "LWE"
    assert result.metrics["feature_attack_type"] == "primal_usvp"


def test_cascade_rejects_invalid_plan_without_estimation() -> None:
    evaluator = CascadeEvaluator(estimator=MockEstimatorAdapter())

    result = evaluator.evaluate_path(
        Path("examples/attack_plans/invalid_plan_should_fail.json")
    )

    assert result.valid is False
    assert result.metrics["combined_score"] == -1e9
    assert result.estimator_result is None
