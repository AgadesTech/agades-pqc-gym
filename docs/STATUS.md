# Status

## 2026-05-18

Current delta on `codex/multifamily-architecture`:

- Tightened the `runbook-family-agnostic-core` importability gate so all 14
  public core symbols are verified through `agades_pqc_gym.core.<symbol>`,
  not through internal submodule paths. This makes the family-agnostic API
  boundary explicit for downstream OSS users and future family plugins.
- Promoted `FamilyPluginDescriptor`, `FamilyPluginEntry`, `FamilyRegistry`,
  and `default_family_registry` onto the `agades_pqc_gym.core` public API. The
  runbook family-agnostic-core gate now verifies 14/14 public core imports,
  including the plugin-extension and default-registry boundary needed by future
  non-lattice families.
- Promoted `ReportGenerator` and `redact_trace_record` onto the
  `agades_pqc_gym.core` public API. The runbook family-agnostic-core gate now
  verifies those public imports directly, keeping reporting and the
  public/private redaction layer inside the documented family-agnostic surface.
- Added the Prime task-metadata schema to the CI artifact-diff gate. GitHub
  Actions and release audit now require
  `prime_intellect/schemas/task_metadata.schema.json` alongside the other Prime
  verifier schemas after `agades-pqc prime-schemas`, so task metadata contract
  drift cannot pass CI unnoticed.
- Hardened `deepevolve-manifest-verify` against full runtime manifest drift.
  The verifier now rejects a structurally valid but stale
  `docs/deepevolve_research_hooks_manifest.json` when PaperCard or project
  metadata diverges from the generated manifest, keeping the OpenEvolve /
  DeepEvolve research-hook surface review-gated, note-only, and aligned with
  current Agades PQC Gym naming.
- Hardened `benchmark-source-verify` against full runtime contract drift. The
  verifier now rejects a structurally valid but stale
  `docs/benchmark_source_contracts.json` when future-adapter source facts or
  review gates drift without changing summary counts, keeping TAPAS, LWE
  benchmarking, Hugging Face, NIST, Prime, and implementation-security anchors
  tied to the generated contract.
- Hardened `source-catalog-verify` against full runtime catalog drift. The
  verifier now rejects a structurally valid but stale `docs/source_catalog.json`
  when OSS source metadata changes without affecting summary counts, so
  Prime/Hugging Face/NVIDIA-facing source anchors cannot silently lag behind the
  generated catalog.
- Hardened `family-plugin-manifest-verify` against full runtime manifest
  drift. The verifier now rejects a structurally valid but stale
  `docs/family_plugin_manifest.json`, including stale release gates, so the
  plugin extension-boundary evidence cannot lag behind the current runtime
  plugin descriptors and source digests.
- Hardened `family-registry-manifest-verify` against full runtime manifest
  drift. The verifier now rejects a structurally valid but stale
  `docs/family_registry_manifest.json`, including stale release gates, while
  resolving family-support and operator-catalog dependencies from the audited
  root.
- Hardened `family-support-verify` against runtime drift. The verifier now
  rejects a self-consistent but stale `docs/family_support_matrix.json` when
  per-family support entries no longer match the current runtime-generated
  support matrix, keeping Prime/Hugging Face/NVIDIA family-readiness summaries
  anchored to implementation reality.
- Hardened `family-operator-catalog-verify` against runtime drift. The verifier
  now rejects a self-consistent but stale `docs/family_operator_catalog.json`
  when operator entries no longer match the current family-plugin runtime
  catalog, so Prime/Hugging Face/NVIDIA-facing operator evidence cannot lag
  behind implementation changes.
- Propagated the external review gate into
  `public/publication_preflight.json`. The publication go/no-go artifact now
  carries the same `external_review` evidence as release status, including
  `reviewer_summary_synced=true`, and `publication-preflight-verify` rejects
  reviewer-summary drift before any Prime/Hugging Face/NVIDIA publication step.
- Surfaced the external publication reviewer-summary gate in
  `docs/release_status.json`. The short OSS release-status view now includes an
  `external_review` block with blockers, credential/review counts, warning
  evidence, and `reviewer_summary_synced=true`; `release-status-verify` rejects
  reviewer-summary drift before publication preflight or ecosystem smoke.
- Propagated the ecosystem smoke reviewer-summary synchronization proof into
  `public/release_audit.json`. The blocking `ecosystem-smoke-report` check now
  exposes `reviewer_summary_synced=true`, making the external-review summary
  drift gate visible from the top-level release audit.
- Propagated the external reviewer-summary gate into the checked ecosystem
  smoke report. `reports/ecosystem_smoke.json` and
  `ecosystem-smoke-verify` now expose `reviewer_summary_synced=true`, and the
  smoke fails if the external publication review packet summary drifts from
  its underlying Hugging Face, Prime Intellect, NVIDIA, GitHub, and runbook
  evidence.
- Added a persisted, verifier-checked `reviewer_summary` to
  `docs/external_publication_review_packet.json`. The packet now gives
  Hugging Face, Prime Intellect, NVIDIA, and GitHub reviewers a compact
  external-publication readiness summary while
  `external-publication-review-packet-verify` rejects summary drift and release
  audit exposes `reviewer_summary_synced=true`.
- Promoted the OpenEvolve private-loop config into a checked CI artifact.
  `agades-pqc openevolve-config` now regenerates
  `examples/openevolve/config.yaml`, `openevolve-config-verify` rejects stale
  or unsafe template drift, and release audit consumes that verifier instead of
  carrying duplicated config-check logic.
- Promoted OpenEvolve evaluator smoke into a checked public report.
  `agades-pqc openevolve-smoke` now writes `reports/openevolve_smoke.json`,
  `openevolve-smoke-verify` rejects stale or unsafe reports, CI regenerates it
  before release convergence, and release audit consumes the checked report
  instead of carrying hidden OpenEvolve smoke logic.
- Updated the public README release workflow so the OSS-facing quick commands
  list the checked Hugging Face Space, Prime environment, NVIDIA safety, and
  ecosystem smoke reports under `reports/`, plus the bounded
  `release-artifacts --max-passes 6` convergence gate.
- Made the CI release-artifact convergence command explicit. GitHub Actions now
  runs `agades-pqc release-artifacts --max-passes 6`, and release audit rejects
  workflows that omit the bounded convergence option.
- Synced `docs/IMPLEMENT.md` with the checked release gates now enforced by
  CI: Hugging Face Space smoke, NVIDIA manifest safety, Prime environment
  smoke, ecosystem smoke, and `release-artifacts --max-passes 6` are explicit
  validation commands, and the runbook diff check covers their checked reports.
- Tightened the external publication review packet dry-run provenance. The
  `huggingface-dataset` dry-run entry now points at
  `hf/dataset/dataset_info.json` instead of the Hugging Face Collection
  manifest, and the verifier rejects any dry-run `source_manifest` that is not
  one of that surface's declared publication artifacts.
- Promoted NVIDIA manifest safety into a checked public report.
  `agades-pqc nvidia-manifest-safety` now writes
  `reports/nvidia_manifest_safety.json`, the verifier rejects stale GPU/current
  workload or security-claim drift, CI regenerates it before the NVIDIA
  publication handoff, and release audit consumes the checked report instead of
  carrying hidden NVIDIA manifest safety logic.
- Promoted the Prime Verifiers environment smoke into a checked public report.
  `agades-pqc prime-environment-smoke` now writes
  `reports/prime_environment_smoke.json`, the verifier rejects stale or unsafe
  reports, CI regenerates it before release convergence, and release audit
  consumes the checked report instead of carrying hidden Prime smoke logic.
- Promoted the Hugging Face Space smoke from an internal release-audit helper
  into a checked public report. `agades-pqc hf-space-smoke` now writes
  `reports/hf_space_smoke.json`, `hf-space-smoke-verify` rejects stale or
  unsafe reports, CI regenerates the report before release convergence, and
  release audit consumes the checked report instead of re-running hidden logic.
- Added a release-audit cross-check tying `docs/family_plugin_manifest.json`
  source digests to `public/runbook_audit.json`. The blocking
  `family-plugin-manifest` check now fails if the manifest module SHA-256 map
  diverges from the runbook family-plugin digest evidence.
- Anchored family plugin source digests directly in `public/runbook_audit.json`.
  The `runbook-family-agnostic-core` gate now records SHA-256 digests for all
  55 declared family implementation modules, and `public/release_audit.json`
  propagates the matching runbook module/digest/import counts.
- Propagated the family plugin source digest evidence from release audit into
  reviewer-facing status artifacts. `docs/release_status.json`,
  `public/publication_preflight.json`, and
  `docs/external_publication_review_packet.json` now expose the 55/55 family
  implementation-module digest count alongside module and import counts.
- Made `docs/family_plugin_manifest.json` digest-backed at the plugin source
  boundary. Each declared family implementation module now carries a SHA-256
  digest, `family-plugin-manifest-verify` rejects digest drift, and
  `public/release_audit.json` exposes the 55/55 implementation-module digest
  count for OSS review.
- Propagated the family plugin implementation-module evidence into
  `public/release_audit.json`. The blocking `family-plugin-manifest` check now
  exposes both the 55 declared implementation modules and the 55/55 successful
  import probes, aligning the top-level release audit with
  `docs/family_plugin_manifest.json`.
- Extended `docs/family_plugin_manifest.json` from descriptor/family bindings
  into a plugin implementation contract. Each plugin now lists its direct
  implementation modules and import paths; `family-plugin-manifest-verify`
  rejects stale module lists, count drift, and non-importable plugin internals,
  with 55/55 implementation module imports visible in the manifest summary.
- Expanded the `runbook-family-agnostic-core` importability gate from the
  minimal plugin/adapter/validator triplet to every direct Python module under
  each family plugin. The runbook audit now imports 55/55 family implementation
  modules, including toy estimators, operators, targets, and fixtures, so broken
  non-lattice family internals are caught by the same runbook evidence.
- Propagated the runbook importability evidence into reviewer-facing release
  surfaces. `docs/release_status.json`, `public/publication_preflight.json`,
  and `docs/external_publication_review_packet.json` now expose the 14/14
  family-agnostic core imports and 55/55 declared family plugin module imports;
  their verifiers reject stale or incomplete runbook architecture evidence.
- Hardened `runbook-family-agnostic-core` from a file/text presence check into
  an importability gate. `agades-pqc runbook-audit` now probes 14 core runtime
  object paths and 55 family plugin modules through an isolated
  `PYTHONPATH=<repo>/src` Python process, so copied-root audits catch broken
  core or plugin imports before runbook completion evidence is accepted.
- Hardened `docs/family_registry_manifest.json` as a runtime validator
  contract: its summary now records 9 applicability-validator bindings, 6
  distinct validator functions, the 4 lattice-validator families, and the 5
  non-lattice validator functions. `family-registry-manifest-verify` now
  imports each validator path, rejects non-callable validator targets, and
  rejects non-lattice registry entries that point at lattice validators; release
  audit carries the same validator evidence.
- Tightened warning-evidence synchronization checks so publication preflight
  warning records must match `public/release_audit.json`, and the external
  publication review packet warning evidence must match
  `public/publication_preflight.json`. The verifiers now catch non-empty but
  stale Prime Hub warning evidence with explicit source-drift failures.
- Propagated `warning_evidence_items` into the blocking
  `external-publication-review-packet` release-audit evidence, so the top-level
  audit now proves reviewer-facing warning evidence is present instead of only
  reporting the warning count.
- Hardened the publication preflight and external review packet verifiers so
  warning records must retain concrete evidence for every warning ID. Their
  verification summaries now expose `warning_evidence_items`, catching a stale
  reviewer-facing artifact that keeps only a warning count or ID.
- Extended `docs/release_status.json` so the audit block carries the concrete
  warning IDs and warning records, including the Prime Hub publication evidence
  derived from release audit. `release-status-verify` now rejects warning
  records that omit evidence instead of allowing a bare warning count.
- Propagated release-audit warning evidence into
  `public/publication_preflight.json` and the external publication review
  packet readiness block. The current Prime Hub warning now carries its
  derived publication/speedrun evidence through the reviewer-facing gate, not
  only in `public/release_audit.json`.
- Strengthened the nonblocking `prime-hub-publication` release-audit warning so
  its evidence is derived from the checked Prime publication and speedrun
  handoffs: local package readiness, credential/review gates, publication
  status, task counts, family counts, public run counts, and bundle counts are
  now visible in the warning instead of a hardcoded two-field summary.
- Added a persisted, verifier-checked `summary` block to
  `docs/source_catalog.json`, exposing current public surfaces, future reviewed
  adapter anchors, platform counts, local artifact source counts,
  source-map-only anchors, GPU-requiring source anchors, and the non-lattice toy
  operator scope. `source-catalog-verify` now rejects summary drift, and release
  audit propagates the richer source-catalog evidence for OSS reviewers.
- Added a persisted, verifier-checked `summary` block to
  `docs/family_support_matrix.json`, exposing family count, plugin count,
  support-level counts, public example count, benchmark count, future reviewed
  adapter source counts, and the `review_required_before_claims` gate. The
  richer summary is now propagated through Hugging Face Collection, Prime
  environment/publication/speedrun handoffs, NVIDIA accelerator/publication
  handoff, release status, publication/preflight packets, and release audit.
- Added `docs/runbook_input_manifest.json` as a digest-only public anchor for
  the user-provided v3 multi-family brief and project-context transcript. The
  manifest records only filenames, SHA-256 digests, line counts, validated
  anchor groups, and the current Agades PQC Gym naming override; it stores no
  local absolute paths and no source text. `runbook-audit`, release audit,
  release status, publication manifest, publication preflight, and the external
  publication review packet now carry that evidence.
- Replaced the hand-maintained non-lattice toy scope in
  `docs/source_catalog.json` with a verifier-checked scope derived from
  `docs/family_operator_catalog.json`: 41 non-lattice toy operator variants are
  now surfaced with family, plugin, operator type, estimator, review gate, and
  `security_claim=false`, including the public JSON-only dudect and ctgrind
  summary checks.
- Synchronized `docs/source_catalog.json` with the already implemented
  `code_based_hqc_circulant_erasure` toy evaluator surface, and refreshed the
  Hugging Face, NVIDIA, Prime speedrun, publication manifest, and external
  review packet digests that depend on the source catalog.
- Added a Prime AutoNanoGPT-style autonomy harness alignment to
  `docs/prime_speedrun_handoff.json`, mapping Prime's public harness pattern
  (`AGENTS.md`, mutable plan, durable thread log, run logs, scripts, configs)
  to Agades' public `AGENTS.md`, `docs/PLAN.md`, `docs/IMPLEMENT.md`,
  `docs/STATUS.md`, `public/run_export/manifest.json`, and
  `docs/private_run_policy.json` surfaces while explicitly recording that no
  external Prime autonomous run, private scratchpad publication, private
  evolution-trace publication, or private candidate-payload publication has
  occurred.
- Aligned the human-facing Hugging Face dataset card, packaged dataset README,
  Prime environment card, MVP report, README, architecture notes, and family
  adapter docs with the current implementation-security constant-time summary
  surfaces. The cards now explicitly mention
  `toy_dudect_summary_threshold_check` and
  `toy_ctgrind_secret_taint_summary_check`, and preserve the boundary that
  they validate public JSON summaries without executing dudect or ctgrind and
  make no constant-time, side-channel, or security claim.
- Added `docs/nvidia_publication_handoff.json` plus
  `agades-pqc nvidia-publication-handoff[-verify]`, turning the NVIDIA-facing
  accelerator strategy into a checked review packet with artifact digests,
  source-catalog anchors, and explicit boundaries that no external NVIDIA
  submission, GPU execution, GPU result, or security claim has been performed.
- Wired the NVIDIA publication handoff into GitHub Actions, release audit,
  publication manifest, release status, publication preflight, and the external
  publication review packet. The NVIDIA story now has the same deterministic
  local handoff gate as Hugging Face and Prime while remaining blocked behind
  human review before external use.
- Promoted the NVIDIA publication handoff into `docs/source_catalog.json` as
  `agades-nvidia-publication-handoff`, raising the source catalog to 41 sources
  and 15 current public surfaces while keeping the NVIDIA Inception entry as a
  source-map-only planning anchor.
- Added Prime Quickstart command alignment to
  `docs/prime_publication_handoff.json`, `docs/PRIME_INTELLECT_RELEASE_PLAN.md`,
  and `prime_intellect/environment_card.md`, recording the current public
  `prime` CLI onboarding and reference eval commands while preserving the
  no-external-Prime-execution and no-credential-material boundary.
- Synchronized the public artifacts after the new handoff: release audit now
  accepts 56/57 gates with the expected Prime publication warning, and the
  publication manifest covers 62 surface artifact SHA-256 digests plus the 3
  audited derived/recursive digest exclusions.
- Added a bounded public MDPC/BIKE-inspired syndrome-weight bit-flip toy
  fixture, AttackPlan, benchmark seed, package fixture mirror, Prime/Hugging
  Face rows, family-operator catalog entry, and regenerated the three-record
  `code_based_toy_mdpc_v0` bundle. This is public verifier plumbing only, not a
  BIKE result or security claim.

## 2026-05-17

Current delta on `codex/multifamily-architecture`:

- Added `docs/huggingface_publication_handoff.json` plus
  `agades-pqc hf-publication-handoff[-verify]`, turning the Hugging Face
  dataset, Space, and Collection publication path into a checked local handoff
  with artifact digests, credential/review blockers, and an explicit no-Hub
  publication claim boundary.
- Added `docs/prime_speedrun_handoff.json` plus
  `agades-pqc prime-speedrun-handoff[-verify]`, turning the Prime
  autonomous-speedrunning and auto-nanoGPT anchors into a checked public
  handoff that ties the JSON-only `SingleTurnEnv` task surface to
  `public/run_export/` while keeping external Prime execution blocked behind
  credential and release review.
- Promoted `public/runbook_audit.json` from a stale incidental output to a
  checked public release artifact: CI now regenerates it in place, release audit
  rejects drift, and the runbook deliverables evidence records the synchronized
  public audit check count.
- Added `docs/ecosystem_source_graph.json` plus
  `agades-pqc ecosystem-source-graph[-verify]`, giving reviewers a
  machine-readable OSS source graph from the public source catalog to future
  benchmark source contracts and then into per-family support. Release audit and
  CI now reject dangling source IDs across those three artifacts, including the
  Prime visibility anchors for quickstart, autonomous speedrunning experiments,
  and auto-nanoGPT.
- Tightened `agades-pqc ecosystem-source-graph-verify` so its public summary is
  recomputed from graph links, unresolved-link sections, source-catalog IDs, and
  Prime ecosystem anchors; release audit now exposes the full summary evidence
  and rejects stale source-graph summaries.
- Added a derived platform review matrix to `publication-preflight` and
  `external-publication-review-packet`, grouping GitHub, Hugging Face, Prime
  Intellect, and NVIDIA surfaces by artifact count, credential requirements,
  review gates, publication status, and smoke gates; both verifiers and release
  audit now reject stale or inconsistent platform-review summaries.
- Added a derived family readiness matrix to `publication-preflight` and
  `external-publication-review-packet`, sourced from
  `docs/family_support_matrix.json`, so external reviewers can inspect each
  family support level, toy/schema/implemented boundary, reproduction status,
  counts, and the LWE/MLWE-only Lattice Estimator allowance; release audit now
  rejects stale or overstated family-readiness summaries.
- Added a `runbook-family-agnostic-core` gate to `agades-pqc runbook-audit`,
  proving the expected core symbols (`TargetSpec`, `AttackPlan`,
  `AttackOperator`, `AssumptionSet`, `EvaluatorResult`, `FitnessReport`,
  `TraceRecord`, `ReportGenerator`, `FamilyAdapter`, and the public/private
  redaction entrypoint) and the six family plugin module triplets
  (`plugin.py`, `adapter.py`, `validators.py`) are present; release audit now
  carries the core-symbol and family-plugin counts.
- Expanded the runbook milestone coverage matrix so each milestone 0-8 now
  carries its exact evidence artifact list in `agades-pqc runbook-audit`, while
  release audit exposes the milestone IDs alongside the 9/9 pass counters for a
  faster external review path.
- Added a runbook milestone coverage matrix to `agades-pqc runbook-audit`,
  mapping milestones 0-8 to committed evidence for scaffold, DSL/validators,
  evaluator suite, trace redaction, OpenEvolve/DeepEvolve hooks, reporting,
  community release artifacts, collaboration briefs, and end-to-end public smoke
  artifacts; release audit now carries the 9/9 milestone evidence as a blocking
  runbook deliverable signal.
- Added a credential-free dry-run publication plan to
  `docs/external_publication_review_packet.json`, deriving five private/draft
  command templates or manual review actions for Hugging Face dataset, Space,
  Collection, and Prime Verifiers publication review while rejecting public
  visibility, embedded credential material, external URL recording, or claims
  that publication has already happened.
- Added a machine-readable credential review queue to
  `public/publication_preflight.json` and
  `docs/external_publication_review_packet.json`, requiring all four
  credentialed Hugging Face and Prime surfaces to stay covered by private/draft
  first-publication targets, review gates, smoke gates, artifact counts, and an
  explicit no-credential-material invariant before external publication.
- Extended `agades-pqc ecosystem-smoke` and the release-audit
  `ecosystem-smoke-report` evidence so Prime, Hugging Face Collection, and
  NVIDIA must each expose the platform-native public/private redaction gates
  for typed `TraceRecord` inputs, raw trace mappings, and matching report
  redaction records before aggregate smoke acceptance.
- Surfaced the public/private report-redaction gate directly in the Prime
  environment manifest, Hugging Face Collection manifest, and NVIDIA
  accelerator manifest, with platform-native verifiers rejecting drift in typed
  `TraceRecord` and raw trace-mapping redaction coverage before publication.
- Propagated the public/private report-redaction gate from release audit into
  `docs/release_status.json`, `public/publication_preflight.json`, and
  `docs/external_publication_review_packet.json`, so external reviewers can see
  that both typed `TraceRecord` inputs and raw trace mappings are covered before
  publication review.
- Hardened the family-agnostic `ReportGenerator` public/private boundary for
  raw trace mappings as well as typed `TraceRecord` objects, so private
  evaluator scores, estimator names, target labels, mutation summaries, and raw
  output keys are replaced with the shared redacted evaluation envelope before
  Markdown rendering. The blocking release-audit redaction smoke now covers both
  input shapes.
- Promoted the multi-family publication gate into
  `docs/publication_manifest.json` itself and added
  `docs/family_support_matrix.json` to the GitHub publication artifact set, so
  the central publish contract now exposes the same Prime/Hugging Face/NVIDIA
  family-count and `review_required_before_claims` checks as preflight, review
  packet, smoke, and release-audit surfaces.
- Added a shared release-status family-support publication summary and carried
  it into `public/publication_preflight.json` plus
  `docs/external_publication_review_packet.json`, so the publication front door
  now proves Prime, Hugging Face Collection, and NVIDIA preserve matching family
  counts and `review_required_before_claims` gates before any external push.
- Extended `agades-pqc ecosystem-smoke` and the release-audit
  `ecosystem-smoke-report` evidence so Prime, Hugging Face Collection, and
  NVIDIA must each expose family-support summaries with matching family counts
  and `review_required_before_claims` gates.
- Propagated the platform-native `family_support` summaries into
  `docs/release_status.json` under Prime Intellect, Hugging Face Collection, and
  NVIDIA, and tightened `release-status-verify` so each platform must preserve
  `review_required_before_claims`.
- Added native `family_support` summaries to the Prime environment, Hugging Face
  Collection, and NVIDIA accelerator manifests, with verifiers enforcing
  `review_required_before_claims` so platform artifacts carry the multi-family
  boundary directly instead of only linking the matrix.
- Propagated the release packet's multi-family support summary into
  `external-publication-review-packet-verify`, `ecosystem-smoke`, and
  `public/release_audit.json`, so no-credential Prime/Hugging Face/NVIDIA smoke
  evidence now carries the family-support review boundary.
- Surfaced the multi-family support summary in `docs/release_status.json` and
  `docs/external_publication_review_packet.json`, including implemented,
  schema-only, toy-evaluator, and future source-contract coverage while keeping
  `review_required_before_claims` enforced.
- Extended `docs/family_support_matrix.json` so every family records its
  future reviewed adapter source-contract IDs and cross-family review source
  IDs, while `family-support-verify` rejects drift and keeps those contracts
  blocked from runtime/public-claim surfaces.
- Promoted `public/run_export/manifest.json` into the Hugging Face Collection
  contract and NVIDIA public artifact set, with release gates requiring
  `agades-pqc public-run-export` and `agades-pqc public-run-export-verify`
  before those ecosystem manifests are considered synchronized.
- Synchronized the public release cards, Prime environment card, NVIDIA strategy,
  and MVP report so the HQC-inspired circulant-erasure surface is visible as
  public fixture plumbing and explicitly not an HQC result.
- Added regression coverage requiring Prime, Hugging Face, NVIDIA, README, and
  MVP report surfaces to describe the `hqc_circulant_erasure_toy` boundary and
  requiring the Prime environment card to list every current public run bundle.
- Ran a private real-checkout Lattice Estimator preflight against
  `malb/lattice-estimator` at the reviewed `6019056011d10d7e9c30a0d5da2d2f729fbc2eec`
  pin; the private preflight is ready, clean, upstream-origin matched, and
  non-executing.
- Installed an isolated local `agades-sage` Conda environment with SageMath
  10.8 for private reproduction work. Direct `sage -python` is not available in
  that conda-forge CLI, so Agades now supports an explicit
  `--sage-python-command` path for Python environments where `sage.all` imports
  successfully.
- Added a private Lattice Estimator Sage runtime preflight. It probes only
  `<sage-command> --version` and
  `<sage-python-command> -c 'import sage.all'`, is documented in the Lattice
  Estimator manifest and release audit, writes only to private roots, and has a
  standalone verifier that accepts both ready reports and closed-failure reports
  while rejecting unsafe drift. The local private runtime preflight now reports
  Sage 10.8 ready with `sage.all` importable.
- Ran the matching private baseline run against the checked-out
  `malb/lattice-estimator` pin through the no-shell Sage Python worker. The
  private report records five pinned numeric LWE mapping results (`bdd`, `bkw`,
  `dual`, `dual_hybrid`, `usvp`), keeps numeric outputs under
  `private/reports/`, stores raw estimator payloads by digest only, and still
  publishes no public numeric baseline or security claim.
- Added `agades-pqc lattice-estimator-baseline-run-verify` as the standalone
  private report verifier for expert review. It re-checks contract sync, the
  reviewed upstream pin, result-to-contract mapping, LWE-only scope, private
  publication flags, raw-output SHA-256 digests, summary counters, and absence
  of raw estimator or AttackPlan payload leakage.
- Added `agades-pqc lattice-estimator-baseline-review-packet` and
  `agades-pqc lattice-estimator-baseline-review-packet-verify` as the private
  digest-only expert-review handoff for verified baseline reports. The packet
  carries source report digests, raw-output digests, upstream pin evidence,
  algorithm/result identifiers, and review questions while rejecting numeric
  leakage, public output paths, raw estimator payloads, and AttackPlan payloads.
- Added a blocking release-audit smoke gate for that runtime preflight verifier,
  proving the missing-Sage closed-failure path without requiring Sage, touching
  `private/`, publishing numeric outputs, or making a security claim.
- Added a Sage subprocess worker path for private baseline runs, so reviewed
  `--estimator-source` checkouts can execute under legacy `sage -python` via
  `--sage-command` or under conda-style Python via `--sage-python-command`
  after the checkout preflight instead of depending on Sage being importable in
  the normal `uv` Python environment.
- Added bounded JSON-only `code_based` HQC-inspired circulant-erasure fixture plumbing through `decoding_fixture_check:hqc_circulant_erasure_toy`, with a dedicated `toy-code-based-circulant-erasure-decoder-estimator`, package fixture mirror, and explicit no-HQC-result/no-security-claim boundary.
- Added the public AttackPlan, benchmark seed, Prime packaged task, Hugging Face rows, and regenerated `code_based_toy_hqc_v0` bundle for the circulant-erasure surface.
- Synchronized release-facing counts to 18 public bundles, 57 accepted public records, 78 Hugging Face AttackPlan rows, 77 valid public task rows, 77 Prime packaged tasks, and 27 NVIDIA workload descriptors.
- Bumped Prime/Hugging Face task metadata to `agades.pqc.task_metadata.v4`, so
  every valid public task row carries the exact seed AttackPlan SHA-256 digest
  while Prime scoring still allows same-task candidate variants instead of
  forcing an `attack_plan_id` copy.
- Tightened the Hugging Face dataset verifier so checked-in task metadata is
  rejected when its seed digest no longer matches the embedded AttackPlan JSON
  row, and added Prime environment coverage that rows expose the packaged seed
  file digest exactly.
- Added a blocking release-audit smoke gate for the checked-in OpenEvolve
  evaluator wrapper, proving it can score a public JSON AttackPlan through
  `combined_score` and MAP-Elites feature metrics without executing Python
  candidates.
- Added `agades-pqc openevolve-smoke` and the importable
  `agades_pqc_gym.openevolve_adapter.build_openevolve_smoke_report`, so
  reviewers can reproduce that OpenEvolve evaluator smoke report directly; CI
  and release-audit required commands now include the smoke report generation.
- Added `agades-pqc ecosystem-smoke`, a local no-credential JSON smoke matrix
  across Hugging Face, Prime Intellect, NVIDIA, publication preflight, and the
  external publication review packet; CI and release audit now require that
  aggregate report while preserving the blocked-by-default external publication
  state.
- Current verification after these changes: `uv run --extra dev ruff check .`
  passed; `uv run --extra dev pytest -q` reported 759 passed; `git diff
  --check` passed; the checked Hugging Face, Prime, and NVIDIA handoffs plus
  release audit regenerate byte-for-byte; release audit accepted 56/57 gates
  with the expected Prime publication warning; runbook audit with the v3
  multi-family brief and project-context transcript accepted 8/8 gates; `uv
  build` and `uv build prime_intellect/verifiers_environment` both passed.

## 2026-05-15

Current milestone: v3 multi-family refactor implemented on branch `codex/multifamily-architecture`.

Completed:

- Baseline on `main` was clean before the v3 refactor.
- Added v3 implementation plan at `docs/superpowers/plans/2026-05-15-multifamily-pqc-gym.md`.
- Renamed package and CLI surface to `agades_pqc_gym` / `agades-pqc`.
- Added family-agnostic core: `TargetSpec`, `AttackPlan`, `AttackOperator`, `FamilyAdapter`, and registry.
- Migrated LWE/MLWE into the `families/lattice` adapter.
- Added schema-only placeholder adapters for code-based, multivariate, hash-based, historical isogeny, and implementation-security families.
- Added schema-only placeholder AttackPlans and benchmark configs.
- Added architecture docs, family adapter docs, contributing/security docs, issue templates, and NVIDIA/accelerator strategy doc.
- Added a checked-in NVIDIA/accelerator manifest at `nvidia/accelerator_manifest.json` plus `agades-pqc nvidia-manifest` regeneration command.
- Added `agades-pqc nvidia-manifest-verify` and wired it into CI/release-audit so NVIDIA-facing artifacts cannot drift toward GPU-required current workloads, private publication, or security-claim language.
- Updated Hugging Face and Prime Intellect cards for the multi-family verifier/environment framing.
- Added a Hugging Face Space example selector for curated public toy/schema-only AttackPlans.
- Made the Hugging Face Space load valid public AttackPlans from the checked-in dataset bundle and install the shared verifier package from GitHub.
- Added a checked-in Hugging Face dataset bundle at `hf/dataset/` plus `agades-pqc hf-dataset` regeneration command.
- Added `agades-pqc hf-dataset-verify` and wired it into CI/release-audit plus HF Space, HF Collection, and NVIDIA release gates so dataset row counts, task metadata, verifier rows, public-run mirrors, checksum manifests, and no-claim/no-private-trace flags cannot drift silently.
- Added YAML PaperCard ingestion for DeepEvolve-style hooks plus review-gated research-note cards across lattice, code-based, multivariate, hash-based, implementation-security, and historical-isogeny directions.
- Added checked-in `docs/deepevolve_research_hooks_manifest.json` plus `agades-pqc deepevolve-manifest` / `agades-pqc deepevolve-manifest-verify`, so PaperCard hooks remain public, `note_only`, review-required, non-executing, and disconnected from estimator scores.
- Added `agades_pqc_gym.deepevolve_hooks.injection` and `agades-pqc deepevolve-injections`, producing private `agades.pqc.paper_card_injection_batch.v1` hypothesis queues from public PaperCards without writing AttackPlans, executing code, modifying estimator scores, publishing candidates, or making research claims.
- Added a shared public verifier API plus `agades-pqc verify`, `prime_intellect/verifier.py`, and `hf/app.py` executable wrappers.
- Added a Prime Verifiers single-turn environment skeleton at `prime_intellect/verifiers_environment/`.
- Expanded the Prime Verifiers environment package to embed every valid public toy/schema-only AttackPlan example across the multi-family surface.
- Added deterministic public run ledger and bundle packaging via `agades-pqc public-ledger` and `agades-pqc public-bundle`.
- Committed the first public toy LWE run bundle at `examples/public_runs/lattice_toy_lwe_v0/`.
- Made public trace and bundle artifacts byte-reproducible by canonicalizing public timestamps and trace IDs.
- Integrated a conservative downscaled evaluator reproduction smoke into lattice cascade metrics, public verifier output, and Hugging Face verifier rows.
- Added a public reproduction-requesting toy LWE AttackPlan for Prime/Hugging Face demos without making a cryptanalytic claim.
- Added a deterministic public source catalog at `docs/source_catalog.json` plus `agades-pqc source-catalog` for OSS/benchmark anchors and release review.
- Added `agades-pqc source-catalog-verify` and release gates that reject private-candidate publication, security claims, missing Prime/HF/NVIDIA/NIST/GitHub anchors, and broken local artifact links in the source catalog.
- Updated the source catalog to enumerate every current non-lattice toy evaluator surface and to add Prime Quickstart plus Prime RL as machine-readable Prime ecosystem anchors; Prime RL remains a future reviewed training adapter, while the quickstart is source-map-only onboarding.
- Added Hugging Face Space and Hugging Face Collection as current public surfaces in `docs/source_catalog.json`, so the source map covers the same HF release contracts as the publication, NVIDIA, and release-status manifests.
- Added a deterministic public family support matrix at `docs/family_support_matrix.json` plus `agades-pqc family-support`; NTRU/SIS are explicitly schema-only until reviewed mappings exist.
- Added `agades-pqc family-support-verify` and release gates that reject matrix drift which would overstate non-lattice support, claim the Lattice Estimator as a universal PQC oracle, or allow fake estimates for unsupported families.
- Added a deterministic runtime family registry manifest at `docs/family_registry_manifest.json` plus `agades-pqc family-registry-manifest` / `agades-pqc family-registry-manifest-verify`, cross-checking every `TargetFamily` against the registered adapter class, plugin, support level, support matrix, operator catalog, and Lattice Estimator boundary.
- Added per-family operator review boundaries to `docs/family_registry_manifest.json`, explicitly separating runtime operator types, cataloged review-gated operator entries, and LWE-only external Lattice Estimator mappings.
- Added a deterministic family plugin descriptor manifest at `docs/family_plugin_manifest.json` plus `agades-pqc family-plugin-manifest` / `agades-pqc family-plugin-manifest-verify`, cross-checking every plugin descriptor, adapter class, support level, and applicability validator while rejecting non-lattice drift toward lattice validators.
- Tightened the lattice adapter so runtime-only LWE transform operators remain auxiliary and return `unsupported` when used as the primary estimator route before catalog review.
- Added a public LWE `modulus_switching` primary-route boundary fixture that is schema-valid but verifier-unsupported, propagates to Hugging Face and Prime as a zero-reward task, and documents that lattice runtime transforms are not reviewed estimator routes by default.
- Added a blocking `lattice-runtime-primary-boundary` release-audit gate that cross-checks the public boundary fixture, public verifier output, Hugging Face task metadata, Hugging Face Space labels, and Prime task metadata so runtime-only lattice transforms cannot silently become accepted LWE estimator routes.
- `agades-pqc prime-manifest` now synchronizes the packaged Prime `data/*.json` mirror from valid public AttackPlan examples before writing the manifest, removing the previous manual-copy failure mode when public examples change.
- Registered `docs/family_registry_manifest.json` and `docs/family_plugin_manifest.json` as current public source-catalog surfaces so OSS reviewers can discover the runtime registry and plugin descriptor contracts alongside the support matrix, publication manifest, Prime, Hugging Face, and NVIDIA surfaces.
- Added a deterministic public release audit at `public/release_audit.json` plus `agades-pqc release-audit` for multi-family plugin readiness and HF/Prime/NVIDIA/source-catalog/public-ledger safety gates.
- Hardened `.github/workflows/ci.yml` so public PR/push CI runs tests, lint, whitespace checks, deterministic release-artifact regeneration, release audit, and package builds for both `agades-pqc-gym` and the Prime verifier environment.
- Added a blocking release-audit Hugging Face Space smoke that imports `hf/app.py`, loads public examples, and evaluates the default AttackPlan without requiring Gradio.
- Added a blocking release-audit Prime Verifiers smoke that imports the packaged environment, builds task rows, scores accepted JSON, and rejects unsupported or prefixed non-JSON submissions.
- Added a blocking release-audit checksum gate for checked-in Hugging Face and public-run `MANIFEST.sha256` files, including stale-manifest regression coverage.
- Added a reviewed LWE BDD operator surface (`bounded_distance_decoding`) mapped to the Lattice Estimator `bdd` key, plus a public toy AttackPlan propagated into Hugging Face and Prime artifacts.
- Tightened the NTRU/SIS boundary so schema-only lattice families require `support_level="schema_only"` and no longer advertise LWE estimator operators in the support matrix.
- Added public direct LWE toy plans for `dual_attack` and `bkw`, so every current direct Lattice Estimator mapping has a checked-in example and Prime/Hugging Face task row.
- Added a blocking release-audit gate proving every reviewed direct LWE Lattice Estimator mapping has a public example, Hugging Face dataset row, and packaged Prime task.
- Extended private candidate mutation beyond lattice-only search: `agades-pqc mutate-candidates` now emits validated private mutations for reviewed code-based toy ISD knobs (`p`, `ell`, `representation_count`) plus Prange toy target weight (`w`), reviewed multivariate toy MQ knobs (`variables`, `equations`, `guessed_variables`, `degree_bound`), reviewed hash-based toy preimage digest bits (`n`), reviewed implementation-security toy KAT knobs (`vector_count`), and reviewed historical-isogeny toy path knobs (`walk_length`, `branching_factor`) while keeping schema-only, fixture-bound, and unsupported families skipped.
- Added public schema-only NTRU and SIS lattice AttackPlans plus `benchmarks/lattice_schema_only/`, keeping both families schema-valid but `evaluation_status="unsupported"` through `lattice-family-router` until reviewed mappings exist.
- Added a deterministic OSS publication manifest at `docs/publication_manifest.json` plus `agades-pqc publication-manifest`, mapping GitHub, Hugging Face, Prime Intellect, and NVIDIA surfaces with credential/review boundaries.
- Added `agades-pqc publication-manifest-verify` and wired it into CI/release-audit so the multi-platform publication contract cannot drift from artifact digests, review gates, no-private-publication flags, or no-security-claim boundaries.
- Added a blocking release-audit publication-manifest gate so public release artifacts cannot silently drift from the multi-platform OSS publication contract.
- Added deterministic SHA-256 provenance to `docs/publication_manifest.json` for GitHub, Hugging Face, Prime Intellect, NVIDIA, and public-run bundle artifacts, with an explicit audited exclusion for the recursive `public/release_audit.json` artifact.
- Wired family adapter applicability findings into static validation and added explicit non-lattice schema-only validators for code-based dimensions, multivariate finite-field notation, reviewed hash-function names, and historical-isogeny boundary assumptions.
- Added a blocking release-audit schema-only applicability gate so non-lattice adapters cannot regress to empty validation while still refusing fake cryptanalytic estimates.
- Added a checked-in Prime Verifiers environment manifest at `prime_intellect/verifiers_environment/prime_manifest.json` plus `agades-pqc prime-manifest`, documenting packaged tasks, eval defaults, reward boundaries, and JSON-only submission safety.
- Added a blocking release-audit Prime environment manifest gate and CI artifact sync so Prime task/package drift is caught before publication.
- Added `agades-pqc prime-manifest-verify` and wired it into CI/release-audit so Prime manifest drift, executable submission flags, schema references, source mirrors, and review gates are checked as a standalone contract.
- Added a checked-in Hugging Face Space manifest at `hf/space_manifest.json` plus `agades-pqc hf-space-manifest`, documenting exposed examples, the default example, dependency file, shared verifier contract, and no-code/no-claim boundaries.
- Added a blocking release-audit Hugging Face Space manifest gate and CI artifact sync so Space selector drift is caught before publication.
- Added `agades-pqc hf-space-manifest-verify` and wired it into CI/release-audit so Space manifest drift, app selector/default mismatch, unsafe code/live-target flags, dataset-count drift, and publication review gates are checked as a standalone contract.
- Added a checked-in Hugging Face Collection manifest at `hf/collection_manifest.json` plus `agades-pqc hf-collection-manifest`, grouping the GitHub repo, dataset, Space, benchmark card, source catalog, and public benchmark manifest into a review-required no-claim publication contract.
- Added a blocking release-audit Hugging Face Collection manifest gate so Collection entries, credential/review boundaries, local artifact links, release gates, and no-private/no-claim flags cannot drift silently.
- Added `agades-pqc hf-collection-manifest-verify` and wired it into CI/release-audit so Collection entries, local artifact links, source/public-benchmark verifier gates, and review/no-claim publication boundaries are checked as a standalone contract.
- Updated the NVIDIA accelerator manifest to reference the Hugging Face Space manifest, Hugging Face Collection manifest, and Prime environment manifest, and tightened the NVIDIA release-audit evidence to catch accelerator-facing artifact drift.
- Tightened the implementation-security schema-only adapter so public plans and benchmark seeds must identify schema fixtures, use explicit `_schema_placeholder` tool/suite/metric parameters, and reject executable/live artifact fields such as `binary_path`.
- Added a second committed public run bundle for the downscaled MLWE benchmark and made the Hugging Face dataset exporter, NVIDIA manifest, and release audit discover or advertise public run bundles instead of hard-coding the first LWE bundle.
- Added explicit public run bundle indexing to `docs/publication_manifest.json`, so the central OSS publication contract now lists the LWE and downscaled MLWE bundles, benchmark paths, artifact files, and no-private/no-claim flags.
- Added the first non-lattice toy evaluator: `CODE_BASED` now supports a bounded `prange_toy` Information Set Decoding work-factor model for small `toy_` syndrome-decoding targets while keeping HQC-like placeholders schema-only/unsupported.
- Added a public code-based toy AttackPlan, benchmark, and committed public run bundle at `examples/public_runs/code_based_toy_isd_v0/`, propagated through Hugging Face, Prime Verifiers, NVIDIA, the publication manifest, checksum manifests, and release audit.
- Added a second bounded code-based ISD toy variant: `stern_toy` with explicit Stern partition parameter validation, deterministic no-claim work-factor output, and a public AttackPlan propagated through Hugging Face, Prime Verifiers, family support, publication manifest, and release audit.
- Added a bounded code-based Lee-Brickell-style toy variant: `lee_brickell_toy` with a dedicated partial-enumeration assumption, strict `p` applicability checks, a public AttackPlan, benchmark seed, Prime task, and a regenerated four-record `code_based_toy_isd_v0` public run bundle. This is ISD evaluator plumbing only, not an HQC, Classic McEliece, or security claim.
- Added a bounded code-based Dumer-style list-merging toy variant: `dumer_toy` with a dedicated merge-window assumption, strict `p`/`ell` applicability checks, a public AttackPlan, benchmark seed, Prime task, and a regenerated five-record `code_based_toy_isd_v0` public run bundle. This is ISD evaluator plumbing only, not an HQC, Classic McEliece, or security claim.
- Added the Stern-style code-based toy seed to the committed public benchmark bundle with explicit public fixture reproduction, regenerating the six-record `code_based_toy_isd_v0` bundle while preserving the no-HQC/no-security-claim boundary.
- Added the second non-lattice toy evaluator: `HASH_BASED` now supports a bounded `toy_preimage_bound` model for small `toy_` hash preimage-bound targets while keeping SLH-DSA-style placeholders schema-only/unsupported.
- Added a public hash-based toy AttackPlan, benchmark, and committed public run bundle at `examples/public_runs/hash_based_toy_bound_v0/`, propagated through Hugging Face, Prime Verifiers, NVIDIA, the publication manifest, checksum manifests, and release audit.
- Added a second hash-based toy surface: `hash_signature_verification:toy_wots_chain_verify`, with a strict public SHAKE256 signature-chain fixture verifier and committed public run bundle at `examples/public_runs/hash_based_toy_signature_v0/`. This is chain-verification plumbing, not an SLH-DSA/SPHINCS+ security claim.
- Added a hash-based Merkle auth-path toy surface: `hash_signature_verification:toy_merkle_auth_path_verify`, with a strict public SHAKE256 auth-path fixture verifier and a regenerated two-record `hash_based_toy_signature_v0` public run bundle. This is auth-path verification plumbing, not an SLH-DSA/SPHINCS+ security claim.
- Added a hash-based FORS-inspired auth-path toy surface: `hash_signature_verification:toy_fors_auth_path_verify`, with `toy_hash_fors_auth_path_model`, strict selected-index/tree bounds, a public SHAKE256 fixture verifier, a package fixture mirror, Prime/Hugging Face propagation, and a regenerated three-record `hash_based_toy_signature_v0` public run bundle. This is FORS-style verifier plumbing, not an SLH-DSA result or security claim.
- Added a hash-based SLH-DSA-like hypertree toy surface: `hash_signature_verification:toy_slh_dsa_hypertree_verify`, with `toy_hash_slh_dsa_hypertree_model`, strict FORS/WOTS/hypertree bounds, a public SHAKE256 fixture verifier, a package fixture mirror, Prime/Hugging Face/NVIDIA propagation, and a regenerated four-record `hash_based_toy_signature_v0` public run bundle. This is JSON-only public verifier plumbing, not an SLH-DSA result or security claim.
- Added a hash-based collision-bound toy surface: `security_bound_check:toy_collision_bound`, with a dedicated `toy_hash_collision_bound_model` assumption, birthday-bound output, public AttackPlan, Prime task, and regenerated three-record `hash_based_toy_bound_v0` public run bundle. This is hash-bound evaluator plumbing only, not collision-finding evidence or a security claim.
- Added a public SHAKE256 truncated-collision fixture verifier for `toy_collision_bound`, mirrored it as package data for installed verifier use, and regenerated the `hash_based_toy_bound_v0` public run bundle plus Hugging Face, Prime, family-support, public-benchmark, publication, and release-status artifacts. This verifies two fixed public messages against a 32-bit digest prefix only; it is not full-size collision evidence or a security claim.
- Added a hash-based reused-salt misuse toy surface: `misuse_check:toy_hash_reused_salt`, with a strict public SHAKE256 JSON-only fixture verifier, package fixture mirror, Prime/Hugging Face/NVIDIA propagation, and committed public run bundle at `examples/public_runs/hash_based_toy_misuse_v0/`. This is misuse-detection plumbing only, not exploit evidence or a security claim.
- Added the third non-lattice toy evaluator: `MULTIVARIATE` now supports bounded `toy_mq_search`, `toy_mq_hybrid_search`, `toy_mq_degree_bound`, `toy_minrank_search`, and `toy_uov_public_map_verify` models for small `toy_` MQ, MinRank, and UOV-inspired public-map verifier targets while keeping real UOV/MAYO/Rainbow-style cryptanalysis placeholders schema-only/unsupported.
- Added a public multivariate toy AttackPlan, benchmark, and committed public run bundle at `examples/public_runs/multivariate_toy_mq_v0/`, propagated through Hugging Face, Prime Verifiers, NVIDIA, the publication manifest, checksum manifests, and release audit.
- Added a second public multivariate toy AttackPlan, benchmark, and committed public run bundle at `examples/public_runs/multivariate_toy_minrank_v0/`, propagated through Hugging Face, Prime Verifiers, NVIDIA, the publication manifest, checksum manifests, and release audit.
- Added a bounded multivariate MQ hybrid-search toy surface, `toy_mq_hybrid_search`, with a dedicated linearization assumption, strict `guessed_variables` applicability checks, a public AttackPlan, benchmark seed, Prime task, and a regenerated four-record `multivariate_toy_mq_v0` public run bundle. The public `GF(2)` fixture path now uses bounded guess-prefix split-search reproduction plumbing; this is not a UOV/MAYO/Rainbow or security claim.
- Added a bounded multivariate MQ degree-bound toy surface, `toy_mq_degree_bound`, with an explicit `toy_mq_degree_bound_model` assumption, strict `degree_bound` and `linear_algebra_omega` applicability checks, a public AttackPlan, benchmark seed, Prime task, family-operator-catalog entry, and a regenerated five-record `multivariate_toy_mq_v0` public run bundle. This is estimator plumbing only, not a Groebner proof, UOV/MAYO/Rainbow result, or security claim.
- Added a public `GF(2)` reproduction wrapper for `toy_mq_degree_bound`, with a dedicated AttackPlan, benchmark seed, Prime task, Hugging Face row, and regenerated six-record `multivariate_toy_mq_v0` bundle. It solves only the tiny public MQ fixture by bounded exhaustive search as verifier plumbing; it is not a Groebner proof or a security claim.
- Added a bounded multivariate UOV-inspired public-map verification surface, `toy_uov_public_map_verify`, with an explicit `toy_uov_public_map_verification_model` assumption, strict oil/vinegar partition checks, a public `GF(2)` fixture, AttackPlan, benchmark seed, Prime task, Hugging Face row, NVIDIA workload descriptor, family-operator-catalog entry, and a new `multivariate_toy_uov_v0` public bundle. It evaluates only one tiny public signature/map fixture as verifier plumbing; it is not a UOV, MAYO, Rainbow, forgery, or security claim.
- Added a third public MinRank reproduction fixture, `toy_minrank_gf2_m4_r2`, with a rank-two `GF(2)` matrix-pencil target, public AttackPlan, benchmark seed, package fixture mirror, Prime packaged task, Hugging Face row, and regenerated three-record `multivariate_toy_minrank_v0` bundle. It remains bounded toy verifier plumbing only, not UOV/MAYO/Rainbow cryptanalysis or a security claim.
- Added public schema-only multivariate placeholders and benchmark targets for MAYO-like and Rainbow-historical shapes. They validate and propagate to Hugging Face and Prime as explicit `unsupported`/zero-reward public tasks, without adding a fake Groebner, MinRank, signature-forgery, MAYO, Rainbow, or security estimate.
- Added the fourth non-lattice toy evaluator: `IMPLEMENTATION_SECURITY` now supports a bounded JSON-only `toy_kat_digest_match` model for small `toy_` KAT digest manifests while keeping constant-time, benchmark-harness, and live-artifact work schema-only/unsupported.
- Added a public implementation-security toy AttackPlan, benchmark, and committed public run bundle at `examples/public_runs/implementation_security_toy_kat_v0/`, propagated through Hugging Face, Prime Verifiers, NVIDIA, the publication manifest, checksum manifests, and release audit.
- Added a second implementation-security toy surface: `constant_time_check:toy_timing_welch_t_check`, computing a bounded Welch-style statistic from tiny public JSON cycle arrays while refusing live traces and making no constant-time, side-channel, or security claim.
- Added a public implementation-security timing AttackPlan, benchmark, fixture verifier, and committed public run bundle at `examples/public_runs/implementation_security_toy_timing_v0/`, propagated through Hugging Face, Prime Verifiers, NVIDIA, the publication manifest, checksum manifests, and release audit.
- Added a bounded JSON-only dudect-summary timing surface: `constant_time_check:toy_dudect_summary_threshold_check`, verifying a reviewed public summary schema without executing dudect and without making a constant-time, side-channel, or security claim.
- Added a bounded JSON-only ctgrind-style secret-taint summary surface: `constant_time_check:toy_ctgrind_secret_taint_summary_check`, verifying public threshold counters without executing ctgrind and without making a constant-time, side-channel, or security claim.
- Added a third implementation-security toy surface: `kat_conformance:toy_acvp_vector_set_match`, validating a bounded JSON-only ACVP-like ML-KEM vector-set manifest by canonical digest, while explicitly making no ACVP certificate, conformance, side-channel, or security claim.
- Added a public implementation-security ACVP-like AttackPlan, public fixture, benchmark seed, Prime packaged task, and regenerated three-record `implementation_security_toy_kat_v0` public run bundle, propagated through Hugging Face, Prime Verifiers, the publication manifest, checksum manifests, and release audit.
- Added a public ML-DSA toy KAT digest AttackPlan, public no-execution fixture, benchmark seed, package fixture mirror, and Prime packaged task, then regenerated the four-record `implementation_security_toy_kat_v0` bundle across Hugging Face, Prime Verifiers, the publication manifest, checksum manifests, and release audit. This remains JSON-only verifier plumbing, not FIPS 204 conformance, side-channel, or security evidence.
- Extended the ACVP-like implementation-security validator with a reviewed ML-DSA `signature-verification` field profile (`seed`, `message`, `publicKey`, `signature`), plus a public ML-DSA ACVP-like vector-set AttackPlan, no-execution fixture, benchmark seed, package fixture mirror, and Prime packaged task. The `implementation_security_toy_kat_v0` bundle now has five records and still makes no ACVP, conformance, side-channel, or security claim.
- Added a fourth implementation-security toy surface: `benchmark_harness:toy_benchmark_summary_check`, computing bounded summary statistics from a tiny public JSON cycle array while refusing live devices/logs and making no performance, conformance, side-channel, or security claim.
- Added a public implementation-security benchmark-summary AttackPlan, benchmark, fixture verifier, Prime packaged task, and committed public run bundle at `examples/public_runs/implementation_security_toy_benchmark_v0/`, propagated through Hugging Face, Prime Verifiers, NVIDIA, the publication manifest, checksum manifests, and release audit.
- Added a fifth implementation-security toy surface: `benchmark_harness:toy_memory_footprint_check`, computing bounded public memory-footprint component byte summaries from JSON-only fixtures while refusing live devices/logs and making no memory-usage, performance, conformance, side-channel, or security claim.
- Added a sixth implementation-security toy surface: `benchmark_harness:toy_binary_size_check`, computing bounded public binary-size summaries from JSON-only fixtures while refusing live binaries/build logs and making no binary-size, performance, conformance, side-channel, or security claim.
- Added a seventh implementation-security toy surface: `benchmark_harness:toy_stack_usage_check`, computing bounded public stack high-water sample summaries from JSON-only fixtures while refusing live binaries/devices/logs and making no stack-usage, performance, conformance, side-channel, or security claim.
- Added the fifth non-lattice toy evaluator: `ISOGENY_HISTORICAL` now supports a bounded historical `toy_sidh_path_search` model for small `toy_` SIDH/SIKE-style path fixtures while keeping current-standard and non-toy claims unsupported.
- Added a second historical-isogeny toy case, `toy_commutative_walk_search`, with a separate `historical_toy_commutative_walk_model` assumption, public fixture, public AttackPlan, and Prime task. This is commutative-walk plumbing only, not a CSIDH result, current-standard result, or security claim.
- Added a third historical-isogeny toy case, `toy_volcano_walk_search`, with a separate `historical_toy_volcano_walk_model` assumption, bounded `volcano_height`, public graph/path fixture, public AttackPlan, Prime/Hugging Face/NVIDIA propagation, and the regenerated four-record `isogeny_historical_toy_path_v0` public bundle. This is volcano-style historical fixture plumbing only, not a CSIDH, SIDH/SIKE, current-standard, or security claim.
- Added a public historical-isogeny toy AttackPlan, benchmark, and committed public run bundle at `examples/public_runs/isogeny_historical_toy_path_v0/`, propagated through Hugging Face, Prime Verifiers, NVIDIA, the publication manifest, checksum manifests, and release audit.
- Added a blocking release-audit community release card gate so Hugging Face, Prime Intellect, and MVP report cards must describe the current toy evaluator families, public run bundles, and stale schema-only claims cannot silently reappear.
- Added a source-catalog sync gate for `implementation_security_memory_footprint` so the public source map enumerates the JSON-only memory-footprint surface alongside the benchmark-summary surface.
- Added a dedicated NVIDIA workload descriptor for the implementation-security memory-footprint benchmark surface so accelerator-facing manifests enumerate it separately from benchmark-summary plumbing.
- Added checked-in Prime/Hugging Face verifier JSON schemas at `prime_intellect/schemas/` plus `agades-pqc prime-schemas`, Prime manifest references, publication-manifest artifacts, CI regeneration, and a blocking release-audit schema sync gate.
- Added `agades-pqc prime-schemas-verify` and a CI/release-audit gate that rejects schema bundle drift, executable/live-target acceptance, unsafe publication flags, stale required fields, and missing Prime schema release gates.
- Tightened the Prime Verifiers environment manifest, README, and release-audit gate so local editable install/eval commands are distinct from owner-qualified Environments Hub install/push commands, and documented that local evaluation requires no environment variables.
- Tightened the Hugging Face Space manifest, README, and release-audit gate so reviewed Space creation/upload commands use the current `hf` CLI with `--repo-type=space`, keep the first publication private, and document `HF_TOKEN` automation boundaries.
- Added a blocking release-audit ecosystem release-plan gate so the Hugging Face, Prime Intellect, and NVIDIA planning docs must mention all current public run bundles, the Prime/HF verifier schemas, the Prime autonomous-speedrunning reference, and no-claim/private-trace boundaries.
- Added checked-in Lattice Estimator pin manifest at `docs/lattice_estimator_manifest.json` plus `agades-pqc lattice-estimator-manifest`, CI regeneration, NVIDIA/publication-manifest references, and a blocking release-audit pin sync gate. The pin records upstream `malb/lattice-estimator` commit `6019056011d10d7e9c30a0d5da2d2f729fbc2eec` as an optional adapter boundary, not a public security claim.
- Added `agades-pqc lattice-estimator-manifest-verify` and a CI/release-audit gate that rejects upstream pin drift, missing runtime commit enforcement, fake NTRU/SIS estimator enablement, unsafe public-claim flags, and stale manifest release gates.
- Added checked-in public benchmark v0 manifest at `docs/public_benchmark_manifest.json` plus `agades-pqc public-benchmark-manifest` and `agades-pqc public-benchmark-verify`, CI regeneration/verification, GitHub/NVIDIA/publication-manifest references, and a blocking release-audit benchmark sync gate covering all public run bundles and public records without private traces or security claims.
- Added checked-in benchmark source contracts at `docs/benchmark_source_contracts.json` plus `agades-pqc benchmark-source-contracts`, keeping TAPAS, LWE-benchmarking, Hugging Face PQC/SCA dataset anchors, NIST HQC/BIKE/Classic McEliece status anchors, PQ Code Package, liboqs, pqm4, NIST ACVP, dudect, ctgrind, and TIMECOP/SUPERCOP sources as future reviewed adapters with explicit source grounding, methodology, storage/device, GPU/toolchain, parameter/vector provenance, measurement/tool interpretation, redaction, and expert-review gates before any public verifier or accelerator use.
- Added a persisted benchmark-source contract summary covering blocked public surfaces, runtime enablement, review gates, source-catalog links, storage/GPU requirements, and family counts; `agades-pqc benchmark-source-verify` and release audit now reject stale summaries instead of silently accepting drift.
- Added `agades-pqc benchmark-source-verify` and a blocking CI/release-audit gate that rejects benchmark source contracts if future reviewed adapters enable runtime, public verifier access, Prime JSON-only reward surfaces, public benchmark claim surfaces, or omit expert-review gates.
- Expanded the source catalog and benchmark source contracts with future reviewed non-lattice family anchors: NIST HQC standardization track for code-based work, FIPS 205 SLH-DSA for hash-based work, and NIST additional-signature round-three multivariate candidates (`MAYO`, `QR-UOV`, `UOV`). These are planning/review contracts only; they do not enable public verifier runtime or candidate security claims.
- Split BIKE and Classic McEliece into explicit future reviewed source-catalog and benchmark-source-contract entries tied to NIST IR 8545 fourth-round status. They are blocked from the current public verifier and Prime reward environment, and document `not_selected` status rather than any standardization or security claim.
- Expanded DeepEvolve-style PaperCards so every implemented/planned family direction now has at least one `note_only` research hook that can propose review-required operators without certifying results or changing estimator scores.
- Added the first bounded public downscaled LWE instance-solving fixture at `benchmarks/lattice_downscaled_lwe_instances/toy_lwe_n4_q17_instance.json`, mirrored it as package data for standalone verifier environments, and added `lattice_downscaled_lwe_instance_solve_v1`, `reproduction_status="instance_solved"`, Hugging Face/Prime propagation, and schema updates. This is exhaustive-search plumbing for a tiny public fixture, not a deployed-parameter security claim.
- Added the committed public benchmark/bundle for that tiny LWE fixture at `benchmarks/lattice_downscaled_lwe_instance_solve/` and `examples/public_runs/lattice_downscaled_lwe_instance_solve_v0/`, propagated through Hugging Face, Prime-facing cards, NVIDIA, the publication manifest, checksum manifests, and release audit.
- Added a second bounded public downscaled LWE fixture at `benchmarks/lattice_downscaled_lwe_instances/toy_lwe_n5_q19_instance.json`, mirrored it as package data for standalone verifier environments, plus `lattice_downscaled_lwe_instance_solve_n5_q19_v1`, Prime/Hugging Face propagation, and expansion of the `lattice_downscaled_lwe_instance_solve_v0` public run bundle beyond the first record.
- Added a ternary-secret bounded public downscaled LWE fixture at `benchmarks/lattice_downscaled_lwe_instances/toy_lwe_n6_q23_ternary_instance.json`, mirrored it as package data for standalone verifier environments, plus `lattice_downscaled_lwe_instance_solve_n6_q23_ternary_v1`, Prime/Hugging Face propagation, and a regenerated three-record `lattice_downscaled_lwe_instance_solve_v0` public run bundle.
- Made `agades-pqc benchmark` overwrite its output trace instead of appending, so deterministic public benchmark regeneration cannot duplicate records when the same command is rerun.
- Added a family-agnostic `AssumptionSet` core model with deterministic unique assumption summaries, occurrence counts, risk scoring, and stable fingerprints; cascade metrics, public verifier features, Prime/Hugging Face schemas, and public bundles now expose those structured assumption features.
- Added a family-agnostic, schema-versioned `EvaluatorResult` core model and made the legacy `EstimatorResult` API an alias of that contract; public verifier outputs and Prime/Hugging Face schemas now expose the evaluator-result schema version.
- Promoted fitness output to a family-agnostic, schema-versioned `FitnessReport` core model returned by `compute_fitness`, with public trace metrics carrying `fitness_schema_version` for reproducible downstream consumers.
- Promoted `TraceRecord` to a family-agnostic, schema-versioned core model while keeping the legacy `agades_pqc_gym.traces.schema.TraceRecord` import as an alias for trace/export compatibility.
- Promoted reporting to a family-agnostic `ReportGenerator` that accepts typed `TraceRecord` objects or JSON-compatible trace rows, summarizes family/target/reproduction/estimator status, and redacts private target, family, attack, and mutation details by default in public Markdown reports.
- Tightened `TraceRecord` public redaction so non-public records no longer expose private acceptance, scores, estimator labels, raw evaluator output, warnings, or feature fields in public JSONL, ledgers, or Markdown reports.
- Added the first positive non-lattice reproduction harness: `CODE_BASED` toy ISD plans can now solve an explicit public binary syndrome-decoding fixture under `benchmarks/code_based_toy_isd/fixtures/`, returning `instance_solved` for the bounded no-claim public benchmark bundle.
- Added a second public code-based syndrome-decoding fixture, `toy_syndrome_15_7_w2`, mirrored it as package data, exposed it through Hugging Face and Prime Intellect examples, and regenerated `code_based_toy_isd_v0` with two accepted no-claim records.
- Added a bounded code-based quasi-cyclic rotation toy surface: `qc_rotation_toy` with explicit block-shape validation, a public `toy_qc_syndrome_21_12_w2` fixture, checkout/package fixture resolution, and no-claim reproduction through the `code_based_toy_isd_v0` bundle. This is not an HQC result.
- Added a bounded code-based HQC-inspired repetition-code fixture surface: `decoding_fixture_check` with `variant="hqc_repetition_toy"`, a dedicated `toy-code-based-repetition-decoder-estimator`, a public `toy_hqc_repetition_21_7_w3` fixture, checkout/package fixture resolution, and no-claim reproduction through the new `code_based_toy_hqc_v0` bundle. This is not an HQC result.
- Added a second bounded code-based HQC-inspired fixture surface: `decoding_fixture_check` with `variant="hqc_parity_check_toy"`, a dedicated `toy-code-based-parity-check-decoder-estimator`, a public `toy_hqc_parity_check_15_7_w2` parity-check/syndrome fixture, checkout/package fixture resolution, Prime/Hugging Face propagation, and no-claim reproduction through the `code_based_toy_hqc_v0` bundle. This is not an HQC result.
- Added a third bounded code-based HQC-inspired fixture surface: `decoding_fixture_check` with `variant="hqc_circulant_syndrome_toy"`, a dedicated `toy-code-based-circulant-syndrome-decoder-estimator`, a public `toy_hqc_circulant_syndrome_16_8_w2` double-block circulant syndrome fixture, checkout/package fixture resolution, Prime/Hugging Face propagation, and no-claim reproduction through the three-record `code_based_toy_hqc_v0` bundle. This is not an HQC result.
- Added bounded code-based MDPC/BIKE-inspired fixture surfaces: `decoding_fixture_check` with `variant="mdpc_bit_flip_toy"` and `variant="mdpc_black_gray_bit_flip_toy"`, a dedicated `toy-code-based-bit-flip-decoder-estimator`, public `toy_mdpc_bit_flip_12_6_w2` and `toy_mdpc_black_gray_12_6_w2` parity-check fixtures, checkout/package fixture resolution, Prime/Hugging Face propagation, and no-claim reproduction through the two-record `code_based_toy_mdpc_v0` bundle. This is not a BIKE result.
- Added a bounded code-based Classic-McEliece-inspired binary syndrome fixture surface: `decoding_fixture_check` with `variant="classic_mceliece_syndrome_toy"`, a dedicated `toy-code-based-classic-mceliece-syndrome-estimator`, a public `toy_classic_mceliece_syndrome_17_9_w2` fixture, checkout/package fixture resolution, Prime/Hugging Face/NVIDIA propagation, and no-claim reproduction through the new `code_based_toy_classic_mceliece_v0` bundle. This is not a Classic McEliece result.
- Added a bounded code-based Classic-McEliece-inspired public support-set syndrome fixture surface: `decoding_fixture_check` with `variant="classic_mceliece_support_syndrome_toy"`, a dedicated `toy-code-based-classic-mceliece-support-syndrome-estimator`, a public `toy_classic_mceliece_support_syndrome_19_10_w2` fixture, checkout/package fixture resolution, Prime/Hugging Face/NVIDIA propagation, and no-claim reproduction through the two-record `code_based_toy_classic_mceliece_v0` bundle. This is not a Classic McEliece result.
- Added public code-based Classic McEliece-like and BIKE-like schema-only AttackPlans plus `benchmarks/code_based_schema_only/` seeds; both validate shape/routing but return `evaluation_status="unsupported"` through `code-based-placeholder-estimator` with no time or memory estimate.
- Added a bounded code-based BJMM-style representation-merge toy variant: `information_set_decoding` with `variant="bjmm_toy"`, explicit `bjmm_isd_representation_merge_model`, bounded `p`, `ell`, and `representation_count` validation, a public AttackPlan, a public benchmark seed, a Prime packaged task, a family-operator-catalog entry, and a regenerated seven-record `code_based_toy_isd_v0` bundle. This is not a code-based security claim.
- Added a second positive non-lattice reproduction harness: `MULTIVARIATE` toy MQ exhaustive-search plans can now solve an explicit public binary `GF(2)` fixture under `benchmarks/multivariate_toy_mq/fixtures/`, mirrored as package data for installed verifier use, returning `instance_solved` for the bounded no-claim public benchmark bundle while keeping `GF(16)` estimator-only.
- Added public `GF(2)` reproduction for the bounded multivariate MQ hybrid-search surface using the same reviewed fixture and a bounded guess-prefix split-search harness that honors `guessed_variables`, without making a Groebner-basis, UOV/MAYO/Rainbow, or security claim.
- Added a sixth positive non-lattice reproduction harness: `MULTIVARIATE` toy MinRank plans can now solve an explicit public binary `GF(2)` matrix-pencil fixture under `benchmarks/multivariate_toy_minrank/fixtures/`, mirrored as package data for installed verifier use, returning `instance_solved` for the bounded no-claim public benchmark bundle.
- Expanded the multivariate MinRank public fixture set with a second `GF(2)` matrix-pencil fixture at `target_rank=1`, plus a public AttackPlan, Prime task, Hugging Face row, and regenerated two-record `multivariate_toy_minrank_v0` bundle. This remains bounded fixture plumbing only, not a UOV/MAYO/Rainbow result.
- Added a third positive non-lattice reproduction harness: `HASH_BASED` toy preimage plans can now solve an explicit public SHAKE256 fixture under `benchmarks/hash_based_toy_bound/fixtures/`, mirrored as package data for installed verifier use, returning `instance_solved` for the bounded no-claim public benchmark bundle.
- Added a fourth positive non-lattice reproduction harness: `IMPLEMENTATION_SECURITY` toy KAT plans can verify an explicit public JSON-only fixture under `benchmarks/implementation_security_toy_kat/fixtures/`, mirrored as package data for installed verifier use, returning `instance_solved` without executing artifacts or making conformance, side-channel, or security claims.
- Added an additional implementation-security reproduction harness: toy timing plans can verify an explicit public JSON-only timing fixture under `benchmarks/implementation_security_toy_timing/fixtures/`, mirrored as package data for installed verifier use, returning `instance_solved` without executing artifacts, reading live traces, or making constant-time/side-channel/security claims.
- Added an additional implementation-security reproduction harness: toy ACVP-like plans can verify an explicit public JSON-only vector-set fixture under `benchmarks/implementation_security_toy_kat/fixtures/`, mirrored as package data for installed verifier use, returning `instance_solved` without executing artifacts or making ACVP/conformance/security claims.
- Added an additional implementation-security reproduction harness: toy benchmark-summary, binary-size, memory-footprint, and stack-usage plans can verify explicit public JSON-only benchmark fixtures under `benchmarks/implementation_security_toy_benchmark/fixtures/`, mirrored as package data for installed verifier use, returning `instance_solved` without executing artifacts or making binary-size/memory-usage/stack-usage/performance/conformance/side-channel/security claims.
- Added a fifth positive non-lattice reproduction harness: `ISOGENY_HISTORICAL` toy path plans can verify an explicit public historical path fixture under `benchmarks/isogeny_historical_toy_path/fixtures/`, mirrored as package data for installed verifier use, returning `instance_solved` without solving isogeny problems or making current-standard/security claims.
- Expanded that historical-isogeny reproduction harness with an explicit public commutative-walk fixture under `benchmarks/isogeny_historical_toy_path/fixtures/`, mirrored as package data for installed verifier use and still limited to path-shape/no-claim verification.
- Added `agades_pqc_gym.evolution.archive` and `agades-pqc evolve-batch`, giving the MVP a deterministic local MAP-Elites-style archive over accepted `AttackPlan` evaluations while keeping arbitrary Python candidates unsupported.
- Added `agades_pqc_gym.evolution.mutation` and `agades-pqc mutate-candidates`, giving the OpenEvolve loop a deterministic private JSON-only candidate mutation batch for reviewed LWE/MLWE knobs (`beta`, `block_size`, `q_prime`, and `zeta`) plus reviewed non-lattice toy knobs while skipping schema-only, fixture-bound, or unsupported families and preserving the no-claim boundary.
- Added `agades-pqc mutate-archive`, giving MAP-Elites archive elites a deterministic next-generation mutation path from exact source `TraceRecord` parents while preserving private candidate status, parent candidate IDs, parent trace IDs, and the no-arbitrary-code boundary.
- Added `agades-pqc openevolve-config` and expanded the importable `agades_pqc_gym.openevolve_adapter.DEFAULT_CONFIG_TEMPLATE` so packaged OpenEvolve integrations can materialize the same private paper-card injection/seed/archive/next-generation/held-out loop as `examples/openevolve/config.yaml`.
- Added `agades_pqc_gym.evolution.rescore` and `agades-pqc rescore-archive`, giving archive elites a deterministic held-out rescore report over explicit private `TraceRecord.parent_id` links without retargeting plans, executing arbitrary candidate code, or publishing private traces. Release audit now includes a blocking smoke gate for this plumbing.
- Added `agades_pqc_gym.evolution.heldout` and `agades-pqc heldout-batch`, giving archive elites a private same-family held-out re-evaluation runner that rebases only reviewed `TargetSpec` values, refuses pre-evaluation claims and target-specific reproduction constraints, writes linked held-out traces, and emits a rescore report.
- Added `agades_pqc_gym.evolution.scheduler`, `agades-pqc heldout-review-log`, and `agades-pqc heldout-schedule`, producing a durable private approval log and reviewed private held-out schedule manifest with a review-log digest from the checked-in private-run policy before automated held-out work can run.
- Added `agades_pqc_gym.evolution.cron` and `agades-pqc heldout-cron-plan`, producing private local-cron plans for already-reviewed `local_cron_after_review` manifests without editing the system crontab or weakening review-log, no-network, or private-output boundaries.
- Added `agades-pqc heldout-run-schedule`, consuming reviewed private schedule manifests through typed Python APIs while rechecking review-log digest stability and without executing stored shell command strings, external networking, or public trace outputs.
- Added `agades_pqc_gym.evolution.heldout_review_packet`, `agades-pqc heldout-review-packet`, and `agades-pqc heldout-review-packet-verify`, giving scheduled held-out runs a private digest-only review handoff that references schedule, trace, and rescore artifacts without exposing trace payloads, AttackPlans, candidate sources, or private scores.
- Added `agades_pqc_gym.evolution.snapshot` and `agades-pqc archive-snapshot`, producing private digest-only archive snapshot manifests with file digests, review-log evidence, retention metadata, and archive-to-trace link integrity while excluding trace payloads, AttackPlans, candidate source, external networking, and public release semantics.
- Expanded the benchmark source contracts for the future Agades PQC Implementation Lab: liboqs test/benchmark harnesses, pqm4 Cortex-M4 benchmarking, NIST ACVP PQC vectors, dudect statistical timing tests, ctgrind secret-taint checks, and TIMECOP/SUPERCOP policy checks are now machine-readable future-reviewed contracts, all blocked from the JSON-only public verifier and Prime reward environment until toolchain, device/vector provenance, measurement protocol, tool-interpretation, redaction, and expert-review gates exist.
- Added PQ Code Package as a future reviewed implementation-security source anchor and benchmark-source contract for native ML-KEM/ML-DSA workflows. It records `mlkem-native`/`mldsa-native`, FIPS 203/204 scope, ACVP/source/toolchain/constant-time review gates, and remains blocked from the JSON-only public verifier, Prime reward environment, and public benchmark claim surface.
- Packaged the code-based toy syndrome fixture under `src/agades_pqc_gym/families/code_based/fixtures/` and aligned its resolver with other non-lattice reproduction harnesses: checkout fixture first, package fixture fallback for installed environments, and strict rejection of traversal or out-of-scope fixture paths.
- Added a shared public fixture resolver for reproduction harnesses, centralizing one-file fixture scoping, checkout-first/package-fallback behavior, traversal rejection, and symlink-escape protection across lattice, code-based, multivariate, hash-based, historical-isogeny, and implementation-security adapters.
- Added a checked-in release status summary at `docs/release_status.json` plus `agades-pqc release-status`, reconciling release audit, public benchmark, publication, Hugging Face, Prime Intellect, and NVIDIA counts without creating a recursive publication digest.
- Added `agades-pqc release-status-verify` as a standalone CI gate for `docs/release_status.json`, so the public OSS status summary is checked without making release audit generation recursive.
- Added a checked-in conservative publication preflight at `public/publication_preflight.json` plus `agades-pqc publication-preflight` / `agades-pqc publication-preflight-verify`, keeping external Hugging Face, Prime Intellect, and NVIDIA-facing publication blocked until explicit release review and credential review are approved.
- Added `docs/external_publication_review_packet.json` plus `agades-pqc external-publication-review-packet` / `agades-pqc external-publication-review-packet-verify`, giving release reviewers a digest-backed cross-surface handoff for Hugging Face, Prime Intellect, and NVIDIA while preserving the default no-publication/no-credentials/no-security-claim boundary.
- Added a checked-in private-run policy at `docs/private_run_policy.json` plus `agades-pqc private-run-policy` / `agades-pqc private-run-policy-verify`, making the private evolution trace roots, forbidden public roots, holdback list, scheduler triggers, retention limits, approval gates, execution-safety defaults, and redaction/preflight controls machine-readable before any future private run collection.
- Added `agades-pqc runbook-audit` plus a blocking release-audit gate for runbook-required architecture docs, collaboration briefs, Hugging Face/Prime/NVIDIA surfaces, machine-readable manifests, current `agades-pqc-gym` naming, and open-core/private-moat boundaries. The command also accepts `--brief` for optional digest-anchored verification of a user-provided long-running brief against the v3 multi-family core/plugin requirements, and `--context` for digest-anchored verification of the project-context transcript themes around TAPAS/LWE-benchmarking, implementation-security seeds, evaluator gates, OpenEvolve/DeepEvolve, ecosystem visibility, and private-moat boundaries.
- Added a checked-in family operator/evaluator catalog at `docs/family_operator_catalog.json` plus `agades-pqc family-operator-catalog`, documenting per-family validator boundaries, estimator names, required assumptions, fixture scopes, review gates, and a blocking release-audit guard against non-lattice Lattice Estimator reuse or schema-only runtime entries.
- Added a persisted family-operator catalog summary covering validator diversity, operator-bearing families, support-level counts, schema-only runtime absence, and Lattice Estimator usage boundaries; `agades-pqc family-operator-catalog-verify` and release audit now reject stale summaries instead of silently accepting drift.
- Added explicit plugin validator modules for `code_based`, `multivariate`, `hash_based`, `isogeny_historical`, and `implementation_security`; family operator and registry manifests now point at those `families/<plugin>/validators.py` functions instead of adapter classes.
- Added explicit importable plugin descriptors at `families/<plugin>/plugin.py`; the family operator catalog and runtime registry manifest now derive plugin ownership, support levels, and validator paths from those descriptors instead of separate integration-local maps.
- Added the checked-in family plugin manifest as the public descriptor-layer contract; publication, source-catalog, release-audit, and CI gates now verify it alongside the registry and operator catalog.
- Tightened the optional Lattice Estimator adapter so backend commit metadata must match the checked-in reviewed pin before any real estimator call is made; missing or mismatched metadata now returns `evaluation_status="error"` without producing an estimate, and the manifest records that runtime enforcement.
- Added `docs/lattice_estimator_baseline_contracts.json` plus `agades-pqc lattice-estimator-baseline-contracts`, recording `review_contract_ready_not_reproduced` contracts for every reviewed direct LWE mapping. This is not a numeric Lattice Estimator baseline reproduction; numeric reference outputs, publication, and security claims remain blocked until expert review and a matching pinned backend.
- Added `agades_pqc_gym.integrations.lattice_estimator_baseline_run` plus `agades-pqc lattice-estimator-baseline-run`, writing private pin-checked LWE baseline-run reports under `private/reports/` with numeric outputs kept private, raw estimator payloads represented by SHA-256 digests only, and publication/security flags kept false.
- Added `--estimator-source` support for private Lattice Estimator baseline runs. The adapter now verifies `git rev-parse HEAD`, `git remote get-url origin`, `git status --porcelain`, and the estimator entrypoint for a local upstream checkout before importing `estimator`, so mismatched, wrong-origin, dirty, or incomplete checkouts fail before executing upstream Python.
- Added public implementation-security schema-only AttackPlans and benchmark entries for PQClean KATs, liboqs test/benchmark workflows, pqm4 Cortex-M4 benchmarking, and PQ Code Package native ML-KEM/ML-DSA workflows. They are visible in Hugging Face, Prime Verifiers, and local benchmark surfaces but return `unsupported`, execute no upstream code or devices, and make no conformance, side-channel, performance, or security claim.
- Added a public implementation-security schema-only AttackPlan and benchmark entry for the real NIST ACVP PQC vector-source placeholder `nist_acvp_pqc_vectors_schema`. It is visible in Hugging Face, Prime Verifiers, and local benchmark surfaces but returns `unsupported`, does not contact an ACVP server or execute ACVP/CAVP vector workflows, and makes no ACVP, conformance, side-channel, or security claim.
- Added public implementation-security schema-only AttackPlans and benchmark entries for dudect timing-leakage, ctgrind secret-taint, and TIMECOP/SUPERCOP policy-check source contracts. They are visible in Hugging Face, Prime Verifiers, and local benchmark surfaces but return `unsupported`, execute no timing/taint/policy tools, and make no constant-time, side-channel, or security claim.
- Bumped Prime/Hugging Face task metadata to `agades.pqc.task_metadata.v2`, adding seed verifier status and seed reward fields so schema-only `unsupported` tasks are explicit zero-reward routing/safety checks rather than ambiguous accepted examples.
- Bumped Prime/Hugging Face task metadata to `agades.pqc.task_metadata.v4`, adding seed AttackPlan SHA-256 digests, seed estimator, and seed reproduction status fields so fixture-backed tasks are inspectable in Prime/Hugging Face rows without changing task-aware scoring or adding claims.
- Added explicit Hugging Face valid/invalid/task-metadata/Prime-eligible row counts to `dataset_info.json`, release status, release audit, and runbook audit evidence so the intentional invalid validator fixture explains the one-row difference between Hugging Face rows and Prime Verifiers tasks.
- Added explicit Hugging Face Space selector counts to `hf/space_manifest.json`, release audit, and release status so Space-visible valid examples are tied to the dataset row count and the intentional invalid validator fixture exclusion.
- Added a derived NVIDIA workload summary to `nvidia/accelerator_manifest.json`, release audit, and release status so the current workloads are explicitly CPU/no-GPU while the single GPU-required workload remains `reserved_future`.
- Added source-catalog ecosystem evidence to `docs/release_status.json`, surfacing the OSS anchors across GitHub, Hugging Face, NIST, NVIDIA, and Prime Intellect along with current public surfaces, future reviewed adapters, and source-map-only partnership references.
- Added `docs/source_catalog.json` as a digest-tracked GitHub repository artifact in `docs/publication_manifest.json`, so the OSS anchor map is part of the public publication contract rather than only a release gate.
- Added `prime_intellect/schemas/task_metadata.schema.json` as a digest-tracked Prime publication artifact, keeping the task metadata/reward contract visible alongside the AttackPlan, verifier-result, and schema-manifest contracts.
- Added `prime_intellect/schemas/task_metadata.schema.json` to the blocking ecosystem release-plan schema-artifact gate, aligning the Hugging Face/Prime/NVIDIA planning proof with the Prime task metadata contract.
- Added a Prime source-mirror contract to `prime_manifest.json` and release audit evidence, proving the packaged Prime data files exactly mirror all valid public `examples/attack_plans` rows.
- Strengthened the blocking ecosystem release-plan gate so Hugging Face, Prime Intellect, and NVIDIA plans must all cover Prime Quickstart, auto-nanoGPT, and `experiments-autonomous-speedrunning` as source-map-only ecosystem anchors without claiming a Prime training run.
- Surfaced that Prime ecosystem release-plan coverage in `docs/release_status.json`, so quick OSS review can see the three Prime anchors and their per-plan coverage without opening the full release audit.
- Added a dedicated Hugging Face `task_metadata.jsonl` export for the valid public task metadata rows, listed it in the publication manifest, and made release audit verify it matches the embedded AttackPlan metadata.
- Added a shared deterministic task-metadata summary to Hugging Face `dataset_info.json` and Prime `prime_manifest.json`, covering family, support-level, seed verifier status/reward, seed estimator, and reproduction-status counts for OSS review without changing scoring.
- Added Hugging Face PQC/SCA dataset anchors to `docs/source_catalog.json` for `AYI-NEDJIMI/post-quantum-crypto-fr`, `AYI-NEDJIMI/post-quantum-crypto-en`, `Q-GRID/pqc-ssl-scans`, and `SCA-HNUST/SC2026`; they are future reviewed dataset inputs only, not current verifier/training surfaces or security claims.
- Added benchmark-source contracts for those Hugging Face PQC/SCA dataset anchors. The instruction datasets require source grounding/license/bias review, `Q-GRID/pqc-ssl-scans` requires migration-scoring methodology review, and `SCA-HNUST/SC2026` requires trace provenance, hardware scope, leakage-model, and disclosure review before any public verifier, Prime reward, benchmark, or NVIDIA-facing workload use.
- Added a bounded HQC-inspired weighted repetition toy decoder, public fixture, AttackPlan, benchmark seed, Prime task, family operator catalog entry, and regenerated the four-record `code_based_toy_hqc_v0` bundle. This is reliability-weighted repetition-code plumbing only, not an HQC result or security claim.
- Added a bounded HQC-inspired erasure-aided syndrome toy decoder, public fixture, AttackPlan, benchmark seed, Prime/Hugging Face/NVIDIA propagation, family operator catalog entry, and regenerated the five-record `code_based_toy_hqc_v0` bundle. This is erasure-position syndrome plumbing only, not an HQC result or security claim.
- Added a bounded HQC-inspired circulant-erasure toy decoder, public fixture, AttackPlan, benchmark seed, Prime/Hugging Face/NVIDIA propagation, family operator catalog entry, and regenerated the six-record `code_based_toy_hqc_v0` bundle. This is erasure-constrained circulant-syndrome plumbing only, not an HQC result or security claim.

Final validation:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
uv build
uv build prime_intellect/verifiers_environment
uv run pytest tests/test_release_audit.py -q
uv run pytest tests/test_public_release_cards.py -q
uv run pytest tests/test_huggingface_dataset_bundle.py -q
uv run pytest tests/test_nvidia_accelerator_manifest.py -q
uv run agades-pqc nvidia-manifest --out nvidia/accelerator_manifest.json
uv run agades-pqc nvidia-manifest-verify --manifest nvidia/accelerator_manifest.json
uv run pytest tests/test_deepevolve_hooks.py -q
uv run pytest tests/test_public_verifier.py tests/test_cli.py -q
uv run pytest tests/test_prime_verifiers_env.py -q
uv run pytest tests/test_lattice_adapter.py tests/test_cascade.py tests/test_public_verifier.py tests/test_huggingface_dataset_bundle.py -q
uv run agades-pqc verify examples/attack_plans/lattice_primal_usvp_toy.json
uv run agades-pqc verify examples/attack_plans/lattice_downscaled_lwe_instance_solve_toy.json
uv run agades-pqc validate examples/attack_plans/lattice_primal_usvp_toy.json
uv run agades-pqc validate examples/attack_plans/code_based_isd_placeholder.json
uv run agades-pqc validate examples/attack_plans/implementation_security_constant_time_placeholder.json
uv run agades-pqc benchmark benchmarks/lattice_toy_lwe --out runs/v3_toy_benchmark.jsonl
uv run agades-pqc public-ledger runs/v3_toy_benchmark.jsonl --out public/v3_toy_run_ledger.json
uv run agades-pqc public-bundle runs/v3_toy_benchmark.jsonl --out public/v3_toy_run_bundle
uv run agades-pqc source-catalog --out docs/source_catalog.json
uv run agades-pqc source-catalog-verify --catalog docs/source_catalog.json
uv run agades-pqc deepevolve-manifest --out docs/deepevolve_research_hooks_manifest.json
uv run agades-pqc deepevolve-manifest-verify --manifest docs/deepevolve_research_hooks_manifest.json
uv run agades-pqc benchmark-source-contracts --out docs/benchmark_source_contracts.json
uv run agades-pqc benchmark-source-verify --contracts docs/benchmark_source_contracts.json
uv run agades-pqc family-support --out docs/family_support_matrix.json
uv run agades-pqc family-support-verify --matrix docs/family_support_matrix.json
uv run agades-pqc family-operator-catalog --out docs/family_operator_catalog.json
uv run agades-pqc family-operator-catalog-verify --catalog docs/family_operator_catalog.json
uv run agades-pqc hf-dataset --out hf/dataset
uv run agades-pqc hf-dataset-verify --dataset hf/dataset
uv run agades-pqc lattice-estimator-manifest --out docs/lattice_estimator_manifest.json
uv run agades-pqc lattice-estimator-manifest-verify --manifest docs/lattice_estimator_manifest.json
uv run agades-pqc public-benchmark-manifest --out docs/public_benchmark_manifest.json
uv run agades-pqc public-benchmark-verify --manifest docs/public_benchmark_manifest.json
uv run agades-pqc hf-space-manifest --out hf/space_manifest.json
uv run agades-pqc hf-space-manifest-verify --manifest hf/space_manifest.json
uv run agades-pqc hf-collection-manifest --out hf/collection_manifest.json
uv run agades-pqc hf-collection-manifest-verify --manifest hf/collection_manifest.json
uv run agades-pqc publication-manifest --out docs/publication_manifest.json
uv run agades-pqc publication-manifest-verify --manifest docs/publication_manifest.json
uv run agades-pqc private-run-policy --out docs/private_run_policy.json
uv run agades-pqc private-run-policy-verify --policy docs/private_run_policy.json
uv run agades-pqc openevolve-config --out examples/openevolve/config.yaml
uv run agades-pqc openevolve-config-verify --config examples/openevolve/config.yaml
uv run agades-pqc prime-manifest --out prime_intellect/verifiers_environment/prime_manifest.json
uv run agades-pqc prime-manifest-verify --manifest prime_intellect/verifiers_environment/prime_manifest.json
uv run agades-pqc prime-schemas --out prime_intellect/schemas
uv run agades-pqc prime-schemas-verify --schemas prime_intellect/schemas
uv run agades-pqc prime-publication-handoff --out docs/prime_publication_handoff.json
uv run agades-pqc prime-publication-handoff-verify --handoff docs/prime_publication_handoff.json
uv run agades-pqc release-audit --out public/release_audit.json
uv run agades-pqc release-status --out docs/release_status.json
uv run agades-pqc release-status-verify --status docs/release_status.json
uv run agades-pqc publication-preflight --out public/publication_preflight.json
uv run agades-pqc publication-preflight-verify --preflight public/publication_preflight.json
uv run agades-pqc runbook-audit --out /tmp/agades_runbook_audit.json
uv build prime_intellect/verifiers_environment
uv run agades-pqc benchmark benchmarks/code_based_schema_only --out runs/v3_code_based_schema.jsonl
uv run agades-pqc benchmark benchmarks/code_based_toy_isd --out runs/code_based_toy_isd.jsonl
uv run agades-pqc public-bundle runs/code_based_toy_isd.jsonl --out examples/public_runs/code_based_toy_isd_v0
uv run agades-pqc benchmark benchmarks/code_based_toy_hqc --out runs/code_based_toy_hqc.jsonl
uv run agades-pqc public-bundle runs/code_based_toy_hqc.jsonl --out examples/public_runs/code_based_toy_hqc_v0
uv run agades-pqc benchmark benchmarks/code_based_toy_mdpc --out runs/code_based_toy_mdpc.jsonl
uv run agades-pqc public-bundle runs/code_based_toy_mdpc.jsonl --out examples/public_runs/code_based_toy_mdpc_v0
uv run agades-pqc benchmark benchmarks/hash_based_toy_bound --out runs/hash_based_toy_bound.jsonl
uv run agades-pqc public-bundle runs/hash_based_toy_bound.jsonl --out examples/public_runs/hash_based_toy_bound_v0
uv run agades-pqc benchmark benchmarks/hash_based_toy_signature --out runs/hash_based_toy_signature.jsonl
uv run agades-pqc public-bundle runs/hash_based_toy_signature.jsonl --out examples/public_runs/hash_based_toy_signature_v0
uv run agades-pqc benchmark benchmarks/multivariate_toy_mq --out runs/multivariate_toy_mq.jsonl
uv run agades-pqc public-bundle runs/multivariate_toy_mq.jsonl --out examples/public_runs/multivariate_toy_mq_v0
uv run agades-pqc benchmark benchmarks/multivariate_toy_minrank --out runs/multivariate_toy_minrank.jsonl
uv run agades-pqc public-bundle runs/multivariate_toy_minrank.jsonl --out examples/public_runs/multivariate_toy_minrank_v0
uv run agades-pqc benchmark benchmarks/multivariate_toy_uov --out runs/multivariate_toy_uov.jsonl
uv run agades-pqc public-bundle runs/multivariate_toy_uov.jsonl --out examples/public_runs/multivariate_toy_uov_v0
uv run agades-pqc benchmark benchmarks/implementation_security_toy_kat --out runs/implementation_security_toy_kat.jsonl
uv run agades-pqc public-bundle runs/implementation_security_toy_kat.jsonl --out examples/public_runs/implementation_security_toy_kat_v0
uv run agades-pqc benchmark benchmarks/implementation_security_toy_timing --out runs/implementation_security_toy_timing.jsonl
uv run agades-pqc public-bundle runs/implementation_security_toy_timing.jsonl --out examples/public_runs/implementation_security_toy_timing_v0
uv run agades-pqc benchmark benchmarks/implementation_security_schema_only --out runs/v3_implementation_security_schema.jsonl
uv run agades-pqc benchmark benchmarks/isogeny_historical_toy_path --out runs/isogeny_historical_toy_path.jsonl
uv run agades-pqc public-bundle runs/isogeny_historical_toy_path.jsonl --out examples/public_runs/isogeny_historical_toy_path_v0
uv run agades-pqc benchmark benchmarks/lattice_downscaled_lwe_instance_solve --out runs/lattice_downscaled_lwe_instance_solve.jsonl
uv run agades-pqc public-bundle runs/lattice_downscaled_lwe_instance_solve.jsonl --out examples/public_runs/lattice_downscaled_lwe_instance_solve_v0
uv run agades-pqc mutate-candidates benchmarks/lattice_toy_lwe/lwe_n64_q257.json --out runs/candidate_mutations --generation 1 --max-mutations-per-plan 4
uv run agades-pqc deepevolve-injections --out private/candidates/paper_card_injections.json --policy docs/private_run_policy.json --paper-card-dir examples/paper_cards
uv run agades-pqc evolve-batch benchmarks/lattice_downscaled_lwe_instance_solve --trace-out runs/evolution_trace.jsonl --archive-out runs/evolution_archive.json
uv run agades-pqc evolve-batch runs/candidate_mutations/plans --trace-out runs/mutated_evolution_trace.jsonl --archive-out runs/mutated_evolution_archive.json
uv run agades-pqc mutate-archive runs/evolution_archive.json runs/evolution_trace.jsonl --out runs/archive_mutations --max-mutations-per-elite 4
uv run agades-pqc evolve-batch runs/archive_mutations/plans --trace-out runs/archive_mutation_trace.jsonl --archive-out runs/archive_mutation_archive.json
uv run agades-pqc evolve-batch benchmarks/lattice_toy_lwe/lwe_n64_q257.json --trace-out runs/heldout_source_trace.jsonl --archive-out runs/heldout_source_archive.json
uv run agades-pqc heldout-review-log --out private/runs/heldout_review_log.json --approval private-run-policy-review --approval heldout-target-review --approval retention-owner-review --approval publication-export-review
uv run agades-pqc archive-snapshot runs/heldout_source_archive.json runs/heldout_source_trace.jsonl --out private/runs/archive_snapshot.json --review-log private/runs/heldout_review_log.json --policy docs/private_run_policy.json
uv run agades-pqc heldout-schedule runs/heldout_source_archive.json runs/heldout_source_trace.jsonl benchmarks/lattice_toy_lwe/lwe_n96_q769.json --out private/runs/heldout_schedule.json --trace-out private/traces/heldout_trace.jsonl --rescore-out private/reports/heldout_rescore.json --review-log private/runs/heldout_review_log.json --trigger local_cron_after_review --approval private-run-policy-review --approval heldout-target-review --approval retention-owner-review --approval publication-export-review
uv run agades-pqc heldout-cron-plan private/runs/heldout_schedule.json --out private/runs/heldout_cron_plan.json --policy docs/private_run_policy.json --minute 17 --every-hours 6 --log-path private/runs/heldout_cron.log
uv run agades-pqc heldout-run-schedule private/runs/heldout_schedule.json --policy docs/private_run_policy.json
uv run agades-pqc heldout-review-packet private/runs/heldout_schedule.json --out private/reports/heldout_review_packet.json --policy docs/private_run_policy.json --reviewer-label local-heldout-review
uv run agades-pqc heldout-review-packet-verify --packet private/reports/heldout_review_packet.json --schedule private/runs/heldout_schedule.json --policy docs/private_run_policy.json
uv run agades-pqc heldout-batch runs/heldout_source_archive.json runs/heldout_source_trace.jsonl benchmarks/lattice_toy_lwe/lwe_n96_q769.json --trace-out runs/heldout_trace.jsonl --rescore-out runs/heldout_rescore.json
uv run agades-pqc verify examples/attack_plans/isogeny_historical_toy.json
```

Current result:

- `764 passed`
- `ruff`: passed
- `git diff --check`: passed
- `uv build`: passed
- `uv build prime_intellect/verifiers_environment`: passed
- Source catalog generated and checked in as `docs/source_catalog.json`.
- Family support matrix generated and checked in as `docs/family_support_matrix.json`.
- Family operator/evaluator catalog generated and checked in as `docs/family_operator_catalog.json`, covering 46 reviewed public operator entries across 9 families.
- Public benchmark v0 manifest generated and checked in as `docs/public_benchmark_manifest.json`.
- Publication manifest generated and checked in as `docs/publication_manifest.json`.
- Hugging Face Collection manifest generated and checked in as `hf/collection_manifest.json`.
- Release audit generated and checked in as `public/release_audit.json` with `56 passed`, `0 failed`, and `1 warning`.
- Release status generated and checked in as `docs/release_status.json`, reconciling 43 runbook-required artifacts, 18 public benchmark bundles, 58 public records, 79 Hugging Face AttackPlan rows, 78 Prime packaged tasks, and 27 NVIDIA workload descriptors.
- Private evolution campaign planning is now available through `agades-pqc private-evolution-campaign-plan`, producing a reviewed, non-executing, private-only argv manifest with seed mutation and complete seed-family held-out coverage preflight counts for seed/archive/snapshot/held-out loops before private trace collection starts.
- Source catalog now exposes the local Prime environment manifest, Prime publication handoff manifest, flat public run export, and NVIDIA accelerator manifest as current public surfaces, while keeping hosted publication and GPU/security claims behind review gates.
- GitHub Actions CI readiness is now a blocking release-audit gate.
- Runbook deliverable audit covers 43 required docs/manifests/reports and cross-checks HF/Prime/NVIDIA/public-benchmark counts plus the no-private-trace/no-security-claim boundary.
- Hugging Face Space smoke loads 78 public examples and evaluates the default LWE plan safely.
- Hugging Face Space manifest gate verifies 78 exposed public examples across 9 families, matches the app selector/default, and blocks drift in reviewed `hf repos create` / `hf upload --repo-type=space` publication commands.
- Hugging Face dataset contains 79 AttackPlan rows including one intentionally invalid public negative-control row.
- Hugging Face dataset now publishes 78 valid public task metadata rows in `task_metadata.jsonl`, and release audit verifies those rows match the embedded `attack_plans.jsonl` task metadata.
- Hugging Face Collection manifest gate verifies 7 reviewed entries across the GitHub repo, dataset, Space, benchmark card, source map, public benchmark manifest, and flat public run export, with 3 credentialed entries and no private traces or security claims.
- Hugging Face publication handoff generated and checked in as `docs/huggingface_publication_handoff.json`, covering 17 local dataset, Space, Collection, source-map, benchmark, run-export, and release-plan artifacts, 78 valid task rows, 18 public run bundles, credential/release-review blockers, and the explicit boundary that no Hugging Face Hub publication has been performed.
- Hugging Face dataset mirrors 18 public run bundles: `code_based_toy_classic_mceliece_v0`, `code_based_toy_hqc_v0`, `code_based_toy_isd_v0`, `code_based_toy_mdpc_v0`, `hash_based_toy_bound_v0`, `hash_based_toy_misuse_v0`, `hash_based_toy_signature_v0`, `implementation_security_toy_benchmark_v0`, `implementation_security_toy_kat_v0`, `implementation_security_toy_timing_v0`, `isogeny_historical_toy_path_v0`, `lattice_downscaled_lwe_instance_solve_v0`, `lattice_downscaled_mlwe_instance_solve_v0`, `lattice_mlwe_downscaled_v0`, `lattice_toy_lwe_v0`, `multivariate_toy_minrank_v0`, `multivariate_toy_mq_v0`, and `multivariate_toy_uov_v0`.
- Prime Verifiers smoke builds 78 task rows, scores the accepted toy plan as `1.0`, and rejects unsupported/prefixed non-JSON submissions as `0.0`.
- Prime publication handoff generated and checked in as `docs/prime_publication_handoff.json`, covering 10 local package/review artifacts, 78 Prime tasks, 9 families, credential/release-review blockers, source-catalog Prime anchors, and the explicit boundary that no Prime Hub publication has been performed.
- Lattice Estimator mapping coverage gate covers 5 direct LWE mappings across public examples, HF rows, and Prime tasks.
- Lattice Estimator pin gate covers the checked-in upstream commit, runtime commit-metadata enforcement, reviewed direct LWE mapping set, NTRU/SIS schema-only boundary, review-before-claim safety flags, and the standalone `lattice-estimator-manifest-verify` release gate.
- Lattice Estimator pin gate now also records the private local-checkout backend contract: `--estimator-source`, commit/origin/clean-tree/entrypoint verification before import, mismatch rejection before import, and release-audit evidence that dirty or wrong-origin checkouts do not import upstream Python.
- Private Lattice Estimator baseline-run gate covers the five reviewed LWE contracts using a pin-matched backend fixture, proving private-only numeric outputs, digest-only raw estimator payloads, LWE-only scope, no public reference outputs, and no security claim.
- Private Lattice Estimator checkout-preflight gate covers a pin-matched local checkout fixture without importing upstream Python or executing estimator code, proving private-only output, Git HEAD readiness, upstream-origin match, clean-tree readiness, and no publication/security claim before a real `--estimator-source` baseline run.
- Public benchmark manifest gate covers 18 local public benchmark v0 bundles, 59 accepted public records, public trace/checksum digests, and regeneration commands without private traces or security claims.
- Evolution mutation, archive-mutation, archive-snapshot, held-out schedule, cron-plan, held-out batch, and rescore gates verify private JSON-only candidate mutation from reviewed lattice knobs (`beta`, `block_size`, `q_prime`, `zeta`), code-based toy ISD knobs (`p`, `ell`, `representation_count`) plus Prange toy target weight (`w`), multivariate toy MQ knobs (`variables`, `equations`, `guessed_variables`, `degree_bound`), hash-based toy preimage digest bits (`n`), implementation-security toy KAT knobs (`vector_count`), and historical-isogeny toy path knobs (`walk_length`, `branching_factor`), schema-only/fixture-bound skip behavior, archive elite parent candidate/trace linkage, digest-only private snapshot retention, reviewed private schedule generation, private local-cron plan generation, private same-family target rebasing, explicit `TraceRecord.parent_id` linkage, one generated held-out candidate, one rescored elite, and no arbitrary code execution.
- Publication manifest gate covers 6 public OSS surfaces, 62 surface artifact SHA-256 digests plus 3 audited derived/recursive digest exclusions, and 18 public run bundles with 72 bundle artifact SHA-256 digests: GitHub repository, Hugging Face dataset, Hugging Face Space, Hugging Face Collection, Prime Verifiers environment, NVIDIA accelerator story, the flat `public/run_export/` JSONL/CSV table, code-based toy Classic-McEliece-inspired binary/support-set syndrome bundle, code-based toy HQC-inspired repetition/weighted-repetition/parity-check/circulant-syndrome/erasure-aided syndrome/circulant-erasure bundle, code-based toy ISD bundle, code-based toy MDPC/BIKE-inspired threshold/black-gray/syndrome-weight bit-flip bundle, hash-based toy bound bundle, hash-based toy misuse bundle, hash-based toy signature bundle, implementation-security toy ML-KEM/ML-DSA KAT/ACVP-like, timing, benchmark-summary, memory-footprint, binary-size, and stack-usage bundles, historical-isogeny toy path bundle, tiny LWE fixture-solving bundle, multivariate toy MQ, MinRank, and UOV public-map verifier bundles, LWE toy run bundle, and downscaled MLWE run bundle.
- Prime environment manifest gate covers 79 packaged tasks across 9 public families, proves they exactly mirror 79 valid public `examples/attack_plans` rows, records the JSON-only reward contract, and blocks drift in local `uv run vf-eval` usage versus Prime Hub push/install commands.
- Prime verifier schema gate covers the checked-in AttackPlan submission schema, task-metadata schema, public verifier result schema, and schema manifest used by Prime, Hugging Face, and CLI wrappers.
- Prime publication handoff gate covers the checked-in local Prime release package, source-catalog Prime anchors, release checklist, credential boundary, and no-external-publication claim boundary.
- Ecosystem release-plan gate covers the Hugging Face, Prime Intellect, and NVIDIA planning docs against 18 public run bundles, 4 Prime/HF schema artifacts in each plan, Prime Quickstart, auto-nanoGPT, the Prime autonomous-speedrunning reference, and explicit no-claim/private-trace publication boundaries.
- Release status now surfaces the same Prime release-plan coverage across Hugging Face, Prime Intellect, and NVIDIA, the Prime handoff readiness evidence, and the source-catalog evidence for the Prime Quickstart, auto-nanoGPT, and autonomous-speedrunning anchors.
- Report generator redaction gate verifies public Markdown reports count private trace rows without exposing private target names, mutation summaries, private scores, or evaluator output.
- Private-run policy gate verifies 4 allowed private roots, 5 forbidden public roots, 12 private commands, 5 required publication controls, 2 allowed scheduler triggers, 4 scheduler approval gates, and 4 retention rules before any private trace artifact can be considered for public export or scheduled held-out re-evaluation.
- Benchmark source contract gate covers 18 future adapters, all blocked from the current public verifier, with 2 large-storage gates and 2 GPU/toolchain gates; the future non-lattice anchors cover HQC, BIKE, Classic McEliece, SLH-DSA, NIST additional-signature multivariate candidates, and Hugging Face PQC/SCA dataset anchors, while the implementation-security anchors cover PQ Code Package, liboqs, pqm4, NIST ACVP vector provenance, dudect timing leakage experiments, ctgrind secret-taint analysis, and TIMECOP/SUPERCOP policy checks without enabling runtime execution.
- NVIDIA manifest safety now covers 18 public artifact pointers, 27 workload descriptors, and 18 public run bundles, including HF Space, HF Collection, Prime environment manifests, Prime verifier schemas, the Lattice Estimator pin manifest, the Lattice Estimator baseline contracts, benchmark source contracts, the public benchmark v0 manifest, the flat public run export, the lattice NTRU/SIS schema-only routing benchmark, the code-based HQC-inspired fixture benchmark, the Classic-McEliece-inspired syndrome and MDPC/BIKE-inspired threshold/black-gray/syndrome-weight bit-flip fixture benchmarks, the hash-bound/misuse/signature and SLH-DSA-like hypertree toy fixture benchmarks, the historical-isogeny path and volcano-style graph/path fixture benchmarks, the multivariate MinRank and UOV public-map verifier fixture benchmarks, the implementation-security timing, benchmark-summary, memory-footprint, binary-size, and stack-usage fixture benchmarks, and the three-record tiny LWE fixture-solving benchmark with the ternary-secret public fixture.
- NVIDIA publication handoff gate covers 16 local accelerator/review artifacts, 26 current CPU workloads, 1 reserved future GPU workload, 18 public run bundles, and explicit no-external-submission/no-GPU-result/no-security-claim boundaries.
- Schema-only applicability gate covers 9 invalid fixtures for code-based, multivariate, hash-based, historical-isogeny, and implementation-security adapters, including implementation-security live-artifact, fake-tool, and schema-fixture naming boundaries.
- Public checksum manifests verify 188 published artifact entries across the Hugging Face dataset, all committed public run bundles, and the flat public run export.
- Public run ledger safety covers 18 bundles and 59 accepted public records across CODE_BASED, HASH_BASED, IMPLEMENTATION_SECURITY, ISOGENY_HISTORICAL, LWE, MLWE, and MULTIVARIATE.
- Lattice toy benchmark generated reportable mock-estimator results.
- Lattice NTRU/SIS schema-only, code-based toy ISD including Prange, Lee-Brickell-style, Stern-style, Dumer-style list-merging, BJMM-style representation-merge, quasi-cyclic rotation variants, HQC-inspired repetition/weighted-repetition/parity-check/circulant-syndrome/erasure-aided syndrome/circulant-erasure fixtures, Classic-McEliece-inspired binary/support-set syndrome fixtures, and the MDPC/BIKE-inspired threshold/black-gray/syndrome-weight bit-flip fixtures, hash-based preimage-bound/collision-bound/signature-chain/Merkle-auth-path/FORS-inspired-auth-path/SLH-DSA-like-hypertree toy surfaces, multivariate toy MQ/hybrid/MinRank/UOV public-map verification, historical-isogeny SIDH/SIKE-style, commutative-walk-style, and volcano-style toy path/graph fixtures, and implementation-security toy ML-KEM/ML-DSA KAT/ACVP-like/timing/dudect-summary/ctgrind-style secret-taint/benchmark-summary/memory-footprint/binary-size/stack-usage benchmarks generated reportable toy or unsupported routing results; schema-only benchmarks returned `evaluation_status="unsupported"` as designed.

Known issues:

- The optional Lattice Estimator adapter maps reviewed LWE-family operators (`primal_usvp`, `bounded_distance_decoding`, `dual_attack`, `dual_hybrid`, `bkw`) to explicit estimator algorithm keys and refuses unsupported mappings instead of fabricating output. Backend commit metadata must match the checked-in reviewed upstream pin before a real estimator call is made, but external expert review is still required before any public security claim. MLWE flattening is warning-gated for expert review.
- Smoke results use `mock-lattice-estimator` and are not cryptanalytic evidence.
- Downscaled reproduction now includes three tiny public LWE fixtures solved by bounded exhaustive search, including one ternary-secret fixture. Broader TAPAS/LWE-benchmarking-style instance harnesses and real implementation-security KAT/ACVP/timing/benchmark/constant-time-tool harnesses are explicitly represented only as future reviewed benchmark source contracts.
- The source catalog is a release-planning map; TAPAS, LWE-benchmarking, HQC, BIKE, Classic McEliece, SLH-DSA, NIST additional-signature candidates, Prime RL, Prime Quickstart, and Prime autonomous-speedrunning ecosystem anchors remain future/reviewed or source-map-only planning inputs unless explicitly implemented elsewhere. PQClean, liboqs, pqm4, PQ Code Package, dudect, ctgrind, and TIMECOP/SUPERCOP now have public schema-only implementation-security placeholders, but their real runtime adapters remain future-reviewed.
- The release audit includes blocking runbook deliverables, GitHub Actions CI, Hugging Face Space smoke, Hugging Face Space manifest sync, Hugging Face publication handoff sync, Prime Verifiers smoke, Prime environment manifest sync, Prime verifier schema sync, Prime publication handoff sync, Prime speedrun handoff sync, NVIDIA manifest artifact coverage, NVIDIA publication handoff sync, Lattice Estimator pin sync, Lattice Estimator baseline-contract sync, private Lattice Estimator baseline-run boundary sync, private Lattice Estimator checkout-preflight boundary sync, lattice runtime-primary boundary sync, public benchmark manifest sync, OpenEvolve config-template sync, DeepEvolve paper-card injection safety, evolution mutation/archive-mutation/archive-snapshot/held-out schedule/schedule-run/review-packet/cron-plan/held-out batch/rescore, ecosystem release-plan sync, report-generator/private-evaluation redaction, private-run policy, Lattice Estimator mapping coverage, schema-only applicability, publication-manifest, checksum-manifest, multi-family readiness, family-support-matrix, family-plugin-manifest, family-operator-catalog, and conservative publication-preflight CI gates, plus one expected non-blocking warning: Prime Hub publication still requires credentials and release review.
- NTRU/SIS have public schema-only lattice examples and benchmarks that return `unsupported` without LWE/MLWE estimator output. Code-based has bounded toy Prange, Lee-Brickell-style, Stern-style, Dumer-style list-merging, BJMM-style representation-merge, and quasi-cyclic rotation ISD-style evaluators plus bounded HQC-inspired repetition/weighted-repetition/parity-check/circulant-syndrome/erasure-aided syndrome/circulant-erasure, Classic-McEliece-inspired binary/support-set syndrome, and MDPC/BIKE-inspired threshold, black-gray, and syndrome-weight bit-flip fixture decoders, three tiny public generic syndrome-decoding reproduction fixtures, two tiny public Classic-McEliece-inspired syndrome fixtures, one tiny public repetition-code fixture, one tiny public weighted-repetition fixture, one tiny public parity-check fixture, one tiny public circulant-syndrome fixture, one tiny public erasure-aided syndrome fixture, one tiny public circulant-erasure fixture, three tiny public MDPC bit-flip fixtures, and explicit unsupported Classic McEliece-like/BIKE-like schema-only routing examples; multivariate has bounded toy MQ exhaustive-search, MQ hybrid-search, MQ degree-bound, MinRank, and UOV-inspired public-map verifier evaluators plus tiny public binary `GF(2)` reproduction fixtures for the explicit MQ exhaustive-search, MQ hybrid-search, MQ degree-bound wrapper, MinRank rank-0/rank-1/rank-2 fixture paths, one UOV-inspired public signature/map fixture, and explicit unsupported UOV-like/MAYO-like/Rainbow-historical schema-only routing examples; hash-based has bounded toy preimage-bound, collision-bound, signature-chain, Merkle-auth-path, FORS-inspired auth-path, SLH-DSA-like hypertree, and reused-salt misuse evaluators plus tiny public SHAKE256 preimage, truncated-collision, chain-verification, Merkle/FORS/hypertree auth-path verification, and reused-salt fixtures; implementation-security has JSON-only toy ML-KEM/ML-DSA KAT digest, ACVP-like vector-set, Welch timing-summary, dudect-summary, ctgrind-style secret-taint summary, benchmark-summary, memory-footprint, binary-size, and stack-usage evaluators plus tiny public no-execution reproduction fixtures and schema-only PQClean/liboqs/pqm4/PQ Code Package source-contract placeholders; historical-isogeny has bounded historical SIDH/SIKE-style, commutative-walk-style, and volcano-style toy path/graph evaluators plus three tiny public historical reproduction fixtures. Real HQC, Classic McEliece, BIKE, deployed-parameter SLH-DSA-style, real UOV/MAYO/Rainbow cryptanalysis, current-standard isogeny, real constant-time, real benchmark-harness execution, real ctgrind execution, and live-artifact public schema placeholders still return `unsupported`.
- `prime_intellect/verifiers_environment/` is packaged and covered by `docs/prime_publication_handoff.json`, but it is not yet pushed to the Prime Environments Hub.

Next step:

- Keep expanding reviewed non-lattice estimators and real benchmark reproductions beyond the current public toy fixtures, especially toward deeper code-based/HQC, Classic McEliece, and BIKE review gates beyond the current bounded Lee-Brickell, Dumer, BJMM-style, quasi-cyclic, repetition-code, weighted-repetition, parity-check, circulant-syndrome, erasure-aided syndrome, Classic-McEliece-inspired binary/support-set syndrome, and MDPC threshold/black-gray/syndrome-weight bit-flip toy models, deeper multivariate MQ/MinRank/UOV-family surfaces beyond the current bounded MQ hybrid, rank-0/rank-1/rank-2 MinRank, and public-map verification toy fixtures, implementation-security, and non-current-standard isogeny research surfaces with explicit expert-review gates.
