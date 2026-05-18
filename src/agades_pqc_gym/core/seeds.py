from __future__ import annotations

from agades_pqc_gym.core.attack_plan import (
    AttackOperator,
    AttackPlan,
    Claims,
    Constraints,
    Metadata,
)
from agades_pqc_gym.core.target import SupportLevel, TargetFamily, TargetSpec
from agades_pqc_gym.families.code_based.isd_estimator import (
    PRANGE_TOY_ASSUMPTION,
    PRANGE_TOY_VARIANT,
)
from agades_pqc_gym.families.hash_based.bound_estimator import (
    TOY_PREIMAGE_ASSUMPTION,
    TOY_PREIMAGE_BOUND_MODEL,
)
from agades_pqc_gym.families.implementation_security.kat_estimator import (
    TOY_KAT_ASSUMPTION,
    TOY_KAT_MODEL,
    TOY_KAT_SAMPLE_DIGEST,
    TOY_KAT_SAMPLE_PAYLOAD,
)
from agades_pqc_gym.families.isogeny_historical.path_estimator import (
    HISTORICAL_NOT_CURRENT_ASSUMPTION,
    TOY_ISOGENY_ASSUMPTION,
    TOY_ISOGENY_CASE,
)
from agades_pqc_gym.families.multivariate.mq_estimator import (
    TOY_MQ_ASSUMPTION,
    TOY_MQ_MODEL,
)


def seed_primal_plan(target: TargetSpec, attack_plan_id: str) -> AttackPlan:
    target_n = target.n or 1
    beta = max(32, min(80, target_n // 2))
    return AttackPlan(
        attack_plan_id=attack_plan_id,
        target=target,
        operators=[
            AttackOperator(
                type="primal_usvp",
                params={"beta": beta, "svp_cost_model": "ADPS16"},
                assumptions=["lattice_estimator_default_cost_model"],
            )
        ],
        constraints=Constraints(
            max_memory_bits=max(64.0, beta * 1.5),
            max_time_bits=max(96.0, target_n * 2.0),
            require_reproducibility_on_downscaled_instances=False,
        ),
        claims=Claims(),
        metadata=Metadata(
            created_by="benchmark_seed",
            public=True,
            notes="Generated seed plan for benchmark smoke evaluation.",
        ),
    )


def seed_plan_for_target(target: TargetSpec) -> AttackPlan:
    if target.family in {TargetFamily.LWE, TargetFamily.MLWE}:
        return seed_primal_plan(target, attack_plan_id=f"{target.name}_primal_seed")
    if (
        target.family is TargetFamily.CODE_BASED
        and target.support_level is SupportLevel.IMPLEMENTED
    ):
        return AttackPlan(
            attack_plan_id=f"{target.name}_prange_seed",
            target=target,
            operators=[
                AttackOperator(
                    type="information_set_decoding",
                    params={"variant": PRANGE_TOY_VARIANT},
                    assumptions=[PRANGE_TOY_ASSUMPTION],
                )
            ],
            constraints=Constraints(),
            claims=Claims(),
            metadata=Metadata(
                created_by="benchmark_seed",
                public=True,
                notes=(
                    "Generated toy Prange ISD seed for benchmark smoke "
                    "evaluation. Not a security claim."
                ),
            ),
        )
    if (
        target.family is TargetFamily.HASH_BASED
        and target.support_level is SupportLevel.IMPLEMENTED
    ):
        return AttackPlan(
            attack_plan_id=f"{target.name}_bound_seed",
            target=target,
            operators=[
                AttackOperator(
                    type="security_bound_check",
                    params={"bound_model": TOY_PREIMAGE_BOUND_MODEL},
                    assumptions=[TOY_PREIMAGE_ASSUMPTION],
                )
            ],
            constraints=Constraints(),
            claims=Claims(),
            metadata=Metadata(
                created_by="benchmark_seed",
                public=True,
                notes=(
                    "Generated toy hash-bound seed for benchmark smoke "
                    "evaluation. Not a security claim."
                ),
            ),
        )
    if (
        target.family is TargetFamily.MULTIVARIATE
        and target.support_level is SupportLevel.IMPLEMENTED
    ):
        return AttackPlan(
            attack_plan_id=f"{target.name}_mq_seed",
            target=target,
            operators=[
                AttackOperator(
                    type="groebner_basis",
                    params={"model": TOY_MQ_MODEL},
                    assumptions=[TOY_MQ_ASSUMPTION],
                )
            ],
            constraints=Constraints(),
            claims=Claims(),
            metadata=Metadata(
                created_by="benchmark_seed",
                public=True,
                notes=(
                    "Generated toy multivariate MQ seed for benchmark smoke "
                    "evaluation. Not a security claim."
                ),
            ),
        )
    if (
        target.family is TargetFamily.IMPLEMENTATION_SECURITY
        and target.support_level is SupportLevel.IMPLEMENTED
    ):
        return AttackPlan(
            attack_plan_id=f"{target.name}_kat_seed",
            target=target,
            operators=[
                AttackOperator(
                    type="kat_conformance",
                    params={
                        "suite": "toy_mlkem_kat",
                        "model": TOY_KAT_MODEL,
                        "payload": TOY_KAT_SAMPLE_PAYLOAD,
                        "expected_sha256": TOY_KAT_SAMPLE_DIGEST,
                        "vector_count": 2,
                    },
                    assumptions=[TOY_KAT_ASSUMPTION],
                )
            ],
            constraints=Constraints(),
            claims=Claims(),
            metadata=Metadata(
                created_by="benchmark_seed",
                public=True,
                notes=(
                    "Generated toy implementation-security KAT digest seed for "
                    "benchmark smoke evaluation. Not a security claim."
                ),
            ),
        )
    if (
        target.family is TargetFamily.ISOGENY_HISTORICAL
        and target.support_level is SupportLevel.IMPLEMENTED
    ):
        return AttackPlan(
            attack_plan_id=f"{target.name}_path_seed",
            target=target,
            operators=[
                AttackOperator(
                    type="historical_isogeny_reconstruction",
                    params={
                        "case": TOY_ISOGENY_CASE,
                        "walk_length": 8,
                        "branching_factor": 4,
                    },
                    assumptions=[
                        HISTORICAL_NOT_CURRENT_ASSUMPTION,
                        TOY_ISOGENY_ASSUMPTION,
                    ],
                )
            ],
            constraints=Constraints(),
            claims=Claims(),
            metadata=Metadata(
                created_by="benchmark_seed",
                public=True,
                notes=(
                    "Generated historical toy isogeny path seed for benchmark "
                    "smoke evaluation. Not a current-standard or security claim."
                ),
            ),
        )

    operator_type, params = {
        TargetFamily.CODE_BASED: (
            "information_set_decoding",
            {"variant": "stern_schema_placeholder"},
        ),
        TargetFamily.MULTIVARIATE: (
            "minrank_attack",
            {"model": "minrank_schema_placeholder"},
        ),
        TargetFamily.HASH_BASED: (
            "security_bound_check",
            {"bound_model": "generic_hash_bound_schema_placeholder"},
        ),
        TargetFamily.ISOGENY_HISTORICAL: (
            "historical_isogeny_reconstruction",
            {"case": "sidh_toy_schema_placeholder"},
        ),
        TargetFamily.IMPLEMENTATION_SECURITY: (
            "benchmark_harness",
            {"metric": "implementation_security_benchmark_schema_placeholder"},
        ),
    }[target.family]

    return AttackPlan(
        attack_plan_id=f"{target.name}_schema_placeholder_seed",
        target=target,
        operators=[
            AttackOperator(
                type=operator_type,
                params=params,
                assumptions=["schema_only_no_estimator"],
            )
        ],
        constraints=Constraints(),
        claims=Claims(),
        metadata=Metadata(
            created_by="benchmark_seed",
            public=True,
            notes="Schema-only placeholder seed. No cryptanalytic estimate.",
        ),
    )
