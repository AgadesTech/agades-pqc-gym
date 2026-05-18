from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from agades_pqc_gym.core.registry import default_family_registry
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.families.plugins import plugin_descriptor_entries_by_family
from agades_pqc_gym.integrations.family_operator_catalog import (
    build_family_operator_catalog,
)
from agades_pqc_gym.integrations.family_plugin_manifest import (
    build_family_plugin_manifest,
)
from agades_pqc_gym.integrations.family_support import build_family_support_matrix

FAMILY_REGISTRY_MANIFEST_SCHEMA = "agades.pqc.family_registry_manifest.v1"
FAMILY_REGISTRY_VERIFICATION_SCHEMA = (
    "agades.pqc.family_registry_manifest_verification.v1"
)
ROOT = Path(__file__).resolve().parents[3]
PROJECT = {
    "cli": "agades-pqc",
    "name": "Agades PQC Gym",
    "package": "agades_pqc_gym",
    "repository": "https://github.com/AgadesTech/agades-pqc-gym",
}
PLUGIN_BINDINGS_BY_FAMILY = plugin_descriptor_entries_by_family()
PLUGIN_BY_FAMILY = {
    family: descriptor.name
    for family, descriptor, _entry in PLUGIN_BINDINGS_BY_FAMILY.values()
}
PLUGIN_DESCRIPTOR_BY_FAMILY = {
    family: descriptor.descriptor_path
    for family, descriptor, _entry in PLUGIN_BINDINGS_BY_FAMILY.values()
}
EXPECTED_FALSE_SAFETY_FLAGS = (
    "lattice_estimator_is_universal_pqc_oracle",
    "non_lattice_entries_use_lattice_estimator",
    "schema_only_families_have_runtime_estimators",
    "security_claim",
    "unsupported_families_return_fake_estimates",
)
LATTICE_FAMILIES = {
    TargetFamily.LWE.value,
    TargetFamily.MLWE.value,
    TargetFamily.NTRU.value,
    TargetFamily.SIS.value,
}


def build_family_registry_manifest(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or ROOT).resolve()
    registry = default_family_registry()
    support_by_family = _families_by_name(
        build_family_support_matrix(root=project_root)
    )
    catalog_by_family = _families_by_name(
        build_family_operator_catalog(root=project_root)
    )

    families = []
    for family in TargetFamily:
        adapter = registry.get(family)
        support_entry = support_by_family[family.value]
        catalog_entry = catalog_by_family[family.value]
        _target_family, plugin_descriptor, plugin_entry = (
            PLUGIN_BINDINGS_BY_FAMILY[family]
        )
        families.append(
            {
                "family": family.value,
                "plugin": plugin_descriptor.name,
                "plugin_descriptor": plugin_descriptor.descriptor_path,
                "adapter_class": _class_path(adapter),
                "adapter_family": adapter.family.value,
                "support_level": adapter.support_level,
                "runtime_registered": True,
                "runtime_operator_count": len(adapter.supported_operators()),
                "support_matrix_support_level": support_entry["support_level"],
                "operator_catalog_support_level": catalog_entry["support_level"],
                "operator_catalog_entries": catalog_entry["operator_entry_count"],
                "operator_review_boundary": _operator_review_boundary(
                    adapter=adapter,
                    catalog_entry=catalog_entry,
                ),
                "default_estimator": support_entry["default_estimator"],
                "optional_estimators": support_entry["optional_estimators"],
                "applicability_validator": plugin_entry.applicability_validator,
                "lattice_estimator_boundary": _lattice_estimator_boundary(
                    family.value
                ),
                "review_required_before_claims": True,
            }
        )

    summary = _summary(families)
    plugin_manifest_alignment = _plugin_manifest_alignment(
        project_root,
        registry_summary=summary,
    )

    return {
        "schema_version": FAMILY_REGISTRY_MANIFEST_SCHEMA,
        "project": PROJECT,
        "summary": summary,
        "plugin_manifest_alignment": plugin_manifest_alignment,
        "families": families,
        "safety": {
            "lattice_estimator_is_universal_pqc_oracle": False,
            "non_lattice_entries_use_lattice_estimator": False,
            "schema_only_families_have_runtime_estimators": False,
            "security_claim": False,
            "unsupported_families_return_fake_estimates": False,
        },
        "release_gates": [
            "uv run pytest tests/test_family_registry_manifest.py -q",
            "uv run agades-pqc family-registry-manifest --out "
            "docs/family_registry_manifest.json",
            "uv run agades-pqc family-registry-manifest-verify --manifest "
            "docs/family_registry_manifest.json",
            "uv run agades-pqc family-support-verify --matrix "
            "docs/family_support_matrix.json",
            "uv run agades-pqc family-operator-catalog-verify --catalog "
            "docs/family_operator_catalog.json",
            "uv run agades-pqc lattice-estimator-manifest-verify --manifest "
            "docs/lattice_estimator_manifest.json",
            "uv run agades-pqc ecosystem-smoke-verify --report "
            "reports/ecosystem_smoke.json",
            "uv run agades-pqc release-audit --out public/release_audit.json",
        ],
    }


def write_family_registry_manifest(
    out: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    manifest = build_family_registry_manifest(root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_family_registry_manifest(
    path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    manifest = _read_manifest(path, failures)
    project_root = (root or ROOT).resolve()

    if manifest.get("schema_version") != FAMILY_REGISTRY_MANIFEST_SCHEMA:
        failures.append(
            f"manifest: schema_version must be {FAMILY_REGISTRY_MANIFEST_SCHEMA}."
        )

    if manifest.get("project") != PROJECT:
        failures.append("manifest: project metadata is not the Agades PQC Gym project.")

    _verify_safety(manifest, failures)
    families = manifest.get("families")
    if not isinstance(families, list):
        failures.append("manifest: families must be a list.")
        families = []

    summary = _verify_family_entries(families, failures, root=project_root)
    expected_summary = _summary(
        [family for family in families if isinstance(family, dict)]
    )
    if manifest.get("summary") != expected_summary:
        failures.append("manifest: summary is inconsistent with families.")
    alignment = _verify_plugin_manifest_alignment(
        manifest.get("plugin_manifest_alignment"),
        registry_summary=expected_summary,
        root=project_root,
        failures=failures,
    )
    summary.update(_plugin_manifest_alignment_summary(alignment))
    if not failures and manifest != build_family_registry_manifest(root=project_root):
        failures.append(
            "manifest: contents are not synchronized with the current runtime "
            "family registry manifest."
        )
    summary["failure_count"] = len(failures)

    return {
        "schema_version": FAMILY_REGISTRY_VERIFICATION_SCHEMA,
        "manifest_path": str(path),
        "accepted": not failures,
        "summary": summary,
        "failures": failures,
    }


def _verify_safety(manifest: dict[str, Any], failures: list[str]) -> None:
    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        failures.append("manifest: safety must be an object.")
        return
    for flag in EXPECTED_FALSE_SAFETY_FLAGS:
        if safety.get(flag) is not False:
            failures.append(f"manifest: safety.{flag} must be false.")


def _verify_family_entries(
    families: list[Any],
    failures: list[str],
    *,
    root: Path,
) -> dict[str, Any]:
    registry = default_family_registry()
    support_by_family = _families_by_name(build_family_support_matrix(root=root))
    catalog_by_family = _families_by_name(build_family_operator_catalog(root=root))
    by_family: dict[str, dict[str, Any]] = {}

    for index, entry in enumerate(families):
        if not isinstance(entry, dict):
            failures.append(f"family[{index}]: family entry must be an object.")
            continue
        family = entry.get("family")
        if not isinstance(family, str) or not family:
            failures.append(f"family[{index}]: family must be a non-empty string.")
            continue
        if family in by_family:
            failures.append(f"{family}: duplicate family registry entry.")
            continue
        by_family[family] = entry

    expected_order = [family.value for family in TargetFamily]
    observed_order = list(by_family)
    if observed_order != expected_order:
        failures.append("manifest: family order must follow TargetFamily declaration.")

    expected_families = set(expected_order)
    observed_families = set(by_family)
    for missing in sorted(expected_families - observed_families):
        failures.append(f"{missing}: missing family registry entry.")
    for unexpected in sorted(observed_families - expected_families):
        failures.append(f"{unexpected}: unexpected family registry entry.")

    for family, entry in by_family.items():
        if family not in expected_families:
            continue
        target_family = TargetFamily(family)
        adapter = registry.get(target_family)
        support_entry = support_by_family[family]
        catalog_entry = catalog_by_family[family]
        _verify_family_entry(
            entry,
            family=family,
            adapter=adapter,
            support_entry=support_entry,
            catalog_entry=catalog_entry,
            failures=failures,
        )

    return _summary(list(by_family.values()))


def _verify_family_entry(
    entry: dict[str, Any],
    *,
    family: str,
    adapter: Any,
    support_entry: dict[str, Any],
    catalog_entry: dict[str, Any],
    failures: list[str],
) -> None:
    target_family = TargetFamily(family)
    _binding_family, descriptor, plugin_entry = (
        PLUGIN_BINDINGS_BY_FAMILY[target_family]
    )
    expected_plugin = PLUGIN_BY_FAMILY[target_family]
    if entry.get("plugin") != expected_plugin:
        failures.append(f"{family}: plugin must be {expected_plugin}.")

    expected_descriptor_path = PLUGIN_DESCRIPTOR_BY_FAMILY[target_family]
    plugin_descriptor = entry.get("plugin_descriptor")
    if plugin_descriptor != expected_descriptor_path:
        failures.append(
            f"{family}: plugin_descriptor must be {expected_descriptor_path}."
        )
    else:
        try:
            imported_descriptor = _import_object(plugin_descriptor)
        except (AttributeError, ImportError, ValueError) as exc:
            failures.append(f"{family}: plugin_descriptor is not importable: {exc}.")
        else:
            if imported_descriptor is not descriptor:
                failures.append(f"{family}: plugin_descriptor resolves incorrectly.")

    expected_class = _class_path(adapter)
    if plugin_entry.adapter_class != expected_class:
        failures.append(
            f"{family}: plugin descriptor adapter_class must be {expected_class}."
        )
    if plugin_entry.support_level != adapter.support_level:
        failures.append(
            f"{family}: plugin descriptor support_level must match runtime."
        )
    if plugin_entry.applicability_validator != catalog_entry["applicability_validator"]:
        failures.append(
            f"{family}: plugin descriptor validator must match the catalog."
        )

    adapter_class = entry.get("adapter_class")
    if adapter_class != expected_class:
        failures.append(f"{family}: adapter_class must be {expected_class}.")
    else:
        try:
            imported_class = _import_object(adapter_class)
        except (AttributeError, ImportError, ValueError) as exc:
            failures.append(f"{family}: adapter_class is not importable: {exc}.")
        else:
            if imported_class is not adapter.__class__:
                failures.append(f"{family}: adapter_class resolves incorrectly.")

    if entry.get("adapter_family") != family:
        failures.append(f"{family}: adapter_family must match family.")
    if entry.get("support_level") != adapter.support_level:
        failures.append(f"{family}: support_level must match the runtime adapter.")
    if entry.get("runtime_registered") is not True:
        failures.append(f"{family}: runtime_registered must be true.")
    if entry.get("runtime_operator_count") != len(adapter.supported_operators()):
        failures.append(f"{family}: runtime_operator_count is inconsistent.")
    if entry.get("support_matrix_support_level") != support_entry["support_level"]:
        failures.append(
            f"{family}: support_matrix_support_level must match the support matrix."
        )
    if entry.get("operator_catalog_support_level") != catalog_entry["support_level"]:
        failures.append(
            f"{family}: operator_catalog_support_level must match the catalog."
        )
    if entry.get("operator_catalog_entries") != catalog_entry["operator_entry_count"]:
        failures.append(f"{family}: operator_catalog_entries is inconsistent.")
    expected_operator_boundary = _operator_review_boundary(
        adapter=adapter,
        catalog_entry=catalog_entry,
    )
    operator_boundary = entry.get("operator_review_boundary")
    if not isinstance(operator_boundary, dict):
        failures.append(f"{family}: operator_review_boundary must be an object.")
    elif operator_boundary != expected_operator_boundary:
        _verify_operator_boundary_fields(
            family=family,
            observed=operator_boundary,
            expected=expected_operator_boundary,
            failures=failures,
        )
    if entry.get("default_estimator") != support_entry["default_estimator"]:
        failures.append(
            f"{family}: default_estimator must match the family support matrix."
        )
    if entry.get("optional_estimators") != support_entry["optional_estimators"]:
        failures.append(
            f"{family}: optional_estimators must match the family support matrix."
        )
    if entry.get("applicability_validator") != plugin_entry.applicability_validator:
        failures.append(
            f"{family}: applicability_validator must match the plugin descriptor."
        )
    if entry.get("applicability_validator") != catalog_entry["applicability_validator"]:
        failures.append(f"{family}: applicability_validator must match the catalog.")
    _verify_applicability_validator(entry, family, failures)
    if entry.get("review_required_before_claims") is not True:
        failures.append(f"{family}: review_required_before_claims must be true.")

    _verify_lattice_estimator_boundary(entry, family, failures)
    _verify_support_boundaries(entry, family, failures)


def _verify_lattice_estimator_boundary(
    entry: dict[str, Any],
    family: str,
    failures: list[str],
) -> None:
    boundary = entry.get("lattice_estimator_boundary")
    if not isinstance(boundary, dict):
        failures.append(f"{family}: lattice_estimator_boundary must be an object.")
        return

    expected_boundary = _lattice_estimator_boundary(family)
    if boundary.get("scope") != expected_boundary["scope"]:
        failures.append(f"{family}: lattice_estimator_boundary.scope is incorrect.")

    external_allowed = boundary.get("external_estimator_allowed")
    if external_allowed != expected_boundary["external_estimator_allowed"]:
        failures.append(
            f"{family}: lattice_estimator_boundary.external_estimator_allowed "
            "is incorrect."
        )
    if family != TargetFamily.LWE.value and external_allowed is True:
        failures.append(
            f"{family}: only LWE may enable the external Lattice Estimator boundary."
        )

    if family not in LATTICE_FAMILIES and _entry_names_lattice_estimator(entry):
        failures.append(
            f"{family}: non-lattice registry entries must not name lattice-estimator."
        )


def _verify_support_boundaries(
    entry: dict[str, Any],
    family: str,
    failures: list[str],
) -> None:
    support_level = entry.get("support_level")
    if family in {TargetFamily.LWE.value, TargetFamily.MLWE.value}:
        if support_level != "implemented":
            failures.append(f"{family}: LWE and MLWE registry entries are implemented.")
    elif family in {TargetFamily.NTRU.value, TargetFamily.SIS.value}:
        if support_level != "schema_only":
            failures.append(f"{family}: NTRU and SIS must remain schema_only.")
        if entry.get("runtime_operator_count") != 0:
            failures.append(f"{family}: schema-only entries must expose no operators.")
        if entry.get("default_estimator") is not None:
            failures.append(
                f"{family}: schema-only entries must not name an estimator."
            )
    elif support_level != "toy_evaluator":
        failures.append(f"{family}: non-lattice entries must remain toy_evaluator.")


def _entry_names_lattice_estimator(entry: dict[str, Any]) -> bool:
    names = [entry.get("default_estimator")]
    optional = entry.get("optional_estimators")
    if isinstance(optional, list):
        names.extend(optional)
    return any(name == "lattice-estimator" for name in names)


def _verify_applicability_validator(
    entry: dict[str, Any],
    family: str,
    failures: list[str],
) -> None:
    validator_path = entry.get("applicability_validator")
    if not isinstance(validator_path, str):
        failures.append(f"{family}: applicability_validator must be a string.")
        return
    try:
        validator = _import_object(validator_path)
    except (AttributeError, ImportError, ValueError) as exc:
        failures.append(f"{family}: applicability_validator is not importable: {exc}.")
        return
    if not callable(validator):
        failures.append(f"{family}: applicability_validator is not callable.")
    if family not in LATTICE_FAMILIES and ".families.lattice." in validator_path:
        failures.append(
            f"{family}: non-lattice registry entries must not use lattice validator."
        )


def _summary(families: list[dict[str, Any]]) -> dict[str, Any]:
    validator_paths = [
        validator
        for family in families
        if isinstance((validator := family.get("applicability_validator")), str)
    ]
    non_lattice_validator_paths = {
        validator
        for family in families
        if isinstance((validator := family.get("applicability_validator")), str)
        and family.get("family") not in LATTICE_FAMILIES
    }
    return {
        "applicability_validator_entries": len(validator_paths),
        "distinct_applicability_validators": len(set(validator_paths)),
        "family_count": len(families),
        "implemented": sorted(
            family["family"]
            for family in families
            if isinstance(family.get("family"), str)
            and family.get("support_level") == "implemented"
        ),
        "lattice_estimator_external_enabled": sorted(
            family["family"]
            for family in families
            if isinstance(family.get("family"), str)
            and isinstance(family.get("lattice_estimator_boundary"), dict)
            and family["lattice_estimator_boundary"].get("external_estimator_allowed")
            is True
        ),
        "lattice_validator_families": [
            family["family"]
            for family in families
            if isinstance(family.get("family"), str)
            and isinstance(family.get("applicability_validator"), str)
            and ".families.lattice." in family["applicability_validator"]
        ],
        "non_lattice_applicability_validators": len(non_lattice_validator_paths),
        "plugin_count": len(
            {
                family["plugin"]
                for family in families
                if isinstance(family.get("plugin"), str)
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


def _plugin_manifest_alignment(
    root: Path,
    *,
    registry_summary: dict[str, Any],
) -> dict[str, Any]:
    plugin_manifest = build_family_plugin_manifest(root=root)
    plugin_summary = plugin_manifest["summary"]
    manifest_path = Path("docs/family_plugin_manifest.json")
    return {
        "committed_manifest_synced": _committed_plugin_manifest_synced(
            root / manifest_path,
            plugin_manifest,
        ),
        "family_count": plugin_summary["family_count"],
        "implementation_module_count": plugin_summary[
            "implementation_module_count"
        ],
        "implementation_module_digest_count": plugin_summary[
            "implementation_module_digest_count"
        ],
        "implementation_module_import_count": plugin_summary[
            "implementation_module_import_count"
        ],
        "manifest_path": manifest_path.as_posix(),
        "plugin_count": plugin_summary["plugin_count"],
        "registry_family_count_matches_manifest": (
            registry_summary.get("family_count") == plugin_summary["family_count"]
        ),
        "registry_plugin_count_matches_manifest": (
            registry_summary.get("plugin_count") == plugin_summary["plugin_count"]
        ),
        "registry_runtime_adapter_entries_match_manifest": (
            registry_summary.get("runtime_adapter_entries")
            == plugin_summary["runtime_adapter_entries"]
        ),
        "runtime_adapter_entries": plugin_summary["runtime_adapter_entries"],
    }


def _verify_plugin_manifest_alignment(
    alignment: Any,
    *,
    registry_summary: dict[str, Any],
    root: Path,
    failures: list[str],
) -> dict[str, Any]:
    if not isinstance(alignment, dict):
        failures.append("manifest: plugin_manifest_alignment must be an object.")
        return {}

    expected = _plugin_manifest_alignment(root, registry_summary=registry_summary)
    for field, expected_value in expected.items():
        if alignment.get(field) != expected_value:
            failures.append(
                f"manifest: plugin_manifest_alignment.{field} is inconsistent."
            )
    for field in sorted(set(alignment) - set(expected)):
        failures.append(f"manifest: plugin_manifest_alignment.{field} is unexpected.")
    return alignment


def _plugin_manifest_alignment_summary(
    alignment: dict[str, Any],
) -> dict[str, Any]:
    return {
        "plugin_manifest_family_count": alignment.get("family_count"),
        "plugin_manifest_implementation_module_count": alignment.get(
            "implementation_module_count"
        ),
        "plugin_manifest_implementation_module_digest_count": alignment.get(
            "implementation_module_digest_count"
        ),
        "plugin_manifest_implementation_module_import_count": alignment.get(
            "implementation_module_import_count"
        ),
        "plugin_manifest_plugin_count": alignment.get("plugin_count"),
        "plugin_manifest_runtime_adapter_entries": alignment.get(
            "runtime_adapter_entries"
        ),
        "plugin_manifest_synced": alignment.get("committed_manifest_synced"),
        "registry_family_count_matches_plugin_manifest": alignment.get(
            "registry_family_count_matches_manifest"
        ),
        "registry_plugin_count_matches_plugin_manifest": alignment.get(
            "registry_plugin_count_matches_manifest"
        ),
        "registry_runtime_adapter_entries_match_plugin_manifest": alignment.get(
            "registry_runtime_adapter_entries_match_manifest"
        ),
    }


def _committed_plugin_manifest_synced(
    path: Path,
    expected_manifest: dict[str, Any],
) -> bool:
    expected_text = json.dumps(expected_manifest, indent=2, sort_keys=True) + "\n"
    try:
        return path.read_text(encoding="utf-8") == expected_text
    except FileNotFoundError:
        return False


def _operator_review_boundary(
    *,
    adapter: Any,
    catalog_entry: dict[str, Any],
) -> dict[str, Any]:
    runtime_operator_types = sorted(adapter.supported_operators())
    catalog_operators = [
        operator
        for operator in catalog_entry.get("operators", [])
        if isinstance(operator, dict)
    ]
    catalog_operator_types = sorted(
        {
            operator_type
            for operator in catalog_operators
            if isinstance((operator_type := operator.get("operator_type")), str)
        }
    )
    external_estimator_operator_types = sorted(
        {
            operator["operator_type"]
            for operator in catalog_operators
            if isinstance(operator.get("operator_type"), str)
            and _uses_external_lattice_estimator(operator)
        }
    )

    return {
        "catalog_operator_types": catalog_operator_types,
        "catalog_variant_entries": len(catalog_operators),
        "external_estimator_operator_types": external_estimator_operator_types,
        "runtime_operator_types": runtime_operator_types,
        "runtime_without_catalog_operator_types": sorted(
            set(runtime_operator_types) - set(catalog_operator_types)
        ),
    }


def _uses_external_lattice_estimator(operator: dict[str, Any]) -> bool:
    external = operator.get("optional_external_estimator")
    return isinstance(external, dict) and external.get("name") == "lattice-estimator"


def _verify_operator_boundary_fields(
    *,
    family: str,
    observed: dict[str, Any],
    expected: dict[str, Any],
    failures: list[str],
) -> None:
    for field, expected_value in expected.items():
        if observed.get(field) != expected_value:
            failures.append(
                f"{family}: operator_review_boundary.{field} is inconsistent."
            )
    for field in sorted(set(observed) - set(expected)):
        failures.append(f"{family}: operator_review_boundary.{field} is unexpected.")


def _families_by_name(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["family"]: entry for entry in manifest["families"]}


def _lattice_estimator_boundary(family: str) -> dict[str, Any]:
    if family == TargetFamily.LWE.value:
        return {
            "external_estimator_allowed": True,
            "scope": "reviewed_lwe_mappings_only",
        }
    if family == TargetFamily.MLWE.value:
        return {
            "external_estimator_allowed": False,
            "scope": "family_adapter_warning_gated_no_external_manifest_scope",
        }
    if family in {TargetFamily.NTRU.value, TargetFamily.SIS.value}:
        return {
            "external_estimator_allowed": False,
            "scope": "schema_only_no_estimator",
        }
    return {
        "external_estimator_allowed": False,
        "scope": "not_applicable_non_lattice_family",
    }


def _class_path(obj: Any) -> str:
    cls = obj.__class__
    return f"{cls.__module__}.{cls.__qualname__}"


def _import_object(path: str) -> Any:
    module_name, _, qualname = path.rpartition(".")
    if not module_name or not qualname:
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
