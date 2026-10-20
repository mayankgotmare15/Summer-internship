"""Unit tests for model drift monitoring and threshold alerting."""

from pathlib import Path

import pandas as pd

from src.models.retrain import build_augmented_training_data
from src.monitoring.check_thresholds import check_thresholds
from src.monitoring.drift_report import calculate_category_drift, calculate_distribution


def test_calculate_distribution() -> None:
    series = pd.Series(["Hardware", "Hardware", "Access", "Storage"])
    dist = calculate_distribution(series)
    assert dist["Hardware"] == 0.50
    assert dist["Access"] == 0.25
    assert dist["Storage"] == 0.25


def test_calculate_category_drift() -> None:
    ref = {"Hardware": 0.5, "Access": 0.5}
    curr_identical = {"Hardware": 0.5, "Access": 0.5}
    curr_shifted = {"Hardware": 0.1, "Access": 0.1, "Storage": 0.8}

    # Identical distributions should have TVD = 0
    assert calculate_category_drift(ref, curr_identical) == 0.0

    # Shifted distribution should have significant TVD
    drift = calculate_category_drift(ref, curr_shifted)
    assert drift > 0.50


def test_check_thresholds_healthy(tmp_path: Path) -> None:
    metrics_file = tmp_path / "healthy_metrics.json"
    alert_file = tmp_path / "alert_summary.json"

    metrics_content = (
        '{"low_confidence_rate": 0.12, "override_rate": 0.05, "category_drift_score": 0.08, '
        '"dataset_drift_detected": false, "sample_count": 200}'
    )
    metrics_file.write_text(metrics_content, encoding="utf-8")

    is_healthy, summary = check_thresholds(
        metrics_path=metrics_file,
        alert_output_path=alert_file,
        max_low_conf_rate=0.25,
        max_override_rate=0.15,
        max_cat_drift_score=0.15,
    )
    assert is_healthy is True
    assert summary["status"] == "HEALTHY"
    assert summary["recommended_action"] == "none"


def test_check_thresholds_breach(tmp_path: Path) -> None:
    metrics_file = tmp_path / "breached_metrics.json"
    alert_file = tmp_path / "alert_summary.json"

    metrics_content = (
        '{"low_confidence_rate": 0.65, "override_rate": 0.40, "category_drift_score": 0.28, '
        '"dataset_drift_detected": true, "sample_count": 200}'
    )
    metrics_file.write_text(metrics_content, encoding="utf-8")

    is_healthy, summary = check_thresholds(
        metrics_path=metrics_file,
        alert_output_path=alert_file,
        max_low_conf_rate=0.25,
        max_override_rate=0.15,
        max_cat_drift_score=0.15,
    )
    assert is_healthy is False
    assert summary["status"] == "ALERT_BREACHED"
    assert summary["recommended_action"] == "retrain_challenger"
    assert len(summary["breaches"]) >= 3


def test_build_augmented_training_data() -> None:
    df_train, df_val, df_test = build_augmented_training_data()
    assert len(df_train) > 30000
    assert "Storage" in df_train["category"].values
    assert "Storage" in df_val["category"].values
    assert "Storage" in df_test["category"].values
