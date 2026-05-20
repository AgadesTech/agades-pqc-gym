from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.family_registry_manifest import (
    FAMILY_REGISTRY_VERIFICATION_SCHEMA,
    build_family_registry_manifest,
    verify_family_registry_manifest,
    write_family_registry_manifest,
)

EXPECTED_VALIDATOR_BY_FAMILY = {
    "CODE_BASED": (
        "agades_pqc_gym.families.code_based.validators.validate_code_based_plan"
    ),
    "MULTIVARIATE": (
        "agades_pqc_gym.families.multivariate.validators."
        "validate_multivariate_plan"
    ),
    "HASH_BASED": (
        "agades_pqc_gym.families.hash_based.validators.validate_hash_based_plan"
    ),
    "ISOGENY_HISTORICAL": (
        "agades_pqc_gym.families.isogeny_historical.validators."
        "validate_isogeny_historical_plan"
    ),
    "IMPLEMENTATION_SECURITY": (
        "agades_pqc_gym.families.implementation_security.validators."
        "validate_implementation_security_plan"
    ),
}

EXPECTED_PLUGIN_DESCRIPTOR_BY_FAMILY = {
    "LWE": "agades_pqc_gym.families.lattice.plugin.PLUGIN_DESCRIPTOR",
    "MLWE": "agades_pqc_gym.families.lattice.plugin.PLUGIN_DESCRIPTOR",
    "NTRU": "agades_pqc_gym.families.lattice.plugin.PLUGIN_DESCRIPTOR",
    "SIS": "agades_pqc_gym.families.lattice.plugin.PLUGIN_DESCRIPTOR",
    "CODE_BASED": "agades_pqc_gym.families.code_based.plugin.PLUGIN_DESCRIPTOR",
    "MULTIVARIATE": (
        "agades_pqc_gym.families.multivariate.plugin.PLUGIN_DESCRIPTOR"
    ),
    "HASH_BASED": "agades_pqc_gym.families.hash_based.plugin.PLUGIN_DESCRIPTOR",
    "ISOGENY_HISTORICAL": (
        "agades_pqc_gym.families.isogeny_historical.plugin.PLUGIN_DESCRIPTOR"
    ),
    "IMPLEMENTATION_SECURITY": (
        "agades_pqc_gym.families.implementation_security.plugin."
        "PLUGIN_DESCRIPTOR"
    ),
}


def test_family_registry_manifest_describes_runtime_registry(
    tmp_path: Path,
) -> None:
    out = tmp_path / "family_registry_manifest.json"

    manifest = write_family_registry_manifest(out)

    assert manifest == build_family_registry_manifest()
    assert json.loads(out.read_text(encoding="utf-8")) == manifest
    assert manifest["schema_version"] == "agades.pqc.family_registry_manifest.v1"
    assert manifest["project"] == {
        "cli": "agades-pqc",
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert manifest["summary"] == {
        "applicability_validator_entries": 9,
        "distinct_applicability_validators": 6,
        "family_count": 9,
        "implemented": ["LWE", "MLWE"],
        "lattice_estimator_external_enabled": ["LWE"],
        "lattice_validator_families": ["LWE", "MLWE", "NTRU", "SIS"],
        "non_lattice_applicability_validators": 5,
        "plugin_count": 6,
        "runtime_adapter_entries": 9,
        "schema_only": ["NTRU", "SIS"],
        "toy_evaluators": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
    }
    assert manifest["plugin_manifest_alignment"] == {
        "committed_manifest_synced": True,
        "family_count": 9,
        "implementation_module_count": 55,
        "implementation_module_digest_count": 55,
        "implementation_module_import_count": 55,
        "manifest_path": "docs/family_plugin_manifest.json",
        "plugin_count": 6,
        "registry_family_count_matches_manifest": True,
        "registry_plugin_count_matches_manifest": True,
        "registry_runtime_adapter_entries_match_manifest": True,
        "runtime_adapter_entries": 9,
    }
    assert manifest["safety"] == {
        "lattice_estimator_is_universal_pqc_oracle": False,
        "non_lattice_entries_use_lattice_estimator": False,
        "schema_only_families_have_runtime_estimators": False,
        "security_claim": False,
        "unsupported_families_return_fake_estimates": False,
    }

    by_family = {family["family"]: family for family in manifest["families"]}
    assert list(by_family) == [
        "LWE",
        "MLWE",
        "NTRU",
        "SIS",
        "CODE_BASED",
        "MULTIVARIATE",
        "HASH_BASED",
        "ISOGENY_HISTORICAL",
        "IMPLEMENTATION_SECURITY",
    ]
    for family, descriptor_path in EXPECTED_PLUGIN_DESCRIPTOR_BY_FAMILY.items():
        assert by_family[family]["plugin_descriptor"] == descriptor_path

    assert by_family["LWE"] == {
        "adapter_class": "agades_pqc_gym.families.lattice.adapter.LatticeFamilyAdapter",
        "adapter_family": "LWE",
        "applicability_validator": (
            "agades_pqc_gym.families.lattice.validators.validate_lattice_plan"
        ),
        "default_estimator": "mock-lattice-estimator",
        "family": "LWE",
        "lattice_estimator_boundary": {
            "external_estimator_allowed": True,
            "scope": "reviewed_lwe_mappings_only",
        },
        "operator_catalog_entries": 5,
        "operator_catalog_support_level": "implemented",
        "operator_review_boundary": {
            "catalog_operator_types": [
                "bkw",
                "bounded_distance_decoding",
                "dual_attack",
                "dual_hybrid",
                "primal_usvp",
            ],
            "catalog_variant_entries": 5,
            "external_estimator_operator_types": [
                "bkw",
                "bounded_distance_decoding",
                "dual_attack",
                "dual_hybrid",
                "primal_usvp",
            ],
            "runtime_operator_types": [
                "bkw",
                "bkz_parameter_sweep",
                "bounded_distance_decoding",
                "dual_attack",
                "dual_hybrid",
                "meet_in_the_middle",
                "module_lattice_reduction_hypothesis",
                "modulus_switching",
                "normal_form_transform",
                "primal_usvp",
                "sample_selection",
                "secret_guessing",
            ],
            "runtime_without_catalog_operator_types": [
                "bkz_parameter_sweep",
                "meet_in_the_middle",
                "module_lattice_reduction_hypothesis",
                "modulus_switching",
                "normal_form_transform",
                "sample_selection",
                "secret_guessing",
            ],
        },
        "optional_estimators": ["lattice-estimator"],
        "plugin": "lattice",
        "plugin_descriptor": (
            "agades_pqc_gym.families.lattice.plugin.PLUGIN_DESCRIPTOR"
        ),
        "review_required_before_claims": True,
        "runtime_operator_count": 12,
        "runtime_registered": True,
        "support_level": "implemented",
        "support_matrix_support_level": "implemented",
    }
    assert by_family["MLWE"]["lattice_estimator_boundary"] == {
        "external_estimator_allowed": False,
        "scope": "family_adapter_warning_gated_no_external_manifest_scope",
    }
    assert by_family["MLWE"]["operator_review_boundary"] == {
        "catalog_operator_types": [
            "bkz_parameter_sweep",
            "module_lattice_reduction_hypothesis",
        ],
        "catalog_variant_entries": 2,
        "external_estimator_operator_types": [],
        "runtime_operator_types": [
            "bkw",
            "bkz_parameter_sweep",
            "bounded_distance_decoding",
            "dual_attack",
            "dual_hybrid",
            "meet_in_the_middle",
            "module_lattice_reduction_hypothesis",
            "modulus_switching",
            "normal_form_transform",
            "primal_usvp",
            "sample_selection",
            "secret_guessing",
        ],
        "runtime_without_catalog_operator_types": [
            "bkw",
            "bounded_distance_decoding",
            "dual_attack",
            "dual_hybrid",
            "meet_in_the_middle",
            "modulus_switching",
            "normal_form_transform",
            "primal_usvp",
            "sample_selection",
            "secret_guessing",
        ],
    }
    assert by_family["NTRU"]["default_estimator"] is None
    assert by_family["NTRU"]["runtime_operator_count"] == 0
    assert by_family["NTRU"]["support_level"] == "schema_only"
    assert by_family["SIS"]["support_level"] == "schema_only"

    non_lattice_families = [
        "CODE_BASED",
        "MULTIVARIATE",
        "HASH_BASED",
        "ISOGENY_HISTORICAL",
        "IMPLEMENTATION_SECURITY",
    ]
    for family in non_lattice_families:
        entry = by_family[family]
        assert entry["support_level"] == "toy_evaluator"
        assert (
            entry["plugin_descriptor"]
            == EXPECTED_PLUGIN_DESCRIPTOR_BY_FAMILY[family]
        )
        assert entry["applicability_validator"] == EXPECTED_VALIDATOR_BY_FAMILY[family]
        assert entry["lattice_estimator_boundary"] == {
            "external_estimator_allowed": False,
            "scope": "not_applicable_non_lattice_family",
        }
        assert entry["default_estimator"].startswith("toy-")
        assert "lattice-estimator" not in entry["optional_estimators"]
        assert entry["operator_review_boundary"][
            "runtime_without_catalog_operator_types"
        ] == []
        assert entry["operator_review_boundary"][
            "external_estimator_operator_types"
        ] == []


def test_committed_family_registry_manifest_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "family_registry_manifest.json"
    committed = Path("docs/family_registry_manifest.json")

    write_family_registry_manifest(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_family_registry_manifest_cli_writes_manifest(tmp_path: Path) -> None:
    out = tmp_path / "family_registry_manifest.json"

    result = CliRunner().invoke(app, ["family-registry-manifest", "--out", str(out)])

    assert result.exit_code == 0
    assert f"family_registry_manifest={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["schema_version"] == (
        "agades.pqc.family_registry_manifest.v1"
    )


def test_family_registry_manifest_verify_accepts_committed_manifest() -> None:
    result = verify_family_registry_manifest(Path("docs/family_registry_manifest.json"))

    assert result["schema_version"] == FAMILY_REGISTRY_VERIFICATION_SCHEMA
    assert result["accepted"] is True
    assert result["summary"] == {
        "applicability_validator_entries": 9,
        "distinct_applicability_validators": 6,
        "failure_count": 0,
        "family_count": 9,
        "implemented": ["LWE", "MLWE"],
        "plugin_manifest_family_count": 9,
        "plugin_manifest_implementation_module_count": 55,
        "plugin_manifest_implementation_module_digest_count": 55,
        "plugin_manifest_implementation_module_import_count": 55,
        "plugin_manifest_plugin_count": 6,
        "plugin_manifest_runtime_adapter_entries": 9,
        "plugin_manifest_synced": True,
        "lattice_estimator_external_enabled": ["LWE"],
        "lattice_validator_families": ["LWE", "MLWE", "NTRU", "SIS"],
        "non_lattice_applicability_validators": 5,
        "plugin_count": 6,
        "registry_family_count_matches_plugin_manifest": True,
        "registry_plugin_count_matches_plugin_manifest": True,
        "registry_runtime_adapter_entries_match_plugin_manifest": True,
        "runtime_adapter_entries": 9,
        "schema_only": ["NTRU", "SIS"],
        "toy_evaluators": [
            "CODE_BASED",
            "HASH_BASED",
            "IMPLEMENTATION_SECURITY",
            "ISOGENY_HISTORICAL",
            "MULTIVARIATE",
        ],
    }
    assert result["failures"] == []


def test_family_registry_manifest_verify_rejects_adapter_class_drift(
    tmp_path: Path,
) -> None:
    manifest = build_family_registry_manifest()
    by_family = {family["family"]: family for family in manifest["families"]}
    by_family["HASH_BASED"]["adapter_class"] = (
        "agades_pqc_gym.families.lattice.adapter.LatticeFamilyAdapter"
    )
    out = tmp_path / "family_registry_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_family_registry_manifest(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "HASH_BASED: adapter_class must be "
        "agades_pqc_gym.families.hash_based.adapter.HashBasedFamilyAdapter."
    ]


def test_family_registry_manifest_verify_rejects_plugin_descriptor_drift(
    tmp_path: Path,
) -> None:
    manifest = build_family_registry_manifest()
    by_family = {family["family"]: family for family in manifest["families"]}
    by_family["CODE_BASED"]["plugin_descriptor"] = (
        "agades_pqc_gym.families.lattice.plugin.PLUGIN_DESCRIPTOR"
    )
    out = tmp_path / "family_registry_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_family_registry_manifest(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "CODE_BASED: plugin_descriptor must be "
        "agades_pqc_gym.families.code_based.plugin.PLUGIN_DESCRIPTOR."
    ]


def test_family_registry_manifest_verify_rejects_non_lattice_lattice_estimator(
    tmp_path: Path,
) -> None:
    manifest = build_family_registry_manifest()
    by_family = {family["family"]: family for family in manifest["families"]}
    by_family["CODE_BASED"]["optional_estimators"] = ["lattice-estimator"]
    by_family["CODE_BASED"]["lattice_estimator_boundary"][
        "external_estimator_allowed"
    ] = True
    out = tmp_path / "family_registry_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_family_registry_manifest(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 5
    assert result["failures"] == [
        "CODE_BASED: optional_estimators must match the family support matrix.",
        "CODE_BASED: lattice_estimator_boundary.external_estimator_allowed "
        "is incorrect.",
        "CODE_BASED: only LWE may enable the external Lattice Estimator boundary.",
        "CODE_BASED: non-lattice registry entries must not name lattice-estimator.",
        "manifest: summary is inconsistent with families.",
    ]


def test_family_registry_manifest_verify_rejects_operator_boundary_drift(
    tmp_path: Path,
) -> None:
    manifest = build_family_registry_manifest()
    by_family = {family["family"]: family for family in manifest["families"]}
    by_family["LWE"]["operator_review_boundary"][
        "external_estimator_operator_types"
    ].append("modulus_switching")
    out = tmp_path / "family_registry_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_family_registry_manifest(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "LWE: operator_review_boundary.external_estimator_operator_types "
        "is inconsistent.",
    ]


def test_family_registry_manifest_verify_rejects_plugin_manifest_alignment_drift(
    tmp_path: Path,
) -> None:
    manifest = build_family_registry_manifest()
    manifest["plugin_manifest_alignment"]["committed_manifest_synced"] = False
    manifest["plugin_manifest_alignment"]["implementation_module_digest_count"] = 17
    manifest["plugin_manifest_alignment"][
        "registry_runtime_adapter_entries_match_manifest"
    ] = False
    out = tmp_path / "family_registry_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_family_registry_manifest(out)

    assert result["accepted"] is False
    assert result["summary"]["plugin_manifest_synced"] is False
    assert result["summary"]["plugin_manifest_implementation_module_digest_count"] == 17
    assert (
        result["summary"]["registry_runtime_adapter_entries_match_plugin_manifest"]
        is False
    )
    assert result["summary"]["failure_count"] == 3
    assert result["failures"] == [
        "manifest: plugin_manifest_alignment.committed_manifest_synced "
        "is inconsistent.",
        "manifest: plugin_manifest_alignment.implementation_module_digest_count "
        "is inconsistent.",
        "manifest: plugin_manifest_alignment."
        "registry_runtime_adapter_entries_match_manifest is inconsistent.",
    ]


def test_family_registry_manifest_verify_rejects_runtime_manifest_drift(
    tmp_path: Path,
) -> None:
    manifest = build_family_registry_manifest()
    manifest["release_gates"] = [
        gate
        for gate in manifest["release_gates"]
        if "family-support-verify" not in gate
    ]
    out = tmp_path / "family_registry_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_family_registry_manifest(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "manifest: contents are not synchronized with the current runtime "
        "family registry manifest."
    ]


def test_family_registry_manifest_verify_rejects_non_importable_validator(
    tmp_path: Path,
) -> None:
    manifest = build_family_registry_manifest()
    by_family = {family["family"]: family for family in manifest["families"]}
    by_family["HASH_BASED"]["applicability_validator"] = (
        "agades_pqc_gym.families.hash_based.validators.missing_validator"
    )
    out = tmp_path / "family_registry_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_family_registry_manifest(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 3
    assert result["failures"] == [
        "HASH_BASED: applicability_validator must match the plugin descriptor.",
        "HASH_BASED: applicability_validator must match the catalog.",
        "HASH_BASED: applicability_validator is not importable: module "
        "'agades_pqc_gym.families.hash_based.validators' has no attribute "
        "'missing_validator'.",
    ]


def test_family_registry_manifest_verify_rejects_non_callable_validator(
    tmp_path: Path,
) -> None:
    manifest = build_family_registry_manifest()
    by_family = {family["family"]: family for family in manifest["families"]}
    by_family["CODE_BASED"]["applicability_validator"] = (
        "agades_pqc_gym.families.code_based.plugin.PLUGIN_DESCRIPTOR"
    )
    out = tmp_path / "family_registry_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_family_registry_manifest(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 3
    assert result["failures"] == [
        "CODE_BASED: applicability_validator must match the plugin descriptor.",
        "CODE_BASED: applicability_validator must match the catalog.",
        "CODE_BASED: applicability_validator is not callable.",
    ]


def test_family_registry_manifest_verify_cli_prints_json() -> None:
    result = CliRunner().invoke(
        app,
        [
            "family-registry-manifest-verify",
            "--manifest",
            "docs/family_registry_manifest.json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == FAMILY_REGISTRY_VERIFICATION_SCHEMA
    assert payload["accepted"] is True
