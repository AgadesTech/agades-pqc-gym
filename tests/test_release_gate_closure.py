from __future__ import annotations

import json
from pathlib import Path


def test_release_audit_gates_are_preceded_by_ecosystem_smoke_gate() -> None:
    checked_artifacts = [
        *Path("docs").glob("*.json"),
        *Path("hf").rglob("*.json"),
        *Path("nvidia").glob("*.json"),
        *Path("prime_intellect").glob("**/*.json"),
        *Path("public").glob("*.json"),
        *Path("reports").glob("*.json"),
    ]
    checked_artifact_paths = [path.as_posix() for path in sorted(checked_artifacts)]
    release_audit_artifacts: list[str] = []
    ecosystem_smoke_artifacts: list[str] = []
    missing: list[str] = []

    assert "hf/dataset/dataset_info.json" in checked_artifact_paths

    for path in sorted(checked_artifacts):
        data = json.loads(path.read_text(encoding="utf-8"))
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

    assert len(release_audit_artifacts) == 24
    assert len(ecosystem_smoke_artifacts) == 26
    assert missing == []
