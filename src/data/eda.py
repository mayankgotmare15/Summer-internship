"""Exploratory Data Analysis (EDA) module: computes class distributions, lengths, and vocabulary statistics."""

import json
from pathlib import Path

import numpy as np
import pandas as pd


def analyze_routing(df: pd.DataFrame) -> dict:
    text_lens = df["text"].str.len()
    word_counts = df["text"].str.split().str.len()

    cat_counts = df["category"].value_counts()
    cat_pcts = (cat_counts / len(df) * 100).round(2)

    return {
        "total_records": len(df),
        "total_categories": int(df["category"].nunique()),
        "class_distribution": {
            cat: {"count": int(count), "percentage": float(cat_pcts[cat])}
            for cat, count in cat_counts.items()
        },
        "character_length": {
            "mean": round(float(text_lens.mean()), 1),
            "median": round(float(text_lens.median()), 1),
            "p95": round(float(np.percentile(text_lens, 95)), 1),
            "min": int(text_lens.min()),
            "max": int(text_lens.max()),
        },
        "word_count": {
            "mean": round(float(word_counts.mean()), 1),
            "median": round(float(word_counts.median()), 1),
            "p95": round(float(np.percentile(word_counts, 95)), 1),
            "min": int(word_counts.min()),
            "max": int(word_counts.max()),
        },
    }


def analyze_priority(df: pd.DataFrame) -> dict:
    priority_counts = df["priority"].value_counts()
    priority_pcts = (priority_counts / len(df) * 100).round(2)

    return {
        "total_records": len(df),
        "priority_distribution": {
            p: {"count": int(count), "percentage": float(priority_pcts[p])}
            for p, count in priority_counts.items()
        },
    }


def main() -> None:
    interim_dir = Path("data/interim")
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    routing_df = pd.read_parquet(interim_dir / "routing.parquet")
    priority_df = pd.read_parquet(interim_dir / "priority.parquet")

    eda_summary = {
        "routing_dataset": analyze_routing(routing_df),
        "priority_dataset": analyze_priority(priority_df),
    }

    report_path = reports_dir / "eda_summary.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(eda_summary, f, indent=2)

    print(f"EDA Summary generated and saved to {report_path}:")
    print(f" - Routing total samples: {eda_summary['routing_dataset']['total_records']:,}")
    print(f" - Routing categories:    {eda_summary['routing_dataset']['total_categories']}")
    print(f" - Priority total samples:{eda_summary['priority_dataset']['total_records']:,}")


if __name__ == "__main__":
    main()
