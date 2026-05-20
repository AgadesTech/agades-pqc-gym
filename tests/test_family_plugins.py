from __future__ import annotations

import importlib

from agades_pqc_gym.core.registry import default_family_registry
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.families.plugins import (
    family_plugin_descriptors,
    plugin_descriptor_entries_by_family,
)
from agades_pqc_gym.integrations.family_operator_catalog import (
    build_family_operator_catalog,
)

EXPECTED_PLUGINS = {
    "lattice": ["LWE", "MLWE", "NTRU", "SIS"],
    "code_based": ["CODE_BASED"],
    "multivariate": ["MULTIVARIATE"],
    "hash_based": ["HASH_BASED"],
    "isogeny_historical": ["ISOGENY_HISTORICAL"],
    "implementation_security": ["IMPLEMENTATION_SECURITY"],
}


def test_family_plugin_descriptors_cover_target_families_once() -> None:
    descriptors = family_plugin_descriptors()

    assert {
        descriptor.name: [entry.family.value for entry in descriptor.families]
        for descriptor in descriptors
    } == EXPECTED_PLUGINS
    observed_families = [
        entry.family
        for descriptor in descriptors
        for entry in descriptor.families
    ]
    assert sorted(observed_families, key=lambda family: family.value) == sorted(
        TargetFamily,
        key=lambda family: family.value,
    )


def test_family_plugin_descriptor_paths_are_importable() -> None:
    for descriptor in family_plugin_descriptors():
        module_name, object_name = descriptor.descriptor_path.rsplit(".", 1)
        module = importlib.import_module(module_name)

        assert getattr(module, object_name) is descriptor


def test_family_plugin_entries_match_runtime_registry_and_catalog() -> None:
    registry = default_family_registry()
    catalog_by_family = {
        family["family"]: family
        for family in build_family_operator_catalog()["families"]
    }

    for family, descriptor, entry in plugin_descriptor_entries_by_family().values():
        adapter = registry.get(family)
        catalog_entry = catalog_by_family[family.value]

        assert entry.adapter_class == (
            f"{adapter.__class__.__module__}.{adapter.__class__.__qualname__}"
        )
        assert entry.support_level == adapter.support_level
        assert (
            entry.applicability_validator
            == catalog_entry["applicability_validator"]
        )
        assert descriptor.name == catalog_entry["plugin"]
