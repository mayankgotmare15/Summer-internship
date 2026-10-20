"""Data validation stage using Pandera: validates schemas, label sets, and data bounds."""

import json
from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

EXPECTED_CATEGORIES = {
    "Access",
    "Administrative rights",
    "HR Support",
    "Hardware",
    "Internal Project",
    "Miscellaneous",
    "Purchase",
    "Storage",
}

EXPECTED_PRIORITIES = {"Low", "Medium", "High", "Critical"}

routing_schema = DataFrameSchema(
    {
        "text": Column(
            str,
            [Check(lambda s: s.str.len() >= 5, error="Text too short (<5 chars)")],
            nullable=False,
        ),
        "category": Column(
            str, [Check.isin(EXPECTED_CATEGORIES, error="Unknown category label")], nullable=False
        ),
    }
)

priority_schema = DataFrameSchema(
    {
        "text": Column(
            str,
            [Check(lambda s: s.str.len() >= 5, error="Text too short (<5 chars)")],
            nullable=False,
        ),
        "priority": Column(
            str, [Check.isin(EXPECTED_PRIORITIES, error="Unknown priority label")], nullable=False
        ),
    }
)


def validate_dataset(df: pd.DataFrame, schema: DataFrameSchema, name: str) -> dict:
    """Validates dataframe against Pandera schema and computes health statistics."""
    initial_count = len(df)
    empty_text_count = (df["text"].str.len() < 5).sum()
    duplicate_count = df["text"].duplicated().sum()

    # Filter out text that is too short
    df_clean = df[df["text"].str.len() >= 5].copy()

    # Validate against Pandera schema
    try:
        schema.validate(df_clean, lazy=True)
        schema_valid = True
        schema_errors = []
    except pa.errors.SchemaErrors as err:
        schema_valid = False
        schema_errors = [str(e) for e in err.failure_cases["check"].tolist()[:5]]

    return {
        "dataset": name,
        "total_records": initial_count,
        "clean_records": len(df_clean),
        "empty_or_short_text": int(empty_text_count),
        "duplicates": int(duplicate_count),
        "duplicate_rate": round(duplicate_count / max(initial_count, 1), 4),
        "schema_valid": schema_valid,
        "schema_errors": schema_errors,
        "classes": df_clean.iloc[:, 1].value_counts().to_dict(),
    }


def main() -> None:
    interim_dir = Path("data/interim")
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    routing_file = interim_dir / "routing.parquet"
    priority_file = interim_dir / "priority.parquet"

    if not routing_file.exists() or not priority_file.exists():
        raise FileNotFoundError("Interim parquet files not found. Run ingest.py first.")

    df_routing = pd.read_parquet(routing_file)
    df_priority = pd.read_parquet(priority_file)

    routing_report = validate_dataset(df_routing, routing_schema, "routing")
    priority_report = validate_dataset(df_priority, priority_schema, "priority")

    report = {
        "routing": routing_report,
        "priority": priority_report,
        "overall_valid": routing_report["schema_valid"] and priority_report["schema_valid"],
    }

    report_path = reports_dir / "validation.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Validation report saved to {report_path}:")
    print(
        f" - Routing: {routing_report['clean_records']:,} clean rows (valid={routing_report['schema_valid']})"
    )
    print(
        f" - Priority: {priority_report['clean_records']:,} clean rows (valid={priority_report['schema_valid']})"
    )


if __name__ == "__main__":
    main()
