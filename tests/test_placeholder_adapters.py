from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.registry import default_family_registry
from agades_pqc_gym.core.seeds import seed_plan_for_target
from agades_pqc_gym.core.target import SupportLevel, TargetFamily, TargetSpec
from agades_pqc_gym.evaluators.cascade import CascadeEvaluator
from agades_pqc_gym.families.implementation_security.adapter import (
    _SCHEMA_PLACEHOLDER_PARAM_BY_OPERATOR,
)
from agades_pqc_gym.validators.static import validate_attack_plan


def test_code_based_placeholder_validates_but_evaluates_as_unsupported() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/code_based_isd_placeholder.json").read_text()
    )
    result = CascadeEvaluator().evaluate_plan(plan)

    assert result.valid is False
    assert result.metrics["evaluation_status"] == "unsupported"
    assert result.metrics["combined_score"] == -1e9
    assert result.estimator_result is not None
    assert result.estimator_result.time_bits is None
    assert "not implemented" in result.warnings[0].lower()


def test_implementation_security_placeholder_is_registered() -> None:
    plan = AttackPlan.model_validate_json(
        Path(
            "examples/attack_plans/implementation_security_constant_time_placeholder.json"
        ).read_text()
    )
    adapter = default_family_registry().get(TargetFamily.IMPLEMENTATION_SECURITY)
    result = CascadeEvaluator().evaluate_plan(plan)

    assert adapter.supported_operators() == {
        "benchmark_harness",
        "constant_time_check",
        "kat_conformance",
    }
    assert result.valid is False
    assert result.metrics["evaluation_status"] == "unsupported"
    assert result.estimator_result is not None
    assert (
        result.estimator_result.estimator_name
        == "implementation-security-placeholder-evaluator"
    )


def test_implementation_security_seed_plan_uses_schema_placeholder_contract() -> None:
    target = TargetSpec(
        family=TargetFamily.IMPLEMENTATION_SECURITY,
        name="kyber_reference_constant_time_schema",
        support_level=SupportLevel.SCHEMA_ONLY,
    )

    plan = seed_plan_for_target(target)
    result = validate_attack_plan(plan)

    assert result.valid is True
    assert plan.operators[0].type == "benchmark_harness"
    assert plan.operators[0].params == {
        "metric": "implementation_security_benchmark_schema_placeholder"
    }


def test_implementation_security_contract_covers_registered_operators() -> None:
    adapter = default_family_registry().get(TargetFamily.IMPLEMENTATION_SECURITY)

    assert set(_SCHEMA_PLACEHOLDER_PARAM_BY_OPERATOR) == adapter.supported_operators()


def test_schema_only_adapters_reject_family_inapplicable_targets() -> None:
    cases = [
        (
            "examples/attack_plans/code_based_isd_placeholder.json",
            ("target", "k"),
            17669,
            "CODE_BASED target k must be smaller than n",
        ),
        (
            "examples/attack_plans/multivariate_minrank_placeholder.json",
            ("target", "field"),
            "Zmod(16)",
            "MULTIVARIATE field must use GF(q) notation",
        ),
        (
            "examples/attack_plans/hash_based_bound_placeholder.json",
            ("target", "hash_function"),
            "MD5",
            "HASH_BASED hash_function must be one of",
        ),
        (
            "examples/attack_plans/isogeny_historical_placeholder.json",
            ("operators", 0, "assumptions"),
            ["schema_only_no_estimator"],
            "ISOGENY_HISTORICAL plans require historical_not_current_standard",
        ),
        (
            "examples/attack_plans/implementation_security_constant_time_placeholder.json",
            ("target", "name"),
            "kyber_reference_constant_time",
            "IMPLEMENTATION_SECURITY target name must identify a schema-only fixture",
        ),
        (
            "examples/attack_plans/implementation_security_constant_time_placeholder.json",
            ("target", "name"),
            "schema_kyber_reference_constant_time",
            "IMPLEMENTATION_SECURITY target name must identify a schema-only fixture",
        ),
        (
            "examples/attack_plans/implementation_security_constant_time_placeholder.json",
            ("operators", 0, "params", "tool"),
            "dudect",
            "IMPLEMENTATION_SECURITY schema-only operator constant_time_check "
            "requires placeholder parameter tool ending in _schema_placeholder",
        ),
        (
            "examples/attack_plans/implementation_security_constant_time_placeholder.json",
            ("operators", 0, "params", "binary_path"),
            "build/kyber_kat",
            "IMPLEMENTATION_SECURITY schema-only plans must not reference "
            "executable/live artifact parameter binary_path",
        ),
    ]

    for path, mutation_path, value, expected_error in cases:
        data = AttackPlan.model_validate_json(Path(path).read_text()).model_dump(
            mode="json"
        )
        cursor = data
        for key in mutation_path[:-1]:
            cursor = cursor[key]
        cursor[mutation_path[-1]] = value

        result = validate_attack_plan(AttackPlan.model_validate(data))

        assert result.valid is False
        assert any(expected_error in error for error in result.errors)
