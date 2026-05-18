from __future__ import annotations

from pathlib import Path

import typer

from agades_pqc_gym.cli import report


def main(trace_path: Path, out: Path = Path("reports/report.md")) -> None:
    report(trace_path=trace_path, out=out)


if __name__ == "__main__":
    typer.run(main)

