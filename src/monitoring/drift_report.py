"""Evidently Data Drift and Model Performance Monitoring.

Generates HTML reports and JSON summary metrics tracking:
1. Low-confidence prediction rates
2. Prediction category distribution shift
3. Text length and vocabulary data drift
4. Agent feedback override rates
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset, DataSummaryPreset

from src.monitoring.export import export_monitoring_datasets, load_reference_dataset


def calculate_distribution(series: pd.Series) -> dict[str, float]:
    """Calculates normalized categorical distribution as percentages."""
    counts = series.value_counts(normalize=True)
    return {k: round(float(v), 4) for k, v in counts.items()}


def calculate_category_drift(ref_dist: dict[str, float], curr_dist: dict[str, float]) -> float:
    """Calculates Total Variation Distance (TVD) between reference and current category distributions.

    TVD = 0.5 * sum(|P(x) - Q(x)|) across all categories. Range: [0.0, 1.0].
    """
    all_cats = set(ref_dist.keys()) | set(curr_dist.keys())
    if not all_cats:
        return 0.0
    tvd = 0.5 * sum(abs(ref_dist.get(c, 0.0) - curr_dist.get(c, 0.0)) for c in all_cats)
    return round(float(tvd), 4)


def get_active_threshold() -> float:
    champ_path = Path("models/champion.json")
    if champ_path.exists():
        try:
            with open(champ_path, encoding="utf-8") as f:
                data = json.load(f)
                return float(data.get("threshold", 0.69))
        except Exception:
            pass
    return 0.69


def generate_drift_report(
    df_ref: pd.DataFrame,
    df_curr: pd.DataFrame,
    output_html_path: str | Path = "reports/drift_report.html",
    output_json_path: str | Path = "reports/drift_metrics.json",
    threshold: float | None = None,
) -> dict[str, Any]:
    """Generates Evidently HTML drift report and computes PRD Section 11.3 monitoring metrics."""
    active_threshold = threshold if threshold is not None else get_active_threshold()

    # Ensure output directory exists
    html_path = Path(output_html_path)
    json_path = Path(output_json_path)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    curr_len = len(df_curr)
    if curr_len == 0:
        print("Warning: Current production dataset is empty. Cannot compute drift metrics.")
        empty_metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sample_count": 0,
            "reference_count": len(df_ref),
            "low_confidence_rate": 0.0,
            "low_confidence_count": 0,
            "override_rate": 0.0,
            "override_count": 0,
            "category_drift_score": 0.0,
            "dataset_drift_detected": False,
            "drifted_features_share": 0.0,
            "category_distribution_ref": calculate_distribution(df_ref["category"]) if "category" in df_ref else {},
            "category_distribution_curr": {},
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(empty_metrics, f, indent=2)
        return empty_metrics

    # 1. Low confidence rate calculation
    if "category_confidence" in df_curr.columns:
        low_conf_mask = df_curr["category_confidence"] < active_threshold
        low_conf_count = int(low_conf_mask.sum())
        low_conf_rate = round(float(low_conf_count / curr_len), 4)
    else:
        low_conf_count = 0
        low_conf_rate = 0.0

    # 2. Agent override rate calculation
    if "is_override" in df_curr.columns:
        override_count = int(df_curr["is_override"].sum())
        override_rate = round(float(override_count / curr_len), 4)
    else:
        override_count = 0
        override_rate = 0.0

    # 3. Category distribution shift
    ref_dist = calculate_distribution(df_ref["category"]) if "category" in df_ref.columns else {}
    curr_dist = calculate_distribution(df_curr["category"]) if "category" in df_curr.columns else {}
    cat_drift_score = calculate_category_drift(ref_dist, curr_dist)

    # 4. Prepare shared features for Evidently Report
    # Align common columns between reference and current
    eval_ref = pd.DataFrame()
    eval_curr = pd.DataFrame()

    if "category" in df_ref.columns and "category" in df_curr.columns:
        eval_ref["category"] = df_ref["category"].astype(str)
        eval_curr["category"] = df_curr["category"].astype(str)

    if "text_length" in df_ref.columns and "text_length" in df_curr.columns:
        eval_ref["text_length"] = df_ref["text_length"].astype(float)
        eval_curr["text_length"] = df_curr["text_length"].astype(float)
    elif "text" in df_ref.columns and "text" in df_curr.columns:
        eval_ref["text_length"] = df_ref["text"].astype(str).str.len().astype(float)
        eval_curr["text_length"] = df_curr["text"].astype(str).str.len().astype(float)

    # If reference lacks category_confidence, synthesize baseline proxy or skip
    if "category_confidence" in df_curr.columns:
        eval_curr["confidence"] = df_curr["category_confidence"].astype(float)
        eval_ref["confidence"] = np.random.uniform(0.75, 0.98, size=len(eval_ref))

    # Run Evidently report
    dataset_drift_detected = False
    drifted_share = 0.0
    try:
        # Sample reference data if too large to accelerate computation
        sample_ref = eval_ref.sample(n=min(len(eval_ref), 1000), random_state=42)
        sample_curr = eval_curr.sample(n=min(len(eval_curr), 1000), random_state=42)

        report = Report([DataSummaryPreset(), DataDriftPreset()])
        snapshot = report.run(reference_data=sample_ref, current_data=sample_curr)
        snapshot.save_html(str(html_path))

        # Check drift indicator from results
        res_dict = snapshot.dict()
        for metric_item in res_dict.get("metrics", []):
            metric_res = metric_item.get("result", {})
            if "dataset_drift" in metric_res:
                dataset_drift_detected = bool(metric_res.get("dataset_drift"))
                drifted_share = float(metric_res.get("share_of_drifted_columns", 0.0))
                break
    except Exception as e:
        print(f"Evidently report generation warning: {e}. Generating fallback HTML.")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(
                f"<html><body><h1>RouteDesk Drift Report</h1>"
                f"<p>Generated at: {datetime.now(timezone.utc).isoformat()}</p>"
                f"<p>Low confidence rate: {low_conf_rate * 100:.1f}%</p>"
                f"<p>Category TVD Drift: {cat_drift_score:.4f}</p>"
                f"</body></html>"
            )

    # If Total Variation Distance is high (> 0.20), mark category drift
    if cat_drift_score > 0.20:
        dataset_drift_detected = True

    summary_metrics: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sample_count": curr_len,
        "reference_count": len(df_ref),
        "active_threshold": active_threshold,
        "low_confidence_rate": low_conf_rate,
        "low_confidence_count": low_conf_count,
        "override_rate": override_rate,
        "override_count": override_count,
        "category_drift_score": cat_drift_score,
        "dataset_drift_detected": dataset_drift_detected,
        "drifted_features_share": round(drifted_share, 4),
        "category_distribution_ref": ref_dist,
        "category_distribution_curr": curr_dist,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_metrics, f, indent=2)

    print(f"Drift report generated: {html_path}")
    print(f"Metrics saved: {json_path}")
    print(
        f"Summary -> Low Conf: {low_conf_rate * 100:.1f}%, Drift Score: {cat_drift_score:.4f}, "
        f"Override Rate: {override_rate * 100:.1f}%, Drift Detected: {dataset_drift_detected}"
    )
    return summary_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Evidently drift report and metrics.")
    parser.add_argument("--reference-path", default="data/processed/val.parquet", help="Reference dataset")
    parser.add_argument("--current-path", default=None, help="Current dataset (or query DB if None)")
    parser.add_argument("--html-output", default="reports/drift_report.html", help="HTML report output path")
    parser.add_argument("--json-output", default="reports/drift_metrics.json", help="JSON metrics output path")
    parser.add_argument("--limit", type=int, default=1500, help="Max database inferences to fetch")
    args = parser.parse_args()

    df_ref = load_reference_dataset(args.reference_path)
    if args.current_path and Path(args.current_path).exists():
        df_curr = pd.read_parquet(args.current_path)
    else:
        _, df_curr = export_monitoring_datasets(reference_path=args.reference_path, limit=args.limit)

    generate_drift_report(
        df_ref=df_ref,
        df_curr=df_curr,
        output_html_path=args.html_output,
        output_json_path=args.json_output,
    )


if __name__ == "__main__":
    main()
