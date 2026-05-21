from __future__ import annotations

import json
from pathlib import Path

from agades_pqc_gym.rl.environment import (
    AgadesPQCGymEnvironment,
    score_attack_plan_candidate,
)
from agades_pqc_gym.rl.private_trace import (
    PRIVATE_PEDAGOGICAL_TRACE_SCHEMA,
    build_private_pedagogical_trace_record,
    verify_private_pedagogical_trace_record,
)

LATTICE_PLAN = Path("examples/attack_plans/lattice_primal_usvp_toy.json")
DATASET_CURATION = Path("docs/private_dataset_curation.json")


def test_private_pedagogical_trace_record_is_digest_only_and_contract_bound() -> None:
    candidate_json = LATTICE_PLAN.read_text(encoding="utf-8")
    task = AgadesPQCGymEnvironment.from_attack_plan_paths([LATTICE_PLAN]).reset()[
        "task"
    ]
    reward_report = score_attack_plan_candidate(
        candidate_json,
        task_info=task,
        require_task_match=True,
        pedagogical_signals={
            "surprise_gaps": [0.0, 2.0],
            "student_token_logprobs": [-2.0, -8.0],
        },
    )

    record = build_private_pedagogical_trace_record(
        task=task,
        candidate_json=candidate_json,
        reward_report=reward_report,
        dataset_curation_manifest_path=DATASET_CURATION,
    )

    assert record["schema_version"] == PRIVATE_PEDAGOGICAL_TRACE_SCHEMA
    assert record["record_kind"] == "private_teacher_student_trace"
    assert len(record["trace_id"]) == 64
    assert len(record["task_digest"]) == 64
    assert len(record["candidate_digest"]) == 64
    assert len(record["reward_report_digest"]) == 64
    assert len(record["dataset_curation_digest"]) == 64
    assert record["pedagogical_reward"] == reward_report["pedagogical_reward"]
    assert record["formal_artifact_binding"]["schema_version"] == (
        "agades.pqc.rl.formal_artifact_binding.v1"
    )
    assert record["formal_artifact_binding"]["attack_plan_id"] == (
        "lattice_primal_usvp_toy_v1"
    )
    assert record["formal_artifact_binding"]["claim_allowed"] is False
    assert record["dataset_curation_gate"] == {
        "schema_version": "agades.pqc.rl.private_trace_dataset_curation_gate.v1",
        "curation_manifest_path": "docs/private_dataset_curation.json",
        "source_count": 3,
        "required_controls": [
            "license_review",
            "provenance_tracking",
            "deduplication",
            "redaction",
            "contamination_audit",
        ],
        "source_license_review_statuses": {
            "facebook_tapas": "required_unverified",
            "facebookresearch_lwe_benchmarking": "required_unverified",
            "pq_code_package": "required_unverified",
        },
        "all_sources_license_reviewed": False,
        "training_eligible": False,
        "promotion_blockers": [
            "dataset_license_review_complete",
            "dataset_provenance_manifest_complete",
            "dataset_deduplication_report_complete",
            "dataset_redaction_report_complete",
            "dataset_contamination_audit_complete",
        ],
    }
    assert record["review_gate"] == {
        "human_crypto_review_required": True,
        "formal_methods_review_required": True,
        "publication_boundary_review_required": True,
        "claim_allowed_without_review": False,
    }
    assert record["privacy_boundary"] == {
        "public_release_ok": False,
        "raw_private_signals_included": False,
        "contains_teacher_prompt": False,
        "contains_student_prompt": False,
        "contains_student_token_logprobs": False,
        "contains_raw_dataset_rows": False,
    }

    serialized = json.dumps(record, sort_keys=True)
    assert '"student_token_logprobs":' not in serialized
    assert '"surprise_gaps":' not in serialized
    assert '"teacher_prompt":' not in serialized
    assert candidate_json not in serialized
    assert verify_private_pedagogical_trace_record(record) == {
        "schema_version": "agades.pqc.rl.private_pedagogical_trace_verification.v1",
        "accepted": True,
        "summary": {
            "has_formal_artifact_binding": True,
            "has_pedagogical_reward": True,
            "training_eligible": False,
            "public_release_ok": False,
            "raw_private_signals_included": False,
            "failure_count": 0,
        },
        "failures": [],
    }


def test_private_pedagogical_trace_verifier_rejects_public_or_raw_fields() -> None:
    candidate_json = LATTICE_PLAN.read_text(encoding="utf-8")
    task = AgadesPQCGymEnvironment.from_attack_plan_paths([LATTICE_PLAN]).reset()[
        "task"
    ]
    reward_report = score_attack_plan_candidate(
        candidate_json,
        task_info=task,
        require_task_match=True,
    )
    record = build_private_pedagogical_trace_record(
        task=task,
        candidate_json=candidate_json,
        reward_report=reward_report,
        dataset_curation_manifest_path=DATASET_CURATION,
    )
    record["privacy_boundary"]["public_release_ok"] = True
    record["student_token_logprobs"] = [-1.0]

    result = verify_private_pedagogical_trace_record(record)

    assert result["accepted"] is False
    assert "Private pedagogical trace must not be public-releaseable." in (
        result["failures"]
    )
    assert (
        "Private pedagogical trace contains forbidden field: "
        "student_token_logprobs."
    ) in result["failures"]


def test_private_pedagogical_trace_verifier_rejects_premature_training_gate() -> None:
    candidate_json = LATTICE_PLAN.read_text(encoding="utf-8")
    task = AgadesPQCGymEnvironment.from_attack_plan_paths([LATTICE_PLAN]).reset()[
        "task"
    ]
    reward_report = score_attack_plan_candidate(
        candidate_json,
        task_info=task,
        require_task_match=True,
    )
    record = build_private_pedagogical_trace_record(
        task=task,
        candidate_json=candidate_json,
        reward_report=reward_report,
        dataset_curation_manifest_path=DATASET_CURATION,
    )
    record["dataset_curation_gate"]["training_eligible"] = True
    record["dataset_curation_gate"]["promotion_blockers"] = []

    result = verify_private_pedagogical_trace_record(record)

    assert result["accepted"] is False
    assert (
        "Private pedagogical trace dataset gate cannot mark unreviewed "
        "sources training eligible."
    ) in result["failures"]
