from __future__ import annotations

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.family_adapter import ReproductionResult
from agades_pqc_gym.core.registry import FamilyRegistry, default_family_registry
from agades_pqc_gym.evaluators.base import EstimatorAdapter, EstimatorResult


class FamilyEvaluatorRouter:
    def __init__(
        self,
        *,
        registry: FamilyRegistry | None = None,
        lattice_estimator: EstimatorAdapter | None = None,
    ) -> None:
        self.registry = registry or default_family_registry(
            lattice_estimator=lattice_estimator
        )

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        return self.registry.get(plan.target.family).estimate(plan)

    def reproduce_downscaled(self, plan: AttackPlan) -> ReproductionResult | None:
        return self.registry.get(plan.target.family).reproduce_downscaled(plan)
