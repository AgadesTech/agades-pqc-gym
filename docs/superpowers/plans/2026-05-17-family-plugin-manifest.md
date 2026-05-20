# Family Plugin Manifest

## Objective

Publish a deterministic, reviewable contract for the multi-family plugin layer.
The manifest must prove that `lattice` is the first implemented plugin surface,
not the boundary of Agades PQC Gym, and that every family owns its own adapter
and applicability validator metadata.

## Constraints

- Keep project naming on `agades-pqc-gym`, `agades_pqc_gym`, and Agades PQC Gym.
- Do not add crypto claims, private traces, or credential-dependent publishing.
- Keep the Lattice Estimator boundary explicit: reviewed LWE mappings only, not
  a universal PQC oracle.
- Use tests first for the manifest schema, verifier, CLI, publication surface,
  and release-audit gate.

## Implementation Plan

1. Add failing tests for `docs/family_plugin_manifest.json`:
   - schema/project metadata;
   - plugin order and family coverage from `FamilyPluginDescriptor`;
   - importability of descriptor, adapter, and validator paths;
   - non-lattice plugins not using lattice validators;
   - CLI writer and verifier behavior;
   - checked-in artifact synchronization.
2. Implement `agades_pqc_gym.integrations.family_plugin_manifest`:
   - build from `family_plugin_descriptors()` and the runtime registry;
   - expose `write_family_plugin_manifest()` and
     `verify_family_plugin_manifest()`;
   - validate summary, coverage, import targets, safety flags, and descriptor
     drift.
3. Add CLI commands:
   - `agades-pqc family-plugin-manifest --out docs/family_plugin_manifest.json`;
   - `agades-pqc family-plugin-manifest-verify --manifest docs/family_plugin_manifest.json`.
4. Add the artifact to public release surfaces:
   - GitHub publication manifest artifact paths;
   - release gates;
   - release-audit blocking check;
   - GitHub Actions artifact drift check.
5. Regenerate checked artifacts and run targeted then full verification.

## Verification

- `uv run pytest tests/test_family_plugin_manifest.py -q`
- `uv run pytest tests/test_publication_manifest.py tests/test_release_audit.py -q`
- `uv run pytest -q`
- `uv run ruff check .`
- `git diff --check`
- `uv build`
- `uv build prime_intellect/verifiers_environment`
- `uv run agades-pqc family-plugin-manifest-verify --manifest docs/family_plugin_manifest.json`
- `uv run agades-pqc publication-manifest-verify --manifest docs/publication_manifest.json`
- `uv run agades-pqc release-audit --out public/release_audit.json`
