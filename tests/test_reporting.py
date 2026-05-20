from pathlib import Path

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.reporting.generator import ReportGenerator
from agades_pqc_gym.reporting.markdown import render_report
from agades_pqc_gym.traces.schema import TraceRecord


def test_report_generator_summarizes_family_target_and_reproduction() -> None:
    report = ReportGenerator(title="Multi-Family Report").render_markdown(
        [
            {
                "candidate_id": "code-based-1",
                "public_release_ok": True,
                "attack_plan": {
                    "target": {
                        "family": "CODE_BASED",
                        "name": "toy_syndrome_31_16_w3",
                    }
                },
                "evaluation": {
                    "valid": True,
                    "evaluation_status": "ok",
                    "combined_score": -18.5,
                    "estimated_time_bits": 14.25,
                    "estimated_memory_bits": 6.5,
                    "estimator_name": "toy-code-based-isd-estimator",
                    "feature_family": "CODE_BASED",
                    "feature_attack_type": "information_set_decoding:prange_toy",
                    "reproduction_status": "instance_solved",
                },
            },
            {
                "candidate_id": "hash-1",
                "public_release_ok": True,
                "attack_plan": {
                    "target": {
                        "family": "HASH_BASED",
                        "name": "toy_hash_preimage_24",
                    }
                },
                "evaluation": {
                    "valid": True,
                    "evaluation_status": "ok",
                    "combined_score": -24.0,
                    "estimated_time_bits": 24.0,
                    "estimated_memory_bits": 1.0,
                    "estimator_name": "toy-hash-bound-estimator",
                    "feature_family": "HASH_BASED",
                    "feature_attack_type": "security_bound_check:toy_preimage_bound",
                    "reproduction_status": "not_requested",
                },
            },
        ]
    )

    assert "Multi-Family Report" in report
    assert "Family Summary" in report
    assert "`CODE_BASED`: 1" in report
    assert "`HASH_BASED`: 1" in report
    assert "toy_syndrome_31_16_w3" in report
    assert "toy_hash_preimage_24" in report
    assert "instance_solved" in report
    assert "toy-code-based-isd-estimator" in report
    assert "Reproduction Status" in report


def test_report_generator_redacts_private_trace_targets_by_default() -> None:
    plan = AttackPlan.model_validate_json(
        Path("examples/attack_plans/lattice_primal_usvp_toy.json").read_text(
            encoding="utf-8"
        )
    )
    private_plan = plan.model_copy(
        update={
            "target": plan.target.model_copy(
                update={"name": "private_sensitive_lwe_candidate"}
            ),
            "metadata": plan.metadata.model_copy(update={"public": False}),
        }
    )
    record = TraceRecord.from_evaluation(
        run_id="private-run",
        candidate_id="candidate-private",
        parent_id=None,
        generation=0,
        mutation_summary="private prompt mutation",
        attack_plan=private_plan,
        evaluation={
            "valid": True,
            "evaluation_status": "ok",
            "combined_score": -88.12345,
            "estimated_time_bits": 72.0,
            "estimated_memory_bits": 24.0,
            "estimator_name": "private-lattice-estimator",
            "feature_family": "LWE",
            "feature_attack_type": "primal_usvp",
            "reproduction_status": "not_requested",
            "raw_output": {"private_recipe": "secret"},
        },
        accepted=True,
        public_release_ok=False,
        redaction_reason="contains private prompt/evolution trace",
    )

    report = ReportGenerator(title="Public Report").render_markdown([record])

    assert "private_sensitive_lwe_candidate" not in report
    assert "private prompt mutation" not in report
    assert "private-lattice-estimator" not in report
    assert "-88.12345" not in report
    assert "Private records redacted: 1" in report
    assert "[redacted]" in report


def test_report_generator_redacts_private_mapping_evaluation_by_default() -> None:
    report = ReportGenerator(title="Public Report").render_markdown(
        [
            {
                "candidate_id": "candidate-private",
                "public_release_ok": False,
                "redaction_reason": "contains private prompt/evolution trace",
                "mutation_summary": "private prompt mutation",
                "attack_plan": {
                    "attack_plan_id": "private-plan",
                    "target": {
                        "family": "LWE",
                        "name": "private_sensitive_lwe_candidate",
                    },
                },
                "evaluation": {
                    "valid": True,
                    "evaluation_status": "ok",
                    "combined_score": -88.12345,
                    "estimated_time_bits": 72.0,
                    "estimated_memory_bits": 24.0,
                    "estimator_name": "private-lattice-estimator",
                    "feature_family": "LWE",
                    "feature_attack_type": "primal_usvp",
                    "reproduction_status": "not_requested",
                    "warnings": ["private evaluator recipe"],
                    "raw_output": {"private_recipe": "secret"},
                },
            }
        ]
    )

    assert "private_sensitive_lwe_candidate" not in report
    assert "private prompt mutation" not in report
    assert "private-lattice-estimator" not in report
    assert "private evaluator recipe" not in report
    assert "private_recipe" not in report
    assert "-88.12345" not in report
    assert "72.0" not in report
    assert "24.0" not in report
    assert "Private records redacted: 1" in report
    assert "| candidate-private | [redacted] | [redacted] | redacted |" in report


def test_report_contains_mock_disclaimer_and_limitations() -> None:
    report = render_report(
        title="Toy Report",
        records=[
            {
                "candidate_id": "candidate-1",
                "evaluation": {
                    "valid": True,
                    "combined_score": -92.0,
                    "estimated_time_bits": 76.0,
                    "estimated_memory_bits": 28.0,
                    "estimator_name": "mock-lattice-estimator",
                },
            }
        ],
    )

    assert "Toy Report" in report
    assert "Mock Vs Real Estimator Status" in report
    assert "Limitations" in report
    assert "not a security claim" in report.lower()


def test_report_contains_unsupported_status() -> None:
    report = render_report(
        title="Unsupported Report",
        records=[
            {
                "candidate_id": "code-based-placeholder",
                "evaluation": {
                    "valid": False,
                    "evaluation_status": "unsupported",
                    "combined_score": -1e9,
                    "estimated_time_bits": None,
                    "estimated_memory_bits": None,
                    "estimator_name": "code-based-placeholder-estimator",
                },
            }
        ],
    )

    assert "unsupported" in report
    assert "No cryptanalytic estimate" in report
