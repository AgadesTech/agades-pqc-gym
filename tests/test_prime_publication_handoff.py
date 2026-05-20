from __future__ import annotations

import json
from pathlib import Path

from expected_family_support_summary import EXPECTED_FAMILY_SUPPORT_SUMMARY
from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.integrations.prime_publication_handoff import (
    build_prime_publication_handoff,
    verify_prime_publication_handoff,
    write_prime_publication_handoff,
)

EXPECTED_PRIME_ARTIFACT_PATHS = [
    "prime_intellect/environment_card.md",
    "prime_intellect/evals/agades_pqc_eval.template.toml",
    "prime_intellect/verifier_spec.md",
    "prime_intellect/verifiers_environment/README.md",
    "prime_intellect/verifiers_environment/pyproject.toml",
    "prime_intellect/verifiers_environment/agades_pqc_verifier_env.py",
    "prime_intellect/verifiers_environment/prime_manifest.json",
    "prime_intellect/schemas/attack_plan.schema.json",
    "prime_intellect/schemas/verifier_result.schema.json",
    "prime_intellect/schemas/task_metadata.schema.json",
    "prime_intellect/schemas/schema_manifest.json",
    "docs/prime_eval_config_manifest.json",
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
EXPECTED_PRIME_QUICKSTART_ALIGNMENT = {
    "source_anchor_id": "prime-quickstart",
    "source_url": "https://app.primeintellect.ai/dashboard/home/quickstart",
    "source_observed_date": "2026-05-18",
    "onboarding_commands": [
        {
            "id": "install_prime_cli",
            "command": "uv tool install -U prime",
            "purpose": "Install the Prime CLI from the public quickstart.",
        },
        {
            "id": "browser_login",
            "command": "prime login",
            "purpose": "Authenticate the local Prime CLI session.",
        },
        {
            "id": "workspace_setup",
            "command": "prime lab setup",
            "purpose": "Prepare local agent and Prime workspace configuration.",
        },
    ],
    "reference_eval_commands": [
        {
            "id": "quick_text_eval",
            "command": (
                "prime eval run primeintellect/reverse-text "
                "-m openai/gpt-oss-20b -p prime -n 1 -r 1 -t 512 -s -A"
            ),
            "purpose": "Prime quickstart one-example evaluation smoke.",
        },
        {
            "id": "reasoning_eval",
            "command": (
                "prime eval run primeintellect/aime2026 "
                "-m openai/gpt-oss-20b -p prime -n 1 -r 1 -t 2048 -s -A"
            ),
            "purpose": "Prime quickstart reasoning evaluation example.",
        },
    ],
    "agades_environment_command": (
        "prime eval run <owner>/agades-pqc-verifier-env"
    ),
    "requires_credentials": True,
    "requires_billing_for_hosted_compute": True,
    "external_prime_execution_performed": False,
    "credentials_checked_at_generation": False,
}


def test_prime_publication_handoff_records_review_boundaries(
    tmp_path: Path,
) -> None:
    out = tmp_path / "prime_publication_handoff.json"

    handoff = write_prime_publication_handoff(out)

    assert handoff == build_prime_publication_handoff()
    assert json.loads(out.read_text(encoding="utf-8")) == handoff
    assert handoff["schema_version"] == "agades.pqc.prime_publication_handoff.v1"
    assert handoff["project"] == {
        "name": "Agades PQC Gym",
        "package": "agades_pqc_gym",
        "cli": "agades-pqc",
        "repository": "https://github.com/AgadesTech/agades-pqc-gym",
    }
    assert handoff["platform"] == {
        "ecosystem": "prime_intellect",
        "environment_package": "agades-pqc-verifier-env",
        "environment_manifest": (
            "prime_intellect/verifiers_environment/prime_manifest.json"
        ),
        "schema_manifest": "prime_intellect/schemas/schema_manifest.json",
        "release_plan": "docs/PRIME_INTELLECT_RELEASE_PLAN.md",
        "handoff_status": "local_package_ready_external_publication_blocked",
    }
    assert handoff["local_package"]["artifact_paths"] == EXPECTED_PRIME_ARTIFACT_PATHS
    assert sorted(handoff["local_package"]["artifact_sha256"]) == sorted(
        EXPECTED_PRIME_ARTIFACT_PATHS
    )
    assert handoff["local_package"]["build_command"] == (
        "uv build prime_intellect/verifiers_environment"
    )
    assert handoff["local_package"]["manifest_verify_command"] == (
        "uv run agades-pqc prime-manifest-verify --manifest "
        "prime_intellect/verifiers_environment/prime_manifest.json"
    )
    assert handoff["local_package"]["schemas_verify_command"] == (
        "uv run agades-pqc prime-schemas-verify --schemas prime_intellect/schemas"
    )
    assert handoff["local_package"]["eval_config_verify_command"] == (
        "uv run agades-pqc prime-eval-config-verify --config "
        "prime_intellect/evals/agades_pqc_eval.template.toml --manifest "
        "docs/prime_eval_config_manifest.json"
    )
    assert handoff["readiness"] == {
        "local_package_ready": True,
        "environment_manifest_accepted": True,
        "schemas_accepted": True,
        "eval_config_accepted": True,
        "task_count": 79,
        "family_count": 9,
        "json_only_scoring": True,
        "public_examples_mirrored": True,
        "prime_hub_publication_performed": False,
        "requires_credentials": True,
        "credentials_checked_at_generation": False,
        "credentials_present_in_artifact": False,
        "external_publication_requires_review": True,
    }
    assert handoff["source_anchors"] == [
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
    assert handoff["prime_quickstart_alignment"] == (
        EXPECTED_PRIME_QUICKSTART_ALIGNMENT
    )
    assert handoff["safety"] == {
        "contains_private_traces": False,
        "arbitrary_code_execution": False,
        "live_targeting": False,
        "security_claim": False,
        "publishes_private_candidates": False,
        "claims_external_publication": False,
    }
    assert handoff["review_required_before_publish"] == [
        "Confirm Prime account, organization, and target namespace.",
        "Run the local Prime environment build and verifier smoke gates.",
        "Review the Prime eval config before any credentialed eval run.",
        "Review all public cards for no private traces and no security claims.",
        "Publish first as private/unlisted if Prime Hub supports the target workflow.",
        "Record external Prime Hub URL only after credentialed review.",
    ]
    assert handoff["release_gates"] == [
        "uv run pytest tests/test_prime_publication_handoff.py -q",
        "uv run agades-pqc prime-publication-handoff --out "
        "docs/prime_publication_handoff.json",
        "uv run agades-pqc prime-publication-handoff-verify --handoff "
        "docs/prime_publication_handoff.json",
        "uv run agades-pqc prime-manifest-verify --manifest "
        "prime_intellect/verifiers_environment/prime_manifest.json",
        "uv run agades-pqc prime-schemas-verify --schemas prime_intellect/schemas",
        "uv run agades-pqc prime-eval-config-verify --config "
        "prime_intellect/evals/agades_pqc_eval.template.toml --manifest "
        "docs/prime_eval_config_manifest.json",
        "uv build prime_intellect/verifiers_environment",
        "uv run agades-pqc ecosystem-smoke-verify --report "
        "reports/ecosystem_smoke.json",
        "uv run agades-pqc release-audit --out public/release_audit.json",
    ]


def test_committed_prime_publication_handoff_is_in_sync(tmp_path: Path) -> None:
    generated = tmp_path / "prime_publication_handoff.json"
    committed = Path("docs/prime_publication_handoff.json")

    write_prime_publication_handoff(generated)

    assert committed.read_bytes() == generated.read_bytes()


def test_prime_publication_handoff_verify_accepts_committed_handoff() -> None:
    result = verify_prime_publication_handoff(
        Path("docs/prime_publication_handoff.json")
    )

    assert result == {
        "schema_version": "agades.pqc.prime_publication_handoff_verification.v1",
        "handoff_path": "docs/prime_publication_handoff.json",
        "accepted": True,
        "summary": {
            "artifact_count": 12,
            "external_publication_requires_review": True,
            "failure_count": 0,
            "family_count": 9,
            "family_support_review_required_before_claims": True,
            "implemented_families": ["LWE", "MLWE"],
            "local_package_ready": True,
            "non_lattice_toy_evaluator_count": 41,
            "non_lattice_toy_operator_security_claims": 0,
            "non_lattice_toy_operator_variant_count": 41,
            "prime_hub_publication_performed": False,
            "requires_credentials": True,
            "task_count": 79,
        },
        "failures": [],
    }


def test_prime_publication_handoff_verify_rejects_external_publication_claim(
    tmp_path: Path,
) -> None:
    handoff = build_prime_publication_handoff()
    handoff["readiness"]["prime_hub_publication_performed"] = True
    handoff["safety"]["claims_external_publication"] = True
    out = tmp_path / "prime_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_prime_publication_handoff(out)

    assert result["accepted"] is False
    assert "Prime publication handoff is not in sync." in result["failures"]
    assert "Prime handoff must not claim Prime Hub publication." in result["failures"]
    assert "Prime handoff claims external publication." in result["failures"]


def test_prime_publication_handoff_verify_rejects_missing_credential_boundary(
    tmp_path: Path,
) -> None:
    handoff = build_prime_publication_handoff()
    handoff["readiness"]["requires_credentials"] = False
    handoff["readiness"]["external_publication_requires_review"] = False
    out = tmp_path / "prime_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_prime_publication_handoff(out)

    assert result["accepted"] is False
    assert "Prime handoff lacks credential boundary." in result["failures"]
    assert "Prime handoff lacks external publication review boundary." in result[
        "failures"
    ]


def test_prime_publication_handoff_verify_rejects_quickstart_drift(
    tmp_path: Path,
) -> None:
    handoff = build_prime_publication_handoff()
    handoff["prime_quickstart_alignment"]["onboarding_commands"][0]["command"] = (
        "curl https://example.invalid/install-prime | sh"
    )
    out = tmp_path / "prime_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_prime_publication_handoff(out)

    assert result["accepted"] is False
    assert "Prime publication handoff is not in sync." in result["failures"]
    assert "Prime handoff quickstart alignment drifted." in result["failures"]


def test_prime_publication_handoff_verify_rejects_security_claim(
    tmp_path: Path,
) -> None:
    handoff = build_prime_publication_handoff()
    handoff["safety"]["security_claim"] = True
    out = tmp_path / "prime_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_prime_publication_handoff(out)

    assert result["accepted"] is False
    assert "Prime handoff advertises a security claim." in result["failures"]


def test_prime_publication_handoff_verify_rejects_source_scope_claim(
    tmp_path: Path,
) -> None:
    handoff = build_prime_publication_handoff()
    handoff["source_catalog_scope"]["non_lattice_toy_operator_security_claims"] = 1
    out = tmp_path / "prime_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_prime_publication_handoff(out)

    assert result["accepted"] is False
    assert "Prime publication handoff is not in sync." in result["failures"]
    assert (
        "Prime handoff source catalog scope must not contain "
        "non-lattice toy security claims."
    ) in result["failures"]


def test_prime_publication_handoff_verify_rejects_family_support_claim_gate(
    tmp_path: Path,
) -> None:
    handoff = build_prime_publication_handoff()
    handoff["family_support"]["review_required_before_claims"] = False
    out = tmp_path / "prime_publication_handoff.json"
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n")

    result = verify_prime_publication_handoff(out)

    assert result["accepted"] is False
    assert "Prime publication handoff is not in sync." in result["failures"]
    assert (
        "Prime handoff family_support.review_required_before_claims must be true."
    ) in result["failures"]


def test_prime_publication_handoff_cli_writes_handoff(tmp_path: Path) -> None:
    out = tmp_path / "prime_publication_handoff.json"

    result = CliRunner().invoke(
        app,
        ["prime-publication-handoff", "--out", str(out)],
    )

    assert result.exit_code == 0
    assert f"prime_publication_handoff={out}" in result.output
    assert json.loads(out.read_text(encoding="utf-8"))["schema_version"] == (
        "agades.pqc.prime_publication_handoff.v1"
    )


def test_prime_publication_handoff_verify_cli_accepts_committed_handoff() -> None:
    result = CliRunner().invoke(
        app,
        [
            "prime-publication-handoff-verify",
            "--handoff",
            "docs/prime_publication_handoff.json",
        ],
    )

    assert result.exit_code == 0
    assert (
        "agades.pqc.prime_publication_handoff_verification.v1"
        in result.output
    )
    assert '"accepted": true' in result.output
