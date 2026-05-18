from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.core.family_adapter import ReproductionResult, ValidationFinding
from agades_pqc_gym.core.operators import PLACEHOLDER_OPERATORS
from agades_pqc_gym.core.target import SupportLevel, TargetFamily, TargetSpec
from agades_pqc_gym.evaluators.base import EstimatorResult
from agades_pqc_gym.families.fixtures import (
    is_scoped_public_fixture_path,
    resolve_public_fixture_path,
)
from agades_pqc_gym.families.isogeny_historical.path_estimator import (
    HISTORICAL_NOT_CURRENT_ASSUMPTION,
    TOY_ISOGENY_ASSUMPTIONS_BY_CASE,
    TOY_ISOGENY_CASES,
    TOY_ISOGENY_MAX_BRANCHING_FACTOR,
    TOY_ISOGENY_MAX_VOLCANO_HEIGHT,
    TOY_ISOGENY_MAX_WALK_LENGTH,
    TOY_ISOGENY_VOLCANO_WALK_CASE,
    ToyIsogenyHistoricalPathEstimator,
)
from agades_pqc_gym.families.isogeny_historical.path_fixture import (
    verify_toy_isogeny_path_fixture,
)
from agades_pqc_gym.families.schema_only import (
    SCHEMA_ONLY_ASSUMPTION,
    SchemaOnlyFamilyAdapter,
)

_MAX_TOY_ISOGENY_N = 128
ISOGENY_HISTORICAL_INSTANCE_REPRODUCTION_SCORE = 0.4
ROOT = Path(__file__).resolve().parents[4]
PACKAGE_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_FIXTURE_ROOT_PARTS = (
    "benchmarks",
    "isogeny_historical_toy_path",
    "fixtures",
)


@dataclass(frozen=True)
class IsogenyHistoricalFamilyAdapter:
    family: TargetFamily = TargetFamily.ISOGENY_HISTORICAL
    support_level: str = "toy_evaluator"
    estimator_name: str = ToyIsogenyHistoricalPathEstimator.estimator_name

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_schema_only",
            SchemaOnlyFamilyAdapter(
                family=TargetFamily.ISOGENY_HISTORICAL,
                estimator_name="isogeny-historical-placeholder-estimator",
            ),
        )
        object.__setattr__(self, "_estimator", ToyIsogenyHistoricalPathEstimator())

    def validate_target(self, target: TargetSpec) -> list[ValidationFinding]:
        findings = _validate_isogeny_historical_shape(target)
        if target.family is not TargetFamily.ISOGENY_HISTORICAL:
            return findings
        if target.support_level is SupportLevel.SCHEMA_ONLY:
            return [*findings, *self._schema_only.validate_target(target)]
        if target.support_level is not SupportLevel.IMPLEMENTED:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="isogeny_historical_support_level_unknown",
                    message=(
                        "ISOGENY_HISTORICAL targets must be schema_only or "
                        "implemented for the reviewed historical toy path "
                        "evaluator"
                    ),
                )
            )
            return findings

        if not target.name.startswith("toy_"):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="isogeny_historical_toy_target_required",
                    message=(
                        "ISOGENY_HISTORICAL implemented evaluator is limited "
                        "to toy_ historical targets"
                    ),
                )
            )
        if target.n is not None and target.n > _MAX_TOY_ISOGENY_N:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="isogeny_historical_toy_n_limit",
                    message=(
                        "ISOGENY_HISTORICAL implemented toy evaluator "
                        f"requires n <= {_MAX_TOY_ISOGENY_N}"
                    ),
                )
            )
        if target.claimed_security_bits is not None:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="isogeny_historical_claimed_security_not_allowed",
                    message=(
                        "ISOGENY_HISTORICAL toy targets must not include "
                        "claimed_security_bits"
                    ),
                )
            )
        return findings

    def validate_plan(self, plan: AttackPlan) -> list[ValidationFinding]:
        if plan.target.support_level is SupportLevel.SCHEMA_ONLY:
            return self._validate_schema_only_plan(plan)

        findings: list[ValidationFinding] = []
        for operator in plan.operators:
            case = operator.params.get("case")
            if (
                operator.type != "historical_isogeny_reconstruction"
                or case not in TOY_ISOGENY_CASES
            ):
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="isogeny_historical_unreviewed_case",
                        message=(
                            "ISOGENY_HISTORICAL implemented evaluator "
                            "supports only historical_isogeny_reconstruction "
                            "with reviewed toy cases: "
                            f"{', '.join(sorted(TOY_ISOGENY_CASES))}"
                        ),
                    )
                )
            if SCHEMA_ONLY_ASSUMPTION in operator.assumptions:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code=(
                            "isogeny_historical_schema_only_assumption_on_"
                            "implemented_plan"
                        ),
                        message=(
                            "ISOGENY_HISTORICAL implemented toy plans must "
                            f"not use {SCHEMA_ONLY_ASSUMPTION}"
                        ),
                    )
                )
            if HISTORICAL_NOT_CURRENT_ASSUMPTION not in operator.assumptions:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="isogeny_historical_boundary_required",
                        message=(
                            "ISOGENY_HISTORICAL plans require "
                            f"{HISTORICAL_NOT_CURRENT_ASSUMPTION}"
                        ),
                    )
                )
            required_case_assumption = (
                TOY_ISOGENY_ASSUMPTIONS_BY_CASE.get(case)
                if isinstance(case, str)
                else None
            )
            if (
                required_case_assumption is not None
                and required_case_assumption not in operator.assumptions
            ):
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="isogeny_historical_toy_path_assumption_required",
                        message=(
                            "ISOGENY_HISTORICAL toy path plans for "
                            f"{case} must include {required_case_assumption}"
                        ),
                    )
                )
            findings.extend(_validate_toy_path_params(operator.params))

        if (
            plan.constraints.require_reproducibility_on_downscaled_instances
            and plan.constraints.downscaled_reproduction_fixture is None
        ):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="isogeny_historical_reproduction_fixture_required",
                    message=(
                        "ISOGENY_HISTORICAL toy path reproduction requires an "
                        "explicit public historical path fixture"
                    ),
                )
            )
        if plan.constraints.downscaled_reproduction_fixture is not None:
            fixture_path = Path(plan.constraints.downscaled_reproduction_fixture)
            if not _is_scoped_path_fixture_path(fixture_path):
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="isogeny_historical_reproduction_fixture_scope",
                        message=(
                            "ISOGENY_HISTORICAL reproduction fixtures must be "
                            "relative paths under "
                            "benchmarks/isogeny_historical_toy_path/fixtures/"
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
                    code="isogeny_historical_pre_evaluation_claims_not_allowed",
                    message=(
                        "ISOGENY_HISTORICAL toy plans must not include "
                        "cryptanalytic estimate claims"
                    ),
                )
            )
        return findings

    def supported_operators(self) -> set[str]:
        return set(PLACEHOLDER_OPERATORS[TargetFamily.ISOGENY_HISTORICAL])

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        if plan.target.support_level is SupportLevel.SCHEMA_ONLY:
            return self._schema_only.estimate(plan)
        return self._estimator.estimate(plan)

    def reproduce_downscaled(self, plan: AttackPlan) -> ReproductionResult | None:
        if not plan.constraints.require_reproducibility_on_downscaled_instances:
            return None

        fixture_path_value = plan.constraints.downscaled_reproduction_fixture
        if not fixture_path_value:
            return ReproductionResult(
                attempted=False,
                status="not_applicable",
                success=False,
                warnings=[
                    "ISOGENY_HISTORICAL toy path reproduction requires an "
                    "explicit public historical path fixture."
                ],
            )

        fixture_path, fixture_warnings = _resolve_path_fixture_path(
            fixture_path_value
        )
        if fixture_path is None:
            return ReproductionResult(
                attempted=False,
                status="not_applicable",
                success=False,
                warnings=fixture_warnings,
            )
        try:
            result = verify_toy_isogeny_path_fixture(fixture_path)
        except (OSError, ValueError) as exc:
            return ReproductionResult(
                attempted=True,
                status="failed",
                success=False,
                warnings=[
                    "ISOGENY_HISTORICAL toy path fixture could not be "
                    f"verified: {exc}"
                ],
            )

        operator = _historical_path_operator(plan)
        if (
            result.verified
            and result.target_name == plan.target.name
            and result.n == plan.target.n
            and result.case == operator.params.get("case")
            and result.walk_length == operator.params.get("walk_length")
            and result.branching_factor == operator.params.get("branching_factor")
            and _result_matches_case_params(result, operator)
            and result.historical_not_current
            and not result.current_standard_claim
            and result.public
            and not result.security_claim
        ):
            return ReproductionResult(
                attempted=True,
                status="instance_solved",
                success=True,
                score=ISOGENY_HISTORICAL_INSTANCE_REPRODUCTION_SCORE,
                warnings=[
                    "Verified a public historical toy isogeny path fixture; "
                    "this is reproducibility plumbing, not a current-standard "
                    "or security claim."
                ],
            )
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                "ISOGENY_HISTORICAL toy path fixture did not match the "
                "expected public historical no-claim plan."
            ],
        )

    def _validate_schema_only_plan(
        self,
        plan: AttackPlan,
    ) -> list[ValidationFinding]:
        findings = self._schema_only.validate_plan(plan)
        if not any(
            HISTORICAL_NOT_CURRENT_ASSUMPTION in operator.assumptions
            for operator in plan.operators
        ):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="isogeny_historical_boundary_required",
                    message=(
                        "ISOGENY_HISTORICAL plans require "
                        f"{HISTORICAL_NOT_CURRENT_ASSUMPTION}"
                    ),
                )
            )
        return findings


def _validate_isogeny_historical_shape(
    target: TargetSpec,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if target.family is not TargetFamily.ISOGENY_HISTORICAL:
        findings.append(
            ValidationFinding(
                severity="error",
                code="family_adapter_mismatch",
                message=(
                    "ISOGENY_HISTORICAL adapter cannot validate "
                    f"{target.family.value} targets"
                ),
            )
        )
    return findings


def _validate_toy_path_params(params: dict[str, object]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    case = params.get("case")
    walk_length = params.get("walk_length")
    branching_factor = params.get("branching_factor")
    volcano_height = params.get("volcano_height")

    if not isinstance(walk_length, int):
        findings.append(
            ValidationFinding(
                severity="error",
                code="isogeny_historical_walk_length_required",
                message="ISOGENY_HISTORICAL toy path requires walk_length",
            )
        )
    elif not 1 <= walk_length <= TOY_ISOGENY_MAX_WALK_LENGTH:
        findings.append(
            ValidationFinding(
                severity="error",
                code="isogeny_historical_walk_length_limit",
                message=(
                    "ISOGENY_HISTORICAL toy path requires "
                    f"1 <= walk_length <= {TOY_ISOGENY_MAX_WALK_LENGTH}"
                ),
            )
        )

    if not isinstance(branching_factor, int):
        findings.append(
            ValidationFinding(
                severity="error",
                code="isogeny_historical_branching_factor_required",
                message="ISOGENY_HISTORICAL toy path requires branching_factor",
            )
        )
    elif not 2 <= branching_factor <= TOY_ISOGENY_MAX_BRANCHING_FACTOR:
        findings.append(
            ValidationFinding(
                severity="error",
                code="isogeny_historical_branching_factor_limit",
                message=(
                    "ISOGENY_HISTORICAL toy path requires "
                    f"2 <= branching_factor <= {TOY_ISOGENY_MAX_BRANCHING_FACTOR}"
                ),
            )
        )
    if case == TOY_ISOGENY_VOLCANO_WALK_CASE:
        if not isinstance(volcano_height, int) or isinstance(volcano_height, bool):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="isogeny_historical_volcano_height_required",
                    message=(
                        "ISOGENY_HISTORICAL toy volcano walk requires "
                        "volcano_height"
                    ),
                )
            )
        elif not 1 <= volcano_height <= TOY_ISOGENY_MAX_VOLCANO_HEIGHT:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="isogeny_historical_volcano_height_limit",
                    message=(
                        "ISOGENY_HISTORICAL toy volcano walk requires "
                        "1 <= volcano_height <= "
                        f"{TOY_ISOGENY_MAX_VOLCANO_HEIGHT}"
                    ),
                )
            )
    return findings


def _historical_path_operator(plan: AttackPlan) -> AttackOperator:
    for operator in plan.operators:
        if operator.type == "historical_isogeny_reconstruction":
            return operator
    raise ValueError(
        "ISOGENY_HISTORICAL reproduction requires "
        "historical_isogeny_reconstruction"
    )


def _result_matches_case_params(result: object, operator: AttackOperator) -> bool:
    if operator.params.get("case") != TOY_ISOGENY_VOLCANO_WALK_CASE:
        return True
    return getattr(result, "volcano_height", None) == operator.params.get(
        "volcano_height"
    )


def _resolve_path_fixture_path(value: str) -> tuple[Path | None, list[str]]:
    return resolve_public_fixture_path(
        value,
        repo_root=ROOT,
        package_fixture_dir=PACKAGE_FIXTURES,
        root_parts=_FIXTURE_ROOT_PARTS,
        family_label="ISOGENY_HISTORICAL",
    )


def _is_scoped_path_fixture_path(path: Path) -> bool:
    return is_scoped_public_fixture_path(path, _FIXTURE_ROOT_PARTS)
