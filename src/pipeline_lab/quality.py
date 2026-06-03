from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean, median


@dataclass(frozen=True)
class ReadingSummary:
    count: int
    minimum: float
    maximum: float
    average: float
    median: float


def normalize_readings(values: list[float]) -> list[float]:
    if not values:
        return []

    low = min(values)
    high = max(values)
    spread = high - low
    if spread == 0:
        return [0.0 for _ in values]

    return [(value - low) / spread for value in values]


def moving_average(values: list[float], window: int) -> list[float]:
    if window <= 0:
        raise ValueError("window must be positive")
    if window > len(values):
        return []

    averages: list[float] = []
    for start in range(0, len(values) - window + 1):
        chunk = values[start : start + window]
        averages.append(mean(chunk))
    return averages


def summarize_readings(values: list[float]) -> ReadingSummary:
    if not values:
        raise ValueError("values cannot be empty")

    return ReadingSummary(
        count=len(values),
        minimum=min(values),
        maximum=max(values),
        average=mean(values),
        median=median(values),
    )


def detect_outliers(values: list[float], threshold: float = 2.0) -> list[float]:
    if len(values) < 2:
        return []

    average = mean(values)
    variance = mean([(value - average) ** 2 for value in values])
    deviation = sqrt(variance)
    if deviation == 0:
        return []

    return [value for value in values if abs((value - average) / deviation) >= threshold]


def calculate_quality_score(values: list[float]) -> float:
    if not values:
        return 0.0

    normalized = normalize_readings(values)
    stability_penalty = len(detect_outliers(values)) / len(values)
    return round((mean(normalized) * 100) * (1 - stability_penalty), 2)
