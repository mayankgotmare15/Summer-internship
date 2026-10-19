"""
Robustness testing against hand-crafted noisy, messy real-world tickets.
Tests resilience to colloquial abbreviations, compound issues, and informal phrasing.
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient

from src.serving.app import app

client = TestClient(app)

MESSY_TICKETS_PATH = Path("data/test_messy_tickets.json")


def test_messy_tickets_robustness():
    assert MESSY_TICKETS_PATH.exists(), "Messy tickets evaluation dataset missing."
    with open(MESSY_TICKETS_PATH, encoding="utf-8") as f:
        tickets = json.load(f)

    assert len(tickets) >= 20, "Should have at least 20 messy tickets for evaluation."

    correct_category_count = 0
    total = len(tickets)

    for item in tickets:
        resp = client.post("/predict", json={"text": item["text"], "ticket_id": item["id"]})
        assert resp.status_code == 200
        data = resp.json()

        if data["category"] == item["expected_category"]:
            correct_category_count += 1

    accuracy = correct_category_count / total
    print(f"\nMessy Tickets Accuracy: {accuracy:.2%} ({correct_category_count}/{total})")

    # Target: At least 60% accuracy on intentionally noisy, out-of-distribution messy tickets
    assert accuracy >= 0.60, f"Expected messy tickets accuracy >= 60%, got {accuracy:.2%}"
