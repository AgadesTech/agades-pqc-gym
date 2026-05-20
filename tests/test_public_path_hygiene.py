import subprocess
from pathlib import Path

FORBIDDEN_LOCAL_PATH_MARKERS = (
    "/".join(("", "Users", "zlaabsi")),
    "/".join(("", "mnt", "data")),
    "sandbox" + ":",
)


def test_tracked_public_files_do_not_expose_local_workspace_paths() -> None:
    tracked = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    leaks: list[str] = []
    for relative_path in tracked:
        path = Path(relative_path)
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for marker in FORBIDDEN_LOCAL_PATH_MARKERS:
            if marker in content:
                leaks.append(f"{relative_path}: contains {marker}")

    assert leaks == []
