from __future__ import annotations

import shlex
from collections.abc import Sequence


def parse_command(command: str, *, label: str) -> list[str]:
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"{label} is not a valid command: {exc}") from exc
    if not parts:
        raise ValueError(f"{label} must not be empty.")
    return parts


def format_command(command: Sequence[str]) -> str:
    return shlex.join(list(command))
