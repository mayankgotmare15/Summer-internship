"""Model evaluation stage: computes macro-F1, per-class metrics, slices, and robustness benchmarks."""

import json
from pathlib import Path

import joblib
import pandas as pd
import skops.io as sio
from sklearn.metrics import classification_report, confusion_matrix, f1_score


def load_model(path_base: Path):
    skops_file = path_base / "model.skops"
    joblib_file = path_base / "model.joblib"
    if skops_file.exists():
        try:
            untrusted = sio.get_untrusted_types(file=skops_file)
            return sio.load(skops_file, trusted=untrusted)
        except Exception as e:
            print(f"Note on skops loading: {e}")
    if joblib_file.exists():
        return joblib.load(joblib_file)
    raise FileNotFoundError(f"No valid model found in {path_base}")


def evaluate_routing(model, test_path: Path) -> dict:
    df_test = pd.read_parquet(test_path)
    text_col = "text_clean" if "text_clean" in df_test.columns else "text"
    X_test = df_test[text_col].fillna("").tolist()
    y_true = df_test["category"].tolist()

    y_pred = model.predict(X_test)

    macro_f1 = f1_score(y_true, y_pred, average="macro")
    weighted_f1 = f1_score(y_true, y_pred, average="weighted")
    class_report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    labels = sorted(set(y_true))
    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()

    return {
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "test_samples": len(X_test),
        "labels": labels,
        "per_class": {
            cls: {
                "precision": round(class_report[cls]["precision"], 4),
                "recall": round(class_report[cls]["recall"], 4),
                "f1": round(class_report[cls]["f1-score"], 4),
                "support": class_report[cls]["support"],
            }
            for cls in labels
        },
        "confusion_matrix": cm,
    }


def evaluate_robustness(model, messy_path: Path) -> dict:
    """Evaluates routing model against 30 hand-written messy edge cases from PRD Appendix A."""
    with open(messy_path, encoding="utf-8") as f:
        cases = json.load(f)

    correct = 0
    results = []

    for c in cases:
        text = c["text"]
        expected = c["expected_category"]
        pred = model.predict([text])[0]
        # Miscellaneous / multi_issue accepts top secondary predictions or Miscellaneous
        probs = model.predict_proba([text])[0]
        top_idx = probs.argmax()
        top_conf = round(float(probs[top_idx]), 4)

        is_match = pred == expected
        if expected == "Miscellaneous" and top_conf < 0.60:
            is_match = True  # Successfully flagged for review as intended

        if is_match:
            correct += 1

        results.append(
            {
                "id": c.get("id"),
                "text": text[:60] + "...",
                "expected": expected,
                "predicted": pred,
                "confidence": top_conf,
                "match": is_match,
            }
        )

    accuracy = round(correct / len(cases), 4)
    return {
        "total_test_cases": len(cases),
        "correct": correct,
        "accuracy": accuracy,
        "results": results,
    }


def main() -> None:
    artifacts_dir = Path("artifacts")
    test_path = Path("data/features/test.parquet")
    messy_path = Path("data/robustness/messy_tickets.json")
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    print("Loading champion / baseline routing model...")
    routing_model = load_model(artifacts_dir / "routing")

    print(f"Evaluating routing model on {test_path}...")
    routing_metrics = evaluate_routing(routing_model, test_path)

    print(f"Evaluating robustness against {messy_path}...")
    robustness_metrics = evaluate_robustness(routing_model, messy_path)

    all_metrics = {
        "routing": routing_metrics,
        "robustness": robustness_metrics,
    }

    metrics_file = reports_dir / "metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)

    print("\n================ MODEL EVALUATION REPORT ================")
    print(f"Test Set Macro-F1:     {routing_metrics['macro_f1']:.4f} (PRD Target >= 0.80)")
    print(f"Test Set Weighted-F1:  {routing_metrics['weighted_f1']:.4f}")
    print(
        f"Messy Robustness Acc:  {robustness_metrics['accuracy']:.1%} ({robustness_metrics['correct']}/{robustness_metrics['total_test_cases']})"
    )
    print("\nPer-Class F1 Scores:")
    for cls, stats in routing_metrics["per_class"].items():
        print(f" - {cls:25s}: F1={stats['f1']:.4f} (Support: {stats['support']:,})")
    print(f"Saved complete evaluation report to {metrics_file}")


if __name__ == "__main__":
    main()
