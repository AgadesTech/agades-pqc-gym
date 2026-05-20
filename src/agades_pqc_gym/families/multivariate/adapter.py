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
from agades_pqc_gym.families.multivariate.minrank_solver import (
    solve_toy_minrank_fixture,
)
from agades_pqc_gym.families.multivariate.mq_estimator import (
    TOY_MINRANK_ASSUMPTION,
    TOY_MINRANK_MODEL,
    TOY_MQ_ASSUMPTION,
    TOY_MQ_DEGREE_BOUND_ASSUMPTION,
    TOY_MQ_DEGREE_BOUND_MODEL,
    TOY_MQ_HYBRID_ASSUMPTION,
    TOY_MQ_HYBRID_MODEL,
    TOY_MQ_MODEL,
    TOY_UOV_PUBLIC_MAP_ASSUMPTION,
    TOY_UOV_PUBLIC_MAP_MODEL,
    ToyMultivariateMQEstimator,
    field_order_from_notation,
)
from agades_pqc_gym.families.multivariate.mq_solver import (
    solve_toy_mq_fixture,
    solve_toy_mq_hybrid_fixture,
)
from agades_pqc_gym.families.multivariate.uov_fixture import (
    verify_toy_uov_public_map_fixture,
)
from agades_pqc_gym.families.schema_only import (
    SCHEMA_ONLY_ASSUMPTION,
    SchemaOnlyFamilyAdapter,
)

_MAX_TOY_VARIABLES = 16
_MAX_TOY_EQUATIONS = 16
_MAX_TOY_FIELD_ORDER = 256
MULTIVARIATE_INSTANCE_REPRODUCTION_SCORE = 0.4
ROOT = Path(__file__).resolve().parents[4]
PACKAGE_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_MQ_FIXTURE_ROOT_PARTS = ("benchmarks", "multivariate_toy_mq", "fixtures")
_MINRANK_FIXTURE_ROOT_PARTS = (
    "benchmarks",
    "multivariate_toy_minrank",
    "fixtures",
)
_UOV_FIXTURE_ROOT_PARTS = (
    "benchmarks",
    "multivariate_toy_uov",
    "fixtures",
)


@dataclass(frozen=True)
class MultivariateFamilyAdapter:
    family: TargetFamily = TargetFamily.MULTIVARIATE
    support_level: str = "toy_evaluator"
    estimator_name: str = ToyMultivariateMQEstimator.estimator_name

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_schema_only",
            SchemaOnlyFamilyAdapter(
                family=TargetFamily.MULTIVARIATE,
                estimator_name="multivariate-placeholder-estimator",
            ),
        )
        object.__setattr__(self, "_estimator", ToyMultivariateMQEstimator())

    def validate_target(self, target: TargetSpec) -> list[ValidationFinding]:
        findings = _validate_multivariate_shape(target)
        if target.family is not TargetFamily.MULTIVARIATE:
            return findings
        if target.support_level is SupportLevel.SCHEMA_ONLY:
            return [*findings, *self._schema_only.validate_target(target)]
        if target.support_level is not SupportLevel.IMPLEMENTED:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="multivariate_support_level_unknown",
                    message=(
                        "MULTIVARIATE targets must be schema_only or implemented "
                        "for the reviewed toy multivariate evaluator"
                    ),
                )
            )
            return findings

        if not target.name.startswith("toy_"):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="multivariate_toy_target_required",
                    message=(
                        "MULTIVARIATE implemented evaluator is limited to toy_ "
                        "multivariate targets"
                    ),
                )
            )
        if target.variables is not None and target.variables > _MAX_TOY_VARIABLES:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="multivariate_toy_variable_limit",
                    message=(
                        "MULTIVARIATE implemented toy evaluator requires "
                        f"variables <= {_MAX_TOY_VARIABLES}"
                    ),
                )
            )
        if target.equations is not None and target.equations > _MAX_TOY_EQUATIONS:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="multivariate_toy_equation_limit",
                    message=(
                        "MULTIVARIATE implemented toy evaluator requires "
                        f"equations <= {_MAX_TOY_EQUATIONS}"
                    ),
                )
            )
        if target.field is not None and _is_finite_field_notation(target.field):
            field_order = field_order_from_notation(target.field)
            if field_order > _MAX_TOY_FIELD_ORDER:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="multivariate_toy_field_limit",
                        message=(
                            "MULTIVARIATE implemented toy evaluator requires "
                            f"field order <= {_MAX_TOY_FIELD_ORDER}"
                        ),
                    )
                )
        return findings

    def validate_plan(self, plan: AttackPlan) -> list[ValidationFinding]:
        if plan.target.support_level is SupportLevel.SCHEMA_ONLY:
            return self._schema_only.validate_plan(plan)

        findings: list[ValidationFinding] = []
        for operator in plan.operators:
            if SCHEMA_ONLY_ASSUMPTION in operator.assumptions:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="multivariate_schema_only_assumption_on_implemented_plan",
                        message=(
                            "MULTIVARIATE implemented toy plans must not use "
                            f"{SCHEMA_ONLY_ASSUMPTION}"
                        ),
                    )
                )
            if operator.type == "groebner_basis":
                findings.extend(_validate_mq_operator(plan, operator))
            elif operator.type == "minrank_attack":
                findings.extend(_validate_minrank_operator(operator))
            elif operator.type == "signature_fixture_check":
                findings.extend(_validate_uov_public_map_operator(plan, operator))
            else:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="multivariate_unreviewed_operator",
                        message=(
                            "MULTIVARIATE implemented evaluator supports only "
                            f"groebner_basis model={TOY_MQ_MODEL}, "
                            f"groebner_basis model={TOY_MQ_HYBRID_MODEL}, or "
                            f"groebner_basis model={TOY_MQ_DEGREE_BOUND_MODEL}, or "
                            f"minrank_attack model={TOY_MINRANK_MODEL}, or "
                            "signature_fixture_check "
                            f"signature_model={TOY_UOV_PUBLIC_MAP_MODEL}"
                        ),
                    )
                )
        if (
            plan.constraints.require_reproducibility_on_downscaled_instances
            and plan.constraints.downscaled_reproduction_fixture is None
        ):
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="multivariate_reproduction_fixture_required",
                    message=(
                        "MULTIVARIATE toy reproduction requires an explicit "
                        "public binary fixture"
                    ),
                )
            )
        if plan.constraints.downscaled_reproduction_fixture is not None:
            fixture_path = Path(plan.constraints.downscaled_reproduction_fixture)
            fixture_root_parts = _fixture_root_parts_for_plan(plan)
            if not _is_scoped_fixture_path(fixture_path, fixture_root_parts):
                findings.append(
                    ValidationFinding(
                        severity="error",
                        code="multivariate_reproduction_fixture_scope",
                        message=(
                            "MULTIVARIATE reproduction fixtures must be relative "
                            f"paths under {_fixture_root_label(fixture_root_parts)}"
                        ),
                    ),
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
                    code="multivariate_pre_evaluation_claims_not_allowed",
                    message=(
                        "MULTIVARIATE toy plans must not include cryptanalytic "
                        "estimate claims"
                    ),
                )
            )
        return findings

    def supported_operators(self) -> set[str]:
        return set(PLACEHOLDER_OPERATORS[TargetFamily.MULTIVARIATE])

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
                    "MULTIVARIATE toy reproduction requires an explicit "
                    "public binary fixture."
                ],
            )

        fixture_root_parts = _fixture_root_parts_for_plan(plan)
        fixture_path, fixture_warnings = _resolve_fixture_path(
            fixture_path_value,
            fixture_root_parts,
        )
        if fixture_path is None:
            return ReproductionResult(
                attempted=False,
                status="not_applicable",
                success=False,
                warnings=fixture_warnings,
            )

        if _is_uov_public_map_plan(plan):
            return _reproduce_uov_public_map_fixture(plan, fixture_path)
        if _is_minrank_plan(plan):
            return _reproduce_minrank_fixture(plan, fixture_path)
        return _reproduce_mq_fixture(plan, fixture_path)


def _validate_mq_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    model = operator.params.get("model")
    if model == TOY_MQ_MODEL:
        if TOY_MQ_ASSUMPTION not in operator.assumptions:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="multivariate_toy_mq_assumption_required",
                    message=(
                        "MULTIVARIATE toy_mq_search plans must include "
                        f"{TOY_MQ_ASSUMPTION}"
                    ),
                )
            )
        return findings

    if model == TOY_MQ_HYBRID_MODEL:
        if TOY_MQ_HYBRID_ASSUMPTION not in operator.assumptions:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="multivariate_toy_mq_hybrid_assumption_required",
                    message=(
                        "MULTIVARIATE toy_mq_hybrid_search plans must include "
                        f"{TOY_MQ_HYBRID_ASSUMPTION}"
                    ),
                )
            )
        findings.extend(_validate_mq_hybrid_operator(plan, operator))
        return findings

    if model == TOY_MQ_DEGREE_BOUND_MODEL:
        if TOY_MQ_DEGREE_BOUND_ASSUMPTION not in operator.assumptions:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="multivariate_toy_mq_degree_bound_assumption_required",
                    message=(
                        "MULTIVARIATE toy_mq_degree_bound plans must include "
                        f"{TOY_MQ_DEGREE_BOUND_ASSUMPTION}"
                    ),
                )
            )
        findings.extend(_validate_mq_degree_bound_operator(plan, operator))
        return findings

    if model not in {TOY_MQ_MODEL, TOY_MQ_HYBRID_MODEL, TOY_MQ_DEGREE_BOUND_MODEL}:
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_unreviewed_mq_model",
                message=(
                    "MULTIVARIATE implemented evaluator supports only "
                    f"groebner_basis with model={TOY_MQ_MODEL} or "
                    f"model={TOY_MQ_HYBRID_MODEL} or "
                    f"model={TOY_MQ_DEGREE_BOUND_MODEL}"
                ),
            )
        )
    return findings


def _validate_mq_hybrid_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    guessed_variables = operator.params.get("guessed_variables")
    variables = plan.target.variables
    if not isinstance(guessed_variables, int) or isinstance(guessed_variables, bool):
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_toy_mq_hybrid_guessed_variables",
                message=(
                    "toy_mq_hybrid_search requires positive integer "
                    "guessed_variables"
                ),
            )
        )
        return findings
    if guessed_variables < 1 or (
        variables is not None and guessed_variables >= variables
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_toy_mq_hybrid_partial_guess",
                message=(
                    "toy_mq_hybrid_search requires 1 <= guessed_variables "
                    "< variables"
                ),
            )
        )
    return findings


def _validate_mq_degree_bound_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    degree_bound = operator.params.get("degree_bound")
    variables = plan.target.variables
    if not isinstance(degree_bound, int) or isinstance(degree_bound, bool):
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_toy_mq_degree_bound_degree",
                message="toy_mq_degree_bound requires integer degree_bound",
            )
        )
        return findings
    if degree_bound < 2 or (variables is not None and degree_bound > variables):
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_toy_mq_degree_bound_range",
                message=(
                    "toy_mq_degree_bound requires 2 <= degree_bound <= variables"
                ),
            )
        )
    linear_algebra_omega = operator.params.get("linear_algebra_omega")
    if isinstance(linear_algebra_omega, bool) or not isinstance(
        linear_algebra_omega,
        int | float,
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_toy_mq_degree_bound_omega",
                message=(
                    "toy_mq_degree_bound requires numeric linear_algebra_omega"
                ),
            )
        )
    elif linear_algebra_omega < 2.0 or linear_algebra_omega > 3.0:
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_toy_mq_degree_bound_omega_range",
                message=(
                    "toy_mq_degree_bound requires "
                    "2.0 <= linear_algebra_omega <= 3.0"
                ),
            )
        )
    return findings


def _validate_minrank_operator(operator: AttackOperator) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    model = operator.params.get("model")
    if model != TOY_MINRANK_MODEL:
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_unreviewed_minrank_model",
                message=(
                    "MULTIVARIATE implemented evaluator supports only "
                    f"minrank_attack with model={TOY_MINRANK_MODEL}"
                ),
            )
        )
    if TOY_MINRANK_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_toy_minrank_assumption_required",
                message=(
                    "MULTIVARIATE toy_minrank_search plans must include "
                    f"{TOY_MINRANK_ASSUMPTION}"
                ),
            )
        )
    rows = _positive_int_param(operator, "matrix_rows", findings)
    cols = _positive_int_param(operator, "matrix_cols", findings)
    target_rank = _non_negative_int_param(operator, "target_rank", findings)
    if (
        rows is not None
        and cols is not None
        and target_rank is not None
        and target_rank >= min(rows, cols)
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_toy_minrank_target_rank",
                message=(
                    "toy_minrank_search requires target_rank smaller than "
                    "matrix_rows and matrix_cols"
                ),
            )
        )
    return findings


def _validate_uov_public_map_operator(
    plan: AttackPlan,
    operator: AttackOperator,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    model = operator.params.get("signature_model")
    if model != TOY_UOV_PUBLIC_MAP_MODEL:
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_unreviewed_signature_model",
                message=(
                    "MULTIVARIATE implemented evaluator supports only "
                    "signature_fixture_check with "
                    f"signature_model={TOY_UOV_PUBLIC_MAP_MODEL}"
                ),
            )
        )
    if TOY_UOV_PUBLIC_MAP_ASSUMPTION not in operator.assumptions:
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_toy_uov_public_map_assumption_required",
                message=(
                    "MULTIVARIATE toy_uov_public_map_verify plans must include "
                    f"{TOY_UOV_PUBLIC_MAP_ASSUMPTION}"
                ),
            )
        )
    oil_variables = _positive_int_param_for_model(
        operator,
        "oil_variables",
        findings,
        model_name=TOY_UOV_PUBLIC_MAP_MODEL,
    )
    vinegar_variables = _positive_int_param_for_model(
        operator,
        "vinegar_variables",
        findings,
        model_name=TOY_UOV_PUBLIC_MAP_MODEL,
    )
    variables = plan.target.variables
    if (
        oil_variables is not None
        and vinegar_variables is not None
        and variables is not None
        and oil_variables + vinegar_variables != variables
    ):
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_toy_uov_public_map_partition",
                message=(
                    "toy_uov_public_map_verify requires oil_variables + "
                    "vinegar_variables == variables"
                ),
            )
        )
    if plan.target.field != "GF(2)":
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_toy_uov_public_map_field",
                message="toy_uov_public_map_verify requires field GF(2)",
            )
        )
    if not plan.target.name.startswith("toy_uov_"):
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_toy_uov_public_map_target_name",
                message=(
                    "toy_uov_public_map_verify targets must start with toy_uov_"
                ),
            )
        )
    return findings


def _positive_int_param_for_model(
    operator: AttackOperator,
    name: str,
    findings: list[ValidationFinding],
    *,
    model_name: str,
) -> int | None:
    value = operator.params.get(name)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"multivariate_{model_name}_{name}",
                message=f"{model_name} requires positive integer {name}",
            )
        )
        return None
    return value


def _positive_int_param(
    operator: AttackOperator,
    name: str,
    findings: list[ValidationFinding],
) -> int | None:
    value = operator.params.get(name)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"multivariate_toy_minrank_{name}",
                message=f"toy_minrank_search requires positive integer {name}",
            )
        )
        return None
    return value


def _non_negative_int_param(
    operator: AttackOperator,
    name: str,
    findings: list[ValidationFinding],
) -> int | None:
    value = operator.params.get(name)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        findings.append(
            ValidationFinding(
                severity="error",
                code=f"multivariate_toy_minrank_{name}",
                message=f"toy_minrank_search requires non-negative integer {name}",
            )
        )
        return None
    return value


def _reproduce_mq_fixture(
    plan: AttackPlan,
    fixture_path: Path,
) -> ReproductionResult:
    try:
        hybrid_operator = _mq_hybrid_operator(plan)
        if hybrid_operator is None:
            solution = solve_toy_mq_fixture(fixture_path)
        else:
            guessed_variables = hybrid_operator.params.get("guessed_variables")
            if not isinstance(guessed_variables, int) or isinstance(
                guessed_variables,
                bool,
            ):
                raise ValueError(
                    "toy_mq_hybrid_search requires integer guessed_variables"
                )
            solution = solve_toy_mq_hybrid_fixture(
                fixture_path,
                guessed_variables=guessed_variables,
            )
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                f"MULTIVARIATE toy MQ fixture could not be solved: {exc}"
            ],
        )

    target_field_order = (
        field_order_from_notation(plan.target.field)
        if plan.target.field is not None
        else None
    )
    if (
        solution.solved
        and solution.target_name == plan.target.name
        and solution.variables == plan.target.variables
        and solution.equations == plan.target.equations
        and solution.field_order == target_field_order
        and solution.public
        and not solution.security_claim
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=MULTIVARIATE_INSTANCE_REPRODUCTION_SCORE,
            warnings=[_mq_reproduction_success_warning(plan)],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "MULTIVARIATE toy MQ fixture did not produce the expected "
            "public target solution."
        ],
    )


def _reproduce_uov_public_map_fixture(
    plan: AttackPlan,
    fixture_path: Path,
) -> ReproductionResult:
    try:
        result = verify_toy_uov_public_map_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                f"MULTIVARIATE toy UOV public-map fixture could not be "
                f"verified: {exc}"
            ],
        )

    target_field_order = (
        field_order_from_notation(plan.target.field)
        if plan.target.field is not None
        else None
    )
    operator = _uov_public_map_operator(plan)
    expected_oil = operator.params.get("oil_variables") if operator else None
    expected_vinegar = (
        operator.params.get("vinegar_variables") if operator else None
    )
    if (
        result.verified
        and result.target_name == plan.target.name
        and result.variables == plan.target.variables
        and result.equations == plan.target.equations
        and result.field_order == target_field_order
        and result.oil_variables == expected_oil
        and result.vinegar_variables == expected_vinegar
        and result.public
        and not result.security_claim
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=MULTIVARIATE_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Verified a public toy UOV-inspired public-map fixture; this "
                "is reproducibility plumbing, not a UOV, MAYO, or Rainbow "
                "result and not a security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "MULTIVARIATE toy UOV public-map fixture did not match the "
            "expected public target."
        ],
    )


def _reproduce_minrank_fixture(
    plan: AttackPlan,
    fixture_path: Path,
) -> ReproductionResult:
    try:
        solution = solve_toy_minrank_fixture(fixture_path)
    except (OSError, ValueError) as exc:
        return ReproductionResult(
            attempted=True,
            status="failed",
            success=False,
            warnings=[
                f"MULTIVARIATE toy MinRank fixture could not be solved: {exc}"
            ],
        )

    target_field_order = (
        field_order_from_notation(plan.target.field)
        if plan.target.field is not None
        else None
    )
    operator = _minrank_operator(plan)
    expected_rows = operator.params.get("matrix_rows") if operator else None
    expected_cols = operator.params.get("matrix_cols") if operator else None
    expected_rank = operator.params.get("target_rank") if operator else None
    if (
        solution.solved
        and solution.target_name == plan.target.name
        and solution.variables == plan.target.variables
        and solution.equations == plan.target.equations
        and solution.field_order == target_field_order
        and solution.matrix_rows == expected_rows
        and solution.matrix_cols == expected_cols
        and solution.target_rank == expected_rank
        and solution.public
        and not solution.security_claim
    ):
        return ReproductionResult(
            attempted=True,
            status="instance_solved",
            success=True,
            score=MULTIVARIATE_INSTANCE_REPRODUCTION_SCORE,
            warnings=[
                "Solved a public toy binary MinRank fixture with bounded "
                "exhaustive search; this is reproducibility plumbing, not "
                "a security claim."
            ],
        )
    return ReproductionResult(
        attempted=True,
        status="failed",
        success=False,
        warnings=[
            "MULTIVARIATE toy MinRank fixture did not produce the expected "
            "public target solution."
        ],
    )


def _validate_multivariate_shape(target: TargetSpec) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if target.family is not TargetFamily.MULTIVARIATE:
        findings.append(
            ValidationFinding(
                severity="error",
                code="family_adapter_mismatch",
                message=(
                    "MULTIVARIATE adapter cannot validate "
                    f"{target.family.value} targets"
                ),
            )
        )
        return findings

    if target.field is not None and not _is_finite_field_notation(target.field):
        findings.append(
            ValidationFinding(
                severity="error",
                code="multivariate_field_notation",
                message="MULTIVARIATE field must use GF(q) notation",
            )
        )
    return findings


def _is_finite_field_notation(field: str) -> bool:
    if not field.startswith("GF(") or not field.endswith(")"):
        return False
    order = field[3:-1]
    return order.isdigit() and int(order) > 1


def _resolve_fixture_path(
    value: str,
    fixture_root_parts: tuple[str, ...],
) -> tuple[Path | None, list[str]]:
    return resolve_public_fixture_path(
        value,
        repo_root=ROOT,
        package_fixture_dir=PACKAGE_FIXTURES,
        root_parts=fixture_root_parts,
        family_label="MULTIVARIATE",
    )


def _fixture_root_parts_for_plan(plan: AttackPlan) -> tuple[str, ...]:
    if _is_uov_public_map_plan(plan):
        return _UOV_FIXTURE_ROOT_PARTS
    if _is_minrank_plan(plan):
        return _MINRANK_FIXTURE_ROOT_PARTS
    return _MQ_FIXTURE_ROOT_PARTS


def _fixture_root_label(fixture_root_parts: tuple[str, ...]) -> str:
    return "/".join(fixture_root_parts) + "/"


def _is_minrank_plan(plan: AttackPlan) -> bool:
    return _minrank_operator(plan) is not None


def _is_mq_hybrid_plan(plan: AttackPlan) -> bool:
    return _mq_hybrid_operator(plan) is not None


def _is_mq_degree_bound_plan(plan: AttackPlan) -> bool:
    return _mq_degree_bound_operator(plan) is not None


def _is_uov_public_map_plan(plan: AttackPlan) -> bool:
    return _uov_public_map_operator(plan) is not None


def _uov_public_map_operator(plan: AttackPlan) -> AttackOperator | None:
    for operator in plan.operators:
        if (
            operator.type == "signature_fixture_check"
            and operator.params.get("signature_model") == TOY_UOV_PUBLIC_MAP_MODEL
        ):
            return operator
    return None


def _mq_hybrid_operator(plan: AttackPlan) -> AttackOperator | None:
    for operator in plan.operators:
        if (
            operator.type == "groebner_basis"
            and operator.params.get("model") == TOY_MQ_HYBRID_MODEL
        ):
            return operator
    return None


def _mq_degree_bound_operator(plan: AttackPlan) -> AttackOperator | None:
    for operator in plan.operators:
        if (
            operator.type == "groebner_basis"
            and operator.params.get("model") == TOY_MQ_DEGREE_BOUND_MODEL
        ):
            return operator
    return None


def _mq_reproduction_success_warning(plan: AttackPlan) -> str:
    if _is_mq_hybrid_plan(plan):
        return (
            "Solved a public toy binary MQ fixture with bounded guess-prefix "
            "split search for hybrid-search reproduction plumbing; this is "
            "not a UOV, MAYO, or Rainbow result and not a security claim."
        )
    if _is_mq_degree_bound_plan(plan):
        return (
            "Solved a public toy binary MQ fixture with bounded exhaustive "
            "search for degree-bound reproduction plumbing; this is not a "
            "Groebner proof, not a UOV, MAYO, or Rainbow result, and not a "
            "security claim."
        )
    return (
        "Solved a public toy binary MQ fixture with bounded exhaustive search; "
        "this is reproducibility plumbing, not a security claim."
    )


def _minrank_operator(plan: AttackPlan) -> AttackOperator | None:
    for operator in plan.operators:
        if operator.type == "minrank_attack":
            return operator
    return None


def _is_scoped_fixture_path(
    path: Path,
    fixture_root_parts: tuple[str, ...],
) -> bool:
    return is_scoped_public_fixture_path(path, fixture_root_parts)
