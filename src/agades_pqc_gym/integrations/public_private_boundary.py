from __future__ import annotations

from pathlib import Path
from typing import Any

from agades_pqc_gym.core.attack_plan import AttackPlan
from agades_pqc_gym.core.trace_record import TraceRecord
from agades_pqc_gym.reporting.generator import ReportGenerator

REPORT_GENERATOR_REDACTION_CHECK_ID = "report-generator-redaction"


def build_public_private_boundary(root: Path) -> dict[str, Any]:
    return public_private_boundary_from_check(
        build_report_generator_redaction_check(root)
    )


def build_report_generator_redaction_check(root: Path) -> dict[str, Any]:
    sensitive_target = "release_audit_private_sensitive_lwe_target"
    sensitive_mapping_target = "release_audit_mapping_private_sensitive_target"
    private_mutation = "release audit private prompt mutation"
    private_mapping_mutation = "release audit mapping private prompt mutation"
    private_estimator = "release-audit-private-estimator"
    private_mapping_estimator = "release-audit-mapping-private-estimator"
    private_score = "-88.12345"
    private_mapping_score = "-77.765"
    failures: list[str] = []

    try:
        plan = AttackPlan.model_validate_json(
            (
                root
                / "examples"
                / "attack_plans"
                / "lattice_primal_usvp_toy.json"
            ).read_text(encoding="utf-8")
        )
        private_plan = plan.model_copy(
            update={
                "target": plan.target.model_copy(
                    update={"name": sensitive_target}
                ),
                "metadata": plan.metadata.model_copy(update={"public": False}),
            }
        )
        record = TraceRecord.from_evaluation(
            run_id="release-audit-report-redaction",
            candidate_id="release-audit-private-candidate",
            parent_id=None,
            generation=0,
            mutation_summary=private_mutation,
            attack_plan=private_plan,
            evaluation={
                "valid": True,
                "evaluation_status": "ok",
                "combined_score": -88.12345,
                "estimated_time_bits": 72.0,
                "estimated_memory_bits": 24.0,
                "estimator_name": private_estimator,
                "feature_family": "LWE",
                "feature_attack_type": "primal_usvp",
                "reproduction_status": "not_requested",
                "raw_output": {"private_recipe": "release audit private recipe"},
            },
            accepted=True,
            public_release_ok=False,
            redaction_reason="contains private prompt/evolution trace",
        )
        private_mapping = {
            "candidate_id": "release-audit-private-mapping-candidate",
            "public_release_ok": False,
            "redaction_reason": "contains private mapping/evolution trace",
            "mutation_summary": private_mapping_mutation,
            "attack_plan": {
                "attack_plan_id": "release-audit-private-mapping-plan",
                "target": {
                    "family": "LWE",
                    "name": sensitive_mapping_target,
                },
            },
            "evaluation": {
                "valid": True,
                "evaluation_status": "ok",
                "combined_score": -77.765,
                "estimated_time_bits": 65.0,
                "estimated_memory_bits": 22.0,
                "estimator_name": private_mapping_estimator,
                "feature_family": "LWE",
                "feature_attack_type": "dual_attack",
                "raw_output": {
                    "private_recipe": "release audit mapping private recipe"
                },
            },
        }
        report = ReportGenerator(title="Release Audit Report").render_markdown(
            [record, private_mapping]
        )
    except Exception as exc:  # noqa: BLE001 - audit must report smoke failures.
        report = ""
        failures.append(f"Report generator redaction smoke failed: {exc}")

    sensitive_target_absent = sensitive_target not in report
    private_mapping_target_absent = sensitive_mapping_target not in report
    private_mutation_absent = (
        private_mutation not in report and private_mapping_mutation not in report
    )
    private_evaluator_output_absent = private_estimator not in report
    private_mapping_evaluator_output_absent = (
        private_mapping_estimator not in report
    )
    private_score_absent = private_score not in report
    private_mapping_score_absent = private_mapping_score not in report
    redacted_count_present = "Private records redacted: 2" in report

    if not sensitive_target_absent:
        failures.append("Report leaked a private target name.")
    if not private_mapping_target_absent:
        failures.append("Report leaked a private mapping target name.")
    if not private_mutation_absent:
        failures.append("Report leaked a private mutation summary.")
    if not private_evaluator_output_absent:
        failures.append("Report leaked private evaluator output.")
    if not private_mapping_evaluator_output_absent:
        failures.append("Report leaked private mapping evaluator output.")
    if not private_score_absent:
        failures.append("Report leaked a private score.")
    if not private_mapping_score_absent:
        failures.append("Report leaked a private mapping score.")
    if not redacted_count_present:
        failures.append("Report did not count the redacted private records.")
    if "[redacted]" not in report:
        failures.append("Report did not render a redacted row marker.")

    return {
        "id": REPORT_GENERATOR_REDACTION_CHECK_ID,
        "status": "failed" if failures else "passed",
        "blocking": True,
        "artifact": "src/agades_pqc_gym/reporting/generator.py",
        "detail": (
            "Family-agnostic public Markdown reports redact private trace target, "
            "family, attack, mutation, and evaluator details by default for typed "
            "trace records and raw trace mappings."
        ),
        "evidence": {
            "redacted_records": 2 if redacted_count_present else 0,
            "sensitive_target_absent": sensitive_target_absent,
            "private_mapping_target_absent": private_mapping_target_absent,
            "private_mutation_absent": private_mutation_absent,
            "private_evaluator_output_absent": private_evaluator_output_absent,
            "private_mapping_evaluator_output_absent": (
                private_mapping_evaluator_output_absent
            ),
            "private_score_absent": private_score_absent,
            "private_mapping_score_absent": private_mapping_score_absent,
        },
        "failures": failures,
    }


def public_private_boundary_from_check(
    redaction_check: dict[str, Any],
) -> dict[str, Any]:
    evidence = _dict_or_empty(redaction_check.get("evidence"))
    typed_trace_redaction_covered = (
        evidence.get("sensitive_target_absent") is True
        and evidence.get("private_evaluator_output_absent") is True
        and evidence.get("private_score_absent") is True
        and evidence.get("private_mutation_absent") is True
    )
    raw_mapping_redaction_covered = (
        evidence.get("private_mapping_target_absent") is True
        and evidence.get("private_mapping_evaluator_output_absent") is True
        and evidence.get("private_mapping_score_absent") is True
        and evidence.get("private_mutation_absent") is True
    )

    return {
        "report_generator_redaction": {
            "blocking": redaction_check.get("blocking"),
            "check_id": REPORT_GENERATOR_REDACTION_CHECK_ID,
            "private_evaluator_output_absent": evidence.get(
                "private_evaluator_output_absent"
            ),
            "private_mapping_evaluator_output_absent": evidence.get(
                "private_mapping_evaluator_output_absent"
            ),
            "private_mapping_score_absent": evidence.get(
                "private_mapping_score_absent"
            ),
            "private_mapping_target_absent": evidence.get(
                "private_mapping_target_absent"
            ),
            "private_mutation_absent": evidence.get("private_mutation_absent"),
            "private_score_absent": evidence.get("private_score_absent"),
            "raw_mapping_redaction_covered": raw_mapping_redaction_covered,
            "redacted_records": evidence.get("redacted_records"),
            "sensitive_target_absent": evidence.get("sensitive_target_absent"),
            "status": redaction_check.get("status"),
            "typed_trace_redaction_covered": typed_trace_redaction_covered,
        }
    }


def redaction_summary_fields(boundary: dict[str, Any]) -> dict[str, Any]:
    redaction = report_generator_redaction_boundary(boundary)
    return {
        "raw_mapping_redaction_covered": redaction.get(
            "raw_mapping_redaction_covered"
        ),
        "report_redaction_records": redaction.get("redacted_records"),
        "typed_trace_redaction_covered": redaction.get(
            "typed_trace_redaction_covered"
        ),
    }


def report_generator_redaction_boundary(
    boundary: dict[str, Any],
) -> dict[str, Any]:
    return _dict_or_empty(boundary.get("report_generator_redaction"))


def verify_public_private_boundary(
    boundary: dict[str, Any],
    failures: list[str],
    *,
    label: str,
) -> None:
    redaction = report_generator_redaction_boundary(boundary)
    if redaction.get("typed_trace_redaction_covered") is not True:
        failures.append(f"{label} typed TraceRecord redaction gate is incomplete.")
    if redaction.get("raw_mapping_redaction_covered") is not True:
        failures.append(f"{label} raw trace mapping redaction gate is incomplete.")
    if redaction.get("redacted_records") != 2:
        failures.append(
            f"{label} report redaction gate must cover two private input shapes."
        )


def _dict_or_empty(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
