from __future__ import annotations

import json
from pathlib import Path

from agades_pqc_gym.integrations.private_pedagogical_trace_batch import (
    PRIVATE_PEDAGOGICAL_TRACE_BATCH_SCHEMA,
    verify_private_pedagogical_trace_batch,
    write_private_pedagogical_trace_batch,
)
from agades_pqc_gym.integrations.private_run_policy import write_private_run_policy

PROJECT_ROOT = Path.cwd()
LATTICE_PLAN = PROJECT_ROOT / "examples/attack_plans/lattice_primal_usvp_toy.json"
DATASET_CURATION = PROJECT_ROOT / "docs/private_dataset_curation.json"


def test_private_pedagogical_trace_batch_writes_digest_only_private_records(
    tmp_path: Path,
) -> None:
    policy = tmp_path / "docs/private_run_policy.json"
    out = tmp_path / "private/traces/pedagogical_rl/trace_records.jsonl"
    write_private_run_policy(policy)

    manifest = write_private_pedagogical_trace_batch(
        [LATTICE_PLAN],
        out,
        dataset_curation_manifest_path=DATASET_CURATION,
        policy_path=policy,
        root=tmp_path,
    )

    assert manifest["schema_version"] == PRIVATE_PEDAGOGICAL_TRACE_BATCH_SCHEMA
    assert manifest["trace_path"] == "private/traces/pedagogical_rl/trace_records.jsonl"
    assert manifest["manifest_path"] == (
        "private/traces/pedagogical_rl/trace_records.manifest.json"
    )
    assert manifest["summary"] == {
        "trace_count": 1,
        "accepted_records": 1,
        "public_release_ok": False,
        "raw_private_signals_included": False,
    }
    assert manifest["safety"] == {
        "private": True,
        "public_release_ok": False,
        "contains_raw_private_signals": False,
        "contains_forbidden_public_fields": False,
        "writes_only_allowed_private_roots": True,
    }
    assert manifest["review_gate"]["human_crypto_review_required"] is True
    assert manifest["review_gate"]["formal_methods_review_required"] is True
    assert manifest["review_gate"]["publication_boundary_review_required"] is True

    records = [
        json.loads(line)
        for line in out.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(records) == 1
    assert records[0]["record_kind"] == "private_teacher_student_trace"
    serialized = json.dumps(records[0], sort_keys=True)
    assert '"teacher_prompt":' not in serialized
    assert '"student_prompt":' not in serialized
    assert '"student_token_logprobs":' not in serialized
    assert LATTICE_PLAN.read_text(encoding="utf-8") not in serialized

    assert json.loads(
        out.with_name("trace_records.manifest.json").read_text(encoding="utf-8")
    ) == manifest
    assert verify_private_pedagogical_trace_batch(
        out,
        policy_path=policy,
        root=tmp_path,
    ) == {
        "schema_version": (
            "agades.pqc.rl.private_pedagogical_trace_batch_verification.v1"
        ),
        "trace_path": "private/traces/pedagogical_rl/trace_records.jsonl",
        "manifest_path": "private/traces/pedagogical_rl/trace_records.manifest.json",
        "accepted": True,
        "summary": {
            "trace_count": 1,
            "accepted_records": 1,
            "failure_count": 0,
            "manifest_in_sync": True,
            "public_release_ok": False,
        },
        "failures": [],
    }


def test_private_pedagogical_trace_batch_rejects_public_output_paths(
    tmp_path: Path,
) -> None:
    policy = tmp_path / "docs/private_run_policy.json"
    write_private_run_policy(policy)

    result = verify_private_pedagogical_trace_batch(
        tmp_path / "hf/dataset/private_trace_records.jsonl",
        policy_path=policy,
        root=tmp_path,
    )

    assert result["accepted"] is False
    assert "Private pedagogical trace batch path must be private." in result[
        "failures"
    ]
