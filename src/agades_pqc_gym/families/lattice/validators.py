from __future__ import annotations

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.family_adapter import ValidationFinding
from agades_pqc_gym.core.target import TargetFamily, TargetSpec


def validate_lattice_target(target: TargetSpec) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if target.family in {TargetFamily.LWE, TargetFamily.MLWE}:
        return findings
    if target.family in {TargetFamily.NTRU, TargetFamily.SIS}:
        findings.append(
            ValidationFinding(
                severity="warning",
                code="lattice_schema_only",
                message=(
                    f"{target.family.value} is represented structurally, but no "
                    "reviewed estimator mapping is implemented in the MVP."
                ),
            )
        )
    return findings


def validate_lattice_plan(plan: AttackPlan) -> list[ValidationFinding]:
    findings = validate_lattice_target(plan.target)
    if plan.target.family in {TargetFamily.NTRU, TargetFamily.SIS}:
        findings.append(
            ValidationFinding(
                severity="warning",
                code="unsupported_lattice_family",
                message=(
                    f"{plan.target.family.value} lattice evaluation is unsupported "
                    "until mappings are reviewed."
                ),
            )
        )
    return findings
