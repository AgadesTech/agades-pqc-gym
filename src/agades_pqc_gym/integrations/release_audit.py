from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.target import TargetSpec
from agades_pqc_gym.core.trace_record import TraceRecord
from agades_pqc_gym.deepevolve_hooks.injection import (
    PAPER_CARD_INJECTION_BATCH_SCHEMA,
    write_paper_card_injection_batch,
)
from agades_pqc_gym.evaluators.lattice_estimator import (
    LATTICE_ESTIMATOR_PINNED_COMMIT,
    LatticeEstimatorAdapter,
    LatticeEstimatorConfig,
    reviewed_lwe_estimator_mappings,
)
from agades_pqc_gym.evaluators.mock_estimator import MockEstimatorAdapter
from agades_pqc_gym.evolution.archive import (
    EVOLUTION_ARCHIVE_SCHEMA,
    build_evolution_archive,
)
from agades_pqc_gym.evolution.campaign import (
    PRIVATE_EVOLUTION_CAMPAIGN_PLAN_SCHEMA,
    verify_private_evolution_campaign_plan,
    write_private_evolution_campaign_plan,
)
from agades_pqc_gym.evolution.cron import write_heldout_cron_plan
from agades_pqc_gym.evolution.heldout import build_heldout_candidate_plans
from agades_pqc_gym.evolution.heldout_review_packet import (
    verify_heldout_review_packet,
    write_heldout_review_packet,
)
from agades_pqc_gym.evolution.mutation import (
    CANDIDATE_MUTATION_BATCH_SCHEMA,
    build_archive_candidate_mutation_batch,
    build_candidate_mutation_batch,
)
from agades_pqc_gym.evolution.rescore import (
    HELDOUT_RESCORE_SCHEMA,
    build_heldout_rescore,
)
from agades_pqc_gym.evolution.scheduler import (
    build_heldout_schedule,
    run_heldout_schedule,
    write_heldout_review_log,
    write_heldout_schedule,
)
from agades_pqc_gym.evolution.snapshot import (
    PRIVATE_ARCHIVE_SNAPSHOT_SCHEMA,
    write_private_archive_snapshot,
)
from agades_pqc_gym.integrations.benchmark_source_contracts import (
    build_benchmark_source_contracts,
    verify_benchmark_source_contracts,
)
from agades_pqc_gym.integrations.deepevolve_research_hooks import (
    build_deepevolve_research_hooks_manifest,
    verify_deepevolve_research_hooks_manifest,
)
from agades_pqc_gym.integrations.ecosystem_smoke import (
    build_ecosystem_smoke_report,
    verify_ecosystem_smoke_report,
)
from agades_pqc_gym.integrations.ecosystem_source_graph import (
    verify_ecosystem_source_graph,
)
from agades_pqc_gym.integrations.external_publication_review_packet import (
    verify_external_publication_review_packet,
)
from agades_pqc_gym.integrations.family_operator_catalog import (
    build_family_operator_catalog,
    verify_family_operator_catalog,
)
from agades_pqc_gym.integrations.family_plugin_manifest import (
    build_family_plugin_manifest,
    verify_family_plugin_manifest,
)
from agades_pqc_gym.integrations.family_registry_manifest import (
    build_family_registry_manifest,
    verify_family_registry_manifest,
)
from agades_pqc_gym.integrations.family_support import (
    build_family_support_matrix,
    verify_family_support_matrix,
)
from agades_pqc_gym.integrations.huggingface_collection_manifest import (
    verify_huggingface_collection_manifest,
)
from agades_pqc_gym.integrations.huggingface_dataset import (
    verify_huggingface_dataset_bundle,
)
from agades_pqc_gym.integrations.huggingface_publication_handoff import (
    verify_huggingface_publication_handoff,
)
from agades_pqc_gym.integrations.huggingface_space_manifest import (
    verify_huggingface_space_manifest,
)
from agades_pqc_gym.integrations.huggingface_space_smoke import (
    verify_huggingface_space_launch_smoke_report,
    verify_huggingface_space_smoke_report,
)
from agades_pqc_gym.integrations.lattice_estimator_baseline_contracts import (
    verify_lattice_estimator_baseline_contracts,
)
from agades_pqc_gym.integrations.lattice_estimator_baseline_run import (
    LATTICE_ESTIMATOR_BASELINE_RUN_SCHEMA,
    verify_lattice_estimator_baseline_run,
    write_lattice_estimator_baseline_run,
)
from agades_pqc_gym.integrations.lattice_estimator_checkout_preflight import (
    LATTICE_ESTIMATOR_CHECKOUT_PREFLIGHT_SCHEMA,
    write_lattice_estimator_checkout_preflight,
)
from agades_pqc_gym.integrations.lattice_estimator_manifest import (
    verify_lattice_estimator_manifest,
)
from agades_pqc_gym.integrations.lattice_estimator_review_packet import (
    verify_lattice_estimator_baseline_review_packet,
    write_lattice_estimator_baseline_review_packet,
)
from agades_pqc_gym.integrations.lattice_estimator_runtime_preflight import (
    DEFAULT_RUNTIME_PREFLIGHT_PATH,
    LATTICE_ESTIMATOR_RUNTIME_PREFLIGHT_SCHEMA,
    build_lattice_estimator_runtime_preflight,
    verify_lattice_estimator_runtime_preflight,
)
from agades_pqc_gym.integrations.nvidia_manifest_safety import (
    verify_nvidia_manifest_safety_report,
)
from agades_pqc_gym.integrations.nvidia_publication_handoff import (
    verify_nvidia_publication_handoff,
)
from agades_pqc_gym.integrations.pedagogical_rl_method import (
    verify_pedagogical_rl_method,
)
from agades_pqc_gym.integrations.prime_environment_manifest import (
    verify_prime_environment_manifest,
)
from agades_pqc_gym.integrations.prime_environment_smoke import (
    verify_prime_environment_smoke_report,
)
from agades_pqc_gym.integrations.prime_eval_config import verify_prime_eval_config
from agades_pqc_gym.integrations.prime_publication_handoff import (
    verify_prime_publication_handoff,
)
from agades_pqc_gym.integrations.prime_speedrun_handoff import (
    verify_prime_speedrun_handoff,
)
from agades_pqc_gym.integrations.prime_verifier_schemas import (
    verify_prime_verifier_schemas,
)
from agades_pqc_gym.integrations.private_dataset_curation import (
    verify_private_dataset_curation,
)
from agades_pqc_gym.integrations.private_run_policy import (
    build_private_run_policy,
    verify_private_run_policy,
)
from agades_pqc_gym.integrations.public_benchmark_manifest import (
    build_public_benchmark_manifest,
)
from agades_pqc_gym.integrations.public_private_boundary import (
    build_report_generator_redaction_check,
)
from agades_pqc_gym.integrations.public_run_export import verify_public_run_export
from agades_pqc_gym.integrations.publication_manifest import (
    verify_publication_manifest,
)
from agades_pqc_gym.integrations.runbook_audit import build_runbook_audit
from agades_pqc_gym.integrations.source_catalog import verify_source_catalog
from agades_pqc_gym.openevolve_adapter.config_templates import (
    DEFAULT_CONFIG_TEMPLATE,
    OPENEVOLVE_CONFIG_ARCHIVE_LOOP_KEYS,
    verify_default_config_template,
)
from agades_pqc_gym.openevolve_adapter.smoke import (
    verify_openevolve_smoke_report,
)
from agades_pqc_gym.validators.static import validate_attack_plan
from agades_pqc_gym.verifier import verify_attack_plan_path

RELEASE_AUDIT_SCHEMA = "agades.pqc.release_audit.v1"
ROOT = Path(__file__).resolve().parents[3]
LEGACY_NAME_PATTERNS = tuple(
    "".join(parts)
    for parts in (
        ("agades", "-", "cryptanalysis", "-", "gym"),
        ("agades", "_", "crypto", "_", "gym"),
        ("agades", "_", "crypto"),
        ("crypto", "_", "gym"),
        ("crypto", "-", "gym"),
        ("Agades", " ", "Cryptanalysis", " ", "Gym"),
        ("Cryptanalysis", " ", "Gym"),
    )
)
LEGACY_NAME_PATHS = (
    "README.md",
    "docs",
    "hf",
    "nvidia",
    "prime_intellect",
    "src",
    "tests",
    "examples",
    "pyproject.toml",
)
COMMUNITY_CARD_PATHS = {
    "benchmark_card": "hf/benchmark_card.md",
    "dataset_readme": "hf/dataset/README.md",
    "dataset_card": "hf/dataset_card.md",
    "prime_environment_card": "prime_intellect/environment_card.md",
    "mvp_report": "reports/AGADES_PQC_GYM_MVP_REPORT.md",
}
ECOSYSTEM_RELEASE_PLAN_PATHS = (
    "docs/HUGGINGFACE_RELEASE_PLAN.md",
    "docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md",
    "docs/PRIME_INTELLECT_RELEASE_PLAN.md",
)
ECOSYSTEM_RELEASE_PLAN_SCHEMA_ARTIFACTS = (
    "prime_intellect/schemas/attack_plan.schema.json",
    "prime_intellect/schemas/schema_manifest.json",
    "prime_intellect/schemas/task_metadata.schema.json",
    "prime_intellect/schemas/verifier_result.schema.json",
)
ECOSYSTEM_RELEASE_PLAN_PRIME_ANCHORS = {
    "prime-autonanogpt-speedrun": "https://www.primeintellect.ai/auto-nanogpt",
    "prime-autonomous-speedrunning-experiments": (
        "PrimeIntellect-ai/experiments-autonomous-speedrunning"
    ),
    "prime-quickstart": "https://app.primeintellect.ai/dashboard/home/quickstart",
}
ECOSYSTEM_RELEASE_PLAN_BOUNDARIES = (
    "No real private evolution traces",
    "not a security claim",
    "Prime Hub publication requires credentials",
    "No GPU workload is claimed in the current MVP",
)
TOY_FAMILY_CARD_PHRASES = {
    "CODE_BASED": ("code-based", "toy-code-based-isd-estimator"),
    "HASH_BASED": ("hash-based", "toy-hash-bound-estimator"),
    "IMPLEMENTATION_SECURITY": (
        "implementation-security",
        "toy-implementation-security-estimator",
    ),
    "ISOGENY_HISTORICAL": (
        "historical-isogeny",
        "toy-isogeny-historical-path-estimator",
    ),
    "MULTIVARIATE": ("multivariate", "toy-multivariate-estimator"),
}
STALE_COMMUNITY_CARD_CLAIMS = (
    "Only LWE/MLWE has an implemented MVP evaluation path",
    "Non-lattice families are schema-only",
    (
        "Code-based, multivariate, hash-based, historical isogeny, "
        "implementation-security: schema-only placeholders"
    ),
)
FAMILY_READINESS_REQUIREMENTS = {
    "code_based": {
        "target_families": {"CODE_BASED"},
        "benchmark_dirs": {
            "benchmarks/code_based_schema_only",
            "benchmarks/code_based_toy_isd",
        },
        "required_files": {
            "__init__.py",
            "adapter.py",
            "isd_estimator.py",
            "operators.py",
            "syndrome_solver.py",
            "targets.py",
        },
    },
    "hash_based": {
        "target_families": {"HASH_BASED"},
        "benchmark_dirs": {
            "benchmarks/hash_based_schema_only",
            "benchmarks/hash_based_toy_bound",
        },
        "required_files": {
            "__init__.py",
            "adapter.py",
            "bound_estimator.py",
            "operators.py",
            "preimage_solver.py",
            "targets.py",
        },
    },
    "implementation_security": {
        "target_families": {"IMPLEMENTATION_SECURITY"},
        "benchmark_dirs": {
            "benchmarks/implementation_security_schema_only",
            "benchmarks/implementation_security_toy_benchmark",
            "benchmarks/implementation_security_toy_kat",
            "benchmarks/implementation_security_toy_timing",
        },
        "required_files": {
            "__init__.py",
            "adapter.py",
            "benchmark_fixture.py",
            "kat_estimator.py",
            "kat_fixture.py",
            "operators.py",
            "targets.py",
            "timing_fixture.py",
        },
    },
    "isogeny_historical": {
        "target_families": {"ISOGENY_HISTORICAL"},
        "benchmark_dirs": {
            "benchmarks/isogeny_historical_schema_only",
            "benchmarks/isogeny_historical_toy_path",
        },
        "required_files": {
            "__init__.py",
            "adapter.py",
            "operators.py",
            "path_estimator.py",
            "path_fixture.py",
            "targets.py",
        },
    },
    "lattice": {
        "target_families": {"LWE", "MLWE", "NTRU", "SIS"},
        "benchmark_dirs": {
            "benchmarks/lattice_schema_only",
            "benchmarks/lattice_mlkem_like",
            "benchmarks/lattice_toy_lwe",
        },
        "required_files": {
            "__init__.py",
            "adapter.py",
            "lattice_estimator.py",
            "operators.py",
            "targets.py",
            "validators.py",
        },
    },
    "multivariate": {
        "target_families": {"MULTIVARIATE"},
        "benchmark_dirs": {
            "benchmarks/multivariate_schema_only",
            "benchmarks/multivariate_toy_minrank",
            "benchmarks/multivariate_toy_mq",
        },
        "required_files": {
            "__init__.py",
            "adapter.py",
            "minrank_solver.py",
            "mq_estimator.py",
            "mq_solver.py",
            "operators.py",
            "targets.py",
        },
    },
}
GITHUB_ACTIONS_REQUIRED_ACTIONS = (
    "actions/checkout@",
    "leanprover/lean-action@",
    "astral-sh/setup-uv@",
)
GITHUB_ACTIONS_LEAN_GATE_REQUIRED_INPUTS: dict[str, Any] = {
    "lake-package-directory": "formal/lean",
    "build": True,
    "test": False,
    "lint": False,
    "auto-config": False,
    "use-mathlib-cache": True,
}
GITHUB_ACTIONS_REQUIRED_COMMANDS = (
    ("build-package", "uv build"),
    ("build-prime-environment", "uv build prime_intellect/verifiers_environment"),
    (
        "check-artifact-diff",
        "git diff --exit-code -- docs/benchmark_source_contracts.json "
        "docs/source_catalog.json docs/deepevolve_research_hooks_manifest.json "
        "docs/family_registry_manifest.json "
        "docs/family_plugin_manifest.json "
        "docs/family_support_matrix.json "
        "docs/ecosystem_source_graph.json "
        "docs/family_operator_catalog.json "
        "docs/formal_lean_backend.json "
        "docs/lattice_estimator_manifest.json "
        "docs/lattice_estimator_baseline_contracts.json "
        "docs/runbook_input_manifest.json "
        "docs/public_benchmark_manifest.json public/run_export "
        "hf/dataset hf/space_manifest.json hf/collection_manifest.json "
        "docs/huggingface_publication_handoff.json "
        "nvidia/accelerator_manifest.json "
        "docs/nvidia_publication_handoff.json "
        "docs/publication_manifest.json "
        "docs/external_publication_review_packet.json "
        "docs/private_run_policy.json docs/private_dataset_curation.json "
        "docs/pedagogical_rl_method.json "
        "docs/prime_publication_handoff.json docs/prime_speedrun_handoff.json "
        "docs/prime_eval_config_manifest.json "
        "prime_intellect/evals/agades_pqc_eval.template.toml "
        "prime_intellect/verifiers_environment/prime_manifest.json "
        "prime_intellect/schemas/attack_plan.schema.json "
        "prime_intellect/schemas/verifier_result.schema.json "
        "prime_intellect/schemas/schema_manifest.json "
        "prime_intellect/schemas/task_metadata.schema.json "
        "public/runbook_audit.json public/release_audit.json "
        "docs/release_status.json public/publication_preflight.json "
        "reports/ecosystem_smoke.json reports/hf_space_smoke.json "
        "reports/hf_space_launch_smoke.json "
        "reports/openevolve_smoke.json reports/prime_environment_smoke.json "
        "reports/nvidia_manifest_safety.json",
    ),
    ("check-whitespace", "git diff --check"),
    (
        "generate-private-run-policy",
        "uv run agades-pqc private-run-policy --out docs/private_run_policy.json",
    ),
    (
        "verify-private-run-policy",
        "uv run agades-pqc private-run-policy-verify --policy "
        "docs/private_run_policy.json",
    ),
    (
        "generate-private-dataset-curation",
        "uv run agades-pqc private-dataset-curation --out "
        "docs/private_dataset_curation.json",
    ),
    (
        "verify-private-dataset-curation",
        "uv run agades-pqc private-dataset-curation-verify --curation "
        "docs/private_dataset_curation.json",
    ),
    (
        "verify-runbook-input-manifest",
        "uv run agades-pqc runbook-input-manifest-verify --manifest "
        "docs/runbook_input_manifest.json",
    ),
    (
        "generate-deepevolve-manifest",
        "uv run agades-pqc deepevolve-manifest --out "
        "docs/deepevolve_research_hooks_manifest.json",
    ),
    (
        "verify-deepevolve-manifest",
        "uv run agades-pqc deepevolve-manifest-verify --manifest "
        "docs/deepevolve_research_hooks_manifest.json",
    ),
    (
        "generate-benchmark-source-contracts",
        "uv run agades-pqc benchmark-source-contracts --out "
        "docs/benchmark_source_contracts.json",
    ),
    (
        "verify-benchmark-source-contracts",
        "uv run agades-pqc benchmark-source-verify --contracts "
        "docs/benchmark_source_contracts.json",
    ),
    (
        "generate-family-registry-manifest",
        "uv run agades-pqc family-registry-manifest --out "
        "docs/family_registry_manifest.json",
    ),
    (
        "verify-family-registry-manifest",
        "uv run agades-pqc family-registry-manifest-verify --manifest "
        "docs/family_registry_manifest.json",
    ),
    (
        "generate-family-plugin-manifest",
        "uv run agades-pqc family-plugin-manifest --out "
        "docs/family_plugin_manifest.json",
    ),
    (
        "verify-family-plugin-manifest",
        "uv run agades-pqc family-plugin-manifest-verify --manifest "
        "docs/family_plugin_manifest.json",
    ),
    (
        "generate-family-support",
        "uv run agades-pqc family-support --out docs/family_support_matrix.json",
    ),
    (
        "verify-family-support",
        "uv run agades-pqc family-support-verify --matrix "
        "docs/family_support_matrix.json",
    ),
    (
        "generate-ecosystem-source-graph",
        "uv run agades-pqc ecosystem-source-graph --out "
        "docs/ecosystem_source_graph.json",
    ),
    (
        "verify-ecosystem-source-graph",
        "uv run agades-pqc ecosystem-source-graph-verify --graph "
        "docs/ecosystem_source_graph.json",
    ),
    (
        "generate-family-operator-catalog",
        "uv run agades-pqc family-operator-catalog --out "
        "docs/family_operator_catalog.json",
    ),
    (
        "verify-family-operator-catalog",
        "uv run agades-pqc family-operator-catalog-verify --catalog "
        "docs/family_operator_catalog.json",
    ),
    (
        "generate-formal-lean-backend",
        "uv run agades-pqc formal-lean-backend --out docs/formal_lean_backend.json",
    ),
    (
        "verify-formal-lean-backend",
        "uv run agades-pqc formal-lean-backend-verify --backend "
        "docs/formal_lean_backend.json",
    ),
    (
        "generate-hf-dataset",
        "uv run agades-pqc hf-dataset --out hf/dataset",
    ),
    (
        "verify-hf-dataset",
        "uv run agades-pqc hf-dataset-verify --dataset hf/dataset",
    ),
    (
        "generate-hf-space-manifest",
        "uv run agades-pqc hf-space-manifest --out hf/space_manifest.json",
    ),
    (
        "verify-hf-space-manifest",
        "uv run agades-pqc hf-space-manifest-verify --manifest hf/space_manifest.json",
    ),
    (
        "generate-hf-space-smoke",
        "uv run agades-pqc hf-space-smoke --out reports/hf_space_smoke.json",
    ),
    (
        "verify-hf-space-smoke",
        "uv run agades-pqc hf-space-smoke-verify --report reports/hf_space_smoke.json",
    ),
    (
        "generate-hf-space-launch-smoke",
        "uv run agades-pqc hf-space-launch-smoke --out "
        "reports/hf_space_launch_smoke.json",
    ),
    (
        "verify-hf-space-launch-smoke",
        "uv run agades-pqc hf-space-launch-smoke-verify --report "
        "reports/hf_space_launch_smoke.json",
    ),
    (
        "generate-hf-collection-manifest",
        "uv run agades-pqc hf-collection-manifest --out hf/collection_manifest.json",
    ),
    (
        "verify-hf-collection-manifest",
        "uv run agades-pqc hf-collection-manifest-verify --manifest "
        "hf/collection_manifest.json",
    ),
    (
        "generate-hf-publication-handoff",
        "uv run agades-pqc hf-publication-handoff --out "
        "docs/huggingface_publication_handoff.json",
    ),
    (
        "verify-hf-publication-handoff",
        "uv run agades-pqc hf-publication-handoff-verify --handoff "
        "docs/huggingface_publication_handoff.json",
    ),
    (
        "generate-lattice-estimator-manifest",
        "uv run agades-pqc lattice-estimator-manifest --out "
        "docs/lattice_estimator_manifest.json",
    ),
    (
        "verify-lattice-estimator-manifest",
        "uv run agades-pqc lattice-estimator-manifest-verify --manifest "
        "docs/lattice_estimator_manifest.json",
    ),
    (
        "generate-lattice-estimator-baseline-contracts",
        "uv run agades-pqc lattice-estimator-baseline-contracts --out "
        "docs/lattice_estimator_baseline_contracts.json",
    ),
    (
        "verify-lattice-estimator-baseline-contracts",
        "uv run agades-pqc lattice-estimator-baseline-contracts-verify "
        "--contracts docs/lattice_estimator_baseline_contracts.json",
    ),
    (
        "generate-nvidia-manifest",
        "uv run agades-pqc nvidia-manifest --out nvidia/accelerator_manifest.json",
    ),
    (
        "verify-nvidia-manifest",
        "uv run agades-pqc nvidia-manifest-verify --manifest "
        "nvidia/accelerator_manifest.json",
    ),
    (
        "generate-nvidia-manifest-safety",
        "uv run agades-pqc nvidia-manifest-safety --out "
        "reports/nvidia_manifest_safety.json",
    ),
    (
        "verify-nvidia-manifest-safety",
        "uv run agades-pqc nvidia-manifest-safety-verify --report "
        "reports/nvidia_manifest_safety.json",
    ),
    (
        "generate-nvidia-publication-handoff",
        "uv run agades-pqc nvidia-publication-handoff --out "
        "docs/nvidia_publication_handoff.json",
    ),
    (
        "verify-nvidia-publication-handoff",
        "uv run agades-pqc nvidia-publication-handoff-verify --handoff "
        "docs/nvidia_publication_handoff.json",
    ),
    (
        "generate-openevolve-config-template",
        "uv run agades-pqc openevolve-config --out examples/openevolve/config.yaml",
    ),
    (
        "verify-openevolve-config-template",
        "uv run agades-pqc openevolve-config-verify --config "
        "examples/openevolve/config.yaml",
    ),
    (
        "generate-openevolve-smoke-report",
        "uv run agades-pqc openevolve-smoke --out reports/openevolve_smoke.json",
    ),
    (
        "verify-openevolve-smoke-report",
        "uv run agades-pqc openevolve-smoke-verify --report "
        "reports/openevolve_smoke.json",
    ),
    (
        "generate-prime-manifest",
        "uv run agades-pqc prime-manifest --out "
        "prime_intellect/verifiers_environment/prime_manifest.json",
    ),
    (
        "verify-prime-manifest",
        "uv run agades-pqc prime-manifest-verify --manifest "
        "prime_intellect/verifiers_environment/prime_manifest.json",
    ),
    (
        "generate-prime-environment-smoke",
        "uv run agades-pqc prime-environment-smoke --out "
        "reports/prime_environment_smoke.json",
    ),
    (
        "verify-prime-environment-smoke",
        "uv run agades-pqc prime-environment-smoke-verify --report "
        "reports/prime_environment_smoke.json",
    ),
    (
        "generate-prime-eval-config",
        "uv run agades-pqc prime-eval-config --config "
        "prime_intellect/evals/agades_pqc_eval.template.toml --manifest "
        "docs/prime_eval_config_manifest.json",
    ),
    (
        "verify-prime-eval-config",
        "uv run agades-pqc prime-eval-config-verify --config "
        "prime_intellect/evals/agades_pqc_eval.template.toml --manifest "
        "docs/prime_eval_config_manifest.json",
    ),
    (
        "generate-pedagogical-rl-method",
        "uv run agades-pqc pedagogical-rl-method --out "
        "docs/pedagogical_rl_method.json",
    ),
    (
        "verify-pedagogical-rl-method",
        "uv run agades-pqc pedagogical-rl-method-verify --method "
        "docs/pedagogical_rl_method.json",
    ),
    (
        "generate-prime-schemas",
        "uv run agades-pqc prime-schemas --out prime_intellect/schemas",
    ),
    (
        "verify-prime-schemas",
        "uv run agades-pqc prime-schemas-verify --schemas prime_intellect/schemas",
    ),
    (
        "generate-prime-publication-handoff",
        "uv run agades-pqc prime-publication-handoff --out "
        "docs/prime_publication_handoff.json",
    ),
    (
        "verify-prime-publication-handoff",
        "uv run agades-pqc prime-publication-handoff-verify --handoff "
        "docs/prime_publication_handoff.json",
    ),
    (
        "generate-prime-speedrun-handoff",
        "uv run agades-pqc prime-speedrun-handoff --out "
        "docs/prime_speedrun_handoff.json",
    ),
    (
        "verify-prime-speedrun-handoff",
        "uv run agades-pqc prime-speedrun-handoff-verify --handoff "
        "docs/prime_speedrun_handoff.json",
    ),
    (
        "generate-public-benchmark-manifest",
        "uv run agades-pqc public-benchmark-manifest --out "
        "docs/public_benchmark_manifest.json",
    ),
    (
        "verify-public-benchmark",
        "uv run agades-pqc public-benchmark-verify --manifest "
        "docs/public_benchmark_manifest.json",
    ),
    (
        "generate-public-run-export",
        "uv run agades-pqc public-run-export --out public/run_export",
    ),
    (
        "verify-public-run-export",
        "uv run agades-pqc public-run-export-verify --export public/run_export",
    ),
    (
        "generate-publication-manifest",
        "uv run agades-pqc publication-manifest --out docs/publication_manifest.json",
    ),
    (
        "verify-publication-manifest",
        "uv run agades-pqc publication-manifest-verify --manifest "
        "docs/publication_manifest.json",
    ),
    (
        "converge-release-artifacts",
        "uv run agades-pqc release-artifacts --max-passes 6",
    ),
    (
        "generate-source-catalog",
        "uv run agades-pqc source-catalog --out docs/source_catalog.json",
    ),
    (
        "verify-source-catalog",
        "uv run agades-pqc source-catalog-verify --catalog docs/source_catalog.json",
    ),
    ("lint", "uv run --extra dev ruff check ."),
    ("tests", "uv run --extra dev pytest -q"),
)


def build_release_audit(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    checks = [
        _runbook_deliverables(project_root),
        _github_actions_ci(project_root),
        _hf_space_smoke(project_root),
        _hf_space_launch_smoke(project_root),
        _hf_space_manifest(project_root),
        _hf_collection_manifest(project_root),
        _hf_publication_handoff(project_root),
        _checksum_manifests(project_root),
        _multi_family_readiness(project_root),
        _family_registry_manifest(project_root),
        _family_plugin_manifest(project_root),
        _family_support_matrix(project_root),
        _ecosystem_source_graph(project_root),
        _family_operator_catalog(project_root),
        _schema_only_applicability_validators(project_root),
        _lattice_estimator_mapping_coverage(project_root),
        _lattice_runtime_primary_boundary(project_root),
        _lattice_estimator_pin(project_root),
        _lattice_estimator_baseline_contracts(project_root),
        _lattice_estimator_baseline_run_boundary(project_root),
        _lattice_estimator_checkout_preflight_boundary(project_root),
        _lattice_estimator_runtime_preflight_verifier(project_root),
        _hf_dataset_safety(project_root),
        _source_catalog_safety(project_root),
        _benchmark_source_contracts(project_root),
        _nvidia_manifest_safety(project_root),
        _nvidia_publication_handoff(project_root),
        _publication_manifest_safety(project_root),
        _external_publication_review_packet(project_root),
        _ecosystem_smoke_report(project_root),
        _release_gate_closure(project_root),
        _public_benchmark_manifest(project_root),
        _public_run_export(project_root),
        _evolution_heldout_rescore(project_root),
        _evolution_heldout_batch(project_root),
        _evolution_heldout_schedule(project_root),
        _evolution_heldout_schedule_run(project_root),
        _evolution_heldout_cron_plan(project_root),
        _private_evolution_campaign_plan(project_root),
        _evolution_archive_snapshot(project_root),
        _evolution_mutation_batch(project_root),
        _evolution_archive_mutation_batch(project_root),
        _openevolve_config_template(project_root),
        _openevolve_evaluator_smoke(project_root),
        _deepevolve_paper_card_injections(project_root),
        _deepevolve_research_hooks(project_root),
        _community_release_cards(project_root),
        _ecosystem_release_plans(project_root),
        _prime_environment_smoke(project_root),
        _prime_environment_manifest(project_root),
        _prime_eval_config(project_root),
        _pedagogical_rl_method(project_root),
        _private_dataset_curation(project_root),
        _prime_verifier_schemas(project_root),
        _prime_publication_handoff(project_root),
        _prime_speedrun_handoff(project_root),
        _prime_environment_json_only(project_root),
        _public_run_ledger_safety(project_root),
        _report_generator_redaction(project_root),
        _private_run_policy(project_root),
        _legacy_name_guard(project_root),
        _prime_hub_publication(project_root),
    ]
    return {
        "schema_version": RELEASE_AUDIT_SCHEMA,
        "project": {
            "name": "Agades PQC Gym",
            "package": "agades_pqc_gym",
            "repository": "https://github.com/AgadesTech/agades-pqc-gym",
        },
        "accepted": all(
            check["status"] != "failed" or check["blocking"] is False
            for check in checks
        ),
        "summary": _summary(checks),
        "checks": checks,
        "safety": {
            "contains_private_traces": False,
            "arbitrary_code_execution": False,
            "live_targeting": False,
            "security_claim": False,
            "publishes_private_candidates": False,
        },
    }


def _runbook_deliverables(root: Path) -> dict[str, Any]:
    runbook_audit = build_runbook_audit(root=root)
    public_runbook_audit = root / "public" / "runbook_audit.json"
    checks = {check["id"]: check for check in runbook_audit["checks"]}
    core = checks.get("runbook-family-agnostic-core", {}).get("evidence", {})
    ecosystem = checks.get("runbook-ecosystem-counts", {}).get("evidence", {})
    milestones = checks.get("runbook-milestone-coverage", {}).get("evidence", {})
    source_inputs = checks.get("runbook-source-input-manifest", {}).get(
        "evidence",
        {},
    )
    failures = [
        failure
        for check in runbook_audit["checks"]
        if check["status"] != "passed"
        for failure in check["failures"]
    ]
    public_runbook_audit_synced = False
    if not public_runbook_audit.is_file():
        failures.append("public/runbook_audit.json is not checked in.")
    else:
        public_runbook_audit_synced = _read_json(public_runbook_audit) == runbook_audit
        if not public_runbook_audit_synced:
            failures.append("public/runbook_audit.json is not in sync.")

    return _check(
        check_id="runbook-deliverables",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="runbook-required docs and public ecosystem artifacts",
        detail=(
            "Runbook-required architecture docs, collaboration briefs, HF/Prime/"
            "NVIDIA surfaces, machine-readable manifests, naming boundaries, "
            "and open-core safety boundaries are present and synchronized."
        ),
        evidence={
            "artifact_count": runbook_audit["summary"]["artifact_count"],
            "hf_attack_plan_rows": ecosystem.get("hf_attack_plan_rows"),
            "hf_valid_attack_plan_rows": ecosystem.get("hf_valid_attack_plan_rows"),
            "hf_invalid_attack_plan_rows": ecosystem.get("hf_invalid_attack_plan_rows"),
            "hf_task_metadata_rows": ecosystem.get("hf_task_metadata_rows"),
            "nvidia_workloads": ecosystem.get("nvidia_workloads"),
            "prime_tasks": ecosystem.get("prime_tasks"),
            "prime_tasks_match_hf_task_metadata_rows": ecosystem.get(
                "prime_tasks_match_hf_task_metadata_rows"
            ),
            "public_records": ecosystem.get("public_records"),
            "public_runbook_audit_checks": len(runbook_audit["checks"]),
            "public_runbook_audit_synced": public_runbook_audit_synced,
            "public_run_bundles": ecosystem.get("public_run_bundles"),
            "runbook_core_symbol_import_count": core.get("core_symbol_import_count"),
            "runbook_core_symbol_count": core.get("core_symbol_count"),
            "runbook_family_plugin_module_count": sum(
                len(paths)
                for paths in _dict_or_empty(core.get("family_plugin_modules")).values()
                if isinstance(paths, list)
            ),
            "runbook_family_plugin_module_digest_count": core.get(
                "family_plugin_module_digest_count"
            ),
            "runbook_family_plugin_module_import_count": core.get(
                "family_plugin_module_import_count"
            ),
            "runbook_family_plugin_count": core.get("family_plugin_count"),
            "runbook_family_registry_family_count_matches_plugin_manifest": core.get(
                "family_registry_family_count_matches_plugin_manifest"
            ),
            "runbook_family_registry_plugin_count_matches_plugin_manifest": core.get(
                "family_registry_plugin_count_matches_plugin_manifest"
            ),
            "runbook_family_registry_plugin_manifest_module_digest_count": core.get(
                "family_registry_plugin_manifest_module_digest_count"
            ),
            "runbook_family_registry_plugin_manifest_synced": core.get(
                "family_registry_plugin_manifest_synced"
            ),
            "runbook_family_registry_runtime_adapter_entries_match_plugin_manifest": (
                core.get(
                    "family_registry_runtime_adapter_entries_match_plugin_manifest"
                )
            ),
            "runbook_failed_milestones": milestones.get("failed_milestones"),
            "runbook_milestone_ids": milestones.get("milestone_ids"),
            "runbook_milestone_count": milestones.get("milestone_count"),
            "runbook_passed_milestones": milestones.get("passed_milestones"),
            "runbook_project_context_sha256": source_inputs.get(
                "project_context_sha256"
            ),
            "runbook_source_brief_sha256": source_inputs.get("source_brief_sha256"),
            "runbook_source_input_count": source_inputs.get("input_count"),
            "runbook_source_input_ids": source_inputs.get("source_input_ids"),
        },
        failures=failures,
    )


def _hf_space_smoke(root: Path) -> dict[str, Any]:
    verification = verify_huggingface_space_smoke_report(
        Path("reports/hf_space_smoke.json"),
        root=root,
    )
    summary = verification["summary"]
    failures = list(verification["failures"])

    return _check(
        check_id="hf-space-smoke",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="reports/hf_space_smoke.json",
        detail=(
            "Hugging Face Space smoke report proves the app imports without "
            "requiring Gradio, loads public examples, and evaluates the "
            "default AttackPlan safely."
        ),
        evidence={
            "default_label": summary["default_label"],
            "example_count": summary["example_count"],
            "imports_without_gradio": summary["imports_without_gradio"],
            "summary_contains_not_security_claim": summary[
                "summary_contains_not_security_claim"
            ],
            "uses_shared_verifier": summary["uses_shared_verifier"],
        },
        failures=failures,
    )


def _hf_space_launch_smoke(root: Path) -> dict[str, Any]:
    verification = verify_huggingface_space_launch_smoke_report(
        Path("reports/hf_space_launch_smoke.json"),
        root=root,
    )
    summary = verification["summary"]
    failures = list(verification["failures"])

    return _check(
        check_id="hf-space-launch-smoke",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="reports/hf_space_launch_smoke.json",
        detail=(
            "Hugging Face Space launch smoke builds the Gradio Blocks UI and "
            "verifies the public Agent Environment API endpoints."
        ),
        evidence={
            "agent_environment_api_names_present": summary[
                "agent_environment_api_names_present"
            ],
            "component_count": summary["component_count"],
            "demo_class": summary["demo_class"],
            "gradio_available": summary["gradio_available"],
            "required_api_names_present": summary["required_api_names_present"],
            "title": summary["title"],
        },
        failures=failures,
    )


def _hf_space_manifest(root: Path) -> dict[str, Any]:
    path = root / "hf" / "space_manifest.json"
    verification = verify_huggingface_space_manifest(path, root=root)
    failures = list(verification["failures"])
    if path.is_file():
        try:
            manifest = _read_json(path)
        except json.JSONDecodeError:
            manifest = {}
    else:
        manifest = {}
    examples = manifest.get("example_manifest", {})
    if not isinstance(examples, dict):
        examples = {}
    space = manifest.get("space", {})
    if not isinstance(space, dict):
        space = {}

    return _check(
        check_id="hf-space-manifest",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="hf/space_manifest.json",
        detail=(
            "Hugging Face Space manifest is checked in, synchronized with the "
            "Space example selector, and documents the no-code/no-claim verifier "
            "contract."
        ),
        evidence={
            "dataset_attack_plan_count": examples.get("dataset_attack_plan_count"),
            "dataset_valid_attack_plan_count": examples.get(
                "dataset_valid_attack_plan_count"
            ),
            "dataset_invalid_attack_plan_count": examples.get(
                "dataset_invalid_attack_plan_count"
            ),
            "default_label": examples.get("default_label"),
            "example_count": examples.get("example_count"),
            "excluded_attack_plan_ids": examples.get("excluded_attack_plan_ids", []),
            "families": examples.get("families", []),
            "hub_create_command_template": space.get("hub_create_command_template"),
            "hub_upload_command_template": space.get("hub_upload_command_template"),
            "labels_match_valid_dataset_rows": examples.get(
                "labels_match_valid_dataset_rows"
            ),
        },
        failures=failures,
    )


def _hf_collection_manifest(root: Path) -> dict[str, Any]:
    path = root / "hf" / "collection_manifest.json"
    verification = verify_huggingface_collection_manifest(path, root=root)
    failures = list(verification["failures"])
    if path.is_file():
        try:
            manifest = _read_json(path)
        except json.JSONDecodeError:
            manifest = {}
    else:
        manifest = {}

    collection = manifest.get("collection", {})
    if not isinstance(collection, dict):
        collection = {}
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        entries = []
    safety = manifest.get("safety", {})
    if not isinstance(safety, dict):
        safety = {}
    entry_ids = [
        entry.get("id")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    ]
    credentialed_entries = sorted(
        entry["id"]
        for entry in entries
        if isinstance(entry, dict)
        and isinstance(entry.get("id"), str)
        and entry.get("requires_credentials") is True
    )
    review_required_entries = sum(
        1
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("review_required_before_publish") is True
    )

    return _check(
        check_id="hf-collection-manifest",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="hf/collection_manifest.json",
        detail=(
            "Hugging Face Collection manifest is checked in, synchronized, and "
            "keeps GitHub, dataset, Space, benchmark, source-map, and public "
            "benchmark links behind review/no-claim boundaries."
        ),
        evidence={
            "contains_private_traces": safety.get("contains_private_traces"),
            "credentialed_entries": credentialed_entries,
            "entries": entry_ids,
            "entry_count": len(entries),
            "external_publication_requires_review": safety.get(
                "external_publication_requires_review"
            ),
            "public_push_requires_review": collection.get(
                "public_push_requires_review"
            ),
            "review_required_entries": review_required_entries,
            "security_claim": safety.get("security_claim"),
            "suggested_slug": collection.get("suggested_slug"),
            "suggested_title": collection.get("suggested_title"),
        },
        failures=failures,
    )


def _hf_publication_handoff(root: Path) -> dict[str, Any]:
    path = root / "docs" / "huggingface_publication_handoff.json"
    verification = verify_huggingface_publication_handoff(path, root=root)
    summary = verification["summary"]

    return _check(
        check_id="hf-publication-handoff",
        status="failed" if verification["failures"] else "passed",
        blocking=True,
        artifact="docs/huggingface_publication_handoff.json",
        detail=(
            "Hugging Face publication handoff is checked in, synchronized with "
            "the local dataset, Space, and Collection artifacts, and keeps Hub "
            "publication behind credentials and release review."
        ),
        evidence={
            "artifact_count": summary["artifact_count"],
            "attack_plan_count": summary["attack_plan_count"],
            "collection_entry_count": summary["collection_entry_count"],
            "external_publication_requires_review": summary[
                "external_publication_requires_review"
            ],
            "public_run_bundles": summary["public_run_bundles"],
            "space_example_count": summary["space_example_count"],
            "task_metadata_rows": summary["task_metadata_rows"],
            "valid_attack_plan_count": summary["valid_attack_plan_count"],
        },
        failures=list(verification["failures"]),
    )


def _checksum_manifests(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    verified_entries = 0
    public_checksum_manifests = _public_checksum_manifests(root)

    for relative_manifest in public_checksum_manifests:
        manifest_path = root / relative_manifest
        if not manifest_path.is_file():
            failures.append(f"Checksum manifest is missing: {relative_manifest}")
            continue

        manifest_root = manifest_path.parent
        for line_number, raw_line in enumerate(
            manifest_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not raw_line.strip():
                continue
            parsed = _parse_sha256_manifest_line(raw_line)
            if parsed is None:
                failures.append(
                    f"{relative_manifest}:{line_number} is not '<sha256>  <path>'."
                )
                continue
            expected_digest, relative_file = parsed
            candidate = (manifest_root / relative_file).resolve()
            try:
                candidate.relative_to(manifest_root.resolve())
            except ValueError:
                failures.append(
                    f"{relative_manifest}:{line_number} escapes its manifest root."
                )
                continue
            if not candidate.is_file():
                failures.append(
                    f"{relative_manifest}:{line_number} target is missing: "
                    f"{relative_file}"
                )
                continue
            actual_digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if actual_digest != expected_digest:
                failures.append(
                    f"{relative_manifest}:{line_number} checksum mismatch for "
                    f"{relative_file}."
                )
                continue
            verified_entries += 1

    return _check(
        check_id="checksum-manifests",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="public checksum manifests",
        detail=(
            "Checked-in Hugging Face and public-run checksum manifests are "
            "present, parseable, root-confined, and synchronized with files."
        ),
        evidence={
            "manifests": public_checksum_manifests,
            "verified_entries": verified_entries,
        },
        failures=failures,
    )


def _public_checksum_manifests(root: Path) -> list[str]:
    manifests = [
        path.relative_to(root).as_posix()
        for parent in (
            root / "examples" / "public_runs",
            root / "hf" / "dataset" / "public_runs",
        )
        if parent.is_dir()
        for path in sorted(parent.glob("*/MANIFEST.sha256"))
    ]
    hf_dataset_manifest = root / "hf" / "dataset" / "MANIFEST.sha256"
    if hf_dataset_manifest.is_file():
        manifests.append(hf_dataset_manifest.relative_to(root).as_posix())
    public_run_export_manifest = root / "public" / "run_export" / "MANIFEST.sha256"
    if public_run_export_manifest.is_file():
        manifests.append(public_run_export_manifest.relative_to(root).as_posix())
    return sorted(manifests)


def _github_actions_ci(root: Path) -> dict[str, Any]:
    workflow_path = root / ".github" / "workflows" / "ci.yml"
    failures: list[str] = []
    run_commands: list[str] = []
    used_actions: list[str] = []
    lean_gate_inputs: dict[str, Any] | None = None
    jobs: dict[str, Any] = {}
    triggers: Any = None

    if not workflow_path.is_file():
        failures.append("GitHub Actions CI workflow is missing.")
    else:
        try:
            workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            workflow = None
            failures.append(f"GitHub Actions CI workflow is invalid YAML: {exc}.")

        if not isinstance(workflow, dict):
            failures.append("GitHub Actions CI workflow must be a mapping.")
        else:
            triggers = workflow.get("on", workflow.get(True))
            jobs = workflow.get("jobs", {})
            if not _workflow_has_trigger(triggers, "push"):
                failures.append("GitHub Actions CI workflow does not run on push.")
            if not _workflow_has_trigger(triggers, "pull_request"):
                failures.append(
                    "GitHub Actions CI workflow does not run on pull_request."
                )
            if not isinstance(jobs, dict) or not jobs:
                failures.append("GitHub Actions CI workflow has no jobs.")
                jobs = {}

            for step in _workflow_steps(jobs):
                run = step.get("run")
                if isinstance(run, str):
                    run_commands.extend(_normalized_run_commands(run))
                uses = step.get("uses")
                if isinstance(uses, str):
                    used_actions.append(uses)
                    if uses.startswith("leanprover/lean-action@"):
                        step_inputs = step.get("with", {})
                        lean_gate_inputs = (
                            dict(step_inputs) if isinstance(step_inputs, dict) else {}
                        )

    for action in GITHUB_ACTIONS_REQUIRED_ACTIONS:
        if not any(used_action.startswith(action) for used_action in used_actions):
            failures.append(f"GitHub Actions CI workflow does not use {action}.")

    if lean_gate_inputs is None:
        failures.append("GitHub Actions CI workflow is missing the Lean build gate.")
    else:
        for input_name, expected_value in (
            GITHUB_ACTIONS_LEAN_GATE_REQUIRED_INPUTS.items()
        ):
            actual_value = lean_gate_inputs.get(input_name)
            if actual_value != expected_value:
                failures.append(
                    "GitHub Actions CI Lean build gate has invalid input "
                    f"{input_name}: expected {expected_value!r}, got {actual_value!r}."
                )

    for command_id, required_command in GITHUB_ACTIONS_REQUIRED_COMMANDS:
        normalized = " ".join(required_command.split())
        if normalized not in run_commands:
            failures.append(
                f"GitHub Actions CI workflow is missing command "
                f"{command_id}: {required_command}"
            )

    return _check(
        check_id="github-actions-ci",
        status="failed" if failures else "passed",
        blocking=True,
        artifact=".github/workflows/ci.yml",
        detail=(
            "GitHub Actions CI runs tests, lint, public artifact sync checks, "
            "release audit, and Python/Prime package builds."
        ),
        evidence={
            "jobs": sorted(jobs) if isinstance(jobs, dict) else [],
            "required_actions": list(GITHUB_ACTIONS_REQUIRED_ACTIONS),
            "lean_gate_required_inputs": dict(GITHUB_ACTIONS_LEAN_GATE_REQUIRED_INPUTS),
            "lean_gate_inputs": lean_gate_inputs or {},
            "required_commands": [
                command_id for command_id, _ in GITHUB_ACTIONS_REQUIRED_COMMANDS
            ],
        },
        failures=failures,
    )


def _multi_family_readiness(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    plugin_root = root / "src" / "agades_pqc_gym" / "families"
    example_families, example_failures = _valid_public_example_families(root)
    benchmark_families, benchmark_failures = _benchmark_target_families(root)
    failures.extend(example_failures)
    failures.extend(benchmark_failures)

    ready_plugins: list[str] = []
    for plugin, requirements in FAMILY_READINESS_REQUIREMENTS.items():
        plugin_path = plugin_root / plugin
        missing_files = sorted(
            filename
            for filename in requirements["required_files"]
            if not (plugin_path / filename).is_file()
        )
        if missing_files:
            failures.append(f"{plugin} plugin missing files: {missing_files}")
            continue

        missing_example_families = sorted(
            requirements["target_families"] - example_families
        )
        if missing_example_families:
            failures.append(
                f"{plugin} lacks valid public examples for {missing_example_families}"
            )

        missing_benchmark_dirs = sorted(
            directory
            for directory in requirements["benchmark_dirs"]
            if not _benchmark_dir_ready(root / directory)
        )
        if missing_benchmark_dirs:
            failures.append(
                f"{plugin} benchmark dirs are incomplete: {missing_benchmark_dirs}"
            )

        missing_benchmark_families = sorted(
            requirements["target_families"] - benchmark_families
        )
        if missing_benchmark_families:
            failures.append(
                f"{plugin} lacks benchmark targets for {missing_benchmark_families}"
            )

        if (
            not missing_example_families
            and not missing_benchmark_dirs
            and not missing_benchmark_families
        ):
            ready_plugins.append(plugin)

    return _check(
        check_id="multi-family-readiness",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="src/agades_pqc_gym/families",
        detail=(
            "Every planned family plugin has source files, valid public examples, "
            "and benchmark coverage without claiming unsupported estimates."
        ),
        evidence={
            "plugins": sorted(ready_plugins),
            "example_families": sorted(example_families),
            "benchmark_families": sorted(benchmark_families),
        },
        failures=failures,
    )


def _family_support_matrix(root: Path) -> dict[str, Any]:
    expected = build_family_support_matrix(root=root)
    path = root / "docs" / "family_support_matrix.json"
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "families": 0,
        "implemented": [],
        "schema_only": [],
        "toy_evaluators": [],
    }

    if not path.is_file():
        failures.append("Family support matrix is not checked in.")
    else:
        matrix = _read_json(path)
        if matrix != expected:
            failures.append("Family support matrix is not in sync.")
        verification = verify_family_support_matrix(path, root=root)
        failures.extend(verification["failures"])
        summary = verification["summary"]
        evidence = {
            "benchmarks": summary["benchmark_count"],
            "cross_family_review_source_count": summary[
                "cross_family_review_source_count"
            ],
            "families": summary["family_count"],
            "families_with_future_reviewed_adapters": summary[
                "families_with_future_reviewed_adapters"
            ],
            "implemented": summary["implemented"],
            "plugins": summary["plugins"],
            "plugin_count": summary["plugin_count"],
            "public_examples": summary["public_example_count"],
            "review_required_before_claims": summary["review_required_before_claims"],
            "schema_only": summary["schema_only"],
            "support_level_counts": summary["support_level_counts"],
            "toy_evaluators": summary["toy_evaluators"],
            "unique_future_reviewed_adapter_source_count": summary[
                "unique_future_reviewed_adapter_source_count"
            ],
        }

    return _check(
        check_id="family-support-matrix",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="docs/family_support_matrix.json",
        detail=(
            "Family support matrix is checked in, synchronized, and does not "
            "overstate non-reviewed family support."
        ),
        evidence=evidence,
        failures=failures,
    )


def _family_registry_manifest(root: Path) -> dict[str, Any]:
    expected = build_family_registry_manifest(root=root)
    path = root / "docs" / "family_registry_manifest.json"
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "applicability_validator_entries": 0,
        "distinct_applicability_validators": 0,
        "families": 0,
        "implemented": [],
        "lattice_estimator_external_enabled": [],
        "lattice_validator_families": [],
        "non_lattice_applicability_validators": 0,
        "operator_review_boundaries": {},
        "plugin_manifest_family_count": 0,
        "plugin_manifest_implementation_module_count": 0,
        "plugin_manifest_implementation_module_digest_count": 0,
        "plugin_manifest_implementation_module_import_count": 0,
        "plugin_manifest_plugin_count": 0,
        "plugin_manifest_runtime_adapter_entries": 0,
        "plugin_manifest_synced": False,
        "plugins": 0,
        "registry_family_count_matches_plugin_manifest": False,
        "registry_plugin_count_matches_plugin_manifest": False,
        "registry_runtime_adapter_entries_match_plugin_manifest": False,
        "runtime_adapter_entries": 0,
        "schema_only": [],
        "toy_evaluators": [],
    }

    if not path.is_file():
        failures.append("Family registry manifest is not checked in.")
    else:
        manifest = _read_json(path)
        if manifest != expected:
            failures.append("Family registry manifest is not in sync.")
        verification = verify_family_registry_manifest(path, root=root)
        failures.extend(verification["failures"])
        summary = verification["summary"]
        evidence = {
            "applicability_validator_entries": summary[
                "applicability_validator_entries"
            ],
            "distinct_applicability_validators": summary[
                "distinct_applicability_validators"
            ],
            "families": summary["family_count"],
            "implemented": summary["implemented"],
            "lattice_estimator_external_enabled": summary[
                "lattice_estimator_external_enabled"
            ],
            "lattice_validator_families": summary["lattice_validator_families"],
            "non_lattice_applicability_validators": summary[
                "non_lattice_applicability_validators"
            ],
            "operator_review_boundaries": _operator_review_boundary_counts(manifest),
            "plugin_manifest_family_count": summary["plugin_manifest_family_count"],
            "plugin_manifest_implementation_module_count": summary[
                "plugin_manifest_implementation_module_count"
            ],
            "plugin_manifest_implementation_module_digest_count": summary[
                "plugin_manifest_implementation_module_digest_count"
            ],
            "plugin_manifest_implementation_module_import_count": summary[
                "plugin_manifest_implementation_module_import_count"
            ],
            "plugin_manifest_plugin_count": summary["plugin_manifest_plugin_count"],
            "plugin_manifest_runtime_adapter_entries": summary[
                "plugin_manifest_runtime_adapter_entries"
            ],
            "plugin_manifest_synced": summary["plugin_manifest_synced"],
            "plugins": summary["plugin_count"],
            "registry_family_count_matches_plugin_manifest": summary[
                "registry_family_count_matches_plugin_manifest"
            ],
            "registry_plugin_count_matches_plugin_manifest": summary[
                "registry_plugin_count_matches_plugin_manifest"
            ],
            "registry_runtime_adapter_entries_match_plugin_manifest": summary[
                "registry_runtime_adapter_entries_match_plugin_manifest"
            ],
            "runtime_adapter_entries": summary["runtime_adapter_entries"],
            "schema_only": summary["schema_only"],
            "toy_evaluators": summary["toy_evaluators"],
        }

    return _check(
        check_id="family-registry-manifest",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="docs/family_registry_manifest.json",
        detail=(
            "Family registry manifest is checked in, synchronized with the "
            "runtime adapters, and proves that Lattice Estimator access is not "
            "silently exposed as a universal PQC route."
        ),
        evidence=evidence,
        failures=failures,
    )


def _operator_review_boundary_counts(manifest: dict[str, Any]) -> dict[str, Any]:
    families = manifest.get("families")
    if not isinstance(families, list):
        return {}

    counts: dict[str, Any] = {}
    for family_entry in families:
        if not isinstance(family_entry, dict):
            continue
        family = family_entry.get("family")
        boundary = family_entry.get("operator_review_boundary")
        if not isinstance(family, str) or not isinstance(boundary, dict):
            continue
        counts[family] = {
            "catalog_operator_types": _list_count(
                boundary.get("catalog_operator_types")
            ),
            "catalog_variant_entries": boundary.get("catalog_variant_entries"),
            "external_estimator_operator_types": _list_count(
                boundary.get("external_estimator_operator_types")
            ),
            "runtime_operator_types": _list_count(
                boundary.get("runtime_operator_types")
            ),
            "runtime_without_catalog_operator_types": _list_count(
                boundary.get("runtime_without_catalog_operator_types")
            ),
        }
    return dict(sorted(counts.items()))


def _list_count(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _family_plugin_manifest(root: Path) -> dict[str, Any]:
    expected = build_family_plugin_manifest(root=root)
    path = root / "docs" / "family_plugin_manifest.json"
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "families": 0,
        "implemented": [],
        "implementation_module_digest_count": 0,
        "implementation_module_count": 0,
        "implementation_module_import_count": 0,
        "lattice_plugin_families": [],
        "non_lattice_plugin_count": 0,
        "plugins": 0,
        "runtime_adapter_entries": 0,
        "runbook_module_digest_count": 0,
        "runbook_module_digests_match": False,
        "schema_only": [],
        "toy_evaluators": [],
    }

    if not path.is_file():
        failures.append("Family plugin manifest is not checked in.")
    else:
        manifest = _read_json(path)
        if manifest != expected:
            failures.append("Family plugin manifest is not in sync.")
        verification = verify_family_plugin_manifest(path, root=root)
        failures.extend(verification["failures"])
        summary = verification["summary"]
        manifest_digests = _family_plugin_manifest_module_digests(manifest)
        runbook_digests = _runbook_family_plugin_module_digests(root)
        runbook_digest_count = _nested_digest_count(runbook_digests)
        digests_match = manifest_digests == runbook_digests
        if not digests_match:
            failures.append(
                "Family plugin manifest digests do not match public runbook "
                "audit digests."
            )
        evidence = {
            "families": summary["family_count"],
            "implemented": summary["implemented"],
            "implementation_module_digest_count": summary[
                "implementation_module_digest_count"
            ],
            "implementation_module_count": summary["implementation_module_count"],
            "implementation_module_import_count": summary[
                "implementation_module_import_count"
            ],
            "lattice_plugin_families": summary["lattice_plugin_families"],
            "non_lattice_plugin_count": summary["non_lattice_plugin_count"],
            "plugins": summary["plugin_count"],
            "runtime_adapter_entries": summary["runtime_adapter_entries"],
            "runbook_module_digest_count": runbook_digest_count,
            "runbook_module_digests_match": digests_match,
            "schema_only": summary["schema_only"],
            "toy_evaluators": summary["toy_evaluators"],
        }

    return _check(
        check_id="family-plugin-manifest",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="docs/family_plugin_manifest.json",
        detail=(
            "Family plugin manifest is checked in, synchronized with plugin "
            "descriptors and runtime adapters, and records that non-lattice "
            "plugins own their validators."
        ),
        evidence=evidence,
        failures=failures,
    )


def _family_plugin_manifest_module_digests(
    manifest: dict[str, Any],
) -> dict[str, dict[str, str]]:
    digests: dict[str, dict[str, str]] = {}
    for plugin in _list_or_empty(manifest.get("plugins")):
        if not isinstance(plugin, dict):
            continue
        name = plugin.get("plugin")
        module_digests = plugin.get("implementation_module_digests")
        if isinstance(name, str) and isinstance(module_digests, dict):
            digests[name] = {
                path: digest
                for path, digest in module_digests.items()
                if isinstance(path, str) and isinstance(digest, str)
            }
    return dict(sorted(digests.items()))


def _runbook_family_plugin_module_digests(root: Path) -> dict[str, dict[str, str]]:
    path = root / "public" / "runbook_audit.json"
    if not path.is_file():
        return {}
    runbook = _read_json(path)
    checks = {
        check.get("id"): check
        for check in _list_or_empty(runbook.get("checks"))
        if isinstance(check, dict)
    }
    evidence = _dict_or_empty(
        _dict_or_empty(checks.get("runbook-family-agnostic-core")).get("evidence")
    )
    digests = evidence.get("family_plugin_module_digests")
    if not isinstance(digests, dict):
        return {}
    return {
        family: {
            path: digest
            for path, digest in _dict_or_empty(family_digests).items()
            if isinstance(path, str) and isinstance(digest, str)
        }
        for family, family_digests in sorted(digests.items())
        if isinstance(family, str)
    }


def _nested_digest_count(digests: dict[str, dict[str, str]]) -> int:
    return sum(len(family_digests) for family_digests in digests.values())


def _family_operator_catalog(root: Path) -> dict[str, Any]:
    expected = build_family_operator_catalog(root=root)
    path = root / "docs" / "family_operator_catalog.json"
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "applicability_validator_count": 0,
        "families": 0,
        "families_with_operator_entries": [],
        "lattice_estimator_operator_entries": 0,
        "non_lattice_lattice_estimator_operator_entries": 0,
        "operator_entries": 0,
        "schema_only_families": [],
        "schema_only_operator_entries": 0,
        "support_level_counts": {},
        "toy_evaluator_families": [],
    }

    if not path.is_file():
        failures.append("Family operator catalog is not checked in.")
    else:
        catalog = _read_json(path)
        if catalog != expected:
            failures.append("Family operator catalog is not in sync.")
        verification = verify_family_operator_catalog(path, root=root)
        failures.extend(verification["failures"])
        summary = verification["summary"]
        evidence = {key: summary[key] for key in evidence}

    return _check(
        check_id="family-operator-catalog",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="docs/family_operator_catalog.json",
        detail=(
            "Family operator catalog is checked in, synchronized, and records "
            "family-specific validators, estimators, fixture scopes, and review "
            "gates without treating the Lattice Estimator as a universal PQC "
            "oracle."
        ),
        evidence=evidence,
        failures=failures,
    )


def _schema_only_applicability_validators(root: Path) -> dict[str, Any]:
    cases: tuple[tuple[str, tuple[Any, ...], Any, str, str], ...] = (
        (
            "examples/attack_plans/code_based_isd_placeholder.json",
            ("target", "k"),
            17669,
            "CODE_BASED target k must be smaller than n",
            "CODE_BASED",
        ),
        (
            "examples/attack_plans/multivariate_minrank_placeholder.json",
            ("target", "field"),
            "Zmod(16)",
            "MULTIVARIATE field must use GF(q) notation",
            "MULTIVARIATE",
        ),
        (
            "examples/attack_plans/hash_based_bound_placeholder.json",
            ("target", "hash_function"),
            "MD5",
            "HASH_BASED hash_function must be one of",
            "HASH_BASED",
        ),
        (
            "examples/attack_plans/implementation_security_constant_time_placeholder.json",
            ("operators", 0, "assumptions"),
            [],
            "IMPLEMENTATION_SECURITY schema-only operator constant_time_check "
            "must include schema_only_no_estimator",
            "IMPLEMENTATION_SECURITY",
        ),
        (
            "examples/attack_plans/implementation_security_constant_time_placeholder.json",
            ("target", "name"),
            "kyber_reference_constant_time",
            "IMPLEMENTATION_SECURITY target name must identify a schema-only fixture",
            "IMPLEMENTATION_SECURITY",
        ),
        (
            "examples/attack_plans/implementation_security_constant_time_placeholder.json",
            ("target", "name"),
            "schema_kyber_reference_constant_time",
            "IMPLEMENTATION_SECURITY target name must identify a schema-only fixture",
            "IMPLEMENTATION_SECURITY",
        ),
        (
            "examples/attack_plans/implementation_security_constant_time_placeholder.json",
            ("operators", 0, "params", "tool"),
            "dudect",
            "IMPLEMENTATION_SECURITY schema-only operator constant_time_check "
            "requires placeholder parameter tool ending in _schema_placeholder",
            "IMPLEMENTATION_SECURITY",
        ),
        (
            "examples/attack_plans/implementation_security_constant_time_placeholder.json",
            ("operators", 0, "params", "binary_path"),
            "build/kyber_kat",
            "IMPLEMENTATION_SECURITY schema-only plans must not reference "
            "executable/live artifact parameter binary_path",
            "IMPLEMENTATION_SECURITY",
        ),
        (
            "examples/attack_plans/isogeny_historical_placeholder.json",
            ("operators", 0, "assumptions"),
            ["schema_only_no_estimator"],
            "ISOGENY_HISTORICAL plans require historical_not_current_standard",
            "ISOGENY_HISTORICAL",
        ),
    )
    failures: list[str] = []
    covered_families: set[str] = set()

    for relative_path, mutation_path, value, expected_error, family in cases:
        plan = AttackPlan.model_validate_json(
            (root / relative_path).read_text(encoding="utf-8")
        )
        data = plan.model_dump(mode="json")
        _set_nested_value(data, mutation_path, value)
        validation = validate_attack_plan(AttackPlan.model_validate(data))
        if validation.valid:
            failures.append(
                f"{family} applicability validator accepted invalid fixture."
            )
            continue
        if not any(expected_error in error for error in validation.errors):
            failures.append(
                f"{family} applicability validator did not report {expected_error!r}."
            )
            continue
        covered_families.add(family)

    return _check(
        check_id="schema-only-applicability-validators",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="src/agades_pqc_gym/families",
        detail=(
            "Schema-only non-lattice family adapters enforce family-specific "
            "applicability boundaries while still refusing cryptanalytic estimates."
        ),
        evidence={
            "families": sorted(covered_families),
            "invalid_cases": len(cases),
        },
        failures=failures,
    )


def _lattice_estimator_mapping_coverage(root: Path) -> dict[str, Any]:
    mappings = reviewed_lwe_estimator_mappings()
    attack_types = set(mappings)
    example_sources: dict[str, str] = {}
    hf_sources: set[str] = set()
    prime_sources: set[str] = set()
    failures: list[str] = []

    for path in sorted((root / "examples" / "attack_plans").glob("*.json")):
        if path.name.startswith("invalid_"):
            continue
        try:
            data = _read_json(path)
        except json.JSONDecodeError as exc:
            failures.append(f"{path.relative_to(root)} is invalid JSON: {exc}")
            continue
        mapped_types = _mapped_attack_types_from_json(data, attack_types)
        if not mapped_types:
            continue
        if data.get("metadata", {}).get("public") is not True:
            failures.append(
                f"{path.relative_to(root)} covers mapped LWE attacks but is not public."
            )
            continue
        if data.get("target", {}).get("family") != "LWE":
            failures.append(
                f"{path.relative_to(root)} covers mapped LWE attacks but is not LWE."
            )
            continue
        for attack_type in mapped_types:
            example_sources.setdefault(attack_type, str(path.relative_to(root)))

    for row in _read_jsonl(root / "hf" / "dataset" / "attack_plans.jsonl"):
        attack_plan = row.get("attack_plan")
        if not isinstance(attack_plan, dict):
            continue
        if _mapped_attack_types_from_json(attack_plan, attack_types):
            source_path = row.get("source_path")
            if isinstance(source_path, str):
                hf_sources.add(source_path)

    for path in sorted(
        (root / "prime_intellect" / "verifiers_environment" / "data").glob("*.json")
    ):
        try:
            data = _read_json(path)
        except json.JSONDecodeError as exc:
            failures.append(f"{path.relative_to(root)} is invalid JSON: {exc}")
            continue
        if _mapped_attack_types_from_json(data, attack_types):
            prime_sources.add(path.name)

    for attack_type, algorithm_key in sorted(mappings.items()):
        source_path = example_sources.get(attack_type)
        if source_path is None:
            failures.append(
                f"No public LWE example covers {attack_type} -> {algorithm_key}."
            )
            continue
        if source_path not in hf_sources:
            failures.append(f"Hugging Face dataset lacks {source_path}.")
        if Path(source_path).name not in prime_sources:
            failures.append(f"Prime environment lacks {Path(source_path).name}.")

    covered_attack_types = [
        attack_type
        for attack_type, _ in sorted(
            mappings.items(),
            key=lambda item: item[1],
        )
        if (
            (source_path := example_sources.get(attack_type)) is not None
            and source_path in hf_sources
            and Path(source_path).name in prime_sources
        )
    ]
    covered_algorithm_keys = [
        mappings[attack_type] for attack_type in covered_attack_types
    ]

    return _check(
        check_id="lattice-estimator-mapping-coverage",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="examples/attack_plans + hf/dataset + prime_intellect",
        detail=(
            "Every reviewed direct LWE Lattice Estimator mapping has a public "
            "toy AttackPlan, a Hugging Face dataset row, and a packaged Prime "
            "Verifier task."
        ),
        evidence={
            "covered_algorithm_keys": covered_algorithm_keys,
            "covered_attack_types": covered_attack_types,
            "hf_rows": len(
                {
                    source
                    for source in hf_sources
                    if source in set(example_sources.values())
                }
            ),
            "prime_tasks": len(
                {
                    Path(source).name
                    for source in example_sources.values()
                    if Path(source).name in prime_sources
                }
            ),
            "public_examples": len(example_sources),
        },
        failures=failures,
    )


def _lattice_runtime_primary_boundary(root: Path) -> dict[str, Any]:
    relative_source = Path(
        "examples/attack_plans/lattice_lwe_modulus_switching_primary.json"
    )
    attack_plan_id = "lattice_lwe_modulus_switching_primary_v1"
    source_path = root / relative_source
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "attack_plan_id": attack_plan_id,
        "estimator": None,
        "hf_seed_evaluation_status": None,
        "hf_seed_reward": None,
        "operator_types": [],
        "prime_seed_evaluation_status": None,
        "prime_seed_reward": None,
        "source_path": relative_source.as_posix(),
        "space_label_present": False,
        "verifier_accepted": None,
        "verifier_evaluation_status": None,
        "verifier_time_bits": None,
        "warning_contains_catalog_boundary": False,
    }

    if not source_path.is_file():
        failures.append("Lattice runtime primary boundary AttackPlan is missing.")
    else:
        try:
            plan = AttackPlan.model_validate_json(
                source_path.read_text(encoding="utf-8")
            )
            verifier_result = verify_attack_plan_path(source_path)
        except Exception as exc:  # noqa: BLE001 - audit must report bad fixtures.
            failures.append(
                f"Lattice runtime primary boundary verification failed: {exc}"
            )
        else:
            operator_types = [operator.type for operator in plan.operators]
            warnings = verifier_result.get("warnings", [])
            if not isinstance(warnings, list):
                warnings = []
            estimator = verifier_result.get("estimator", {})
            if not isinstance(estimator, dict):
                estimator = {}
            evidence.update(
                {
                    "estimator": estimator.get("name"),
                    "operator_types": operator_types,
                    "verifier_accepted": verifier_result.get("accepted"),
                    "verifier_evaluation_status": verifier_result.get(
                        "evaluation_status"
                    ),
                    "verifier_time_bits": verifier_result.get("estimated_time_bits"),
                    "warning_contains_catalog_boundary": any(
                        "not a cataloged primary LWE/MLWE estimator route"
                        in str(warning)
                        for warning in warnings
                    ),
                }
            )

            if plan.attack_plan_id != attack_plan_id:
                failures.append("Lattice runtime boundary AttackPlan id drifted.")
            if plan.target.family.value != "LWE":
                failures.append("Lattice runtime boundary target is not LWE.")
            if operator_types != ["modulus_switching"]:
                failures.append(
                    "Lattice runtime boundary must use modulus_switching "
                    "as the only primary operator."
                )
            if verifier_result.get("accepted") is not False:
                failures.append(
                    "Lattice runtime boundary verifier result must be rejected."
                )
            if verifier_result.get("evaluation_status") != "unsupported":
                failures.append(
                    "Lattice runtime boundary verifier status must be unsupported."
                )
            if verifier_result.get("estimated_time_bits") is not None:
                failures.append(
                    "Lattice runtime boundary must not expose a time estimate."
                )
            if estimator.get("name") != "lattice-family-router":
                failures.append(
                    "Lattice runtime boundary must route through lattice-family-router."
                )
            if evidence["warning_contains_catalog_boundary"] is not True:
                failures.append(
                    "Lattice runtime boundary warning lacks catalog-review wording."
                )

    hf_metadata = _hf_task_metadata_for_attack_plan(root, attack_plan_id)
    if hf_metadata is None:
        failures.append("Hugging Face task metadata lacks lattice runtime boundary.")
    else:
        evidence["hf_seed_evaluation_status"] = hf_metadata.get(
            "seed_evaluation_status"
        )
        evidence["hf_seed_reward"] = hf_metadata.get("seed_reward")
        if hf_metadata.get("seed_evaluation_status") != "unsupported":
            failures.append(
                "Hugging Face lattice runtime boundary seed status is not unsupported."
            )
        if hf_metadata.get("seed_reward") != 0.0:
            failures.append(
                "Hugging Face lattice runtime boundary seed reward must be 0.0."
            )

    prime_metadata = _prime_task_metadata_for_attack_plan(root, attack_plan_id)
    if prime_metadata is None:
        failures.append("Prime task metadata lacks lattice runtime boundary.")
    else:
        evidence["prime_seed_evaluation_status"] = prime_metadata.get(
            "seed_evaluation_status"
        )
        evidence["prime_seed_reward"] = prime_metadata.get("seed_reward")
        if prime_metadata.get("seed_evaluation_status") != "unsupported":
            failures.append(
                "Prime lattice runtime boundary seed status is not unsupported."
            )
        if prime_metadata.get("seed_reward") != 0.0:
            failures.append("Prime lattice runtime boundary seed reward must be 0.0.")

    space_labels = _hf_space_labels(root)
    label = f"LWE / {attack_plan_id}"
    evidence["space_label_present"] = label in space_labels
    if label not in space_labels:
        failures.append("Hugging Face Space does not expose lattice runtime boundary.")

    return _check(
        check_id="lattice-runtime-primary-boundary",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="examples/attack_plans/lattice_lwe_modulus_switching_primary.json",
        detail=(
            "Runtime-only lattice transforms remain public zero-reward routing "
            "fixtures when used as primary estimator routes, proving they are "
            "not silently treated as reviewed LWE estimates."
        ),
        evidence=evidence,
        failures=failures,
    )


def _lattice_estimator_pin(root: Path) -> dict[str, Any]:
    relative_path = Path("docs/lattice_estimator_manifest.json")
    path = root / relative_path
    verification = verify_lattice_estimator_manifest(relative_path, root=root)
    failures = list(verification["failures"])

    try:
        manifest = _read_json(path) if path.is_file() else {}
    except json.JSONDecodeError:
        manifest = {}

    upstream = manifest.get("upstream", {})
    boundary = manifest.get("agades_boundary", {})
    mappings = boundary.get("reviewed_lwe_mappings", {})
    pin_enforcement = boundary.get("pin_enforcement")
    pinned_commit = upstream.get("pinned_commit")
    source_checkout_import_guard = _lattice_estimator_source_checkout_import_guard(
        root,
        failures=failures,
    )

    return _check(
        check_id="lattice-estimator-pin",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="docs/lattice_estimator_manifest.json",
        detail=(
            "Lattice Estimator upstream pin and Agades adapter boundary are "
            "checked in, synchronized, and marked review-required/no-claim."
        ),
        evidence={
            "mapping_count": len(mappings) if isinstance(mappings, dict) else 0,
            "pin_enforcement": pin_enforcement,
            "pinned_commit": pinned_commit,
            "schema_only_lattice_families": boundary.get(
                "schema_only_lattice_families",
            ),
            "runtime_environment": boundary.get("runtime_environment"),
            "source_checkout_backend": boundary.get("source_checkout_backend"),
            "source_checkout_import_guard": source_checkout_import_guard,
        },
        failures=failures,
    )


def _lattice_estimator_source_checkout_import_guard(
    root: Path,
    *,
    failures: list[str],
) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "dirty_checkout_imported_estimator": None,
        "dirty_checkout_status": None,
        "wrong_origin_imported_estimator": None,
        "wrong_origin_status": None,
    }

    try:
        plan = AttackPlan.model_validate_json(
            (root / "examples/attack_plans/lattice_primal_usvp_toy.json").read_text(
                encoding="utf-8"
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            dirty_source, dirty_commit = (
                _write_release_audit_lattice_estimator_checkout(tmp_path / "dirty")
            )
            (dirty_source / "README.md").write_text(
                "unreviewed local edit\n",
                encoding="utf-8",
            )
            _clear_estimator_modules()
            dirty_result = LatticeEstimatorAdapter(
                source_path=dirty_source,
                config=LatticeEstimatorConfig(required_commit=dirty_commit),
            ).estimate(plan)
            evidence["dirty_checkout_status"] = dirty_result.evaluation_status
            evidence["dirty_checkout_imported_estimator"] = (
                dirty_source / "estimator" / "IMPORT_MARKER"
            ).exists()

            wrong_origin_source, wrong_origin_commit = (
                _write_release_audit_lattice_estimator_checkout(
                    tmp_path / "wrong-origin"
                )
            )
            subprocess.run(
                [
                    "git",
                    "remote",
                    "set-url",
                    "origin",
                    "https://example.com/fork.git",
                ],
                cwd=wrong_origin_source,
                check=True,
                capture_output=True,
            )
            _clear_estimator_modules()
            wrong_origin_result = LatticeEstimatorAdapter(
                source_path=wrong_origin_source,
                config=LatticeEstimatorConfig(required_commit=wrong_origin_commit),
            ).estimate(plan)
            evidence["wrong_origin_status"] = wrong_origin_result.evaluation_status
            evidence["wrong_origin_imported_estimator"] = (
                wrong_origin_source / "estimator" / "IMPORT_MARKER"
            ).exists()
    except Exception as exc:  # noqa: BLE001 - audit reports integration failures.
        failures.append(f"Lattice Estimator source checkout import guard failed: {exc}")
    finally:
        _clear_estimator_modules()

    if evidence["dirty_checkout_status"] != "error":
        failures.append("Dirty Lattice Estimator checkouts must fail before import.")
    if evidence["dirty_checkout_imported_estimator"] is not False:
        failures.append("Dirty Lattice Estimator checkout imported estimator.")
    if evidence["wrong_origin_status"] != "error":
        failures.append(
            "Wrong-origin Lattice Estimator checkouts must fail before import."
        )
    if evidence["wrong_origin_imported_estimator"] is not False:
        failures.append("Wrong-origin Lattice Estimator checkout imported estimator.")

    return evidence


def _clear_estimator_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "estimator" or module_name.startswith("estimator."):
            del sys.modules[module_name]


def _lattice_estimator_baseline_contracts(root: Path) -> dict[str, Any]:
    relative_path = Path("docs/lattice_estimator_baseline_contracts.json")
    verification = verify_lattice_estimator_baseline_contracts(
        relative_path,
        root=root,
    )
    failures = list(verification["failures"])
    summary = verification["summary"]

    return _check(
        check_id="lattice-estimator-baseline-contracts",
        status="failed" if failures else "passed",
        blocking=True,
        artifact=relative_path.as_posix(),
        detail=(
            "Reviewed LWE Lattice Estimator mappings have baseline reproduction "
            "contracts tied to the checked upstream pin, while numeric reference "
            "outputs and security claims remain blocked until expert review."
        ),
        evidence={
            "contract_count": summary["contract_count"],
            "covered_algorithm_keys": summary["covered_algorithm_keys"],
            "numeric_reference_outputs_committed": summary[
                "numeric_reference_outputs_committed"
            ],
            "pinned_commit": summary["pinned_commit"],
            "security_claim": summary["security_claim"],
        },
        failures=failures,
    )


class _ReleaseAuditLatticeBaselineBackend:
    version = "release-audit-baseline-0.1"
    commit = LATTICE_ESTIMATOR_PINNED_COMMIT

    def make_binary_distribution(self) -> tuple[str]:
        return ("binary",)

    def make_sparse_binary_distribution(self, hamming_weight: int) -> tuple[str, int]:
        return ("sparse_binary", hamming_weight)

    def make_centered_binomial_distribution(self, eta: int) -> tuple[str, int]:
        return ("centered_binomial", eta)

    def make_discrete_gaussian_distribution(self, sigma: float) -> tuple[str, float]:
        return ("discrete_gaussian", sigma)

    def make_lwe_parameters(
        self,
        *,
        n: int,
        q: int,
        xs: Any,
        xe: Any,
        m: int,
        tag: str,
    ) -> dict[str, Any]:
        return {"n": n, "q": q, "xs": xs, "xe": xe, "m": m, "tag": tag}

    def estimate_lwe(
        self,
        *,
        params: Any,
        algorithm_key: str,
        red_cost_model: str | None,
        red_shape_model: str | None,
        jobs: int,
        catch_exceptions: bool,
    ) -> dict[str, Any]:
        del params, red_cost_model, red_shape_model, jobs, catch_exceptions
        return {algorithm_key: {"rop": 57.25, "mem": 19.5, "beta": 72}}


def _lattice_estimator_baseline_run_boundary(root: Path) -> dict[str, Any]:
    relative_path = Path("private/reports/lattice_estimator_baseline_run.json")
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "all_successful_results_from_pinned_commit": False,
        "contract_count": 0,
        "lwe_only": False,
        "numeric_reference_outputs_committed": None,
        "numeric_result_count": 0,
        "ok_results": 0,
        "private_numeric_outputs": None,
        "private_report": None,
        "public_release_ok": None,
        "publishes_numeric_references": None,
        "raw_estimator_output_committed": None,
        "raw_output_digest_count": 0,
        "review_packet_accepted": None,
        "review_packet_contains_numeric_values": None,
        "review_packet_public_release_ok": None,
        "review_packet_raw_output_digest_count": 0,
        "security_claim": None,
        "standalone_verifier_accepted": None,
    }
    verification: dict[str, Any] | None = None
    packet_verification: dict[str, Any] | None = None
    packet: dict[str, Any] | None = None

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            report = write_lattice_estimator_baseline_run(
                relative_path,
                contracts_path=Path("docs/lattice_estimator_baseline_contracts.json"),
                policy=build_private_run_policy(),
                adapter=LatticeEstimatorAdapter(
                    backend=_ReleaseAuditLatticeBaselineBackend()
                ),
                contracts_root=root,
                policy_root=Path(tmpdir),
                run_id="release-audit-lattice-estimator-baseline-run",
            )
            verification = verify_lattice_estimator_baseline_run(
                tmp_root / relative_path,
                contracts_root=root,
            )
            review_packet_path = Path(
                "private/reports/lattice_estimator_baseline_review_packet.json"
            )
            packet = write_lattice_estimator_baseline_review_packet(
                review_packet_path,
                baseline_report_path=tmp_root / relative_path,
                policy=build_private_run_policy(),
                contracts_root=root,
                policy_root=tmp_root,
                reviewer_label="release-audit-lattice-review",
            )
            packet_verification = verify_lattice_estimator_baseline_review_packet(
                tmp_root / review_packet_path,
                baseline_report_path=tmp_root / relative_path,
                contracts_root=root,
            )
    except Exception as exc:  # noqa: BLE001 - audit reports integration failures.
        failures.append(f"Private Lattice Estimator baseline run failed: {exc}")
        report = {}

    if report:
        summary = _dict_or_empty(report.get("summary"))
        policy = _dict_or_empty(report.get("baseline_policy"))
        safety = _dict_or_empty(report.get("safety"))
        report_ref = _dict_or_empty(report.get("report"))
        results = report.get("results", [])
        if not isinstance(results, list):
            results = []

        evidence.update(
            {
                "all_successful_results_from_pinned_commit": summary.get(
                    "all_successful_results_from_pinned_commit"
                ),
                "contract_count": summary.get("contract_count"),
                "lwe_only": safety.get("lwe_only"),
                "numeric_reference_outputs_committed": policy.get(
                    "numeric_reference_outputs_committed"
                ),
                "numeric_result_count": summary.get("numeric_result_count"),
                "ok_results": summary.get("ok_results"),
                "private_numeric_outputs": policy.get("private_numeric_outputs"),
                "private_report": report_ref.get("private"),
                "public_release_ok": summary.get("public_release_ok"),
                "publishes_numeric_references": safety.get(
                    "publishes_numeric_references"
                ),
                "raw_estimator_output_committed": safety.get(
                    "raw_estimator_output_committed"
                ),
                "raw_output_digest_count": sum(
                    1
                    for result in results
                    if isinstance(result, dict)
                    and isinstance(result.get("raw_output_sha256"), str)
                    and len(result["raw_output_sha256"]) == 64
                ),
                "review_packet_accepted": (
                    packet_verification["accepted"]
                    if packet_verification is not None
                    else None
                ),
                "review_packet_contains_numeric_values": (
                    _dict_or_empty(packet.get("safety")).get("contains_numeric_values")
                    if packet is not None
                    else None
                ),
                "review_packet_public_release_ok": (
                    _dict_or_empty(packet.get("safety")).get("public_release_ok")
                    if packet is not None
                    else None
                ),
                "review_packet_raw_output_digest_count": (
                    packet_verification["summary"]["raw_output_digest_count"]
                    if packet_verification is not None
                    else 0
                ),
                "security_claim": summary.get("security_claim"),
                "standalone_verifier_accepted": (
                    verification["accepted"] if verification is not None else None
                ),
            }
        )

        if verification is None:
            failures.append("Private baseline run standalone verifier did not run.")
        elif not verification["accepted"]:
            failures.extend(
                f"Private baseline run standalone verification failed: {failure}"
                for failure in verification["failures"]
            )
        if report.get("schema_version") != LATTICE_ESTIMATOR_BASELINE_RUN_SCHEMA:
            failures.append("Private baseline run schema drifted.")
        if report_ref.get("path") != relative_path.as_posix():
            failures.append("Private baseline run report path drifted.")
        if evidence["private_report"] is not True:
            failures.append("Private baseline run must be marked private.")
        if evidence["contract_count"] != 5:
            failures.append("Private baseline run must cover five contracts.")
        if evidence["ok_results"] != 5 or evidence["numeric_result_count"] != 5:
            failures.append("Private baseline run must produce five numeric results.")
        if evidence["all_successful_results_from_pinned_commit"] is not True:
            failures.append("Private baseline run must use the checked estimator pin.")
        if evidence["numeric_reference_outputs_committed"] is not False:
            failures.append("Private baseline run must not commit numeric references.")
        if evidence["private_numeric_outputs"] is not True:
            failures.append("Private baseline run numeric outputs must stay private.")
        if evidence["public_release_ok"] is not False:
            failures.append("Private baseline run must not be public-release-ready.")
        if evidence["publishes_numeric_references"] is not False:
            failures.append("Private baseline run must not publish numeric references.")
        if evidence["raw_estimator_output_committed"] is not False:
            failures.append(
                "Private baseline run must not commit raw estimator output."
            )
        if evidence["raw_output_digest_count"] != 5:
            failures.append(
                "Private baseline run must digest every raw estimator output."
            )
        if evidence["lwe_only"] is not True:
            failures.append("Private baseline run must remain LWE-only.")
        if evidence["security_claim"] is not False:
            failures.append("Private baseline run must not advertise a security claim.")
        if evidence["standalone_verifier_accepted"] is not True:
            failures.append("Private baseline run standalone verifier must accept.")
        if evidence["review_packet_accepted"] is not True:
            failures.append("Private baseline review packet verifier must accept.")
        if evidence["review_packet_contains_numeric_values"] is not False:
            failures.append(
                "Private baseline review packet must not contain numeric values."
            )
        if evidence["review_packet_public_release_ok"] is not False:
            failures.append(
                "Private baseline review packet must not be public-release-ready."
            )
        if evidence["review_packet_raw_output_digest_count"] != 5:
            failures.append(
                "Private baseline review packet must include five raw-output digests."
            )
        if '"raw_output":' in json.dumps(report):
            failures.append("Private baseline run exposed raw estimator output.")

    return _check(
        check_id="lattice-estimator-baseline-run-boundary",
        status="failed" if failures else "passed",
        blocking=True,
        artifact=relative_path.as_posix(),
        detail=(
            "A private Lattice Estimator baseline run can reproduce the checked "
            "LWE contracts with a pin-matched backend while keeping numeric "
            "outputs private, digesting raw estimator payloads, and preserving "
            "the no-security-claim boundary."
        ),
        evidence=evidence,
        failures=failures,
    )


def _lattice_estimator_checkout_preflight_boundary(root: Path) -> dict[str, Any]:
    del root
    relative_path = Path("private/reports/lattice_estimator_checkout_preflight.json")
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "executes_estimator": None,
        "failure_count": None,
        "head_matches_required_pin": None,
        "imports_upstream_python": None,
        "private_report": None,
        "publication_allowed": None,
        "ready_for_private_baseline_run": None,
        "remote_matches_upstream": None,
        "security_claim": None,
        "writes_only_allowed_private_roots": None,
    }

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source_path, commit = _write_release_audit_lattice_estimator_checkout(
                tmp_path
            )
            report = write_lattice_estimator_checkout_preflight(
                relative_path,
                source_path=source_path,
                policy=build_private_run_policy(),
                policy_root=tmp_path,
                required_commit=commit,
            )
            import_marker_exists = (
                source_path / "estimator" / "IMPORT_MARKER"
            ).exists()
    except Exception as exc:  # noqa: BLE001 - audit reports integration failures.
        failures.append(f"Private Lattice Estimator checkout preflight failed: {exc}")
        report = {}
        import_marker_exists = False

    if report:
        report_ref = _dict_or_empty(report.get("report"))
        git = _dict_or_empty(_dict_or_empty(report.get("source_checkout")).get("git"))
        readiness = _dict_or_empty(report.get("readiness"))
        safety = _dict_or_empty(report.get("safety"))

        evidence.update(
            {
                "executes_estimator": safety.get("executes_estimator"),
                "failure_count": readiness.get("failure_count"),
                "head_matches_required_pin": git.get("head_matches_required_pin"),
                "imports_upstream_python": safety.get("imports_upstream_python"),
                "private_report": report_ref.get("private"),
                "publication_allowed": safety.get("publication_allowed"),
                "ready_for_private_baseline_run": readiness.get(
                    "ready_for_private_baseline_run"
                ),
                "remote_matches_upstream": git.get("remote_matches_upstream"),
                "security_claim": safety.get("security_claim"),
                "writes_only_allowed_private_roots": safety.get(
                    "writes_only_allowed_private_roots"
                ),
            }
        )

        if report.get("schema_version") != LATTICE_ESTIMATOR_CHECKOUT_PREFLIGHT_SCHEMA:
            failures.append("Private checkout preflight schema drifted.")
        if report_ref.get("path") != relative_path.as_posix():
            failures.append("Private checkout preflight report path drifted.")
        if evidence["private_report"] is not True:
            failures.append("Private checkout preflight must be marked private.")
        if evidence["ready_for_private_baseline_run"] is not True:
            failures.append(
                "Private checkout preflight must accept the pin-matched checkout."
            )
        if evidence["failure_count"] != 0:
            failures.append("Private checkout preflight must have no failures.")
        if evidence["head_matches_required_pin"] is not True:
            failures.append("Private checkout preflight must prove the commit pin.")
        if evidence["remote_matches_upstream"] is not True:
            failures.append(
                "Private checkout preflight must prove the upstream origin remote."
            )
        if evidence["imports_upstream_python"] is not False:
            failures.append(
                "Private checkout preflight must not import upstream Python."
            )
        if evidence["executes_estimator"] is not False:
            failures.append(
                "Private checkout preflight must not execute estimator code."
            )
        if import_marker_exists:
            failures.append(
                "Private checkout preflight imported the estimator package."
            )
        if evidence["writes_only_allowed_private_roots"] is not True:
            failures.append(
                "Private checkout preflight must write only allowed private roots."
            )
        if evidence["publication_allowed"] is not False:
            failures.append("Private checkout preflight must not allow publication.")
        if evidence["security_claim"] is not False:
            failures.append("Private checkout preflight must not make security claims.")

    return _check(
        check_id="lattice-estimator-checkout-preflight-boundary",
        status="failed" if failures else "passed",
        blocking=True,
        artifact=relative_path.as_posix(),
        detail=(
            "A private Lattice Estimator checkout preflight can prove a local "
            "checkout is at the reviewed pin before baseline runs use "
            "--estimator-source, without importing upstream Python or executing "
            "estimator code."
        ),
        evidence=evidence,
        failures=failures,
    )


def _lattice_estimator_runtime_preflight_verifier(root: Path) -> dict[str, Any]:
    del root
    relative_path = DEFAULT_RUNTIME_PREFLIGHT_PATH
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "accepted_closed_failure_report": False,
        "executes_estimator": None,
        "external_network_access": None,
        "failure_count": None,
        "imports_upstream_python": None,
        "numeric_reference_outputs_committed": None,
        "private_report": None,
        "publication_allowed": None,
        "ready_for_private_lattice_estimator_import": None,
        "sage_found": None,
        "sage_python_imports_sage": None,
        "security_claim": None,
        "writes_only_allowed_private_roots": None,
    }

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            report = build_lattice_estimator_runtime_preflight(
                sage_command=(tmp_path / "missing-sage").as_posix(),
                report_path=relative_path,
                timeout_seconds=1,
            )
            preflight_path = tmp_path / "lattice_estimator_runtime_preflight.json"
            preflight_path.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            verification = verify_lattice_estimator_runtime_preflight(preflight_path)
    except Exception as exc:  # noqa: BLE001 - audit reports integration failures.
        failures.append(
            f"Lattice Estimator runtime preflight verifier smoke failed: {exc}"
        )
        report = {}
        verification = {"accepted": False, "summary": {}, "failures": []}

    if report:
        report_ref = _dict_or_empty(report.get("report"))
        runtime_environment = _dict_or_empty(report.get("runtime_environment"))
        readiness = _dict_or_empty(report.get("readiness"))
        safety = _dict_or_empty(report.get("safety"))
        report_failures = report.get("failures", [])
        if not isinstance(report_failures, list):
            report_failures = []

        evidence.update(
            {
                "accepted_closed_failure_report": (
                    verification.get("accepted") is True
                    and readiness.get("ready_for_private_lattice_estimator_import")
                    is False
                    and readiness.get("failure_count") == 1
                ),
                "executes_estimator": safety.get("executes_estimator"),
                "external_network_access": safety.get("external_network_access"),
                "failure_count": readiness.get("failure_count"),
                "imports_upstream_python": safety.get("imports_upstream_python"),
                "numeric_reference_outputs_committed": safety.get(
                    "numeric_reference_outputs_committed"
                ),
                "private_report": report_ref.get("private"),
                "publication_allowed": safety.get("publication_allowed"),
                "ready_for_private_lattice_estimator_import": readiness.get(
                    "ready_for_private_lattice_estimator_import"
                ),
                "sage_found": runtime_environment.get("sage_found"),
                "sage_python_imports_sage": runtime_environment.get(
                    "sage_python_imports_sage"
                ),
                "security_claim": safety.get("security_claim"),
                "writes_only_allowed_private_roots": safety.get(
                    "writes_only_allowed_private_roots"
                ),
            }
        )

        if report.get("schema_version") != LATTICE_ESTIMATOR_RUNTIME_PREFLIGHT_SCHEMA:
            failures.append("Runtime preflight schema drifted.")
        if report_ref.get("path") != relative_path.as_posix():
            failures.append("Runtime preflight report path drifted.")
        if report_ref.get("private") is not True:
            failures.append("Runtime preflight report must be marked private.")
        if verification.get("accepted") is not True:
            failures.append(
                "Runtime preflight verifier must accept a valid closed-failure report."
            )
        if evidence["accepted_closed_failure_report"] is not True:
            failures.append(
                "Runtime preflight verifier did not preserve closed-failure readiness."
            )
        if evidence["failure_count"] != 1:
            failures.append("Runtime preflight closed-failure smoke must fail once.")
        if not any(
            isinstance(failure, str)
            and failure.startswith("Sage executable not found:")
            for failure in report_failures
        ):
            failures.append("Runtime preflight closed-failure reason drifted.")
        if evidence["ready_for_private_lattice_estimator_import"] is not False:
            failures.append(
                "Runtime preflight must block private imports when Sage is missing."
            )
        if evidence["sage_found"] is not False:
            failures.append("Runtime preflight smoke must report missing Sage.")
        if evidence["sage_python_imports_sage"] is not False:
            failures.append(
                "Runtime preflight smoke must not mark Sage Python import ready."
            )
        for flag in (
            "executes_estimator",
            "external_network_access",
            "imports_upstream_python",
            "numeric_reference_outputs_committed",
            "publication_allowed",
            "security_claim",
        ):
            if evidence[flag] is not False:
                failures.append(f"Runtime preflight safety.{flag} must be false.")
        if evidence["writes_only_allowed_private_roots"] is not True:
            failures.append(
                "Runtime preflight must keep writes under allowed private roots."
            )

    return _check(
        check_id="lattice-estimator-runtime-preflight-verifier",
        status="failed" if failures else "passed",
        blocking=True,
        artifact=relative_path.as_posix(),
        detail=(
            "The Sage runtime preflight verifier accepts a synthetic missing-Sage "
            "closed-failure report, preserving private-report, no-estimator, "
            "no-network, no-public-output, and no-security-claim boundaries."
        ),
        evidence=evidence,
        failures=failures,
    )


def _write_release_audit_lattice_estimator_checkout(
    tmp_path: Path,
) -> tuple[Path, str]:
    source = tmp_path / "fake-lattice-estimator-checkout"
    package = source / "estimator"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        (
            "from pathlib import Path\n"
            "Path(__file__).with_name('IMPORT_MARKER').write_text('imported')\n"
        ),
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=source, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/malb/lattice-estimator"],
        cwd=source,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "add", "estimator/__init__.py"],
        cwd=source,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=release-audit@example.com",
            "-c",
            "user.name=Agades Release Audit",
            "commit",
            "-m",
            "Add fake estimator package",
        ],
        cwd=source,
        check=True,
        capture_output=True,
    )
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=source,
        text=True,
    ).strip()
    return source, commit


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def write_release_audit(out: Path, *, root: Path | None = None) -> dict[str, Any]:
    audit = build_release_audit(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return audit


def _hf_dataset_safety(root: Path) -> dict[str, Any]:
    verification = verify_huggingface_dataset_bundle(Path("hf/dataset"), root=root)
    summary = verification["summary"]
    return _check(
        check_id="hf-dataset-safety",
        status="failed" if verification["failures"] else "passed",
        blocking=True,
        artifact="hf/dataset",
        detail="Hugging Face dataset metadata and verifier rows are public-safe.",
        evidence={
            "attack_plan_count": summary["attack_plan_count"],
            "task_metadata_rows": summary["task_metadata_rows"],
            "task_metadata_rows_match_attack_plans": (
                summary["task_metadata_rows_match_attack_plans"]
            ),
            "verifier_output_count": summary["verifier_rows"],
            "verifier_rows": summary["verifier_rows"],
        },
        failures=list(verification["failures"]),
    )


def _source_catalog_safety(root: Path) -> dict[str, Any]:
    path = root / "docs" / "source_catalog.json"
    failed_reasons: list[str] = []
    if not path.is_file():
        evidence = {"source_count": 0}
        failed_reasons.append("Source catalog is not checked in.")
    else:
        verification = verify_source_catalog(path, root=root)
        failed_reasons.extend(verification["failures"])
        summary = verification["summary"]
        evidence = {
            "current_public_surface_count": summary["current_public_surface_count"],
            "current_public_surfaces": summary["current_public_surfaces"],
            "future_reviewed_adapter_count": summary["future_reviewed_adapter_count"],
            "future_reviewed_adapters": summary["future_reviewed_adapters"],
            "local_artifact_source_count": summary["local_artifact_source_count"],
            "non_lattice_toy_evaluator_count": summary[
                "non_lattice_toy_evaluator_count"
            ],
            "non_lattice_toy_operator_families": summary[
                "non_lattice_toy_operator_families"
            ],
            "non_lattice_toy_operator_security_claims": summary[
                "non_lattice_toy_operator_security_claims"
            ],
            "non_lattice_toy_operator_variant_count": summary[
                "non_lattice_toy_operator_variant_count"
            ],
            "platforms": summary["platforms"],
            "platform_counts": summary["platform_counts"],
            "requires_gpu_source_count": summary["requires_gpu_source_count"],
            "source_count": summary["source_count"],
            "source_map_only": summary["source_map_only"],
            "source_map_only_count": summary["source_map_only_count"],
        }
    return _check(
        check_id="source-catalog-safety",
        status="failed" if failed_reasons else "passed",
        blocking=True,
        artifact="docs/source_catalog.json",
        detail="Source catalog keeps external anchors public and review-gated.",
        evidence=evidence,
        failures=failed_reasons,
    )


def _benchmark_source_contracts(root: Path) -> dict[str, Any]:
    expected = build_benchmark_source_contracts()
    path = root / "docs" / "benchmark_source_contracts.json"
    failed_reasons: list[str] = []
    evidence = {
        "blocked_public_benchmark_claim_surface_contracts": 0,
        "blocked_public_verifier_contracts": 0,
        "blocked_prime_reward_contracts": 0,
        "contract_count": 0,
        "current_runtime_enabled_contracts": 0,
        "expert_review_gate_contracts": 0,
        "future_reviewed_adapters": 0,
        "heavy_storage_contracts": 0,
        "public_verifier_allowed_contracts": 0,
        "requires_gpu_contracts": 0,
        "source_catalog_id_count": 0,
        "target_family_counts": {},
    }

    if not path.is_file():
        failed_reasons.append("Benchmark source contracts are not checked in.")
    else:
        manifest = _read_json(path)
        if manifest != expected:
            failed_reasons.append("Benchmark source contracts are not in sync.")
        verification = verify_benchmark_source_contracts(path)
        failed_reasons.extend(verification["failures"])
        evidence = {key: verification["summary"][key] for key in evidence}

    return _check(
        check_id="benchmark-source-contracts",
        status="failed" if failed_reasons else "passed",
        blocking=True,
        artifact="docs/benchmark_source_contracts.json",
        detail=(
            "Heavy lattice sources, non-lattice family standards, and "
            "implementation-security sources remain future reviewed adapters "
            "with explicit runtime, storage/device, toolchain, vector "
            "provenance, parameter-mapping, and claim gates."
        ),
        evidence=evidence,
        failures=failed_reasons,
    )


def _ecosystem_source_graph(root: Path) -> dict[str, Any]:
    path = root / "docs" / "ecosystem_source_graph.json"
    failed_reasons: list[str] = []
    evidence = {
        "benchmark_source_catalog_links": 0,
        "benchmark_source_contracts": 0,
        "family_count": 0,
        "family_cross_family_source_links": 0,
        "family_future_source_links": 0,
        "prime_source_ids": 0,
        "prime_visibility_anchor_ids": 0,
        "source_catalog_sources": 0,
        "unique_family_cross_family_source_ids": 0,
        "unique_family_future_source_ids": 0,
        "unresolved_benchmark_source_catalog_links": 0,
        "unresolved_family_source_links": 0,
    }

    if not path.is_file():
        failed_reasons.append("Ecosystem source graph is not checked in.")
    else:
        verification = verify_ecosystem_source_graph(path, root=root)
        failed_reasons.extend(verification["failures"])
        evidence = {key: verification["summary"][key] for key in evidence}

    return _check(
        check_id="ecosystem-source-graph",
        status="failed" if failed_reasons else "passed",
        blocking=True,
        artifact="docs/ecosystem_source_graph.json",
        detail=(
            "The public source catalog, future benchmark source contracts, and "
            "family support matrix form a closed OSS review graph with no "
            "dangling source IDs."
        ),
        evidence=evidence,
        failures=failed_reasons,
    )


def _nvidia_manifest_safety(root: Path) -> dict[str, Any]:
    verification = verify_nvidia_manifest_safety_report(
        Path("reports/nvidia_manifest_safety.json"),
        root=root,
    )
    summary = verification["summary"]
    failed_reasons = list(verification["failures"])

    return _check(
        check_id="nvidia-manifest-safety",
        status="failed" if failed_reasons else "passed",
        blocking=True,
        artifact="reports/nvidia_manifest_safety.json",
        detail=(
            "NVIDIA manifest safety report keeps the current MVP "
            "CPU/verifier-only, with GPU work reserved as a future reviewed "
            "acceleration surface."
        ),
        evidence={
            "all_current_workloads_cpu": summary["all_current_workloads_cpu"],
            "artifact_count": summary["artifact_count"],
            "cpu_workload_count": summary["cpu_workload_count"],
            "current_gpu_required_workload_count": summary[
                "current_gpu_required_workload_count"
            ],
            "current_workload_count": summary["current_workload_count"],
            "gpu_future_workload_count": summary["gpu_future_workload_count"],
            "workload_count": summary["workload_count"],
            "gpu_status": summary["gpu_status"],
            "no_current_workload_requires_gpu": summary[
                "no_current_workload_requires_gpu"
            ],
            "public_run_bundle_count": summary["public_run_bundle_count"],
            "reserved_future_gpu_required_workload_count": summary[
                "reserved_future_gpu_required_workload_count"
            ],
            "reserved_future_workload_count": summary["reserved_future_workload_count"],
        },
        failures=failed_reasons,
    )


def _nvidia_publication_handoff(root: Path) -> dict[str, Any]:
    path = root / "docs" / "nvidia_publication_handoff.json"
    verification = verify_nvidia_publication_handoff(path, root=root)
    summary = verification["summary"]

    return _check(
        check_id="nvidia-publication-handoff",
        status="failed" if verification["failures"] else "passed",
        blocking=True,
        artifact="docs/nvidia_publication_handoff.json",
        detail=(
            "NVIDIA publication handoff is checked in, synchronized with the "
            "accelerator strategy and manifest, and keeps external submission "
            "and GPU-result claims behind review."
        ),
        evidence={
            "artifact_count": summary["artifact_count"],
            "current_gpu_required_workload_count": summary[
                "current_gpu_required_workload_count"
            ],
            "current_workload_count": summary["current_workload_count"],
            "external_submission_requires_review": summary[
                "external_submission_requires_review"
            ],
            "gpu_execution_performed": summary["gpu_execution_performed"],
            "gpu_future_workload_count": summary["gpu_future_workload_count"],
            "nvidia_submission_performed": summary["nvidia_submission_performed"],
            "public_run_bundles": summary["public_run_bundles"],
            "requires_credentials": summary["requires_credentials"],
            "total_workload_count": summary["total_workload_count"],
        },
        failures=list(verification["failures"]),
    )


def _publication_manifest_safety(root: Path) -> dict[str, Any]:
    path = root / "docs" / "publication_manifest.json"
    verification = verify_publication_manifest(path, root=root)
    failures = list(verification["failures"])
    evidence = {
        key: value
        for key, value in verification["summary"].items()
        if key != "failure_count"
    }

    return _check(
        check_id="publication-manifest-safety",
        status="failed" if not verification["accepted"] else "passed",
        blocking=True,
        artifact="docs/publication_manifest.json",
        detail=(
            "Publication manifest maps GitHub, Hugging Face, Prime, and NVIDIA "
            "surfaces without leaking moat artifacts or making security claims."
        ),
        evidence=evidence,
        failures=failures,
    )


def _public_benchmark_manifest(root: Path) -> dict[str, Any]:
    expected = build_public_benchmark_manifest(root=root)
    path = root / "docs" / "public_benchmark_manifest.json"
    failures: list[str] = []
    manifest: dict[str, Any]

    if not path.is_file():
        manifest = {}
        failures.append("Public benchmark manifest is not checked in.")
    else:
        manifest = _read_json(path)
        if manifest != expected:
            failures.append("Public benchmark manifest is not in sync.")

    summary = manifest.get("summary", {})
    safety = manifest.get("safety", {})
    bundles = manifest.get("bundles", [])
    if not isinstance(bundles, list):
        bundles = []
        failures.append("Public benchmark manifest bundles must be a list.")

    if safety.get("contains_private_traces") is not False:
        failures.append("Public benchmark manifest may expose private traces.")
    if safety.get("publishes_private_candidates") is not False:
        failures.append("Public benchmark manifest may publish private candidates.")
    if safety.get("security_claim") is not False:
        failures.append("Public benchmark manifest advertises a security claim.")
    if safety.get("review_required_before_publish") is not True:
        failures.append("Public benchmark manifest lacks publish-review gate.")
    if summary.get("bundle_count") != len(bundles):
        failures.append("Public benchmark manifest bundle count is inconsistent.")

    record_count = 0
    for bundle in bundles:
        if not isinstance(bundle, dict):
            failures.append("Public benchmark manifest contains a non-object bundle.")
            continue
        bundle_id = bundle.get("id")
        bundle_path = bundle.get("bundle_path")
        benchmark_path = bundle.get("benchmark_path")
        if not isinstance(bundle_path, str) or not (root / bundle_path).is_dir():
            failures.append(f"Public benchmark bundle path is missing: {bundle_id}.")
        if not isinstance(benchmark_path, str) or not (root / benchmark_path).is_dir():
            failures.append(f"Public benchmark input path is missing: {bundle_id}.")
        if bundle.get("security_claim") is not False:
            failures.append(f"Public benchmark bundle makes a claim: {bundle_id}.")
        if bundle.get("publishes_private_candidates") is not False:
            failures.append(
                f"Public benchmark bundle may publish private candidates: {bundle_id}."
            )
        if bundle.get("redacted_records") != 0:
            failures.append(
                f"Public benchmark bundle contains redacted records: {bundle_id}."
            )
        manifest_sha = bundle.get("manifest_sha256")
        if not isinstance(manifest_sha, str) or len(manifest_sha) != 64:
            failures.append(
                f"Public benchmark bundle lacks checksum digest: {bundle_id}."
            )
        trace_sha = bundle.get("trace_public_sha256")
        if not isinstance(trace_sha, str) or len(trace_sha) != 64:
            failures.append(
                f"Public benchmark bundle lacks public trace digest: {bundle_id}."
            )
        commands = bundle.get("regenerate_commands", [])
        if not isinstance(commands, list) or len(commands) != 2:
            failures.append(
                f"Public benchmark bundle lacks regenerate commands: {bundle_id}."
            )
        record_count += int(bundle.get("record_count", 0))

    if summary.get("record_count") != record_count:
        failures.append("Public benchmark manifest record count is inconsistent.")
    if summary.get("security_claim") is not False:
        failures.append("Public benchmark manifest summary advertises a claim.")

    return _check(
        check_id="public-benchmark-manifest",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="docs/public_benchmark_manifest.json",
        detail=(
            "Public benchmark v0 manifest is checked in, synchronized with "
            "public run bundles, and preserves no-private/no-claim boundaries."
        ),
        evidence={
            "bundle_count": summary.get("bundle_count"),
            "families": summary.get("families", []),
            "record_count": summary.get("record_count"),
        },
        failures=failures,
    )


def _public_run_export(root: Path) -> dict[str, Any]:
    verification = verify_public_run_export(
        Path("public/run_export"),
        root=root,
    )
    failures = list(verification["failures"])
    manifest_path = root / "public" / "run_export" / "manifest.json"
    manifest = _read_json(manifest_path) if manifest_path.is_file() else {}
    safety = _dict_or_empty(manifest.get("safety"))
    summary = _dict_or_empty(manifest.get("summary"))
    if safety.get("contains_private_traces") is not False:
        failures.append("Public run export may expose private traces.")
    if safety.get("publishes_private_candidates") is not False:
        failures.append("Public run export may publish private candidates.")
    if safety.get("security_claim") is not False:
        failures.append("Public run export advertises a security claim.")

    return _check(
        check_id="public-run-export",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="public/run_export",
        detail=(
            "Flat public run export is checked in for Prime-style autonomous "
            "run review while preserving no-private/no-claim boundaries."
        ),
        evidence={
            "bundle_count": summary.get("bundle_count"),
            "contains_private_traces": safety.get("contains_private_traces"),
            "run_count": summary.get("run_count"),
            "security_claim": safety.get("security_claim"),
        },
        failures=failures,
    )


def _evolution_heldout_rescore(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "archive_schema": EVOLUTION_ARCHIVE_SCHEMA,
        "arbitrary_code_execution": False,
        "heldout_rescore_schema": HELDOUT_RESCORE_SCHEMA,
        "requires_parent_link": True,
        "rescored_elites": 0,
    }

    try:
        plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "lattice_primal_usvp_toy.json"
            ).read_text(encoding="utf-8")
        )
        training = _audit_trace_record(
            plan=plan,
            run_id="release-audit-training",
            candidate_id="release-audit-candidate",
            parent_id=None,
            score=-90.0,
            accepted=True,
        )
        archive = build_evolution_archive([training], run_id="release-audit-training")
        heldout = _audit_trace_record(
            plan=plan,
            run_id="release-audit-heldout",
            candidate_id="release-audit-candidate-heldout",
            parent_id=training.candidate_id,
            score=-92.0,
            accepted=True,
        )
        report = build_heldout_rescore(
            archive,
            [heldout],
            run_id="release-audit-heldout-rescore",
        )
    except Exception as exc:  # noqa: BLE001 - audit must report smoke failures.
        failures.append(f"Held-out rescore smoke failed: {exc}")
    else:
        evidence["rescored_elites"] = report.summary["rescored_elite_count"]
        if archive.schema_version != EVOLUTION_ARCHIVE_SCHEMA:
            failures.append("Evolution archive schema version is unexpected.")
        if report.schema_version != HELDOUT_RESCORE_SCHEMA:
            failures.append("Held-out rescore schema version is unexpected.")
        if report.summary["rescored_elite_count"] != 1:
            failures.append("Held-out rescore did not rescore exactly one elite.")
        if report.summary["unmatched_heldout_record_count"] != 0:
            failures.append("Held-out rescore failed explicit parent linkage.")
        if report.global_best_by_heldout is None:
            failures.append("Held-out rescore did not rank a held-out elite.")

    return _check(
        check_id="evolution-heldout-rescore",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="src/agades_pqc_gym/evolution/rescore.py",
        detail=(
            "Evolution archives have a deterministic held-out rescore layer "
            "that only aggregates explicit TraceRecord parent links and does "
            "not execute arbitrary candidate code."
        ),
        evidence=evidence,
        failures=failures,
    )


def _evolution_heldout_batch(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "arbitrary_code_execution": False,
        "heldout_candidates": 0,
        "private_rebased_plan": False,
        "requires_same_family": True,
        "source_parent_link": None,
    }

    try:
        plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "lattice_primal_usvp_toy.json"
            ).read_text(encoding="utf-8")
        )
        heldout_target = TargetSpec.model_validate_json(
            (root / "benchmarks" / "lattice_toy_lwe" / "lwe_n96_q769.json").read_text(
                encoding="utf-8"
            )
        )
        training = _audit_trace_record(
            plan=plan,
            run_id="release-audit-training",
            candidate_id="release-audit-candidate",
            parent_id=None,
            score=-90.0,
            accepted=True,
        )
        archive = build_evolution_archive([training], run_id="release-audit-training")
        candidates = build_heldout_candidate_plans(
            archive,
            [training],
            [heldout_target],
        )
    except Exception as exc:  # noqa: BLE001 - audit must report smoke failures.
        failures.append(f"Held-out batch smoke failed: {exc}")
    else:
        evidence["heldout_candidates"] = len(candidates)
        if candidates:
            candidate = candidates[0]
            evidence["private_rebased_plan"] = (
                candidate.attack_plan.metadata.public is False
            )
            evidence["source_parent_link"] = candidate.parent_id
            if candidate.parent_id != training.candidate_id:
                failures.append("Held-out candidate lacks source parent link.")
            if candidate.attack_plan.target != heldout_target:
                failures.append("Held-out candidate target was not rebased.")
            if candidate.attack_plan.metadata.public is not False:
                failures.append("Held-out candidate plan is not private.")
        if len(candidates) != 1:
            failures.append("Held-out batch did not produce exactly one candidate.")

    return _check(
        check_id="evolution-heldout-batch",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="src/agades_pqc_gym/evolution/heldout.py",
        detail=(
            "Evolution archives can produce private held-out candidate plans "
            "from source traces with same-family target rebasing, explicit "
            "parent links, and no arbitrary candidate code execution."
        ),
        evidence=evidence,
        failures=failures,
    )


def _evolution_heldout_schedule(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "approval_gates": 0,
        "ready_to_run": False,
        "scheduled_candidates": 0,
        "trace_output_private": False,
    }

    try:
        plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "lattice_primal_usvp_toy.json"
            ).read_text(encoding="utf-8")
        )
        training = _audit_trace_record(
            plan=plan,
            run_id="release-audit-training",
            candidate_id="release-audit-candidate",
            parent_id=None,
            score=-90.0,
            accepted=True,
        )
        archive = build_evolution_archive([training], run_id="release-audit-training")
        policy = build_private_run_policy()
        with tempfile.TemporaryDirectory() as schedule_dir:
            schedule_root = Path(schedule_dir)
            archive_path = schedule_root / "archive.json"
            source_trace_path = schedule_root / "source_trace.jsonl"
            review_log_path = Path("private/runs/release_audit_review_log.json")
            archive_path.write_text(
                archive.model_dump_json(indent=2) + "\n",
                encoding="utf-8",
            )
            source_trace_path.write_text(
                training.model_dump_json() + "\n",
                encoding="utf-8",
            )
            write_heldout_review_log(
                schedule_root / review_log_path,
                approvals=policy["scheduler_policy"]["approval_gates"],
                reviewed_by="release-audit",
                review_id="release-audit-heldout-review",
                policy=policy,
                root=schedule_root,
            )
            schedule = build_heldout_schedule(
                archive_path=archive_path,
                source_trace_path=source_trace_path,
                heldout_targets_path=root
                / "benchmarks"
                / "lattice_toy_lwe"
                / "lwe_n96_q769.json",
                policy=policy,
                trace_out=Path("private/traces/release_audit_heldout_trace.jsonl"),
                rescore_out=Path("private/reports/release_audit_heldout_rescore.json"),
                approvals=policy["scheduler_policy"]["approval_gates"],
                review_log_path=review_log_path,
                root=schedule_root,
                run_id="release-audit-heldout-schedule",
            )
    except Exception as exc:  # noqa: BLE001 - audit must report smoke failures.
        failures.append(f"Held-out schedule smoke failed: {exc}")
    else:
        outputs = schedule["outputs"]
        evidence = {
            "approval_gates": len(schedule["approval_gates"]["required"]),
            "ready_to_run": schedule["ready_to_run"],
            "review_log_attached": bool(schedule["review_log"]["sha256"]),
            "scheduled_candidates": schedule["summary"]["scheduled_candidates"],
            "trace_output_private": outputs["heldout_trace"].startswith(
                "private/traces/"
            ),
        }
        if schedule["ready_to_run"] is not True:
            failures.append("Held-out schedule is not ready after policy approvals.")
        if schedule["summary"]["scheduled_candidates"] != 1:
            failures.append("Held-out schedule did not schedule exactly one candidate.")
        if not schedule["review_log"]["sha256"]:
            failures.append("Held-out schedule did not attach a review log digest.")
        if not outputs["heldout_trace"].startswith("private/traces/"):
            failures.append("Held-out schedule trace output is not private.")

    return _check(
        check_id="evolution-heldout-schedule",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="src/agades_pqc_gym/evolution/scheduler.py",
        detail=(
            "Held-out re-evaluation scheduling consumes the private-run policy, "
            "requires review gates, and only targets private trace/report roots."
        ),
        evidence=evidence,
        failures=failures,
    )


def _evolution_heldout_schedule_run(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "arbitrary_code_execution": False,
        "external_network_access": False,
        "heldout_records": 0,
        "rescored_elites": 0,
        "review_packet_accepted": None,
        "review_packet_contains_private_scores": None,
        "review_packet_public_release_ok": None,
        "review_packet_trace_digest_present": False,
        "shell_commands_executed": False,
        "trace_output_private": False,
    }

    try:
        plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "lattice_primal_usvp_toy.json"
            ).read_text(encoding="utf-8")
        )
        training = _audit_trace_record(
            plan=plan,
            run_id="release-audit-training",
            candidate_id="release-audit-candidate",
            parent_id=None,
            score=-90.0,
            accepted=True,
        )
        archive = build_evolution_archive([training], run_id="release-audit-training")
        policy = build_private_run_policy()
        with tempfile.TemporaryDirectory() as schedule_dir:
            schedule_root = Path(schedule_dir)
            archive_path = schedule_root / "archive.json"
            source_trace_path = schedule_root / "source_trace.jsonl"
            schedule_path = schedule_root / "private" / "runs" / "schedule.json"
            review_log_path = Path("private/runs/release_audit_review_log.json")
            archive_path.write_text(
                archive.model_dump_json(indent=2) + "\n",
                encoding="utf-8",
            )
            source_trace_path.write_text(
                training.model_dump_json() + "\n",
                encoding="utf-8",
            )
            write_heldout_review_log(
                schedule_root / review_log_path,
                approvals=policy["scheduler_policy"]["approval_gates"],
                reviewed_by="release-audit",
                review_id="release-audit-heldout-review",
                policy=policy,
                root=schedule_root,
            )
            write_heldout_schedule(
                schedule_path,
                archive_path=archive_path,
                source_trace_path=source_trace_path,
                heldout_targets_path=root
                / "benchmarks"
                / "lattice_toy_lwe"
                / "lwe_n96_q769.json",
                policy=policy,
                trace_out=Path("private/traces/release_audit_heldout_trace.jsonl"),
                rescore_out=Path("private/reports/release_audit_heldout_rescore.json"),
                approvals=policy["scheduler_policy"]["approval_gates"],
                review_log_path=review_log_path,
                root=schedule_root,
                run_id="release-audit-heldout-schedule",
            )
            run_report = run_heldout_schedule(
                schedule_path,
                policy=policy,
                estimator=MockEstimatorAdapter(),
                root=schedule_root,
            )
            review_packet_path = Path(
                "private/reports/release_audit_heldout_review_packet.json"
            )
            review_packet = write_heldout_review_packet(
                review_packet_path,
                schedule_path=schedule_path,
                policy=policy,
                root=schedule_root,
                reviewer_label="release-audit-heldout-review",
            )
            review_packet_verification = verify_heldout_review_packet(
                schedule_root / review_packet_path,
                schedule_path=schedule_path,
                policy=policy,
                root=schedule_root,
            )
    except Exception as exc:  # noqa: BLE001 - audit must report smoke failures.
        failures.append(f"Held-out schedule run smoke failed: {exc}")
    else:
        outputs = run_report["outputs"]
        execution = run_report["execution"]
        summary = run_report["summary"]
        evidence = {
            "arbitrary_code_execution": execution["arbitrary_code_execution"],
            "external_network_access": execution["external_network_access"],
            "heldout_records": summary["heldout_records"],
            "rescored_elites": summary["rescored_elites"],
            "review_packet_accepted": review_packet_verification["accepted"],
            "review_packet_contains_private_scores": review_packet_verification[
                "summary"
            ]["contains_private_scores"],
            "review_packet_public_release_ok": review_packet["safety"][
                "public_release_ok"
            ],
            "review_packet_trace_digest_present": len(
                review_packet["artifacts"]["heldout_trace"]["sha256"]
            )
            == 64,
            "shell_commands_executed": execution["shell_commands_executed"],
            "trace_output_private": outputs["heldout_trace"].startswith(
                "private/traces/"
            ),
        }
        if execution["shell_commands_executed"] is not False:
            failures.append("Held-out schedule runner executed shell commands.")
        if summary["heldout_records"] != 1:
            failures.append("Held-out schedule runner did not write one trace record.")
        if summary["rescored_elites"] != 1:
            failures.append("Held-out schedule runner did not rescore one elite.")
        if not outputs["heldout_trace"].startswith("private/traces/"):
            failures.append("Held-out schedule runner trace output is not private.")
        if evidence["review_packet_accepted"] is not True:
            failures.append("Held-out review packet verifier must accept.")
        if evidence["review_packet_contains_private_scores"] is not False:
            failures.append("Held-out review packet must not contain private scores.")
        if evidence["review_packet_public_release_ok"] is not False:
            failures.append("Held-out review packet must not be public-release-ready.")
        if evidence["review_packet_trace_digest_present"] is not True:
            failures.append(
                "Held-out review packet must include held-out trace digest."
            )

    return _check(
        check_id="evolution-heldout-schedule-run",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="src/agades_pqc_gym/evolution/scheduler.py",
        detail=(
            "Reviewed held-out schedules can be consumed through typed Python "
            "APIs without executing shell command strings, external networking, "
            "or public trace outputs."
        ),
        evidence=evidence,
        failures=failures,
    )


def _evolution_heldout_cron_plan(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "cron_expression": None,
        "manual_install_required": False,
        "review_log_revalidated": False,
        "schedule_trigger": None,
        "system_crontab_written": True,
        "trace_output_private": False,
    }

    try:
        plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "lattice_primal_usvp_toy.json"
            ).read_text(encoding="utf-8")
        )
        training = _audit_trace_record(
            plan=plan,
            run_id="release-audit-training",
            candidate_id="release-audit-candidate",
            parent_id=None,
            score=-90.0,
            accepted=True,
        )
        archive = build_evolution_archive([training], run_id="release-audit-training")
        policy = build_private_run_policy()
        with tempfile.TemporaryDirectory() as schedule_dir:
            schedule_root = Path(schedule_dir)
            archive_path = schedule_root / "archive.json"
            source_trace_path = schedule_root / "source_trace.jsonl"
            schedule_path = schedule_root / "private" / "runs" / "schedule.json"
            cron_plan_path = Path("private/runs/heldout_cron_plan.json")
            review_log_path = Path("private/runs/release_audit_review_log.json")
            archive_path.write_text(
                archive.model_dump_json(indent=2) + "\n",
                encoding="utf-8",
            )
            source_trace_path.write_text(
                training.model_dump_json() + "\n",
                encoding="utf-8",
            )
            write_heldout_review_log(
                schedule_root / review_log_path,
                approvals=policy["scheduler_policy"]["approval_gates"],
                reviewed_by="release-audit",
                review_id="release-audit-heldout-review",
                policy=policy,
                root=schedule_root,
            )
            write_heldout_schedule(
                schedule_path,
                archive_path=archive_path,
                source_trace_path=source_trace_path,
                heldout_targets_path=root
                / "benchmarks"
                / "lattice_toy_lwe"
                / "lwe_n96_q769.json",
                policy=policy,
                trace_out=Path("private/traces/release_audit_heldout_trace.jsonl"),
                rescore_out=Path("private/reports/release_audit_heldout_rescore.json"),
                approvals=policy["scheduler_policy"]["approval_gates"],
                review_log_path=review_log_path,
                trigger="local_cron_after_review",
                root=schedule_root,
                run_id="release-audit-heldout-schedule",
            )
            cron_plan = write_heldout_cron_plan(
                cron_plan_path,
                schedule_path=Path("private/runs/schedule.json"),
                policy=policy,
                policy_path=Path("docs/private_run_policy.json"),
                minute=17,
                every_hours=6,
                log_path=Path("private/runs/heldout_cron.log"),
                root=schedule_root,
            )
    except Exception as exc:  # noqa: BLE001 - audit must report smoke failures.
        failures.append(f"Held-out cron plan smoke failed: {exc}")
    else:
        schedule = cron_plan["schedule"]
        installation = cron_plan["installation"]
        outputs_private = schedule["outputs"]["heldout_trace"].startswith(
            "private/traces/"
        )
        evidence = {
            "cron_expression": cron_plan["cron"]["expression"],
            "manual_install_required": installation["requires_manual_install"],
            "review_log_revalidated": bool(schedule["review_log_path"]),
            "schedule_trigger": schedule["trigger"],
            "system_crontab_written": installation["writes_system_crontab"],
            "trace_output_private": outputs_private,
        }
        if cron_plan["cron"]["expression"] != "17 */6 * * *":
            failures.append("Held-out cron plan expression is not deterministic.")
        if schedule["trigger"] != "local_cron_after_review":
            failures.append("Held-out cron plan did not require cron-reviewed trigger.")
        if installation["writes_system_crontab"] is not False:
            failures.append("Held-out cron plan wrote to the system crontab.")
        if installation["requires_manual_install"] is not True:
            failures.append("Held-out cron plan lacks manual install boundary.")
        if (
            "agades-pqc heldout-run-schedule"
            not in cron_plan["command"]["crontab_entry"]
        ):
            failures.append("Held-out cron plan does not call heldout-run-schedule.")

    return _check(
        check_id="evolution-heldout-cron-plan",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="src/agades_pqc_gym/evolution/cron.py",
        detail=(
            "Reviewed held-out schedules can produce a private local-cron plan "
            "for manual installation without editing the system crontab or "
            "weakening review-log, no-network, or private-output boundaries."
        ),
        evidence=evidence,
        failures=failures,
    )


def _private_evolution_campaign_plan(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "campaign_schema": PRIVATE_EVOLUTION_CAMPAIGN_PLAN_SCHEMA,
        "compatible_target_family_count": 0,
        "heldout_target_count": 0,
        "outputs_private": False,
        "private_plan": False,
        "public_release_ok": None,
        "review_log_attached": False,
        "seed_family_coverage_complete": False,
        "seed_mutation_candidate_count": 0,
        "seed_plan_count": 0,
        "shell_commands_executed": None,
        "step_count": 0,
        "verification_accepted": False,
    }

    try:
        policy = build_private_run_policy()
        with tempfile.TemporaryDirectory() as campaign_dir:
            campaign_root = Path(campaign_dir)
            review_log_path = Path("private/runs/release_audit_review_log.json")
            campaign_plan_path = Path(
                "private/runs/release_audit_campaign/campaign_plan.json"
            )
            write_heldout_review_log(
                campaign_root / review_log_path,
                approvals=policy["scheduler_policy"]["approval_gates"],
                reviewed_by="release-audit",
                review_id="release-audit-campaign-review",
                policy=policy,
                root=campaign_root,
            )
            plan = write_private_evolution_campaign_plan(
                campaign_plan_path,
                seed_candidates_path=root
                / "examples"
                / "attack_plans"
                / "lattice_primal_usvp_toy.json",
                heldout_targets_path=root
                / "benchmarks"
                / "lattice_toy_lwe"
                / "lwe_n96_q769.json",
                policy=policy,
                review_log_path=review_log_path,
                root=campaign_root,
                run_id="release-audit-campaign",
                policy_path=Path("docs/private_run_policy.json"),
            )
            verification = verify_private_evolution_campaign_plan(
                campaign_root / campaign_plan_path,
                policy=policy,
                root=campaign_root,
            )
    except Exception as exc:  # noqa: BLE001 - audit must report smoke failures.
        failures.append(f"Private evolution campaign plan smoke failed: {exc}")
    else:
        outputs = plan["outputs"]
        safety = plan["safety"]
        summary = plan["summary"]
        outputs_private = all(
            value.startswith(
                (
                    "private/candidates/",
                    "private/reports/",
                    "private/runs/",
                    "private/traces/",
                )
            )
            for value in outputs.values()
        )
        evidence = {
            "campaign_schema": plan["schema_version"],
            "compatible_target_family_count": summary["compatible_target_family_count"],
            "heldout_target_count": summary["heldout_target_count"],
            "outputs_private": outputs_private,
            "private_plan": safety["private_plan"],
            "public_release_ok": safety["public_release_ok"],
            "review_log_attached": bool(plan["review_log"]["sha256"]),
            "seed_family_coverage_complete": summary["seed_family_coverage_complete"],
            "seed_mutation_candidate_count": summary["seed_mutation_candidate_count"],
            "seed_plan_count": summary["seed_plan_count"],
            "shell_commands_executed": safety["shell_commands_executed"],
            "step_count": summary["step_count"],
            "verification_accepted": verification["accepted"],
        }
        if plan["schema_version"] != PRIVATE_EVOLUTION_CAMPAIGN_PLAN_SCHEMA:
            failures.append("Private evolution campaign plan schema drifted.")
        if summary["step_count"] != 7:
            failures.append("Private evolution campaign plan step count drifted.")
        if not outputs_private:
            failures.append("Private evolution campaign plan has non-private outputs.")
        if safety["shell_commands_executed"] is not False:
            failures.append("Private evolution campaign plan executed shell commands.")
        if safety["public_release_ok"] is not False:
            failures.append(
                "Private evolution campaign plan must not be public-release-ready."
            )
        if evidence["review_log_attached"] is not True:
            failures.append("Private evolution campaign plan lacks review-log digest.")
        if evidence["seed_mutation_candidate_count"] < 1:
            failures.append(
                "Private evolution campaign plan has no reviewed seed mutations."
            )
        if evidence["compatible_target_family_count"] < 1:
            failures.append(
                "Private evolution campaign plan has no compatible held-out "
                "target families."
            )
        if evidence["seed_family_coverage_complete"] is not True:
            failures.append(
                "Private evolution campaign plan lacks complete seed-family "
                "held-out coverage."
            )
        if verification["accepted"] is not True:
            failures.extend(verification["failures"])

    return _check(
        check_id="private-evolution-campaign-plan",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="src/agades_pqc_gym/evolution/campaign.py",
        detail=(
            "Private long-running evolution campaigns can be planned as reviewed, "
            "non-executing argv steps with private-only outputs before any trace "
            "collection or held-out run starts."
        ),
        evidence=evidence,
        failures=failures,
    )


def _evolution_archive_snapshot(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "archive_schema": EVOLUTION_ARCHIVE_SCHEMA,
        "contains_attack_plans": True,
        "contains_trace_payloads": True,
        "digest_only_artifacts": 0,
        "private_snapshot": False,
        "public_release_ok": True,
        "retention_days": None,
        "review_log_attached": False,
        "snapshot_schema": PRIVATE_ARCHIVE_SNAPSHOT_SCHEMA,
        "trace_links_complete": False,
        "writes_only_allowed_private_roots": False,
    }

    try:
        plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "lattice_primal_usvp_toy.json"
            ).read_text(encoding="utf-8")
        )
        training = _audit_trace_record(
            plan=plan,
            run_id="release-audit-training",
            candidate_id="release-audit-candidate",
            parent_id=None,
            score=-90.0,
            accepted=True,
        )
        archive = build_evolution_archive([training], run_id="release-audit-training")
        policy = build_private_run_policy()
        with tempfile.TemporaryDirectory() as snapshot_dir:
            snapshot_root = Path(snapshot_dir)
            archive_path = Path("runs/evolution_archive.json")
            source_trace_path = Path("runs/evolution_trace.jsonl")
            review_log_path = Path("private/runs/release_audit_review_log.json")
            snapshot_path = Path("private/runs/archive_snapshot.json")
            (snapshot_root / archive_path).parent.mkdir(parents=True, exist_ok=True)
            (snapshot_root / source_trace_path).parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            (snapshot_root / archive_path).write_text(
                archive.model_dump_json(indent=2) + "\n",
                encoding="utf-8",
            )
            (snapshot_root / source_trace_path).write_text(
                training.model_dump_json() + "\n",
                encoding="utf-8",
            )
            write_heldout_review_log(
                snapshot_root / review_log_path,
                approvals=policy["scheduler_policy"]["approval_gates"],
                reviewed_by="release-audit",
                review_id="release-audit-archive-snapshot-review",
                policy=policy,
                root=snapshot_root,
            )
            snapshot = write_private_archive_snapshot(
                snapshot_path,
                archive_path=archive_path,
                source_trace_path=source_trace_path,
                review_log_path=review_log_path,
                policy=policy,
                root=snapshot_root,
                run_id="release-audit-archive-snapshot",
            )
            reloaded = json.loads(
                (snapshot_root / snapshot_path).read_text(encoding="utf-8")
            )
    except Exception as exc:  # noqa: BLE001 - audit must report smoke failures.
        failures.append(f"Private archive snapshot smoke failed: {exc}")
    else:
        if snapshot != reloaded:
            failures.append("Private archive snapshot is not deterministic on disk.")
        encoded_snapshot = json.dumps(snapshot, sort_keys=True)
        inputs = snapshot.get("inputs", {})
        review_log = inputs.get("review_log", {})
        safety = snapshot.get("safety", {})
        retention = snapshot.get("retention", {})
        summary = snapshot.get("summary", {})
        trace_link_integrity = snapshot.get("trace_link_integrity", {})
        evidence = {
            "archive_schema": inputs.get("archive", {}).get("schema_version"),
            "contains_attack_plans": '"attack_plan":' in encoded_snapshot,
            "contains_trace_payloads": safety.get("contains_trace_payloads"),
            "digest_only_artifacts": summary.get("artifact_count"),
            "private_snapshot": summary.get("private_snapshot"),
            "public_release_ok": summary.get("public_release_ok"),
            "retention_days": retention.get("archive_snapshot_max_age_days"),
            "review_log_attached": bool(review_log.get("sha256")),
            "snapshot_schema": snapshot.get("schema_version"),
            "trace_links_complete": trace_link_integrity.get("complete"),
            "writes_only_allowed_private_roots": safety.get(
                "writes_only_allowed_private_roots"
            ),
        }
        if evidence["snapshot_schema"] != PRIVATE_ARCHIVE_SNAPSHOT_SCHEMA:
            failures.append("Private archive snapshot schema is unexpected.")
        if evidence["archive_schema"] != EVOLUTION_ARCHIVE_SCHEMA:
            failures.append("Private archive snapshot archive schema is unexpected.")
        if evidence["digest_only_artifacts"] != 3:
            failures.append("Private archive snapshot should record three digests.")
        if evidence["review_log_attached"] is not True:
            failures.append("Private archive snapshot lacks review-log digest.")
        if evidence["trace_links_complete"] is not True:
            failures.append("Private archive snapshot trace links are incomplete.")
        if evidence["private_snapshot"] is not True:
            failures.append("Private archive snapshot is not marked private.")
        if evidence["public_release_ok"] is not False:
            failures.append("Private archive snapshot is marked public release ok.")
        if evidence["contains_trace_payloads"] is not False:
            failures.append("Private archive snapshot includes trace payloads.")
        if evidence["contains_attack_plans"] is not False:
            failures.append("Private archive snapshot includes AttackPlan payloads.")
        if evidence["writes_only_allowed_private_roots"] is not True:
            failures.append("Private archive snapshot does not enforce private roots.")
        if evidence["retention_days"] != 90:
            failures.append("Private archive snapshot retention limit drifted.")

    return _check(
        check_id="evolution-archive-snapshot",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="src/agades_pqc_gym/evolution/snapshot.py",
        detail=(
            "Reviewed evolution archives can be snapshotted to a private "
            "digest-only manifest with review-log evidence, retention metadata, "
            "and complete archive-to-trace link checks, without trace payloads "
            "or public publication semantics."
        ),
        evidence=evidence,
        failures=failures,
    )


def _evolution_mutation_batch(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "arbitrary_code_execution": False,
        "candidate_count": 0,
        "generation": 1,
        "fixture_bound_skipped": 0,
        "mutated_parameters": [],
        "private_candidates": False,
        "schema_only_skipped": 0,
        "skipped_count": 0,
        "source_count": 0,
    }

    try:
        lattice_plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "lattice_primal_usvp_toy.json"
            ).read_text(encoding="utf-8")
        )
        bkw_plan = AttackPlan.model_validate_json(
            (root / "examples" / "attack_plans" / "lattice_bkw_toy.json").read_text(
                encoding="utf-8"
            )
        )
        dual_hybrid_plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "lattice_dual_hybrid_toy.json"
            ).read_text(encoding="utf-8")
        )
        code_based_lee_brickell_plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "code_based_lee_brickell_toy.json"
            ).read_text(encoding="utf-8")
        )
        code_based_dumer_plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "code_based_dumer_toy.json"
            ).read_text(encoding="utf-8")
        )
        code_based_bjmm_plan = AttackPlan.model_validate_json(
            (root / "examples" / "attack_plans" / "code_based_bjmm_toy.json").read_text(
                encoding="utf-8"
            )
        )
        code_based_prange_plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "code_based_prange_toy.json"
            ).read_text(encoding="utf-8")
        )
        code_based_prange_fixture_plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "code_based_prange_toy_n15.json"
            ).read_text(encoding="utf-8")
        )
        multivariate_mq_hybrid_plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "multivariate_mq_hybrid_toy.json"
            ).read_text(encoding="utf-8")
        )
        multivariate_mq_fixture_plan = AttackPlan.model_validate_json(
            (
                root
                / "examples"
                / "attack_plans"
                / "multivariate_mq_hybrid_gf2_toy.json"
            ).read_text(encoding="utf-8")
        )
        multivariate_mq_plan = AttackPlan.model_validate_json(
            (root / "examples" / "attack_plans" / "multivariate_mq_toy.json").read_text(
                encoding="utf-8"
            )
        )
        multivariate_mq_degree_bound_plan = AttackPlan.model_validate_json(
            (
                root
                / "examples"
                / "attack_plans"
                / "multivariate_mq_degree_bound_toy.json"
            ).read_text(encoding="utf-8")
        )
        hash_based_preimage_plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "hash_based_preimage_toy.json"
            ).read_text(encoding="utf-8")
        )
        hash_based_collision_fixture_plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "hash_based_collision_toy.json"
            ).read_text(encoding="utf-8")
        )
        implementation_security_kat_plan = AttackPlan.model_validate_json(
            (
                root
                / "examples"
                / "attack_plans"
                / "implementation_security_kat_toy.json"
            ).read_text(encoding="utf-8")
        )
        implementation_security_kat_fixture_plan = AttackPlan.model_validate_json(
            (
                root
                / "examples"
                / "attack_plans"
                / "implementation_security_mldsa_kat_toy.json"
            ).read_text(encoding="utf-8")
        )
        isogeny_historical_plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "isogeny_historical_toy.json"
            ).read_text(encoding="utf-8")
        )
        isogeny_historical_fixture_plan = AttackPlan.model_validate_json(
            (
                root
                / "examples"
                / "attack_plans"
                / "isogeny_historical_commutative_walk_toy.json"
            ).read_text(encoding="utf-8")
        )
        schema_only_plan = AttackPlan.model_validate_json(
            (
                root
                / "examples"
                / "attack_plans"
                / "lattice_ntru_schema_placeholder.json"
            ).read_text(encoding="utf-8")
        )
        batch = build_candidate_mutation_batch(
            [
                lattice_plan,
                bkw_plan,
                dual_hybrid_plan,
                code_based_lee_brickell_plan,
                code_based_dumer_plan,
                code_based_bjmm_plan,
                code_based_prange_plan,
                code_based_prange_fixture_plan,
                multivariate_mq_hybrid_plan,
                multivariate_mq_fixture_plan,
                multivariate_mq_plan,
                multivariate_mq_degree_bound_plan,
                hash_based_preimage_plan,
                hash_based_collision_fixture_plan,
                implementation_security_kat_plan,
                implementation_security_kat_fixture_plan,
                isogeny_historical_plan,
                isogeny_historical_fixture_plan,
                schema_only_plan,
            ],
            run_id="release-audit-mutation",
            generation=1,
            max_mutations_per_plan=6,
        )
    except Exception as exc:  # noqa: BLE001 - audit must report smoke failures.
        failures.append(f"Candidate mutation batch smoke failed: {exc}")
    else:
        evidence["candidate_count"] = batch.summary["candidate_count"]
        evidence["source_count"] = batch.summary["source_count"]
        evidence["skipped_count"] = batch.summary["skipped_count"]
        evidence["schema_only_skipped"] = sum(
            skipped.reason.startswith("schema-only") for skipped in batch.skipped
        )
        evidence["fixture_bound_skipped"] = sum(
            skipped.reason.startswith("fixture-bound") for skipped in batch.skipped
        )
        evidence["mutated_parameters"] = _mutation_batch_parameters(batch)
        evidence["private_candidates"] = all(
            candidate.attack_plan.metadata.public is False
            for candidate in batch.candidates
        )
        if batch.schema_version != CANDIDATE_MUTATION_BATCH_SCHEMA:
            failures.append("Candidate mutation batch schema version is unexpected.")
        if batch.summary["candidate_count"] != 35:
            failures.append(
                "Candidate mutation batch did not produce thirty-five candidates."
            )
        if batch.summary["source_count"] != 19:
            failures.append(
                "Candidate mutation batch did not inspect nineteen sources."
            )
        if batch.summary["skipped_count"] != 6:
            failures.append(
                "Candidate mutation batch did not skip six non-mutatable inputs."
            )
        if evidence["schema_only_skipped"] != 1:
            failures.append("Candidate mutation batch did not skip schema-only input.")
        if evidence["fixture_bound_skipped"] != 5:
            failures.append(
                "Candidate mutation batch did not skip fixture-bound inputs."
            )
        if evidence["mutated_parameters"] != [
            "beta",
            "block_size",
            "branching_factor",
            "degree_bound",
            "ell",
            "equations",
            "guessed_variables",
            "n",
            "p",
            "q_prime",
            "representation_count",
            "variables",
            "vector_count",
            "w",
            "walk_length",
            "zeta",
        ]:
            failures.append("Candidate mutation batch lacks reviewed knob coverage.")
        if not evidence["private_candidates"]:
            failures.append("Candidate mutation batch produced public candidates.")
        if any(
            candidate.attack_plan.claims.external_claim
            for candidate in batch.candidates
        ):
            failures.append("Candidate mutation batch preserved pre-evaluation claims.")

    return _check(
        check_id="evolution-mutation-batch",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="src/agades_pqc_gym/evolution/mutation.py",
        detail=(
            "Evolution can generate deterministic private JSON AttackPlan "
            "mutations from reviewed lattice, code-based, multivariate, "
            "hash-based, implementation-security, and historical-isogeny toy "
            "rules while classifying unsupported, schema-only, and fixture-bound "
            "sources without executing arbitrary candidate code."
        ),
        evidence=evidence,
        failures=failures,
    )


def _evolution_archive_mutation_batch(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "arbitrary_code_execution": False,
        "candidate_count": 0,
        "generation": None,
        "parent_candidate_id": None,
        "parent_trace_linked": False,
        "private_candidates": False,
        "source_count": 0,
    }

    try:
        plan = AttackPlan.model_validate_json(
            (
                root / "examples" / "attack_plans" / "lattice_dual_hybrid_toy.json"
            ).read_text(encoding="utf-8")
        )
        training = _audit_trace_record(
            plan=plan,
            run_id="release-audit-training",
            candidate_id="release-audit-elite",
            parent_id=None,
            score=-88.0,
            accepted=True,
        )
        archive = build_evolution_archive([training], run_id="release-audit-training")
        batch = build_archive_candidate_mutation_batch(
            archive,
            [training],
            run_id="release-audit-archive-mutation",
            max_mutations_per_elite=6,
        )
    except Exception as exc:  # noqa: BLE001 - audit must report smoke failures.
        failures.append(f"Archive mutation batch smoke failed: {exc}")
    else:
        evidence["candidate_count"] = batch.summary["candidate_count"]
        evidence["source_count"] = batch.summary["source_count"]
        evidence["private_candidates"] = all(
            candidate.attack_plan.metadata.public is False
            for candidate in batch.candidates
        )
        evidence["parent_trace_linked"] = all(
            candidate.parent_candidate_id == training.candidate_id
            and candidate.parent_trace_id == training.trace_id
            for candidate in batch.candidates
        )
        if batch.candidates:
            evidence["generation"] = batch.candidates[0].generation
            evidence["parent_candidate_id"] = batch.candidates[0].parent_candidate_id

        if batch.schema_version != CANDIDATE_MUTATION_BATCH_SCHEMA:
            failures.append("Archive mutation batch schema version is unexpected.")
        if batch.summary["candidate_count"] != 6:
            failures.append("Archive mutation batch did not produce six candidates.")
        if batch.summary["source_count"] != 1:
            failures.append("Archive mutation batch did not inspect one archive elite.")
        if batch.summary["skipped_count"] != 0:
            failures.append("Archive mutation batch skipped a mutatable elite.")
        if any(candidate.generation != 1 for candidate in batch.candidates):
            failures.append("Archive mutation batch did not advance generation.")
        if not evidence["parent_trace_linked"]:
            failures.append("Archive mutation batch lacks source trace parent links.")
        if not evidence["private_candidates"]:
            failures.append("Archive mutation batch produced public candidates.")
        if any(
            candidate.attack_plan.claims.external_claim
            for candidate in batch.candidates
        ):
            failures.append("Archive mutation batch preserved pre-evaluation claims.")

    return _check(
        check_id="evolution-archive-mutation-batch",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="src/agades_pqc_gym/evolution/mutation.py",
        detail=(
            "MAP-Elites archives can generate the next private mutation batch "
            "from exact source TraceRecord parents, preserving elite candidate "
            "and trace links without arbitrary candidate code execution."
        ),
        evidence=evidence,
        failures=failures,
    )


def _openevolve_config_template(root: Path) -> dict[str, Any]:
    config_path = Path("examples/openevolve/config.yaml")
    verification = verify_default_config_template(config_path, root=root)
    summary = verification["summary"]
    failures = list(verification["failures"])
    evidence: dict[str, Any] = {
        "archive_loop_keys": list(OPENEVOLVE_CONFIG_ARCHIVE_LOOP_KEYS),
        "checked_config_synced": summary["checked_config_synced"],
        "config_path": config_path.as_posix(),
        "example_config_synced": summary["checked_config_synced"],
        "private_qwen_enabled": summary["private_qwen_enabled"],
        "python_candidates_executed": summary["python_candidates_executed"],
        "security_claim": summary["security_claim"],
        "template_keys": len(DEFAULT_CONFIG_TEMPLATE),
    }
    return _check(
        check_id="openevolve-config-template",
        status="failed" if failures else "passed",
        blocking=True,
        artifact=(
            "src/agades_pqc_gym/openevolve_adapter/config_templates.py + "
            "examples/openevolve/config.yaml"
        ),
        detail=(
            "The packaged OpenEvolve template and checked-in example config "
            "expose the same private JSON AttackPlan seed/archive/held-out loop "
            "without enabling arbitrary Python candidate execution."
        ),
        evidence=evidence,
        failures=failures,
    )


def _openevolve_evaluator_smoke(root: Path) -> dict[str, Any]:
    report_path = Path("reports/openevolve_smoke.json")
    verification = verify_openevolve_smoke_report(report_path, root=root)
    report = _read_optional_json(root / report_path)
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    safety = report.get("safety") if isinstance(report.get("safety"), dict) else {}
    failures = list(verification["failures"])
    evidence = {
        "attack_plan_path": report.get("attack_plan_path"),
        "checked_in_report_synced": verification["summary"]["checked_in_report_synced"],
        "combined_score": summary.get("combined_score"),
        "evaluation_status": summary.get("evaluation_status"),
        "feature_attack_type": summary.get("feature_attack_type"),
        "feature_family": summary.get("feature_family"),
        "feature_memory_bucket": summary.get("feature_memory_bucket"),
        "metric_count": summary.get("metric_count"),
        "primary_metric": report.get("primary_metric") or summary.get("primary_metric"),
        "python_candidates_executed": summary.get("python_candidates_executed"),
        "report_path": report_path.as_posix(),
        "security_claim": safety.get("security_claim"),
    }

    return _check(
        check_id="openevolve-evaluator-smoke",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="reports/openevolve_smoke.json",
        detail=(
            "The checked OpenEvolve evaluator smoke report proves that the "
            "wrapper can evaluate a public JSON AttackPlan and return the "
            "scalar fitness plus MAP-Elites feature metrics without executing "
            "arbitrary Python candidates."
        ),
        evidence=evidence,
        failures=failures,
    )


def _deepevolve_paper_card_injections(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "all_injections_review_required": False,
        "arbitrary_code_execution": True,
        "contains_private_traces": True,
        "injection_count": 0,
        "modifies_estimator_scores": True,
        "public_release_ok": True,
        "research_claim": True,
        "writes_attack_plans": True,
    }
    try:
        with tempfile.TemporaryDirectory() as tmp:
            private_root = Path(tmp)
            out = (
                private_root / "private" / "candidates" / ("paper_card_injections.json")
            )
            batch = write_paper_card_injection_batch(
                out,
                paper_card_dir=root / "examples" / "paper_cards",
                run_id="release-audit-paper-card-injection",
                policy=build_private_run_policy(),
                root=private_root,
            )
            reloaded = json.loads(out.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        batch = {}
        reloaded = {}
        failures.append(f"DeepEvolve paper-card injection smoke failed: {exc}.")

    if batch != reloaded:
        failures.append("DeepEvolve paper-card injection batch is not deterministic.")
    if batch.get("schema_version") != PAPER_CARD_INJECTION_BATCH_SCHEMA:
        failures.append("DeepEvolve paper-card injection schema is unexpected.")

    summary = batch.get("summary", {})
    safety = batch.get("safety", {})
    injections = batch.get("injections", [])
    if isinstance(summary, dict):
        evidence["all_injections_review_required"] = summary.get(
            "all_injections_review_required",
            False,
        )
        evidence["injection_count"] = summary.get("injection_count", 0)
    if isinstance(safety, dict):
        evidence["arbitrary_code_execution"] = safety.get(
            "arbitrary_code_execution",
            True,
        )
        evidence["contains_private_traces"] = safety.get(
            "contains_private_traces",
            True,
        )
        evidence["modifies_estimator_scores"] = safety.get(
            "modifies_estimator_scores",
            True,
        )
        evidence["research_claim"] = safety.get("research_claim", True)
        evidence["writes_attack_plans"] = safety.get("writes_attack_plans", True)
    if isinstance(injections, list):
        evidence["public_release_ok"] = any(
            isinstance(injection, dict)
            and injection.get("public_release_ok") is not False
            for injection in injections
        )

    if evidence["all_injections_review_required"] is not True:
        failures.append("DeepEvolve paper-card injections are not all review-gated.")
    if evidence["injection_count"] != 13:
        failures.append("DeepEvolve paper-card injection count drifted.")
    if evidence["arbitrary_code_execution"] is not False:
        failures.append("DeepEvolve paper-card injections allow arbitrary code.")
    if evidence["contains_private_traces"] is not False:
        failures.append("DeepEvolve paper-card injections contain private traces.")
    if evidence["modifies_estimator_scores"] is not False:
        failures.append("DeepEvolve paper-card injections modify estimator scores.")
    if evidence["public_release_ok"] is not False:
        failures.append("DeepEvolve paper-card injections are marked public.")
    if evidence["research_claim"] is not False:
        failures.append("DeepEvolve paper-card injections make research claims.")
    if evidence["writes_attack_plans"] is not False:
        failures.append("DeepEvolve paper-card injections write AttackPlans.")

    return _check(
        check_id="deepevolve-paper-card-injections",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="private/candidates/paper_card_injections.json",
        detail=(
            "DeepEvolve PaperCards can produce a private review-gated "
            "hypothesis injection queue without executing code, changing "
            "estimator scores, writing AttackPlans, or publishing candidates."
        ),
        evidence=evidence,
        failures=failures,
    )


def _deepevolve_research_hooks(root: Path) -> dict[str, Any]:
    manifest_path = root / "docs" / "deepevolve_research_hooks_manifest.json"
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "all_cards_note_only": False,
        "all_proposals_review_required": False,
        "arbitrary_code_execution": True,
        "card_count": 0,
        "modifies_estimator_scores": True,
        "private_qwen_bound": False,
        "proposal_count": 0,
        "research_claim": True,
        "review_required_before_implementation": False,
    }

    if not manifest_path.is_file():
        failures.append("DeepEvolve research hook manifest is missing.")
    else:
        try:
            committed = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            committed = None
            failures.append(f"DeepEvolve research hook manifest is invalid JSON: {exc}")

        if isinstance(committed, dict):
            expected = build_deepevolve_research_hooks_manifest()
            if committed != expected:
                failures.append("DeepEvolve research hook manifest is not in sync.")

            verification = verify_deepevolve_research_hooks_manifest(manifest_path)
            failures.extend(verification["failures"])
            evidence["private_qwen_bound"] = verification["summary"][
                "private_qwen_bound"
            ]
            summary = committed.get("summary", {})
            safety = committed.get("safety", {})
            if isinstance(summary, dict):
                evidence["all_cards_note_only"] = summary.get(
                    "all_cards_note_only",
                    False,
                )
                evidence["all_proposals_review_required"] = summary.get(
                    "all_proposals_review_required",
                    False,
                )
                evidence["card_count"] = summary.get("card_count", 0)
                evidence["proposal_count"] = summary.get("proposal_count", 0)
            if isinstance(safety, dict):
                evidence["arbitrary_code_execution"] = safety.get(
                    "arbitrary_code_execution",
                    True,
                )
                evidence["modifies_estimator_scores"] = safety.get(
                    "modifies_estimator_scores",
                    True,
                )
                evidence["research_claim"] = safety.get("research_claim", True)
                evidence["review_required_before_implementation"] = safety.get(
                    "review_required_before_implementation",
                    False,
                )

    if evidence["all_cards_note_only"] is not True:
        failures.append("DeepEvolve paper cards are not all note-only.")
    if evidence["all_proposals_review_required"] is not True:
        failures.append("DeepEvolve proposals are not all review-required.")
    if evidence["card_count"] != 8:
        failures.append("DeepEvolve paper card count drifted.")
    if evidence["proposal_count"] != 13:
        failures.append("DeepEvolve proposal count drifted.")
    if evidence["private_qwen_bound"] is not True:
        failures.append("DeepEvolve hooks are not bound to private Qwen.")
    if evidence["arbitrary_code_execution"] is not False:
        failures.append("DeepEvolve hooks allow arbitrary code execution.")
    if evidence["modifies_estimator_scores"] is not False:
        failures.append("DeepEvolve hooks modify estimator scores.")
    if evidence["research_claim"] is not False:
        failures.append("DeepEvolve hooks advertise a research claim.")
    if evidence["review_required_before_implementation"] is not True:
        failures.append("DeepEvolve hooks are not review-gated.")

    return _check(
        check_id="deepevolve-research-hooks",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="docs/deepevolve_research_hooks_manifest.json",
        detail=(
            "DeepEvolve-style PaperCards are checked in as note-only, "
            "review-required hypothesis hooks that do not execute code, alter "
            "estimator scores, publish private candidates, or make research claims."
        ),
        evidence=evidence,
        failures=failures,
    )


def _mutation_batch_parameters(batch: Any) -> list[str]:
    derived_target_fields = {"claimed_security_bits", "name"}
    parameters: set[str] = set()
    for candidate in batch.candidates:
        summary = candidate.mutation_summary
        for segment in summary.split(";"):
            segment = segment.strip()
            if ".params." in segment:
                tail = segment.split(".params.", 1)[1]
                param_name = tail.split(":", 1)[0]
                if param_name:
                    parameters.add(param_name)
            elif segment.startswith("target."):
                tail = segment.split("target.", 1)[1]
                field_name = tail.split(":", 1)[0]
                if field_name and field_name not in derived_target_fields:
                    parameters.add(field_name)
    return sorted(parameters)


def _community_release_cards(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    family_support = _read_json(root / "docs" / "family_support_matrix.json")
    dataset_info = _read_json(root / "hf" / "dataset" / "dataset_info.json")
    toy_families = sorted(
        family["family"]
        for family in family_support.get("families", [])
        if family.get("support_level") == "toy_evaluator"
    )
    public_run_bundles = dataset_info.get("public_run_bundles", [])
    if not isinstance(public_run_bundles, list):
        public_run_bundles = []
        failures.append("Hugging Face dataset public_run_bundles must be a list.")

    card_texts: dict[str, str] = {}
    for card_id, relative_path in COMMUNITY_CARD_PATHS.items():
        path = root / relative_path
        if not path.is_file():
            failures.append(f"Community release card is missing: {relative_path}.")
            card_texts[card_id] = ""
            continue
        card_texts[card_id] = path.read_text(encoding="utf-8")

    for family in toy_families:
        phrases = TOY_FAMILY_CARD_PHRASES.get(family)
        if phrases is None:
            failures.append(f"Toy family lacks card expectations: {family}.")
            continue
        for phrase in phrases:
            for card_id in (
                "dataset_card",
                "dataset_readme",
                "prime_environment_card",
                "mvp_report",
            ):
                if phrase not in card_texts.get(card_id, ""):
                    failures.append(
                        f"{COMMUNITY_CARD_PATHS[card_id]} does not mention "
                        f"{phrase!r} for {family}."
                    )

    for bundle_id in public_run_bundles:
        if not isinstance(bundle_id, str):
            failures.append("Public run bundle ids must be strings.")
            continue
        for card_id in (
            "benchmark_card",
            "dataset_card",
            "dataset_readme",
            "mvp_report",
        ):
            if bundle_id not in card_texts.get(card_id, ""):
                failures.append(
                    f"{COMMUNITY_CARD_PATHS[card_id]} does not mention public "
                    f"run bundle {bundle_id}."
                )

    combined = "\n".join(card_texts.values())
    for stale_claim in STALE_COMMUNITY_CARD_CLAIMS:
        if stale_claim in combined:
            failures.append(
                f"Community release cards contain stale claim: {stale_claim}"
            )

    return _check(
        check_id="community-release-cards",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="hf + prime_intellect + reports release cards",
        detail=(
            "Human-facing community cards and MVP report describe the current "
            "toy family surfaces and public run bundles without stale "
            "schema-only claims."
        ),
        evidence={
            "cards": sorted(COMMUNITY_CARD_PATHS.values()),
            "public_run_bundles": len(public_run_bundles),
            "toy_families": toy_families,
        },
        failures=failures,
    )


def _ecosystem_release_plans(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    dataset_info = _read_json(root / "hf" / "dataset" / "dataset_info.json")
    public_run_bundles = dataset_info.get("public_run_bundles", [])
    if not isinstance(public_run_bundles, list):
        public_run_bundles = []
        failures.append("Hugging Face dataset public_run_bundles must be a list.")

    plan_texts: dict[str, str] = {}
    for relative_path in ECOSYSTEM_RELEASE_PLAN_PATHS:
        path = root / relative_path
        if not path.is_file():
            failures.append(f"Ecosystem release plan is missing: {relative_path}.")
            plan_texts[relative_path] = ""
            continue
        plan_texts[relative_path] = path.read_text(encoding="utf-8")

    for bundle_id in public_run_bundles:
        if not isinstance(bundle_id, str):
            failures.append("Public run bundle ids must be strings.")
            continue
        for relative_path, text in plan_texts.items():
            if bundle_id not in text:
                failures.append(
                    f"{relative_path} does not mention public run bundle {bundle_id}."
                )

    combined = "\n".join(plan_texts.values())
    schema_artifact_plan_coverage: dict[str, list[str]] = {
        relative_path: [] for relative_path in ECOSYSTEM_RELEASE_PLAN_PATHS
    }
    for artifact_path in ECOSYSTEM_RELEASE_PLAN_SCHEMA_ARTIFACTS:
        for relative_path, text in plan_texts.items():
            if artifact_path not in text:
                failures.append(
                    f"{relative_path} does not mention schema artifact {artifact_path}."
                )
            else:
                schema_artifact_plan_coverage[relative_path].append(artifact_path)

    prime_ecosystem_anchor_plan_coverage: dict[str, list[str]] = {
        relative_path: [] for relative_path in ECOSYSTEM_RELEASE_PLAN_PATHS
    }
    for anchor_id, marker in ECOSYSTEM_RELEASE_PLAN_PRIME_ANCHORS.items():
        for relative_path, text in plan_texts.items():
            if marker not in text:
                failures.append(
                    f"{relative_path} does not mention Prime ecosystem anchor "
                    f"{anchor_id}."
                )
            else:
                prime_ecosystem_anchor_plan_coverage[relative_path].append(anchor_id)

    for boundary in ECOSYSTEM_RELEASE_PLAN_BOUNDARIES:
        if boundary not in combined:
            failures.append(
                f"Ecosystem release plans omit safety boundary: {boundary}."
            )

    stale_prime_phrases = (
        "downscaled MLWE public run bundles",
        "only the committed LWE and downscaled MLWE",
    )
    prime_text = plan_texts.get("docs/PRIME_INTELLECT_RELEASE_PLAN.md", "")
    for stale_phrase in stale_prime_phrases:
        if stale_phrase in prime_text:
            failures.append(f"Prime release plan contains stale phrase: {stale_phrase}")

    return _check(
        check_id="ecosystem-release-plans",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="docs/*_RELEASE_PLAN.md + docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md",
        detail=(
            "Hugging Face, Prime, and NVIDIA planning docs are synchronized "
            "with current public run bundles, Prime/HF schema artifacts, and "
            "safety/review boundaries."
        ),
        evidence={
            "plans": sorted(ECOSYSTEM_RELEASE_PLAN_PATHS),
            "prime_ecosystem_anchor_plan_coverage": {
                relative_path: sorted(anchors)
                for relative_path, anchors in sorted(
                    prime_ecosystem_anchor_plan_coverage.items()
                )
            },
            "prime_ecosystem_anchors": sorted(ECOSYSTEM_RELEASE_PLAN_PRIME_ANCHORS),
            "public_run_bundles": len(public_run_bundles),
            "schema_artifacts": sorted(ECOSYSTEM_RELEASE_PLAN_SCHEMA_ARTIFACTS),
            "schema_artifact_plan_coverage": {
                relative_path: sorted(artifacts)
                for relative_path, artifacts in sorted(
                    schema_artifact_plan_coverage.items()
                )
            },
        },
        failures=failures,
    )


def _prime_environment_smoke(root: Path) -> dict[str, Any]:
    verification = verify_prime_environment_smoke_report(
        Path("reports/prime_environment_smoke.json"),
        root=root,
    )
    summary = verification["summary"]
    failures = list(verification["failures"])

    return _check(
        check_id="prime-environment-smoke",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="reports/prime_environment_smoke.json",
        detail=(
            "Prime verifier environment smoke report proves the package "
            "imports without Verifiers, builds packaged task rows, scores "
            "accepted JSON, rejects unsupported/prefixed submissions, and "
            "reports optional dependency boundaries cleanly."
        ),
        evidence={
            "accepted_score": summary["accepted_score"],
            "dataset_rows": summary["dataset_rows"],
            "imports_without_verifiers": summary["imports_without_verifiers"],
            "optional_dependency_boundary": summary["load_environment_boundary_ok"],
            "prefixed_json_score": summary["prefixed_json_score"],
            "unsupported_score": summary["unsupported_score"],
        },
        failures=failures,
    )


def _prime_environment_manifest(root: Path) -> dict[str, Any]:
    path = root / "prime_intellect" / "verifiers_environment" / "prime_manifest.json"
    verification = verify_prime_environment_manifest(path, root=root)
    failures = list(verification["failures"])
    if path.is_file():
        try:
            manifest = _read_json(path)
        except json.JSONDecodeError:
            manifest = {}
    else:
        manifest = {}
    task_manifest = manifest.get("task_manifest", {})
    if not isinstance(task_manifest, dict):
        task_manifest = {}
    prime = manifest.get("prime", {})
    if not isinstance(prime, dict):
        prime = {}
    source_mirror = manifest.get("source_mirror", {})
    if not isinstance(source_mirror, dict):
        source_mirror = {}

    return _check(
        check_id="prime-environment-manifest",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="prime_intellect/verifiers_environment/prime_manifest.json",
        detail=(
            "Prime environment manifest is checked in, synchronized with "
            "packaged tasks, and documents the JSON-only scoring contract."
        ),
        evidence={
            "families": task_manifest.get("families", []),
            "hub_install_command_template": prime.get("hub_install_command_template"),
            "eval_config_path": prime.get("eval_config_path"),
            "local_eval_command": prime.get("local_eval_command"),
            "mirrored_public_examples": source_mirror.get("valid_public_example_count"),
            "mirrors_public_examples": source_mirror.get(
                "mirrors_valid_public_examples"
            ),
            "task_count": task_manifest.get("task_count"),
        },
        failures=failures,
    )


def _prime_eval_config(root: Path) -> dict[str, Any]:
    verification = verify_prime_eval_config(
        Path("prime_intellect/evals/agades_pqc_eval.template.toml"),
        Path("docs/prime_eval_config_manifest.json"),
        root=root,
    )
    summary = verification["summary"]

    return _check(
        check_id="prime-eval-config",
        status="failed" if verification["failures"] else "passed",
        blocking=True,
        artifact="docs/prime_eval_config_manifest.json",
        detail=(
            "Prime eval config template is checked in, synchronized with the "
            "Verifiers environment, and blocks credentialed eval runs until "
            "Prime namespace, billing, and model review."
        ),
        evidence={
            "family_count": summary["family_count"],
            "num_examples": summary["num_examples"],
            "rollouts_per_example": summary["rollouts_per_example"],
            "task_count": summary["task_count"],
        },
        failures=list(verification["failures"]),
    )


def _pedagogical_rl_method(root: Path) -> dict[str, Any]:
    verification = verify_pedagogical_rl_method(
        Path("docs/pedagogical_rl_method.json"),
        root=root,
    )
    summary = verification["summary"]
    artifact = _read_json(root / "docs" / "pedagogical_rl_method.json")
    reward_contract = artifact.get("reward_contract", {})
    if not isinstance(reward_contract, dict):
        reward_contract = {}
    roles = artifact.get("roles", {})
    if not isinstance(roles, dict):
        roles = {}
    teacher = roles.get("self_teacher", {})
    if not isinstance(teacher, dict):
        teacher = {}
    privacy = artifact.get("privacy", {})
    if not isinstance(privacy, dict):
        privacy = {}

    privacy_preserving = all(
        privacy.get(key) is False
        for key in (
            "raw_rollouts_publication_allowed",
            "teacher_prompts_publication_allowed",
            "student_logprobs_publication_allowed",
            "reviewer_annotations_publication_allowed",
            "fine_tuned_weights_publication_allowed",
        )
    )

    return _check(
        check_id="pedagogical-rl-method",
        status="failed" if verification["failures"] else "passed",
        blocking=True,
        artifact="docs/pedagogical_rl_method.json",
        detail=(
            "Pedagogical RL is captured as a verifiable private method "
            "contract with teacher/student roles, spike-aware reward, "
            "surprisal-gated assimilation, and publication boundaries."
        ),
        evidence={
            "stages": summary["stages"],
            "reward_terms": summary["reward_terms"],
            "linked_artifacts": summary["linked_artifacts"],
            "teacher_student_pattern": (
                "privileged_self_teacher_student"
                if teacher.get("privileged_context_visible") is True
                else None
            ),
            "pedagogy_reward": reward_contract.get("pedagogy_reward"),
            "privacy_preserving": privacy_preserving,
        },
        failures=list(verification["failures"]),
    )


def _private_dataset_curation(root: Path) -> dict[str, Any]:
    path = root / "docs" / "private_dataset_curation.json"
    verification = verify_private_dataset_curation(path, root=root)
    summary = verification["summary"]
    artifact = _read_optional_json(path)
    outputs = artifact.get("outputs", {})
    if not isinstance(outputs, dict):
        outputs = {}
    sources = artifact.get("sources", {})
    if not isinstance(sources, dict):
        sources = {}

    license_review_required = all(
        isinstance(source, dict)
        and source.get("license_review_status") == "required_unverified"
        and source.get("ingestion_allowed_before_license_review") is False
        for source in sources.values()
    )

    return _check(
        check_id="private-dataset-curation",
        status="failed" if verification["failures"] else "passed",
        blocking=True,
        artifact="docs/private_dataset_curation.json",
        detail=(
            "Private RL dataset curation is represented by a public manifest "
            "only: sources require license review, provenance, deduplication, "
            "redaction, contamination audit, and no private rows or prompts "
            "may be published."
        ),
        evidence={
            "sources": summary["sources"],
            "pipeline_stages": summary["pipeline_stages"],
            "required_controls": summary["required_controls"],
            "linked_artifacts": summary["linked_artifacts"],
            "public_rows_allowed": outputs.get("public_rows_allowed"),
            "license_review_required": license_review_required,
        },
        failures=list(verification["failures"]),
    )


def _prime_verifier_schemas(root: Path) -> dict[str, Any]:
    verification = verify_prime_verifier_schemas(
        Path("prime_intellect/schemas"),
        root=root,
    )
    summary = verification["summary"]

    return _check(
        check_id="prime-verifier-schemas",
        status="failed" if verification["failures"] else "passed",
        blocking=True,
        artifact="prime_intellect/schemas",
        detail=(
            "Prime/HF public verifier submission and result JSON Schemas are "
            "checked in, synchronized, and preserve the JSON-only/no-claim "
            "contract."
        ),
        evidence={
            "result_required_fields": summary["result_required_fields"],
            "schema_files": summary["schema_files"],
            "submission_required_fields": summary["submission_required_fields"],
        },
        failures=list(verification["failures"]),
    )


def _prime_publication_handoff(root: Path) -> dict[str, Any]:
    path = root / "docs" / "prime_publication_handoff.json"
    verification = verify_prime_publication_handoff(path, root=root)
    summary = verification["summary"]

    return _check(
        check_id="prime-publication-handoff",
        status="failed" if verification["failures"] else "passed",
        blocking=True,
        artifact="docs/prime_publication_handoff.json",
        detail=(
            "Prime publication handoff is checked in, synchronized with the "
            "local environment package, and keeps external Prime Hub "
            "publication behind credentials and release review."
        ),
        evidence={
            "artifact_count": summary["artifact_count"],
            "external_publication_requires_review": summary[
                "external_publication_requires_review"
            ],
            "family_count": summary["family_count"],
            "local_package_ready": summary["local_package_ready"],
            "prime_hub_publication_performed": summary[
                "prime_hub_publication_performed"
            ],
            "requires_credentials": summary["requires_credentials"],
            "task_count": summary["task_count"],
        },
        failures=list(verification["failures"]),
    )


def _prime_speedrun_handoff(root: Path) -> dict[str, Any]:
    path = root / "docs" / "prime_speedrun_handoff.json"
    verification = verify_prime_speedrun_handoff(path, root=root)
    summary = verification["summary"]

    return _check(
        check_id="prime-speedrun-handoff",
        status="failed" if verification["failures"] else "passed",
        blocking=True,
        artifact="docs/prime_speedrun_handoff.json",
        detail=(
            "Prime speedrun handoff ties the JSON-only Verifiers environment "
            "to the flat public run export and Prime speedrunning source "
            "anchors while keeping external execution behind review."
        ),
        evidence={
            "artifact_count": summary["artifact_count"],
            "bundle_count": summary["bundle_count"],
            "external_execution_requires_review": summary[
                "external_execution_requires_review"
            ],
            "family_count": summary["family_count"],
            "run_count": summary["run_count"],
            "task_count": summary["task_count"],
        },
        failures=list(verification["failures"]),
    )


def _external_publication_review_packet(root: Path) -> dict[str, Any]:
    path = root / "docs" / "external_publication_review_packet.json"
    verification = verify_external_publication_review_packet(path, root=root)
    summary = verification["summary"]

    return _check(
        check_id="external-publication-review-packet",
        status="failed" if verification["failures"] else "passed",
        blocking=True,
        artifact="docs/external_publication_review_packet.json",
        detail=(
            "External publication review packet synchronizes Hugging Face, "
            "Prime Intellect, and NVIDIA-facing surfaces while keeping "
            "external publication blocked behind review and credentials."
        ),
        evidence={
            "blockers": summary["blockers"],
            "credential_material_included": summary["credential_material_included"],
            "credential_review_queue_complete": summary[
                "credential_review_queue_complete"
            ],
            "credential_review_queue_items": summary["credential_review_queue_items"],
            "credentialed_surface_count": summary["credentialed_surface_count"],
            "families_with_future_reviewed_adapters": summary[
                "families_with_future_reviewed_adapters"
            ],
            "family_count": summary["family_count"],
            "family_readiness_family_count": summary["family_readiness_family_count"],
            "family_readiness_lattice_estimator_families": summary[
                "family_readiness_lattice_estimator_families"
            ],
            "family_readiness_non_lattice_lattice_estimator_families": summary[
                "family_readiness_non_lattice_lattice_estimator_families"
            ],
            "family_readiness_review_required_families": summary[
                "family_readiness_review_required_families"
            ],
            "family_readiness_schema_only_default_estimators": summary[
                "family_readiness_schema_only_default_estimators"
            ],
            "reviewer_summary_synced": summary["reviewer_summary_synced"],
            "future_reviewed_adapter_sources_by_family": summary[
                "future_reviewed_adapter_sources_by_family"
            ],
            "platform_review_matrix_credentialed_surfaces": summary[
                "platform_review_matrix_credentialed_surfaces"
            ],
            "platform_review_matrix_review_required_surfaces": summary[
                "platform_review_matrix_review_required_surfaces"
            ],
            "platform_review_matrix_surfaces": summary[
                "platform_review_matrix_surfaces"
            ],
            "platform_family_support_family_counts_match": summary[
                "platform_family_support_family_counts_match"
            ],
            "platform_family_support_surfaces": summary[
                "platform_family_support_surfaces"
            ],
            "platforms_with_family_claim_review_gate": summary[
                "platforms_with_family_claim_review_gate"
            ],
            "publication_dry_run_commands": summary["publication_dry_run_commands"],
            "publication_dry_run_contains_credentials": summary[
                "publication_dry_run_contains_credentials"
            ],
            "publication_dry_run_entries": summary["publication_dry_run_entries"],
            "publication_dry_run_external_publication_performed": summary[
                "publication_dry_run_external_publication_performed"
            ],
            "publication_dry_run_manual_entries": summary[
                "publication_dry_run_manual_entries"
            ],
            "publication_dry_run_private_first": summary[
                "publication_dry_run_private_first"
            ],
            "ready_for_external_publication": summary["ready_for_external_publication"],
            "review_required_before_claims": summary["review_required_before_claims"],
            "review_required_surface_count": summary["review_required_surface_count"],
            "surface_count": summary["surface_count"],
            "warnings": summary["warnings"],
            "warning_evidence_items": summary["warning_evidence_items"],
        },
        failures=list(verification["failures"]),
    )


def _ecosystem_smoke_report(root: Path) -> dict[str, Any]:
    report = build_ecosystem_smoke_report(root=root)
    verification = verify_ecosystem_smoke_report(
        Path("reports/ecosystem_smoke.json"),
        root=root,
    )
    summary = report["summary"]
    verification_summary = verification["summary"]
    failures = list(report["failures"])
    failures.extend(str(failure) for failure in verification["failures"])
    if report["accepted"] is not True:
        failures.append("Ecosystem smoke report must accept local OSS surfaces.")

    return _check(
        check_id="ecosystem-smoke-report",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="reports/ecosystem_smoke.json",
        detail=(
            "The local ecosystem smoke report aggregates Hugging Face, Prime "
            "Intellect, NVIDIA, and publication verifiers without external "
            "credentials or publication side effects."
        ),
        evidence={
            "checked_in_report_synced": verification_summary[
                "checked_in_report_synced"
            ],
            "external_publication_ready": summary["external_publication_ready"],
            "families_with_future_reviewed_adapters": summary[
                "families_with_future_reviewed_adapters"
            ],
            "family_count": summary["family_count"],
            "future_reviewed_adapter_sources_by_family": summary[
                "future_reviewed_adapter_sources_by_family"
            ],
            "hf_valid_attack_plan_rows": summary["hf_valid_attack_plan_rows"],
            "local_artifacts_ready": summary["local_artifacts_ready"],
            "nvidia_current_gpu_required_workloads": summary[
                "nvidia_current_gpu_required_workloads"
            ],
            "platform_family_support_family_counts_match": summary[
                "platform_family_support_family_counts_match"
            ],
            "platform_family_support_surfaces": summary[
                "platform_family_support_surfaces"
            ],
            "platform_public_private_boundary_surfaces": summary[
                "platform_public_private_boundary_surfaces"
            ],
            "platform_report_redaction_records_match": summary[
                "platform_report_redaction_records_match"
            ],
            "platforms_with_family_claim_review_gate": summary[
                "platforms_with_family_claim_review_gate"
            ],
            "platforms_with_raw_mapping_redaction_gate": summary[
                "platforms_with_raw_mapping_redaction_gate"
            ],
            "platforms_with_typed_trace_redaction_gate": summary[
                "platforms_with_typed_trace_redaction_gate"
            ],
            "prime_tasks": summary["prime_tasks"],
            "public_run_bundles": summary["public_run_bundles"],
            "reviewer_summary_synced": verification_summary[
                "reviewer_summary_synced"
            ],
            "runbook_core_symbol_import_count": summary[
                "runbook_core_symbol_import_count"
            ],
            "runbook_family_plugin_manifest_digests_match": summary[
                "runbook_family_plugin_manifest_digests_match"
            ],
            "runbook_family_plugin_module_count": summary[
                "runbook_family_plugin_module_count"
            ],
            "runbook_family_plugin_module_digest_count": summary[
                "runbook_family_plugin_module_digest_count"
            ],
            "runbook_family_plugin_module_import_count": summary[
                "runbook_family_plugin_module_import_count"
            ],
            "runbook_family_registry_family_count_matches_plugin_manifest": summary[
                "runbook_family_registry_family_count_matches_plugin_manifest"
            ],
            "runbook_family_registry_plugin_count_matches_plugin_manifest": summary[
                "runbook_family_registry_plugin_count_matches_plugin_manifest"
            ],
            "runbook_family_registry_plugin_manifest_module_digest_count": summary[
                "runbook_family_registry_plugin_manifest_module_digest_count"
            ],
            "runbook_family_registry_plugin_manifest_synced": summary[
                "runbook_family_registry_plugin_manifest_synced"
            ],
            "runbook_family_registry_runtime_adapter_entries_match_plugin_manifest": (
                summary[
                    "runbook_family_registry_runtime_adapter_entries_match_plugin_manifest"
                ]
            ),
        },
        failures=failures,
    )


def _release_gate_closure(root: Path) -> dict[str, Any]:
    checked_release_gate_artifacts = 0
    release_audit_gate_artifacts = 0
    ecosystem_smoke_gate_artifacts = 0
    missing_ecosystem_smoke_gate: list[str] = []
    late_ecosystem_smoke_gate: list[str] = []

    for path in _release_gate_artifact_paths(root):
        data = _read_json(path)
        release_gates = data.get("release_gates")
        if not isinstance(release_gates, list):
            continue

        checked_release_gate_artifacts += 1
        audit_indices = _release_gate_indices(release_gates, "release-audit")
        smoke_indices = _release_gate_indices(
            release_gates,
            "ecosystem-smoke-verify",
        )
        if smoke_indices:
            ecosystem_smoke_gate_artifacts += 1
        if not audit_indices:
            continue

        release_audit_gate_artifacts += 1
        relative_path = path.relative_to(root).as_posix()
        if not smoke_indices:
            missing_ecosystem_smoke_gate.append(relative_path)
        elif min(smoke_indices) > min(audit_indices):
            late_ecosystem_smoke_gate.append(relative_path)

    failures: list[str] = []
    if missing_ecosystem_smoke_gate:
        failures.append(
            "Release audit gates missing ecosystem smoke gate: "
            f"{', '.join(missing_ecosystem_smoke_gate)}."
        )
    if late_ecosystem_smoke_gate:
        failures.append(
            "Release audit gates must place ecosystem smoke before release "
            f"audit: {', '.join(late_ecosystem_smoke_gate)}."
        )

    return _check(
        check_id="release-gate-closure",
        status="failed" if failures else "passed",
        blocking=True,
        artifact="checked-in JSON release_gates",
        detail=(
            "Checked-in release gates that depend on release-audit must first "
            "declare ecosystem-smoke-verify, including nested Hugging Face "
            "dataset metadata."
        ),
        evidence={
            "checked_release_gate_artifacts": checked_release_gate_artifacts,
            "release_audit_gate_artifacts": release_audit_gate_artifacts,
            "ecosystem_smoke_gate_artifacts": ecosystem_smoke_gate_artifacts,
            "missing_ecosystem_smoke_gate": missing_ecosystem_smoke_gate,
            "late_ecosystem_smoke_gate": late_ecosystem_smoke_gate,
        },
        failures=failures,
    )


def _release_gate_artifact_paths(root: Path) -> list[Path]:
    return sorted(
        [
            *root.joinpath("docs").glob("*.json"),
            *root.joinpath("hf").rglob("*.json"),
            *root.joinpath("nvidia").glob("*.json"),
            *root.joinpath("prime_intellect").glob("**/*.json"),
            *root.joinpath("public").glob("*.json"),
            *root.joinpath("reports").glob("*.json"),
        ],
        key=lambda path: path.relative_to(root).as_posix(),
    )


def _release_gate_indices(release_gates: list[Any], gate_id: str) -> list[int]:
    return [
        index
        for index, gate in enumerate(release_gates)
        if isinstance(gate, str) and gate_id in gate
    ]


def _prime_environment_json_only(root: Path) -> dict[str, Any]:
    pyproject = root / "prime_intellect" / "verifiers_environment" / "pyproject.toml"
    readme = root / "prime_intellect" / "verifiers_environment" / "README.md"
    module = (
        root
        / "prime_intellect"
        / "verifiers_environment"
        / "agades_pqc_verifier_env.py"
    )
    failed_reasons: list[str] = []
    module_text = module.read_text(encoding="utf-8")
    readme_text = readme.read_text(encoding="utf-8")
    if "agades-pqc-verifier-env" not in pyproject.read_text(encoding="utf-8"):
        failed_reasons.append("Prime environment pyproject name is missing.")
    if "Do not submit Python" not in module_text:
        failed_reasons.append("Prime environment prompt lacks Python submission ban.")
    if "does not execute model-submitted Python" not in readme_text:
        failed_reasons.append("Prime environment README lacks execution boundary.")
    packaged_tasks = sorted(
        (root / "prime_intellect" / "verifiers_environment" / "data").glob("*.json")
    )
    if not packaged_tasks:
        failed_reasons.append("Prime environment packages no task JSON files.")
    return _check(
        check_id="prime-environment-json-only",
        status="failed" if failed_reasons else "passed",
        blocking=True,
        artifact="prime_intellect/verifiers_environment",
        detail="Prime environment remains JSON-only and packages public tasks.",
        evidence={"packaged_tasks": len(packaged_tasks)},
        failures=failed_reasons,
    )


def _public_run_ledger_safety(root: Path) -> dict[str, Any]:
    public_run_root = root / "examples" / "public_runs"
    ledger_paths = (
        sorted(public_run_root.glob("*/run_ledger.json"))
        if public_run_root.is_dir()
        else []
    )
    failed_reasons: list[str] = []
    total_records = 0
    redacted_records = 0
    families: set[str] = set()

    if not ledger_paths:
        failed_reasons.append("No committed public run ledgers were found.")

    for ledger_path in ledger_paths:
        relative_ledger = ledger_path.relative_to(root).as_posix()
        ledger = _read_json(ledger_path)
        safety = ledger.get("safety", {})
        if safety.get("arbitrary_code_execution") is not False:
            failed_reasons.append(f"{relative_ledger} advertises arbitrary execution.")
        if safety.get("security_claim") is not False:
            failed_reasons.append(f"{relative_ledger} advertises a security claim.")
        summary = ledger.get("summary", {})
        ledger_redacted_records = summary.get("redacted_records")
        if ledger_redacted_records != 0:
            failed_reasons.append(f"{relative_ledger} contains redacted records.")
        if any("attack_plan" in entry for entry in ledger.get("entries", [])):
            failed_reasons.append(
                f"{relative_ledger} entries include full AttackPlans."
            )
        if isinstance(summary.get("total_records"), int):
            total_records += summary["total_records"]
        if isinstance(ledger_redacted_records, int):
            redacted_records += ledger_redacted_records
        if isinstance(summary.get("by_family"), dict):
            families.update(str(family) for family in summary["by_family"])

    return _check(
        check_id="public-run-ledger-safety",
        status="failed" if failed_reasons else "passed",
        blocking=True,
        artifact="examples/public_runs/*/run_ledger.json",
        detail="Committed public run ledgers are compact and non-claiming.",
        evidence={
            "bundles": len(ledger_paths),
            "families": sorted(families),
            "total_records": total_records,
            "redacted_records": redacted_records,
        },
        failures=failed_reasons,
    )


def _report_generator_redaction(root: Path) -> dict[str, Any]:
    return build_report_generator_redaction_check(root)


def _private_run_policy(root: Path) -> dict[str, Any]:
    path = root / "docs" / "private_run_policy.json"
    verification = verify_private_run_policy(path, root=root)
    failures = list(verification["failures"])
    evidence = {
        key: value
        for key, value in verification["summary"].items()
        if key != "failure_count"
    }

    return _check(
        check_id="private-run-policy",
        status="failed" if not verification["accepted"] else "passed",
        blocking=True,
        artifact="docs/private_run_policy.json",
        detail=(
            "Private evolution traces and candidate strategies are confined to "
            "private roots and require redaction/preflight before public export."
        ),
        evidence=evidence,
        failures=failures,
    )


def _legacy_name_guard(root: Path) -> dict[str, Any]:
    matches: list[str] = []
    for relative in LEGACY_NAME_PATHS:
        path = root / relative
        candidates = [path] if path.is_file() else sorted(path.rglob("*"))
        for candidate in candidates:
            if not candidate.is_file():
                continue
            if _is_binary(candidate):
                continue
            text = candidate.read_text(encoding="utf-8", errors="ignore")
            for pattern in LEGACY_NAME_PATTERNS:
                if pattern in text:
                    matches.append(f"{candidate.relative_to(root)}:{pattern}")
    return _check(
        check_id="legacy-name-guard",
        status="failed" if matches else "passed",
        blocking=True,
        artifact="repository text paths",
        detail="Repository public surface uses Agades PQC naming.",
        evidence={"matches": matches},
        failures=["Legacy cryptanalysis/crypto naming found."] if matches else [],
    )


def _prime_hub_publication(root: Path) -> dict[str, Any]:
    publication_verification = verify_prime_publication_handoff(
        root / "docs" / "prime_publication_handoff.json",
        root=root,
    )
    publication_summary = publication_verification["summary"]
    speedrun_verification = verify_prime_speedrun_handoff(
        root / "docs" / "prime_speedrun_handoff.json",
        root=root,
    )
    speedrun_summary = speedrun_verification["summary"]

    return _check(
        check_id="prime-hub-publication",
        status="warning",
        blocking=False,
        artifact="prime_intellect/verifiers_environment",
        detail=(
            "Prime package is locally packaged but not published to the Prime "
            "Environments Hub without credentials and release review."
        ),
        evidence={
            "external_execution_requires_review": speedrun_summary[
                "external_execution_requires_review"
            ],
            "external_publication_requires_review": publication_summary[
                "external_publication_requires_review"
            ],
            "local_package_ready": publication_summary["local_package_ready"],
            "prime_hub_publication_performed": publication_summary[
                "prime_hub_publication_performed"
            ],
            "publication_artifact_count": publication_summary["artifact_count"],
            "publication_family_count": publication_summary["family_count"],
            "publication_task_count": publication_summary["task_count"],
            "requires_credentials": publication_summary["requires_credentials"],
            "speedrun_artifact_count": speedrun_summary["artifact_count"],
            "speedrun_bundle_count": speedrun_summary["bundle_count"],
            "speedrun_family_count": speedrun_summary["family_count"],
            "speedrun_run_count": speedrun_summary["run_count"],
            "speedrun_task_count": speedrun_summary["task_count"],
        },
        failures=[],
    )


def _audit_trace_record(
    *,
    plan: AttackPlan,
    run_id: str,
    candidate_id: str,
    parent_id: str | None,
    score: float,
    accepted: bool,
) -> TraceRecord:
    return TraceRecord.from_evaluation(
        run_id=run_id,
        candidate_id=candidate_id,
        parent_id=parent_id,
        generation=0,
        mutation_summary="release audit smoke",
        attack_plan=plan,
        evaluation={
            "combined_score": score,
            "evaluation_status": "ok" if accepted else "invalid",
            "feature_family": plan.target.family.value,
            "feature_attack_type": "primal_usvp",
            "feature_memory_bucket": "low",
            "feature_assumption_bucket": "some",
            "feature_estimator_model": "mock-lattice-estimator",
            "valid": accepted,
        },
        accepted=accepted,
        public_release_ok=accepted,
        redaction_reason=None if accepted else "invalid",
    )


def _summary(checks: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "passed": sum(1 for check in checks if check["status"] == "passed"),
        "failed": sum(1 for check in checks if check["status"] == "failed"),
        "warning": sum(1 for check in checks if check["status"] == "warning"),
        "total": len(checks),
    }


def _check(
    *,
    check_id: str,
    status: str,
    blocking: bool,
    artifact: str,
    detail: str,
    evidence: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "blocking": blocking,
        "artifact": artifact,
        "detail": detail,
        "evidence": evidence,
        "failures": failures,
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_json(path: Path) -> dict[str, Any]:
    try:
        payload = _read_json(path)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _load_python_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse_sha256_manifest_line(line: str) -> tuple[str, str] | None:
    if "  " not in line:
        return None
    digest, relative_path = line.split("  ", 1)
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        return None
    if not relative_path or relative_path.startswith("/") or "\\" in relative_path:
        return None
    parts = Path(relative_path).parts
    if any(part in {"", ".", ".."} for part in parts):
        return None
    return digest, relative_path


def _workflow_has_trigger(triggers: Any, trigger: str) -> bool:
    if isinstance(triggers, str):
        return triggers == trigger
    if isinstance(triggers, list):
        return trigger in triggers
    if isinstance(triggers, dict):
        return trigger in triggers
    return False


def _workflow_steps(jobs: dict[str, Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        job_steps = job.get("steps", [])
        if not isinstance(job_steps, list):
            continue
        steps.extend(step for step in job_steps if isinstance(step, dict))
    return steps


def _normalized_run_commands(run: str) -> list[str]:
    return [
        " ".join(line.strip().split())
        for line in run.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _valid_public_example_families(root: Path) -> tuple[set[str], list[str]]:
    families: set[str] = set()
    failures: list[str] = []
    for path in sorted((root / "examples" / "attack_plans").glob("*.json")):
        if path.name.startswith("invalid_"):
            continue
        data = _read_json(path)
        family = data.get("target", {}).get("family")
        if not isinstance(family, str):
            failures.append(f"{path.relative_to(root)} lacks target.family")
            continue
        if data.get("metadata", {}).get("public") is not True:
            failures.append(f"{path.relative_to(root)} is not marked public")
            continue
        families.add(family)
    return families, failures


def _benchmark_target_families(root: Path) -> tuple[set[str], list[str]]:
    families: set[str] = set()
    failures: list[str] = []
    for path in sorted((root / "benchmarks").glob("*/*.json")):
        data = _read_json(path)
        target = data.get("target", data)
        family = target.get("family") if isinstance(target, dict) else None
        if not isinstance(family, str):
            failures.append(f"{path.relative_to(root)} lacks target family")
            continue
        families.add(family)
    return families, failures


def _benchmark_dir_ready(path: Path) -> bool:
    return path.is_dir() and (path / "README.md").is_file() and any(path.glob("*.json"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _hf_task_metadata_for_attack_plan(
    root: Path,
    attack_plan_id: str,
) -> dict[str, Any] | None:
    task_metadata_path = root / "hf" / "dataset" / "task_metadata.jsonl"
    if not task_metadata_path.is_file():
        return None
    for row in _read_jsonl(task_metadata_path):
        if row.get("attack_plan_id") == attack_plan_id:
            return row
    return None


def _prime_task_metadata_for_attack_plan(
    root: Path,
    attack_plan_id: str,
) -> dict[str, Any] | None:
    module_path = (
        root
        / "prime_intellect"
        / "verifiers_environment"
        / "agades_pqc_verifier_env.py"
    )
    if not module_path.is_file():
        return None
    module = _load_python_module(
        module_path,
        "agades_pqc_prime_boundary_audit",
    )
    for row in module.build_dataset_rows():
        info = row.get("info")
        if isinstance(info, dict) and info.get("attack_plan_id") == attack_plan_id:
            return info
    return None


def _hf_space_labels(root: Path) -> set[str]:
    manifest_path = root / "hf" / "space_manifest.json"
    if not manifest_path.is_file():
        return set()
    manifest = _read_json(manifest_path)
    example_manifest = manifest.get("example_manifest")
    if not isinstance(example_manifest, dict):
        return set()
    labels = example_manifest.get("labels")
    if not isinstance(labels, list):
        return set()
    return {label for label in labels if isinstance(label, str)}


def _set_nested_value(data: dict[str, Any], path: tuple[Any, ...], value: Any) -> None:
    cursor: Any = data
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value


def _mapped_attack_types_from_json(
    data: dict[str, Any],
    mapped_attack_types: set[str],
) -> set[str]:
    operators = data.get("operators")
    if not isinstance(operators, list):
        return set()
    return {
        operator.get("type")
        for operator in operators
        if isinstance(operator, dict) and isinstance(operator.get("type"), str)
        if operator.get("type") in mapped_attack_types
    }


def _is_binary(path: Path) -> bool:
    return b"\0" in path.read_bytes()[:4096]
