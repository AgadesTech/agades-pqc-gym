from __future__ import annotations

from agades_pqc_gym.core.family_plugin import (
    FamilyPluginDescriptor,
    FamilyPluginEntry,
)
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.families.code_based.plugin import (
    PLUGIN_DESCRIPTOR as CODE_BASED_PLUGIN_DESCRIPTOR,
)
from agades_pqc_gym.families.hash_based.plugin import (
    PLUGIN_DESCRIPTOR as HASH_BASED_PLUGIN_DESCRIPTOR,
)
from agades_pqc_gym.families.implementation_security.plugin import (
    PLUGIN_DESCRIPTOR as IMPLEMENTATION_SECURITY_PLUGIN_DESCRIPTOR,
)
from agades_pqc_gym.families.isogeny_historical.plugin import (
    PLUGIN_DESCRIPTOR as ISOGENY_HISTORICAL_PLUGIN_DESCRIPTOR,
)
from agades_pqc_gym.families.lattice.plugin import (
    PLUGIN_DESCRIPTOR as LATTICE_PLUGIN_DESCRIPTOR,
)
from agades_pqc_gym.families.multivariate.plugin import (
    PLUGIN_DESCRIPTOR as MULTIVARIATE_PLUGIN_DESCRIPTOR,
)

FamilyPluginBinding = tuple[
    TargetFamily,
    FamilyPluginDescriptor,
    FamilyPluginEntry,
]


def family_plugin_descriptors() -> tuple[FamilyPluginDescriptor, ...]:
    return (
        LATTICE_PLUGIN_DESCRIPTOR,
        CODE_BASED_PLUGIN_DESCRIPTOR,
        MULTIVARIATE_PLUGIN_DESCRIPTOR,
        HASH_BASED_PLUGIN_DESCRIPTOR,
        ISOGENY_HISTORICAL_PLUGIN_DESCRIPTOR,
        IMPLEMENTATION_SECURITY_PLUGIN_DESCRIPTOR,
    )


def plugin_descriptor_entries_by_family() -> dict[TargetFamily, FamilyPluginBinding]:
    entries: dict[TargetFamily, FamilyPluginBinding] = {}
    for descriptor in family_plugin_descriptors():
        for entry in descriptor.families:
            if entry.family in entries:
                raise ValueError(
                    f"{entry.family.value} is declared by more than one plugin"
                )
            entries[entry.family] = (entry.family, descriptor, entry)

    missing = set(TargetFamily) - set(entries)
    if missing:
        missing_names = ", ".join(sorted(family.value for family in missing))
        raise ValueError(f"missing family plugin descriptors: {missing_names}")
    return entries
