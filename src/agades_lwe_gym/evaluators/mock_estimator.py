from __future__ import annotations

import math

from agades_lwe_gym.dsl.schema import AttackPlan
from agades_lwe_gym.evaluators.base import EstimatorResult
from agades_lwe_gym.validators.consistency import primary_attack_type


class MockEstimatorAdapter:
    """Deterministic CI-safe estimator for toy evaluation plumbing."""

    estimator_name = "mock-lattice-estimator"
    estimator_version = "0.1.0"

    def is_available(self) -> bool:
        return True

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        attack_type = primary_attack_type(plan)
        beta = _max_int_param(plan, "beta", default=max(32, plan.target.n // 2))
        operator_adjustment = _operator_adjustment(plan)
        q_bits = math.log2(plan.target.q)
        module_factor = plan.target.k if plan.target.k is not None else 1
        dimension = plan.target.n * module_factor

        attack_multiplier = {
            "primal_usvp": 1.0,
            "dual_attack": 0.95,
            "dual_hybrid": 0.9,
            "bkw": 1.15,
        }.get(attack_type, 1.1)

        time_bits = max(
            8.0,
            dimension * 0.42 * attack_multiplier
            + q_bits * 1.7
            + beta * 0.72
            - operator_adjustment,
        )
        memory_bits = max(4.0, beta * 0.48 + len(plan.operators) * 2.0)
        success_probability = max(0.05, min(0.99, 0.72 - len(plan.operators) * 0.03))

        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            attack_type=attack_type,
            time_bits=round(time_bits, 4),
            memory_bits=round(memory_bits, 4),
            success_probability=round(success_probability, 4),
            raw_output={
                "dimension": dimension,
                "q_bits": round(q_bits, 4),
                "operator_adjustment": round(operator_adjustment, 4),
            },
            warnings=[
                "Mock estimator output is for plumbing tests only; "
                "it is not cryptanalytic evidence."
            ],
        )


def _max_int_param(plan: AttackPlan, name: str, default: int) -> int:
    values = [
        operator.params[name]
        for operator in plan.operators
        if isinstance(operator.params.get(name), int)
    ]
    return max(values) if values else default


def _operator_adjustment(plan: AttackPlan) -> float:
    adjustment = 0.0
    for operator in plan.operators:
        if operator.type == "modulus_switching":
            q_prime = operator.params.get("q_prime")
            if isinstance(q_prime, int) and q_prime < plan.target.q:
                adjustment += min(8.0, math.log2(plan.target.q / q_prime) * 2.0)
        if operator.type == "secret_guessing":
            guess_dimension = operator.params.get("guess_dimension")
            if isinstance(guess_dimension, int):
                adjustment += min(12.0, guess_dimension * 0.5)
    return adjustment

