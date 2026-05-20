from __future__ import annotations

from agades_pqc_gym.core.family_plugin import (
    FamilyPluginDescriptor,
    FamilyPluginEntry,
)
from agades_pqc_gym.core.target import TargetFamily

PLUGIN_DESCRIPTOR = FamilyPluginDescriptor(
    name="implementation_security",
    descriptor_path=(
        "agades_pqc_gym.families.implementation_security.plugin.PLUGIN_DESCRIPTOR"
    ),
    families=(
        FamilyPluginEntry(
            family=TargetFamily.IMPLEMENTATION_SECURITY,
            adapter_class=(
                "agades_pqc_gym.families.implementation_security.adapter."
                "ImplementationSecurityFamilyAdapter"
            ),
            support_level="toy_evaluator",
            applicability_validator=(
                "agades_pqc_gym.families.implementation_security.validators."
                "validate_implementation_security_plan"
            ),
        ),
    ),
)

__all__ = ["PLUGIN_DESCRIPTOR"]
