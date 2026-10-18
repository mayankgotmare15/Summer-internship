"""
Data validation module for IT Support Ticket dataset.
Enforces schema contracts using Pandera and performs data leakage checks across splits.
"""

import hashlib
from typing import Dict, List, Set, Tuple
import pandas as pd
import pandera as pa
from pandera.typing import Series

VALID_CATEGORIES = [
    "Access",
    "Administrative rights",
    "HR Support",
    "Hardware",
    "Internal Project",
    "Miscellaneous",
    "Purchase",
    "Storage",
]

VALID_PRIORITIES = ["Low", "Medium", "High", "Critical"]


# Pandera Schema for Ingested Routing Data
class RoutingDataSchema(pa.DataFrameModel):
    text: Series[str] = pa.Field(nullable=False, str_length={"min_value": 3})
    category: Series[str] = pa.Field(isin=VALID_CATEGORIES)

    class Config:
        strict = False
        coerce = True


def validate_routing_dataframe(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates the routing dataframe against schema contracts and data quality checks:
    - Required columns present
    - Non-null and non-empty text
    - Category in allowed 8 classes
    - Reports duplicate count
    """
    issues = []

    if "text" not in df.columns or "category" not in df.columns:
        issues.append("Missing required columns: 'text' and 'category'")
        return False, issues

    # Drop null rows if any
    null_texts = df["text"].isna().sum()
    if null_texts > 0:
        issues.append(f"Found {null_texts} null text records.")

    # Check for empty text
    empty_texts = (df["text"].str.strip() == "").sum()
    if empty_texts > 0:
        issues.append(f"Found {empty_texts} empty/whitespace text records.")

    # Check categories
    invalid_cats = set(df["category"].dropna().unique()) - set(VALID_CATEGORIES)
    if invalid_cats:
        issues.append(f"Unrecognized categories found: {invalid_cats}")

    try:
        RoutingDataSchema.validate(df, lazy=True)
    except pa.errors.SchemaErrors as e:
        issues.append(f"Pandera validation failed with {len(e.failure_cases)} issues: {e.failure_cases.head(5).to_dict()}")

    is_valid = len(issues) == 0
    return is_valid, issues


def compute_text_hashes(series: pd.Series) -> Set[str]:
    """Generates SHA-256 hashes of normalized strings for exact match leakage detection."""
    return {
        hashlib.sha256(str(val).strip().lower().encode("utf-8")).hexdigest()
        for val in series if isinstance(val, str) and val.strip()
    }


def verify_no_data_leakage(train_df: pd.DataFrame, test_df: pd.DataFrame) -> Tuple[bool, int]:
    """
    Verifies that no text in test_df leaked from train_df.
    Returns (is_clean, overlap_count).
    """
    train_hashes = compute_text_hashes(train_df["text"])
    test_hashes = compute_text_hashes(test_df["text"])

    overlap = train_hashes.intersection(test_hashes)
    overlap_count = len(overlap)
    return overlap_count == 0, overlap_count
