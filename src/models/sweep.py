"""Confidence threshold optimization sweep maximizing net agent hours saved (PRD Section 12)."""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import skops.io as sio
import yaml


def load_params() -> dict:
    with open("configs/params.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_model(model_path: Path):
    untrusted = sio.get_untrusted_types(file=model_path)
    return sio.load(model_path, trusted=untrusted)


def main() -> None:
    params = load_params()
    cost_cfg = params.get("cost_model", {})
    t_min = cost_cfg.get("t_minutes", 3)
    c_min = cost_cfg.get("c_minutes", 15)
    r_usd = cost_cfg.get("r_usd", 10)
    min_acc = cost_cfg.get("min_auto_accuracy", 0.90)
    monthly_tickets = 5000

    val_path = Path("data/features/val.parquet")
    model_path = Path("artifacts/routing/model.skops")
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading validation set from {val_path}...")
    df_val = pd.read_parquet(val_path)
    text_col = "text_clean" if "text_clean" in df_val.columns else "text"
    X_val = df_val[text_col].fillna("").tolist()
    y_val = df_val["category"].tolist()

    print(f"Loading routing model from {model_path}...")
    model = load_model(model_path)
    classes = list(model.classes_)

    print("Computing prediction probabilities on validation split...")
    probs = model.predict_proba(X_val)
    top_indices = probs.argmax(axis=1)
    max_probs = probs.max(axis=1)
    predicted_labels = [classes[idx] for idx in top_indices]

    thresholds = np.arange(0.50, 0.96, 0.01)
    records = []

    best_threshold = 0.65
    max_hours_saved = -float("inf")
    best_stats = {}

    for t in thresholds:
        t_val = round(float(t), 2)
        auto_mask = (max_probs >= t_val) & (np.array(predicted_labels) != "Miscellaneous")
        n_auto = int(auto_mask.sum())
        auto_rate = round(n_auto / len(y_val), 4)

        if n_auto > 0:
            auto_y_true = np.array(y_val)[auto_mask]
            auto_y_pred = np.array(predicted_labels)[auto_mask]
            acc = round(float((auto_y_true == auto_y_pred).mean()), 4)
        else:
            acc = 1.0

        # PRD Section 12 Net Minutes formula:
        # Net Minutes = N * a * [ t - (1 - p) * c ]
        net_minutes_per_ticket = auto_rate * (t_min - (1.0 - acc) * c_min)
        net_hours_saved = round(float((monthly_tickets * net_minutes_per_ticket) / 60.0), 2)
        net_cost_saved = round(float(net_hours_saved * r_usd), 2)

        records.append({
            "threshold": t_val,
            "auto_route_rate": auto_rate,
            "auto_route_accuracy": acc,
            "net_hours_saved": net_hours_saved,
            "net_cost_saved_usd": net_cost_saved,
        })

        # Selection rule: maximize net hours saved subject to accuracy >= min_auto_accuracy
        if acc >= min_acc and net_hours_saved > max_hours_saved:
            max_hours_saved = net_hours_saved
            best_threshold = t_val
            best_stats = {
                "threshold": t_val,
                "auto_route_rate": auto_rate,
                "auto_route_accuracy": acc,
                "net_hours_saved_monthly": net_hours_saved,
                "net_cost_saved_usd_monthly": net_cost_saved,
                "meets_accuracy_target": True,
            }

    # If no threshold reached 90%, fallback to highest accuracy threshold
    if not best_stats:
        best_row = max(records, key=lambda r: (r["auto_route_accuracy"], r["net_hours_saved"]))
        best_threshold = best_row["threshold"]
        best_stats = {
            "threshold": best_threshold,
            "auto_route_rate": best_row["auto_route_rate"],
            "auto_route_accuracy": best_row["auto_route_accuracy"],
            "net_hours_saved_monthly": best_row["net_hours_saved"],
            "net_cost_saved_usd_monthly": best_row["net_cost_saved_usd"],
            "meets_accuracy_target": False,
        }

    df_sweep = pd.DataFrame(records)
    csv_path = reports_dir / "sweep.csv"
    df_sweep.to_csv(csv_path, index=False)
    print(f"Saved sweep metrics to {csv_path}")

    # Generate visualization plot
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    ax1.plot(df_sweep["threshold"], df_sweep["auto_route_accuracy"] * 100, "b-", label="Auto Accuracy (%)")
    ax1.plot(df_sweep["threshold"], df_sweep["auto_route_rate"] * 100, "g--", label="Auto-Route Rate (%)")
    ax1.axhline(min_acc * 100, color="r", linestyle=":", label=f"Accuracy Target ({int(min_acc*100)}%)")
    ax1.axvline(best_threshold, color="k", linestyle="-.", label=f"Optimal Thr ({best_threshold})")

    ax2.plot(df_sweep["threshold"], df_sweep["net_hours_saved"], "m-.", label="Net Hours Saved / Month")

    ax1.set_xlabel("Confidence Threshold (tau)")
    ax1.set_ylabel("Rate / Accuracy (%)")
    ax2.set_ylabel("Net Agent Hours Saved / Month")
    ax1.set_title("Confidence Threshold vs. Accuracy & Business ROI (PRD 12)")
    ax1.grid(True, alpha=0.3)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="lower left")

    plt.tight_layout()
    png_path = reports_dir / "sweep.png"
    plt.savefig(png_path, dpi=150)
    plt.close()
    print(f"Saved threshold sweep chart to {png_path}")

    # Save best threshold JSON
    json_path = reports_dir / "threshold.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(best_stats, f, indent=2)
    print(f"Saved optimal threshold configuration to {json_path}:")
    print(f" - Optimal Threshold (tau*): {best_stats['threshold']}")
    print(f" - Auto-Route Rate:         {best_stats['auto_route_rate']:.1%}")
    print(f" - Accuracy on Auto-Routed: {best_stats['auto_route_accuracy']:.1%}")
    print(f" - Net Agent Hours Saved:   {best_stats['net_hours_saved_monthly']} hrs/month (~${best_stats['net_cost_saved_usd_monthly']}/mo)")


if __name__ == "__main__":
    main()
