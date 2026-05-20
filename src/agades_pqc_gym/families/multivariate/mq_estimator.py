from __future__ import annotations

import math

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.evaluators.base import EstimatorResult

TOY_MQ_MODEL = "toy_mq_search"
TOY_MQ_ASSUMPTION = "toy_mq_exhaustive_search_model"
TOY_MQ_HYBRID_MODEL = "toy_mq_hybrid_search"
TOY_MQ_HYBRID_ASSUMPTION = "toy_mq_hybrid_linearization_model"
TOY_MQ_DEGREE_BOUND_MODEL = "toy_mq_degree_bound"
TOY_MQ_DEGREE_BOUND_ASSUMPTION = "toy_mq_degree_bound_model"
TOY_MINRANK_MODEL = "toy_minrank_search"
TOY_MINRANK_ASSUMPTION = "toy_minrank_exhaustive_search_model"
TOY_UOV_PUBLIC_MAP_MODEL = "toy_uov_public_map_verify"
TOY_UOV_PUBLIC_MAP_ASSUMPTION = "toy_uov_public_map_verification_model"


class ToyMultivariateMQEstimator:
    """Toy multivariate exhaustive-search bounds for public verifier plumbing."""

    estimator_name = "toy-multivariate-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _multivariate_operator(plan)
        if operator.type == "signature_fixture_check":
            return _estimate_uov_public_map(plan, operator)
        if operator.type == "minrank_attack":
            return _estimate_minrank(plan, operator)
        if operator.params.get("model") == TOY_MQ_DEGREE_BOUND_MODEL:
            return _estimate_mq_degree_bound(plan, operator)
        if operator.params.get("model") == TOY_MQ_HYBRID_MODEL:
            return _estimate_mq_hybrid(plan, operator)

        variables = _required_int(plan.target.variables, "variables")
        equations = _required_int(plan.target.equations, "equations")
        field_order = field_order_from_notation(
            _required_str(plan.target.field, "field")
        )

        assignment_space_bits = variables * math.log2(field_order)
        equation_check_bits = math.log2(equations)
        time_bits = assignment_space_bits + equation_check_bits
        memory_bits = math.log2(variables + equations)

        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            evaluation_status="ok",
            attack_type=f"{operator.type}:{operator.params['model']}",
            time_bits=round(time_bits, 4),
            memory_bits=round(memory_bits, 4),
            success_probability=None,
            raw_output={
                "assignment_space_bits": round(assignment_space_bits, 4),
                "equation_check_bits": round(equation_check_bits, 4),
                "equations": equations,
                "field_order": field_order,
                "model": TOY_MQ_MODEL,
                "variables": variables,
            },
            warnings=[
                "Toy multivariate MQ output is for public evaluator plumbing "
                "only; it is not a security claim."
            ],
        )


def _estimate_mq_hybrid(plan: AttackPlan, operator: AttackOperator) -> EstimatorResult:
    variables = _required_int(plan.target.variables, "variables")
    equations = _required_int(plan.target.equations, "equations")
    field_order = field_order_from_notation(_required_str(plan.target.field, "field"))
    guessed_variables = _required_int(
        operator.params.get("guessed_variables"),
        "guessed_variables",
    )
    residual_variables = variables - guessed_variables
    if guessed_variables < 1 or residual_variables < 1:
        raise ValueError(
            "toy_mq_hybrid_search requires 1 <= guessed_variables < variables"
        )

    linearized_monomials = 1 + residual_variables + (
        residual_variables * (residual_variables + 1)
    ) // 2
    guess_space_bits = guessed_variables * math.log2(field_order)
    linear_algebra_bits = math.log2(linearized_monomials**3)
    equation_check_bits = math.log2(equations)
    time_bits = guess_space_bits + linear_algebra_bits + equation_check_bits
    memory_bits = math.log2((linearized_monomials**2) + equations)

    return EstimatorResult(
        estimator_name=ToyMultivariateMQEstimator.estimator_name,
        estimator_version=ToyMultivariateMQEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{operator.params['model']}",
        time_bits=round(time_bits, 4),
        memory_bits=round(memory_bits, 4),
        success_probability=None,
        raw_output={
            "equation_check_bits": round(equation_check_bits, 4),
            "equations": equations,
            "field_order": field_order,
            "guess_space_bits": round(guess_space_bits, 4),
            "guessed_variables": guessed_variables,
            "linear_algebra_bits": round(linear_algebra_bits, 4),
            "linearized_monomials": linearized_monomials,
            "model": TOY_MQ_HYBRID_MODEL,
            "residual_variables": residual_variables,
            "variables": variables,
        },
        warnings=[
            "Toy multivariate MQ hybrid-search output is for public evaluator "
            "plumbing only; it is not a UOV, MAYO, or Rainbow result and not "
            "a security claim."
        ],
    )


def _estimate_mq_degree_bound(
    plan: AttackPlan,
    operator: AttackOperator,
) -> EstimatorResult:
    variables = _required_int(plan.target.variables, "variables")
    equations = _required_int(plan.target.equations, "equations")
    field_order = field_order_from_notation(_required_str(plan.target.field, "field"))
    degree_bound = _required_int(operator.params.get("degree_bound"), "degree_bound")
    linear_algebra_omega = _required_number(
        operator.params.get("linear_algebra_omega"),
        "linear_algebra_omega",
    )
    if degree_bound < 2 or degree_bound > variables:
        raise ValueError(
            "toy_mq_degree_bound requires 2 <= degree_bound <= variables"
        )
    if linear_algebra_omega < 2.0 or linear_algebra_omega > 3.0:
        raise ValueError(
            "toy_mq_degree_bound requires 2.0 <= linear_algebra_omega <= 3.0"
        )

    monomial_count = math.comb(variables + degree_bound, degree_bound)
    multiplier_degree = max(degree_bound - 2, 0)
    macaulay_rows = equations * math.comb(
        variables + multiplier_degree,
        multiplier_degree,
    )
    linear_algebra_bits = linear_algebra_omega * math.log2(monomial_count)
    field_operation_bits = math.log2(field_order)
    equation_check_bits = math.log2(equations)
    time_bits = linear_algebra_bits + field_operation_bits + equation_check_bits
    memory_bits = math.log2(macaulay_rows * monomial_count)

    return EstimatorResult(
        estimator_name=ToyMultivariateMQEstimator.estimator_name,
        estimator_version=ToyMultivariateMQEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{operator.params['model']}",
        time_bits=round(time_bits, 4),
        memory_bits=round(memory_bits, 4),
        success_probability=None,
        raw_output={
            "degree_bound": degree_bound,
            "equation_check_bits": round(equation_check_bits, 4),
            "equations": equations,
            "field_operation_bits": round(field_operation_bits, 4),
            "field_order": field_order,
            "linear_algebra_bits": round(linear_algebra_bits, 4),
            "linear_algebra_omega": linear_algebra_omega,
            "macaulay_rows": macaulay_rows,
            "model": TOY_MQ_DEGREE_BOUND_MODEL,
            "monomial_count": monomial_count,
            "variables": variables,
        },
        warnings=[
            "Toy multivariate MQ degree-bound output is for public evaluator "
            "plumbing only; it is not a Groebner proof, not a UOV, MAYO, or "
            "Rainbow result, and not a security claim."
        ],
    )


def _estimate_uov_public_map(
    plan: AttackPlan,
    operator: AttackOperator,
) -> EstimatorResult:
    signature_model = _required_str(
        operator.params.get("signature_model"),
        "signature_model",
    )
    if signature_model != TOY_UOV_PUBLIC_MAP_MODEL:
        raise ValueError(
            "MULTIVARIATE signature_fixture_check supports only "
            f"signature_model={TOY_UOV_PUBLIC_MAP_MODEL}"
        )
    if plan.target.field != "GF(2)":
        raise ValueError("toy_uov_public_map_verify requires field GF(2)")
    if not plan.target.name.startswith("toy_uov_"):
        raise ValueError("toy_uov_public_map_verify targets must start with toy_uov_")
    variables = _required_int(plan.target.variables, "variables")
    equations = _required_int(plan.target.equations, "equations")
    field_order = field_order_from_notation(_required_str(plan.target.field, "field"))
    oil_variables = _required_int(operator.params.get("oil_variables"), "oil_variables")
    vinegar_variables = _required_int(
        operator.params.get("vinegar_variables"),
        "vinegar_variables",
    )
    if oil_variables + vinegar_variables != variables:
        raise ValueError(
            "toy_uov_public_map_verify requires oil_variables + "
            "vinegar_variables == variables"
        )

    monomial_count = 1 + variables + (variables * (variables + 1)) // 2
    evaluation_bits = math.log2(equations * monomial_count)
    field_operation_bits = math.log2(field_order)
    time_bits = evaluation_bits + field_operation_bits
    memory_bits = math.log2(
        variables + equations + monomial_count + oil_variables + vinegar_variables
    )

    return EstimatorResult(
        estimator_name=ToyMultivariateMQEstimator.estimator_name,
        estimator_version=ToyMultivariateMQEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{signature_model}",
        time_bits=round(time_bits, 4),
        memory_bits=round(memory_bits, 4),
        success_probability=None,
        raw_output={
            "equations": equations,
            "evaluation_bits": round(evaluation_bits, 4),
            "field_operation_bits": round(field_operation_bits, 4),
            "field_order": field_order,
            "model": TOY_UOV_PUBLIC_MAP_MODEL,
            "monomial_count": monomial_count,
            "oil_variables": oil_variables,
            "variables": variables,
            "vinegar_variables": vinegar_variables,
        },
        warnings=[
            "Toy UOV-inspired public-map verification output is for public "
            "evaluator plumbing only; it is not a UOV, MAYO, or Rainbow "
            "result and not a security claim."
        ],
    )


def _multivariate_operator(plan: AttackPlan) -> AttackOperator:
    for operator in plan.operators:
        if operator.type in {
            "groebner_basis",
            "minrank_attack",
            "signature_fixture_check",
        }:
            return operator
    raise ValueError(
        "MULTIVARIATE estimate requires groebner_basis, minrank_attack, "
        "or signature_fixture_check"
    )


def _estimate_minrank(plan: AttackPlan, operator: AttackOperator) -> EstimatorResult:
    variables = _required_int(plan.target.variables, "variables")
    field_order = field_order_from_notation(_required_str(plan.target.field, "field"))
    matrix_rows = _required_int(operator.params.get("matrix_rows"), "matrix_rows")
    matrix_cols = _required_int(operator.params.get("matrix_cols"), "matrix_cols")
    target_rank = _required_int(operator.params.get("target_rank"), "target_rank")

    assignment_space_bits = variables * math.log2(field_order)
    rank_operations = matrix_rows * matrix_cols * min(matrix_rows, matrix_cols)
    rank_cost_bits = math.log2(rank_operations)
    time_bits = assignment_space_bits + rank_cost_bits
    memory_bits = math.log2((matrix_rows * matrix_cols) + variables)

    return EstimatorResult(
        estimator_name=ToyMultivariateMQEstimator.estimator_name,
        estimator_version=ToyMultivariateMQEstimator.estimator_version,
        estimator_commit=None,
        evaluation_status="ok",
        attack_type=f"{operator.type}:{operator.params['model']}",
        time_bits=round(time_bits, 4),
        memory_bits=round(memory_bits, 4),
        success_probability=None,
        raw_output={
            "assignment_space_bits": round(assignment_space_bits, 4),
            "field_order": field_order,
            "matrix_cols": matrix_cols,
            "matrix_rows": matrix_rows,
            "model": TOY_MINRANK_MODEL,
            "rank_cost_bits": round(rank_cost_bits, 4),
            "target_rank": target_rank,
            "variables": variables,
        },
        warnings=[
            "Toy multivariate MinRank output is for public evaluator plumbing "
            "only; it is not a security claim."
        ],
    )


def _required_int(value: int | None, name: str) -> int:
    if value is None:
        raise ValueError(f"MULTIVARIATE target requires {name}")
    return value


def _required_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"MULTIVARIATE target requires numeric {name}")
    return float(value)


def _required_str(value: str | None, name: str) -> str:
    if value is None:
        raise ValueError(f"MULTIVARIATE target requires {name}")
    return value


def field_order_from_notation(field: str) -> int:
    if not field.startswith("GF(") or not field.endswith(")"):
        raise ValueError("MULTIVARIATE field must use GF(q) notation")
    order = field[3:-1]
    if not order.isdigit():
        raise ValueError("MULTIVARIATE field must use GF(q) notation")
    return int(order)
