from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agades_pqc_gym.integrations.ecosystem_smoke import (
    verify_ecosystem_smoke_report,
    write_ecosystem_smoke_report,
)
from agades_pqc_gym.integrations.external_publication_review_packet import (
    verify_external_publication_review_packet,
    write_external_publication_review_packet,
)
from agades_pqc_gym.integrations.huggingface_publication_handoff import (
    verify_huggingface_publication_handoff,
    write_huggingface_publication_handoff,
)
from agades_pqc_gym.integrations.huggingface_space_manifest import (
    verify_huggingface_space_manifest,
    write_huggingface_space_manifest,
)
from agades_pqc_gym.integrations.nvidia_publication_handoff import (
    verify_nvidia_publication_handoff,
    write_nvidia_publication_handoff,
)
from agades_pqc_gym.integrations.publication_manifest import (
    verify_publication_manifest,
    write_publication_manifest,
)
from agades_pqc_gym.integrations.publication_preflight import (
    verify_publication_preflight,
    write_publication_preflight,
)
from agades_pqc_gym.integrations.release_audit import write_release_audit
from agades_pqc_gym.integrations.release_status import (
    verify_release_status,
    write_release_status,
)
from agades_pqc_gym.integrations.reviewer_governance import (
    verify_reviewer_governance,
    write_reviewer_governance,
)
from agades_pqc_gym.integrations.rl_environment_contract import (
    verify_rl_environment_contract,
    write_rl_environment_contract,
)
from agades_pqc_gym.integrations.runbook_audit import write_runbook_audit

RELEASE_ARTIFACTS_SCHEMA = "agades.pqc.release_artifacts.v1"
ROOT = Path(__file__).resolve().parents[3]

RELEASE_ARTIFACT_PATHS = (
    Path("hf/space_manifest.json"),
    Path("docs/huggingface_publication_handoff.json"),
    Path("docs/nvidia_publication_handoff.json"),
    Path("docs/publication_manifest.json"),
    Path("public/runbook_audit.json"),
    Path("public/release_audit.json"),
    Path("docs/release_status.json"),
    Path("public/publication_preflight.json"),
    Path("docs/external_publication_review_packet.json"),
    Path("reports/ecosystem_smoke.json"),
    Path("docs/reviewer_governance.json"),
    Path("docs/rl_environment_contract.json"),
)

ReleaseArtifactWriter = Callable[[Path], dict[str, Any]]


@dataclass(frozen=True)
class ReleaseArtifactStep:
    id: str
    path: Path
    write: ReleaseArtifactWriter


def write_release_artifacts_until_stable(
    *,
    root: Path | None = None,
    max_passes: int = 6,
) -> dict[str, Any]:
    """Regenerate cyclic release artifacts until a full pass is stable."""
    if max_passes < 1:
        raise ValueError("max_passes must be at least 1")

    project_root = (root or ROOT).resolve()
    pass_summaries: list[dict[str, Any]] = []
    stable = False

    for pass_number in range(1, max_passes + 1):
        before = _artifact_digests(project_root)
        _write_release_artifact_sequence(project_root)
        after = _artifact_digests(project_root)
        changed_artifacts = [
            path.as_posix()
            for path in RELEASE_ARTIFACT_PATHS
            if before[path.as_posix()] != after[path.as_posix()]
        ]
        pass_summaries.append(
            {
                "pass": pass_number,
                "changed_count": len(changed_artifacts),
                "changed_artifacts": changed_artifacts,
            }
        )
        if not changed_artifacts:
            stable = True
            break

    verifications = _verify_release_artifacts(project_root)
    failures = _verification_failures(verifications)
    if not stable:
        failures.insert(
            0,
            f"Release artifacts did not converge after {max_passes} passes.",
        )

    return {
        "schema_version": RELEASE_ARTIFACTS_SCHEMA,
        "accepted": stable and not failures,
        "stable": stable,
        "passes": len(pass_summaries),
        "max_passes": max_passes,
        "root": project_root.as_posix(),
        "artifact_paths": [path.as_posix() for path in RELEASE_ARTIFACT_PATHS],
        "sequence": [step.id for step in _release_artifact_sequence(project_root)],
        "pass_summaries": pass_summaries,
        "verifications": verifications,
        "failures": failures,
    }


def _write_release_artifact_sequence(project_root: Path) -> None:
    for step in _release_artifact_sequence(project_root):
        step.write(project_root / step.path)


def _release_artifact_sequence(project_root: Path) -> tuple[ReleaseArtifactStep, ...]:
    return (
        ReleaseArtifactStep(
            id="hf-space-manifest",
            path=Path("hf/space_manifest.json"),
            write=lambda out: write_huggingface_space_manifest(out, root=project_root),
        ),
        ReleaseArtifactStep(
            id="hf-publication-handoff",
            path=Path("docs/huggingface_publication_handoff.json"),
            write=lambda out: write_huggingface_publication_handoff(
                out,
                root=project_root,
            ),
        ),
        ReleaseArtifactStep(
            id="nvidia-publication-handoff",
            path=Path("docs/nvidia_publication_handoff.json"),
            write=lambda out: write_nvidia_publication_handoff(
                out,
                root=project_root,
            ),
        ),
        ReleaseArtifactStep(
            id="publication-manifest",
            path=Path("docs/publication_manifest.json"),
            write=lambda out: write_publication_manifest(out, root=project_root),
        ),
        ReleaseArtifactStep(
            id="runbook-audit",
            path=Path("public/runbook_audit.json"),
            write=lambda out: write_runbook_audit(out, root=project_root),
        ),
        ReleaseArtifactStep(
            id="release-audit",
            path=Path("public/release_audit.json"),
            write=lambda out: write_release_audit(out, root=project_root),
        ),
        ReleaseArtifactStep(
            id="release-status",
            path=Path("docs/release_status.json"),
            write=lambda out: write_release_status(out, root=project_root),
        ),
        ReleaseArtifactStep(
            id="publication-preflight",
            path=Path("public/publication_preflight.json"),
            write=lambda out: write_publication_preflight(
                out,
                root=project_root,
            ),
        ),
        ReleaseArtifactStep(
            id="external-publication-review-packet",
            path=Path("docs/external_publication_review_packet.json"),
            write=lambda out: write_external_publication_review_packet(
                out,
                root=project_root,
            ),
        ),
        ReleaseArtifactStep(
            id="ecosystem-smoke",
            path=Path("reports/ecosystem_smoke.json"),
            write=lambda out: write_ecosystem_smoke_report(
                out,
                root=project_root,
            ),
        ),
        ReleaseArtifactStep(
            id="reviewer-governance",
            path=Path("docs/reviewer_governance.json"),
            write=lambda out: write_reviewer_governance(out, root=project_root),
        ),
        ReleaseArtifactStep(
            id="rl-environment-contract",
            path=Path("docs/rl_environment_contract.json"),
            write=lambda out: write_rl_environment_contract(out, root=project_root),
        ),
    )


def _artifact_digests(project_root: Path) -> dict[str, str | None]:
    return {
        path.as_posix(): _file_digest(project_root / path)
        for path in RELEASE_ARTIFACT_PATHS
    }


def _file_digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_release_artifacts(project_root: Path) -> dict[str, dict[str, Any]]:
    runbook_audit = _accepted_json_artifact(
        project_root / "public/runbook_audit.json",
        label="runbook audit",
    )
    release_audit = _accepted_json_artifact(
        project_root / "public/release_audit.json",
        label="release audit",
    )
    return {
        "hf-space-manifest": verify_huggingface_space_manifest(
            Path("hf/space_manifest.json"),
            root=project_root,
        ),
        "hf-publication-handoff": verify_huggingface_publication_handoff(
            Path("docs/huggingface_publication_handoff.json"),
            root=project_root,
        ),
        "nvidia-publication-handoff": verify_nvidia_publication_handoff(
            Path("docs/nvidia_publication_handoff.json"),
            root=project_root,
        ),
        "publication-manifest": verify_publication_manifest(
            Path("docs/publication_manifest.json"),
            root=project_root,
        ),
        "runbook-audit": runbook_audit,
        "release-audit": release_audit,
        "release-status": verify_release_status(
            Path("docs/release_status.json"),
            root=project_root,
        ),
        "publication-preflight": verify_publication_preflight(
            Path("public/publication_preflight.json"),
            root=project_root,
        ),
        "external-publication-review-packet": (
            verify_external_publication_review_packet(
                Path("docs/external_publication_review_packet.json"),
                root=project_root,
            )
        ),
        "ecosystem-smoke": verify_ecosystem_smoke_report(
            Path("reports/ecosystem_smoke.json"),
            root=project_root,
        ),
        "reviewer-governance": verify_reviewer_governance(
            Path("docs/reviewer_governance.json"),
            root=project_root,
        ),
        "rl-environment-contract": verify_rl_environment_contract(
            Path("docs/rl_environment_contract.json"),
            root=project_root,
        ),
    }


def _accepted_json_artifact(path: Path, *, label: str) -> dict[str, Any]:
    failures: list[str] = []
    payload: dict[str, Any] = {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"{label} is missing: {path.as_posix()}.")
    except json.JSONDecodeError as exc:
        failures.append(f"{label} is invalid JSON at line {exc.lineno}.")
    else:
        if isinstance(loaded, dict):
            payload = loaded
            if loaded.get("accepted") is not True:
                failures.append(f"{label} is not accepted.")
        else:
            failures.append(f"{label} must be a JSON object.")

    return {
        "accepted": not failures,
        "schema_version": payload.get("schema_version"),
        "failures": failures,
    }


def _verification_failures(verifications: dict[str, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for artifact_id, verification in verifications.items():
        if verification.get("accepted") is True:
            continue
        nested_failures = verification.get("failures", [])
        if isinstance(nested_failures, list) and nested_failures:
            failures.extend(
                f"{artifact_id}: {failure}"
                for failure in nested_failures
                if isinstance(failure, str)
            )
        else:
            failures.append(f"{artifact_id}: verification did not accept artifact.")
    return failures
