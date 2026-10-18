"""
Evaluation and Threshold Optimization Module.
Computes test metrics, per-class reports, confusion matrices, and the business cost-benefit threshold sweep.
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score
import yaml


def load_config() -> dict:
    with open("configs/params.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def evaluate_models():
    config = load_config()
    processed_dir = Path(config["data"]["processed_dir"])
    test_path = processed_dir / "test.csv"

    if not test_path.exists():
        raise FileNotFoundError(f"Processed test data not found at {test_path}")

    test_df = pd.read_csv(test_path)
    X_test = test_df["cleaned_text"].fillna("")
    y_test = test_df["category"]

    routing_model_path = Path("models/routing_model.joblib")
    if not routing_model_path.exists():
        raise FileNotFoundError(f"Routing model not found at {routing_model_path}")

    model = joblib.load(routing_model_path)

    # 1. Prediction & Probabilities
    probs = model.predict_proba(X_test)
    preds = model.predict(X_test)
    max_probs = probs.max(axis=1)

    macro_f1 = f1_score(y_test, preds, average="macro")
    weighted_f1 = f1_score(y_test, preds, average="weighted")
    clf_report = classification_report(y_test, preds, output_dict=True)

    print(f"Test Set Evaluation Results:")
    print(f" - Macro-F1: {macro_f1:.4f}")
    print(f" - Weighted-F1: {weighted_f1:.4f}")

    # 2. Threshold Sweep & Business Impact Modeling
    biz = config.get("business_impact", {})
    N = biz.get("tickets_per_month", 5000)
    t = biz.get("triage_minutes_saved", 3.0)
    c = biz.get("misroute_penalty_minutes", 15.0)
    r = biz.get("agent_hourly_rate_usd", 10.0)

    sweep_results = []
    thresholds = np.linspace(0.50, 0.95, 10)
    best_threshold = 0.75
    max_net_hours = -float("inf")

    total_tickets = len(test_df)

    for tau in thresholds:
        tau = round(float(tau), 2)
        routed_mask = (max_probs >= tau)
        auto_routed_count = int(routed_mask.sum())
        auto_route_rate = auto_routed_count / total_tickets if total_tickets > 0 else 0.0

        if auto_routed_count > 0:
            routed_preds = preds[routed_mask]
            routed_actuals = y_test.values[routed_mask]
            accuracy_on_routed = float((routed_preds == routed_actuals).mean())
        else:
            accuracy_on_routed = 0.0

        # Business Impact Formula from PRD Section 12:
        # Net minutes saved per month = N * a * [ t - (1 - p) * c ]
        net_minutes = N * auto_route_rate * (t - (1.0 - accuracy_on_routed) * c)
        net_hours = net_minutes / 60.0
        net_savings_usd = net_hours * r

        sweep_record = {
            "threshold": tau,
            "auto_route_rate": round(auto_route_rate, 4),
            "routed_accuracy": round(accuracy_on_routed, 4),
            "net_minutes_saved": round(net_minutes, 1),
            "net_hours_saved": round(net_hours, 1),
            "net_savings_usd": round(net_savings_usd, 2),
        }
        sweep_results.append(sweep_record)

        # Select best threshold guaranteeing accuracy >= 90%
        if accuracy_on_routed >= 0.90 and net_hours > max_net_hours:
            max_net_hours = net_hours
            best_threshold = tau

    # Fallback to highest net hours if no threshold reached 90%
    if max_net_hours == -float("inf") and sweep_results:
        best_threshold = max(sweep_results, key=lambda x: x["net_hours_saved"])["threshold"]

    print(f"Optimal Threshold Selected: {best_threshold} (Max Net Hours Saved: {max_net_hours:.1f} hrs/mo)")

    # 3. Save Reports
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    eval_summary = {
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "total_test_samples": total_tickets,
        "optimal_threshold": best_threshold,
        "per_class": {
            cls_name: {
                "precision": round(metrics.get("precision", 0), 4),
                "recall": round(metrics.get("recall", 0), 4),
                "f1_score": round(metrics.get("f1-score", 0), 4),
                "support": metrics.get("support", 0),
            }
            for cls_name, metrics in clf_report.items()
            if isinstance(metrics, dict)
        },
        "threshold_sweep": sweep_results,
    }

    with open(reports_dir / "eval_metrics.json", "w", encoding="utf-8") as f:
        json.dump(eval_summary, f, indent=2)

    print(f"Evaluation metrics and threshold sweep written to {reports_dir / 'eval_metrics.json'}.")


if __name__ == "__main__":
    evaluate_models()
