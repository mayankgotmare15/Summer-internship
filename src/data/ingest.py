"""Data ingestion stage: loads raw datasets and standardizes schemas into interim parquet."""

import os
from pathlib import Path
import pandas as pd


def ingest_routing_data(raw_dir: Path, interim_dir: Path) -> Path:
    """Ingests the IT ticket classification dataset."""
    possible_files = [
        raw_dir / "all_tickets_processed_improved_v3.csv",
        raw_dir / "routing.csv",
    ]
    source_file = next((f for f in possible_files if f.exists()), None)
    if not source_file:
        raise FileNotFoundError(f"Routing raw data not found in {raw_dir}")

    print(f"Reading routing dataset from {source_file}...")
    df = pd.read_csv(source_file)

    # Standardize column names
    col_map = {
        "Document": "text",
        "Topic_group": "category",
        "body": "text",
        "category": "category",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # Retain required columns
    df = df[["text", "category"]].dropna()
    df["text"] = df["text"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()

    output_path = interim_dir / "routing.parquet"
    df.to_parquet(output_path, index=False)
    print(f"Saved {len(df):,} routing records to {output_path}")
    return output_path


def ingest_priority_data(raw_dir: Path, interim_dir: Path) -> Path:
    """Ingests and filters the customer support priority dataset (English only)."""
    possible_files = [
        raw_dir / "priority_raw" / "aa_dataset-tickets-multi-lang-5-2-50-version.csv",
        raw_dir / "priority.csv",
    ]
    source_file = next((f for f in possible_files if f.exists()), None)
    if not source_file:
        raise FileNotFoundError(f"Priority raw data not found in {raw_dir}")

    print(f"Reading priority dataset from {source_file}...")
    df = pd.read_csv(source_file, low_memory=False)

    # Filter to English language tickets
    if "language" in df.columns:
        df = df[df["language"] == "en"]

    # Combine subject and body if both present
    if "subject" in df.columns and "body" in df.columns:
        df["text"] = df["subject"].fillna("") + " " + df["body"].fillna("")
    elif "body" in df.columns:
        df["text"] = df["body"]
    elif "text" not in df.columns:
        raise KeyError("Priority dataset missing text/body columns")

    df = df[["text", "priority"]].dropna()
    df["text"] = df["text"].astype(str).str.strip()

    # Capitalize priority labels to match system enum: Low, Medium, High, Critical
    priority_map = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "critical": "Critical",
    }
    df["priority"] = df["priority"].str.lower().map(priority_map).fillna("Medium")

    output_path = interim_dir / "priority.parquet"
    df.to_parquet(output_path, index=False)
    print(f"Saved {len(df):,} English priority records to {output_path}")
    return output_path


def main() -> None:
    raw_dir = Path("data/raw")
    interim_dir = Path("data/interim")
    interim_dir.mkdir(parents=True, exist_ok=True)

    ingest_routing_data(raw_dir, interim_dir)
    ingest_priority_data(raw_dir, interim_dir)
    print("Ingestion stage complete.")


if __name__ == "__main__":
    main()
