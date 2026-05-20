from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.family_adapter import ReproductionResult, ValidationFinding
from agades_pqc_gym.core.operators import LATTICE_OPERATORS
from agades_pqc_gym.core.target import TargetFamily, TargetSpec
from agades_pqc_gym.evaluators.base import EstimatorAdapter, EstimatorResult
from agades_pqc_gym.evaluators.mock_estimator import MockEstimatorAdapter
from agades_pqc_gym.families.fixtures import resolve_public_fixture_path
from agades_pqc_gym.families.lattice.downscaled_solver import (
    solve_downscaled_lwe_fixture,
    solve_downscaled_mlwe_fixture,
)
from agades_pqc_gym.families.lattice.validators import (
    validate_lattice_plan,
    validate_lattice_target,
)
from agades_pqc_gym.validators.consistency import primary_attack_type

DOWNSCALED_REPRODUCTION_SCORE = 0.2
DOWNSCALED_INSTANCE_REPRODUCTION_SCORE = 0.4
MAX_DOWNSCALED_LATTICE_DIMENSION = 1024
ROOT = Path(__file__).resolve().parents[4]
PACKAGE_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_DOWNSCALED_LWE_FIXTURE_ROOT_PARTS = (
    "benchmarks",
    "lattice_downscaled_lwe_instances",
)
_DOWNSCALED_MLWE_FIXTURE_ROOT_PARTS = (
    "benchmarks",
    "lattice_downscaled_mlwe_instances",
)
CATALOGED_PRIMARY_OPERATORS_BY_FAMILY = {
    TargetFamily.LWE: frozenset(
        {
            "bounded_distance_decoding",
            "bkw",
            "dual_attack",
            "dual_hybrid",
            "primal_usvp",
        }
    ),
    TargetFamily.MLWE: frozenset(
        {
            "bkz_parameter_sweep",
            "module_lattice_reduction_hypothesis",
        }
    ),
}


@dataclass
class LatticeFamilyAdapter:
    family: TargetFamily = TargetFamily.LWE
    estimator: EstimatorAdapter | None = None
    support_level: str = "implemented"

    def validate_target(self, target: TargetSpec) -> list[ValidationFinding]:
        return validate_lattice_target(target)

    def validate_plan(self, plan: AttackPlan) -> list[ValidationFinding]:
        return validate_lattice_plan(plan)

    def supported_operators(self) -> set[str]:
        if self.support_level != "implemented":
            return set()
        return set(LATTICE_OPERATORS)

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        findings = self.validate_plan(plan)
        errors = [finding for finding in findings if finding.severity == "error"]
        if errors:
            return EstimatorResult(
                estimator_name="lattice-family-router",
                estimator_version="0.1.0",
                estimator_commit=None,
                evaluation_status="unsupported",
                attack_type=plan.operators[-1].type,
                time_bits=None,
                memory_bits=None,
                warnings=[finding.message for finding in findings],
            )
        if self.support_level != "implemented":
            return EstimatorResult(
                estimator_name="lattice-family-router",
                estimator_version="0.1.0",
                estimator_commit=None,
                evaluation_status="unsupported",
                attack_type=plan.operators[-1].type,
                time_bits=None,
                memory_bits=None,
                warnings=[finding.message for finding in findings],
            )
        primary_operator = primary_attack_type(plan)
        if not _is_cataloged_primary_operator(plan.target.family, primary_operator):
            return EstimatorResult(
                estimator_name="lattice-family-router",
                estimator_version="0.1.0",
                estimator_commit=None,
                evaluation_status="unsupported",
                attack_type=primary_operator,
                time_bits=None,
                memory_bits=None,
                warnings=[
                    (
                        f"{primary_operator} is a lattice runtime operator but is "
                        "not a cataloged primary LWE/MLWE estimator route."
                    )
                ],
            )
        estimator = self.estimator or MockEstimatorAdapter()
        return estimator.estimate(plan)

    def reproduce_downscaled(self, plan: AttackPlan) -> ReproductionResult | None:
        if not plan.constraints.require_reproducibility_on_downscaled_instances:
            return ReproductionResult(attempted=False, status="not_requested")

        if not _is_public_downscaled_lattice_target(plan):
            return ReproductionResult(
                attempted=False,
                status="not_applicable",
                warnings=[
                    "Downscaled reproduction is only enabled for public toy or "
                    "downscaled LWE/MLWE targets in the MVP."
                ],
            )

        fixture_path_value = plan.constraints.downscaled_reproduction_fixture
        if fixture_path_value:
            fixture_path, fixture_warnings = _resolve_downscaled_fixture_path(
                fixture_path_value,
                plan.target.family,
            )
            if fixture_path is None:
                return ReproductionResult(
                    attempted=False,
                    status="not_applicable",
                    success=False,
                    warnings=fixture_warnings,
                )
            return _reproduce_declared_lattice_fixture(
                plan,
                fixture_path,
            )

        estimator = self.estimator or MockEstimatorAdapter()
        first = estimator.estimate(plan)
        second = estimator.estimate(plan)
        constraints_ok = (
            first.evaluation_status == "ok"
            and first.time_bits is not None
            and first.memory_bits is not None
            and _within_limit(first.time_bits, plan.constraints.max_time_bits)
            and _within_limit(first.memory_bits, plan.constraints.max_memory_bits)
        )
        deterministic = first.model_dump(mode="json") == second.model_dump(mode="json")
        if constraints_ok and deterministic:
            return ReproductionResult(
                attempted=True,
                status="estimator_reproduced",
                success=True,
                score=DOWNSCALED_REPRODUCTION_SCORE,
                warnings=[
                    "Deterministic downscaled evaluator reproduction smoke passed; "
                    "this is not cryptanalytic evidence and does not solve an "
                    "LWE instance."
                ],
            )
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "Downscaled evaluator reproduction smoke failed or exceeded "
                "declared resource constraints."
            ],
        )


def _is_public_downscaled_lattice_target(plan: AttackPlan) -> bool:
    if not plan.metadata.public:
        return False
    if plan.target.family not in {TargetFamily.LWE, TargetFamily.MLWE}:
        return False
    target_name = plan.target.name.lower()
    if "toy" not in target_name and "downscaled" not in target_name:
        return False
    dimension = (plan.target.n or 0) * (plan.target.k or 1)
    return dimension <= MAX_DOWNSCALED_LATTICE_DIMENSION


def _within_limit(value: float, limit: float | None) -> bool:
    return limit is None or value <= limit


def _is_cataloged_primary_operator(family: TargetFamily, operator_type: str) -> bool:
    return operator_type in CATALOGED_PRIMARY_OPERATORS_BY_FAMILY.get(
        family,
        frozenset(),
    )


def _reproduce_declared_lattice_fixture(
    plan: AttackPlan,
    fixture_path: Path,
) -> ReproductionResult:
    if plan.target.family is TargetFamily.MLWE:
        try:
            solution = solve_downscaled_mlwe_fixture(fixture_path)
        except (OSError, ValueError) as exc:
            return ReproductionResult(
                attempted=True,
                status="failed",
                success=False,
                warnings=[f"Downscaled MLWE fixture could not be solved: {exc}"],
            )
        if (
            solution.solved
            and solution.target_name == plan.target.name
            and solution.n == plan.target.n
            and solution.k == plan.target.k
            and solution.q == plan.target.q
            and solution.public
            and not solution.security_claim
        ):
            return ReproductionResult(
                attempted=True,
                status="instance_solved",
                success=True,
                score=DOWNSCALED_INSTANCE_REPRODUCTION_SCORE,
                warnings=[
                    "Solved a public downscaled MLWE fixture with bounded "
                    "exhaustive search over a tiny linearized module instance; "
                    "this is reproducibility plumbing, not a security claim."
                ],
            )
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "Downscaled MLWE fixture did not produce the expected public "
                "target solution."
            ],
        )

    try:
        solution = solve_downscaled_lwe_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[f"Downscaled LWE fixture could not be solved: {exc}"],
        )
    if (
        solution.solved
        and solution.target_name == plan.target.name
        and solution.n == plan.target.n
        and solution.q == plan.target.q
        and solution.public
        and not solution.security_claim
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=DOWNSCALED_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Solved a public downscaled LWE fixture with bounded "
                "exhaustive search; this is reproducibility plumbing, "
                "not a security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "Downscaled LWE fixture did not produce the expected public "
            "target solution."
        ],
    )


def _resolve_downscaled_fixture_path(
    value: str,
    family: TargetFamily,
) -> tuple[Path | None, list[str]]:
    root_parts = (
        _DOWNSCALED_MLWE_FIXTURE_ROOT_PARTS
        if family is TargetFamily.MLWE
        else _DOWNSCALED_LWE_FIXTURE_ROOT_PARTS
    )
    return resolve_public_fixture_path(
        value,
        repo_root=ROOT,
        package_fixture_dir=PACKAGE_FIXTURES,
        root_parts=root_parts,
        family_label="LATTICE",
    )
