from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agades_lwe_gym.reporting.markdown import render_report


def load_jsonl_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def render_report_from_jsonl(path: Path, title: str) -> str:
    return render_report(title=title, records=load_jsonl_records(path))

