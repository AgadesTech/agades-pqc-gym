from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from agades_lwe_gym.dsl.schema import AttackPlan
from agades_lwe_gym.evaluators.base import EstimatorAdapter, EstimatorResult
from agades_lwe_gym.evaluators.fitness import compute_fitness
from agades_lwe_gym.evaluators.mock_estimator import MockEstimatorAdapter
from agades_lwe_gym.validators.assumptions import assumption_penalty
from agades_lwe_gym.validators.static import ValidationResult, validate_attack_plan


class CascadeResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    valid: bool
    plan: AttackPlan | None = None
    validation: ValidationResult
    estimator_result: EstimatorResult | None = None
    metrics: dict[str, float | int | str | bool | None]
    warnings: list[str]


class CascadeEvaluator:
    def __init__(self, estimator: EstimatorAdapter | None = None) -> None:
        self.estimator = estimator or MockEstimatorAdapter()

    def evaluate_path(self, path: Path) -> CascadeResult:
        try:
            plan = AttackPlan.model_validate_json(path.read_text())
        except (OSError, ValidationError) as exc:
            validation = ValidationResult(valid=False, errors=[str(exc)])
            fitness = compute_fitness(validation, None)
            return CascadeResult(
                valid=False,
                plan=None,
                validation=validation,
                estimator_result=None,
                metrics=fitness.as_metrics(),
                warnings=[],
            )

        return self.evaluate_plan(plan)

    def evaluate_plan(self, plan: AttackPlan) -> CascadeResult:
        validation = validate_attack_plan(plan)
        plan_assumption_penalty = assumption_penalty(plan)
        if not validation.valid:
            fitness = compute_fitness(
                validation,
                None,
                assumption_penalty=plan_assumption_penalty,
            )
            return _result_from_parts(plan, validation, None, fitness.as_metrics())

        estimator_result = self.estimator.estimate(plan)
        instability_penalty = _instability_penalty(estimator_result)
        fitness = compute_fitness(
            validation,
            estimator_result,
            reproducibility_score=0.0,
            novelty_score=0.2,
            assumption_penalty=plan_assumption_penalty,
            instability_penalty=instability_penalty,
        )
        metrics = fitness.as_metrics()
        metrics.update(_feature_metrics(plan, estimator_result))
        return _result_from_parts(plan, validation, estimator_result, metrics)


def _result_from_parts(
    plan: AttackPlan,
    validation: ValidationResult,
    estimator_result: EstimatorResult | None,
    metrics: dict[str, Any],
) -> CascadeResult:
    warnings = list(validation.warnings)
    if estimator_result is not None:
        warnings.extend(estimator_result.warnings)
    return CascadeResult(
        valid=validation.valid,
        plan=plan,
        validation=validation,
        estimator_result=estimator_result,
        metrics=metrics,
        warnings=warnings,
    )


def _instability_penalty(estimate: EstimatorResult) -> float:
    if estimate.success_probability is None:
        return 0.1
    if estimate.success_probability < 0.1:
        return 0.5
    return 0.0


def _feature_metrics(
    plan: AttackPlan, estimate: EstimatorResult
) -> dict[str, float | int | str]:
    memory_bucket = "low"
    if estimate.memory_bits >= 96:
        memory_bucket = "high"
    elif estimate.memory_bits >= 48:
        memory_bucket = "medium"

    assumption_count = sum(len(operator.assumptions) for operator in plan.operators)
    assumption_bucket = "none"
    if assumption_count >= 4:
        assumption_bucket = "many"
    elif assumption_count:
        assumption_bucket = "some"

    return {
        "feature_family": plan.target.family.value,
        "feature_attack_type": estimate.attack_type,
        "feature_operator_count": len(plan.operators),
        "feature_memory_bucket": memory_bucket,
        "feature_assumption_bucket": assumption_bucket,
        "feature_estimator_model": estimate.estimator_name,
    }

