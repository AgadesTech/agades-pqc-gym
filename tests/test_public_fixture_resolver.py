from __future__ import annotations

from pathlib import Path

import pytest

from agades_pqc_gym.families.fixtures import (
    is_scoped_public_fixture_path,
    resolve_public_fixture_path,
)

ROOT_PARTS = ("benchmarks", "toy_family", "fixtures")


def test_scoped_public_fixture_paths_accept_only_one_json_file_under_scope() -> None:
    assert is_scoped_public_fixture_path(
        Path("benchmarks/toy_family/fixtures/fixture.json"),
        ROOT_PARTS,
    )
    assert not is_scoped_public_fixture_path(
        Path("benchmarks/toy_family/fixtures/nested/fixture.json"),
        ROOT_PARTS,
    )
    assert not is_scoped_public_fixture_path(
        Path("benchmarks/toy_family/fixtures/../fixture.json"),
        ROOT_PARTS,
    )
    assert not is_scoped_public_fixture_path(
        Path("benchmarks/toy_family/fixtures/fixture.txt"),
        ROOT_PARTS,
    )


def test_resolve_public_fixture_path_prefers_checked_out_fixture(
    tmp_path: Path,
) -> None:
    fixture_dir = tmp_path.joinpath(*ROOT_PARTS)
    fixture_dir.mkdir(parents=True)
    checkout_fixture = fixture_dir / "fixture.json"
    checkout_fixture.write_text("{}", encoding="utf-8")

    path, warnings = resolve_public_fixture_path(
        "benchmarks/toy_family/fixtures/fixture.json",
        repo_root=tmp_path,
        package_fixture_dir=tmp_path / "package-fixtures",
        root_parts=ROOT_PARTS,
        family_label="TOY",
    )

    assert path == checkout_fixture
    assert warnings == []


def test_resolve_public_fixture_path_uses_packaged_fixture_when_checkout_missing(
    tmp_path: Path,
) -> None:
    package_fixture_dir = tmp_path / "package-fixtures"
    package_fixture_dir.mkdir()
    package_fixture = package_fixture_dir / "fixture.json"
    package_fixture.write_text("{}", encoding="utf-8")

    path, warnings = resolve_public_fixture_path(
        "benchmarks/toy_family/fixtures/fixture.json",
        repo_root=tmp_path,
        package_fixture_dir=package_fixture_dir,
        root_parts=ROOT_PARTS,
        family_label="TOY",
    )

    assert path == package_fixture
    assert warnings == []


def test_resolve_public_fixture_path_rejects_unscoped_paths(tmp_path: Path) -> None:
    path, warnings = resolve_public_fixture_path(
        "benchmarks/toy_family/not-fixtures/fixture.json",
        repo_root=tmp_path,
        package_fixture_dir=tmp_path / "package-fixtures",
        root_parts=ROOT_PARTS,
        family_label="TOY",
    )

    assert path is None
    assert warnings == [
        "TOY reproduction fixtures must be relative paths under "
        "benchmarks/toy_family/fixtures/."
    ]


def test_resolve_public_fixture_path_rejects_checkout_symlink_escape(
    tmp_path: Path,
) -> None:
    fixture_dir = tmp_path.joinpath(*ROOT_PARTS)
    fixture_dir.mkdir(parents=True)
    outside_fixture = tmp_path / "outside.json"
    outside_fixture.write_text("{}", encoding="utf-8")
    symlink_fixture = fixture_dir / "fixture.json"
    _symlink_or_skip(symlink_fixture, outside_fixture)

    path, warnings = resolve_public_fixture_path(
        "benchmarks/toy_family/fixtures/fixture.json",
        repo_root=tmp_path,
        package_fixture_dir=tmp_path / "package-fixtures",
        root_parts=ROOT_PARTS,
        family_label="TOY",
    )

    assert path is None
    assert warnings == [
        "TOY reproduction fixture resolves outside "
        "benchmarks/toy_family/fixtures/."
    ]


def test_resolve_public_fixture_path_rejects_package_symlink_escape(
    tmp_path: Path,
) -> None:
    package_fixture_dir = tmp_path / "package-fixtures"
    package_fixture_dir.mkdir()
    outside_fixture = tmp_path / "outside.json"
    outside_fixture.write_text("{}", encoding="utf-8")
    symlink_fixture = package_fixture_dir / "fixture.json"
    _symlink_or_skip(symlink_fixture, outside_fixture)

    path, warnings = resolve_public_fixture_path(
        "benchmarks/toy_family/fixtures/fixture.json",
        repo_root=tmp_path,
        package_fixture_dir=package_fixture_dir,
        root_parts=ROOT_PARTS,
        family_label="TOY",
    )

    assert path is None
    assert warnings == ["TOY package fixture resolves outside package fixture dir."]


def _symlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable in this environment: {exc}")
