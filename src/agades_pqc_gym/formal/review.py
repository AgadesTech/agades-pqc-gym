from __future__ import annotations

from agades_pqc_gym.core.target import TargetFamily

FORMAL_METHODS_REVIEWER = "formal_methods_reviewer"
RELEASE_BOUNDARY_REVIEWER = "release_boundary_reviewer"
REVIEWER_ROLE_GROUPS = [
    "family_cryptography_reviewer",
    FORMAL_METHODS_REVIEWER,
    RELEASE_BOUNDARY_REVIEWER,
]
REVIEW_STATUSES = [
    "pending_review",
    "reviewed",
    "rejected",
]
FAMILY_REVIEWER_ROLE_IDS = {
    TargetFamily.LWE.value: "lattice_cryptographer",
    TargetFamily.MLWE.value: "lattice_cryptographer",
    TargetFamily.NTRU.value: "lattice_cryptographer",
    TargetFamily.SIS.value: "lattice_cryptographer",
    TargetFamily.CODE_BASED.value: "code_based_cryptographer",
    TargetFamily.MULTIVARIATE.value: "multivariate_cryptographer",
    TargetFamily.HASH_BASED.value: "hash_based_signature_reviewer",
    TargetFamily.ISOGENY_HISTORICAL.value: "isogeny_historical_reviewer",
    TargetFamily.IMPLEMENTATION_SECURITY.value: "implementation_security_reviewer",
}


def family_reviewer_role_id(family: TargetFamily) -> str:
    return FAMILY_REVIEWER_ROLE_IDS[family.value]


def required_reviewers_for_family(family: TargetFamily) -> list[str]:
    return [
        family_reviewer_role_id(family),
        FORMAL_METHODS_REVIEWER,
        RELEASE_BOUNDARY_REVIEWER,
    ]
