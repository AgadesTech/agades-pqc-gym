from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from agades_lwe_gym.evaluators.base import EstimatorResult
from agades_lwe_gym.validators.static import ValidationResult


class FitnessResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    combined_score: float
    estimated_time_bits: float | None
    estimated_memory_bits: float | None
    validity_score: float
    reproducibility_score: float
    novelty_score: float
    assumption_penalty: float
    instability_penalty: float

    def as_metrics(self) -> dict[str, float]:
        return self.model_dump()


def compute_fitness(
    validation: ValidationResult,
    estimate: EstimatorResult | None,
    *,
    reproducibility_score: float = 0.0,
    novelty_score: float = 0.2,
    assumption_penalty: float = 0.0,
    instability_penalty: float = 0.0,
) -> FitnessResult:
    if not validation.valid or estimate is None:
        return FitnessResult(
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
    return FitnessResult(
        combined_score=round(combined_score, 4),
        estimated_time_bits=estimate.time_bits,
        estimated_memory_bits=estimate.memory_bits,
        validity_score=1.0,
        reproducibility_score=reproducibility_score,
        novelty_score=novelty_score,
        assumption_penalty=assumption_penalty,
        instability_penalty=instability_penalty,
    )

