"""Data splitting stage: creates stratified train/val/test splits and isolates drift holdout data."""

import hashlib
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
import yaml


def load_params() -> dict:
    with open("configs/params.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def compute_hashes(series: pd.Series) -> set:
    """Computes MD5 hashes of text strings to verify zero split leakage."""
    return {hashlib.md5(text.encode("utf-8")).hexdigest() for text in series}


def main() -> None:
    params = load_params()
    seed = params.get("seed", 42)
    split_cfg = params.get("split", {})
    train_ratio = split_cfg.get("train", 0.70)
    val_ratio = split_cfg.get("val", 0.15)
    test_ratio = split_cfg.get("test", 0.15)
    holdout_cat = split_cfg.get("holdout_category", "Storage")

    interim_dir = Path("data/interim")
    processed_dir = Path("data/processed")
    holdout_dir = Path("data/holdout")
    processed_dir.mkdir(parents=True, exist_ok=True)
    holdout_dir.mkdir(parents=True, exist_ok=True)

    routing_path = interim_dir / "routing.parquet"
    if not routing_path.exists():
        raise FileNotFoundError(f"{routing_path} does not exist. Run ingest.py first.")

    df_routing = pd.read_parquet(routing_path)
    print(f"Loaded {len(df_routing):,} routing rows.")

    # 1. Isolate holdout category for drift simulation (PRD Section 6.3 & Phase 6)
    if holdout_cat and holdout_cat in df_routing["category"].values:
        df_holdout = df_routing[df_routing["category"] == holdout_cat].copy()
        df_train_pool = df_routing[df_routing["category"] != holdout_cat].copy()

        holdout_out = holdout_dir / "storage_holdout.parquet"
        df_holdout.to_parquet(holdout_out, index=False)
        print(f"Isolated {len(df_holdout):,} '{holdout_cat}' tickets into {holdout_out} for drift simulation.")
    else:
        df_train_pool = df_routing.copy()

    # 2. Stratified train/val/test split
    # First split off test set: test_ratio
    val_plus_test_ratio = val_ratio + test_ratio
    df_train, df_temp = train_test_split(
        df_train_pool,
        test_size=val_plus_test_ratio,
        random_state=seed,
        stratify=df_train_pool["category"],
    )

    # Then split temp into val and test: 50% each of the remaining 30% = 15% each
    relative_test_ratio = test_ratio / val_plus_test_ratio
    df_val, df_test = train_test_split(
        df_temp,
        test_size=relative_test_ratio,
        random_state=seed,
        stratify=df_temp["category"],
    )

    # 3. Verify zero data leakage
    train_hashes = compute_hashes(df_train["text"])
    val_hashes = compute_hashes(df_val["text"])
    test_hashes = compute_hashes(df_test["text"])

    leakage_train_test = train_hashes.intersection(test_hashes)
    leakage_train_val = train_hashes.intersection(val_hashes)

    if leakage_train_test or leakage_train_val:
        print(f"WARNING: Leakage detected: {len(leakage_train_test)} train-test, {len(leakage_train_val)} train-val overlap.")
        # Remove exact hash matches from test and val to guarantee 100% clean benchmark
        df_val = df_val[~df_val["text"].apply(lambda t: hashlib.md5(t.encode("utf-8")).hexdigest() in train_hashes)]
        df_test = df_test[~df_test["text"].apply(lambda t: hashlib.md5(t.encode("utf-8")).hexdigest() in train_hashes)]

    # 4. Save processed parquet splits
    train_out = processed_dir / "train.parquet"
    val_out = processed_dir / "val.parquet"
    test_out = processed_dir / "test.parquet"

    df_train.to_parquet(train_out, index=False)
    df_val.to_parquet(val_out, index=False)
    df_test.to_parquet(test_out, index=False)

    print(f"Splits saved successfully (zero data leakage verified):")
    print(f" - Train: {len(df_train):,} rows ({len(df_train)/len(df_routing):.1%})")
    print(f" - Val:   {len(df_val):,} rows ({len(df_val)/len(df_routing):.1%})")
    print(f" - Test:  {len(df_test):,} rows ({len(df_test)/len(df_routing):.1%})")


if __name__ == "__main__":
    main()
