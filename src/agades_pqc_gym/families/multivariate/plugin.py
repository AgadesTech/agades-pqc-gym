from __future__ import annotations

from agades_pqc_gym.core.family_plugin import (
    FamilyPluginDescriptor,
    FamilyPluginEntry,
)
from agades_pqc_gym.core.target import TargetFamily

PLUGIN_DESCRIPTOR = FamilyPluginDescriptor(
    name="multivariate",
    descriptor_path="agades_pqc_gym.families.multivariate.plugin.PLUGIN_DESCRIPTOR",
    families=(
        FamilyPluginEntry(
            family=TargetFamily.MULTIVARIATE,
            adapter_class=(
                "agades_pqc_gym.families.multivariate.adapter."
                "MultivariateFamilyAdapter"
            ),
            support_level="toy_evaluator",
            applicability_validator=(
                "agades_pqc_gym.families.multivariate.validators."
                "validate_multivariate_plan"
            ),
        ),
    ),
)

__all__ = ["PLUGIN_DESCRIPTOR"]
