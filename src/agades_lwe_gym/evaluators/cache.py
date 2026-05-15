from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonFileCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text())
        value = data.get(key)
        return value if isinstance(value, dict) else None

    def set(self, key: str, value: dict[str, Any]) -> None:
        data: dict[str, Any] = {}
        if self.path.exists():
            data = json.loads(self.path.read_text())
        data[key] = value
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

