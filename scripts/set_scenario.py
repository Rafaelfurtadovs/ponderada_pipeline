from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_fail(value: str) -> int | None:
    if value.lower() in {"none", "null", "-"}:
        return None
    return int(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Atualiza experiment_scenario.json.")
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--mode", choices=["parallel", "sequential"], required=True)
    parser.add_argument("--cache", choices=["enabled", "disabled"], required=True)
    parser.add_argument("--tests", type=int, required=True)
    parser.add_argument("--delay", type=float, required=True)
    parser.add_argument("--fail", default="none")
    parser.add_argument("--notes", default="")
    parser.add_argument("--path", type=Path, default=Path("experiment_scenario.json"))
    args = parser.parse_args()

    scenario = {
        "scenario_id": args.scenario_id,
        "execution_mode": args.mode,
        "cache": args.cache,
        "generated_test_count": args.tests,
        "slow_test_delay_seconds": args.delay,
        "failing_case": parse_fail(args.fail),
        "notes": args.notes,
    }
    args.path.write_text(
        json.dumps(scenario, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
