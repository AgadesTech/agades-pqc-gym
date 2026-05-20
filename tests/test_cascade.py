from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackPlan, Constraints
from agades_pqc_gym.evaluators.cascade import CascadeEvaluator
from agades_pqc_gym.evaluators.mock_estimator import MockEstimatorAdapter


def test_cascade_returns_openevolve_metrics_for_valid_plan() -> None:
    evaluator = CascadeEvaluator(estimator=MockEstimatorAdapter())

    result = evaluator.evaluate_path(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json")
    )

    assert result.valid is True
    assert result.metrics["combined_score"] < 0
    assert result.metrics["feature_family"] == "LWE"
    assert result.metrics["feature_attack_type"] == "primal_usvp"
    assert result.metrics["reproduction_status"] == "not_requested"


def test_cascade_exposes_structured_assumption_set_metrics() -> None:
    evaluator = CascadeEvaluator(estimator=MockEstimatorAdapter())
    base_plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    plan = base_plan.model_copy(
        update={
            "operators": [
                base_plan.operators[0].model_copy(
                    update={
                        "assumptions": [
                            "requires_expert_review",
                            "noise_model_preserved_approximately",
                        ]
                    }
                )
            ]
        }
    )

    result = evaluator.evaluate_plan(plan)

    assert result.metrics["feature_assumption_count"] == 2
    assert result.metrics["feature_unique_assumption_count"] == 2
    assert result.metrics["feature_risky_assumption_count"] == 2
    assert result.metrics["assumption_penalty"] == 0.5
    assert isinstance(result.metrics["feature_assumption_fingerprint"], str)
    assert len(result.metrics["feature_assumption_fingerprint"]) == 64


def test_cascade_rejects_invalid_plan_without_estimation() -> None:
    evaluator = CascadeEvaluator(estimator=MockEstimatorAdapter())

    result = evaluator.evaluate_path(
        Path("examples/attack_plans/invalid_plan_should_fail.json")
    )

    assert result.valid is False
    assert result.metrics["combined_score"] == -1e9
    assert result.estimator_result is None


def test_cascade_scores_requested_downscaled_reproduction_smoke() -> None:
    evaluator = CascadeEvaluator(estimator=MockEstimatorAdapter())
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    ).model_copy(
        update={
            "constraints": Constraints(
                max_memory_bits=80.0,
                max_time_bits=128.0,
                require_reproducibility_on_downscaled_instances=True,
            )
        }
    )

    result = evaluator.evaluate_plan(plan)

    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "estimator_reproduced"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "estimator_reproduced"
    assert result.metrics["reproducibility_score"] == 0.2


def test_cascade_scores_public_downscaled_lwe_instance_solution() -> None:
    evaluator = CascadeEvaluator(estimator=MockEstimatorAdapter())

    result = evaluator.evaluate_path(
        Path("examples/attack_plans/lattice_downscaled_lwe_instance_solve_toy.json")
    )

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4


def test_cascade_scores_second_public_downscaled_lwe_instance_solution() -> None:
    evaluator = CascadeEvaluator(estimator=MockEstimatorAdapter())

    result = evaluator.evaluate_path(
        Path(
            "examples/attack_plans/"
            "lattice_downscaled_lwe_instance_solve_n5_q19_toy.json"
        )
    )

    assert result.valid is True
    assert result.reproduction_result is not None
    assert result.reproduction_result.status == "instance_solved"
    assert result.metrics["reproduction_attempted"] is True
    assert result.metrics["reproduction_status"] == "instance_solved"
    assert result.metrics["reproducibility_score"] == 0.4
