# Verifier Spec

## Input

An AttackPlan JSON file.

The stable submission schema is checked in at:

```text
prime_intellect/schemas/attack_plan.schema.json
```

CLI-compatible entrypoints:

```bash
uv run agades-pqc verify examples/attack_plans/lattice_primal_usvp_toy.json
python prime_intellect/verifier.py examples/attack_plans/lattice_primal_usvp_toy.json
cd prime_intellect/verifiers_environment && prime eval run agades-pqc-verifier-env
```

Prime task rows provide `agades.pqc.task_metadata.v5` `info` metadata with
`target_family`, `target_name`, `support_level`, ordered `operator_types`,
ordered `operator_assumptions`, the seed AttackPlan SHA-256 digest, seed
verifier status/reward, seed estimator, and seed reproduction status. The
environment reward uses the task identity fields to reject unrelated valid
AttackPlans or candidates that drop required hypotheses; changing
`attack_plan_id` alone is allowed so candidates can be treated as variants
instead of exact copies.

## Output

The stable verifier result schema is checked in at:

```text
prime_intellect/schemas/verifier_result.schema.json
```

Implemented family example:

```json
{
  "schema_version": "agades.pqc.verifier.v1",
  "attack_plan_id": "lattice_dual_hybrid_toy_v1",
  "target_family": "LWE",
  "schema_valid": true,
  "accepted": true,
  "evaluation_status": "ok",
  "combined_score": -118.4,
  "estimated_time_bits": 112.3,
  "estimated_memory_bits": 64.1,
  "validity_score": 1.0,
  "features": {
    "family": "LWE",
    "attack_type": "dual_hybrid",
    "operator_count": 2,
    "memory_bucket": "medium",
    "assumption_bucket": "some",
    "assumption_count": 2,
    "unique_assumption_count": 2,
    "risky_assumption_count": 1,
    "assumption_fingerprint": "64-char stable sha256",
    "estimator_model": "mock-lattice-estimator"
  }
}
```

Unsupported family example:

```json
{
  "schema_version": "agades.pqc.verifier.v1",
  "target_family": "CODE_BASED",
  "schema_valid": true,
  "accepted": false,
  "evaluation_status": "unsupported",
  "combined_score": -1000000000.0,
  "estimated_time_bits": null,
  "estimated_memory_bits": null,
  "features": {
    "family": "CODE_BASED",
    "attack_type": "information_set_decoding",
    "operator_count": 1,
    "memory_bucket": "low",
    "assumption_bucket": "some",
    "assumption_count": 1,
    "unique_assumption_count": 1,
    "risky_assumption_count": 0,
    "assumption_fingerprint": "64-char stable sha256",
    "estimator_model": "code-based-placeholder-estimator"
  }
}
```

## Requirements

- Deterministic output for a fixed evaluator configuration.
- Prime reward must enforce task metadata, not merely global AttackPlan validity.
- Clear mock vs real estimator status.
- Structured assumption-set features for family-agnostic scoring and reproducible verifier rows.
- No arbitrary code execution in the MVP.
- No fake estimates for unsupported families.
- Public exports must redact private trace fields.
- Schema files must be regenerated with `agades-pqc prime-schemas` and checked by release audit before publication.
