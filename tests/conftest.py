from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache
def scenario() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "experiment_scenario.json"
    return json.loads(path.read_text(encoding="utf-8"))


def pytest_generate_tests(metafunc):
    if "generated_case" in metafunc.fixturenames:
        count = int(scenario()["generated_test_count"])
        metafunc.parametrize("generated_case", range(count))
