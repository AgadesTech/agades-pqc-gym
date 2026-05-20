from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

LATTICE_ESTIMATOR_REPOSITORY = "https://github.com/malb/lattice-estimator"


@dataclass(frozen=True)
class LatticeEstimatorCheckoutInspection:
    source_path: Path
    head_commit: str | None
    head_matches_required_pin: bool
    remote_origin: str | None
    remote_matches_upstream: bool
    working_tree_clean: bool
    estimator_package: bool
    estimator_module: bool
    failures: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.failures


def inspect_lattice_estimator_checkout(
    source_path: Path,
    *,
    required_commit: str | None,
    upstream_repository: str = LATTICE_ESTIMATOR_REPOSITORY,
) -> LatticeEstimatorCheckoutInspection:
    resolved_source = source_path.resolve()
    failures: list[str] = []

    if not resolved_source.is_dir():
        failures.append(
            f"Local Lattice Estimator checkout is not a directory: {resolved_source}"
        )
        return LatticeEstimatorCheckoutInspection(
            source_path=resolved_source,
            head_commit=None,
            head_matches_required_pin=False,
            remote_origin=None,
            remote_matches_upstream=False,
            working_tree_clean=False,
            estimator_package=False,
            estimator_module=False,
            failures=tuple(failures),
        )

    head_commit = _git_stdout(resolved_source, "rev-parse", "HEAD")
    if head_commit is None:
        failures.append(
            "could not verify local Lattice Estimator checkout commit: "
            "git rev-parse HEAD failed"
        )
    elif not _is_full_sha1(head_commit):
        failures.append(
            "Local Lattice Estimator checkout HEAD is not a full lowercase SHA-1."
        )
        head_commit = None

    head_matches_required_pin = (
        required_commit is None or head_commit == required_commit
    )
    if (
        required_commit is not None
        and head_commit is not None
        and not head_matches_required_pin
    ):
        failures.append(
            f"Local Lattice Estimator checkout commit {head_commit} does not "
            f"match reviewed pin {required_commit}."
        )

    remote_origin = _git_stdout(resolved_source, "remote", "get-url", "origin")
    remote_matches_upstream = _remote_matches_upstream(
        remote_origin,
        upstream_repository=upstream_repository,
    )
    if remote_origin is None:
        failures.append("Local Lattice Estimator checkout has no origin remote.")
    elif not remote_matches_upstream:
        failures.append(
            "Local Lattice Estimator checkout origin remote "
            f"{remote_origin} does not match reviewed upstream "
            f"{upstream_repository}."
        )

    status = _git_stdout(resolved_source, "status", "--porcelain")
    working_tree_clean = status == ""
    if status is None:
        failures.append(
            "could not verify local Lattice Estimator checkout working tree."
        )
    elif not working_tree_clean:
        failures.append("Local Lattice Estimator checkout working tree is not clean.")

    estimator_package = (resolved_source / "estimator" / "__init__.py").is_file()
    estimator_module = (resolved_source / "estimator.py").is_file()
    if not estimator_package and not estimator_module:
        failures.append(
            "Local Lattice Estimator checkout does not contain an estimator "
            "package or module."
        )

    return LatticeEstimatorCheckoutInspection(
        source_path=resolved_source,
        head_commit=head_commit,
        head_matches_required_pin=head_matches_required_pin,
        remote_origin=remote_origin,
        remote_matches_upstream=remote_matches_upstream,
        working_tree_clean=working_tree_clean,
        estimator_package=estimator_package,
        estimator_module=estimator_module,
        failures=tuple(failures),
    )


def _git_stdout(source_path: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(source_path), *args],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _is_full_sha1(value: str) -> bool:
    return len(value) == 40 and all(
        character in "0123456789abcdef" for character in value
    )


def _remote_matches_upstream(
    remote_origin: str | None,
    *,
    upstream_repository: str,
) -> bool:
    if remote_origin is None:
        return False
    return _canonical_github_remote(remote_origin) == _canonical_github_remote(
        upstream_repository
    )


def _canonical_github_remote(remote_origin: str) -> str:
    remote = remote_origin.strip()
    if remote.startswith("git@github.com:"):
        remote = f"https://github.com/{remote.removeprefix('git@github.com:')}"
    elif remote.startswith("ssh://git@github.com/"):
        remote = f"https://github.com/{remote.removeprefix('ssh://git@github.com/')}"
    if remote.endswith(".git"):
        remote = remote.removesuffix(".git")
    return remote.removesuffix("/")
