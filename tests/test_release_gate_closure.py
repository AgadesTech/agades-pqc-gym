from __future__ import annotations

import json
import subprocess
from pathlib import Path

from agades_pqc_gym.integrations.release_audit import _release_gate_artifact_paths


def test_release_audit_gates_are_preceded_by_ecosystem_smoke_gate() -> None:
    checked_artifacts = _release_gate_artifact_paths(Path("."))
    checked_artifact_paths = [path.as_posix() for path in sorted(checked_artifacts)]
    release_audit_artifacts: list[str] = []
    ecosystem_smoke_artifacts: list[str] = []
    missing: list[str] = []

    assert "hf/dataset/dataset_info.json" in checked_artifact_paths
    assert all("/.venv/" not in path for path in checked_artifact_paths)

    for path in sorted(checked_artifacts):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        release_gates = data.get("release_gates")
        if not isinstance(release_gates, list):
            continue

        audit_indices = [
            index for index, gate in enumerate(release_gates) if "release-audit" in gate
        ]
        smoke_indices = [
            index
            for index, gate in enumerate(release_gates)
            if "ecosystem-smoke-verify" in gate
        ]
        if smoke_indices:
            ecosystem_smoke_artifacts.append(path.as_posix())
        if not audit_indices:
            continue

        if not smoke_indices or min(smoke_indices) > min(audit_indices):
            missing.append(path.as_posix())
        else:
            release_audit_artifacts.append(path.as_posix())

    assert len(release_audit_artifacts) == 55
    assert len(ecosystem_smoke_artifacts) == 59
    assert missing == []


def test_release_gate_artifact_paths_ignore_gitignored_local_reports(
    tmp_path: Path,
) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text("reports/*.local.json\n", encoding="utf-8")
    tracked_report = tmp_path / "docs" / "tracked.json"
    local_report = tmp_path / "reports" / "hf_space_smoke.local.json"
    _write_release_gate_report(tracked_report)
    _write_release_gate_report(local_report)
    subprocess.run(
        ["git", "add", ".gitignore", "docs/tracked.json"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    paths = {
        path.relative_to(tmp_path).as_posix()
        for path in _release_gate_artifact_paths(tmp_path)
    }

    assert "docs/tracked.json" in paths
    assert "reports/hf_space_smoke.local.json" not in paths


def _write_release_gate_report(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ecosystem_gate = (
        "uv run agades-pqc ecosystem-smoke-verify "
        "--report reports/ecosystem_smoke.json"
    )
    path.write_text(
        json.dumps(
            {
                "schema_version": "test.release_gate.v1",
                "release_gates": [
                    ecosystem_gate,
                    "uv run agades-pqc release-audit --out public/release_audit.json",
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
