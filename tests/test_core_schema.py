from pathlib import Path

import pytest
from pydantic import ValidationError

from agades_pqc_gym.core import EvaluatorResult, TraceRecord
from agades_pqc_gym.core.attack_plan import AttackPlan, TargetFamily
from agades_pqc_gym.core.target import Distribution, TargetSpec
from agades_pqc_gym.evaluators.base import EstimatorResult
from agades_pqc_gym.traces.schema import TraceRecord as LegacyTraceRecord


def test_lattice_attack_plan_loads_with_generic_core_schema() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )

    assert plan.attack_plan_id == "lattice_primal_usvp_toy_v1"
    assert plan.target.family is TargetFamily.LWE
    assert plan.operators[0].type == "primal_usvp"


def test_code_based_placeholder_plan_validates_structurally() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/code_based_isd_placeholder.json").read_text()
    )

    assert plan.target.family is TargetFamily.CODE_BASED
    assert plan.target.support_level == "schema_only"
    assert plan.operators[0].type == "information_set_decoding"


def test_module_hypothesis_requires_module_like_family() -> None:
    with pytest.raises(ValidationError, match="module_lattice_reduction_hypothesis"):
        AttackPlan.model_validate_json(
            Path("examples/attack_plans/invalid_plan_should_fail.json").read_text()
        )


def test_ntru_and_sis_targets_must_remain_schema_only_until_reviewed() -> None:
    for family in (TargetFamily.NTRU, TargetFamily.SIS):
        with pytest.raises(ValidationError, match="schema_only until"):
            TargetSpec(
                family=family,
                name=f"{family.value.lower()}_toy_unreviewed",
                n=64,
                q=257,
                secret_distribution=Distribution(type="binary"),
            )


def test_evaluator_result_is_family_agnostic_core_schema() -> None:
    result = EvaluatorResult(
        evaluator_name="toy-evaluator",
        evaluator_version="0.1.0",
        evaluator_commit=None,
        evaluation_status="ok",
        attack_type="toy_attack",
        time_bits=12.0,
        memory_bits=3.0,
    )

    assert result.schema_version == "agades.pqc.evaluator_result.v1"
    assert result.evaluator_name == "toy-evaluator"
    assert result.model_dump(mode="json")["schema_version"] == (
        "agades.pqc.evaluator_result.v1"
    )
    properties = EvaluatorResult.model_json_schema()["properties"]
    assert "evaluator_name" in properties
    assert "estimator_name" not in properties


def test_legacy_estimator_result_alias_uses_evaluator_result_contract() -> None:
    result = EstimatorResult(
        evaluator_name="toy-evaluator",
        evaluator_version="0.1.0",
        evaluator_commit=None,
        evaluation_status="unsupported",
        attack_type="toy_attack",
        time_bits=None,
        memory_bits=None,
    )

    assert isinstance(result, EvaluatorResult)
    assert result.estimator_name == "toy-evaluator"
    assert result.estimator_version == "0.1.0"


def test_trace_record_is_family_agnostic_core_schema() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text()
    )
    record = TraceRecord.from_evaluation(
        run_id="core-run",
        candidate_id="candidate-1",
        parent_id=None,
        generation=0,
        mutation_summary="seed plan",
        attack_plan=plan,
        evaluation={"valid": True, "evaluation_status": "ok"},
        accepted=True,
        public_release_ok=True,
        redaction_reason=None,
    )

    assert record.schema_version == "agades.pqc.trace_record.v1"
    assert record.model_dump(mode="json")["schema_version"] == (
        "agades.pqc.trace_record.v1"
    )
    assert TraceRecord.model_json_schema()["properties"]["schema_version"]["const"] == (
        "agades.pqc.trace_record.v1"
    )


def test_legacy_trace_record_import_uses_core_contract() -> None:
    assert LegacyTraceRecord is TraceRecord
