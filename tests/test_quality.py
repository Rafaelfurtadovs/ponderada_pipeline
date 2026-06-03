from __future__ import annotations

import time

import pytest

from pipeline_lab import (
    calculate_quality_score,
    detect_outliers,
    moving_average,
    normalize_readings,
    summarize_readings,
)
from tests.conftest import scenario


def test_normalize_readings_scales_values_between_zero_and_one():
    assert normalize_readings([10, 20, 30]) == [0.0, 0.5, 1.0]


def test_normalize_readings_handles_constant_series():
    assert normalize_readings([5, 5, 5]) == [0.0, 0.0, 0.0]


def test_moving_average_uses_fixed_window():
    assert moving_average([2, 4, 6, 8], 2) == [3, 5, 7]


def test_moving_average_rejects_invalid_window():
    with pytest.raises(ValueError, match="window"):
        moving_average([1, 2, 3], 0)


def test_summarize_readings_returns_descriptive_statistics():
    summary = summarize_readings([4, 1, 7, 8])

    assert summary.count == 4
    assert summary.minimum == 1
    assert summary.maximum == 8
    assert summary.average == 5
    assert summary.median == 5.5


def test_detect_outliers_flags_extreme_values():
    assert detect_outliers([10, 11, 10, 9, 90], threshold=1.5) == [90]


def test_quality_score_penalizes_outliers():
    clean_score = calculate_quality_score([10, 11, 12, 13])
    noisy_score = calculate_quality_score([10, 11, 12, 90])

    assert clean_score > noisy_score


def test_generated_metric_case(generated_case: int):
    active_scenario = scenario()
    delay = float(active_scenario["slow_test_delay_seconds"])
    if delay:
        time.sleep(delay)

    values = [generated_case, generated_case + 1, generated_case + 2, generated_case + 3]
    summary = summarize_readings(values)

    if active_scenario["failing_case"] == generated_case:
        pytest.fail(f"falha intencional do cenario {active_scenario['scenario_id']}")

    assert summary.count == 4
    assert summary.maximum - summary.minimum == 3
