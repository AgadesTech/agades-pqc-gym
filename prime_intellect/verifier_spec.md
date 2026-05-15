# Verifier Spec

## Input

AttackPlan JSON.

## Output

```json
{
  "combined_score": -118.4,
  "estimated_time_bits": 112.3,
  "estimated_memory_bits": 64.1,
  "validity_score": 1.0,
  "feature_family": "LWE",
  "feature_attack_type": "dual_hybrid"
}
```

## Requirements

- Deterministic output for a fixed estimator configuration.
- Clear mock vs real estimator status.
- No arbitrary code execution in the MVP.
- Public exports must redact private trace fields.

