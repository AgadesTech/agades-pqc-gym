from __future__ import annotations

from pathlib import Path

import typer

from agades_pqc_gym.cli import evaluate_attack_plan


def main(plan_path: Path, out: Path = Path("runs/eval_trace.jsonl")) -> None:
    evaluate_attack_plan(plan_path=plan_path, out=out)


if __name__ == "__main__":
    typer.run(main)

