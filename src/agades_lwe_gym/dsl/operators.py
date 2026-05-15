from __future__ import annotations

from typing import Any

ALLOWED_OPERATORS = frozenset(
    {
        "primal_usvp",
        "dual_attack",
        "dual_hybrid",
        "bkw",
        "modulus_switching",
        "sample_selection",
        "secret_guessing",
        "meet_in_the_middle",
        "normal_form_transform",
        "bkz_parameter_sweep",
        "module_lattice_reduction_hypothesis",
    }
)

_REQUIRED_PARAM_TYPES: dict[str, dict[str, type | tuple[type, ...]]] = {
    "primal_usvp": {"beta": int},
    "dual_attack": {"beta": int},
    "dual_hybrid": {"zeta": int, "beta": int},
    "bkw": {"block_size": int},
    "modulus_switching": {"q_prime": int},
    "sample_selection": {"sample_count": int},
    "secret_guessing": {"guess_dimension": int},
    "meet_in_the_middle": {"split_dimension": int},
    "normal_form_transform": {},
    "bkz_parameter_sweep": {"beta_min": int, "beta_max": int},
    "module_lattice_reduction_hypothesis": {"model": str},
}


def validate_operator_params(operator_type: str, params: dict[str, Any]) -> list[str]:
    """Return human-readable parameter validation errors for one operator."""
    if operator_type not in ALLOWED_OPERATORS:
        return [f"unsupported operator type: {operator_type}"]

    errors: list[str] = []
    required = _REQUIRED_PARAM_TYPES[operator_type]
    for name, expected_type in required.items():
        if name not in params:
            errors.append(f"{operator_type} requires parameter {name}")
            continue
        value = params[name]
        if not isinstance(value, expected_type):
            errors.append(
                f"{operator_type}.{name} must be {expected_type_name(expected_type)}"
            )
        elif isinstance(value, int) and value <= 0:
            errors.append(f"{operator_type}.{name} must be positive")

    if operator_type == "modulus_switching" and params.get("q_prime", 1) <= 1:
        errors.append("modulus_switching.q_prime must be greater than 1")
    if operator_type == "dual_hybrid" and params.get("zeta", 1) <= 0:
        errors.append("dual_hybrid.zeta must be positive")
    if operator_type == "bkz_parameter_sweep":
        beta_min = params.get("beta_min")
        beta_max = params.get("beta_max")
        if (
            isinstance(beta_min, int)
            and isinstance(beta_max, int)
            and beta_min > beta_max
        ):
            errors.append("bkz_parameter_sweep.beta_min cannot exceed beta_max")

    return errors


def expected_type_name(expected_type: type | tuple[type, ...]) -> str:
    if isinstance(expected_type, tuple):
        return " or ".join(item.__name__ for item in expected_type)
    return expected_type.__name__
