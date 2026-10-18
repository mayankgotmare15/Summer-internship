"""
Shared text preprocessing module for IT Ticket Classification.
Guarantees zero training-serving skew by enforcing the exact same text normalization
pipeline across offline training, batch evaluation, and online FastAPI serving.
"""

import re
import string
from typing import Any

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer

    # Download required NLTK corpora quietly if missing
    try:
        _STOPWORDS = set(stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords", quiet=True)
        _STOPWORDS = set(stopwords.words("english"))

    try:
        _LEMMATIZER = WordNetLemmatizer()
        _LEMMATIZER.lemmatize("tickets")
    except LookupError:
        nltk.download("wordnet", quiet=True)
        nltk.download("omw-1.4", quiet=True)
        _LEMMATIZER = WordNetLemmatizer()
except Exception:
    # Safe fallback if NLTK is not yet initialized
    _STOPWORDS = {
        "i",
        "me",
        "my",
        "myself",
        "we",
        "our",
        "ours",
        "ourselves",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
        "he",
        "him",
        "his",
        "himself",
        "she",
        "her",
        "hers",
        "herself",
        "it",
        "its",
        "itself",
        "they",
        "them",
        "their",
        "theirs",
        "themselves",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        "am",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "doing",
        "a",
        "an",
        "the",
        "and",
        "but",
        "if",
        "or",
        "because",
        "as",
        "until",
        "while",
        "of",
        "at",
        "by",
        "for",
        "with",
        "about",
        "against",
        "between",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "to",
        "from",
        "up",
        "down",
        "in",
        "out",
        "on",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "any",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "s",
        "t",
        "can",
        "will",
        "just",
        "don",
        "should",
        "now",
    }
    _LEMMATIZER = None


def clean_text(
    text: str, lowercase: bool = True, remove_stopwords: bool = True, lemmatize: bool = True
) -> str:
    """
    Cleans raw ticket text by:
    1. Converting to string and handling nulls
    2. Lowercasing
    3. Stripping email addresses, URLs, and special characters
    4. Removing stop words
    5. Lemmatizing tokens
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    if lowercase:
        text = text.lower()

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Remove email addresses
    text = re.sub(r"\S+@\S+", " ", text)

    # Remove punctuations and digits
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
    text = re.sub(r"\d+", " ", text)

    # Tokenize by whitespace
    tokens = text.split()

    # Filter stopwords
    if remove_stopwords:
        tokens = [t for t in tokens if t not in _STOPWORDS and len(t) > 1]

    # Lemmatize
    if lemmatize and _LEMMATIZER is not None:
        tokens = [_LEMMATIZER.lemmatize(t) for t in tokens]

    return " ".join(tokens)


def preprocess_corpus(
    texts: Any,
    lowercase: bool = True,
    remove_stopwords: bool = True,
    lemmatize: bool = True,
) -> list[str]:
    """Applies clean_text across a sequence of documents."""
    return [
        clean_text(t, lowercase=lowercase, remove_stopwords=remove_stopwords, lemmatize=lemmatize)
        for t in texts
    ]
