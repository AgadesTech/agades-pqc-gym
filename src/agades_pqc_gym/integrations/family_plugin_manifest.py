from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.family_plugin import (
    FamilyPluginDescriptor,
    FamilyPluginEntry,
)
from agades_pqc_gym.core.registry import FamilyRegistry, default_family_registry
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.families.plugins import family_plugin_descriptors

FAMILY_PLUGIN_MANIFEST_SCHEMA = "agades.pqc.family_plugin_manifest.v1"
FAMILY_PLUGIN_MANIFEST_VERIFICATION_SCHEMA = (
    "agades.pqc.family_plugin_manifest_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
PROJECT = {
    "cli": "agades-pqc",
    "name": "Agades PQC Gym",
    "package": "agades_pqc_gym",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
}
EXPECTED_FALSE_SAFETY_FLAGS = (
    "lattice_estimator_is_universal_pqc_oracle",
    "non_lattice_plugins_use_lattice_validator",
    "non_lattice_plugins_use_lattice_estimator",
    "schema_only_families_have_runtime_estimators",
    "security_claim",
)
LATTICE_PLUGIN_NAME = "lattice"
MODULE_IMPORT_PROBE_SCRIPT = r"""
import importlib
import json
import sys

failures = []
for module_name in json.loads(sys.argv[1]):
    try:
        importlib.import_module(module_name)
    except Exception as exc:
        failures.append(
            f"{module_name} is not importable: {type(exc).__name__}: {exc}"
        )

print(json.dumps(failures, sort_keys=True))
raise SystemExit(1 if failures else 0)
"""


def build_family_plugin_manifest(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    registry = default_family_registry()
    plugins = [
        _plugin_entry(descriptor, registry=registry, root=project_root)
        for descriptor in family_plugin_descriptors()
    ]
    return {
        "schema_version": FAMILY_PLUGIN_MANIFEST_SCHEMA,
        "project": PROJECT,
        "summary": _summary(plugins),
        "plugins": plugins,
        "safety": {
            "family_plugins_are_extension_boundary": True,
            "lattice_estimator_is_universal_pqc_oracle": False,
            "non_lattice_plugins_use_lattice_validator": False,
            "non_lattice_plugins_use_lattice_estimator": False,
            "schema_only_families_have_runtime_estimators": False,
            "security_claim": False,
        },
        "release_gates": [
            "uv run pytest tests/test_family_plugin_manifest.py -q",
            "uv run agades-pqc family-plugin-manifest --out "
            "docs/family_plugin_manifest.json",
            "uv run agades-pqc family-plugin-manifest-verify --manifest "
            "docs/family_plugin_manifest.json",
            "uv run agades-pqc family-registry-manifest-verify --manifest "
            "docs/family_registry_manifest.json",
            "uv run agades-pqc family-operator-catalog-verify --catalog "
            "docs/family_operator_catalog.json",
            "uv run agades-pqc ecosystem-smoke-verify --report "
            "reports/ecosystem_smoke.json",
            "uv run agades-pqc release-audit --out public/release_audit.json",
        ],
    }


def write_family_plugin_manifest(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    manifest = build_family_plugin_manifest(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_family_plugin_manifest(
    path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    manifest = _read_manifest(path, failures)
    project_root = (root or ROOT).resolve()

    if manifest.get("schema_version") != FAMILY_PLUGIN_MANIFEST_SCHEMA:
        failures.append(
            f"manifest: schema_version must be {FAMILY_PLUGIN_MANIFEST_SCHEMA}."
        )
    if manifest.get("project") != PROJECT:
        failures.append("manifest: project metadata is not the Agades PQC Gym project.")

    _verify_safety(manifest, failures)
    plugins = manifest.get("plugins")
    if not isinstance(plugins, list):
        failures.append("manifest: plugins must be a list.")
        plugins = []

    summary = _verify_plugin_entries(plugins, failures, root=project_root)
    if manifest.get("summary") != _summary(
        [plugin for plugin in plugins if isinstance(plugin, dict)]
    ):
        failures.append("manifest: summary is inconsistent with plugins.")
    if not failures and manifest != build_family_plugin_manifest(root=project_root):
        failures.append(
            "manifest: contents are not synchronized with the current runtime "
            "family plugin manifest."
        )
    summary["failure_count"] = len(failures)

    return {
        "schema_version": FAMILY_PLUGIN_MANIFEST_VERIFICATION_SCHEMA,
        "manifest_path": str(path),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _plugin_entry(
    descriptor: FamilyPluginDescriptor,
    *,
    registry: FamilyRegistry,
    root: Path,
) -> dict[str, Any]:
    implementation_modules = _implementation_modules(descriptor.name, root=root)
    implementation_module_digests = _implementation_module_digests(
        implementation_modules,
        root=root,
    )
    implementation_module_imports = [
        _source_path_to_module(path) for path in implementation_modules
    ]
    return {
        "plugin": descriptor.name,
        "descriptor_path": descriptor.descriptor_path,
        "family_count": len(descriptor.families),
        "families": [
            _family_entry(entry, registry=registry) for entry in descriptor.families
        ],
        "implementation_module_count": len(implementation_modules),
        "implementation_module_digest_count": len(implementation_module_digests),
        "implementation_module_digests": implementation_module_digests,
        "implementation_module_import_count": len(implementation_module_imports),
        "implementation_module_imports": implementation_module_imports,
        "implementation_modules": implementation_modules,
        "lattice_estimator_boundary": _lattice_estimator_boundary(descriptor.name),
    }


def _family_entry(
    entry: FamilyPluginEntry,
    *,
    registry: FamilyRegistry,
) -> dict[str, Any]:
    registry.get(entry.family)
    return {
        "family": entry.family.value,
        "adapter_class": entry.adapter_class,
        "support_level": entry.support_level,
        "applicability_validator": entry.applicability_validator,
        "runtime_registered": True,
        "review_required_before_claims": True,
    }


def _verify_safety(manifest: dict[str, Any], failures: list[str]) -> None:
    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        failures.append("manifest: safety must be an object.")
        return
    if safety.get("family_plugins_are_extension_boundary") is not True:
        failures.append(
            "manifest: safety.family_plugins_are_extension_boundary must be true."
        )
    for flag in EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            failures.append(f"manifest: safety.{flag} must be false.")


def _verify_plugin_entries(
    plugins: list[Any],
    failures: list[str],
    *,
    root: Path,
) -> dict[str, Any]:
    descriptors = family_plugin_descriptors()
    registry = default_family_registry()
    expected_order = [descriptor.name for descriptor in descriptors]
    by_name: dict[str, dict[str, Any]] = {}

    for index, plugin in enumerate(plugins):
        if not isinstance(plugin, dict):
            failures.append(f"plugin[{index}]: plugin entry must be an object.")
            continue
        name = plugin.get("plugin")
        if not isinstance(name, str) or not name:
            failures.append(f"plugin[{index}]: plugin must be a non-empty string.")
            continue
        if name in by_name:
            failures.append(f"{name}: duplicate plugin entry.")
            continue
        by_name[name] = plugin

    observed_order = list(by_name)
    if observed_order != expected_order:
        failures.append("manifest: plugin order must follow descriptor declaration.")

    expected_names = set(expected_order)
    observed_names = set(by_name)
    for missing in sorted(expected_names - observed_names):
        failures.append(f"{missing}: missing plugin entry.")
    for unexpected in sorted(observed_names - expected_names):
        failures.append(f"{unexpected}: unexpected plugin entry.")

    seen_families: list[str] = []
    for descriptor in descriptors:
        plugin = by_name.get(descriptor.name)
        if plugin is None:
            continue
        _verify_plugin_entry(
            plugin,
            descriptor,
            seen_families,
            failures,
            registry=registry,
            root=root,
        )

    expected_families = [family.value for family in TargetFamily]
    if seen_families != expected_families:
        failures.append("manifest: family order must follow TargetFamily declaration.")

    return _summary([plugin for plugin in plugins if isinstance(plugin, dict)])


def _verify_plugin_entry(
    plugin: dict[str, Any],
    descriptor: FamilyPluginDescriptor,
    seen_families: list[str],
    failures: list[str],
    *,
    registry: FamilyRegistry,
    root: Path,
) -> None:
    name = descriptor.name
    if plugin.get("descriptor_path") != descriptor.descriptor_path:
        failures.append(f"{name}: descriptor_path must match the plugin descriptor.")
    else:
        _verify_import_resolves_to(
            plugin["descriptor_path"],
            descriptor,
            f"{name}: descriptor_path",
            failures,
        )

    if plugin.get("family_count") != len(descriptor.families):
        failures.append(f"{name}: family_count is inconsistent.")
    _verify_implementation_modules(plugin, name, failures, root=root)
    boundary = plugin.get("lattice_estimator_boundary")
    expected_boundary = _lattice_estimator_boundary(name)
    if boundary != expected_boundary:
        failures.append(f"{name}: lattice_estimator_boundary is inconsistent.")

    families = plugin.get("families")
    if not isinstance(families, list):
        failures.append(f"{name}: families must be a list.")
        return
    expected_family_order = [entry.family.value for entry in descriptor.families]
    observed_family_order = [
        family.get("family") for family in families if isinstance(family, dict)
    ]
    if observed_family_order != expected_family_order:
        failures.append(f"{name}: family order must match the plugin descriptor.")
    if len(families) != len(descriptor.families):
        failures.append(f"{name}: families length must match family_count.")

    descriptor_entries = {entry.family.value: entry for entry in descriptor.families}
    for index, family in enumerate(families):
        if not isinstance(family, dict):
            failures.append(f"{name}.family[{index}]: entry must be an object.")
            continue
        family_name = family.get("family")
        if not isinstance(family_name, str):
            failures.append(f"{name}.family[{index}]: family must be a string.")
            continue
        if family_name in seen_families:
            failures.append(f"{family_name}: duplicate family plugin binding.")
        seen_families.append(family_name)
        descriptor_entry = descriptor_entries.get(family_name)
        if descriptor_entry is None:
            failures.append(f"{family_name}: family is not declared by {name}.")
            continue
        _verify_family_entry(
            family,
            descriptor_entry,
            name,
            failures,
            registry=registry,
        )


def _verify_family_entry(
    family: dict[str, Any],
    descriptor_entry: FamilyPluginEntry,
    plugin_name: str,
    failures: list[str],
    *,
    registry: FamilyRegistry,
) -> None:
    family_name = descriptor_entry.family.value
    adapter = registry.get(descriptor_entry.family)
    expected_adapter_class = _class_path(adapter)

    if descriptor_entry.adapter_class != expected_adapter_class:
        failures.append(
            f"{family_name}: plugin descriptor adapter_class must be "
            f"{expected_adapter_class}."
        )
    if descriptor_entry.support_level != adapter.support_level:
        failures.append(f"{family_name}: plugin descriptor support_level drifted.")

    if family.get("adapter_class") != descriptor_entry.adapter_class:
        failures.append(
            f"{family_name}: adapter_class must match the plugin descriptor."
        )
    else:
        _verify_import_resolves_to(
            family["adapter_class"],
            adapter.__class__,
            f"{family_name}: adapter_class",
            failures,
        )

    if family.get("support_level") != descriptor_entry.support_level:
        failures.append(
            f"{family_name}: support_level must match the plugin descriptor."
        )
    if family.get("applicability_validator") != (
        descriptor_entry.applicability_validator
    ):
        failures.append(
            f"{family_name}: applicability_validator must match the plugin "
            "descriptor."
        )

    validator_path = family.get("applicability_validator")
    if isinstance(validator_path, str):
        imported_validator = _import_object_or_failure(
            validator_path,
            f"{family_name}: applicability_validator",
            failures,
        )
        if imported_validator is not None and not callable(imported_validator):
            failures.append(f"{family_name}: applicability_validator is not callable.")
        if plugin_name != LATTICE_PLUGIN_NAME:
            if ".families.lattice." in validator_path:
                failures.append(
                    f"{family_name}: non-lattice plugin must not use lattice "
                    "validator."
                )
            expected_prefix = f"agades_pqc_gym.families.{plugin_name}."
            if not validator_path.startswith(expected_prefix):
                failures.append(
                    f"{family_name}: applicability_validator must live under "
                    f"{expected_prefix}."
                )
    else:
        failures.append(f"{family_name}: applicability_validator must be a string.")

    if family.get("runtime_registered") is not True:
        failures.append(f"{family_name}: runtime_registered must be true.")
    if family.get("review_required_before_claims") is not True:
        failures.append(f"{family_name}: review_required_before_claims must be true.")
    if (
        descriptor_entry.family in {TargetFamily.NTRU, TargetFamily.SIS}
        and family.get("support_level") != "schema_only"
    ):
        failures.append(f"{family_name}: schema-only families must stay schema_only.")


def _verify_implementation_modules(
    plugin: dict[str, Any],
    plugin_name: str,
    failures: list[str],
    *,
    root: Path,
) -> None:
    expected_modules = _implementation_modules(plugin_name, root=root)
    expected_digests = _implementation_module_digests(expected_modules, root=root)
    expected_imports = [_source_path_to_module(path) for path in expected_modules]
    modules = plugin.get("implementation_modules")
    digests = plugin.get("implementation_module_digests")
    imports = plugin.get("implementation_module_imports")
    if modules != expected_modules:
        failures.append(
            f"{plugin_name}: implementation_modules must match discovered modules."
        )
        modules = []
    if digests != expected_digests:
        failures.append(
            f"{plugin_name}: implementation_module_digests must match discovered "
            "module SHA-256 digests."
        )
        digests = {}
    if imports != expected_imports:
        failures.append(
            f"{plugin_name}: implementation_module_imports must match "
            "implementation_modules."
        )
        imports = []
    if plugin.get("implementation_module_count") != len(expected_modules):
        failures.append(
            f"{plugin_name}: implementation_module_count is inconsistent."
        )
    if plugin.get("implementation_module_digest_count") != len(expected_digests):
        failures.append(
            f"{plugin_name}: implementation_module_digest_count is inconsistent."
        )
    if plugin.get("implementation_module_import_count") != len(expected_imports):
        failures.append(
            f"{plugin_name}: implementation_module_import_count is inconsistent."
        )
    if isinstance(imports, list):
        import_failures = _run_module_import_probe(
            root,
            [module_path for module_path in imports if isinstance(module_path, str)],
        )
        failures.extend(
            f"{plugin_name}: implementation module {failure}"
            for failure in import_failures
        )


def _summary(plugins: list[dict[str, Any]]) -> dict[str, Any]:
    families = [
        family
        for plugin in plugins
        if isinstance(plugin.get("families"), list)
        for family in plugin["families"]
        if isinstance(family, dict)
    ]
    return {
        "family_count": len(families),
        "implemented": sorted(
            family["family"]
            for family in families
            if isinstance(family.get("family"), str)
            and family.get("support_level") == "implemented"
        ),
        "implementation_module_count": sum(
            _int_or_zero(plugin.get("implementation_module_count"))
            for plugin in plugins
        ),
        "implementation_module_digest_count": sum(
            _int_or_zero(plugin.get("implementation_module_digest_count"))
            for plugin in plugins
        ),
        "implementation_module_import_count": sum(
            _int_or_zero(plugin.get("implementation_module_import_count"))
            for plugin in plugins
        ),
        "lattice_plugin_families": [
            family["family"]
            for plugin in plugins
            if plugin.get("plugin") == LATTICE_PLUGIN_NAME
            and isinstance(plugin.get("families"), list)
            for family in plugin["families"]
            if isinstance(family, dict) and isinstance(family.get("family"), str)
        ],
        "non_lattice_plugin_count": sum(
            1
            for plugin in plugins
            if isinstance(plugin.get("plugin"), str)
            and plugin["plugin"] != LATTICE_PLUGIN_NAME
        ),
        "plugin_count": len(
            {
                plugin["plugin"]
                for plugin in plugins
                if isinstance(plugin.get("plugin"), str)
            }
        ),
        "runtime_adapter_entries": sum(
            1 for family in families if family.get("runtime_registered") is True
        ),
        "schema_only": sorted(
            family["family"]
            for family in families
            if isinstance(family.get("family"), str)
            and family.get("support_level") == "schema_only"
        ),
        "toy_evaluators": sorted(
            family["family"]
            for family in families
            if isinstance(family.get("family"), str)
            and family.get("support_level") == "toy_evaluator"
        ),
    }


def _lattice_estimator_boundary(plugin_name: str) -> dict[str, Any]:
    if plugin_name == LATTICE_PLUGIN_NAME:
        return {
            "external_estimator_allowed": True,
            "external_estimator_enabled_families": [TargetFamily.LWE.value],
            "scope": "reviewed_lwe_mappings_only",
        }
    return {
        "external_estimator_allowed": False,
        "scope": "not_applicable_non_lattice_plugin",
    }


def _class_path(obj: Any) -> str:
    cls = obj.__class__
    return f"{cls.__module__}.{cls.__qualname__}"


def _implementation_modules(plugin_name: str, *, root: Path) -> list[str]:
    plugin_root = root / "src" / "agades_pqc_gym" / "families" / plugin_name
    return sorted(
        path.relative_to(root).as_posix()
        for path in plugin_root.glob("*.py")
        if path.name != "__init__.py"
    )


def _implementation_module_digests(
    relative_paths: list[str],
    *,
    root: Path,
) -> dict[str, str]:
    return {
        relative_path: hashlib.sha256((root / relative_path).read_bytes()).hexdigest()
        for relative_path in relative_paths
    }


def _source_path_to_module(relative_path: str) -> str:
    return relative_path.removeprefix("src/").removesuffix(".py").replace("/", ".")


def _verify_import_resolves_to(
    path: str,
    expected: Any,
    label: str,
    failures: list[str],
) -> None:
    imported = _import_object_or_failure(path, label, failures)
    if imported is not None and imported is not expected:
        failures.append(f"{label} resolves incorrectly.")


def _import_object_or_failure(
    path: str,
    label: str,
    failures: list[str],
) -> Any | None:
    try:
        return _import_object(path)
    except (AttributeError, ImportError, ValueError) as exc:
        failures.append(f"{label} is not importable: {exc}.")
        return None


def _run_module_import_probe(root: Path, module_names: list[str]) -> list[str]:
    env = os.environ.copy()
    source_root = str((root / "src").resolve())
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        source_root
        if not existing_pythonpath
        else source_root + os.pathsep + existing_pythonpath
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            MODULE_IMPORT_PROBE_SCRIPT,
            json.dumps(module_names, sort_keys=True),
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        failures = json.loads(completed.stdout)
    except json.JSONDecodeError:
        if completed.returncode == 0:
            return []
        output = completed.stderr.strip() or completed.stdout.strip()
        return [f"import probe failed without JSON output: {output}"]
    if not isinstance(failures, list):
        return ["import probe returned an invalid JSON payload."]
    return [str(failure) for failure in failures]


def _import_object(path: str) -> Any:
    module_name, separator, qualname = path.rpartition(".")
    if not separator or not module_name or not qualname:
        raise ValueError("dotted object path must include a module and object")
    module = importlib.import_module(module_name)
    obj: Any = module
    for part in qualname.split("."):
        obj = getattr(obj, part)
    return obj


def _read_manifest(path: Path, failures: list[str]) -> dict[str, Any]:
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


def _int_or_zero(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0
