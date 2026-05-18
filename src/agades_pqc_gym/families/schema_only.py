from __future__ import annotations

from dataclasses import dataclass

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.family_adapter import ReproductionResult, ValidationFinding
from agades_pqc_gym.core.operators import PLACEHOLDER_OPERATORS
from agades_pqc_gym.core.target import TargetFamily, TargetSpec
from agades_pqc_gym.evaluators.base import EstimatorResult

SCHEMA_ONLY_ASSUMPTION = "schema_only_no_estimator"


@dataclass(frozen=True)
class SchemaOnlyFamilyAdapter:
    family: TargetFamily
    estimator_name: str
    support_level: str = "schema_only"

    def validate_target(self, target: TargetSpec) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        if target.family is not self.family:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="family_adapter_mismatch",
                    message=(
                        f"{self.family.value} adapter cannot validate "
                        f"{target.family.value} targets"
                    ),
                )
            )
        if target.support_level.value != self.support_level:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="schema_only_support_level_required",
                    message=(
                        f"{self.family.value} targets must remain schema_only "
                        "until a reviewed family evaluator is implemented"
                    ),
                )
            )
        return findings

    def validate_plan(self, plan: AttackPlan) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        for operator in plan.operators:
            if SCHEMA_ONLY_ASSUMPTION not in operator.assumptions:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="schema_only_assumption_required",
                        message=(
                            f"{self.family.value} schema-only operator "
                            f"{operator.type} must include "
                            f"{SCHEMA_ONLY_ASSUMPTION}"
                        ),
                    )
                )
        if plan.constraints.require_reproducibility_on_downscaled_instances:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="schema_only_reproduction_not_available",
                    message=(
                        f"{self.family.value} schema-only plans cannot require "
                        "downscaled reproduction before a reviewed harness exists"
                    ),
                )
            )
        if any(
            claim is not None
            for claim in (
                plan.claims.estimated_time_bits,
                plan.claims.estimated_memory_bits,
                plan.claims.success_probability,
            )
        ):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="schema_only_claims_not_allowed",
                    message=(
                        f"{self.family.value} schema-only plans must not include "
                        "cryptanalytic estimate claims"
                    ),
                )
            )
        return findings

    def supported_operators(self) -> set[str]:
        return set(PLACEHOLDER_OPERATORS[self.family])

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version="0.1.0",
            estimator_commit=None,
            evaluation_status="unsupported",
            attack_type=plan.operators[-1].type,
            time_bits=None,
            memory_bits=None,
            warnings=[
                f"{self.family.value} evaluator is not implemented; schema-only "
                "target validated without a cryptanalytic estimate."
            ],
        )

    def reproduce_downscaled(self, plan: AttackPlan) -> ReproductionResult | None:
        del plan
        return None
