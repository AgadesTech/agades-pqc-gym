from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.family_operator_catalog import (
    build_family_operator_catalog,
)

SOURCE_CATALOG_SCHEMA = "agades.pqc.source_catalog.v1"
SOURCE_CATALOG_VERIFICATION_SCHEMA = "agades.pqc.source_catalog_verification.v1"

ROOT = Path(__file__).resolve().parents[3]
_EXPECTED_FALSE_SAFETY_FLAGS = (
    "contains_private_traces",
    "arbitrary_code_execution",
    "live_targeting",
    "security_claim",
    "publishes_private_candidates",
)
_REQUIRED_SOURCE_FIELDS = (
    "id",
    "title",
    "url",
    "platform",
    "family",
    "kind",
    "current_use",
    "integration_status",
)
_REQUIRED_BOOL_SOURCE_FIELDS = (
    "requires_gpu",
    "public",
    "publishes_private_candidates",
    "review_required_before_claims",
)
_REQUIRED_SOURCE_IDS = {
    "agades-benchmark-source-contracts",
    "agades-family-plugin-manifest",
    "agades-family-registry-manifest",
    "agades-family-support-matrix",
    "agades-hf-collection",
    "agades-hf-dataset",
    "agades-hf-space",
    "agades-lattice-estimator-baseline-contracts",
    "agades-nvidia-accelerator",
    "agades-nvidia-publication-handoff",
    "agades-prime-environment",
    "agades-prime-publication-handoff",
    "agades-public-run-export",
    "agades-publication-manifest",
    "ctgrind",
    "dudect",
    "facebook-lwe-benchmarking",
    "facebook-tapas",
    "hf-post-quantum-crypto-en",
    "hf-post-quantum-crypto-fr",
    "hf-pqc-ssl-scans",
    "hf-sc2026-side-channel",
    "lattice-estimator",
    "liboqs",
    "nist-acvp",
    "nist-additional-signatures-round3",
    "nist-bike-round4-status",
    "nist-classic-mceliece-round4-status",
    "nist-fips-203",
    "nist-fips-205",
    "nist-hqc-selection",
    "nvidia-inception",
    "pq-code-package",
    "pqclean",
    "pqm4",
    "prime-autonanogpt-speedrun",
    "prime-autonomous-speedrunning-experiments",
    "prime-quickstart",
    "prime-rl",
    "prime-verifiers",
    "timecop-supercop",
}
_REQUIRED_PLATFORMS = {
    "github",
    "hugging_face",
    "nist",
    "nvidia",
    "prime_intellect",
}
_LOCAL_ARTIFACT_SOURCE_IDS = {
    "agades-benchmark-source-contracts",
    "agades-family-plugin-manifest",
    "agades-family-registry-manifest",
    "agades-family-support-matrix",
    "agades-hf-collection",
    "agades-hf-dataset",
    "agades-hf-space",
    "agades-lattice-estimator-baseline-contracts",
    "agades-nvidia-accelerator",
    "agades-nvidia-publication-handoff",
    "agades-prime-environment",
    "agades-prime-publication-handoff",
    "agades-public-run-export",
    "agades-publication-manifest",
}
_NON_LATTICE_TOY_EVALUATOR_LABEL_BY_VARIANT = {
    ("CODE_BASED", "bjmm_toy"): "code_based_bjmm_isd",
    ("CODE_BASED", "classic_mceliece_support_syndrome_toy"): (
        "code_based_classic_mceliece_support_syndrome"
    ),
    ("CODE_BASED", "classic_mceliece_syndrome_toy"): (
        "code_based_classic_mceliece_syndrome"
    ),
    ("CODE_BASED", "dumer_toy"): "code_based_dumer_isd",
    ("CODE_BASED", "hqc_circulant_erasure_toy"): (
        "code_based_hqc_circulant_erasure"
    ),
    ("CODE_BASED", "hqc_circulant_syndrome_toy"): (
        "code_based_hqc_circulant_syndrome"
    ),
    ("CODE_BASED", "hqc_erasure_syndrome_toy"): (
        "code_based_hqc_erasure_syndrome"
    ),
    ("CODE_BASED", "hqc_parity_check_toy"): "code_based_hqc_parity_check",
    ("CODE_BASED", "hqc_repetition_toy"): "code_based_hqc_repetition",
    ("CODE_BASED", "hqc_weighted_repetition_toy"): (
        "code_based_hqc_weighted_repetition"
    ),
    ("CODE_BASED", "lee_brickell_toy"): "code_based_lee_brickell_isd",
    ("CODE_BASED", "mdpc_bit_flip_toy"): "code_based_mdpc_bit_flip",
    ("CODE_BASED", "mdpc_black_gray_bit_flip_toy"): (
        "code_based_mdpc_black_gray_bit_flip"
    ),
    ("CODE_BASED", "mdpc_syndrome_weight_bit_flip_toy"): (
        "code_based_mdpc_syndrome_weight_bit_flip"
    ),
    ("CODE_BASED", "prange_toy"): "code_based_prange_isd",
    ("CODE_BASED", "qc_rotation_toy"): "code_based_qc_rotation",
    ("CODE_BASED", "stern_toy"): "code_based_stern_isd",
    ("HASH_BASED", "toy_collision_bound"): "hash_based_collision_bound",
    ("HASH_BASED", "toy_fors_auth_path_verify"): (
        "hash_based_fors_auth_path_verify"
    ),
    ("HASH_BASED", "toy_hash_reused_salt"): "hash_based_misuse_reused_salt",
    ("HASH_BASED", "toy_merkle_auth_path_verify"): (
        "hash_based_merkle_auth_path_verify"
    ),
    ("HASH_BASED", "toy_preimage_bound"): "hash_based_preimage_bound",
    ("HASH_BASED", "toy_slh_dsa_hypertree_verify"): (
        "hash_based_slh_dsa_hypertree_verify"
    ),
    ("HASH_BASED", "toy_wots_chain_verify"): "hash_based_wots_chain_verify",
    ("IMPLEMENTATION_SECURITY", "toy_acvp_vector_set_match"): (
        "implementation_security_acvp_vector_set"
    ),
    ("IMPLEMENTATION_SECURITY", "toy_benchmark_summary_check"): (
        "implementation_security_benchmark_summary"
    ),
    ("IMPLEMENTATION_SECURITY", "toy_binary_size_check"): (
        "implementation_security_binary_size"
    ),
    ("IMPLEMENTATION_SECURITY", "toy_ctgrind_secret_taint_summary_check"): (
        "implementation_security_ctgrind_secret_taint"
    ),
    ("IMPLEMENTATION_SECURITY", "toy_dudect_summary_threshold_check"): (
        "implementation_security_dudect_summary"
    ),
    ("IMPLEMENTATION_SECURITY", "toy_kat_digest_match"): (
        "implementation_security_kat_digest"
    ),
    ("IMPLEMENTATION_SECURITY", "toy_memory_footprint_check"): (
        "implementation_security_memory_footprint"
    ),
    ("IMPLEMENTATION_SECURITY", "toy_stack_usage_check"): (
        "implementation_security_stack_usage"
    ),
    ("IMPLEMENTATION_SECURITY", "toy_timing_welch_t_check"): (
        "implementation_security_timing_check"
    ),
    ("ISOGENY_HISTORICAL", "toy_commutative_walk_search"): (
        "isogeny_historical_commutative_walk"
    ),
    ("ISOGENY_HISTORICAL", "toy_sidh_path_search"): (
        "isogeny_historical_sidh_path"
    ),
    ("ISOGENY_HISTORICAL", "toy_volcano_walk_search"): (
        "isogeny_historical_volcano_walk"
    ),
    ("MULTIVARIATE", "toy_minrank_search"): "multivariate_minrank_search",
    ("MULTIVARIATE", "toy_mq_degree_bound"): (
        "multivariate_mq_degree_bound"
    ),
    ("MULTIVARIATE", "toy_mq_hybrid_search"): "multivariate_mq_hybrid_search",
    ("MULTIVARIATE", "toy_mq_search"): "multivariate_mq_search",
    ("MULTIVARIATE", "toy_uov_public_map_verify"): (
        "multivariate_uov_public_map_verify"
    ),
}


def _non_lattice_toy_evaluator_labels() -> list[str]:
    labels: list[str] = []
    missing_keys: list[str] = []
    for entry in _non_lattice_toy_operator_variants():
        key = (entry["family"], entry["variant"])
        label = _NON_LATTICE_TOY_EVALUATOR_LABEL_BY_VARIANT.get(key)
        if label is None:
            missing_keys.append(f"{key[0]}:{key[1]}")
            continue
        labels.append(label)
    if missing_keys:
        raise RuntimeError(
            "Missing source catalog toy evaluator labels for "
            f"{', '.join(sorted(missing_keys))}."
        )
    return sorted(labels)


def _non_lattice_toy_operator_variants() -> list[dict[str, Any]]:
    operator_catalog = build_family_operator_catalog()
    return [
        {
            "default_estimator": operator["default_estimator"],
            "family": family["family"],
            "operator_type": operator["operator_type"],
            "plugin": family["plugin"],
            "review_gate": operator["review_gate"],
            "security_claim": operator["security_claim"],
            "variant": operator["variant"],
        }
        for family in operator_catalog["families"]
        if family["support_level"] == "toy_evaluator"
        for operator in family["operators"]
        if operator["support_status"] == "implemented_toy"
    ]


def build_source_catalog() -> dict[str, Any]:
    catalog = {
        "schema_version": SOURCE_CATALOG_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
            "cli": "agades-pqc",
        },
        "scope": {
            "current_public_runtime": "typed-attackplan-verifier",
            "first_executable_family": "lattice",
            "non_lattice_toy_evaluators": _non_lattice_toy_evaluator_labels(),
            "non_lattice_toy_operator_variants": (
                _non_lattice_toy_operator_variants()
            ),
            "future_family_surfaces": [],
        },
        "sources": [
            {
                "id": "lattice-estimator",
                "title": "Lattice Estimator",
                "url": "https://github.com/malb/lattice-estimator",
                "platform": "github",
                "family": "lattice",
                "kind": "estimator",
                "current_use": "optional_lattice_estimator",
                "integration_status": "current_reviewed_boundary",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Used only for reviewed lattice-family mappings.",
                    "Not a universal PQC oracle.",
                ],
            },
            {
                "id": "facebook-tapas",
                "title": (
                    "TAPAS: Datasets for Learning the Learning with Errors Problem"
                ),
                "url": "https://huggingface.co/datasets/facebook/TAPAS",
                "platform": "hugging_face",
                "family": "lattice",
                "kind": "dataset",
                "current_use": "public_future_reproduction_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Large public LWE dataset for future reproduction ladders.",
                    "No benchmark claim should be made until mappings and storage "
                    "requirements are reviewed.",
                ],
            },
            {
                "id": "facebook-lwe-benchmarking",
                "title": "Benchmarking Attacks on Learning with Errors",
                "url": "https://github.com/facebookresearch/LWE-benchmarking",
                "platform": "github",
                "family": "lattice",
                "kind": "benchmark_harness",
                "current_use": "public_future_reproduction_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": True,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Future adapter must isolate heavyweight GPU/Sage workflows "
                    "from the current lightweight verifier.",
                    "Results must be reported as public benchmark reproduction, "
                    "not as deployed-standard break claims.",
                ],
            },
            {
                "id": "hf-post-quantum-crypto-fr",
                "title": "AYI-NEDJIMI post-quantum crypto FR dataset",
                "url": (
                    "https://huggingface.co/datasets/"
                    "AYI-NEDJIMI/post-quantum-crypto-fr"
                ),
                "platform": "hugging_face",
                "family": "all",
                "kind": "instruction_seed_dataset",
                "current_use": "future_pqc_instruction_eval_seed",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Small French Q&A/classification seed dataset for PQC "
                    "migration and standards topics.",
                    "Useful for future evaluator-facing documentation checks "
                    "or instruction-eval seeds, not as a complete PQC corpus.",
                    "Must be source-verified before any generated answer or "
                    "training claim is published.",
                ],
            },
            {
                "id": "hf-post-quantum-crypto-en",
                "title": "AYI-NEDJIMI post-quantum crypto EN dataset",
                "url": (
                    "https://huggingface.co/datasets/"
                    "AYI-NEDJIMI/post-quantum-crypto-en"
                ),
                "platform": "hugging_face",
                "family": "all",
                "kind": "instruction_seed_dataset",
                "current_use": "future_pqc_instruction_eval_seed",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Small English Q&A/classification seed dataset for PQC "
                    "migration and standards topics.",
                    "Useful for future evaluator-facing documentation checks "
                    "or instruction-eval seeds, not as a complete PQC corpus.",
                    "Must be source-verified before any generated answer or "
                    "training claim is published.",
                ],
            },
            {
                "id": "hf-pqc-ssl-scans",
                "title": "Q-GRID PQC SSL scan dataset",
                "url": "https://huggingface.co/datasets/Q-GRID/pqc-ssl-scans",
                "platform": "hugging_face",
                "family": "all",
                "kind": "migration_scoring_dataset",
                "current_use": "future_pqc_migration_scoring_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Small tabular SSL/TLS scan dataset for PQC migration "
                    "prioritization and compliance-scoring experiments.",
                    "Not a cryptanalysis dataset and not used by the current "
                    "AttackPlan verifier.",
                    "Future use must keep scoring methodology, domain sampling, "
                    "and claim boundaries explicit.",
                ],
            },
            {
                "id": "hf-sc2026-side-channel",
                "title": "SCA-HNUST SC2026 far-field side-channel dataset",
                "url": "https://huggingface.co/datasets/SCA-HNUST/SC2026",
                "platform": "hugging_face",
                "family": "implementation_security",
                "kind": "side_channel_dataset",
                "current_use": "future_side_channel_research_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": True,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Public far-field EM side-channel dataset with a "
                    "CRYSTALS-Kyber subset for future implementation-security "
                    "research planning.",
                    "Not invoked by the current JSON-only public verifier and "
                    "not a conformance, side-channel-resistance, or security "
                    "claim.",
                    "Future adapters must define trace provenance, leakage "
                    "model, hardware scope, and disclosure boundaries before "
                    "publication.",
                ],
            },
            {
                "id": "nist-hqc-selection",
                "title": "NIST HQC fourth-round selection",
                "url": (
                    "https://csrc.nist.gov/News/2025/"
                    "hqc-announced-as-a-4th-round-selection"
                ),
                "platform": "nist",
                "family": "code_based",
                "kind": "standardization_selection",
                "current_use": "future_code_based_standardization_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "HQC was selected for standardization after NIST PQC "
                    "fourth-round evaluation.",
                    "Agades code-based toy evaluators are not HQC security "
                    "evaluators.",
                    "Any HQC adapter requires reviewed parameter, decoder, "
                    "test-vector, and claim-boundary mappings.",
                ],
            },
            {
                "id": "nist-bike-round4-status",
                "title": "NIST BIKE fourth-round status",
                "url": "https://csrc.nist.gov/pubs/ir/8545/final",
                "platform": "nist",
                "family": "code_based",
                "kind": "standardization_status",
                "current_use": "future_code_based_nonselected_candidate_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "BIKE was studied in NIST PQC round four but was not "
                    "selected for standardization in NIST IR 8545.",
                    "Agades BIKE-like examples are schema-only routing "
                    "fixtures, not BIKE security estimators.",
                    "Any future BIKE adapter requires reviewed parameter, "
                    "decoder, failure-rate, and claim-boundary mappings.",
                ],
            },
            {
                "id": "nist-classic-mceliece-round4-status",
                "title": "NIST Classic McEliece fourth-round status",
                "url": "https://csrc.nist.gov/pubs/ir/8545/final",
                "platform": "nist",
                "family": "code_based",
                "kind": "standardization_status",
                "current_use": "future_code_based_nonselected_candidate_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Classic McEliece was studied in NIST PQC round four but "
                    "was not selected for standardization in NIST IR 8545.",
                    "Agades Classic-McEliece-inspired public fixtures are "
                    "bounded toy verifier plumbing; schema-only "
                    "Classic-McEliece-like placeholders still route "
                    "unsupported, and none are Classic McEliece security "
                    "estimators.",
                    "Any future Classic McEliece adapter requires reviewed "
                    "parameter, decoding-workfactor, KAT provenance, and "
                    "claim-boundary mappings.",
                ],
            },
            {
                "id": "nist-fips-205",
                "title": "NIST FIPS 205 SLH-DSA",
                "url": "https://csrc.nist.gov/pubs/fips/205/final",
                "platform": "nist",
                "family": "hash_based",
                "kind": "standard",
                "current_use": "future_hash_based_standard_anchor",
                "integration_status": "public_reference",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Used as a public standards anchor for SLH-DSA only.",
                    "The current hash-based toy WOTS-chain verifier is not an "
                    "SLH-DSA implementation, proof, or security claim.",
                    "Future SLH-DSA adapters require parameter-set and vector "
                    "provenance review.",
                ],
            },
            {
                "id": "nist-additional-signatures-round3",
                "title": (
                    "NIST additional PQC digital signatures third-round "
                    "selection"
                ),
                "url": (
                    "https://csrc.nist.gov/News/2026/"
                    "nist-advances-9-candidates-to-the-3rd-round-of-pqc"
                ),
                "platform": "nist",
                "family": "multivariate",
                "kind": "standardization_process",
                "current_use": "future_multivariate_signature_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "MAYO, QR-UOV, and UOV are relevant multivariate "
                    "third-round candidates in the NIST additional-signature "
                    "process.",
                    "Agades MQ, MinRank, and UOV-inspired public-map toy "
                    "evaluators are not candidate security estimators.",
                    "Future adapters require reviewed public-parameter, "
                    "algebraic-attack-model, and implementation-source pins.",
                ],
            },
            {
                "id": "pqclean",
                "title": "PQClean",
                "url": "https://github.com/PQClean/PQClean",
                "platform": "github",
                "family": "implementation_security",
                "kind": "implementation_corpus",
                "current_use": "future_implementation_security_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Useful as a public implementation corpus and testing anchor.",
                    "The current MVP only verifies toy JSON digest and timing "
                    "summaries.",
                    "No real implementation-security score is produced by the MVP.",
                ],
            },
            {
                "id": "pq-code-package",
                "title": "PQ Code Package",
                "url": "https://github.com/pq-code-package",
                "platform": "github",
                "family": "implementation_security",
                "kind": "high_assurance_implementation_corpus",
                "current_use": (
                    "future_high_assurance_implementation_security_anchor"
                ),
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Public high-assurance implementation anchor for ML-KEM "
                    "and ML-DSA native code.",
                    "Relevant repositories include mlkem-native and "
                    "mldsa-native.",
                    "Future adapters must pin source revisions, ACVP vector "
                    "releases, toolchains, and constant-time test scope before "
                    "any public result.",
                    "Not invoked by the current JSON-only public verifier.",
                ],
            },
            {
                "id": "liboqs",
                "title": "Open Quantum Safe liboqs",
                "url": "https://github.com/open-quantum-safe/liboqs",
                "platform": "github",
                "family": "implementation_security",
                "kind": "implementation_test_harness",
                "current_use": "future_implementation_security_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Candidate anchor for future KAT, API, benchmark, and "
                    "implementation-security gates.",
                    "Not invoked by the current public verifier.",
                ],
            },
            {
                "id": "pqm4",
                "title": "pqm4 ARM Cortex-M4 PQC benchmarks",
                "url": "https://github.com/mupq/pqm4",
                "platform": "github",
                "family": "implementation_security",
                "kind": "embedded_benchmark_harness",
                "current_use": "future_embedded_implementation_security_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Candidate anchor for future Cortex-M4 KAT, speed, stack, "
                    "and code-size benchmarks.",
                    "Requires isolated device/simulator protocol before any "
                    "public result.",
                    "Not invoked by the current public verifier.",
                ],
            },
            {
                "id": "nist-acvp",
                "title": "NIST Automated Cryptographic Validation Protocol",
                "url": "https://github.com/usnistgov/ACVP",
                "platform": "nist",
                "family": "implementation_security",
                "kind": "validation_protocol",
                "current_use": "future_kat_validation_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Candidate anchor for future ML-KEM, ML-DSA, and SLH-DSA "
                    "KAT/validation vector workflows.",
                    "Requires vector provenance and algorithm revision pinning "
                    "before publication.",
                    "No ACVP server interaction is performed by the current "
                    "public verifier.",
                ],
            },
            {
                "id": "dudect",
                "title": "dudect statistical constant-time tester",
                "url": "https://github.com/oreparaz/dudect",
                "platform": "github",
                "family": "implementation_security",
                "kind": "statistical_timing_leakage_tool",
                "current_use": "future_constant_time_leakage_test_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Candidate anchor for future Welch t-test timing leakage "
                    "experiments over pinned public implementations.",
                    "Statistical timing output is not a constant-time proof.",
                    "Not executed by the current public verifier or Prime "
                    "JSON-only reward environment.",
                ],
            },
            {
                "id": "ctgrind",
                "title": "ctgrind Valgrind secret-taint checker",
                "url": "https://github.com/agl/ctgrind",
                "platform": "github",
                "family": "implementation_security",
                "kind": "dynamic_secret_taint_tool",
                "current_use": "future_secret_taint_analysis_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Candidate anchor for future secret-dependent branch and "
                    "memory-access dynamic checks.",
                    "Requires reviewed Valgrind/toolchain support before any "
                    "public result.",
                    "Not executed by the current public verifier.",
                ],
            },
            {
                "id": "timecop-supercop",
                "title": "TIMECOP inside SUPERCOP",
                "url": "https://bench.cr.yp.to/supercop.html",
                "platform": "ebacs",
                "family": "implementation_security",
                "kind": "supercop_constant_time_tool",
                "current_use": "future_supercop_timecop_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Candidate anchor for future TIMECOP/SUPERCOP "
                    "constant-time policy checks over pinned implementations.",
                    "Requires reviewed SUPERCOP source, toolchain, CPU, and "
                    "result provenance before publication.",
                    "Not executed by the current public verifier or Prime "
                    "JSON-only reward environment.",
                ],
            },
            {
                "id": "nist-fips-203",
                "title": "NIST FIPS 203 ML-KEM",
                "url": "https://csrc.nist.gov/pubs/fips/203/final",
                "platform": "nist",
                "family": "lattice",
                "kind": "standard",
                "current_use": "parameter_reference_anchor",
                "integration_status": "public_reference",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Used as a public standards anchor only.",
                    "The MVP does not claim attacks on standardized ML-KEM.",
                ],
            },
            {
                "id": "prime-verifiers",
                "title": "Prime Intellect Verifiers",
                "url": "https://github.com/PrimeIntellect-ai/verifiers",
                "platform": "prime_intellect",
                "family": "all",
                "kind": "agent_evaluation_environment",
                "current_use": "current_verifier_packaging",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Agades packages JSON-only AttackPlan scoring for this surface.",
                    "The environment does not execute model-submitted code.",
                ],
            },
            {
                "id": "prime-quickstart",
                "title": "Prime Intellect quickstart",
                "url": "https://app.primeintellect.ai/dashboard/home/quickstart",
                "platform": "prime_intellect",
                "family": "all",
                "kind": "developer_onboarding",
                "current_use": "current_operator_onboarding_reference",
                "integration_status": "source_map_only",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Reference for CLI and workspace onboarding only.",
                    "Prime credentials, billing, and hosted-job launches stay "
                    "outside committed public artifacts.",
                ],
            },
            {
                "id": "prime-rl",
                "title": "Prime RL",
                "url": "https://github.com/PrimeIntellect-ai/prime-rl",
                "platform": "prime_intellect",
                "family": "all",
                "kind": "agentic_rl_framework",
                "current_use": "future_agentic_rl_training_anchor",
                "integration_status": "future_reviewed_adapter",
                "requires_gpu": True,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Future anchor for agentic RL training over reviewed "
                    "AttackPlan verifier tasks.",
                    "The current release packages a JSON-only verifier "
                    "environment, not a Prime RL training run.",
                    "No model-submitted code or private evolution traces are "
                    "published through this surface.",
                ],
            },
            {
                "id": "prime-autonanogpt-speedrun",
                "title": "Prime Intellect auto-nanoGPT speedrun",
                "url": "https://www.primeintellect.ai/auto-nanogpt",
                "platform": "prime_intellect",
                "family": "all",
                "kind": "ecosystem_pattern",
                "current_use": "public_benchmark_story_anchor",
                "integration_status": "source_map_only",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Inspiration for public, observable evaluator-led runs.",
                    "Agades does not publish private evolution traces.",
                ],
            },
            {
                "id": "prime-autonomous-speedrunning-experiments",
                "title": "Prime Intellect autonomous speedrunning experiments",
                "url": (
                    "https://github.com/PrimeIntellect-ai/"
                    "experiments-autonomous-speedrunning"
                ),
                "platform": "prime_intellect",
                "family": "all",
                "kind": "ecosystem_pattern",
                "current_use": "public_evaluator_observability_pattern",
                "integration_status": "source_map_only",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Reference pattern for observable evaluator-led runs.",
                    "Agades public artifacts keep private evolution traces out "
                    "of the release surface.",
                ],
            },
            {
                "id": "agades-hf-dataset",
                "title": "Agades PQC Gym toy dataset bundle",
                "url": "hf/dataset",
                "platform": "hugging_face",
                "family": "all",
                "kind": "local_dataset_bundle",
                "current_use": "current_public_artifact",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Contains only toy/schema-only AttackPlans and verifier output.",
                    "No private traces or unpublished candidate strategies.",
                ],
            },
            {
                "id": "agades-hf-space",
                "title": "Agades PQC Gym Hugging Face Space manifest",
                "url": "hf/space_manifest.json",
                "platform": "hugging_face",
                "family": "all",
                "kind": "local_space_manifest",
                "current_use": "current_public_gradio_space_contract",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Documents the public Gradio Space selector and shared verifier.",
                    "Keeps Space publication behind review and no-claim guardrails.",
                ],
            },
            {
                "id": "agades-hf-collection",
                "title": "Agades PQC Gym Hugging Face Collection manifest",
                "url": "hf/collection_manifest.json",
                "platform": "hugging_face",
                "family": "all",
                "kind": "local_collection_manifest",
                "current_use": "current_public_collection_contract",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Groups the GitHub repo, toy dataset, Space, benchmark card, "
                    "source map, and public benchmark manifest for review.",
                    "Does not publish private evolution traces or security claims.",
                ],
            },
            {
                "id": "agades-lattice-estimator-baseline-contracts",
                "title": "Agades PQC Gym Lattice Estimator baseline contracts",
                "url": "docs/lattice_estimator_baseline_contracts.json",
                "platform": "github",
                "family": "lattice",
                "kind": "local_lattice_baseline_contract",
                "current_use": (
                    "current_lattice_estimator_baseline_reproduction_contract"
                ),
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Review-ready contracts for direct LWE Lattice Estimator mappings.",
                    "This is not a numeric baseline reproduction.",
                    "Numeric outputs, publication, and security claims remain blocked "
                    "until expert review.",
                ],
            },
            {
                "id": "agades-prime-environment",
                "title": "Agades PQC Gym Prime environment manifest",
                "url": "prime_intellect/verifiers_environment/prime_manifest.json",
                "platform": "prime_intellect",
                "family": "all",
                "kind": "local_prime_environment_manifest",
                "current_use": "current_public_verifier_environment_contract",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Documents packaged Prime task rows, reward boundaries, "
                    "and JSON-only scoring.",
                    "Keeps Prime Hub publication behind credentials and "
                    "release review.",
                ],
            },
            {
                "id": "agades-prime-publication-handoff",
                "title": "Agades PQC Gym Prime publication handoff manifest",
                "url": "docs/prime_publication_handoff.json",
                "platform": "prime_intellect",
                "family": "all",
                "kind": "local_publication_handoff_manifest",
                "current_use": "current_prime_publication_review_handoff",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Records local Prime package readiness and review gates.",
                    "Does not claim Prime Hub publication or credential presence.",
                    "Keeps external Prime publication behind release and "
                    "credential review.",
                ],
            },
            {
                "id": "agades-public-run-export",
                "title": "Agades PQC Gym public run export",
                "url": "public/run_export/manifest.json",
                "platform": "prime_intellect",
                "family": "all",
                "kind": "local_public_run_export",
                "current_use": "current_flat_public_run_review_surface",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Flattens checked-in public run ledgers into deterministic "
                    "JSONL and CSV rows for Prime-style autonomous run review.",
                    "Contains only toy and downscaled public verifier bundles.",
                    "No private evolution traces, private candidates, live "
                    "targets, or security claims are published through this "
                    "surface.",
                ],
            },
            {
                "id": "agades-nvidia-accelerator",
                "title": "Agades PQC Gym NVIDIA accelerator manifest",
                "url": "nvidia/accelerator_manifest.json",
                "platform": "nvidia",
                "family": "all",
                "kind": "local_accelerator_manifest",
                "current_use": "current_public_accelerator_contract",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Documents CPU-only current workloads and reserved future "
                    "GPU boundaries.",
                    "Does not claim current GPU acceleration or security "
                    "results.",
                ],
            },
            {
                "id": "agades-nvidia-publication-handoff",
                "title": "Agades PQC Gym NVIDIA publication handoff manifest",
                "url": "docs/nvidia_publication_handoff.json",
                "platform": "nvidia",
                "family": "all",
                "kind": "local_publication_handoff_manifest",
                "current_use": "current_nvidia_publication_review_handoff",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Records local NVIDIA review packet readiness and "
                    "artifact digests.",
                    "Does not claim external NVIDIA submission, GPU execution, "
                    "GPU results, credential presence, or security results.",
                    "Keeps external NVIDIA-facing use behind release review.",
                ],
            },
            {
                "id": "agades-family-registry-manifest",
                "title": "Agades PQC Gym family registry manifest",
                "url": "docs/family_registry_manifest.json",
                "platform": "github",
                "family": "all",
                "kind": "local_runtime_registry_manifest",
                "current_use": "current_runtime_family_registry_contract",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Machine-readable runtime adapter registry for every "
                    "TargetFamily.",
                    "Cross-checks adapter class, plugin, support matrix, "
                    "operator catalog, and Lattice Estimator boundaries.",
                    "Only LWE may expose the external Lattice Estimator route.",
                ],
            },
            {
                "id": "agades-family-plugin-manifest",
                "title": "Agades PQC Gym family plugin descriptor manifest",
                "url": "docs/family_plugin_manifest.json",
                "platform": "github",
                "family": "all",
                "kind": "local_family_plugin_manifest",
                "current_use": "current_family_plugin_descriptor_contract",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Machine-readable plugin descriptor contract for every "
                    "family plugin.",
                    "Records plugin-owned adapter and applicability validator "
                    "paths.",
                    "Keeps non-lattice plugins separate from the lattice "
                    "validator and Lattice Estimator boundary.",
                ],
            },
            {
                "id": "agades-family-support-matrix",
                "title": "Agades PQC Gym family support matrix",
                "url": "docs/family_support_matrix.json",
                "platform": "github",
                "family": "all",
                "kind": "local_support_manifest",
                "current_use": "current_public_artifact",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Machine-readable support boundary for every target family.",
                    "Marks LWE/MLWE as implemented and non-lattice executable "
                    "families only as bounded toy evaluator surfaces.",
                ],
            },
            {
                "id": "agades-publication-manifest",
                "title": "Agades PQC Gym OSS publication readiness manifest",
                "url": "docs/publication_manifest.json",
                "platform": "github",
                "family": "all",
                "kind": "local_publication_contract",
                "current_use": "current_release_readiness_contract",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Maps GitHub, Hugging Face, Prime, and NVIDIA release surfaces.",
                    "Keeps external publication credential and review boundaries "
                    "explicit.",
                ],
            },
            {
                "id": "agades-benchmark-source-contracts",
                "title": "Agades PQC Gym benchmark source contracts",
                "url": "docs/benchmark_source_contracts.json",
                "platform": "github",
                "family": "all",
                "kind": "local_future_adapter_contract",
                "current_use": "current_future_adapter_contract",
                "integration_status": "current_public_surface",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Machine-readable TAPAS, LWE-benchmarking, HQC, BIKE, "
                    "Classic McEliece, SLH-DSA, multivariate "
                    "additional-signature, HF PQC/SCA dataset, PQ Code "
                    "Package, liboqs, pqm4, and NIST ACVP boundaries.",
                    "Keeps heavyweight and future family adapters review-gated "
                    "and out of the JSON-only public verifier.",
                ],
            },
            {
                "id": "nvidia-inception",
                "title": "NVIDIA Inception",
                "url": "https://www.nvidia.com/en-us/startups/",
                "platform": "nvidia",
                "family": "all",
                "kind": "startup_ecosystem",
                "current_use": "accelerator_strategy_anchor",
                "integration_status": "source_map_only",
                "requires_gpu": False,
                "public": True,
                "publishes_private_candidates": False,
                "review_required_before_claims": True,
                "safety_notes": [
                    "Public positioning anchor for evaluator and future GPU work.",
                    "No GPU workload is claimed in the current MVP.",
                ],
            },
        ],
        "private_holdback": [
            "serious evolution traces",
            "private prompts and prompt-ranking policies",
            "evaluator weighting and anti-gaming heuristics",
            "unreleased candidate strategies",
            "responsible-disclosure material",
        ],
        "safety": {
            "contains_private_traces": False,
            "arbitrary_code_execution": False,
            "live_targeting": False,
            "security_claim": False,
            "publishes_private_candidates": False,
        },
        "release_gates": [
            "uv run pytest tests/test_source_catalog.py -q",
            "uv run agades-pqc source-catalog --out docs/source_catalog.json",
            "uv run agades-pqc source-catalog-verify --catalog "
            "docs/source_catalog.json",
            "uv run agades-pqc public-run-export --out public/run_export",
            "uv run agades-pqc public-run-export-verify --export public/run_export",
            "uv run agades-pqc family-registry-manifest --out "
            "docs/family_registry_manifest.json",
            "uv run agades-pqc family-registry-manifest-verify --manifest "
            "docs/family_registry_manifest.json",
            "uv run agades-pqc family-plugin-manifest --out "
            "docs/family_plugin_manifest.json",
            "uv run agades-pqc family-plugin-manifest-verify --manifest "
            "docs/family_plugin_manifest.json",
            "uv run agades-pqc family-support --out docs/family_support_matrix.json",
            "uv run agades-pqc family-support-verify --matrix "
            "docs/family_support_matrix.json",
            "uv run agades-pqc prime-publication-handoff --out "
            "docs/prime_publication_handoff.json",
            "uv run agades-pqc prime-publication-handoff-verify --handoff "
            "docs/prime_publication_handoff.json",
        ],
    }
    catalog["summary"] = summarize_source_catalog(catalog)
    return catalog


def write_source_catalog(out: Path) -> dict[str, Any]:
    catalog = build_source_catalog()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(catalog, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return catalog


def summarize_source_catalog_scope(catalog: dict[str, Any]) -> dict[str, Any]:
    summary = _scope_summary(catalog)
    sources = catalog.get("sources")
    summary["source_count"] = len(sources) if isinstance(sources, list) else 0
    return summary


def summarize_source_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    sources = catalog.get("sources")
    if not isinstance(sources, list):
        sources = []
    by_id = {
        source["id"]: source
        for source in sources
        if isinstance(source, dict)
        and isinstance(source.get("id"), str)
        and source["id"]
    }
    summary = _summarize_sources_by_id(by_id, len(sources))
    summary.update(_scope_summary(catalog))
    return summary


def verify_source_catalog(
    path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    failures: list[str] = []
    catalog = _read_source_catalog(path, failures)

    if catalog.get("schema_version") != SOURCE_CATALOG_SCHEMA:
        failures.append(f"manifest: schema_version must be {SOURCE_CATALOG_SCHEMA}.")

    _verify_catalog_safety(catalog, failures)
    _verify_scope(catalog, failures)

    sources = catalog.get("sources")
    if not isinstance(sources, list):
        failures.append("manifest: sources must be a list.")
        sources = []

    summary = _verify_sources(sources, project_root, failures)
    summary.update(_scope_summary(catalog))
    stored_summary = catalog.get("summary")
    if not failures and stored_summary != summary:
        failures.append(
            "manifest: summary is inconsistent with source entries and scope."
        )
    if not failures and catalog != build_source_catalog():
        failures.append(
            "manifest: contents are not synchronized with the current runtime "
            "source catalog."
        )
    summary["failure_count"] = len(failures)

    return {
        "schema_version": SOURCE_CATALOG_VERIFICATION_SCHEMA,
        "catalog_path": str(path),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _read_source_catalog(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"manifest: missing file {path}.")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"manifest: invalid JSON at line {exc.lineno}.")
        return {}

    if not isinstance(payload, dict):
        failures.append("manifest: top-level JSON value must be an object.")
        return {}
    return payload


def _verify_catalog_safety(catalog: dict[str, Any], failures: list[str]) -> None:
    safety = catalog.get("safety")
    if not isinstance(safety, dict):
        failures.append("manifest: safety must be an object.")
        return

    for flag in _EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            failures.append(f"manifest: safety.{flag} must be false.")


def _verify_scope(catalog: dict[str, Any], failures: list[str]) -> None:
    scope = catalog.get("scope")
    if not isinstance(scope, dict):
        failures.append("manifest: scope must be an object.")
        return
    if scope.get("non_lattice_toy_evaluators") != (
        _non_lattice_toy_evaluator_labels()
    ):
        failures.append("manifest: non_lattice_toy_evaluators drifted.")
    if scope.get("non_lattice_toy_operator_variants") != (
        _non_lattice_toy_operator_variants()
    ):
        failures.append("manifest: non_lattice_toy_operator_variants drifted.")


def _scope_summary(catalog: dict[str, Any]) -> dict[str, Any]:
    scope = catalog.get("scope")
    if not isinstance(scope, dict):
        scope = {}
    toy_evaluators = scope.get("non_lattice_toy_evaluators")
    if not isinstance(toy_evaluators, list):
        toy_evaluators = []
    operator_variants = scope.get("non_lattice_toy_operator_variants")
    if not isinstance(operator_variants, list):
        operator_variants = []
    operator_entries = [
        entry for entry in operator_variants if isinstance(entry, dict)
    ]
    return {
        "non_lattice_toy_evaluator_count": len(toy_evaluators),
        "non_lattice_toy_operator_families": sorted(
            family
            for family in {entry.get("family") for entry in operator_entries}
            if isinstance(family, str)
        ),
        "non_lattice_toy_operator_security_claims": sum(
            1 for entry in operator_entries if entry.get("security_claim") is True
        ),
        "non_lattice_toy_operator_variant_count": len(operator_entries),
    }


def _verify_sources(
    sources: list[Any],
    root: Path,
    failures: list[str],
) -> dict[str, Any]:
    by_id: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            failures.append(f"source[{index}]: source entry must be an object.")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id:
            failures.append(f"source[{index}]: id must be a non-empty string.")
            continue
        if source_id in by_id:
            failures.append(f"{source_id}: duplicate source entry.")
            continue
        by_id[source_id] = source

    for missing in sorted(_REQUIRED_SOURCE_IDS - set(by_id)):
        failures.append(f"{missing}: missing required source entry.")

    for source_id, source in by_id.items():
        _verify_source_entry(source, source_id, root, failures)

    platforms = sorted(
        platform
        for platform in {source.get("platform") for source in by_id.values()}
        if isinstance(platform, str)
    )
    for missing_platform in sorted(_REQUIRED_PLATFORMS - set(platforms)):
        failures.append(f"manifest: missing platform {missing_platform}.")

    return _summarize_sources_by_id(by_id, len(sources))


def _summarize_sources_by_id(
    by_id: dict[str, dict[str, Any]],
    source_count: int,
) -> dict[str, Any]:
    current_public_surfaces = _sources_by_status(by_id, "current_public_surface")
    future_reviewed_adapters = _sources_by_status(by_id, "future_reviewed_adapter")
    source_map_only = _sources_by_status(by_id, "source_map_only")
    platform_counts = {
        platform: sum(
            1 for source in by_id.values() if source.get("platform") == platform
        )
        for platform in sorted(
            platform
            for platform in {source.get("platform") for source in by_id.values()}
            if isinstance(platform, str)
        )
    }
    return {
        "current_public_surface_count": len(current_public_surfaces),
        "current_public_surfaces": current_public_surfaces,
        "future_reviewed_adapter_count": len(future_reviewed_adapters),
        "future_reviewed_adapters": future_reviewed_adapters,
        "local_artifact_source_count": sum(
            1 for source_id in by_id if source_id in _LOCAL_ARTIFACT_SOURCE_IDS
        ),
        "platform_counts": platform_counts,
        "platforms": sorted(platform_counts),
        "requires_gpu_source_count": sum(
            1 for source in by_id.values() if source.get("requires_gpu") is True
        ),
        "source_count": source_count,
        "source_map_only": source_map_only,
        "source_map_only_count": len(source_map_only),
    }


def _verify_source_entry(
    source: dict[str, Any],
    source_id: str,
    root: Path,
    failures: list[str],
) -> None:
    for field in _REQUIRED_SOURCE_FIELDS:
        value = source.get(field)
        if not isinstance(value, str) or not value:
            failures.append(f"{source_id}: {field} must be a non-empty string.")

    for field in _REQUIRED_BOOL_SOURCE_FIELDS:
        if not isinstance(source.get(field), bool):
            failures.append(f"{source_id}: {field} must be a boolean.")

    if source.get("public") is not True:
        failures.append(f"{source_id}: sources must remain public.")
    if source.get("publishes_private_candidates") is not False:
        failures.append(f"{source_id}: sources must not publish private candidates.")
    if source.get("review_required_before_claims") is not True:
        failures.append(f"{source_id}: review before claims is required.")

    safety_notes = source.get("safety_notes")
    if not _is_non_empty_text_list(safety_notes):
        failures.append(f"{source_id}: safety_notes must be a non-empty string list.")

    if source_id in _LOCAL_ARTIFACT_SOURCE_IDS:
        _verify_local_artifact_url(source, source_id, root, failures)

    if source_id == "lattice-estimator":
        notes = safety_notes if isinstance(safety_notes, list) else []
        if "Not a universal PQC oracle." not in notes:
            failures.append(
                "lattice-estimator: must state that it is not a universal PQC oracle."
            )


def _verify_local_artifact_url(
    source: dict[str, Any],
    source_id: str,
    root: Path,
    failures: list[str],
) -> None:
    url = source.get("url")
    if not isinstance(url, str):
        return
    if "://" in url or url.startswith("/"):
        failures.append(f"{source_id}: local artifact URL must be repository-relative.")
        return
    if not (root / url).exists():
        failures.append(f"{source_id}: local artifact URL does not exist: {url}.")


def _sources_by_status(
    by_id: dict[str, dict[str, Any]],
    status: str,
) -> list[str]:
    return sorted(
        source_id
        for source_id, source in by_id.items()
        if source.get("integration_status") == status
    )


def _is_non_empty_text_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item for item in value)
    )
