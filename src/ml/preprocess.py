"""Shared text preprocessing module for both training and serving (PRD FR-03).

Ensures zero training-serving skew by providing identical tokenization,
stopword removal, and lemmatization routines across pipelines.
"""

import hashlib
import inspect
import re
from typing import List, Optional
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import pandas as pd

# Pre-compiled regex patterns for fast normalization
RE_URL = re.compile(r"https?://\S+|www\.\S+")
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
RE_NON_ALPHA = re.compile(r"[^a-zA-Z\s]")
RE_WHITESPACE = re.compile(r"\s+")

_lemmatizer: Optional[WordNetLemmatizer] = None
_stop_words: Optional[set] = None


def _init_nltk() -> None:
    """Lazy initialization of NLTK corpora and models."""
    global _lemmatizer, _stop_words
    if _lemmatizer is None:
        try:
            nltk.data.find("corpora/stopwords")
        except LookupError:
            nltk.download("stopwords", quiet=True)
        try:
            nltk.data.find("corpora/wordnet")
        except LookupError:
            nltk.download("wordnet", quiet=True)
            nltk.download("omw-1.4", quiet=True)

        _lemmatizer = WordNetLemmatizer()
        _stop_words = set(stopwords.words("english"))


def clean_text(text: str) -> str:
    """Normalizes text: lowercase, strips URLs, emails, and non-alphabetic chars."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = RE_URL.sub(" ", text)
    text = RE_EMAIL.sub(" ", text)
    text = RE_NON_ALPHA.sub(" ", text)
    text = RE_WHITESPACE.sub(" ", text).strip()
    return text


def preprocess_text(text: str) -> str:
    """End-to-end preprocessing: clean -> tokenize -> remove stopwords -> lemmatize."""
    _init_nltk()
    cleaned = clean_text(text)
    if not cleaned:
        return ""

    tokens = cleaned.split()
    processed_tokens: List[str] = [
        _lemmatizer.lemmatize(token)
        for token in tokens
        if token not in _stop_words and len(token) >= 2
    ]
    return " ".join(processed_tokens)


def preprocess_series(series: pd.Series) -> pd.Series:
    """Preprocesses a pandas Series of texts."""
    return series.astype(str).apply(preprocess_text)


def get_preprocess_fingerprint() -> str:
    """Generates a SHA-256 fingerprint of the preprocessing logic.

    Baking this into the champion bundle allows the API to detect training-serving skew at startup.
    """
    code_str = inspect.getsource(clean_text) + inspect.getsource(preprocess_text)
    return hashlib.sha256(code_str.encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Preprocess processed parquet datasets into features.")
    parser.add_argument("--input-dir", type=str, default="data/processed")
    parser.add_argument("--output-dir", type=str, default="data/features")
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for split in ["train", "val", "test"]:
        file_path = in_dir / f"{split}.parquet"
        if file_path.exists():
            print(f"Preprocessing {split}.parquet...")
            df = pd.read_parquet(file_path)
            df["text_clean"] = preprocess_series(df["text"])
            output_file = out_dir / f"{split}.parquet"
            df.to_parquet(output_file, index=False)
            print(f"Saved features to {output_file} (fingerprint={get_preprocess_fingerprint()})")
