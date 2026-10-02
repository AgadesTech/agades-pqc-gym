import subprocess
import sys


def test_public_tree_has_no_internal_material() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_public_tree.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
