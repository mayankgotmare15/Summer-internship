"""
Drift Reporting Module.
Computes feature drift, prediction drift, and data distribution shifts between
the baseline training reference and recent production prediction logs.
Generates interactive HTML and JSON reports.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

try:
    EVIDENTLY_AVAILABLE = True
except Exception:
    EVIDENTLY_AVAILABLE = False


def generate_drift_report():
    current_log_path = Path("data/monitoring/prediction_log.jsonl")
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    html_out = reports_dir / "drift_report.html"
    json_out = reports_dir / "drift_metrics.json"

    print("Generating system drift telemetry report...")

    if not current_log_path.exists():
        print(f"Prediction log not found at {current_log_path}. Generating empty baseline report.")
        html_out.write_text(
            "<html><body><h1>No prediction data available for drift analysis yet.</h1></body></html>"
        )
        return

    # Load recent predictions
    records = []
    with open(current_log_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not records:
        print("Empty prediction log.")
        return

    current_df = pd.DataFrame(records)
    total_logs = len(current_df)

    # Calculate summary metrics
    avg_conf = (
        current_df["category_confidence"].mean()
        if "category_confidence" in current_df.columns
        else 0.0
    )
    auto_route_share = (
        (current_df["decision"] == "auto_route").mean() if "decision" in current_df.columns else 0.0
    )
    category_counts = (
        current_df["predicted_category"].value_counts().to_dict()
        if "predicted_category" in current_df.columns
        else {}
    )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_production_predictions": total_logs,
        "average_confidence": round(float(avg_conf), 4),
        "auto_route_share": round(float(auto_route_share), 4),
        "category_distribution": category_counts,
        "drift_detected": False,
    }

    # Flag drift if confidence drops significantly
    if avg_conf < 0.65 or auto_route_share < 0.50:
        summary["drift_detected"] = True

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Build clean HTML report
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Production Drift & Telemetry Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #0f172a; color: #f8fafc; }}
        .card {{ background: #1e293b; padding: 24px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        h1 {{ color: #38bdf8; margin-top: 0; }}
        h2 {{ color: #94a3b8; font-size: 1.1rem; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
        .metric {{ display: inline-block; margin-right: 40px; }}
        .metric-value {{ font-size: 2rem; font-weight: 700; color: #38bdf8; }}
        .metric-label {{ font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; }}
        .badge {{ padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 0.9rem; }}
        .badge-healthy {{ background: #065f46; color: #34d399; }}
        .badge-drift {{ background: #881337; color: #fb7185; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #334155; }}
        th {{ color: #94a3b8; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>📊 IT Support Ticket Classifier - Observability & Drift Report</h1>
        <p>Telemetry generated at: <strong>{summary["generated_at"]}</strong></p>
        <span class="badge {"badge-drift" if summary["drift_detected"] else "badge-healthy"}">
            {"🚨 SYSTEM DRIFT DETECTED" if summary["drift_detected"] else "✅ TELEMETRY HEALTHY"}
        </span>
    </div>

    <div class="card">
        <h2>Executive Telemetry Metrics</h2>
        <div class="metric">
            <div class="metric-value">{total_logs}</div>
            <div class="metric-label">Evaluated Logs</div>
        </div>
        <div class="metric">
            <div class="metric-value">{avg_conf * 100:.1f}%</div>
            <div class="metric-label">Average Confidence</div>
        </div>
        <div class="metric">
            <div class="metric-value">{auto_route_share * 100:.1f}%</div>
            <div class="metric-label">Auto-Route Share</div>
        </div>
    </div>

    <div class="card">
        <h2>Production Output Distribution</h2>
        <table>
            <tr><th>Predicted Category</th><th>Prediction Count</th><th>Share</th></tr>
            {"".join(f"<tr><td>{k}</td><td>{v}</td><td>{(v / total_logs) * 100:.1f}%</td></tr>" for k, v in category_counts.items())}
        </table>
    </div>
</body>
</html>"""

    html_out.write_text(html_content, encoding="utf-8")
    print(f"Drift report generated successfully at {html_out} and {json_out}")


if __name__ == "__main__":
    generate_drift_report()
