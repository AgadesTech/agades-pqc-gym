from __future__ import annotations

import importlib.util

from agades_lwe_gym.dsl.schema import AttackPlan
from agades_lwe_gym.evaluators.base import EstimatorResult, EstimatorUnavailable


class LatticeEstimatorAdapter:
    """Conservative boundary for the real Lattice Estimator.

    The MVP intentionally does not infer unsupported mappings. A future adapter
    should pin an estimator commit and map each DSL operator to a reviewed call.
    """

    estimator_name = "lattice-estimator"

    def is_available(self) -> bool:
        return importlib.util.find_spec("estimator") is not None

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        del plan
        if not self.is_available():
            raise EstimatorUnavailable(
                "Lattice Estimator Python module is not importable in this environment"
            )
        raise EstimatorUnavailable(
            "Real Lattice Estimator mapping is not implemented for this DSL yet"
        )

