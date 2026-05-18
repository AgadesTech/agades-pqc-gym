from __future__ import annotations

import argparse
import json
from pathlib import Path

from agades_pqc_gym.verifier import verify_attack_plan_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Agades PQC Gym public AttackPlan verifier."
    )
    parser.add_argument("attack_plan", type=Path)
    args = parser.parse_args()

    result = verify_attack_plan_path(args.attack_plan)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
