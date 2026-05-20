# Prime Publication Handoff Manifest

## Goal

Add a checked, verifiable Prime Intellect publication handoff manifest that records
the local Prime package readiness, review/credential boundaries, local artifacts,
and release gates without claiming that the package has been published to Prime
Hub.

## Constraints

- Keep `agades-pqc-gym` / `agades_pqc_gym` naming.
- Do not remove the existing non-blocking Prime Hub publication warning.
- Do not claim external publication, credentials, GPU work, security results, or
  private candidate publication.
- Keep the manifest generated from existing checked artifacts.

## TDD

1. Add `tests/test_prime_publication_handoff.py` importing a new integration
   module and asserting the manifest contract, verifier behavior, CLI commands,
   and committed artifact sync.
2. Run the targeted test and confirm it fails because the module is missing.
3. Implement the integration module and CLI.
4. Regenerate `docs/prime_publication_handoff.json`.
5. Wire the artifact into publication/source/release surfaces and regenerate
   derived manifests.
6. Run targeted and full verification.

## Files

- Create: `src/agades_pqc_gym/integrations/prime_publication_handoff.py`
- Create: `tests/test_prime_publication_handoff.py`
- Create: `docs/prime_publication_handoff.json`
- Modify: `src/agades_pqc_gym/cli.py`
- Modify: `src/agades_pqc_gym/integrations/release_audit.py`
- Modify: `src/agades_pqc_gym/integrations/publication_manifest.py`
- Modify: `src/agades_pqc_gym/integrations/source_catalog.py`
- Modify: `src/agades_pqc_gym/integrations/release_status.py`
- Modify: `.github/workflows/ci.yml`
- Update generated docs under `docs/`, `public/`, `hf/`, and `nvidia/` only when
  their deterministic generators require it.
