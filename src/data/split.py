"""
Data splitting and preprocessing pipeline.
Enforces stratified splitting, data contract validation, leakage detection,
and creates the held-out category set for Phase 5 drift drill.
"""

import sys
from pathlib import Path

# Ensure workspace root is always on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

from src.data.validate import validate_routing_dataframe, verify_no_data_leakage
from src.features.preprocess import preprocess_corpus


def split_and_preprocess_data():
    with open("configs/params.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    raw_path = Path(config["data"]["raw_routing_path"])
    processed_dir = Path(config["data"]["processed_dir"])
    processed_dir.mkdir(parents=True, exist_ok=True)
    held_out_cat = config["data"].get("held_out_drift_category", "Storage")
    seed = config["data"].get("random_seed", 42)

    print(f"Reading raw data from {raw_path}...")
    df = pd.read_csv(raw_path)

    # 1. Validation check
    is_valid, issues = validate_routing_dataframe(df)
    if not is_valid:
        print(f"Validation issues found: {issues}")
    else:
        print("Raw dataset schema validation passed.")

    # 2. Extract Drift Dataset (Held-back category)
    if held_out_cat in df["category"].values:
        drift_df = df[df["category"] == held_out_cat].copy()
        trainable_df = df[df["category"] != held_out_cat].copy()
        drift_path = processed_dir / "drift_held_out_category.csv"
        drift_df.to_csv(drift_path, index=False)
        print(
            f"Extracted {len(drift_df)} samples for held-out drift category '{held_out_cat}' -> {drift_path}"
        )
    else:
        trainable_df = df.copy()

    # Deduplicate to strictly prevent split leakage
    trainable_df = trainable_df.drop_duplicates(subset=["text"]).copy()

    # 3. Stratified Split: 70% Train, 15% Val, 15% Test
    train_df, temp_df = train_test_split(
        trainable_df, test_size=0.30, random_state=seed, stratify=trainable_df["category"]
    )
    val_df, test_df = train_test_split(
        temp_df, test_size=0.50, random_state=seed, stratify=temp_df["category"]
    )

    # 4. Leakage Verification
    is_clean, overlap = verify_no_data_leakage(train_df, test_df)
    print(
        f"Split leakage check: {'CLEAN' if is_clean else 'LEAK DETECTED'} ({overlap} overlapping texts)"
    )

    # 5. Preprocessing
    print("Running shared preprocessing engine...")
    train_df = train_df.copy()
    val_df = val_df.copy()
    test_df = test_df.copy()

    train_df["cleaned_text"] = preprocess_corpus(train_df["text"])
    val_df["cleaned_text"] = preprocess_corpus(val_df["text"])
    test_df["cleaned_text"] = preprocess_corpus(test_df["text"])

    # 6. Save Processed Datasets
    train_df.to_csv(processed_dir / "train.csv", index=False)
    val_df.to_csv(processed_dir / "val.csv", index=False)
    test_df.to_csv(processed_dir / "test.csv", index=False)

    print(f"Processed splits saved to {processed_dir}:")
    print(f" - Train: {len(train_df)} rows")
    print(f" - Validation: {len(val_df)} rows")
    print(f" - Test: {len(test_df)} rows")


if __name__ == "__main__":
    split_and_preprocess_data()
