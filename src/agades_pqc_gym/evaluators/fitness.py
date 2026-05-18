from __future__ import annotations

from agades_pqc_gym.core.fitness import FitnessReport
from agades_pqc_gym.evaluators.base import EstimatorResult
from agades_pqc_gym.validators.static import ValidationResult


def compute_fitness(
    validation: ValidationResult,
    estimate: EstimatorResult | None,
    *,
    reproducibility_score: float = 0.0,
    novelty_score: float = 0.2,
    assumption_penalty: float = 0.0,
    instability_penalty: float = 0.0,
) -> FitnessReport:
    if (
        not validation.valid
        or estimate is None
        or estimate.evaluation_status != "ok"
        or estimate.time_bits is None
        or estimate.memory_bits is None
    ):
        return FitnessReport(
            combined_score=-1e9,
            estimated_time_bits=None,
            estimated_memory_bits=None,
            validity_score=0.0,
            reproducibility_score=0.0,
            novelty_score=0.0,
            assumption_penalty=assumption_penalty,
            instability_penalty=instability_penalty,
        )

    combined_score = (
        -estimate.time_bits
        - 0.25 * estimate.memory_bits
        + 5.0 * reproducibility_score
        + 2.0 * novelty_score
        - 10.0 * assumption_penalty
        - 50.0 * instability_penalty
    )
    return FitnessReport(
        combined_score=round(combined_score, 4),
        estimated_time_bits=estimate.time_bits,
        estimated_memory_bits=estimate.memory_bits,
        validity_score=1.0,
        reproducibility_score=reproducibility_score,
        novelty_score=novelty_score,
        assumption_penalty=assumption_penalty,
        instability_penalty=instability_penalty,
    )
