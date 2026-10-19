"""
Unit tests for Monitoring, Telemetry, Drift Reporting, and Threshold Evaluation.
"""

import json
from pathlib import Path
import pytest

from src.monitoring.check_thresholds import evaluate_telemetry
from src.monitoring.drift_report import generate_drift_report
from src.monitoring.simulate_traffic import HELD_OUT_CATEGORY_SAMPLES, NORMAL_SAMPLES


def test_traffic_samples_structure():
    assert len(NORMAL_SAMPLES) > 0
    assert len(HELD_OUT_CATEGORY_SAMPLES) > 0
    assert all(isinstance(s, str) and len(s) > 10 for s in NORMAL_SAMPLES)
    assert any("storage" in s.lower() or "s3" in s.lower() or "disk" in s.lower() for s in HELD_OUT_CATEGORY_SAMPLES)


def test_generate_drift_report(tmp_path: Path, monkeypatch):
    test_log = tmp_path / "test_prediction_log.jsonl"
    html_out = tmp_path / "drift_report.html"
    json_out = tmp_path / "drift_metrics.json"

    # Write synthetic log records
    records = [
        {
            "timestamp": "2026-10-19T10:00:00Z",
            "ticket_id": f"tkt-{i}",
            "text_hash": "hash123",
            "predicted_category": "Hardware" if i % 2 == 0 else "Access",
            "category_confidence": 0.85 if i < 8 else 0.45,
            "predicted_priority": "Medium",
            "priority_confidence": 0.80,
            "decision": "auto_route" if i < 8 else "human_review",
            "routed_team": "Desktop Support & Hardware Services",
            "model_version": "1.0.0",
        }
        for i in range(10)
    ]
    with open(test_log, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    generate_drift_report(log_path=test_log, html_out=html_out, json_out=json_out)

    assert html_out.exists()
    assert json_out.exists()

    with open(json_out, encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_logs"] == 10
    assert "average_confidence" in data
    assert "auto_route_share" in data

    html_content = html_out.read_text(encoding="utf-8")
    assert "Production Observability & Drift Report" in html_content
    assert "Hardware" in html_content
    assert "Access" in html_content


def test_threshold_evaluation_passing(tmp_path: Path, monkeypatch):
    pred_log = tmp_path / "clean_preds.jsonl"
    feedback_log = tmp_path / "clean_feedback.jsonl"

    monkeypatch.setattr("src.monitoring.check_thresholds.PRED_LOG_PATH", pred_log)
    monkeypatch.setattr("src.monitoring.check_thresholds.FEEDBACK_LOG_PATH", feedback_log)

    # 10 confident predictions -> low_conf_rate = 0% < 25% threshold
    clean_preds = [
        {"decision": "auto_route", "predicted_category": "Hardware"}
        for _ in range(10)
    ]
    with open(pred_log, "w", encoding="utf-8") as f:
        for p in clean_preds:
            f.write(json.dumps(p) + "\n")

    # 10 matching feedbacks -> override_rate = 0% < 15% threshold
    clean_fb = [
        {"predicted_category": "Hardware", "corrected_category": "Hardware"}
        for _ in range(10)
    ]
    with open(feedback_log, "w", encoding="utf-8") as f:
        for fb in clean_fb:
            f.write(json.dumps(fb) + "\n")

    is_healthy = evaluate_telemetry()
    assert is_healthy is True


def test_threshold_evaluation_breach_detected(tmp_path: Path, monkeypatch):
    pred_log = tmp_path / "breached_preds.jsonl"
    feedback_log = tmp_path / "breached_feedback.jsonl"

    monkeypatch.setattr("src.monitoring.check_thresholds.PRED_LOG_PATH", pred_log)
    monkeypatch.setattr("src.monitoring.check_thresholds.FEEDBACK_LOG_PATH", feedback_log)

    # 5 out of 10 human review -> 50% > 25% threshold
    breached_preds = [
        {"decision": "human_review" if i < 5 else "auto_route", "predicted_category": "Hardware"}
        for i in range(10)
    ]
    with open(pred_log, "w", encoding="utf-8") as f:
        for p in breached_preds:
            f.write(json.dumps(p) + "\n")

    # 5 out of 10 overrides -> 50% > 15% threshold
    breached_fb = [
        {"predicted_category": "Hardware", "corrected_category": "Access" if i < 5 else "Hardware"}
        for i in range(10)
    ]
    with open(feedback_log, "w", encoding="utf-8") as f:
        for fb in breached_fb:
            f.write(json.dumps(fb) + "\n")

    is_healthy = evaluate_telemetry()
    assert is_healthy is False
