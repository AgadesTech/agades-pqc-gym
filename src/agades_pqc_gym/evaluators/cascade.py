from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from agades_pqc_gym.core.assumptions import AssumptionSet
from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.family_adapter import ReproductionResult
from agades_pqc_gym.core.registry import FamilyRegistry
from agades_pqc_gym.evaluators.base import EstimatorAdapter, EstimatorResult
from agades_pqc_gym.evaluators.fitness import compute_fitness
from agades_pqc_gym.evaluators.router import FamilyEvaluatorRouter
from agades_pqc_gym.utils.validation_errors import stable_validation_error_messages
from agades_pqc_gym.validators.assumptions import assumption_penalty
from agades_pqc_gym.validators.static import ValidationResult, validate_attack_plan


class CascadeResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    valid: bool
    plan: AttackPlan | None = None
    validation: ValidationResult
    estimator_result: EstimatorResult | None = None
    reproduction_result: ReproductionResult | None = None
    metrics: dict[str, float | int | str | bool | None]
    warnings: list[str]


class CascadeEvaluator:
    def __init__(
        self,
        estimator: EstimatorAdapter | None = None,
        registry: FamilyRegistry | None = None,
    ) -> None:
        self.router = FamilyEvaluatorRouter(
            registry=registry,
            lattice_estimator=estimator,
        )

    def evaluate_path(self, path: Path) -> CascadeResult:
        try:
            plan = AttackPlan.model_validate_json(path.read_text())
        except OSError as exc:
            validation = ValidationResult(valid=False, errors=[str(exc)])
            fitness = compute_fitness(validation, None)
            return CascadeResult(
                valid=False,
                plan=None,
                validation=validation,
                estimator_result=None,
                reproduction_result=None,
                metrics=fitness.as_metrics(),
                warnings=[],
            )
        except ValidationError as exc:
            validation = ValidationResult(
                valid=False,
                errors=stable_validation_error_messages(exc),
            )
            fitness = compute_fitness(validation, None)
            return CascadeResult(
                valid=False,
                plan=None,
                validation=validation,
                estimator_result=None,
                reproduction_result=None,
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
            metrics = fitness.as_metrics()
            metrics["evaluation_status"] = "invalid"
            return _result_from_parts(plan, validation, None, None, metrics)

        estimator_result = self.router.estimate(plan)
        reproduction_result = self.router.reproduce_downscaled(plan)
        instability_penalty = _instability_penalty(estimator_result)
        fitness = compute_fitness(
            validation,
            estimator_result,
            reproducibility_score=_reproducibility_score(reproduction_result),
            novelty_score=0.2,
            assumption_penalty=plan_assumption_penalty,
            instability_penalty=instability_penalty,
        )
        metrics = fitness.as_metrics()
        metrics.update(_feature_metrics(plan, estimator_result))
        metrics.update(_reproduction_metrics(reproduction_result))
        metrics["evaluation_status"] = estimator_result.evaluation_status
        return _result_from_parts(
            plan,
            validation,
            estimator_result,
            reproduction_result,
            metrics,
        )


def _result_from_parts(
    plan: AttackPlan,
    validation: ValidationResult,
    estimator_result: EstimatorResult | None,
    reproduction_result: ReproductionResult | None,
    metrics: dict[str, Any],
) -> CascadeResult:
    warnings = list(validation.warnings)
    if estimator_result is not None:
        warnings.extend(estimator_result.warnings)
    if reproduction_result is not None:
        warnings.extend(reproduction_result.warnings)
    result_valid = validation.valid and (
        estimator_result is None or estimator_result.evaluation_status == "ok"
    )
    return CascadeResult(
        valid=result_valid,
        plan=plan,
        validation=validation,
        estimator_result=estimator_result,
        reproduction_result=reproduction_result,
        metrics=metrics,
        warnings=warnings,
    )


def _instability_penalty(estimate: EstimatorResult) -> float:
    if estimate.evaluation_status != "ok":
        return 1.0
    if estimate.success_probability is None:
        return 0.1
    if estimate.success_probability < 0.1:
        return 0.5
    return 0.0


def _feature_metrics(
    plan: AttackPlan, estimate: EstimatorResult
) -> dict[str, float | int | str]:
    memory_bucket = "low"
    memory_bits = estimate.memory_bits or 0.0
    if memory_bits >= 96:
        memory_bucket = "high"
    elif memory_bits >= 48:
        memory_bucket = "medium"

    assumption_set = AssumptionSet.from_plan(plan)

    return {
        "feature_family": plan.target.family.value,
        "feature_attack_type": estimate.attack_type,
        "feature_operator_count": len(plan.operators),
        "feature_memory_bucket": memory_bucket,
        "feature_assumption_bucket": assumption_set.bucket,
        "feature_assumption_count": assumption_set.total_count,
        "feature_unique_assumption_count": len(assumption_set.items),
        "feature_risky_assumption_count": assumption_set.risky_occurrence_count,
        "feature_assumption_fingerprint": assumption_set.fingerprint,
        "feature_estimator_model": estimate.estimator_name,
    }


def _reproducibility_score(result: ReproductionResult | None) -> float:
    if result is None:
        return 0.0
    return result.score


def _reproduction_metrics(
    result: ReproductionResult | None,
) -> dict[str, bool | str | None]:
    if result is None:
        return {
            "reproduction_attempted": False,
            "reproduction_status": "not_applicable",
            "reproduction_success": None,
        }
    return {
        "reproduction_attempted": result.attempted,
        "reproduction_status": result.status,
        "reproduction_success": result.success,
    }
