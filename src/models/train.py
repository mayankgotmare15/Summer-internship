"""Model training stage: trains TF-IDF + LogisticRegression / LinearSVC models and logs to MLflow."""

import argparse
import os
from pathlib import Path

import joblib
import pandas as pd
import skops.io as sio
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

try:
    import mlflow

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


def load_params() -> dict:
    with open("configs/params.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def train_routing_model(params: dict, features_dir: Path, artifacts_dir: Path) -> Pipeline:
    """Trains the ticket category routing classifier."""
    routing_cfg = params.get("routing", {})
    tfidf_cfg = routing_cfg.get("tfidf", {})
    logreg_cfg = routing_cfg.get("logreg", {})
    seed = params.get("seed", 42)

    train_path = features_dir / "train.parquet"
    print(f"Loading training data from {train_path}...")
    df_train = pd.read_parquet(train_path)

    # Text clean is already lemmatized, but fallback to raw text if needed
    text_col = "text_clean" if "text_clean" in df_train.columns else "text"
    X_train = df_train[text_col].fillna("").tolist()
    y_train = df_train["category"].tolist()

    print(f"Fitting routing pipeline on {len(X_train):,} samples...")
    pipeline = Pipeline(
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
                    max_iter=logreg_cfg.get("max_iter", 2000),
                    random_state=seed,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    pipeline.fit(X_train, y_train)

    # Save model artifact
    out_dir = artifacts_dir / "routing"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file_skops = out_dir / "model.skops"
    out_file_joblib = out_dir / "model.joblib"

    try:
        sio.dump(pipeline, out_file_skops)
        print(f"Saved routing model in skops format to {out_file_skops}")
    except Exception as e:
        print(f"skops serialization note: {e}, falling back to joblib...")
        joblib.dump(pipeline, out_file_joblib)
        print(f"Saved routing model in joblib format to {out_file_joblib}")

    return pipeline


def train_priority_model(params: dict, interim_dir: Path, artifacts_dir: Path) -> Pipeline:
    """Trains the ticket priority classifier (Low, Medium, High)."""
    priority_cfg = params.get("priority", {})
    tfidf_cfg = priority_cfg.get("tfidf", {})
    logreg_cfg = priority_cfg.get("logreg", {})
    seed = params.get("seed", 42)

    priority_path = interim_dir / "priority.parquet"
    print(f"Loading priority data from {priority_path}...")
    df_priority = pd.read_parquet(priority_path)

    X = df_priority["text"].fillna("").tolist()
    y = df_priority["priority"].tolist()

    print(f"Fitting priority pipeline on {len(X):,} samples...")
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=tuple(tfidf_cfg.get("ngram_range", [1, 2])),
                    min_df=tfidf_cfg.get("min_df", 3),
                    max_features=tfidf_cfg.get("max_features", 25000),
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=logreg_cfg.get("C", 1.0),
                    class_weight=logreg_cfg.get("class_weight", "balanced"),
                    max_iter=logreg_cfg.get("max_iter", 2000),
                    random_state=seed,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    pipeline.fit(X, y)

    out_dir = artifacts_dir / "priority"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file_skops = out_dir / "model.skops"
    out_file_joblib = out_dir / "model.joblib"

    try:
        sio.dump(pipeline, out_file_skops)
        print(f"Saved priority model in skops format to {out_file_skops}")
    except Exception as e:
        print(f"skops note: {e}, falling back to joblib...")
        joblib.dump(pipeline, out_file_joblib)
        print(f"Saved priority model in joblib format to {out_file_joblib}")

    return pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Train routing or priority model.")
    parser.add_argument("--task", type=str, choices=["routing", "priority", "both"], default="both")
    args = parser.parse_args()

    params = load_params()
    features_dir = Path("data/features")
    interim_dir = Path("data/interim")
    artifacts_dir = Path("artifacts")

    # Configure MLflow if enabled
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///./local_db/mlflow.db")
    if MLFLOW_AVAILABLE:
        try:
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment("it-ticket-routing")
            print(f"Connected to MLflow tracking: {tracking_uri}")
        except Exception as e:
            print(f"MLflow setup note: {e}")

    if args.task in ["routing", "both"]:
        train_routing_model(params, features_dir, artifacts_dir)

    if args.task in ["priority", "both"]:
        train_priority_model(params, interim_dir, artifacts_dir)

    print("Training phase complete.")


if __name__ == "__main__":
    main()
