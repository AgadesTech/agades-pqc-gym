from __future__ import annotations

import math
from typing import Any

from agades_pqc_gym.core.attack_plan import AttackOperator, AttackPlan
from agades_pqc_gym.evaluators.base import EstimatorResult

TOY_ISOGENY_CASE = "toy_sidh_path_search"
TOY_ISOGENY_COMMUTATIVE_WALK_CASE = "toy_commutative_walk_search"
TOY_ISOGENY_VOLCANO_WALK_CASE = "toy_volcano_walk_search"
TOY_ISOGENY_ASSUMPTION = "historical_toy_isogeny_path_model"
TOY_ISOGENY_COMMUTATIVE_WALK_ASSUMPTION = "historical_toy_commutative_walk_model"
TOY_ISOGENY_VOLCANO_WALK_ASSUMPTION = "historical_toy_volcano_walk_model"
HISTORICAL_NOT_CURRENT_ASSUMPTION = "historical_not_current_standard"
TOY_ISOGENY_MAX_WALK_LENGTH = 32
TOY_ISOGENY_MAX_BRANCHING_FACTOR = 8
TOY_ISOGENY_MAX_VOLCANO_HEIGHT = 8
TOY_ISOGENY_ASSUMPTIONS_BY_CASE = {
    TOY_ISOGENY_CASE: TOY_ISOGENY_ASSUMPTION,
    TOY_ISOGENY_COMMUTATIVE_WALK_CASE: TOY_ISOGENY_COMMUTATIVE_WALK_ASSUMPTION,
    TOY_ISOGENY_VOLCANO_WALK_CASE: TOY_ISOGENY_VOLCANO_WALK_ASSUMPTION,
}
TOY_ISOGENY_CASES = frozenset(TOY_ISOGENY_ASSUMPTIONS_BY_CASE)


class ToyIsogenyHistoricalPathEstimator:
    """Historical toy isogeny path-search bound for public verifier plumbing."""

    estimator_name = "toy-isogeny-historical-path-estimator"
    estimator_version = "0.1.0"

    def estimate(self, plan: AttackPlan) -> EstimatorResult:
        operator = _path_operator(plan)
        n = _required_int(plan.target.n, "n")
        walk_length = required_int(operator.params, "walk_length")
        branching_factor = required_int(operator.params, "branching_factor")
        case = operator.params["case"]

        path_count_bits = walk_length * math.log2(branching_factor)
        field_overhead_bits = math.log2(n)
        time_bits = path_count_bits + field_overhead_bits
        memory_input_size = n + walk_length + branching_factor
        raw_output: dict[str, Any] = {
            "branching_factor": branching_factor,
            "case": case,
            "field_overhead_bits": round(field_overhead_bits, 4),
            "model": TOY_ISOGENY_ASSUMPTIONS_BY_CASE[case],
            "n": n,
            "path_count_bits": round(path_count_bits, 4),
            "walk_length": walk_length,
        }
        if case == TOY_ISOGENY_VOLCANO_WALK_CASE:
            volcano_height = required_int(operator.params, "volcano_height")
            volcano_overhead_bits = math.log2(volcano_height + 1)
            time_bits += volcano_overhead_bits
            memory_input_size += volcano_height
            raw_output["volcano_height"] = volcano_height
            raw_output["volcano_overhead_bits"] = round(
                volcano_overhead_bits,
                4,
            )
        memory_bits = math.log2(memory_input_size)

        return EstimatorResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            estimator_commit=None,
            evaluation_status="ok",
            attack_type=f"{operator.type}:{case}",
            time_bits=round(time_bits, 4),
            memory_bits=round(memory_bits, 4),
            success_probability=None,
            raw_output=raw_output,
            warnings=[
                "This historical toy isogeny output is for public evaluator "
                "plumbing only; it is not a current-standard claim and not a "
                "security claim."
            ],
        )


def _path_operator(plan: AttackPlan) -> AttackOperator:
    for operator in plan.operators:
        if operator.type == "historical_isogeny_reconstruction":
            return operator
    raise ValueError(
        "ISOGENY_HISTORICAL estimate requires "
        "historical_isogeny_reconstruction"
    )


def required_int(params: dict[str, Any], name: str) -> int:
    value = params.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"ISOGENY_HISTORICAL toy path requires {name}")
    return value


def _required_int(value: int | None, name: str) -> int:
    if value is None:
        raise ValueError(f"ISOGENY_HISTORICAL target requires {name}")
    return value
