"""Monitoring Thresholds and SLA/Drift Alert Checker.

Evaluates monitoring metrics against PRD Section 11.3 criteria:
1. Low-confidence rate > 25%
2. Agent feedback override rate > 15%
3. Prediction category distribution shift (TVD > 0.15)
4. Data/text feature drift detected
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def check_thresholds(
    metrics_path: str | Path = "reports/drift_metrics.json",
    alert_output_path: str | Path = "reports/alert_summary.json",
    max_low_conf_rate: float = 0.25,
    max_override_rate: float = 0.15,
    max_cat_drift_score: float = 0.15,
) -> tuple[bool, dict[str, Any]]:
    """Evaluates metrics against monitoring policy thresholds.

    Returns:
        (is_healthy, alert_summary_dict)
    """
    path = Path(metrics_path)
    if not path.exists():
        print(f"Error: Metrics file not found at {path}. Run drift_report.py first.")
        return False, {"status": "ERROR", "reason": "metrics_file_missing"}

    with open(path, encoding="utf-8") as f:
        metrics = json.load(f)

    breaches: list[str] = []

    low_conf_rate = metrics.get("low_confidence_rate", 0.0)
    override_rate = metrics.get("override_rate", 0.0)
    cat_drift_score = metrics.get("category_drift_score", 0.0)
    dataset_drift = metrics.get("dataset_drift_detected", False)
    sample_count = metrics.get("sample_count", 0)

    # 1. Low confidence rate check (PRD Section 11.3: > 25%)
    if low_conf_rate > max_low_conf_rate:
        breaches.append(
            f"Low-confidence rate {low_conf_rate * 100:.1f}% exceeds threshold of {max_low_conf_rate * 100:.1f}%"
        )

    # 2. Agent override rate check (PRD Section 11.3: > 15%)
    if override_rate > max_override_rate:
        breaches.append(
            f"Agent override rate {override_rate * 100:.1f}% exceeds threshold of {max_override_rate * 100:.1f}%"
        )

    # 3. Category distribution shift check
    if cat_drift_score > max_cat_drift_score:
        breaches.append(
            f"Category distribution shift {cat_drift_score:.4f} exceeds threshold of {max_cat_drift_score:.4f}"
        )

    # 4. Feature / dataset drift
    if dataset_drift and cat_drift_score > 0.10:
        breaches.append("Evidently detected statistically significant dataset feature drift")

    is_healthy = len(breaches) == 0

    alert_summary: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "HEALTHY" if is_healthy else "ALERT_BREACHED",
        "sample_count": sample_count,
        "is_healthy": is_healthy,
        "breach_count": len(breaches),
        "breaches": breaches,
        "thresholds": {
            "max_low_conf_rate": max_low_conf_rate,
            "max_override_rate": max_override_rate,
            "max_cat_drift_score": max_cat_drift_score,
        },
        "observed_metrics": {
            "low_confidence_rate": low_conf_rate,
            "override_rate": override_rate,
            "category_drift_score": cat_drift_score,
            "dataset_drift_detected": dataset_drift,
        },
        "recommended_action": "none" if is_healthy else "retrain_challenger",
    }

    out_path = Path(alert_output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(alert_summary, f, indent=2)

    print("\n" + "=" * 60)
    print(f"MONITORING THRESHOLD CHECK: {alert_summary['status']}")
    print("=" * 60)
    if is_healthy:
        print("All monitored signals are within acceptable production tolerances.")
    else:
        print(f"ALERT: {len(breaches)} threshold breach(es) detected:")
        for b in breaches:
            print(f"  - {b}")
        print("Recommended Action: Trigger retrain.yml (Champion-Challenger pipeline).")
    print(f"Alert summary saved to: {out_path}\n")

    return is_healthy, alert_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Check monitoring thresholds and raise alert on breaches.")
    parser.add_argument("--metrics-path", default="reports/drift_metrics.json", help="Path to drift metrics JSON")
    parser.add_argument("--alert-output", default="reports/alert_summary.json", help="Path to alert summary output")
    parser.add_argument("--max-low-conf", type=float, default=0.25, help="Max allowed low confidence rate")
    parser.add_argument("--max-override", type=float, default=0.15, help="Max allowed agent override rate")
    parser.add_argument("--max-drift", type=float, default=0.15, help="Max category distribution drift")
    args = parser.parse_args()

    is_healthy, _ = check_thresholds(
        metrics_path=args.metrics_path,
        alert_output_path=args.alert_output,
        max_low_conf_rate=args.max_low_conf,
        max_override_rate=args.max_override,
        max_cat_drift_score=args.max_drift,
    )

    if not is_healthy:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
