from agades_pqc_gym.core.registry import default_family_registry
from agades_pqc_gym.core.target import TargetFamily


def test_default_registry_exposes_all_declared_family_adapters() -> None:
    registry = default_family_registry()

    assert registry.get(TargetFamily.LWE).family is TargetFamily.LWE
    assert registry.get(TargetFamily.MLWE).family is TargetFamily.MLWE
    assert registry.get(TargetFamily.CODE_BASED).family is TargetFamily.CODE_BASED
    assert registry.get(TargetFamily.MULTIVARIATE).family is TargetFamily.MULTIVARIATE
    assert registry.get(TargetFamily.HASH_BASED).family is TargetFamily.HASH_BASED
    assert (
        registry.get(TargetFamily.ISOGENY_HISTORICAL).family
        is TargetFamily.ISOGENY_HISTORICAL
    )
    assert (
        registry.get(TargetFamily.IMPLEMENTATION_SECURITY).family
        is TargetFamily.IMPLEMENTATION_SECURITY
    )


def test_default_registry_reports_current_family_support_levels() -> None:
    registry = default_family_registry()

    assert registry.get(TargetFamily.CODE_BASED).support_level == "toy_evaluator"
    assert registry.get(TargetFamily.HASH_BASED).support_level == "toy_evaluator"
    assert registry.get(TargetFamily.MULTIVARIATE).support_level == "toy_evaluator"
    assert registry.get(TargetFamily.ISOGENY_HISTORICAL).support_level == (
        "toy_evaluator"
    )
    assert (
        registry.get(TargetFamily.IMPLEMENTATION_SECURITY).support_level
        == "toy_evaluator"
    )
