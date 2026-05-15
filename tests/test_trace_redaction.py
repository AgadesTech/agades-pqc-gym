from pathlib import Path

from agades_lwe_gym.dsl.schema import AttackPlan
from agades_lwe_gym.traces.redaction import redact_trace_record
from agades_lwe_gym.traces.schema import TraceRecord


def test_redaction_removes_private_attack_plan_and_mutation_summary() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/primal_usvp_toy.json").read_text()
    )
    record = TraceRecord.from_evaluation(
        run_id="demo",
        candidate_id="candidate-1",
        parent_id=None,
        generation=0,
        mutation_summary="private prompt mutation",
        attack_plan=plan,
        evaluation={"valid": True, "combined_score": -90.0},
        accepted=True,
        public_release_ok=False,
        redaction_reason="contains private prompt/evolution trace",
    )

    public = redact_trace_record(record)

    assert public["attack_plan"] == {"attack_plan_id": "primal_usvp_toy_v1"}
    assert public["mutation_summary"] == "[redacted]"
    assert public["public_release_ok"] is True

