#!/usr/bin/env python3
"""Block internal or sensitive material from entering the public repository.

Checks every tracked (or staged) file for:
- paths reserved for internal working notes (agent rule files, planning
  scratchpads, briefs, strategy notes, private roots);
- secret-like tokens (API keys, private keys);
- personal email addresses (only example.com and GitHub noreply are allowed);
- terms listed in an optional, untracked ``.public-denylist`` file (one term per
  line), so sensitive names never have to be written into the repository.

Exit code 1 means the public tree is not clean. Run it locally with
``python scripts/check_public_tree.py`` or through pre-commit.
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN_PATH_GLOBS = (
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".codex/*",
    ".claude/*",
    ".cursor/*",
    "notes/*",
    "scratchpad/*",
    "private/*",
    "docs/internal/*",
    "docs/superpowers/*",
    "docs/*BRIEF*",
    "docs/*STRATEGY*",
    "*.private.*",
    ".env",
    ".env.local",
)
SECRET_PATTERNS = (
    re.compile(r"sk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}"),
    re.compile(r"hf_[A-Za-z0-9]{30,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ALLOWED_EMAIL_SUFFIXES = (
    "@example.com",
    "@users.noreply.github.com",
    "git@github.com",
)
SKIPPED_CONTENT_FILES = {"uv.lock", "scripts/check_public_tree.py"}
DENYLIST_FILE = Path(".public-denylist")


def tracked_files(staged_only: bool) -> list[str]:
    if staged_only:
        cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"]
    else:
        cmd = ["git", "ls-files"]
    output = subprocess.check_output(cmd, text=True)
    return [line for line in output.splitlines() if line]


def load_denylist() -> list[str]:
    if not DENYLIST_FILE.is_file():
        return []
    return [
        line.strip()
        for line in DENYLIST_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def check(paths: list[str]) -> list[str]:
    failures: list[str] = []
    denylist = [term.lower() for term in load_denylist()]
    for path in paths:
        for pattern in FORBIDDEN_PATH_GLOBS:
            if fnmatch.fnmatch(path, pattern):
                failures.append(
                    f"{path}: path is reserved for internal material ({pattern})"
                )
        if path in SKIPPED_CONTENT_FILES:
            continue
        file_path = Path(path)
        if not file_path.is_file():
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(
                    f"{path}: secret-like token matches {pattern.pattern!r}"
                )
        for email in set(EMAIL_PATTERN.findall(text)):
            if not email.endswith(ALLOWED_EMAIL_SUFFIXES):
                failures.append(f"{path}: contains an email address ({email})")
        lowered = text.lower()
        for term in denylist:
            if term in lowered:
                failures.append(f"{path}: contains a denylisted term")
    return failures


def main(argv: list[str]) -> int:
    failures = check(tracked_files(staged_only="--staged" in argv))
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        print(f"public tree check failed: {len(failures)} issue(s)", file=sys.stderr)
        return 1
    print("public tree check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
