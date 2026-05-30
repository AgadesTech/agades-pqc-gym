from __future__ import annotations

import json
from pathlib import Path

CARD_PATHS = {
    "dataset_card": Path("hf/dataset_card.md"),
    "dataset_readme": Path("hf/dataset/README.md"),
    "benchmark_card": Path("hf/benchmark_card.md"),
    "prime_environment_card": Path("prime_intellect/environment_card.md"),
    "mvp_report": Path("reports/AGADES_PQC_GYM_MVP_REPORT.md"),
}

IMPLEMENTATION_SECURITY_MEMORY_DOC_PATHS = {
    "readme": Path("README.md"),
    "architecture": Path("docs/ARCHITECTURE.md"),
    "family_adapters": Path("docs/FAMILY_ADAPTERS.md"),
    "dataset_card": Path("hf/dataset_card.md"),
    "dataset_readme": Path("hf/dataset/README.md"),
    "prime_environment_card": Path("prime_intellect/environment_card.md"),
    "mvp_report": Path("reports/AGADES_PQC_GYM_MVP_REPORT.md"),
}

IMPLEMENTATION_SECURITY_BINARY_SIZE_DOC_PATHS = {
    "readme": Path("README.md"),
    "architecture": Path("docs/ARCHITECTURE.md"),
    "family_adapters": Path("docs/FAMILY_ADAPTERS.md"),
    "dataset_card": Path("hf/dataset_card.md"),
    "dataset_readme": Path("hf/dataset/README.md"),
    "prime_environment_card": Path("prime_intellect/environment_card.md"),
    "mvp_report": Path("reports/AGADES_PQC_GYM_MVP_REPORT.md"),
}

IMPLEMENTATION_SECURITY_CONSTANT_TIME_DOC_PATHS = {
    "readme": Path("README.md"),
    "architecture": Path("docs/ARCHITECTURE.md"),
    "family_adapters": Path("docs/FAMILY_ADAPTERS.md"),
    "dataset_card": Path("hf/dataset_card.md"),
    "dataset_readme": Path("hf/dataset/README.md"),
    "prime_environment_card": Path("prime_intellect/environment_card.md"),
    "mvp_report": Path("reports/AGADES_PQC_GYM_MVP_REPORT.md"),
}

IMPLEMENTATION_SECURITY_SOURCE_SCHEMA_DOC_PATHS = {
    "readme": Path("README.md"),
    "architecture": Path("docs/ARCHITECTURE.md"),
    "family_adapters": Path("docs/FAMILY_ADAPTERS.md"),
    "mvp_report": Path("reports/AGADES_PQC_GYM_MVP_REPORT.md"),
}

HASH_BASED_SLH_DSA_DOC_PATHS = {
    "readme": Path("README.md"),
    "architecture": Path("docs/ARCHITECTURE.md"),
    "family_adapters": Path("docs/FAMILY_ADAPTERS.md"),
    "dataset_card": Path("hf/dataset_card.md"),
    "dataset_readme": Path("hf/dataset/README.md"),
    "benchmark_card": Path("hf/benchmark_card.md"),
    "prime_environment_card": Path("prime_intellect/environment_card.md"),
    "mvp_report": Path("reports/AGADES_PQC_GYM_MVP_REPORT.md"),
}

CODE_BASED_HQC_CIRCULANT_ERASURE_DOC_PATHS = {
    "readme": Path("README.md"),
    "family_adapters": Path("docs/FAMILY_ADAPTERS.md"),
    "dataset_card": Path("hf/dataset_card.md"),
    "dataset_readme": Path("hf/dataset/README.md"),
    "benchmark_card": Path("hf/benchmark_card.md"),
    "prime_environment_card": Path("prime_intellect/environment_card.md"),
    "mvp_report": Path("reports/AGADES_PQC_GYM_MVP_REPORT.md"),
    "nvidia_strategy": Path("docs/NVIDIA_AND_ACCELERATOR_STRATEGY.md"),
    "nvidia_readme": Path("nvidia/README.md"),
}

FAMILY_ADAPTER_DOC = Path("docs/FAMILY_ADAPTERS.md")

TOY_FAMILY_PHRASES = {
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


def test_public_release_cards_cover_current_toy_families_and_bundles() -> None:
    family_support = json.loads(Path("docs/family_support_matrix.json").read_text())
    dataset_info = json.loads(Path("hf/dataset/dataset_info.json").read_text())
    cards = {
        name: path.read_text(encoding="utf-8") for name, path in CARD_PATHS.items()
    }

    toy_families = {
        family["family"]
        for family in family_support["families"]
        if family["support_level"] == "toy_evaluator"
    }

    assert toy_families == set(TOY_FAMILY_PHRASES)
    for family, phrases in TOY_FAMILY_PHRASES.items():
        for phrase in phrases:
            assert phrase in cards["dataset_card"], family
            assert phrase in cards["dataset_readme"], family
            assert phrase in cards["prime_environment_card"], family
            assert phrase in cards["mvp_report"], family

    for bundle_id in dataset_info["public_run_bundles"]:
        assert bundle_id in cards["dataset_card"]
        assert bundle_id in cards["dataset_readme"]
        assert bundle_id in cards["benchmark_card"]
        assert bundle_id in cards["prime_environment_card"]
        assert bundle_id in cards["mvp_report"]


def test_public_release_cards_do_not_describe_toy_families_as_schema_only() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in CARD_PATHS.values()
    )

    stale_claims = [
        "Only LWE/MLWE has an implemented MVP evaluation path",
        "Non-lattice families are schema-only",
        (
            "Code-based, multivariate, hash-based, historical isogeny, "
            "implementation-security: schema-only placeholders"
        ),
    ]

    for stale_claim in stale_claims:
        assert stale_claim not in combined


def test_public_docs_cover_implementation_security_memory_footprint_surface() -> None:
    operator_catalog = json.loads(Path("docs/family_operator_catalog.json").read_text())
    implementation_entries = [
        entry
        for family in operator_catalog["families"]
        if family["family"] == "IMPLEMENTATION_SECURITY"
        for entry in family["operators"]
    ]

    assert any(
        entry["variant"] == "toy_memory_footprint_check"
        for entry in implementation_entries
    )

    docs = {
        name: path.read_text(encoding="utf-8")
        for name, path in IMPLEMENTATION_SECURITY_MEMORY_DOC_PATHS.items()
    }
    for name, content in docs.items():
        assert "toy_memory_footprint_check" in content, name
        assert "memory-footprint" in content, name


def test_public_docs_cover_implementation_security_binary_size_surface() -> None:
    operator_catalog = json.loads(Path("docs/family_operator_catalog.json").read_text())
    implementation_entries = [
        entry
        for family in operator_catalog["families"]
        if family["family"] == "IMPLEMENTATION_SECURITY"
        for entry in family["operators"]
    ]

    assert any(
        entry["variant"] == "toy_binary_size_check" for entry in implementation_entries
    )

    docs = {
        name: path.read_text(encoding="utf-8")
        for name, path in IMPLEMENTATION_SECURITY_BINARY_SIZE_DOC_PATHS.items()
    }
    for name, content in docs.items():
        assert "toy_binary_size_check" in content, name
        assert "binary-size" in content, name


def test_public_docs_cover_implementation_security_constant_time_summary_surfaces() -> (
    None
):
    operator_catalog = json.loads(Path("docs/family_operator_catalog.json").read_text())
    implementation_entries = [
        entry
        for family in operator_catalog["families"]
        if family["family"] == "IMPLEMENTATION_SECURITY"
        for entry in family["operators"]
    ]

    assert any(
        entry["variant"] == "toy_dudect_summary_threshold_check"
        for entry in implementation_entries
    )
    assert any(
        entry["variant"] == "toy_ctgrind_secret_taint_summary_check"
        for entry in implementation_entries
    )

    docs = {
        name: path.read_text(encoding="utf-8")
        for name, path in IMPLEMENTATION_SECURITY_CONSTANT_TIME_DOC_PATHS.items()
    }
    for name, content in docs.items():
        normalized = " ".join(content.split())
        assert "toy_dudect_summary_threshold_check" in normalized, name
        assert "toy_ctgrind_secret_taint_summary_check" in normalized, name
        assert "dudect-style" in normalized, name
        assert "ctgrind-style" in normalized, name
        assert "without executing dudect" in normalized, name
        assert "without executing ctgrind" in normalized, name
        assert "no constant-time, side-channel, or security claim" in normalized, name


def test_public_docs_cover_implementation_security_source_schema_placeholders() -> None:
    schema_only_paths = [
        Path("examples/attack_plans/implementation_security_dudect_schema.json"),
        Path("examples/attack_plans/implementation_security_ctgrind_schema.json"),
        Path("examples/attack_plans/implementation_security_timecop_schema.json"),
        Path("examples/attack_plans/implementation_security_nist_acvp_schema.json"),
    ]
    for path in schema_only_paths:
        attack_plan = json.loads(path.read_text(encoding="utf-8"))
        assert attack_plan["target"]["support_level"] == "schema_only"
        assert attack_plan["operators"][0]["type"] in {
            "constant_time_check",
            "kat_conformance",
        }

    docs = {
        name: path.read_text(encoding="utf-8")
        for name, path in IMPLEMENTATION_SECURITY_SOURCE_SCHEMA_DOC_PATHS.items()
    }
    for name, content in docs.items():
        normalized = " ".join(content.split())
        assert "dudect" in normalized, name
        assert "ctgrind" in normalized, name
        assert "TIMECOP/SUPERCOP" in normalized, name
        assert "nist_acvp_pqc_vectors_schema" in normalized, name
        assert "ACVP server" in normalized, name
        assert "schema-only" in normalized, name
        assert "no ACVP, conformance, side-channel, or security claim" in normalized, (
            name
        )
        assert "no constant-time, side-channel, or security claim" in normalized, name


def test_public_docs_cover_hash_based_slh_dsa_hypertree_surface() -> None:
    operator_catalog = json.loads(Path("docs/family_operator_catalog.json").read_text())
    hash_entries = [
        entry
        for family in operator_catalog["families"]
        if family["family"] == "HASH_BASED"
        for entry in family["operators"]
    ]

    assert any(
        entry["variant"] == "toy_slh_dsa_hypertree_verify" for entry in hash_entries
    )

    docs = {
        name: path.read_text(encoding="utf-8")
        for name, path in HASH_BASED_SLH_DSA_DOC_PATHS.items()
    }
    for name, content in docs.items():
        assert "toy_slh_dsa_hypertree_verify" in content, name
        assert "SLH-DSA-like hypertree" in content, name
        assert "not an SLH-DSA result" in content, name


def test_public_docs_cover_code_based_hqc_circulant_erasure_surface() -> None:
    operator_catalog = json.loads(Path("docs/family_operator_catalog.json").read_text())
    code_based_entries = [
        entry
        for family in operator_catalog["families"]
        if family["family"] == "CODE_BASED"
        for entry in family["operators"]
    ]

    assert any(
        entry["variant"] == "hqc_circulant_erasure_toy"
        and entry["default_estimator"]
        == "toy-code-based-circulant-erasure-decoder-estimator"
        for entry in code_based_entries
    )

    docs = {
        name: path.read_text(encoding="utf-8")
        for name, path in CODE_BASED_HQC_CIRCULANT_ERASURE_DOC_PATHS.items()
    }
    for name, content in docs.items():
        normalized = " ".join(content.split())
        assert "circulant-erasure" in normalized, name
        assert "not an HQC result" in normalized, name


def test_public_docs_describe_current_lwe_downscaled_fixture_count() -> None:
    public_benchmark = json.loads(
        Path("docs/public_benchmark_manifest.json").read_text(encoding="utf-8")
    )
    bundle = next(
        entry
        for entry in public_benchmark["bundles"]
        if entry["id"] == "lattice_downscaled_lwe_instance_solve_v0"
    )
    docs = {
        "mvp_report": CARD_PATHS["mvp_report"].read_text(encoding="utf-8"),
        "status": Path("docs/STATUS.md").read_text(encoding="utf-8"),
    }

    assert bundle["record_count"] == 3
    for name, content in docs.items():
        assert "three tiny public LWE" in content, name
        assert "ternary-secret" in content, name
        assert "two tiny public LWE" not in content, name
        assert "two-record tiny LWE" not in content, name
        assert "two-record `lattice_downscaled_lwe_instance_solve_v0`" not in content


def test_family_adapter_docs_match_classic_support_syndrome_bounds() -> None:
    content = FAMILY_ADAPTER_DOC.read_text(encoding="utf-8")

    global_code_based_line = next(
        line for line in content.splitlines() if "`k < n` and `w < n`" in line
    )
    support_syndrome_line = next(
        line
        for line in content.splitlines()
        if "`classic_mceliece_support_syndrome_toy` plans must include" in line
    )

    assert "w <= n-k" not in global_code_based_line
    assert "support_size >= max_error_weight" in support_syndrome_line
    assert "support_size <= n" in support_syndrome_line
    assert "w <= n-k" not in support_syndrome_line


def test_roadmap_tracks_current_public_release_state() -> None:
    public_benchmark = json.loads(
        Path("docs/public_benchmark_manifest.json").read_text(encoding="utf-8")
    )
    benchmark_contracts = json.loads(
        Path("docs/benchmark_source_contracts.json").read_text(encoding="utf-8")
    )
    release_status = json.loads(
        Path("docs/release_status.json").read_text(encoding="utf-8")
    )
    prime_task_count = release_status["ecosystem"]["prime_intellect"]["task_count"]
    hf_space_example_count = release_status["ecosystem"]["huggingface_space"][
        "example_count"
    ]
    roadmap = Path("docs/ROADMAP.md").read_text(encoding="utf-8")
    normalized_roadmap = " ".join(roadmap.split())

    expected_current_state = [
        "## Current Public Baseline",
        f"{public_benchmark['summary']['bundle_count']} public benchmark bundles",
        f"{public_benchmark['summary']['record_count']} accepted public records",
        "three tiny public LWE",
        "ternary-secret",
        (
            f"{len(benchmark_contracts['contracts'])} future reviewed adapter "
            "source contracts"
        ),
        "Hugging Face PQC/SCA dataset anchors",
        f"{prime_task_count} Prime JSON verifier tasks",
        f"{hf_space_example_count} Hugging Face Space examples",
        "Hugging Face collection manifest",
        "NVIDIA accelerator manifest",
        "Prime Hub publication remains credentialed and review-gated",
        "## Future Reviewed Work",
    ]
    stale_claims = [
        "Hugging Face dataset card and Space plan",
        "Publish public benchmark v0",
        "Expand downscaled reproduction beyond the initial tiny public LWE fixtures",
    ]

    for expected in expected_current_state:
        assert expected in normalized_roadmap
    for stale_claim in stale_claims:
        assert stale_claim not in normalized_roadmap


def test_public_docs_describe_lattice_estimator_baseline_contract_boundary() -> None:
    docs = {
        "readme": Path("README.md").read_text(encoding="utf-8"),
        "roadmap": Path("docs/ROADMAP.md").read_text(encoding="utf-8"),
        "status": Path("docs/STATUS.md").read_text(encoding="utf-8"),
    }
    for name, content in docs.items():
        assert "docs/lattice_estimator_baseline_contracts.json" in content, name
        assert "review_contract_ready_not_reproduced" in content, name
        assert "not a numeric Lattice Estimator baseline reproduction" in content, name


def test_readme_describes_sage_worker_lattice_estimator_baseline_path() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    normalized = " ".join(readme.split())

    assert "agades-pqc lattice-estimator-runtime-preflight" in normalized
    assert "agades-pqc lattice-estimator-runtime-preflight-verify" in normalized
    assert "agades-pqc lattice-estimator-checkout-preflight" in normalized
    assert "agades-pqc lattice-estimator-baseline-run" in normalized
    assert "--estimator-source <path>" in normalized
    assert "--sage-command sage" in normalized
    assert "--sage-python-command <python-with-sage-all>" in normalized
    assert "sage -python" in normalized
    assert "conda-style installs" in normalized
    assert "private/reports/" in normalized
    assert "no public numeric outputs" in normalized


def test_readme_lists_checked_release_smoke_reports() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    required_commands = (
        (
            "uv run agades-pqc openevolve-config --out "
            "examples/openevolve/config.yaml"
        ),
        (
            "uv run agades-pqc openevolve-config-verify --config "
            "examples/openevolve/config.yaml"
        ),
        (
            "uv run agades-pqc hf-space-smoke --out "
            "reports/hf_space_smoke.json"
        ),
        (
            "uv run agades-pqc hf-space-smoke-verify --report "
            "reports/hf_space_smoke.json"
        ),
        (
            "uv run agades-pqc nvidia-manifest-safety --out "
            "reports/nvidia_manifest_safety.json"
        ),
        (
            "uv run agades-pqc nvidia-manifest-safety-verify --report "
            "reports/nvidia_manifest_safety.json"
        ),
        (
            "uv run agades-pqc openevolve-smoke --out "
            "reports/openevolve_smoke.json"
        ),
        (
            "uv run agades-pqc openevolve-smoke-verify --report "
            "reports/openevolve_smoke.json"
        ),
        (
            "uv run agades-pqc prime-environment-smoke --out "
            "reports/prime_environment_smoke.json"
        ),
        (
            "uv run agades-pqc prime-environment-smoke-verify --report "
            "reports/prime_environment_smoke.json"
        ),
        (
            "uv run agades-pqc ecosystem-smoke --out "
            "reports/ecosystem_smoke.json"
        ),
        (
            "uv run agades-pqc ecosystem-smoke-verify --report "
            "reports/ecosystem_smoke.json"
        ),
        "uv run agades-pqc release-artifacts --max-passes 6",
    )

    for command in required_commands:
        assert command in readme
    assert "/tmp/agades_ecosystem_smoke.json" not in readme
    assert "/tmp/agades_openevolve_config.yaml" not in readme
    assert "/tmp/agades_openevolve_smoke.json" not in readme
