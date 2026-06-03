"""Funcoes de exemplo usadas no experimento de CI/CD."""

from pipeline_lab.quality import (
    calculate_quality_score,
    detect_outliers,
    moving_average,
    normalize_readings,
    summarize_readings,
)

__all__ = [
    "calculate_quality_score",
    "detect_outliers",
    "moving_average",
    "normalize_readings",
    "summarize_readings",
]
