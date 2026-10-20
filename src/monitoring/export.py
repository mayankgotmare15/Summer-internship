"""Monitoring Data Exporter.

Extracts reference features and production inferences from the database
and feedback logs for drift detection and quality evaluation.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from src.db.models.feedback import Feedback
from src.db.models.prediction import Prediction
from src.db.session import SessionLocal


def load_reference_dataset(reference_path: str | Path = "data/processed/val.parquet") -> pd.DataFrame:
    """Loads reference dataset (validation or baseline split) used for drift benchmarking."""
    path = Path(reference_path)
    if not path.exists():
        # Fallback to train if val does not exist
        path = Path("data/processed/train.parquet")
    if not path.exists():
        raise FileNotFoundError(f"Reference dataset not found at {reference_path}")

    df = pd.read_parquet(path)
    # Ensure standard columns: text, category, text_length
    if "text" in df.columns and "text_length" not in df.columns:
        df["text_length"] = df["text"].astype(str).str.len()
    return df


def export_production_inferences(
    db: Session,
    limit: int = 2000,
) -> pd.DataFrame:
    """Queries recent production predictions and associated agent feedback from the database."""
    # Query latest predictions
    preds = db.query(Prediction).order_by(Prediction.created_at.desc()).limit(limit).all()

    if not preds:
        return pd.DataFrame(
            columns=[
                "id",
                "text",
                "text_length",
                "category",
                "category_confidence",
                "decision",
                "review_reason",
                "corrected_category",
                "is_override",
            ]
        )

    pred_ids = [p.id for p in preds]
    feedbacks = db.query(Feedback).filter(Feedback.prediction_id.in_(pred_ids)).all()
    feedback_map: dict[Any, Feedback] = {f.prediction_id: f for f in feedbacks if f.prediction_id}

    records = []
    for p in preds:
        fb = feedback_map.get(p.id)
        corrected_cat = fb.corrected_category if fb else None
        is_override = bool(corrected_cat and corrected_cat != p.category)

        records.append(
            {
                "id": str(p.id),
                "text": p.text_preview,
                "text_length": len(p.text_preview),
                "category": p.category,
                "category_confidence": float(p.category_confidence),
                "decision": p.decision,
                "review_reason": p.review_reason,
                "corrected_category": corrected_cat,
                "is_override": is_override,
                "created_at": p.created_at,
            }
        )

    return pd.DataFrame(records)


def export_monitoring_datasets(
    output_dir: str | Path = "reports/monitoring_data",
    reference_path: str | Path = "data/processed/val.parquet",
    limit: int = 2000,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Exports both reference and current production datasets to Parquet files."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df_ref = load_reference_dataset(reference_path)
    with SessionLocal() as db:
        df_curr = export_production_inferences(db, limit=limit)

    ref_file = out_dir / "reference.parquet"
    curr_file = out_dir / "current.parquet"

    df_ref.to_parquet(ref_file, index=False)
    df_curr.to_parquet(curr_file, index=False)

    print(f"Exported {len(df_ref):,} reference rows to {ref_file}")
    print(f"Exported {len(df_curr):,} current production rows to {curr_file}")
    return df_ref, df_curr


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export monitoring reference and production datasets.")
    parser.add_argument("--output-dir", default="reports/monitoring_data", help="Output directory")
    parser.add_argument("--reference-path", default="data/processed/val.parquet", help="Reference parquet path")
    parser.add_argument("--limit", type=int, default=2000, help="Max production inferences to export")
    args = parser.parse_args()

    export_monitoring_datasets(output_dir=args.output_dir, reference_path=args.reference_path, limit=args.limit)
