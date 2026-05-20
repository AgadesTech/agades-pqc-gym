from __future__ import annotations

from typing import Any

from agades_pqc_gym.reporting.generator import ReportGenerator


def render_report(title: str, records: list[dict[str, Any]]) -> str:
    return ReportGenerator(title=title).render_markdown(records)
