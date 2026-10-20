"""Unit tests for shared preprocessing, normalization, lemmatization, and fingerprinting."""

from src.ml.preprocess import clean_text, get_preprocess_fingerprint, preprocess_text


def test_clean_text_lowercasing_and_punctuation():
    raw = "My Laptop WON'T Turn On!! Please Help..."
    cleaned = clean_text(raw)
    assert cleaned == "my laptop won t turn on please help"


def test_clean_text_url_and_email_stripping():
    raw = "Check https://vpn.company.internal/login or email support@company.com immediately"
    cleaned = clean_text(raw)
    assert "https" not in cleaned
    assert "vpn.company" not in cleaned
    assert "support@company.com" not in cleaned


def test_preprocess_text_stopwords_and_lemmatization():
    raw = "The user passwords and accounts were locked after multiple connection drops"
    processed = preprocess_text(raw)
    words = processed.split()
    assert "the" not in words
    assert "were" not in words
    assert "and" not in words
    # Lemmatized plurals to singular forms
    assert "password" in words
    assert "account" in words
    assert "drop" in words


def test_preprocess_fingerprint_deterministic():
    fp1 = get_preprocess_fingerprint()
    fp2 = get_preprocess_fingerprint()
    assert isinstance(fp1, str)
    assert len(fp1) == 16
    assert fp1 == fp2
