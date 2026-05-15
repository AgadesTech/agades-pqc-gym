from __future__ import annotations

from pathlib import Path

import typer

from agades_lwe_gym.cli import export_public


def main(trace_path: Path, out: Path = Path("public/trace_public.jsonl")) -> None:
    export_public(trace_path=trace_path, out=out)


if __name__ == "__main__":
    typer.run(main)

