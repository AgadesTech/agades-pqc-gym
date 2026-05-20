# Implementation-Security Toy KAT Reproduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reviewed, bounded public reproduction harness for the existing `IMPLEMENTATION_SECURITY` toy KAT digest surface by verifying one tiny JSON-only public KAT fixture.

**Architecture:** Keep the existing `toy_kat_digest_match` estimator as JSON-only estimator evidence. Add a fixture verifier for explicit public fixtures under `benchmarks/implementation_security_toy_kat/fixtures/`, mirrored as package data for installed verifier use. The adapter should return `instance_solved` only when the fixture is public, no-claim, declares no artifact execution, stays inside the fixture directory, and matches the target/operator shape.

**Tech Stack:** Python 3.12, `hashlib.sha256`, Pydantic, pytest, Typer CLI/public benchmark artifacts.

---

### Task 1: RED Tests For Implementation-Security Reproduction

**Files:**
- Create: `tests/test_implementation_security_kat_fixture.py`
- Modify: `tests/test_implementation_security_adapter.py`

- [x] **Step 1: Add a fixture verifier contract test**

Add a test that imports `verify_toy_kat_fixture`, loads `benchmarks/implementation_security_toy_kat/fixtures/toy_mlkem_kat_digest_fixture.json`, and asserts it verifies the public SHA-256 digest `42b4b222b2c3dee6b453babe2ea401606b24032174d9ed734d2de31c0097cba8`, reports `suite == "toy_mlkem_kat"`, `vector_count == 2`, `artifact_execution is False`, and `security_claim is False`.

- [x] **Step 2: Add an adapter reproduction test**

Add a test that builds the existing toy KAT plan with `require_reproducibility_on_downscaled_instances=True` and `downscaled_reproduction_fixture="benchmarks/implementation_security_toy_kat/fixtures/toy_mlkem_kat_digest_fixture.json"`, then asserts cascade metrics return `reproduction_status == "instance_solved"` and `reproducibility_score == 0.4`.

- [x] **Step 3: Add fixture-required, scope, and traversal tests**

Add tests that reject reproduction requests without a fixture, reject fixture paths outside `benchmarks/implementation_security_toy_kat/fixtures/`, and reject `..` path traversal.

- [x] **Step 4: Run RED tests**

Run:

```bash
PYTHONPATH=src uv run pytest tests/test_implementation_security_kat_fixture.py tests/test_implementation_security_adapter.py::test_implementation_security_toy_kat_reproduction_verifies_public_fixture tests/test_implementation_security_adapter.py::test_implementation_security_toy_kat_reproduction_requires_fixture tests/test_implementation_security_adapter.py::test_implementation_security_toy_kat_reproduction_fixture_scope tests/test_implementation_security_adapter.py::test_implementation_security_toy_kat_reproduction_fixture_traversal -q
```

Expected: FAIL because the fixture verifier module, fixture, package data, and adapter reproduction path do not exist yet.

### Task 2: Implement JSON-Only KAT Fixture Verifier

**Files:**
- Create: `src/agades_pqc_gym/families/implementation_security/kat_fixture.py`
- Create: `benchmarks/implementation_security_toy_kat/fixtures/toy_mlkem_kat_digest_fixture.json`
- Create: `src/agades_pqc_gym/families/implementation_security/fixtures/toy_mlkem_kat_digest_fixture.json`
- Modify: `pyproject.toml`

- [x] **Step 1: Add schema-versioned fixture and result models**

Implement a Pydantic fixture schema for `toy_kat_digest_match`, UTF-8 payload bytes bounded by `TOY_KAT_MAX_PAYLOAD_BYTES`, `vector_count` bounded by `TOY_KAT_MAX_VECTOR_COUNT`, `public=true`, `security_claim=false`, and `artifact_execution=false`.

- [x] **Step 2: Add deterministic digest verification**

Recompute `hashlib.sha256(payload.encode("utf-8")).hexdigest()`, require it to match `expected_sha256`, and return a typed result model with payload bytes, digest, suite, model, vector count, public/no-claim, and no-execution flags.

- [x] **Step 3: Mirror fixture as package data**

Add the same fixture under `src/agades_pqc_gym/families/implementation_security/fixtures/` and include `families/implementation_security/fixtures/*.json` in `pyproject.toml` package data.

- [x] **Step 4: Verify fixture tests pass**

Run:

```bash
PYTHONPATH=src uv run pytest tests/test_implementation_security_kat_fixture.py -q
```

Expected: PASS.

### Task 3: Wire Adapter Reproduction

**Files:**
- Modify: `src/agades_pqc_gym/families/implementation_security/adapter.py`
- Modify: `docs/FAMILY_ADAPTERS.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Replace blanket reproduction rejection for explicit public fixtures**

Keep rejecting reproduction requests without a fixture. For explicit relative direct JSON fixtures under `benchmarks/implementation_security_toy_kat/fixtures/`, call the fixture verifier.

- [x] **Step 2: Return `instance_solved` only for matching public no-claim fixtures**

Validate target name, suite, model, vector count, expected digest, public, `security_claim=false`, and `artifact_execution=false` before returning a positive reproduction result.

- [x] **Step 3: Verify adapter tests pass**

Run:

```bash
PYTHONPATH=src uv run pytest tests/test_implementation_security_adapter.py tests/test_implementation_security_kat_fixture.py -q
```

Expected: PASS.

### Task 4: Regenerate Public Artifacts And Verify

**Files:**
- Modify generated public bundle/checksum artifacts for `implementation_security_toy_kat_v0`
- Modify generated HF/publication/family/release manifests as needed

- [x] **Step 1: Add benchmark plan and regenerate implementation-security bundle**

Run:

```bash
PYTHONPATH=src uv run agades-pqc benchmark benchmarks/implementation_security_toy_kat --out runs/implementation_security_toy_kat.jsonl
PYTHONPATH=src uv run agades-pqc public-bundle runs/implementation_security_toy_kat.jsonl --out examples/public_runs/implementation_security_toy_kat_v0
```

- [x] **Step 2: Regenerate OSS manifests**

Run the checked-in manifest generation commands for family support, Hugging Face dataset, public benchmark manifest, publication manifest, Prime manifest, NVIDIA manifest, and release audit.

- [x] **Step 3: Verify**

Run:

```bash
PYTHONPATH=src uv run pytest -q
PYTHONPATH=src uv run ruff check .
PYTHONPATH=src uv run agades-pqc public-benchmark-verify --manifest docs/public_benchmark_manifest.json
PYTHONPATH=src uv run agades-pqc release-audit --out public/release_audit.json
git diff --check
uv build
(cd prime_intellect/verifiers_environment && uv build)
```
