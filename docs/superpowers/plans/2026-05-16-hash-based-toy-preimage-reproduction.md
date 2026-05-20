# Hash-Based Toy Preimage Reproduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reviewed, bounded public reproduction harness for the existing `HASH_BASED` toy preimage-bound surface by solving one tiny SHAKE256 preimage fixture.

**Architecture:** Keep the existing toy preimage-bound estimator as estimator evidence. Add a separate fixture solver for explicit public fixtures under `benchmarks/hash_based_toy_bound/fixtures/`, mirrored as package data for installed verifier use. The adapter should return `instance_solved` only when the fixture is public, no-claim, scoped to the fixture directory, and matches the target shape.

**Tech Stack:** Python 3.12, `hashlib.shake_256`, Pydantic, pytest, Typer CLI/public benchmark artifacts.

---

### Task 1: RED Tests For Hash-Based Reproduction

**Files:**
- Create: `tests/test_hash_based_preimage_solver.py`
- Modify: `tests/test_hash_based_adapter.py`

- [x] **Step 1: Add a solver contract test**

Add a test that imports `solve_toy_preimage_fixture`, loads `benchmarks/hash_based_toy_bound/fixtures/toy_hash_preimage_24_fixture.json`, and asserts it recovers the unique public candidate `4242`, reports `candidate_count == 65536`, `digest_hex == "59c55a"`, and keeps `security_claim is False`.

- [x] **Step 2: Add an adapter reproduction test**

Add a test that builds a tiny `SHAKE256` toy hash plan with `require_reproducibility_on_downscaled_instances=True` and `downscaled_reproduction_fixture="benchmarks/hash_based_toy_bound/fixtures/toy_hash_preimage_24_fixture.json"`, then asserts cascade metrics return `reproduction_status == "instance_solved"` and `reproducibility_score == 0.4`.

- [x] **Step 3: Add fixture scope and traversal tests**

Add tests that reject reproduction fixture paths outside `benchmarks/hash_based_toy_bound/fixtures/` and reject `..` path traversal.

- [x] **Step 4: Run RED tests**

Run:

```bash
PYTHONPATH=src uv run pytest tests/test_hash_based_preimage_solver.py tests/test_hash_based_adapter.py::test_hash_based_toy_reproduction_solves_public_preimage_fixture tests/test_hash_based_adapter.py::test_hash_based_toy_reproduction_fixture_must_stay_in_fixture_dir tests/test_hash_based_adapter.py::test_hash_based_toy_reproduction_fixture_rejects_path_traversal -q
```

Expected: FAIL because the solver module, fixture, and adapter reproduction path do not exist yet.

### Task 2: Implement Bounded SHAKE256 Preimage Fixture Solver

**Files:**
- Create: `src/agades_pqc_gym/families/hash_based/preimage_solver.py`
- Create: `benchmarks/hash_based_toy_bound/fixtures/toy_hash_preimage_24_fixture.json`
- Create: `src/agades_pqc_gym/families/hash_based/fixtures/toy_hash_preimage_24_fixture.json`
- Modify: `pyproject.toml`

- [x] **Step 1: Add schema-versioned fixture and solution models**

Implement a Pydantic fixture schema for `SHAKE256`, byte-aligned digest truncation, fixed-width unsigned integer candidate encoding, an explicit bounded candidate range, expected candidate, `public=true`, and `security_claim=false`.

- [x] **Step 2: Add bounded exhaustive solve**

Enumerate `range(max_candidate_exclusive)`, encode each candidate as fixed-width big-endian bytes appended to `message_prefix`, compute `hashlib.shake_256(...).digest(digest_bits // 8).hex()`, require a unique matching candidate, and return a typed solution model.

- [x] **Step 3: Mirror fixture as package data**

Add the same fixture under `src/agades_pqc_gym/families/hash_based/fixtures/` and include `families/hash_based/fixtures/*.json` in `pyproject.toml` package data.

- [x] **Step 4: Verify solver tests pass**

Run:

```bash
PYTHONPATH=src uv run pytest tests/test_hash_based_preimage_solver.py -q
```

Expected: PASS.

### Task 3: Wire Adapter Reproduction

**Files:**
- Modify: `src/agades_pqc_gym/families/hash_based/adapter.py`
- Modify: `docs/FAMILY_ADAPTERS.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Replace blanket reproduction rejection for explicit public fixtures**

Keep rejecting reproduction requests without a fixture. For explicit relative direct JSON fixtures under `benchmarks/hash_based_toy_bound/fixtures/`, call the solver.

- [x] **Step 2: Return `instance_solved` only for matching public no-claim fixtures**

Validate target name, digest bits, hash function, `public`, and `security_claim=false` before returning a positive reproduction result.

- [x] **Step 3: Verify adapter tests pass**

Run:

```bash
PYTHONPATH=src uv run pytest tests/test_hash_based_adapter.py -q
```

Expected: PASS.

### Task 4: Regenerate Public Artifacts And Verify

**Files:**
- Modify generated public bundle/checksum artifacts for `hash_based_toy_bound_v0`
- Modify generated HF/publication/family/release manifests as needed

- [x] **Step 1: Add benchmark plan and regenerate hash-based bundle**

Run:

```bash
PYTHONPATH=src uv run agades-pqc benchmark benchmarks/hash_based_toy_bound --out runs/hash_based_toy_bound.jsonl
PYTHONPATH=src uv run agades-pqc public-bundle runs/hash_based_toy_bound.jsonl --out examples/public_runs/hash_based_toy_bound_v0
```

- [x] **Step 2: Regenerate OSS manifests**

Run the existing checked-in manifest generation commands for family support, Hugging Face dataset, public benchmark manifest, publication manifest, Prime manifest, NVIDIA manifest, and release audit.

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
