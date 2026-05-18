from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.traces.redaction import redact_trace_record
from agades_pqc_gym.traces.schema import TraceRecord


def test_redaction_removes_private_attack_plan_and_mutation_summary() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
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

    assert public["attack_plan"] == {"attack_plan_id": "lattice_primal_usvp_toy_v1"}
    assert public["mutation_summary"] == "[redacted]"
    assert public["public_release_ok"] is True


def test_redaction_removes_private_evaluation_details() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    record = TraceRecord.from_evaluation(
        run_id="demo",
        candidate_id="candidate-1",
        parent_id=None,
        generation=0,
        mutation_summary="private prompt mutation",
        attack_plan=plan,
        evaluation={
            "valid": True,
            "evaluation_status": "ok",
            "combined_score": -12.5,
            "estimated_time_bits": 64.0,
            "estimated_memory_bits": 20.0,
            "estimator_name": "private-estimator",
            "estimator_version": "private-version",
            "feature_family": "LWE",
            "feature_attack_type": "private-attack",
            "raw_output": {"private_recipe": "secret"},
            "warnings": ["private warning"],
        },
        accepted=True,
        public_release_ok=False,
        redaction_reason="contains private evaluator output",
    )

    public = redact_trace_record(record)

    assert public["accepted"] is None
    assert public["evaluation"] == {
        "valid": None,
        "evaluation_status": "redacted",
        "combined_score": None,
        "estimated_time_bits": None,
        "estimated_memory_bits": None,
        "estimator_name": None,
        "estimator_version": None,
        "warnings": ["private evaluation redacted from public trace"],
    }
    assert "raw_output" not in public["evaluation"]
    assert "feature_family" not in public["evaluation"]
    assert "private-estimator" not in str(public)
