from __future__ import annotations

from typing import Protocol

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.evaluator_result import EvaluatorResult

EstimatorResult = EvaluatorResult


class EstimatorAdapter(Protocol):
    def is_available(self) -> bool:
        ...

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        ...


class EstimatorUnavailable(RuntimeError):
    pass
