from __future__ import annotations

from agades_pqc_gym.core.family_plugin import (
    FamilyPluginDescriptor,
    FamilyPluginEntry,
)
from agades_pqc_gym.core.target import TargetFamily

PLUGIN_DESCRIPTOR = FamilyPluginDescriptor(
    name="code_based",
    descriptor_path="agades_pqc_gym.families.code_based.plugin.PLUGIN_DESCRIPTOR",
    families=(
        FamilyPluginEntry(
            family=TargetFamily.CODE_BASED,
            adapter_class=(
                "agades_pqc_gym.families.code_based.adapter."
                "CodeBasedFamilyAdapter"
            ),
            support_level="toy_evaluator",
            applicability_validator=(
                "agades_pqc_gym.families.code_based.validators."
                "validate_code_based_plan"
            ),
        ),
    ),
)

__all__ = ["PLUGIN_DESCRIPTOR"]
