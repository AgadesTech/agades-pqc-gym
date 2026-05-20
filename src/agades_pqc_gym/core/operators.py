from __future__ import annotations

from typing import Any

from agades_pqc_gym.core.target import TargetFamily

LATTICE_OPERATORS = frozenset(
    {
        "primal_usvp",
        "bounded_distance_decoding",
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

PLACEHOLDER_OPERATORS = {
    TargetFamily.CODE_BASED: frozenset(
        {"decoding_fixture_check", "information_set_decoding"}
    ),
    TargetFamily.MULTIVARIATE: frozenset(
        {"minrank_attack", "groebner_basis", "signature_fixture_check"}
    ),
    TargetFamily.HASH_BASED: frozenset(
        {"security_bound_check", "hash_signature_verification", "misuse_check"}
    ),
    TargetFamily.ISOGENY_HISTORICAL: frozenset(
        {"historical_isogeny_reconstruction"}
    ),
    TargetFamily.IMPLEMENTATION_SECURITY: frozenset(
        {"kat_conformance", "constant_time_check", "benchmark_harness"}
    ),
}

ALLOWED_OPERATORS = frozenset().union(
    LATTICE_OPERATORS,
    *PLACEHOLDER_OPERATORS.values(),
)

_REQUIRED_PARAM_TYPES: dict[str, dict[str, type | tuple[type, ...]]] = {
    "primal_usvp": {"beta": int},
    "bounded_distance_decoding": {"beta": int},
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
    "decoding_fixture_check": {"variant": str},
    "information_set_decoding": {"variant": str},
    "minrank_attack": {"model": str},
    "groebner_basis": {"model": str},
    "signature_fixture_check": {"signature_model": str},
    "security_bound_check": {"bound_model": str},
    "hash_signature_verification": {"signature_model": str},
    "misuse_check": {"fixture": str},
    "historical_isogeny_reconstruction": {"case": str},
    "kat_conformance": {"suite": str},
    "constant_time_check": {"tool": str},
    "benchmark_harness": {"metric": str},
}


def supported_operators_for_family(family: TargetFamily) -> set[str]:
    lattice_families = {
        TargetFamily.LWE,
        TargetFamily.MLWE,
        TargetFamily.NTRU,
        TargetFamily.SIS,
    }
    if family in lattice_families:
        return set(LATTICE_OPERATORS)
    return set(PLACEHOLDER_OPERATORS.get(family, frozenset()))


def operator_required_param_schema(operator_type: str) -> dict[str, str]:
    if operator_type not in ALLOWED_OPERATORS:
        raise KeyError(f"unsupported operator type: {operator_type}")
    return {
        name: expected_type_name(expected_type)
        for name, expected_type in sorted(_REQUIRED_PARAM_TYPES[operator_type].items())
    }


def all_operator_required_param_schemas() -> dict[str, dict[str, str]]:
    return {
        operator_type: operator_required_param_schema(operator_type)
        for operator_type in sorted(ALLOWED_OPERATORS)
    }


def validate_operator_params(operator_type: str, params: dict[str, Any]) -> list[str]:
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
