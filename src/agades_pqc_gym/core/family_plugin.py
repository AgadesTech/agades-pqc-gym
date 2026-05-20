from __future__ import annotations

from dataclasses import dataclass

from agades_pqc_gym.core.target import TargetFamily


@dataclass(frozen=True)
class FamilyPluginEntry:
    family: TargetFamily
    adapter_class: str
    support_level: str
    applicability_validator: str


@dataclass(frozen=True)
class FamilyPluginDescriptor:
    name: str
    descriptor_path: str
    families: tuple[FamilyPluginEntry, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("family plugin descriptor name must be non-empty")
        if not self.descriptor_path:
            raise ValueError(
                "family plugin descriptor_path must be a non-empty dotted path"
            )
        if not self.families:
            raise ValueError(
                f"family plugin {self.name} must declare at least one family"
            )
        observed: set[TargetFamily] = set()
        for entry in self.families:
            if entry.family in observed:
                raise ValueError(
                    f"family plugin {self.name} declares {entry.family.value} twice"
                )
            observed.add(entry.family)

    def entry_for(self, family: TargetFamily) -> FamilyPluginEntry:
        for entry in self.families:
            if entry.family is family:
                return entry
        raise KeyError(
            f"family plugin {self.name} does not declare {family.value}"
        )
