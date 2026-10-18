"""
Unit tests for text preprocessing engine.
"""

from src.features.preprocess import clean_text, preprocess_corpus


def test_clean_text_basic():
    raw = "Need ACCESS to the database immediately!!!"
    cleaned = clean_text(raw)
    assert "access" in cleaned
    assert "database" in cleaned
    assert "immediately" in cleaned
    # Verify punctuation removed
    assert "!" not in cleaned


def test_clean_text_removes_urls_and_emails():
    raw = "Check http://example.com/login and email admin@company.com for ticket."
    cleaned = clean_text(raw)
    assert "http" not in cleaned
    assert "example" not in cleaned
    assert "admin" not in cleaned
    assert "company" not in cleaned
    assert "ticket" in cleaned


def test_clean_text_empty_and_null():
    assert clean_text("") == ""
    assert clean_text("    ") == ""
    assert clean_text(None) == ""


def test_preprocess_corpus():
    corpus = [
        "Printer not responding",
        "Need new monitor for desk"
    ]
    cleaned_corpus = preprocess_corpus(corpus)
    assert len(cleaned_corpus) == 2
    assert "printer" in cleaned_corpus[0]
    assert "monitor" in cleaned_corpus[1]
