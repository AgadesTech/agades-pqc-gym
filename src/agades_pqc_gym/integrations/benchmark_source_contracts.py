from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BENCHMARK_SOURCE_CONTRACTS_SCHEMA = "agades.pqc.benchmark_source_contracts.v1"
BENCHMARK_SOURCE_CONTRACTS_VERIFICATION_SCHEMA = (
    "agades.pqc.benchmark_source_contracts_verification.v1"
)

_EXPECTED_FALSE_SAFETY_FLAGS = (
    "arbitrary_code_execution",
    "contains_private_traces",
    "public_verifier_downloads_large_assets",
    "publishes_private_candidates",
    "security_claim",
)
_REQUIRED_CONTRACT_TEXT_FIELDS = (
    "source_id",
    "target_family",
    "source_url",
    "source_catalog_id",
    "adapter_status",
)
_REQUIRED_CONTRACT_LIST_FIELDS = (
    "allowed_surfaces",
    "blocked_surfaces",
    "required_review_gates",
    "claim_boundaries",
)
_FUTURE_ADAPTER_BLOCKED_SURFACES = (
    "current_public_verifier",
    "prime_json_only_reward_environment",
    "public_benchmark_v0_claim_surface",
)


def build_benchmark_source_contracts() -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "schema_version": BENCHMARK_SOURCE_CONTRACTS_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
            "package": "agades_pqc_gym",
            "cli": "agades-pqc",
        },
        "contracts": [
            {
                "source_id": "facebook-tapas",
                "title": (
                    "TAPAS: Datasets for Learning the Learning with Errors Problem"
                ),
                "source_url": "https://huggingface.co/datasets/facebook/TAPAS",
                "source_catalog_id": "facebook-tapas",
                "target_family": "lattice",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": True,
                "allowed_surfaces": [
                    "private_reproduction_workspace",
                    "future_reviewed_huggingface_dataset_mirror",
                    "future_nvidia_gpu_reproduction_plan",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "reviewed_parameter_mapping",
                    "storage_and_checksum_plan",
                    "private_trace_redaction_plan",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "license": "cc-by-4.0",
                    "total_file_size_gb": 364,
                    "settings": [
                        {
                            "n": 256,
                            "log_q": 20,
                            "omega": 10,
                            "rho": 0.4284,
                            "samples": "400M",
                        },
                        {
                            "n": 512,
                            "log_q": 12,
                            "omega": 10,
                            "rho": 0.9036,
                            "samples": "40M",
                        },
                        {
                            "n": 512,
                            "log_q": 28,
                            "omega": 10,
                            "rho": 0.6740,
                            "samples": "40M",
                        },
                        {
                            "n": 512,
                            "log_q": 41,
                            "omega": 10,
                            "rho": 0.3992,
                            "samples": "40M",
                        },
                        {
                            "n": 1024,
                            "log_q": 26,
                            "omega": 10,
                            "rho": 0.86,
                            "samples": "40M",
                        },
                    ],
                },
                "claim_boundaries": [
                    "Dataset ingestion is not implemented in the public MVP.",
                    "No result from this source may be reported as a deployed "
                    "standard break without expert review.",
                    "Large public data must not be downloaded by the JSON-only "
                    "public verifier.",
                ],
            },
            {
                "source_id": "facebook-lwe-benchmarking",
                "title": "Benchmarking Attacks on Learning with Errors",
                "source_url": "https://github.com/facebookresearch/LWE-benchmarking",
                "source_catalog_id": "facebook-lwe-benchmarking",
                "target_family": "lattice",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": True,
                "requires_large_storage": True,
                "allowed_surfaces": [
                    "private_reproduction_workspace",
                    "future_nvidia_gpu_reproduction_plan",
                    "future_reviewed_public_reproduction_bundle",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "gpu_isolated_runner",
                    "external_toolchain_pin",
                    "reviewed_attack_mapping",
                    "private_trace_redaction_plan",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "min_python": "3.10.12",
                    "requires_nvidia_gpu": True,
                    "external_tools": ["flatter"],
                    "separate_environments": ["non_sage_conda", "sage"],
                    "attacks": [
                        "uSVP",
                        "SALSA",
                        "Cool&Cruel",
                        "Dual Hybrid MitM",
                    ],
                    "toy_dataset": {
                        "n": 80,
                        "log_q": 7,
                        "compressed_size_mb": 140,
                        "uncompressed_size_gb": 1,
                    },
                },
                "claim_boundaries": [
                    "Repository workflows require heavyweight dependencies and "
                    "must stay outside the JSON-only verifier.",
                    "Results must be labeled benchmark reproduction evidence, "
                    "not a deployed PQC security claim.",
                    "GPU/Sage execution requires a separately reviewed runner.",
                ],
            },
            {
                "source_id": "hf-post-quantum-crypto-fr-instruction-seed",
                "title": (
                    "AYI-NEDJIMI French post-quantum cryptography instruction seed"
                ),
                "source_url": (
                    "https://huggingface.co/datasets/"
                    "AYI-NEDJIMI/post-quantum-crypto-fr"
                ),
                "source_catalog_id": "hf-post-quantum-crypto-fr",
                "target_family": "all",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "future_reviewed_instruction_eval_seed",
                    "future_huggingface_dataset_card_context",
                    "private_pqc_qa_validation_workspace",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "source_fact_verification",
                    "license_review",
                    "answer_source_grounding_review",
                    "dataset_bias_and_staleness_review",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "language": "fr",
                    "row_count": 122,
                    "tasks": ["question_answering", "text_classification"],
                    "license": "apache-2.0",
                    "schema_fields": [
                        "id",
                        "question",
                        "answer",
                        "category",
                        "source_url",
                    ],
                },
                "claim_boundaries": [
                    "This source is a future reviewed instruction or QA seed, "
                    "not a complete PQC cryptanalysis corpus.",
                    "Rows must not be used for supervised training, evaluator "
                    "claims, or migration advice without source grounding and "
                    "license review.",
                    "No item from this dataset is accepted by the current "
                    "JSON-only public verifier.",
                ],
            },
            {
                "source_id": "hf-post-quantum-crypto-en-instruction-seed",
                "title": (
                    "AYI-NEDJIMI English post-quantum cryptography instruction seed"
                ),
                "source_url": (
                    "https://huggingface.co/datasets/"
                    "AYI-NEDJIMI/post-quantum-crypto-en"
                ),
                "source_catalog_id": "hf-post-quantum-crypto-en",
                "target_family": "all",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "future_reviewed_instruction_eval_seed",
                    "future_huggingface_dataset_card_context",
                    "private_pqc_qa_validation_workspace",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "source_fact_verification",
                    "license_review",
                    "answer_source_grounding_review",
                    "dataset_bias_and_staleness_review",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "language": "en",
                    "row_count": 122,
                    "tasks": ["question_answering", "text_classification"],
                    "license": "apache-2.0",
                    "schema_fields": [
                        "id",
                        "question",
                        "answer",
                        "category",
                        "source_url",
                    ],
                },
                "claim_boundaries": [
                    "This source is a future reviewed instruction or QA seed, "
                    "not a complete PQC cryptanalysis corpus.",
                    "Rows must not be used for supervised training, evaluator "
                    "claims, or migration advice without source grounding and "
                    "license review.",
                    "No item from this dataset is accepted by the current "
                    "JSON-only public verifier.",
                ],
            },
            {
                "source_id": "hf-pqc-ssl-scans-migration-scoring",
                "title": "Q-GRID PQC SSL scan dataset migration-scoring anchor",
                "source_url": "https://huggingface.co/datasets/Q-GRID/pqc-ssl-scans",
                "source_catalog_id": "hf-pqc-ssl-scans",
                "target_family": "all",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "future_reviewed_migration_scoring_eval",
                    "future_huggingface_dataset_card_context",
                    "private_pqc_migration_analysis_workspace",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "source_fact_verification",
                    "license_review",
                    "domain_sampling_review",
                    "migration_scoring_methodology_review",
                    "staleness_review",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "row_count": 45,
                    "domains": ["finance", "government", "healthcare"],
                    "tasks": [
                        "tls_pqc_readiness_review",
                        "migration_scoring",
                    ],
                    "observations": [
                        "ssl_scan_metadata",
                        "pqc_support_indicators",
                    ],
                },
                "claim_boundaries": [
                    "This source may only seed future migration-readiness "
                    "analysis after sampling, staleness, and methodology review.",
                    "A small public scan dataset is not a representative "
                    "industry-wide PQC deployment survey.",
                    "No endpoint or score from this dataset is accepted by the "
                    "current JSON-only public verifier.",
                ],
            },
            {
                "source_id": "hf-sc2026-side-channel-research",
                "title": "SC2026 far-field EM side-channel research anchor",
                "source_url": "https://huggingface.co/datasets/SCA-HNUST/SC2026",
                "source_catalog_id": "hf-sc2026-side-channel",
                "target_family": "implementation_security",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": True,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "private_side_channel_research_workspace",
                    "future_reviewed_side_channel_reproduction_plan",
                    "future_nvidia_gpu_reproduction_plan",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "trace_provenance_review",
                    "hardware_scope_review",
                    "leakage_model_review",
                    "responsible_disclosure_review",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "contains_kyber": True,
                    "algorithms": ["AES", "SM4", "CRYSTALS-Kyber"],
                    "modalities": ["far_field_em", "time_series"],
                    "file_formats": ["parquet_preview", "npy_full_dataset"],
                    "research_tasks": [
                        "cpa",
                        "template_attack",
                        "cnn",
                        "mlp",
                        "transformer",
                        "domain_adaptation",
                    ],
                    "preview_row_count": 1000,
                    "total_file_size_mb": 342,
                },
                "claim_boundaries": [
                    "This source is side-channel research infrastructure, not "
                    "a current Agades public verifier input.",
                    "Any reproduction plan must pin trace provenance, hardware "
                    "scope, leakage model, and disclosure boundaries first.",
                    "No result from this dataset may be reported as a general "
                    "PQC side-channel resistance claim.",
                ],
            },
            {
                "source_id": "nist-hqc-standardization-track",
                "title": "NIST HQC standardization track",
                "source_url": (
                    "https://csrc.nist.gov/News/2025/"
                    "hqc-announced-as-a-4th-round-selection"
                ),
                "source_catalog_id": "nist-hqc-selection",
                "target_family": "code_based",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "private_code_based_review_workspace",
                    "future_reviewed_public_hqc_schema_benchmark",
                    "future_nvidia_cpu_benchmark_plan",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "reviewed_hqc_parameter_mapping",
                    "decoder_failure_model_review",
                    "test_vector_provenance_pin",
                    "nist_status_pin",
                    "private_trace_redaction_plan",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "selection_date": "2025-03-11",
                    "selected_algorithm": "HQC",
                    "selection_round": "NIST PQC fourth round",
                    "selected_as": "second PQC KEM following ML-KEM",
                    "standard_status": "draft_standard_expected_before_final",
                    "nist_report": "NIST IR 8545",
                    "not_selected": ["BIKE", "Classic McEliece"],
                },
                "claim_boundaries": [
                    "The current code-based toy ISD and quasi-cyclic rotation "
                    "surfaces are not HQC security estimators.",
                    "Future HQC work must pin NIST status, parameters, "
                    "test-vector provenance, and decoder-failure assumptions.",
                    "No HQC result may be reported from the JSON-only public "
                    "verifier without expert review.",
                ],
            },
            {
                "source_id": "nist-bike-round4-status",
                "title": "NIST BIKE fourth-round status",
                "source_url": "https://csrc.nist.gov/pubs/ir/8545/final",
                "source_catalog_id": "nist-bike-round4-status",
                "target_family": "code_based",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "private_code_based_review_workspace",
                    "future_reviewed_public_bike_schema_benchmark",
                    "future_nvidia_cpu_benchmark_plan",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "reviewed_bike_parameter_mapping",
                    "decoder_failure_model_review",
                    "nist_status_pin",
                    "private_trace_redaction_plan",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "selection_date": "2025-03-11",
                    "selected_algorithm": "HQC",
                    "round4_outcome": "not_selected",
                    "selection_round": "NIST PQC fourth round",
                    "nist_report": "NIST IR 8545",
                },
                "claim_boundaries": [
                    "The current BIKE-like schema-only AttackPlan validates "
                    "routing only and is not a BIKE security estimator.",
                    "Future BIKE work must pin NIST status, parameters, "
                    "decoder-failure assumptions, and claim boundaries.",
                    "No BIKE result may be reported from the JSON-only public "
                    "verifier without expert review.",
                ],
            },
            {
                "source_id": "nist-classic-mceliece-round4-status",
                "title": "NIST Classic McEliece fourth-round status",
                "source_url": "https://csrc.nist.gov/pubs/ir/8545/final",
                "source_catalog_id": "nist-classic-mceliece-round4-status",
                "target_family": "code_based",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "private_code_based_review_workspace",
                    "future_reviewed_public_classic_mceliece_schema_benchmark",
                    "future_nvidia_cpu_benchmark_plan",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "reviewed_classic_mceliece_parameter_mapping",
                    "decoding_workfactor_model_review",
                    "kat_vector_provenance_pin",
                    "nist_status_pin",
                    "private_trace_redaction_plan",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "selection_date": "2025-03-11",
                    "selected_algorithm": "HQC",
                    "round4_outcome": "not_selected",
                    "selection_round": "NIST PQC fourth round",
                    "nist_report": "NIST IR 8545",
                },
                "claim_boundaries": [
                    "The current Classic McEliece-like schema-only AttackPlan "
                    "validates routing only and is not a Classic McEliece "
                    "security estimator.",
                    "Future Classic McEliece work must pin NIST status, "
                    "parameters, KAT provenance, decoding-workfactor model, "
                    "and claim boundaries.",
                    "No Classic McEliece result may be reported from the "
                    "JSON-only public verifier without expert review.",
                ],
            },
            {
                "source_id": "nist-fips-205-slh-dsa-reference",
                "title": "NIST FIPS 205 SLH-DSA standard reference",
                "source_url": "https://csrc.nist.gov/pubs/fips/205/final",
                "source_catalog_id": "nist-fips-205",
                "target_family": "hash_based",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "private_hash_based_review_workspace",
                    "future_reviewed_public_slh_dsa_vector_bundle",
                    "future_huggingface_slh_dsa_metadata_dataset",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "algorithm_revision_mapping",
                    "parameter_set_mapping",
                    "test_vector_provenance_pin",
                    "signature_trace_redaction_plan",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "publication_date": "2024-08-13",
                    "algorithm": "SLH-DSA",
                    "based_on": "SPHINCS+",
                    "standard": "FIPS 205",
                    "scheme_type": "stateless_hash_based_signature",
                },
                "claim_boundaries": [
                    "The current hash-based WOTS-chain fixture is toy plumbing, "
                    "not an SLH-DSA implementation or proof.",
                    "Future SLH-DSA test bundles must pin parameter sets, "
                    "revision status, and vector provenance before publication.",
                    "Passing a future vector fixture would be conformance "
                    "evidence only, not a hash-function or signature-security "
                    "claim.",
                ],
            },
            {
                "source_id": "nist-additional-signatures-round3-multivariate",
                "title": (
                    "NIST additional PQC digital signatures round-three "
                    "multivariate candidates"
                ),
                "source_url": (
                    "https://csrc.nist.gov/News/2026/"
                    "nist-advances-9-candidates-to-the-3rd-round-of-pqc"
                ),
                "source_catalog_id": "nist-additional-signatures-round3",
                "target_family": "multivariate",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "private_multivariate_review_workspace",
                    "future_reviewed_public_multivariate_schema_benchmark",
                    "future_prime_environment_after_expert_review",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "selected_candidate_status_pin",
                    "public_parameter_mapping",
                    "algebraic_attack_model_review",
                    "implementation_source_pin",
                    "private_trace_redaction_plan",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "announcement_date": "2026-05-14",
                    "nist_report": "NIST IR 8610",
                    "phase": "third_round_additional_digital_signatures",
                    "expected_review_duration_years": 2,
                    "multivariate_candidates": [
                        "MAYO",
                        "QR-UOV",
                        "UOV",
                    ],
                },
                "claim_boundaries": [
                    "The current MQ and MinRank toy evaluators are not MAYO, "
                    "QR-UOV, UOV, or candidate-security estimators.",
                    "Future candidate adapters must pin NIST status, public "
                    "parameters, implementation sources, and attack-model "
                    "scope before publication.",
                    "No NIST additional-signature security claim may be made "
                    "from current public toy results.",
                ],
            },
            {
                "source_id": "liboqs-implementation-harness",
                "title": "Open Quantum Safe liboqs test and benchmark harness",
                "source_url": "https://github.com/open-quantum-safe/liboqs",
                "source_catalog_id": "liboqs",
                "target_family": "implementation_security",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "private_implementation_security_workspace",
                    "future_reviewed_public_kat_bundle",
                    "future_prime_environment_with_isolated_runner",
                    "future_nvidia_cpu_benchmark_plan",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "external_toolchain_pin",
                    "kat_conformance_mapping",
                    "memory_benchmark_mapping",
                    "constant_time_tool_interpretation",
                    "private_trace_redaction_plan",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "build_system": "cmake+ninja",
                    "test_programs": [
                        "test_kem",
                        "test_sig",
                        "test_sig_stfl",
                        "test_kem_mem",
                        "test_sig_mem",
                        "test_portability",
                    ],
                    "kat_programs": ["kat_kem", "kat_sig", "kat_sig_stfl"],
                    "benchmark_programs": [
                        "speed_kem",
                        "speed_sig",
                        "speed_sig_stfl",
                    ],
                    "upstream_warning": (
                        "liboqs is for research/prototyping and is not "
                        "recommended by upstream for protecting sensitive data"
                    ),
                },
                "claim_boundaries": [
                    "liboqs workflows are not executed by the current public "
                    "verifier.",
                    "Future KAT, memory, and speed results require pinned "
                    "toolchains, reviewed algorithm mappings, and explicit "
                    "hardware/software environment records.",
                    "Passing liboqs tests is implementation evidence only, not "
                    "a cryptanalytic or production-security claim.",
                ],
            },
            {
                "source_id": "pq-code-package-native-implementations",
                "title": (
                    "PQ Code Package native ML-KEM/ML-DSA implementation "
                    "contracts"
                ),
                "source_url": "https://github.com/pq-code-package",
                "source_catalog_id": "pq-code-package",
                "target_family": "implementation_security",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "private_implementation_security_workspace",
                    "future_reviewed_public_acvp_kat_bundle",
                    "future_prime_environment_with_isolated_runner",
                    "future_nvidia_cpu_benchmark_plan",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "high_assurance_source_pin",
                    "acvp_vector_release_pin",
                    "external_toolchain_pin",
                    "static_model_checking_scope_review",
                    "constant_time_tool_interpretation",
                    "benchmark_environment_record",
                    "private_trace_redaction_plan",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "repositories": ["mlkem-native", "mldsa-native"],
                    "standards_scope": ["FIPS 203", "FIPS 204"],
                    "implementation_style": (
                        "portable C90 frontends with native backend options"
                    ),
                    "review_signals": [
                        "ACVP test vectors",
                        "CBMC undefined-behaviour checks",
                        "valgrind secret-dependent branch/access checks",
                    ],
                    "benchmark_surfaces": [
                        "speed",
                        "stack_usage",
                        "binary_size",
                    ],
                },
                "claim_boundaries": [
                    "PQ Code Package workflows are not executed by the current "
                    "JSON-only public verifier.",
                    "Future KAT, constant-time, and benchmark outputs require "
                    "pinned source revisions, ACVP vector releases, toolchains, "
                    "and hardware/software environment records.",
                    "Passing future native implementation tests would be "
                    "correctness or implementation evidence only, not a "
                    "cryptanalytic or production-security claim.",
                ],
            },
            {
                "source_id": "pqm4-cortexm4-benchmarking",
                "title": "pqm4 ARM Cortex-M4 testing and benchmarking framework",
                "source_url": "https://github.com/mupq/pqm4",
                "source_catalog_id": "pqm4",
                "target_family": "implementation_security",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "private_embedded_benchmark_workspace",
                    "future_reviewed_public_embedded_benchmark_bundle",
                    "future_nvidia_embedded_workload_plan",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "device_or_simulator_isolation",
                    "board_firmware_pin",
                    "kat_reference_mapping",
                    "serial_io_redaction_plan",
                    "timing_measurement_protocol",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "target": "ARM Cortex-M4",
                    "metrics": [
                        "speed",
                        "stack_usage",
                        "code_size",
                        "symmetric_primitive_cycles",
                    ],
                    "testing_features": [
                        "functional_testing",
                        "test_vector_generation",
                        "reference_output_comparison",
                    ],
                    "implementation_sources": ["PQClean", "NIST submissions"],
                },
                "claim_boundaries": [
                    "pqm4 requires reviewed device, simulator, firmware, and "
                    "serial-output handling before any public benchmark result.",
                    "Embedded speed, stack, and code-size measurements are "
                    "environment-specific and must not be compared without a "
                    "pinned board/simulator protocol.",
                    "The current MVP records this as future infrastructure only.",
                ],
            },
            {
                "source_id": "nist-acvp-pqc-vectors",
                "title": "NIST ACVP PQC validation protocol and vector sources",
                "source_url": "https://github.com/usnistgov/ACVP",
                "source_catalog_id": "nist-acvp",
                "target_family": "implementation_security",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "private_kat_validation_workspace",
                    "future_reviewed_public_kat_bundle",
                    "future_huggingface_kat_metadata_dataset",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "vector_provenance_pin",
                    "algorithm_revision_mapping",
                    "validation_scope_mapping",
                    "generated_vector_redaction_plan",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "protocol": "Automated Cryptographic Validation Protocol",
                    "pqc_algorithm_groups": [
                        "ML-KEM",
                        "ML-DSA",
                        "SLH-DSA",
                    ],
                    "nist_project": "ACVP",
                    "server_repository": "https://github.com/usnistgov/ACVP-Server",
                },
                "claim_boundaries": [
                    "ACVP/CAVP vectors are correctness or validation inputs, "
                    "not cryptanalytic attack evidence.",
                    "Future public KAT bundles must pin vector provenance and "
                    "algorithm revision before publication.",
                    "No ACVP server interaction is performed by the current "
                    "JSON-only public verifier.",
                ],
            },
            {
                "source_id": "dudect-statistical-timing-leakage",
                "title": "dudect statistical timing-leakage test harness",
                "source_url": "https://github.com/oreparaz/dudect",
                "source_catalog_id": "dudect",
                "target_family": "implementation_security",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "private_constant_time_review_workspace",
                    "future_reviewed_public_timing_leakage_bundle",
                    "future_nvidia_cpu_benchmark_plan",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "source_revision_pin",
                    "compiler_and_flags_pin",
                    "measurement_protocol_review",
                    "statistical_threshold_review",
                    "hardware_noise_model_record",
                    "private_trace_redaction_plan",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "method": "two-class timing measurement",
                    "statistical_method": [
                        "welch_t_test",
                        "t_value_threshold_review_required",
                    ],
                    "requires": [
                        "c_compiler",
                        "pinned_cpu_environment",
                        "reviewed_input_classification",
                    ],
                    "typical_outputs": [
                        "measurement_count",
                        "max_t_statistic",
                        "timing_leakage_classification",
                    ],
                },
                "claim_boundaries": [
                    "dudect is not executed by the current JSON-only public "
                    "verifier.",
                    "A passing timing experiment is not a constant-time proof "
                    "and must not be reported as a production-security claim.",
                    "Future outputs require pinned source, compiler, CPU, "
                    "input classes, thresholds, and expert review.",
                ],
            },
            {
                "source_id": "ctgrind-secret-taint-analysis",
                "title": "ctgrind Valgrind secret-taint analysis contract",
                "source_url": "https://github.com/agl/ctgrind",
                "source_catalog_id": "ctgrind",
                "target_family": "implementation_security",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "private_constant_time_review_workspace",
                    "future_reviewed_public_secret_taint_bundle",
                    "future_nvidia_cpu_benchmark_plan",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "source_revision_pin",
                    "valgrind_environment_pin",
                    "secret_annotation_scope_review",
                    "compiler_and_flags_pin",
                    "tool_limitation_review",
                    "private_trace_redaction_plan",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "base_tool": "Valgrind memcheck",
                    "checks": [
                        "secret_dependent_branch",
                        "secret_dependent_memory_access",
                    ],
                    "inputs_required": [
                        "secret_annotation_policy",
                        "public_input_policy",
                        "pinned_binary_under_test",
                    ],
                    "status_note": (
                        "historical patch-based approach; modern review must "
                        "pin usable Valgrind support or successor tooling"
                    ),
                },
                "claim_boundaries": [
                    "ctgrind workflows are not executed by the current "
                    "JSON-only public verifier.",
                    "Dynamic secret-taint checks are implementation evidence "
                    "only and do not prove absence of all side channels.",
                    "Future outputs require reviewed annotations, toolchain, "
                    "Valgrind behavior, and expert interpretation.",
                ],
            },
            {
                "source_id": "timecop-supercop-policy-checks",
                "title": "TIMECOP/SUPERCOP constant-time policy checks",
                "source_url": "https://bench.cr.yp.to/supercop.html",
                "source_catalog_id": "timecop-supercop",
                "target_family": "implementation_security",
                "adapter_status": "future_reviewed_adapter",
                "current_runtime_enabled": False,
                "public_verifier_allowed": False,
                "requires_gpu": False,
                "requires_large_storage": False,
                "allowed_surfaces": [
                    "private_supercop_review_workspace",
                    "future_reviewed_public_timecop_bundle",
                    "future_nvidia_cpu_benchmark_plan",
                ],
                "blocked_surfaces": [
                    "current_public_verifier",
                    "prime_json_only_reward_environment",
                    "public_benchmark_v0_claim_surface",
                ],
                "required_review_gates": [
                    "supercop_source_pin",
                    "timecop_policy_scope_review",
                    "cpu_and_toolchain_record",
                    "implementation_opt_goal_mapping",
                    "result_database_provenance_pin",
                    "private_trace_redaction_plan",
                    "expert_review_before_claims",
                ],
                "source_facts": {
                    "framework": "SUPERCOP",
                    "tool_versions": [
                        "original TIMECOP",
                        "TIMECOP 2",
                    ],
                    "policy_surfaces": [
                        "secret_dependent_branch",
                        "secret_dependent_memory_access",
                        "public_input_declassification",
                    ],
                    "result_scope": [
                        "implementation_specific",
                        "cpu_specific",
                        "toolchain_specific",
                    ],
                },
                "claim_boundaries": [
                    "TIMECOP/SUPERCOP workflows are not executed by the current "
                    "JSON-only public verifier.",
                    "Future TIMECOP outputs are implementation-testing evidence "
                    "only, not a general constant-time or security claim.",
                    "Publication requires pinned SUPERCOP source, policy scope, "
                    "CPU/toolchain metadata, and expert review.",
                ],
            },
        ],
        "safety": {
            "arbitrary_code_execution": False,
            "contains_private_traces": False,
            "public_verifier_downloads_large_assets": False,
            "publishes_private_candidates": False,
            "security_claim": False,
        },
        "release_gates": [
            "uv run pytest tests/test_benchmark_source_contracts.py -q",
            (
                "uv run agades-pqc benchmark-source-contracts --out "
                "docs/benchmark_source_contracts.json"
            ),
            (
                "uv run agades-pqc benchmark-source-verify --contracts "
                "docs/benchmark_source_contracts.json"
            ),
            "uv run agades-pqc ecosystem-smoke-verify --report "
            "reports/ecosystem_smoke.json",
            "uv run agades-pqc release-audit --out public/release_audit.json",
        ],
    }
    manifest["summary"] = summarize_benchmark_source_contracts(manifest)
    return manifest


def write_benchmark_source_contracts(out: Path) -> dict[str, Any]:
    contracts = build_benchmark_source_contracts()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(contracts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return contracts


def verify_benchmark_source_contracts(path: Path) -> dict[str, Any]:
    failures: list[str] = []
    manifest = _read_contract_manifest(path, failures)

    if manifest.get("schema_version") != BENCHMARK_SOURCE_CONTRACTS_SCHEMA:
        failures.append(
            "manifest: schema_version must be "
            f"{BENCHMARK_SOURCE_CONTRACTS_SCHEMA}."
        )

    _verify_safety_block(manifest, failures)

    contracts = manifest.get("contracts")
    if not isinstance(contracts, list):
        failures.append("manifest: contracts must be a list.")
        contracts = []

    summary = _summarize_contracts(contracts, failures)
    if not failures and manifest.get("summary") != summary:
        failures.append("manifest: summary is inconsistent with contract entries.")
    if not failures and manifest != build_benchmark_source_contracts():
        failures.append(
            "manifest: contents are not synchronized with the current runtime "
            "benchmark source contracts."
        )
    summary["failure_count"] = len(failures)

    return {
        "schema_version": BENCHMARK_SOURCE_CONTRACTS_VERIFICATION_SCHEMA,
        "contracts_path": str(path),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def summarize_benchmark_source_contracts(manifest: dict[str, Any]) -> dict[str, Any]:
    contracts = manifest.get("contracts")
    if not isinstance(contracts, list):
        contracts = []
    return _summarize_contracts_without_validation(contracts)


def _read_contract_manifest(path: Path, failures: list[str]) -> dict[str, Any]:
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


def _verify_safety_block(manifest: dict[str, Any], failures: list[str]) -> None:
    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        failures.append("manifest: safety must be an object.")
        return

    for flag in _EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            failures.append(f"manifest: safety.{flag} must be false.")


def _summarize_contracts(
    contracts: list[Any],
    failures: list[str],
) -> dict[str, Any]:
    for index, contract in enumerate(contracts):
        if not isinstance(contract, dict):
            failures.append(f"contract[{index}]: contract must be an object.")
            continue

        contract_id = _contract_id(contract, index)
        _verify_contract_shape(contract, contract_id, failures)

        if contract.get("adapter_status") == "future_reviewed_adapter":
            _verify_future_reviewed_contract(contract, contract_id, failures)

    return _summarize_contracts_without_validation(contracts)


def _summarize_contracts_without_validation(contracts: list[Any]) -> dict[str, Any]:
    blocked_public_benchmark_claim_surface = 0
    blocked_public_verifier = 0
    blocked_prime_reward = 0
    current_runtime_enabled = 0
    expert_review_gate = 0
    future_reviewed = 0
    heavy_storage = 0
    public_verifier_allowed = 0
    requires_gpu = 0
    source_catalog_ids: set[str] = set()
    target_family_counts: dict[str, int] = {}

    for contract in contracts:
        if not isinstance(contract, dict):
            continue

        blocked_surfaces = _list_or_empty(contract.get("blocked_surfaces"))
        if "current_public_verifier" in blocked_surfaces:
            blocked_public_verifier += 1
        if "prime_json_only_reward_environment" in blocked_surfaces:
            blocked_prime_reward += 1
        if "public_benchmark_v0_claim_surface" in blocked_surfaces:
            blocked_public_benchmark_claim_surface += 1

        required_review_gates = _list_or_empty(contract.get("required_review_gates"))
        if "expert_review_before_claims" in required_review_gates:
            expert_review_gate += 1

        if contract.get("adapter_status") == "future_reviewed_adapter":
            future_reviewed += 1
        if contract.get("current_runtime_enabled") is True:
            current_runtime_enabled += 1
        if contract.get("public_verifier_allowed") is True:
            public_verifier_allowed += 1
        if contract.get("requires_gpu") is True:
            requires_gpu += 1
        if contract.get("requires_large_storage") is True:
            heavy_storage += 1

        source_catalog_id = contract.get("source_catalog_id")
        if isinstance(source_catalog_id, str) and source_catalog_id:
            source_catalog_ids.add(source_catalog_id)

        target_family = contract.get("target_family")
        if isinstance(target_family, str) and target_family:
            target_family_counts[target_family] = (
                target_family_counts.get(target_family, 0) + 1
            )

    return {
        "blocked_public_benchmark_claim_surface_contracts": (
            blocked_public_benchmark_claim_surface
        ),
        "blocked_public_verifier_contracts": blocked_public_verifier,
        "blocked_prime_reward_contracts": blocked_prime_reward,
        "contract_count": len(contracts),
        "current_runtime_enabled_contracts": current_runtime_enabled,
        "expert_review_gate_contracts": expert_review_gate,
        "future_reviewed_adapters": future_reviewed,
        "heavy_storage_contracts": heavy_storage,
        "public_verifier_allowed_contracts": public_verifier_allowed,
        "requires_gpu_contracts": requires_gpu,
        "source_catalog_id_count": len(source_catalog_ids),
        "target_family_counts": dict(sorted(target_family_counts.items())),
    }


def _contract_id(contract: dict[str, Any], index: int) -> str:
    source_id = contract.get("source_id")
    if isinstance(source_id, str) and source_id:
        return source_id
    return f"contract[{index}]"


def _verify_contract_shape(
    contract: dict[str, Any],
    contract_id: str,
    failures: list[str],
) -> None:
    for field in _REQUIRED_CONTRACT_TEXT_FIELDS:
        value = contract.get(field)
        if not isinstance(value, str) or not value:
            failures.append(f"{contract_id}: {field} must be a non-empty string.")

    for field in _REQUIRED_CONTRACT_LIST_FIELDS:
        value = contract.get(field)
        if not _is_non_empty_text_list(value):
            failures.append(f"{contract_id}: {field} must be a non-empty string list.")

    if not isinstance(contract.get("source_facts"), dict):
        failures.append(f"{contract_id}: source_facts must be an object.")

    for field in (
        "current_runtime_enabled",
        "public_verifier_allowed",
        "requires_gpu",
        "requires_large_storage",
    ):
        if not isinstance(contract.get(field), bool):
            failures.append(f"{contract_id}: {field} must be a boolean.")


def _verify_future_reviewed_contract(
    contract: dict[str, Any],
    contract_id: str,
    failures: list[str],
) -> None:
    if contract.get("current_runtime_enabled") is not False:
        failures.append(
            f"{contract_id}: future reviewed adapters must not enable runtime."
        )

    if contract.get("public_verifier_allowed") is not False:
        failures.append(
            f"{contract_id}: future reviewed adapters must not be allowed "
            "in the public verifier."
        )

    blocked_surfaces = _list_or_empty(contract.get("blocked_surfaces"))
    for surface in _FUTURE_ADAPTER_BLOCKED_SURFACES:
        if surface not in blocked_surfaces:
            failures.append(f"{contract_id}: missing blocked surface {surface}.")

    required_review_gates = _list_or_empty(contract.get("required_review_gates"))
    if "expert_review_before_claims" not in required_review_gates:
        failures.append(f"{contract_id}: missing gate expert_review_before_claims.")


def _is_non_empty_text_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item for item in value)
    )


def _list_or_empty(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []
