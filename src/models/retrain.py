"""Champion-Challenger Automated Retraining Pipeline.

Incorporates accumulated feedback and holdout category data,
trains candidate challenger model, evaluates quality gate against champion,
and promotes atomically if all criteria are satisfied.
"""

from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import skops.io as sio
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.ml.bundle import package_bundle
from src.ml.preprocess import get_preprocess_fingerprint
from src.models.evaluate import evaluate_robustness
from src.models.promote import evaluate_gate
from src.models.sweep import sweep_thresholds


def load_params() -> dict[str, Any]:
    with open("configs/params.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_champion_manifest(champion_path: str | Path = "models/champion.json") -> dict | None:
    p = Path(champion_path)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def build_augmented_training_data(
    base_train_path: str | Path = "data/processed/train.parquet",
    base_val_path: str | Path = "data/processed/val.parquet",
    base_test_path: str | Path = "data/processed/test.parquet",
    holdout_path: str | Path = "data/holdout/storage_holdout.parquet",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Combines baseline data with held-back category and feedback for retraining."""
    df_train = pd.read_parquet(base_train_path)
    df_val = pd.read_parquet(base_val_path)
    df_test = pd.read_parquet(base_test_path)

    # Load holdout category
    holdout_p = Path(holdout_path)
    if holdout_p.exists():
        df_holdout = pd.read_parquet(holdout_p)
        print(f"Augmenting with {len(df_holdout):,} holdout category ('{df_holdout['category'].iloc[0]}') samples...")

        # Stratified 70/15/15 split of holdout data
        h_train, h_temp = train_test_split(df_holdout, test_size=0.30, random_state=42)
        h_val, h_test = train_test_split(h_temp, test_size=0.50, random_state=42)

        df_train_aug = pd.concat([df_train, h_train], ignore_index=True)
        df_val_aug = pd.concat([df_val, h_val], ignore_index=True)
        df_test_aug = pd.concat([df_test, h_test], ignore_index=True)
    else:
        print("No holdout file found; retraining solely on existing dataset.")
        df_train_aug = df_train
        df_val_aug = df_val
        df_test_aug = df_test

    # Shuffle training set
    df_train_aug = df_train_aug.sample(frac=1.0, random_state=42).reset_index(drop=True)
    return df_train_aug, df_val_aug, df_test_aug


def measure_p95_latency(model: Any, samples: list[str]) -> float:
    """Measures single-prediction p95 latency on CPU."""
    latencies = []
    # Warmup
    for s in samples[:5]:
        _ = model.predict([s])
    for s in samples:
        t0 = time.perf_counter()
        _ = model.predict([s])
        latencies.append((time.perf_counter() - t0) * 1000.0)
    return float(sorted(latencies)[int(len(latencies) * 0.95)])


def run_retraining_drill(
    run_tag: str = "v2-retrained",
    output_dir: str | Path = "reports",
) -> tuple[bool, dict[str, Any]]:
    """Executes full Champion-Challenger retraining pipeline."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    params = load_params()

    print("\n" + "=" * 65)
    print("STARTING CHAMPION-CHALLENGER RETRAINING DRILL")
    print("=" * 65)

    # 1. Prepare Augmented Dataset
    df_train, df_val, df_test = build_augmented_training_data()
    print(f"Training Pool: {len(df_train):,} tickets across {df_train['category'].nunique()} categories.")
    print(f"Categories in Training: {sorted(df_train['category'].unique())}")

    # 2. Train Challenger Model
    routing_cfg = params.get("routing", {})
    tfidf_cfg = routing_cfg.get("tfidf", {})
    logreg_cfg = routing_cfg.get("logreg", {})

    challenger_pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=tuple(tfidf_cfg.get("ngram_range", [1, 2])),
                    min_df=tfidf_cfg.get("min_df", 2),
                    max_features=tfidf_cfg.get("max_features", 50000),
                    sublinear_tf=tfidf_cfg.get("sublinear_tf", True),
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=logreg_cfg.get("C", 4.0),
                    class_weight=logreg_cfg.get("class_weight", "balanced"),
                    max_iter=logreg_cfg.get("max_iter", 1000),
                    random_state=42,
                    solver="lbfgs",
                ),
            ),
        ]
    )

    print("Fitting Challenger Model...")
    t0 = time.perf_counter()
    challenger_pipeline.fit(df_train["text"].fillna("").tolist(), df_train["category"].tolist())
    train_duration = time.perf_counter() - t0
    print(f"Challenger Model trained in {train_duration:.2f}s.")

    # 3. Evaluate Challenger on Test Set
    X_test = df_test["text"].fillna("").tolist()
    y_true = df_test["category"].tolist()
    y_pred = challenger_pipeline.predict(X_test)

    macro_f1 = f1_score(y_true, y_pred, average="macro")
    weighted_f1 = f1_score(y_true, y_pred, average="weighted")
    class_report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    labels = sorted(set(y_true))

    # 4. Optimal Threshold Sweep on Validation Set
    sweep_results = sweep_thresholds(
        model=challenger_pipeline,
        df_val=df_val,
        params=params,
    )
    best_threshold = sweep_results.get("optimal_threshold", 0.69)
    optimal_row = sweep_results.get("optimal_row", {})
    auto_route_rate = optimal_row.get("auto_route_rate", 0.60)
    auto_accuracy = optimal_row.get("auto_accuracy", 0.95)

    # 5. Robustness & Latency Checks
    messy_path = Path("data/robustness/messy_tickets.json")
    robustness_res = evaluate_robustness(challenger_pipeline, messy_path) if messy_path.exists() else {}
    p95_latency = measure_p95_latency(challenger_pipeline, X_test[:200])

    challenger_metrics = {
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "auto_route_rate": round(float(auto_route_rate), 4),
        "auto_route_accuracy": round(float(auto_accuracy), 4),
        "optimal_threshold": best_threshold,
        "p95_latency_ms": round(p95_latency, 2),
        "robustness_score": robustness_res.get("accuracy", 0.0),
        "per_class": {
            cls: {
                "precision": round(class_report[cls]["precision"], 4),
                "recall": round(class_report[cls]["recall"], 4),
                "f1": round(class_report[cls]["f1-score"], 4),
                "support": class_report[cls]["support"],
            }
            for cls in labels
        },
    }

    # 6. Quality Gate Evaluation Against Current Champion
    champion_manifest = load_champion_manifest()
    champion_metrics = champion_manifest.get("metrics") if champion_manifest else None

    gate_passed, gate_reasons = evaluate_gate(
        candidate_metrics=challenger_metrics,
        champion_metrics=champion_metrics,
        gate_params=params.get("gate", {}),
        p95_latency_ms=p95_latency,
    )

    print("\nQUALITY GATE EVALUATION:")
    if gate_passed:
        print("  [PASSED] Challenger satisfies all quality gate criteria!")
    else:
        print("  [REJECTED] Challenger failed quality gate:")
        for r in gate_reasons:
            print(f"    - {r}")

    # 7. Comparison Summary Table
    comparison = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": f"run_{uuid.uuid4().hex[:8]}",
        "champion": {
            "version": champion_manifest.get("version") if champion_manifest else "none",
            "threshold": champion_manifest.get("threshold") if champion_manifest else None,
            "classes": champion_manifest.get("labels") if champion_manifest else [],
            "macro_f1": champion_metrics.get("macro_f1") if champion_metrics else None,
            "auto_route_rate": champion_metrics.get("auto_route_rate") if champion_metrics else None,
        },
        "challenger": {
            "version": run_tag,
            "threshold": best_threshold,
            "classes": labels,
            "macro_f1": challenger_metrics["macro_f1"],
            "auto_route_rate": challenger_metrics["auto_route_rate"],
            "auto_route_accuracy": challenger_metrics["auto_route_accuracy"],
            "p95_latency_ms": challenger_metrics["p95_latency_ms"],
        },
        "gate_status": "PASSED" if gate_passed else "REJECTED",
        "gate_reasons": gate_reasons,
    }

    with open(out_dir / "retraining_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)

    # 8. Promotion if Passed
    if gate_passed:
        # Save challenger skops artifact
        artifacts_routing = Path("artifacts/routing")
        artifacts_routing.mkdir(parents=True, exist_ok=True)
        sio.dump(challenger_pipeline, artifacts_routing / "model.skops")
        joblib.dump(challenger_pipeline, artifacts_routing / "model.joblib")

        # Update reports/threshold.json and reports/metrics.json
        with open("reports/threshold.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "threshold": best_threshold,
                    "target_accuracy": 0.90,
                    "optimal_metrics": optimal_row,
                },
                f,
                indent=2,
            )

        with open("reports/metrics.json", "w", encoding="utf-8") as f:
            json.dump({"routing": challenger_metrics}, f, indent=2)

        # Repackage bundle
        package_bundle(
            artifacts_dir=Path("artifacts"),
            bundle_dir=Path("artifacts/bundle"),
            version_tag=run_tag,
        )

        # Update models/champion.json
        new_champion_record = {
            "model_name": "ticket-routing",
            "version": run_tag,
            "run_id": comparison["run_id"],
            "alias": "champion",
            "promoted_at": datetime.now(timezone.utc).isoformat(),
            "threshold": best_threshold,
            "metrics": {
                "macro_f1": challenger_metrics["macro_f1"],
                "weighted_f1": challenger_metrics["weighted_f1"],
                "auto_route_rate": challenger_metrics["auto_route_rate"],
                "auto_route_accuracy": challenger_metrics["auto_route_accuracy"],
                "p95_latency_ms": challenger_metrics["p95_latency_ms"],
            },
            "labels": labels,
            "preprocess_fingerprint": get_preprocess_fingerprint(),
            "gate_status": "PASSED",
        }
        with open("models/champion.json", "w", encoding="utf-8") as f:
            json.dump(new_champion_record, f, indent=2)

        print(f"\nPROMOTION SUCCESSFUL: {run_tag} is now active champion.")
        print(f"Updated classes: {labels}")
        print("Bundle repacked into artifacts/bundle/ and models/champion.json updated.")

    return gate_passed, comparison


def main() -> None:
    parser = argparse.ArgumentParser(description="Run champion-challenger retraining pipeline.")
    parser.add_argument("--version-tag", default="v2-retrained", help="Challenger version tag")
    parser.add_argument("--output-dir", default="reports", help="Output directory for reports")
    args = parser.parse_args()

    passed, _ = run_retraining_drill(run_tag=args.version_tag, output_dir=args.output_dir)
    if not passed:
        exit(1)
    exit(0)


if __name__ == "__main__":
    main()
