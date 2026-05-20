from __future__ import annotations

from dataclasses import dataclass

from agades_pqc_gym.core.family_adapter import FamilyAdapter
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.evaluators.base import EstimatorAdapter


@dataclass(frozen=True)
class FamilyRegistry:
    adapters: dict[TargetFamily, FamilyAdapter]

    def get(self, family: TargetFamily) -> FamilyAdapter:
        try:
            return self.adapters[family]
        except KeyError as exc:
            raise KeyError(f"no adapter registered for family {family.value}") from exc


def default_family_registry(
    *, lattice_estimator: EstimatorAdapter | None = None
) -> FamilyRegistry:
    from agades_pqc_gym.families.code_based.adapter import CodeBasedFamilyAdapter
    from agades_pqc_gym.families.hash_based.adapter import HashBasedFamilyAdapter
    from agades_pqc_gym.families.implementation_security.adapter import (
        ImplementationSecurityFamilyAdapter,
    )
    from agades_pqc_gym.families.isogeny_historical.adapter import (
        IsogenyHistoricalFamilyAdapter,
    )
    from agades_pqc_gym.families.lattice.adapter import LatticeFamilyAdapter
    from agades_pqc_gym.families.multivariate.adapter import (
        MultivariateFamilyAdapter,
    )

    lattice_lwe = LatticeFamilyAdapter(
        family=TargetFamily.LWE,
        estimator=lattice_estimator,
    )
    lattice_mlwe = LatticeFamilyAdapter(
        family=TargetFamily.MLWE,
        estimator=lattice_estimator,
    )
    return FamilyRegistry(
        adapters={
            TargetFamily.LWE: lattice_lwe,
            TargetFamily.MLWE: lattice_mlwe,
            TargetFamily.NTRU: LatticeFamilyAdapter(
                family=TargetFamily.NTRU,
                support_level="schema_only",
            ),
            TargetFamily.SIS: LatticeFamilyAdapter(
                family=TargetFamily.SIS,
                support_level="schema_only",
            ),
            TargetFamily.CODE_BASED: CodeBasedFamilyAdapter(),
            TargetFamily.MULTIVARIATE: MultivariateFamilyAdapter(),
            TargetFamily.HASH_BASED: HashBasedFamilyAdapter(),
            TargetFamily.ISOGENY_HISTORICAL: IsogenyHistoricalFamilyAdapter(),
            TargetFamily.IMPLEMENTATION_SECURITY: ImplementationSecurityFamilyAdapter(),
        }
    )
