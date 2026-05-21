from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from agades_pqc_gym.cli import app
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


def test_release_artifact_convergence_repairs_dependent_artifacts(
    tmp_path: Path,
) -> None:
    copied_root = _copy_repo(tmp_path)
    corrupted_report = copied_root / "reports" / "ecosystem_smoke.json"
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
    assert result["failures"] == []
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
