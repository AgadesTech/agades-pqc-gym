# Agades PQC Verifier Environment

Prime Verifiers environment skeleton for Agades PQC Gym.

This is a single-turn environment: each rollout asks a model to submit one JSON
`AttackPlan`. The reward function runs the shared public verifier and returns
`1.0` only when the candidate is schema-valid, routed to an implemented family,
accepted by the evaluator, and still matches the current task's
`agades.pqc.task_metadata.v6` identity fields: `target_family`, `target_name`,
`support_level`, ordered `operator_types`, ordered `operator_params`, and ordered
`operator_assumptions`. The candidate may change `attack_plan_id`; it cannot
score by submitting an unrelated valid public plan, by changing attack
parameters in repair tasks, or by dropping required operator hypotheses.
Semantic-mutation tasks are the only exception: they may change operator params
when the challenge explicitly asks for a semantic variant. Rows also expose the
seed AttackPlan SHA-256 digest, seed
verifier status/reward, seed estimator, and seed reproduction status, so
unsupported schema-only tasks are labeled `unsupported`, fixture-backed seeds
are inspectable, and no arbitrary code is executed.

The package embeds every valid public AttackPlan example from the repository,
covering the lattice MVP, bounded toy evaluator examples for code-based,
multivariate, hash-based, historical isogeny, and implementation-security
families, plus schema-only placeholders where reviewed estimators do not exist.
The intentionally invalid validator fixture is not packaged as an evaluation
task.

The default reward profile is `strict`: only a fully accepted, task-matching
AttackPlan receives non-zero aggregate reward. Hosted training can opt into
`reward_profile="pedagogical_dense"`, which keeps the same acceptance rule but
weights JSON-format compliance and the existing verifier sub-scores to avoid a
zero-advantage collapse during private RL. Public evaluation should remain on
`strict`.

The default `prompt_profile="attackplan_json"` is strict about the model output
boundary: if the seed already satisfies the task, return it unchanged; do not
wrap it in markdown, prose, comments, analysis, code fences, or any prefix/suffix
text. The first non-whitespace character must be `{` and the final
non-whitespace character must be `}`.

For private format-curriculum experiments, `prompt_profile="format_repair_extract_seed"`
wraps the seed plan in prose and a markdown fence and asks the model to return
only the repaired JSON object. Pair it with
`reward_profile="format_repair_dense"` for a graded format signal: exact
single-object JSON can still receive full verifier reward when it is readable,
while wrapped or prefixed JSON receives partial private-training reward without
being accepted as a valid final answer. `student_readability` scores the
visible AttackPlan and reviewer-facing notes. Provider-side hidden reasoning is
tracked and quarantined by private reports, but is not mixed into the visible
readability reward.

The `prompt_profile="claims_guard_repair"` curriculum targets a concrete model
failure mode: adding pre-evaluation estimates inside `claims` without reviewed
`external_claim` evidence. It shows the model an invalid public toy AttackPlan
and asks it to restore unknown `null` claims while preserving the rest of the
task. This is a private training/eval curriculum only; public quality claims
still require strict eval.

The `prompt_profile="claims_guard_format_repair"` curriculum combines the two
observed failure modes before another paid training attempt: it wraps the same
invalid-claims AttackPlan in prose and a markdown fence, then requires the model
to extract one JSON object and restore unknown `null` claims. Pair it with
`reward_profile="format_repair_dense"` for a short private format/claims repair
eval. Do not treat high reward on this curriculum as a cryptographic claim; it
only measures AttackPlan formatting and claim-boundary discipline.

The `prompt_profile="claims_guard_decoy_format_repair"` curriculum adds an
AttackPlan-like decoy from a different task before the fenced invalid
AttackPlan. It is intended for private short evals when
`claims_guard_format_repair` is too easy and produces zero rollout variance. A
correct answer must ignore the decoy, extract the fenced AttackPlan, repair
unknown claims back to `null`, and return one JSON object.

For stricter private evals, call `load_environment(..., challenge_suite=True)`.
This does not add private data. It rewrites public seed rows into task-aware
repair challenges and stores the real scoring target under
`info["task_metadata"]`. The current challenge types are
`claims_guard_repair`, `contextual_claims_guard_decoy_repair`,
`semantic_mutation_repair`, `wrong_family_decoy_repair`, `multi_trap_repair`,
`contextual_multi_trap_repair`, `implicit_operator_semantics_repair`,
`operator_mismatch_repair`,
`operator_param_mismatch_repair`, `missing_hypothesis_repair`, and
`invented_complexity_repair` for supported AttackPlans, plus
`unsupported_refusal` for schema-only or unsupported targets. Copying the broken
or decoy object from the prompt does not score; the submitted AttackPlan must
satisfy the nested target metadata, the verifier, the formal bindings, and the
no-claim gate. For `contextual_claims_guard_decoy_repair`, the prompt does not
spell out the exact claim-field edit. The model must use the visible target
metadata, ignore the clean-looking wrong-task decoy, and repair the right-task
AttackPlan back to Agades' conservative no-claim boundary. For
`semantic_mutation_repair`, copying the seed or changing only
metadata does not score; the submitted AttackPlan must make a valid semantic
change while preserving the target and conservative claim boundary. For
`missing_hypothesis_repair`, dropping the seed operator assumptions does not
score. For `operator_param_mismatch_repair`, changing attack parameters instead
of restoring the target task parameters does not score. For
`invented_complexity_repair`, a schema-valid but unreviewed complexity claim
does not score.
For `multi_trap_repair`, the prompt combines a wrong-family decoy with a right-task
AttackPlan that has a wrong operator, missing operator hypothesis, and invented
complexity evidence; all defects must be repaired before the answer can score.
For
`unsupported_refusal`, the correct output is not an
AttackPlan: it is a conservative JSON refusal that names the unsupported target,
sets `claims_pqc_break=false`, and requires human review.
Use `challenge_split="heldout"` for base-model vs adapted-model comparisons;
the train split is only for curriculum work. The held-out split is deterministic
from `(attack_plan_id, challenge_type)` and stays public-safe.
For a broad eval that cannot pass by overfitting one trap type, use
`min_challenge_examples_per_type=8` together with
`challenge_suite=True` and `challenge_split="heldout"`. This builds a stable
balanced held-out suite with the same minimum count for
`claims_guard_repair`, `contextual_claims_guard_decoy_repair`,
`semantic_mutation_repair`, `wrong_family_decoy_repair`, `multi_trap_repair`,
`contextual_multi_trap_repair`, `operator_mismatch_repair`,
`implicit_operator_semantics_repair`, `operator_param_mismatch_repair`,
`missing_hypothesis_repair`,
`invented_complexity_repair`, and `unsupported_refusal`; it fails instead of
duplicating prompts if the public corpus cannot satisfy the requested minimum.
Challenge prompts expose the task metadata required by the verifier. In
particular, `missing_hypothesis_repair` includes the ordered
`operator_assumptions` in the visible target line so the task measures repair
quality instead of guessing hidden hypotheses. `operator_param_mismatch_repair`
includes the ordered `operator_params` for the same reason.
`contextual_multi_trap_repair` also exposes ordered `operator_types`,
`operator_params`, and `operator_assumptions`; its difficulty comes from using
the visible context correctly while ignoring decoys and claims, not from
guessing hidden fields.
`implicit_operator_semantics_repair` is stricter: it does not expose those
ordered operator fields as a visible answer line. It does expose a public
operator-semantics hint with compatible operator types, candidate parameter
keys, relevant public operator cards, required hypothesis terms, the required
AttackPlan operator key `type`, the forbidden key `operator_id`, and the
no-claim boundary. Candidate object 2 already contains the public parameter
values to preserve; the model must use the semantic context to repair the
operator type, missing hypothesis, and claim boundary, while the scorer still
checks the hidden public seed metadata.
For failed-row diagnosis, pass `challenge_row_indices=[...]` after the same
challenge filters. This rebuilds the stable ordered suite and returns only the
requested row indices, adding `info["challenge_row_index"]` to each selected
row. Use this for targeted reruns of known failed examples only; it does not
replace the full held-out eval and must not relax reward metrics.
`build_challenge_scorecard()` summarizes these rows by challenge type, verifies
that broken submissions score `0.0`, and verifies that the repaired public seed
or strict unsupported refusal scores `1.0`. Use that scorecard as a local
preflight before spending Prime training budget.

Dataset rows can be filtered with `attack_plan_id`, `target_family`, and
`seed_accepted`. Use `seed_accepted=true` for supported-only strict quality
evals, and run unsupported tasks as a separate safety eval so unsupported seeds
do not look like model failures. Do not use accepted-only copy-seed batches for
Prime RL training; they can produce zero-advantage batches when every rollout
receives the same reward.

`prime_manifest.json` is generated by `agades-pqc prime-manifest`. It records
the packaged task list, family coverage, default eval settings, reward contract,
deterministic task summary, and safety boundaries expected before any Prime
Environments Hub push.

## Local Install

```bash
cd prime_intellect/verifiers_environment
uv pip install -e .
```

## Evaluate

```bash
cd prime_intellect/verifiers_environment
uv run vf-eval agades-pqc-verifier-env
```

The credentialed Prime eval template is generated and verified from the repo
root:

```bash
uv run agades-pqc prime-eval-config --config prime_intellect/evals/agades_pqc_eval.template.toml --manifest docs/prime_eval_config_manifest.json
uv run agades-pqc prime-eval-config-verify --config prime_intellect/evals/agades_pqc_eval.template.toml --manifest docs/prime_eval_config_manifest.json
```

It uses `AGADES_PRIME_ENV_REF` for the owner-qualified Prime environment and
`AGADES_EVAL_MODEL` for the reviewed model id. The template is intentionally
blocked until Prime credentials, organization/namespace, billing, and model
choice have been reviewed.

## Publish

```bash
cd prime_intellect/verifiers_environment
prime env push --visibility PRIVATE
```

After a reviewed Hub push, install the uploaded environment by owner-qualified
name:

```bash
prime env install <owner>/agades-pqc-verifier-env
```

Use `--visibility PUBLIC` only after reviewing the release bundle, dependency
pin, and public benchmark manifests.

## Required Environment Variables

No environment variables are required for local evaluation. Prime CLI
authentication is required only for `prime env push` and hosted Hub workflows.

## Safety

- The environment accepts JSON `AttackPlan` objects only.
- It does not execute model-submitted Python, shell, or network actions.
- Scores are verifier plumbing signals, not security claims about deployed PQC systems.
