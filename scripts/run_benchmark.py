from __future__ import annotations

from pathlib import Path

import typer

from agades_pqc_gym.cli import benchmark


def main(benchmark_path: Path, out: Path = Path("runs/benchmark_trace.jsonl")) -> None:
    benchmark(benchmark_path=benchmark_path, out=out)


if __name__ == "__main__":
    typer.run(main)

