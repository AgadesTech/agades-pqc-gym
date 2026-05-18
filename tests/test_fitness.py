from agades_pqc_gym.core import FitnessReport
from agades_pqc_gym.core.fitness import FITNESS_REPORT_SCHEMA
from agades_pqc_gym.evaluators.base import EstimatorResult
from agades_pqc_gym.evaluators.fitness import compute_fitness
from agades_pqc_gym.validators.static import ValidationResult


def test_fitness_rewards_lower_time_cost() -> None:
    validation = ValidationResult(valid=True)
    slow = EstimatorResult(
        estimator_name="mock",
        estimator_version="0",
        estimator_commit=None,
        attack_type="primal_usvp",
        time_bits=120.0,
        memory_bits=40.0,
    )
    fast = slow.model_copy(update={"time_bits": 100.0})

    assert compute_fitness(validation, fast).combined_score > compute_fitness(
        validation, slow
    ).combined_score


def test_compute_fitness_returns_core_fitness_report_contract() -> None:
    validation = ValidationResult(valid=True)
    estimate = EstimatorResult(
        estimator_name="mock",
        estimator_version="0",
        estimator_commit=None,
        attack_type="primal_usvp",
        time_bits=80.0,
        memory_bits=20.0,
    )

    fitness = compute_fitness(validation, estimate)

    assert isinstance(fitness, FitnessReport)
    assert fitness.schema_version == FITNESS_REPORT_SCHEMA
    metrics = fitness.as_metrics()
    assert metrics["fitness_schema_version"] == FITNESS_REPORT_SCHEMA
    assert "schema_version" not in metrics
    assert metrics["combined_score"] == fitness.combined_score


def test_invalid_plan_gets_rejection_score() -> None:
    validation = ValidationResult(valid=False, errors=["bad plan"])
    estimate = EstimatorResult(
        estimator_name="mock",
        estimator_version="0",
        estimator_commit=None,
        attack_type="primal_usvp",
        time_bits=80.0,
        memory_bits=20.0,
    )

    fitness = compute_fitness(validation, estimate)

    assert fitness.combined_score == -1e9
    assert fitness.validity_score == 0.0
