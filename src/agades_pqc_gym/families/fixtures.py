from __future__ import annotations

from pathlib import Path


def is_scoped_public_fixture_path(
    path: Path,
    root_parts: tuple[str, ...],
    *,
    suffix: str = ".json",
) -> bool:
    """Return whether a user-declared fixture path is a single public fixture."""

    return (
        not path.is_absolute()
        and path.parts[: len(root_parts)] == root_parts
        and len(path.parts) == len(root_parts) + 1
        and path.suffix == suffix
        and ".." not in path.parts
    )


def resolve_public_fixture_path(
    value: str,
    *,
    repo_root: Path,
    package_fixture_dir: Path,
    root_parts: tuple[str, ...],
    family_label: str,
    suffix: str = ".json",
) -> tuple[Path | None, list[str]]:
    """Resolve a public fixture from checkout or package data without escapes."""

    fixture_path = Path(value)
    fixture_scope = _fixture_scope(root_parts)
    if not is_scoped_public_fixture_path(
        fixture_path,
        root_parts,
        suffix=suffix,
    ):
        return (
            None,
            [
                f"{family_label} reproduction fixtures must be relative paths "
                f"under {fixture_scope}."
            ],
        )

    checkout_path = repo_root / fixture_path
    checkout_root = repo_root.joinpath(*root_parts).resolve(strict=False)
    if checkout_path.is_file():
        checkout_resolved = checkout_path.resolve(strict=True)
        if not _is_relative_to(checkout_resolved, checkout_root):
            return (
                None,
                [
                    f"{family_label} reproduction fixture resolves outside "
                    f"{fixture_scope}."
                ],
            )
        return checkout_path, []

    package_fixture = package_fixture_dir / fixture_path.name
    package_root = package_fixture_dir.resolve(strict=False)
    if package_fixture.is_file():
        package_resolved = package_fixture.resolve(strict=True)
        if not _is_relative_to(package_resolved, package_root):
            return (
                None,
                [
                    f"{family_label} package fixture resolves outside "
                    "package fixture dir."
                ],
            )
        return package_fixture, []

    return checkout_path, []


def _fixture_scope(root_parts: tuple[str, ...]) -> str:
    return "/".join(root_parts) + "/"


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
