from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.family_plugin_manifest import (
    FAMILY_PLUGIN_MANIFEST_VERIFICATION_SCHEMA,
    build_family_plugin_manifest,
    verify_family_plugin_manifest,
    write_family_plugin_manifest,
)

EXPECTED_PLUGIN_ORDER = [
    "lattice",
    "code_based",
    "multivariate",
    "hash_based",
    "isogeny_historical",
    "implementation_security",
]
EXPECTED_FAMILY_ORDER = [
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


def test_family_plugin_manifest_describes_descriptor_layer(tmp_path: Path) -> None:
    out = tmp_path / "family_plugin_manifest.json"

    manifest = write_family_plugin_manifest(out)

    assert manifest == build_family_plugin_manifest()
    assert json.loads(out.read_text(encoding="utf-8")) == manifest
    assert manifest["schema_version"] == "agades.pqc.family_plugin_manifest.v1"
    assert manifest["project"] == {
        "cli": "agades-pqc",
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert manifest["summary"] == {
        "family_count": 9,
        "implemented": ["LWE", "MLWE"],
        "implementation_module_digest_count": 55,
        "implementation_module_count": 55,
        "implementation_module_import_count": 55,
        "lattice_plugin_families": ["LWE", "MLWE", "NTRU", "SIS"],
        "non_lattice_plugin_count": 5,
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
    assert manifest["safety"] == {
        "family_plugins_are_extension_boundary": True,
        "lattice_estimator_is_universal_pqc_oracle": False,
        "non_lattice_plugins_use_lattice_validator": False,
        "non_lattice_plugins_use_lattice_estimator": False,
        "schema_only_families_have_runtime_estimators": False,
        "security_claim": False,
    }

    by_plugin = {plugin["plugin"]: plugin for plugin in manifest["plugins"]}
    assert list(by_plugin) == EXPECTED_PLUGIN_ORDER
    assert by_plugin["lattice"]["descriptor_path"] == (
        "agades_pqc_gym.families.lattice.plugin.PLUGIN_DESCRIPTOR"
    )
    assert by_plugin["lattice"]["implementation_module_count"] == 7
    assert by_plugin["lattice"]["implementation_module_digest_count"] == 7
    assert by_plugin["lattice"]["implementation_module_import_count"] == 7
    assert by_plugin["lattice"]["implementation_modules"] == [
        "src/agades_pqc_gym/families/lattice/adapter.py",
        "src/agades_pqc_gym/families/lattice/downscaled_solver.py",
        "src/agades_pqc_gym/families/lattice/lattice_estimator.py",
        "src/agades_pqc_gym/families/lattice/operators.py",
        "src/agades_pqc_gym/families/lattice/plugin.py",
        "src/agades_pqc_gym/families/lattice/targets.py",
        "src/agades_pqc_gym/families/lattice/validators.py",
    ]
    assert by_plugin["lattice"]["implementation_module_imports"] == [
        "agades_pqc_gym.families.lattice.adapter",
        "agades_pqc_gym.families.lattice.downscaled_solver",
        "agades_pqc_gym.families.lattice.lattice_estimator",
        "agades_pqc_gym.families.lattice.operators",
        "agades_pqc_gym.families.lattice.plugin",
        "agades_pqc_gym.families.lattice.targets",
        "agades_pqc_gym.families.lattice.validators",
    ]
    lattice_digests = by_plugin["lattice"]["implementation_module_digests"]
    assert sorted(lattice_digests) == by_plugin["lattice"]["implementation_modules"]
    assert all(
        len(digest) == 64 and set(digest) <= set("0123456789abcdef")
        for digest in lattice_digests.values()
    )
    assert by_plugin["code_based"]["implementation_module_count"] == 13
    assert by_plugin["code_based"]["implementation_module_digest_count"] == 13
    assert by_plugin["code_based"]["implementation_module_import_count"] == 13
    assert (
        "src/agades_pqc_gym/families/code_based/hqc_fixture_estimator.py"
        in by_plugin["code_based"]["implementation_modules"]
    )
    assert (
        "agades_pqc_gym.families.code_based.hqc_fixture_estimator"
        in by_plugin["code_based"]["implementation_module_imports"]
    )
    assert [
        family["family"] for family in by_plugin["lattice"]["families"]
    ] == ["LWE", "MLWE", "NTRU", "SIS"]

    all_families = [
        family["family"]
        for plugin in manifest["plugins"]
        for family in plugin["families"]
    ]
    assert all_families == EXPECTED_FAMILY_ORDER

    for plugin in manifest["plugins"]:
        for family in plugin["families"]:
            assert family["runtime_registered"] is True
            assert family["review_required_before_claims"] is True

    non_lattice_plugins = [
        plugin for plugin in manifest["plugins"] if plugin["plugin"] != "lattice"
    ]
    for plugin in non_lattice_plugins:
        assert plugin["lattice_estimator_boundary"] == {
            "external_estimator_allowed": False,
            "scope": "not_applicable_non_lattice_plugin",
        }
        for family in plugin["families"]:
            assert ".families.lattice." not in family["applicability_validator"]
            assert family["applicability_validator"].startswith(
                f"agades_pqc_gym.families.{plugin['plugin']}."
            )

    assert (
        "uv run agades-pqc family-plugin-manifest --out "
        "docs/family_plugin_manifest.json"
    ) in manifest["release_gates"]
    assert (
        "uv run agades-pqc family-plugin-manifest-verify --manifest "
        "docs/family_plugin_manifest.json"
    ) in manifest["release_gates"]


def test_committed_family_plugin_manifest_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "family_plugin_manifest.json"
    committed = Path("docs/family_plugin_manifest.json")

    write_family_plugin_manifest(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_family_plugin_manifest_discovers_modules_from_requested_root(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    extra_module = (
        copied_root
        / "src"
        / "agades_pqc_gym"
        / "families"
        / "hash_based"
        / "copied_root_probe.py"
    )
    extra_module.write_text(
        "from __future__ import annotations\n\nROOT_ONLY_PROBE = True\n",
        encoding="utf-8",
    )

    manifest = build_family_plugin_manifest(root=copied_root)
    hash_based = next(
        plugin for plugin in manifest["plugins"] if plugin["plugin"] == "hash_based"
    )

    assert (
        "src/agades_pqc_gym/families/hash_based/copied_root_probe.py"
        in hash_based["implementation_modules"]
    )
    assert (
        "agades_pqc_gym.families.hash_based.copied_root_probe"
        in hash_based["implementation_module_imports"]
    )


def test_family_plugin_manifest_verify_accepts_committed_manifest() -> None:
    result = verify_family_plugin_manifest(Path("docs/family_plugin_manifest.json"))

    assert result == {
        "schema_version": FAMILY_PLUGIN_MANIFEST_VERIFICATION_SCHEMA,
        "manifest_path": "docs/family_plugin_manifest.json",
        "accepted": True,
        "summary": {
            "family_count": 9,
            "failure_count": 0,
            "implemented": ["LWE", "MLWE"],
            "implementation_module_digest_count": 55,
            "implementation_module_count": 55,
            "implementation_module_import_count": 55,
            "lattice_plugin_families": ["LWE", "MLWE", "NTRU", "SIS"],
            "non_lattice_plugin_count": 5,
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
        },
        "failures": [],
    }


def test_family_plugin_manifest_verify_rejects_lattice_validator_drift(
    tmp_path: Path,
) -> None:
    manifest = build_family_plugin_manifest()
    code_based = next(
        plugin for plugin in manifest["plugins"] if plugin["plugin"] == "code_based"
    )
    code_based["families"][0]["applicability_validator"] = (
        "agades_pqc_gym.families.lattice.validators.validate_lattice_plan"
    )
    out = tmp_path / "family_plugin_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_family_plugin_manifest(out)

    assert result["accepted"] is False
    assert "CODE_BASED: non-lattice plugin must not use lattice validator." in result[
        "failures"
    ]


def test_family_plugin_manifest_verify_rejects_descriptor_drift(
    tmp_path: Path,
) -> None:
    manifest = build_family_plugin_manifest()
    manifest["plugins"][0]["descriptor_path"] = (
        "agades_pqc_gym.families.code_based.plugin.PLUGIN_DESCRIPTOR"
    )
    out = tmp_path / "family_plugin_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_family_plugin_manifest(out)

    assert result["accepted"] is False
    assert "lattice: descriptor_path must match the plugin descriptor." in result[
        "failures"
    ]


def test_family_plugin_manifest_verify_rejects_module_import_drift(
    tmp_path: Path,
) -> None:
    manifest = build_family_plugin_manifest()
    code_based = next(
        plugin for plugin in manifest["plugins"] if plugin["plugin"] == "code_based"
    )
    code_based["implementation_module_imports"].remove(
        "agades_pqc_gym.families.code_based.hqc_fixture_estimator"
    )
    code_based["implementation_module_import_count"] -= 1
    out = tmp_path / "family_plugin_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_family_plugin_manifest(out)

    assert result["accepted"] is False
    assert (
        "code_based: implementation_module_imports must match implementation_modules."
        in result["failures"]
    )


def test_family_plugin_manifest_verify_rejects_module_digest_drift(
    tmp_path: Path,
) -> None:
    manifest = build_family_plugin_manifest()
    code_based = next(
        plugin for plugin in manifest["plugins"] if plugin["plugin"] == "code_based"
    )
    code_based["implementation_module_digests"] = dict.fromkeys(
        code_based["implementation_modules"],
        "0" * 64,
    )
    code_based["implementation_module_digest_count"] = len(
        code_based["implementation_module_digests"]
    )
    out = tmp_path / "family_plugin_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_family_plugin_manifest(out)

    assert result["accepted"] is False
    assert (
        "code_based: implementation_module_digests must match discovered module "
        "SHA-256 digests."
    ) in result["failures"]


def test_family_plugin_manifest_verify_rejects_runtime_manifest_drift(
    tmp_path: Path,
) -> None:
    manifest = build_family_plugin_manifest()
    manifest["release_gates"] = [
        gate
        for gate in manifest["release_gates"]
        if "family-registry-manifest-verify" not in gate
    ]
    out = tmp_path / "family_plugin_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    result = verify_family_plugin_manifest(out)

    assert result["accepted"] is False
    assert result["summary"]["failure_count"] == 1
    assert result["failures"] == [
        "manifest: contents are not synchronized with the current runtime family "
        "plugin manifest."
    ]


def test_family_plugin_manifest_cli_writes_manifest(tmp_path: Path) -> None:
    out = tmp_path / "family_plugin_manifest.json"

    result = CliRunner().invoke(app, ["family-plugin-manifest", "--out", str(out)])

    assert result.exit_code == 0
    assert f"family_plugin_manifest={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["schema_version"] == (
        "agades.pqc.family_plugin_manifest.v1"
    )


def test_family_plugin_manifest_verify_cli_prints_json() -> None:
    result = CliRunner().invoke(
        app,
        [
            "family-plugin-manifest-verify",
            "--manifest",
            "docs/family_plugin_manifest.json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == FAMILY_PLUGIN_MANIFEST_VERIFICATION_SCHEMA
    assert payload["accepted"] is True
    assert payload["summary"]["plugin_count"] == 6
