from __future__ import annotations

import json
from pathlib import Path

from expected_family_support_summary import EXPECTED_FAMILY_SUPPORT_SUMMARY
from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.prime_speedrun_handoff import (
    build_prime_speedrun_handoff,
    verify_prime_speedrun_handoff,
    write_prime_speedrun_handoff,
)

EXPECTED_SPEEDRUN_ARTIFACT_PATHS = [
    "docs/prime_publication_handoff.json",
    "prime_intellect/verifiers_environment/prime_manifest.json",
    "prime_intellect/verifiers_environment/agades_pqc_verifier_env.py",
    "prime_intellect/verifiers_environment/README.md",
    "prime_intellect/schemas/task_metadata.schema.json",
    "prime_intellect/schemas/verifier_result.schema.json",
    "docs/source_catalog.json",
    "public/run_export/manifest.json",
    "public/run_export/runs.jsonl",
    "public/run_export/runs.csv",
    "public/run_export/MANIFEST.sha256",
]
EXPECTED_SOURCE_CATALOG_SCOPE = {
    "non_lattice_toy_evaluator_count": 41,
    "non_lattice_toy_operator_families": [
        "CODE_BASED",
        "HASH_BASED",
        "IMPLEMENTATION_SECURITY",
        "ISOGENY_HISTORICAL",
        "MULTIVARIATE",
    ],
    "non_lattice_toy_operator_security_claims": 0,
    "non_lattice_toy_operator_variant_count": 41,
    "source_count": 41,
}


def test_prime_speedrun_handoff_records_public_speedrun_contract(
    tmp_path: Path,
) -> None:
    out = tmp_path / "prime_speedrun_handoff.json"

    handoff = write_prime_speedrun_handoff(out)

    assert handoff == build_prime_speedrun_handoff()
    assert json.loads(out.read_text(encoding="utf-8")) == handoff
    assert handoff["schema_version"] == "agades.pqc.prime_speedrun_handoff.v1"
    assert handoff["project"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "cli": "agades-pqc",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert handoff["platform"] == {
        "ecosystem": "prime_intellect",
        "handoff_status": (
            "local_public_speedrun_packet_ready_external_execution_blocked"
        ),
        "environment_docs_url": (
            "https://docs.primeintellect.ai/verifiers/environments"
        ),
        "autonomous_speedrunning_archive_url": (
            "https://github.com/PrimeIntellect-ai/"
            "experiments-autonomous-speedrunning"
        ),
        "auto_nanogpt_story_url": "https://www.primeintellect.ai/auto-nanogpt",
    }
    assert handoff["prime_verifiers_alignment"] == {
        "environment_manifest": (
            "prime_intellect/verifiers_environment/prime_manifest.json"
        ),
        "environment_package": "agades-pqc-verifier-env",
        "entrypoint": "agades_pqc_verifier_env:load_environment",
        "environment_type": "SingleTurnEnv",
        "dataset_row_fields": ["answer", "info", "prompt"],
        "task_count": 79,
        "family_count": 9,
        "num_examples_default": 2,
        "rollouts_per_example_default": 1,
        "json_only_reward": True,
    }
    assert handoff["public_speedrun_alignment"] == {
        "public_run_export": "public/run_export",
        "public_run_export_accepted": True,
        "bundle_count": 18,
        "run_count": 59,
        "artifact_formats": ["manifest.json", "runs.jsonl", "runs.csv"],
        "observable_loop": [
            "select_public_prime_task",
            "submit_single_json_attack_plan",
            "score_with_deterministic_verifier",
            "review_before_public_run_export_update",
        ],
        "publishes_private_scratchpads": False,
        "publishes_private_candidates": False,
    }
    assert handoff["autonomy_harness_alignment"] == {
        "source_anchor_id": "prime-autonanogpt-speedrun",
        "source_publication_date": "2026-05-14",
        "source_observed_date": "2026-05-18",
        "source_pattern": {
            "agent_rules_file": "AGENTS.md",
            "mission_context_file": "goal.md",
            "mutable_plan_file": "plan.md",
            "durable_thread_log": "scratchpad/THREAD.md",
            "released_observability_artifacts": [
                "scratchpads",
                "run logs",
                "scripts",
                "configs",
            ],
        },
        "agades_public_harness_paths": [
            "AGENTS.md",
            "docs/PLAN.md",
            "docs/IMPLEMENT.md",
            "docs/STATUS.md",
            "public/run_export/manifest.json",
            "docs/private_run_policy.json",
        ],
        "agades_public_harness_roles": {
            "AGENTS.md": "repository-level safety and code-quality rules",
            "docs/PLAN.md": "stable milestone plan",
            "docs/IMPLEMENT.md": "reproducible command runbook",
            "docs/STATUS.md": "durable long-running implementation log",
            "public/run_export/manifest.json": "public run observability export",
            "docs/private_run_policy.json": "private moat and release boundary",
        },
        "public_harness_paths_exist": True,
        "external_prime_autonomous_run_performed": False,
        "publishes_private_scratchpads": False,
        "publishes_private_evolution_traces": False,
        "publishes_private_candidate_payloads": False,
        "review_required_before_prime_autonomy": True,
    }
    assert handoff["source_anchors"] == [
        {
            "id": "prime-verifiers",
            "source_catalog_required": True,
            "current_use": "current_verifier_packaging",
        },
        {
            "id": "prime-quickstart",
            "source_catalog_required": True,
            "current_use": "current_operator_onboarding_reference",
        },
        {
            "id": "prime-autonomous-speedrunning-experiments",
            "source_catalog_required": True,
            "current_use": "public_evaluator_observability_pattern",
        },
        {
            "id": "prime-autonanogpt-speedrun",
            "source_catalog_required": True,
            "current_use": "public_benchmark_story_anchor",
        },
    ]
    assert handoff["family_support"] == EXPECTED_FAMILY_SUPPORT_SUMMARY
    assert handoff["source_catalog_scope"] == EXPECTED_SOURCE_CATALOG_SCOPE
    assert handoff["local_artifacts"]["artifact_paths"] == (
        EXPECTED_SPEEDRUN_ARTIFACT_PATHS
    )
    assert sorted(handoff["local_artifacts"]["artifact_sha256"]) == sorted(
        EXPECTED_SPEEDRUN_ARTIFACT_PATHS
    )
    assert handoff["safety"] == {
        "contains_private_traces": False,
        "publishes_private_candidates": False,
        "publishes_private_scratchpads": False,
        "arbitrary_code_execution": False,
        "live_targeting": False,
        "security_claim": False,
        "claims_external_execution": False,
        "claims_external_publication": False,
    }
    assert handoff["review_required_before_external_execution"] == [
        "Confirm Prime credentials, organization, and target namespace.",
        "Run Prime environment smoke and local package build.",
        "Run release audit and publication preflight.",
        "Start with a private or unlisted Prime environment execution.",
        "Record external run URLs only after reviewer approval.",
    ]
    assert handoff["release_gates"] == [
        "uv run pytest tests/test_prime_speedrun_handoff.py -q",
        "uv run agades-pqc prime-speedrun-handoff --out "
        "docs/prime_speedrun_handoff.json",
        "uv run agades-pqc prime-speedrun-handoff-verify --handoff "
        "docs/prime_speedrun_handoff.json",
        "uv run agades-pqc prime-manifest-verify --manifest "
        "prime_intellect/verifiers_environment/prime_manifest.json",
        "uv run agades-pqc prime-publication-handoff-verify --handoff "
        "docs/prime_publication_handoff.json",
        "uv run agades-pqc public-run-export-verify --export public/run_export",
        "uv build prime_intellect/verifiers_environment",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]


def test_committed_prime_speedrun_handoff_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "prime_speedrun_handoff.json"
    committed = Path("docs/prime_speedrun_handoff.json")

    write_prime_speedrun_handoff(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_prime_speedrun_handoff_verify_accepts_committed_handoff() -> None:
    result = verify_prime_speedrun_handoff(Path("docs/prime_speedrun_handoff.json"))

    assert result == {
        "schema_version": "agades.pqc.prime_speedrun_handoff_verification.v1",
        "handoff_path": "docs/prime_speedrun_handoff.json",
        "accepted": True,
        "summary": {
            "artifact_count": 11,
            "bundle_count": 18,
            "external_execution_requires_review": True,
            "failure_count": 0,
            "family_count": 9,
            "family_support_review_required_before_claims": True,
            "implemented_families": ["LWE", "MLWE"],
            "non_lattice_toy_evaluator_count": 41,
            "non_lattice_toy_operator_security_claims": 0,
            "non_lattice_toy_operator_variant_count": 41,
            "run_count": 59,
            "task_count": 79,
        },
        "failures": [],
    }


def test_prime_speedrun_handoff_verify_rejects_autonomy_execution_claim(
    tmp_path: Path,
) -> None:
    handoff = build_prime_speedrun_handoff()
    handoff["autonomy_harness_alignment"][
        "external_prime_autonomous_run_performed"
    ] = True
    out = tmp_path / "prime_speedrun_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_prime_speedrun_handoff(out)

    assert result["accepted"] is False
    assert "Prime speedrun handoff is not in sync." in result["failures"]
    assert "Prime speedrun handoff claims Prime autonomous execution." in result[
        "failures"
    ]


def test_prime_speedrun_handoff_verify_rejects_external_execution_claim(
    tmp_path: Path,
) -> None:
    handoff = build_prime_speedrun_handoff()
    handoff["safety"]["claims_external_execution"] = True
    out = tmp_path / "prime_speedrun_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_prime_speedrun_handoff(out)

    assert result["accepted"] is False
    assert "Prime speedrun handoff is not in sync." in result["failures"]
    assert "Prime speedrun handoff claims external execution." in result["failures"]


def test_prime_speedrun_handoff_verify_rejects_private_scratchpad_publication(
    tmp_path: Path,
) -> None:
    handoff = build_prime_speedrun_handoff()
    handoff["public_speedrun_alignment"]["publishes_private_scratchpads"] = True
    handoff["safety"]["publishes_private_scratchpads"] = True
    out = tmp_path / "prime_speedrun_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_prime_speedrun_handoff(out)

    assert result["accepted"] is False
    assert "Prime speedrun handoff may publish private scratchpads." in result[
        "failures"
    ]


def test_prime_speedrun_handoff_verify_rejects_family_support_claim_gate(
    tmp_path: Path,
) -> None:
    handoff = build_prime_speedrun_handoff()
    handoff["family_support"]["review_required_before_claims"] = False
    out = tmp_path / "prime_speedrun_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_prime_speedrun_handoff(out)

    assert result["accepted"] is False
    assert "Prime speedrun handoff is not in sync." in result["failures"]
    assert (
        "Prime speedrun handoff family_support.review_required_before_claims "
        "must be true."
    ) in result["failures"]


def test_prime_speedrun_handoff_verify_rejects_source_scope_claim(
    tmp_path: Path,
) -> None:
    handoff = build_prime_speedrun_handoff()
    handoff["source_catalog_scope"]["non_lattice_toy_operator_security_claims"] = 1
    out = tmp_path / "prime_speedrun_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_prime_speedrun_handoff(out)

    assert result["accepted"] is False
    assert "Prime speedrun handoff is not in sync." in result["failures"]
    assert (
        "Prime speedrun handoff source catalog scope must not contain "
        "non-lattice toy security claims."
    ) in result["failures"]


def test_prime_speedrun_handoff_cli_writes_handoff(tmp_path: Path) -> None:
    out = tmp_path / "prime_speedrun_handoff.json"

    result = CliRunner().invoke(
        app,
        ["prime-speedrun-handoff", "--out", str(out)],
    )

    assert result.exit_code == 0
    assert f"prime_speedrun_handoff={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["schema_version"] == (
        "agades.pqc.prime_speedrun_handoff.v1"
    )


def test_prime_speedrun_handoff_verify_cli_accepts_committed_handoff() -> None:
    result = CliRunner().invoke(
        app,
        [
            "prime-speedrun-handoff-verify",
            "--handoff",
            "docs/prime_speedrun_handoff.json",
        ],
    )

    assert result.exit_code == 0
    assert "agades.pqc.prime_speedrun_handoff_verification.v1" in result.output
    assert '"accepted": true' in result.output
