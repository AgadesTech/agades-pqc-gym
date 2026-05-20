from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.utils.hashing import stable_sha256

RISKY_ASSUMPTIONS = frozenset(
    {
        "requires_expert_review",
        "noise_model_preserved_approximately",
    }
)


class AssumptionSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: tuple[str, ...] = Field(default_factory=tuple)
    occurrence_counts: dict[str, int] = Field(default_factory=dict)

    @classmethod
    def from_plan(cls, plan: AttackPlan) -> AssumptionSet:
        return cls.from_sequences(operator.assumptions for operator in plan.operators)

    @classmethod
    def from_sequences(cls, assumptions: Iterable[Iterable[str]]) -> AssumptionSet:
        counter: Counter[str] = Counter()
        for sequence in assumptions:
            counter.update(str(item) for item in sequence)
        items = tuple(sorted(counter))
        return cls(
            items=items,
            occurrence_counts={item: counter[item] for item in items},
        )

    @model_validator(mode="after")
    def validate_consistency(self) -> AssumptionSet:
        if tuple(sorted(set(self.items))) != self.items:
            raise ValueError("AssumptionSet items must be sorted and unique")
        if set(self.occurrence_counts) != set(self.items):
            raise ValueError("AssumptionSet occurrence_counts must match items")
        invalid_counts = [
            assumption
            for assumption, count in self.occurrence_counts.items()
            if count <= 0
        ]
        if invalid_counts:
            raise ValueError("AssumptionSet occurrence counts must be positive")
        return self

    @property
    def total_count(self) -> int:
        return sum(self.occurrence_counts.values())

    @property
    def risky_items(self) -> tuple[str, ...]:
        return tuple(item for item in self.items if item in RISKY_ASSUMPTIONS)

    @property
    def risky_occurrence_count(self) -> int:
        return sum(self.occurrence_counts[item] for item in self.risky_items)

    @property
    def risk_score(self) -> float:
        return min(1.0, self.risky_occurrence_count * 0.25)

    @property
    def bucket(self) -> str:
        if self.total_count >= 4:
            return "many"
        if self.total_count:
            return "some"
        return "none"

    @property
    def fingerprint(self) -> str:
        return stable_sha256(
            {
                "items": self.items,
                "occurrence_counts": self.occurrence_counts,
            }
        )
