"""
Unit tests for data validation contracts and leakage detection.
"""

import pandas as pd

from src.data.validate import validate_routing_dataframe, verify_no_data_leakage


def test_validate_routing_dataframe_valid():
    df = pd.DataFrame(
        {
            "text": ["Need new laptop charger", "Password expired for email"],
            "category": ["Hardware", "Access"],
        }
    )
    is_valid, issues = validate_routing_dataframe(df)
    assert is_valid is True
    assert len(issues) == 0


def test_validate_routing_dataframe_invalid_category():
    df = pd.DataFrame({"text": ["System update issue"], "category": ["UnknownNonExistentCategory"]})
    is_valid, issues = validate_routing_dataframe(df)
    assert is_valid is False
    assert any("Unrecognized categories" in issue for issue in issues)


def test_validate_routing_dataframe_empty_text():
    df = pd.DataFrame({"text": ["   "], "category": ["Hardware"]})
    is_valid, issues = validate_routing_dataframe(df)
    assert is_valid is False
    assert any("empty/whitespace" in issue for issue in issues)


def test_verify_no_data_leakage():
    train_df = pd.DataFrame({"text": ["Cannot connect to VPN", "Need extra RAM for desktop"]})
    clean_test_df = pd.DataFrame(
        {"text": ["Outlook crashes on open", "Requesting HR leave calendar"]}
    )
    is_clean, overlap_count = verify_no_data_leakage(train_df, clean_test_df)
    assert is_clean is True
    assert overlap_count == 0

    leaked_test_df = pd.DataFrame({"text": ["cannot connect to vpn", "Different ticket text"]})
    is_clean, overlap_count = verify_no_data_leakage(train_df, leaked_test_df)
    assert is_clean is False
    assert overlap_count == 1
