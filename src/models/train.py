"""
Model Training Module.
Trains TF-IDF vectorizer + Calibrated Classifier on validated processed dataset.
Logs parameters, metrics, and model artifacts to MLflow.
"""

import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.pipeline import Pipeline
import yaml

try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

from src.features.preprocess import clean_text


def load_config() -> dict:
    with open("configs/params.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def train_models():
    config = load_config()
    train_params = config.get("train", {})
    prep_params = config.get("preprocess", {})
    data_params = config.get("data", {})

    processed_dir = Path(data_params.get("processed_dir", "data/processed"))
    train_path = processed_dir / "train.csv"
    val_path = processed_dir / "val.csv"

    # Fallback to raw ingestion if processed data does not exist yet
    if not train_path.exists():
        from src.data.ingest import ingest_data
        ingest_data()
        from src.data.split import split_and_preprocess_data
        split_and_preprocess_data()

    print(f"Loading training data from {train_path}...")
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)

    X_train = train_df["cleaned_text"].fillna("")
    y_train_routing = train_df["category"]

    X_val = val_df["cleaned_text"].fillna("")
    y_val_routing = val_df["category"]

    # 1. Routing Model Pipeline
    ngram_range = tuple(prep_params.get("ngram_range", [1, 2]))
    max_features = prep_params.get("max_features", 10000)
    C_param = train_params.get("C", 1.0)
    class_weight = train_params.get("class_weight", "balanced")
    seed = train_params.get("random_seed", 42)

    routing_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=ngram_range,
            max_features=max_features,
            sublinear_tf=True
        )),
        ("clf", LogisticRegression(
            C=C_param,
            class_weight=class_weight,
            max_iter=1000,
            random_state=seed
        ))
    ])

    print("Fitting Routing Model Pipeline...")
    routing_pipeline.fit(X_train, y_train_routing)

    val_preds = routing_pipeline.predict(X_val)
    val_macro_f1 = f1_score(y_val_routing, val_preds, average="macro")
    val_weighted_f1 = f1_score(y_val_routing, val_preds, average="weighted")

    print(f"Validation Macro-F1: {val_macro_f1:.4f} | Weighted-F1: {val_weighted_f1:.4f}")

    # 2. Priority Model Pipeline (if priority is present)
    priority_pipeline = None
    if "priority" in train_df.columns:
        y_train_priority = train_df["priority"]
        y_val_priority = val_df["priority"]

        priority_pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True
            )),
            ("clf", LogisticRegression(
                C=1.0,
                class_weight="balanced",
                max_iter=1000,
                random_state=seed
            ))
        ])
        print("Fitting Priority Model Pipeline...")
        priority_pipeline.fit(X_train, y_train_priority)
        prio_val_preds = priority_pipeline.predict(X_val)
        prio_f1 = f1_score(y_val_priority, prio_val_preds, average="weighted")
        print(f"Priority Validation Weighted-F1: {prio_f1:.4f}")

    # 3. Save Artifacts locally
    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(routing_pipeline, models_dir / "routing_model.joblib")
    print(f"Saved routing model to {models_dir / 'routing_model.joblib'}")

    if priority_pipeline is not None:
        joblib.dump(priority_pipeline, models_dir / "priority_model.joblib")
        print(f"Saved priority model to {models_dir / 'priority_model.joblib'}")

    # 4. MLflow Logging
    if MLFLOW_AVAILABLE:
        try:
            with mlflow.start_run(run_name="train_champion_baseline"):
                mlflow.log_params({
                    "model_type": train_params.get("model_type", "logistic_regression"),
                    "C": C_param,
                    "class_weight": str(class_weight),
                    "ngram_range": str(ngram_range),
                    "max_features": max_features,
                    "seed": seed,
                })
                mlflow.log_metrics({
                    "val_macro_f1": val_macro_f1,
                    "val_weighted_f1": val_weighted_f1,
                })
                mlflow.sklearn.log_model(routing_pipeline, "routing_model")
                print("MLflow logging completed.")
        except Exception as e:
            print(f"Notice: MLflow logging skipped ({e})")

    # Save summary metrics
    Path("reports").mkdir(exist_ok=True)
    with open("reports/val_metrics.json", "w", encoding="utf-8") as f:
        json.dump({
            "val_macro_f1": round(val_macro_f1, 4),
            "val_weighted_f1": round(val_weighted_f1, 4),
            "train_samples": len(train_df),
            "val_samples": len(val_df),
        }, f, indent=2)


if __name__ == "__main__":
    train_models()
