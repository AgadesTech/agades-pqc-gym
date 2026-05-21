from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
from agades_pqc_gym.formal.artifacts import (
    MVP_VERTICAL_ESTIMATOR_RESULT_PATHS,
    MVP_VERTICAL_PROOF_ARTIFACT_PATHS,
    verify_attack_plan_evaluator_result,
    verify_attack_plan_proof_artifact,
)
from agades_pqc_gym.formal.attack_plan_semantics import (
    DEFAULT_ATTACKPLAN_SEMANTICS_PATH,
    verify_formal_attackplan_semantics,
)
from agades_pqc_gym.formal.estimator_model import (
    DEFAULT_ESTIMATOR_MODEL_PATH,
    verify_formal_estimator_model,
)
from agades_pqc_gym.formal.family_coverage import (
    DEFAULT_COVERAGE_PATH,
    verify_formal_family_coverage,
)
from agades_pqc_gym.formal.lean_backend import (
    DEFAULT_BACKEND_PATH,
    verify_formal_lean_backend,
)
from agades_pqc_gym.formal.obligation_ledger import (
    DEFAULT_OBLIGATION_LEDGER_PATH,
    verify_formal_obligation_ledger,
)
from agades_pqc_gym.formal.operator_semantics import (
    DEFAULT_OPERATOR_SEMANTICS_PATH,
    verify_formal_operator_semantics,
)
from agades_pqc_gym.formal.smt_assist import (
    DEFAULT_SMT_ASSIST_PATH,
    verify_formal_smt_assist_contract,
)
from agades_pqc_gym.integrations.deepevolve_research_hooks import (
    DEFAULT_MANIFEST_PATH as DEEPEVOLVE_MANIFEST_PATH,
)
from agades_pqc_gym.integrations.deepevolve_research_hooks import (
    verify_deepevolve_research_hooks_manifest,
)
from agades_pqc_gym.integrations.ecosystem_smoke import verify_ecosystem_smoke_report
from agades_pqc_gym.integrations.external_publication_review_packet import (
    verify_external_publication_review_packet,
)
from agades_pqc_gym.integrations.huggingface_dataset import (
    verify_huggingface_dataset_bundle,
)
from agades_pqc_gym.integrations.huggingface_space_smoke import (
    verify_huggingface_space_smoke_report,
)
from agades_pqc_gym.integrations.pedagogical_rl_method import (
    DEFAULT_METHOD_PATH as PEDAGOGICAL_RL_METHOD_PATH,
)
from agades_pqc_gym.integrations.pedagogical_rl_method import (
    verify_pedagogical_rl_method,
)
from agades_pqc_gym.integrations.prime_environment_manifest import (
    verify_prime_environment_manifest,
)
from agades_pqc_gym.integrations.prime_environment_smoke import (
    verify_prime_environment_smoke_report,
)
from agades_pqc_gym.integrations.prime_eval_config import (
    DEFAULT_CONFIG_PATH as PRIME_EVAL_CONFIG_PATH,
)
from agades_pqc_gym.integrations.prime_eval_config import (
    DEFAULT_MANIFEST_PATH as PRIME_EVAL_MANIFEST_PATH,
)
from agades_pqc_gym.integrations.prime_eval_config import (
    verify_prime_eval_config,
)
from agades_pqc_gym.integrations.prime_publication_handoff import (
    verify_prime_publication_handoff,
)
from agades_pqc_gym.integrations.prime_speedrun_handoff import (
    verify_prime_speedrun_handoff,
)
from agades_pqc_gym.integrations.private_dataset_curation import (
    DEFAULT_CURATION_PATH as PRIVATE_DATASET_CURATION_PATH,
)
from agades_pqc_gym.integrations.private_dataset_curation import (
    verify_private_dataset_curation,
)
from agades_pqc_gym.integrations.private_run_policy import verify_private_run_policy
from agades_pqc_gym.integrations.private_training_config import (
    DEFAULT_CONFIG_PATH as PRIVATE_TRAINING_CONFIG_PATH,
)
from agades_pqc_gym.integrations.private_training_config import (
    DEFAULT_MANIFEST_PATH as PRIVATE_TRAINING_MANIFEST_PATH,
)
from agades_pqc_gym.integrations.private_training_config import (
    verify_private_training_config,
)
from agades_pqc_gym.integrations.private_training_readiness import (
    DEFAULT_READINESS_PATH as PRIVATE_TRAINING_READINESS_PATH,
)
from agades_pqc_gym.integrations.private_training_readiness import (
    verify_private_training_readiness,
)
from agades_pqc_gym.integrations.publication_preflight import (
    verify_publication_preflight,
)
from agades_pqc_gym.integrations.release_artifacts import (
    RELEASE_ARTIFACT_PATHS,
    write_release_artifacts_until_stable,
)
from agades_pqc_gym.integrations.release_status import verify_release_status
from agades_pqc_gym.integrations.reviewer_governance import verify_reviewer_governance
from agades_pqc_gym.integrations.rl_environment_contract import (
    verify_rl_environment_contract,
)
from agades_pqc_gym.openevolve_adapter.config_templates import (
    DEFAULT_CONFIG_PATH as OPENEVOLVE_CONFIG_PATH,
)
from agades_pqc_gym.openevolve_adapter.config_templates import (
    verify_default_config_template,
)
from agades_pqc_gym.openevolve_adapter.smoke import (
    DEFAULT_REPORT as OPENEVOLVE_SMOKE_REPORT,
)
from agades_pqc_gym.openevolve_adapter.smoke import (
    verify_openevolve_smoke_report,
)

LWE_PLAN = Path("examples/attack_plans/lattice_primal_usvp_toy.json")
MLWE_PLAN = Path("examples/attack_plans/lattice_mlwe_module_hypothesis_toy.json")


def test_release_artifact_convergence_repairs_dependent_artifacts(
    tmp_path: Path,
) -> None:
    copied_root = _copy_repo(tmp_path)
    corrupted_semantics = copied_root / DEFAULT_OPERATOR_SEMANTICS_PATH
    corrupted_attackplan = copied_root / DEFAULT_ATTACKPLAN_SEMANTICS_PATH
    corrupted_smt = copied_root / DEFAULT_SMT_ASSIST_PATH
    corrupted_training = copied_root / PRIVATE_TRAINING_MANIFEST_PATH
    corrupted_readiness = copied_root / PRIVATE_TRAINING_READINESS_PATH
    corrupted_deepevolve = copied_root / DEEPEVOLVE_MANIFEST_PATH
    corrupted_hf_dataset_manifest = copied_root / "hf" / "dataset" / "MANIFEST.sha256"
    corrupted_hf_space_smoke = copied_root / "reports" / "hf_space_smoke.json"
    corrupted_prime_environment_smoke = (
        copied_root / "reports" / "prime_environment_smoke.json"
    )
    corrupted_report = copied_root / "reports" / "ecosystem_smoke.json"
    corrupted_semantics.write_text("{}\n", encoding="utf-8")
    corrupted_attackplan.write_text("{}\n", encoding="utf-8")
    corrupted_smt.write_text("{}\n", encoding="utf-8")
    corrupted_training.write_text("{}\n", encoding="utf-8")
    corrupted_readiness.write_text("{}\n", encoding="utf-8")
    corrupted_deepevolve.write_text("{}\n", encoding="utf-8")
    corrupted_hf_dataset_manifest.write_text("{}\n", encoding="utf-8")
    corrupted_hf_space_smoke.write_text("{}\n", encoding="utf-8")
    corrupted_prime_environment_smoke.write_text("{}\n", encoding="utf-8")
    corrupted_report.write_text("{}\n", encoding="utf-8")

    result = write_release_artifacts_until_stable(root=copied_root, max_passes=6)

    assert result["accepted"] is True
    assert result["stable"] is True
    assert result["passes"] >= 2
    assert result["artifact_paths"] == [
        path.as_posix() for path in RELEASE_ARTIFACT_PATHS
    ]
    assert "reports/ecosystem_smoke.json" in {
        path
        for release_pass in result["pass_summaries"]
        for path in release_pass["changed_artifacts"]
    }
    assert DEFAULT_OPERATOR_SEMANTICS_PATH.as_posix() in {
        path
        for release_pass in result["pass_summaries"]
        for path in release_pass["changed_artifacts"]
    }
    assert DEFAULT_ATTACKPLAN_SEMANTICS_PATH.as_posix() in {
        path
        for release_pass in result["pass_summaries"]
        for path in release_pass["changed_artifacts"]
    }
    assert DEFAULT_SMT_ASSIST_PATH.as_posix() in {
        path
        for release_pass in result["pass_summaries"]
        for path in release_pass["changed_artifacts"]
    }
    assert PRIVATE_TRAINING_MANIFEST_PATH.as_posix() in {
        path
        for release_pass in result["pass_summaries"]
        for path in release_pass["changed_artifacts"]
    }
    assert PRIVATE_TRAINING_READINESS_PATH.as_posix() in {
        path
        for release_pass in result["pass_summaries"]
        for path in release_pass["changed_artifacts"]
    }
    assert DEEPEVOLVE_MANIFEST_PATH.as_posix() in {
        path
        for release_pass in result["pass_summaries"]
        for path in release_pass["changed_artifacts"]
    }
    assert "hf/dataset/MANIFEST.sha256" in {
        path
        for release_pass in result["pass_summaries"]
        for path in release_pass["changed_artifacts"]
    }
    assert "reports/hf_space_smoke.json" in {
        path
        for release_pass in result["pass_summaries"]
        for path in release_pass["changed_artifacts"]
    }
    assert "reports/prime_environment_smoke.json" in {
        path
        for release_pass in result["pass_summaries"]
        for path in release_pass["changed_artifacts"]
    }
    assert result["failures"] == []
    _assert_formal_artifacts_verified(copied_root)
    _assert_private_rl_prime_artifacts_verified(copied_root)
    assert json.loads((copied_root / "public" / "release_audit.json").read_text())[
        "accepted"
    ] is True
    assert verify_release_status(
        Path("docs/release_status.json"),
        root=copied_root,
    )["accepted"] is True
    assert verify_publication_preflight(
        Path("public/publication_preflight.json"),
        root=copied_root,
    )["accepted"] is True
    assert verify_external_publication_review_packet(
        Path("docs/external_publication_review_packet.json"),
        root=copied_root,
    )["accepted"] is True
    assert verify_huggingface_dataset_bundle(
        Path("hf/dataset"),
        root=copied_root,
    )["accepted"] is True
    assert verify_huggingface_space_smoke_report(
        Path("reports/hf_space_smoke.json"),
        root=copied_root,
    )["accepted"] is True
    assert verify_prime_environment_smoke_report(
        Path("reports/prime_environment_smoke.json"),
        root=copied_root,
    )["accepted"] is True
    assert verify_ecosystem_smoke_report(
        Path("reports/ecosystem_smoke.json"),
        root=copied_root,
    )["accepted"] is True
    assert verify_reviewer_governance(
        Path("docs/reviewer_governance.json"),
        root=copied_root,
    )["accepted"] is True
    assert verify_rl_environment_contract(
        Path("docs/rl_environment_contract.json"),
        root=copied_root,
    )["accepted"] is True


def test_release_artifacts_cli_converges_explicit_root(tmp_path: Path) -> None:
    copied_root = _copy_repo(tmp_path)
    (copied_root / "public" / "publication_preflight.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "release-artifacts",
            "--root",
            str(copied_root),
            "--max-passes",
            "6",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["accepted"] is True
    assert payload["stable"] is True
    assert payload["passes"] >= 2


def _assert_formal_artifacts_verified(root: Path) -> None:
    assert verify_formal_lean_backend(DEFAULT_BACKEND_PATH, root=root)[
        "accepted"
    ] is True
    assert verify_formal_operator_semantics(
        DEFAULT_OPERATOR_SEMANTICS_PATH,
        root=root,
    )["accepted"] is True
    assert verify_formal_attackplan_semantics(
        DEFAULT_ATTACKPLAN_SEMANTICS_PATH,
        root=root,
    )["accepted"] is True
    assert verify_attack_plan_evaluator_result(
        Path(MVP_VERTICAL_ESTIMATOR_RESULT_PATHS["LWE"]),
        LWE_PLAN,
        root=root,
    )["accepted"] is True
    assert verify_attack_plan_evaluator_result(
        Path(MVP_VERTICAL_ESTIMATOR_RESULT_PATHS["MLWE"]),
        MLWE_PLAN,
        root=root,
    )["accepted"] is True
    assert verify_attack_plan_proof_artifact(
        root / MVP_VERTICAL_PROOF_ARTIFACT_PATHS["LWE"],
        root=root,
    )["accepted"] is True
    assert verify_attack_plan_proof_artifact(
        root / MVP_VERTICAL_PROOF_ARTIFACT_PATHS["MLWE"],
        root=root,
    )["accepted"] is True
    assert verify_formal_family_coverage(DEFAULT_COVERAGE_PATH, root=root)[
        "accepted"
    ] is True
    assert verify_formal_estimator_model(DEFAULT_ESTIMATOR_MODEL_PATH, root=root)[
        "accepted"
    ] is True
    assert verify_formal_obligation_ledger(
        DEFAULT_OBLIGATION_LEDGER_PATH,
        root=root,
    )["accepted"] is True
    assert verify_formal_smt_assist_contract(DEFAULT_SMT_ASSIST_PATH, root=root)[
        "accepted"
    ] is True


def _assert_private_rl_prime_artifacts_verified(root: Path) -> None:
    assert verify_private_run_policy(
        Path("docs/private_run_policy.json"),
        root=root,
    )["accepted"] is True
    assert verify_prime_eval_config(
        PRIME_EVAL_CONFIG_PATH,
        PRIME_EVAL_MANIFEST_PATH,
        root=root,
    )["accepted"] is True
    assert verify_prime_environment_manifest(
        Path("prime_intellect/verifiers_environment/prime_manifest.json"),
        root=root,
    )["accepted"] is True
    assert verify_private_dataset_curation(
        PRIVATE_DATASET_CURATION_PATH,
        root=root,
    )["accepted"] is True
    assert verify_pedagogical_rl_method(
        PEDAGOGICAL_RL_METHOD_PATH,
        root=root,
    )["accepted"] is True
    assert verify_private_training_config(
        PRIVATE_TRAINING_CONFIG_PATH,
        PRIVATE_TRAINING_MANIFEST_PATH,
        root=root,
    )["accepted"] is True
    assert verify_private_training_readiness(
        PRIVATE_TRAINING_READINESS_PATH,
        root=root,
    )["accepted"] is True
    assert verify_default_config_template(OPENEVOLVE_CONFIG_PATH, root=root)[
        "accepted"
    ] is True
    assert verify_openevolve_smoke_report(OPENEVOLVE_SMOKE_REPORT, root=root)[
        "accepted"
    ] is True
    assert verify_deepevolve_research_hooks_manifest(
        DEEPEVOLVE_MANIFEST_PATH,
        root=root,
    )["accepted"] is True
    assert verify_prime_publication_handoff(
        Path("docs/prime_publication_handoff.json"),
        root=root,
    )["accepted"] is True
    assert verify_prime_speedrun_handoff(
        Path("docs/prime_speedrun_handoff.json"),
        root=root,
    )["accepted"] is True


def _copy_repo(tmp_path: Path) -> Path:
    copied_root = tmp_path / "repo"
    shutil.copytree(
        Path.cwd(),
        copied_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
        ),
    )
    return copied_root
