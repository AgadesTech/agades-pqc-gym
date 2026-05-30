from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from agades_pqc_gym import __version__
from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.evaluators.base import EstimatorAdapter
from agades_pqc_gym.evaluators.cascade import CascadeEvaluator, CascadeResult
from agades_pqc_gym.evaluators.fitness import compute_fitness
from agades_pqc_gym.evaluators.lattice_estimator import LatticeEstimatorAdapter
from agades_pqc_gym.evaluators.mock_estimator import MockEstimatorAdapter
from agades_pqc_gym.utils.validation_errors import stable_validation_error_messages
from agades_pqc_gym.validators.static import ValidationResult

EstimatorChoice = Literal["mock", "lattice"]
PUBLIC_VERIFIER_SCHEMA = "agades.pqc.verifier.v1"


class VerifierFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: str | None
    attack_type: str | None
    operator_count: int | None
    memory_bucket: str | None
    assumption_bucket: str | None
    assumption_count: int | None
    unique_assumption_count: int | None
    risky_assumption_count: int | None
    assumption_fingerprint: str | None
    estimator_model: str | None


class VerifierEstimator(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str | None
    name: str | None
    version: str | None
    commit: str | None
    attack_type: str | None


class VerifierReproduction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempted: bool
    status: str
    success: bool | None
    score: float
    warnings: list[str]


class VerifierSafety(BaseModel):
    model_config = ConfigDict(extra="forbid")

    arbitrary_code_execution: bool
    live_targeting: bool
    security_claim: bool


class VerifierResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["agades.pqc.verifier.v1"]
    verifier_version: str
    attack_plan_id: str | None
    target_family: str | None
    schema_valid: bool
    accepted: bool
    evaluation_status: str
    combined_score: float | None
    estimated_time_bits: float | None
    estimated_memory_bits: float | None
    validity_score: float | None
    reproducibility_score: float | None
    novelty_score: float | None
    assumption_penalty: float | None
    instability_penalty: float | None
    features: VerifierFeatures
    estimator: VerifierEstimator
    reproduction: VerifierReproduction
    warnings: list[str]
    validation_errors: list[str]
    safety: VerifierSafety


def verify_attack_plan_path(
    path: Path,
    *,
    estimator: EstimatorChoice = "mock",
    estimator_cache: Path | None = None,
) -> dict[str, Any]:
    return verify_attack_plan_json(
        path.read_text(encoding="utf-8"),
        estimator=estimator,
        estimator_cache=estimator_cache,
    )


def verify_attack_plan_json(
    raw_json: str,
    *,
    estimator: EstimatorChoice = "mock",
    estimator_cache: Path | None = None,
) -> dict[str, Any]:
    try:
        plan = AttackPlan.model_validate_json(raw_json)
    except ValidationError as exc:
        validation = ValidationResult(
            valid=False,
            errors=stable_validation_error_messages(exc),
        )
        metrics = compute_fitness(validation, None).as_metrics()
        metrics["evaluation_status"] = "invalid"
        return _public_response(
            result=CascadeResult(
                valid=False,
                plan=None,
                validation=validation,
                estimator_result=None,
                metrics=metrics,
                warnings=[],
            )
        )

    evaluator = CascadeEvaluator(
        estimator=_build_lattice_estimator(
            estimator=estimator,
            estimator_cache=estimator_cache,
        )
    )
    return _public_response(result=evaluator.evaluate_plan(plan))


def _build_lattice_estimator(
    *,
    estimator: EstimatorChoice,
    estimator_cache: Path | None,
) -> EstimatorAdapter:
    if estimator == "mock":
        return MockEstimatorAdapter()
    if estimator == "lattice":
        return LatticeEstimatorAdapter(cache_path=estimator_cache)
    raise ValueError(f"unsupported estimator backend: {estimator}")


def _public_response(result: CascadeResult) -> dict[str, Any]:
    metrics = result.metrics
    estimator = result.estimator_result
    reproduction = result.reproduction_result
    plan = result.plan
    response = VerifierResult(
        schema_version=PUBLIC_VERIFIER_SCHEMA,
        verifier_version=__version__,
        attack_plan_id=plan.attack_plan_id if plan else None,
        target_family=plan.target.family.value if plan else None,
        schema_valid=result.validation.valid,
        accepted=result.valid,
        evaluation_status=metrics.get("evaluation_status", "invalid"),
        combined_score=metrics.get("combined_score"),
        estimated_time_bits=metrics.get("estimated_time_bits"),
        estimated_memory_bits=metrics.get("estimated_memory_bits"),
        validity_score=metrics.get("validity_score"),
        reproducibility_score=metrics.get("reproducibility_score"),
        novelty_score=metrics.get("novelty_score"),
        assumption_penalty=metrics.get("assumption_penalty"),
        instability_penalty=metrics.get("instability_penalty"),
        features=VerifierFeatures(
            family=metrics.get("feature_family"),
            attack_type=metrics.get("feature_attack_type"),
            operator_count=metrics.get("feature_operator_count"),
            memory_bucket=metrics.get("feature_memory_bucket"),
            assumption_bucket=metrics.get("feature_assumption_bucket"),
            assumption_count=metrics.get("feature_assumption_count"),
            unique_assumption_count=metrics.get("feature_unique_assumption_count"),
            risky_assumption_count=metrics.get("feature_risky_assumption_count"),
            assumption_fingerprint=metrics.get("feature_assumption_fingerprint"),
            estimator_model=metrics.get("feature_estimator_model"),
        ),
        estimator=VerifierEstimator(
            schema_version=estimator.schema_version if estimator else None,
            name=estimator.estimator_name if estimator else None,
            version=estimator.estimator_version if estimator else None,
            commit=estimator.estimator_commit if estimator else None,
            attack_type=estimator.attack_type if estimator else None,
        ),
        reproduction=VerifierReproduction(
            attempted=reproduction.attempted if reproduction else False,
            status=reproduction.status if reproduction else "not_applicable",
            success=reproduction.success if reproduction else None,
            score=reproduction.score if reproduction else 0.0,
            warnings=reproduction.warnings if reproduction else [],
        ),
        warnings=result.warnings,
        validation_errors=result.validation.errors,
        safety=VerifierSafety(
            arbitrary_code_execution=False,
            live_targeting=False,
            security_claim=False,
        ),
    )
    return response.model_dump(mode="json")
