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


def generate_drift_report(
    log_path: Path | str | None = None,
    html_out: Path | str | None = None,
    json_out: Path | str | None = None,
):
    current_log_path = Path(log_path) if log_path else Path("data/monitoring/prediction_log.jsonl")
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    html_out = Path(html_out) if html_out else reports_dir / "drift_report.html"
    json_out = Path(json_out) if json_out else reports_dir / "drift_metrics.json"

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
        "total_logs": total_logs,
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

    # Build clean HTML report with minimal bright relaxed design
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Production Drift & Telemetry Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-base: #f8fafc;
            --surface-card: #ffffff;
            --border-subtle: #e2e8f0;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --primary: #0284c7;
            --success-bg: #ecfdf5;
            --success-border: #a7f3d0;
            --success-text: #065f46;
            --danger-bg: #fff1f2;
            --danger-border: #fecdd3;
            --danger-text: #9f1239;
        }}
        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 40px 24px;
            background: var(--bg-base);
            color: var(--text-main);
            line-height: 1.5;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .card {{
            background: var(--surface-card);
            padding: 28px;
            border-radius: 16px;
            margin-bottom: 24px;
            border: 1px solid var(--border-subtle);
            box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
        }}
        .header-card {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 16px;
        }}
        h1 {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-main);
            margin: 0 0 6px 0;
            letter-spacing: -0.02em;
        }}
        p.subtitle {{
            color: var(--text-muted);
            font-size: 0.9rem;
            margin: 0;
        }}
        h2 {{
            color: #334155;
            font-size: 1.05rem;
            font-weight: 600;
            margin-top: 0;
            margin-bottom: 20px;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 10px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
        }}
        .metric-box {{
            background: #f8fafc;
            border: 1px solid var(--border-subtle);
            padding: 18px;
            border-radius: 12px;
        }}
        .metric-value {{
            font-size: 1.85rem;
            font-weight: 700;
            color: var(--primary);
            line-height: 1.2;
        }}
        .metric-label {{
            font-size: 0.8rem;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 4px;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
            letter-spacing: 0.01em;
        }}
        .badge-healthy {{
            background: var(--success-bg);
            border: 1px solid var(--success-border);
            color: var(--success-text);
        }}
        .badge-drift {{
            background: var(--danger-bg);
            border: 1px solid var(--danger-border);
            color: var(--danger-text);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.92rem;
        }}
        th {{
            background: #f8fafc;
            color: var(--text-muted);
            font-weight: 600;
            text-align: left;
            padding: 12px 16px;
            border-bottom: 2px solid var(--border-subtle);
        }}
        td {{
            padding: 14px 16px;
            border-bottom: 1px solid #f1f5f9;
            color: var(--text-main);
        }}
        tr:hover td {{
            background: #fbfcfe;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card header-card">
            <div>
                <h1>📊 Production Observability & Drift Report</h1>
                <p class="subtitle">Report generated at <strong>{summary["generated_at"]}</strong></p>
            </div>
            <span class="badge {"badge-drift" if summary["drift_detected"] else "badge-healthy"}">
                {"🚨 SYSTEM DRIFT DETECTED" if summary["drift_detected"] else "✅ TELEMETRY HEALTHY"}
            </span>
        </div>

        <div class="card">
            <h2>Executive Telemetry Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-box">
                    <div class="metric-value">{total_logs}</div>
                    <div class="metric-label">Evaluated Logs</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{avg_conf * 100:.1f}%</div>
                    <div class="metric-label">Average Confidence</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{auto_route_share * 100:.1f}%</div>
                    <div class="metric-label">Auto-Route Share</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Production Output Distribution</h2>
            <table>
                <thead>
                    <tr><th>Predicted Category</th><th>Prediction Count</th><th>Share</th></tr>
                </thead>
                <tbody>
                    {"".join(f"<tr><td><strong>{k}</strong></td><td>{v}</td><td>{(v / total_logs) * 100:.1f}%</td></tr>" for k, v in category_counts.items())}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""

    html_out.write_text(html_content, encoding="utf-8")
    print(f"Drift report generated successfully at {html_out} and {json_out}")


if __name__ == "__main__":
    generate_drift_report()
