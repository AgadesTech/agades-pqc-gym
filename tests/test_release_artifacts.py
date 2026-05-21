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
from agades_pqc_gym.integrations.ecosystem_smoke import verify_ecosystem_smoke_report
from agades_pqc_gym.integrations.external_publication_review_packet import (
    verify_external_publication_review_packet,
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

LWE_PLAN = Path("examples/attack_plans/lattice_primal_usvp_toy.json")
MLWE_PLAN = Path("examples/attack_plans/lattice_mlwe_module_hypothesis_toy.json")


def test_release_artifact_convergence_repairs_dependent_artifacts(
    tmp_path: Path,
) -> None:
    copied_root = _copy_repo(tmp_path)
    corrupted_semantics = copied_root / DEFAULT_OPERATOR_SEMANTICS_PATH
    corrupted_report = copied_root / "reports" / "ecosystem_smoke.json"
    corrupted_semantics.write_text("{}\n", encoding="utf-8")
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
    assert result["failures"] == []
    _assert_formal_artifacts_verified(copied_root)
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
