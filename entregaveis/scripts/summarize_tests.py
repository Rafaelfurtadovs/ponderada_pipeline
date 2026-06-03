from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree


def parse_junit(path: Path) -> dict[str, float | int]:
    if not path.exists():
        return {"test_count": 0, "test_failures": 0, "test_errors": 0, "test_time": 0.0}

    root = ElementTree.parse(path).getroot()
    suites = root.findall("testsuite") if root.tag == "testsuites" else [root]

    test_count = 0
    failures = 0
    errors = 0
    test_time = 0.0

    for suite in suites:
        test_count += int(suite.attrib.get("tests", 0))
        failures += int(suite.attrib.get("failures", 0))
        errors += int(suite.attrib.get("errors", 0))
        test_time += float(suite.attrib.get("time", 0.0))

    return {
        "test_count": test_count,
        "test_failures": failures,
        "test_errors": errors,
        "test_time": round(test_time, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume o JUnit XML gerado pelo Pytest.")
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    summary = parse_junit(args.junit)
    scenario = json.loads(args.scenario.read_text(encoding="utf-8"))
    test_count = int(summary["test_count"])
    summary["test_average_time"] = (
        round(float(summary["test_time"]) / test_count, 4) if test_count else 0
    )
    summary["scenario"] = scenario

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
