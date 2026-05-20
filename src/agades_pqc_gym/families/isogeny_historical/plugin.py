from __future__ import annotations

from agades_pqc_gym.core.family_plugin import (
    FamilyPluginDescriptor,
    FamilyPluginEntry,
)
from agades_pqc_gym.core.target import TargetFamily

PLUGIN_DESCRIPTOR = FamilyPluginDescriptor(
    name="isogeny_historical",
    descriptor_path=(
        "agades_pqc_gym.families.isogeny_historical.plugin.PLUGIN_DESCRIPTOR"
    ),
    families=(
        FamilyPluginEntry(
            family=TargetFamily.ISOGENY_HISTORICAL,
            adapter_class=(
                "agades_pqc_gym.families.isogeny_historical.adapter."
                "IsogenyHistoricalFamilyAdapter"
            ),
            support_level="toy_evaluator",
            applicability_validator=(
                "agades_pqc_gym.families.isogeny_historical.validators."
                "validate_isogeny_historical_plan"
            ),
        ),
    ),
)

__all__ = ["PLUGIN_DESCRIPTOR"]
