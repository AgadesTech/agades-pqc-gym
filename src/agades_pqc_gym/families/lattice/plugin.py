from __future__ import annotations

from agades_pqc_gym.core.family_plugin import (
    FamilyPluginDescriptor,
    FamilyPluginEntry,
)
from agades_pqc_gym.core.target import TargetFamily

LATTICE_ADAPTER = "agades_pqc_gym.families.lattice.adapter.LatticeFamilyAdapter"
LATTICE_VALIDATOR = (
    "agades_pqc_gym.families.lattice.validators.validate_lattice_plan"
)

PLUGIN_DESCRIPTOR = FamilyPluginDescriptor(
    name="lattice",
    descriptor_path="agades_pqc_gym.families.lattice.plugin.PLUGIN_DESCRIPTOR",
    families=(
        FamilyPluginEntry(
            family=TargetFamily.LWE,
            adapter_class=LATTICE_ADAPTER,
            support_level="implemented",
            applicability_validator=LATTICE_VALIDATOR,
        ),
        FamilyPluginEntry(
            family=TargetFamily.MLWE,
            adapter_class=LATTICE_ADAPTER,
            support_level="implemented",
            applicability_validator=LATTICE_VALIDATOR,
        ),
        FamilyPluginEntry(
            family=TargetFamily.NTRU,
            adapter_class=LATTICE_ADAPTER,
            support_level="schema_only",
            applicability_validator=LATTICE_VALIDATOR,
        ),
        FamilyPluginEntry(
            family=TargetFamily.SIS,
            adapter_class=LATTICE_ADAPTER,
            support_level="schema_only",
            applicability_validator=LATTICE_VALIDATOR,
        ),
    ),
)

__all__ = ["PLUGIN_DESCRIPTOR"]
