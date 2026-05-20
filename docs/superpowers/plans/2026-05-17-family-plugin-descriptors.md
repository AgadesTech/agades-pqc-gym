# Family Plugin Descriptors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every PQC family plugin expose an importable machine-readable descriptor, then derive registry/catalog plugin boundaries from those descriptors.

**Architecture:** Add a small family-plugin descriptor model plus one `plugin.py` module per family plugin. The descriptor declares owned `TargetFamily` values, adapter class paths, support levels, and applicability validator paths; integration manifests consume those descriptors instead of keeping separate hard-coded plugin/validator maps.

**Tech Stack:** Python 3.12, dataclasses, existing `TargetFamily`, pytest, Typer artifact generators.

---

### Task 1: Descriptor Contract RED Tests

**Files:**
- Create: `tests/test_family_plugins.py`
- Modify: `tests/test_family_registry_manifest.py`
- Modify: `tests/test_family_operator_catalog.py`

- [x] **Step 1: Add descriptor coverage tests**

Create `tests/test_family_plugins.py` with tests that import `family_plugin_descriptors()` and assert:

```python
from __future__ import annotations

import importlib

from agades_pqc_gym.core.registry import default_family_registry
from agades_pqc_gym.core.target import TargetFamily
from agades_pqc_gym.families.plugins import (
    family_plugin_descriptors,
    plugin_descriptor_entries_by_family,
)
from agades_pqc_gym.integrations.family_operator_catalog import (
    build_family_operator_catalog,
)


EXPECTED_PLUGINS = {
    "lattice": ["LWE", "MLWE", "NTRU", "SIS"],
    "code_based": ["CODE_BASED"],
    "multivariate": ["MULTIVARIATE"],
    "hash_based": ["HASH_BASED"],
    "isogeny_historical": ["ISOGENY_HISTORICAL"],
    "implementation_security": ["IMPLEMENTATION_SECURITY"],
}


def test_family_plugin_descriptors_cover_declared_target_families_once() -> None:
    descriptors = family_plugin_descriptors()

    assert {descriptor.name: [entry.family.value for entry in descriptor.families] for descriptor in descriptors} == EXPECTED_PLUGINS
    assert sorted(entry.family for descriptor in descriptors for entry in descriptor.families) == sorted(TargetFamily)


def test_family_plugin_descriptor_paths_are_importable() -> None:
    for descriptor in family_plugin_descriptors():
        module_name, object_name = descriptor.descriptor_path.rsplit(".", 1)
        module = importlib.import_module(module_name)

        assert getattr(module, object_name) is descriptor


def test_family_plugin_entries_match_runtime_registry_and_catalog() -> None:
    registry = default_family_registry()
    catalog_by_family = {
        family["family"]: family
        for family in build_family_operator_catalog()["families"]
    }

    for family, descriptor, entry in plugin_descriptor_entries_by_family().values():
        adapter = registry.get(family)
        catalog_entry = catalog_by_family[family.value]

        assert entry.adapter_class == f"{adapter.__class__.__module__}.{adapter.__class__.__qualname__}"
        assert entry.support_level == adapter.support_level
        assert entry.applicability_validator == catalog_entry["applicability_validator"]
        assert descriptor.name == catalog_entry["plugin"]
```

- [x] **Step 2: Require descriptor paths in registry manifest tests**

Update `tests/test_family_registry_manifest.py` so every family entry has `plugin_descriptor` pointing to:

```python
{
    "LWE": "agades_pqc_gym.families.lattice.plugin.PLUGIN_DESCRIPTOR",
    "MLWE": "agades_pqc_gym.families.lattice.plugin.PLUGIN_DESCRIPTOR",
    "NTRU": "agades_pqc_gym.families.lattice.plugin.PLUGIN_DESCRIPTOR",
    "SIS": "agades_pqc_gym.families.lattice.plugin.PLUGIN_DESCRIPTOR",
    "CODE_BASED": "agades_pqc_gym.families.code_based.plugin.PLUGIN_DESCRIPTOR",
    "MULTIVARIATE": "agades_pqc_gym.families.multivariate.plugin.PLUGIN_DESCRIPTOR",
    "HASH_BASED": "agades_pqc_gym.families.hash_based.plugin.PLUGIN_DESCRIPTOR",
    "ISOGENY_HISTORICAL": "agades_pqc_gym.families.isogeny_historical.plugin.PLUGIN_DESCRIPTOR",
    "IMPLEMENTATION_SECURITY": "agades_pqc_gym.families.implementation_security.plugin.PLUGIN_DESCRIPTOR",
}
```

- [x] **Step 3: Run RED**

Run:

```bash
uv run pytest tests/test_family_plugins.py tests/test_family_registry_manifest.py::test_family_registry_manifest_describes_runtime_registry -q
```

Expected: fail because `agades_pqc_gym.families.plugins` and per-family `plugin.py` modules do not exist yet.

### Task 2: Descriptor Model and Family Plugin Modules

**Files:**
- Create: `src/agades_pqc_gym/core/family_plugin.py`
- Create: `src/agades_pqc_gym/families/plugins.py`
- Create: `src/agades_pqc_gym/families/lattice/plugin.py`
- Create: `src/agades_pqc_gym/families/code_based/plugin.py`
- Create: `src/agades_pqc_gym/families/multivariate/plugin.py`
- Create: `src/agades_pqc_gym/families/hash_based/plugin.py`
- Create: `src/agades_pqc_gym/families/isogeny_historical/plugin.py`
- Create: `src/agades_pqc_gym/families/implementation_security/plugin.py`

- [x] **Step 1: Add immutable descriptor types**

Create `FamilyPluginEntry` and `FamilyPluginDescriptor` dataclasses with
descriptor-level plugin name/path plus entry-level `family`, `adapter_class`,
`support_level`, and `applicability_validator` fields.

- [x] **Step 2: Add per-family plugin modules**

Each family plugin module exports `PLUGIN_DESCRIPTOR` with current adapter/support/validator paths. Lattice owns `LWE`, `MLWE`, `NTRU`, and `SIS`; each non-lattice plugin owns exactly one family.

- [x] **Step 3: Add descriptor registry helpers**

Create `family_plugin_descriptors()` and `plugin_descriptor_entries_by_family()` in `src/agades_pqc_gym/families/plugins.py`. The helper must raise `ValueError` if a `TargetFamily` is missing or registered by more than one plugin.

- [x] **Step 4: Run GREEN for descriptor tests**

Run:

```bash
uv run pytest tests/test_family_plugins.py -q
```

Expected: pass.

### Task 3: Consume Descriptors in Integration Manifests

**Files:**
- Modify: `src/agades_pqc_gym/integrations/family_operator_catalog.py`
- Modify: `src/agades_pqc_gym/integrations/family_registry_manifest.py`
- Regenerate: `docs/family_operator_catalog.json`
- Regenerate: `docs/family_registry_manifest.json`
- Regenerate: `docs/publication_manifest.json`
- Regenerate: `public/release_audit.json`
- Regenerate: `docs/release_status.json`
- Regenerate: `public/publication_preflight.json`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Replace hard-coded plugin/validator maps**

In operator catalog and registry manifest builders, derive plugin name, support level, validator path, and registry `plugin_descriptor` from `plugin_descriptor_entries_by_family()`.

- [x] **Step 2: Verify registry manifest rejects descriptor drift**

Add or update tests so changing `plugin_descriptor`, `plugin`, or `applicability_validator` for one family causes `family-registry-manifest-verify` to fail with a concrete family-specific error.

- [x] **Step 3: Regenerate artifacts**

Run:

```bash
env PYTHONPATH=src uv run agades-pqc family-operator-catalog --out docs/family_operator_catalog.json
env PYTHONPATH=src uv run agades-pqc family-registry-manifest --out docs/family_registry_manifest.json
env PYTHONPATH=src uv run agades-pqc publication-manifest --out docs/publication_manifest.json
env PYTHONPATH=src uv run agades-pqc release-audit --out public/release_audit.json
env PYTHONPATH=src uv run agades-pqc release-status --out docs/release_status.json
env PYTHONPATH=src uv run agades-pqc publication-preflight --out public/publication_preflight.json
```

- [x] **Step 4: Update docs**

Document that family plugins now declare explicit importable descriptors consumed by manifests/catalogs.

### Task 4: Verification, Commit, Push

**Files:**
- Verify all modified files.

- [x] **Step 1: Full verification**

Run:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
uv build
uv build prime_intellect/verifiers_environment
```

- [x] **Step 2: Artifact and naming gates**

Run family/publication/release verifiers, release/runbook audits, and the
checked naming guard:

```bash
env PYTHONPATH=src uv run agades-pqc family-operator-catalog-verify --catalog docs/family_operator_catalog.json
env PYTHONPATH=src uv run agades-pqc family-registry-manifest-verify --manifest docs/family_registry_manifest.json
env PYTHONPATH=src uv run agades-pqc publication-manifest-verify --manifest docs/publication_manifest.json
env PYTHONPATH=src uv run agades-pqc release-status-verify --status docs/release_status.json
env PYTHONPATH=src uv run agades-pqc publication-preflight-verify --preflight public/publication_preflight.json
env PYTHONPATH=src uv run agades-pqc release-audit --out /tmp/agades_release_audit_check.json
env PYTHONPATH=src uv run agades-pqc runbook-audit --brief /path/to/agades_codex_long_running_brief_v3_multifamily.md --context /path/to/contexte-projet-agades.md --out /tmp/agades_runbook_audit_with_inputs.json
env PYTHONPATH=src uv run agades-pqc release-audit --out /tmp/agades_release_audit_name_guard.json
```

Expected: verifiers/audits pass and the naming guard reports no legacy terms.

- [ ] **Step 3: Commit, push, and check CI**

Commit, push `codex/multifamily-architecture`, and verify PR checks.
